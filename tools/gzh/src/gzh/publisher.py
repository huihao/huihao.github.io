"""发布器：把内容池里的文章真正推到微信。

一条完整链路：

    选稿 → 配额校验 → 渲染（排版/清洗/图片/封面）→ 建草稿 → 发布/群发 → 落库留痕

三种发布模式：

* ``draft``   —— 只进草稿箱，由运营在后台人工确认后发布（最安全，适合新流程冷启动）。
* ``publish`` —— 走发布能力（freepublish），发布后可在「已发表」中查看。
* ``mass``    —— 群发消息，真正触达粉丝，受每日群发次数限制。
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config import Account, Config, Plan
from .errors import GzhError, QuotaExceeded, WechatAPIError
from .http import HttpClient
from .logging_setup import get_logger
from .models import (
    STATUS_APPROVED,
    STATUS_BLOCKED,
    STATUS_DRAFTED,
    STATUS_FAILED,
    STATUS_MASS_SENT,
    STATUS_PUBLISHED,
    STATUS_RENDERED,
    STATUS_SKIPPED,
    Article,
    PublishResult,
)
from .pipeline.css import DEFAULT_CSS
from .pipeline.render import Renderer
from .pipeline.sanitize import check_compliance, plain_text
from .sources import build_source
from .store import Store
from .wechat.client import WeChatClient

#: 各模式对应的每日配额键。
QUOTA_KEYS = {"draft": "draft_per_day", "publish": "publish_per_day", "mass": "mass_per_day"}

#: 各模式默认每日配额（以微信后台实际额度为准）。
DEFAULT_QUOTA = {"draft_per_day": 50, "publish_per_day": 4, "mass_per_day": 1}

#: 各模式计入配额的终态。
QUOTA_STATUS = {"draft": STATUS_DRAFTED, "publish": STATUS_PUBLISHED, "mass": STATUS_MASS_SENT}


class Publisher:
    """内容发布器。"""

    def __init__(
        self,
        config: Config,
        store: Store,
        logger: Any = None,
        http: HttpClient | None = None,
    ) -> None:
        self.config = config
        self.store = store
        self.logger = logger or get_logger("gzh.publisher")
        self.http = http or HttpClient(logger=self.logger)
        self._clients: dict[str, WeChatClient] = {}

    # ------------------------------------------------------------------ 客户端
    def client(self, account: Account) -> WeChatClient:
        """获取（并缓存）账号对应的微信客户端。"""
        if account.id not in self._clients:
            self._clients[account.id] = WeChatClient(
                account=account, store=self.store, http=self.http, logger=self.logger
            )
        return self._clients[account.id]

    def _renderer(self, account: Account) -> Renderer:
        policies = self.config.policies
        styles = policies.get("styles")
        css_text = styles if isinstance(styles, str) and styles.strip() else DEFAULT_CSS
        return Renderer(
            client=self.client(account),
            store=self.store,
            logger=self.logger,
            http=self.http,
            css_text=css_text,
            digest_max_length=int(policies.get("digest_max_length", 120)),
            content_roots=[self.config.content_dir, self.config.root, self.config.assets_dir],
            upload_remote_images=bool(policies.get("upload_remote_images", True)),
            allow_missing_cover=bool(policies.get("allow_missing_cover", False)),
        )

    # ------------------------------------------------------------------ 采集
    def collect(self, plan: Plan) -> tuple[int, int]:
        """从内容源采集文章入池。

        Returns:
            (新增数量, 已存在跳过数量)
        """
        account = self.config.account(plan.account)
        source = build_source(
            plan.source,
            roots=[self.config.content_dir, self.config.root],
            http=self.http,
            logger=self.logger,
        )
        articles = source.fetch()
        created = 0
        duplicated = 0
        for article in articles:
            article.plan_id = plan.id
            article.account_id = account.id
            if not article.title:
                article.title = "(无标题)"
            if self.store.upsert_article(article):
                created += 1
                self.store.add_event(
                    "INFO",
                    "内容已入池",
                    component="collect",
                    account_id=account.id,
                    plan_id=plan.id,
                    article_id=article.id,
                    data={"title": article.title, "source": article.source_key},
                )
            else:
                duplicated += 1
        self.logger.info(
            "采集完成",
            extra={
                "context": {
                    "plan": plan.id,
                    "fetched": len(articles),
                    "created": created,
                    "duplicated": duplicated,
                }
            },
        )
        return created, duplicated

    # ------------------------------------------------------------------ 发布
    def publish(
        self,
        plan: Plan,
        *,
        limit: int | None = None,
        dry_run: bool = False,
        trigger: str = "manual",
    ) -> list[PublishResult]:
        """执行一次发布。"""
        account = self.config.account(plan.account)
        mode = plan.mode
        results: list[PublishResult] = []

        quota_limit = self.quota_limit(account, mode)
        used = self.quota_used(account, mode)
        remaining = max(0, quota_limit - used)

        self.logger.info(
            "开始发布",
            extra={
                "context": {
                    "plan": plan.id,
                    "account": account.id,
                    "mode": mode,
                    "quota_limit": quota_limit,
                    "used_today": used,
                    "dry_run": dry_run or plan.dry_run,
                }
            },
        )

        if remaining <= 0:
            self.logger.warning(
                "当日配额已用尽，跳过本次发布",
                extra={"context": {"plan": plan.id, "limit": quota_limit, "used": used}},
            )
            self.store.add_event(
                "WARNING",
                "当日配额已用尽",
                component="publish",
                account_id=account.id,
                plan_id=plan.id,
                data={"limit": quota_limit, "used": used},
            )
            return results

        select = plan.select
        candidates = self.store.pick_candidates(
            plan.id,
            limit=limit if limit is not None else plan.limit,
            strategy=plan.strategy,
            require_tags=select.get("require_tags", []) or [],
            exclude_tags=select.get("exclude_tags", []) or [],
            require_approval=plan.require_approval,
        )

        if not candidates:
            self.logger.info(
                "没有待发布内容",
                extra={"context": {"plan": plan.id, "require_approval": plan.require_approval}},
            )
            return results

        for article in candidates:
            if remaining <= 0:
                self.logger.warning(
                    "配额用尽，剩余内容留待下次",
                    extra={"context": {"plan": plan.id, "title": article.title}},
                )
                break
            result = self.publish_article(
                article,
                plan=plan,
                account=account,
                dry_run=dry_run or plan.dry_run,
                trigger=trigger,
            )
            results.append(result)
            if result.ok and result.status in (STATUS_PUBLISHED, STATUS_MASS_SENT, STATUS_DRAFTED):
                remaining -= 1
        return results

    def publish_article(
        self,
        article: Article,
        *,
        plan: Plan,
        account: Account,
        dry_run: bool = False,
        trigger: str = "manual",
    ) -> PublishResult:
        """发布单篇文章（可能抛异常，异常会被记录到文章状态里）。"""
        result = PublishResult(
            plan_id=plan.id,
            article_id=article.id,
            title=article.title,
            status=article.status,
            mode=plan.mode,
            dry_run=dry_run,
        )

        # 人工审核门禁
        if plan.require_approval and article.status != STATUS_APPROVED:
            result.status = STATUS_BLOCKED
            result.error = "等待人工审核放行（gzh approve --id ...）"
            self.store.update_article(article.id, status=STATUS_BLOCKED)
            self.store.add_event(
                "INFO",
                "文章等待人工审核",
                component="publish",
                account_id=account.id,
                plan_id=plan.id,
                article_id=article.id,
                data={"title": article.title},
            )
            self.logger.info(
                "文章等待人工审核",
                extra={"context": {"plan": plan.id, "title": article.title}},
            )
            return result

        # 合规红线粗筛（在任何写操作之前，避免脏内容进入草稿箱）
        forbidden = self.config.policies.get("forbidden_keywords") or []
        if forbidden:
            safe_contexts = self.config.policies.get("forbidden_keyword_safe_contexts") or {}
            hits = check_compliance(
                plain_text(article.markdown, article.source_html),
                forbidden_keywords=forbidden,
                safe_contexts=safe_contexts,
            )
            if hits:
                result.status = STATUS_BLOCKED
                result.error = f"命中红线关键词，需人工复核: {', '.join(hits)}"
                self.store.update_article(
                    article.id, status=STATUS_BLOCKED, error=result.error
                )
                self.store.add_event(
                    "WARNING",
                    "文章命中红线关键词",
                    component="compliance",
                    account_id=account.id,
                    plan_id=plan.id,
                    article_id=article.id,
                    data={"title": article.title, "hits": hits},
                )
                self.logger.warning(
                    "文章命中红线关键词，已拦下",
                    extra={"context": {"plan": plan.id, "title": article.title, "hits": hits}},
                )
                return result

        try:
            rendered = self._render_for_publish(article, account, plan, dry_run=dry_run)
            for warning in rendered.warnings:
                self.logger.warning(
                    "渲染告警",
                    extra={"context": {"title": article.title, "warning": warning}},
                )

            if dry_run:
                result.status = STATUS_RENDERED
                result.ok = True
                self.store.update_article(
                    article.id,
                    status=STATUS_RENDERED,
                    content_html=rendered.content_html,
                    digest=rendered.digest,
                    error="",
                )
                self.logger.info(
                    "演练完成（未真实发布）",
                    extra={"context": {"title": article.title, "digest": rendered.digest}},
                )
                return result

            client = self.client(account)
            media_id = client.add_draft(rendered.payload)
            self.store.update_article(
                article.id,
                status=STATUS_DRAFTED,
                media_id=media_id,
                content_html=rendered.content_html,
                digest=rendered.digest,
                thumb_media_id=rendered.thumb_media_id,
                error="",
            )
            self.logger.info(
                "草稿已创建",
                extra={
                    "context": {
                        "title": article.title,
                        "media_id": media_id,
                        "thumb": rendered.thumb_media_id,
                    }
                },
            )
            result.media_id = media_id

            if plan.mode == "draft":
                result.status = STATUS_DRAFTED
                result.ok = True
                self._mark_published(article, account, plan, result)
                return result

            if plan.mode == "publish":
                publish_id = client.submit_publish(media_id)
                self.store.update_article(article.id, publish_id=publish_id)
                publish_result = client.wait_publish(publish_id, timeout=180)
                wechat_article_id = str(publish_result.get("article_id") or "")
                result.publish_id = publish_id
                result.article_id_wechat = wechat_article_id
                result.status = STATUS_PUBLISHED
                result.ok = True
                self.store.update_article(
                    article.id,
                    status=STATUS_PUBLISHED,
                    wechat_article_id=wechat_article_id,
                    error="",
                )
                self.logger.info(
                    "文章已发布",
                    extra={
                        "context": {
                            "title": article.title,
                            "publish_id": publish_id,
                            "article_id": wechat_article_id,
                        }
                    },
                )
                self._mark_published(article, account, plan, result)
                return result

            if plan.mode == "mass":
                mass_media_id = media_id
                use_article_id = plan.mass_media_id_source in ("article_id", "auto")
                if use_article_id:
                    try:
                        publish_id = client.submit_publish(media_id)
                        publish_result = client.wait_publish(publish_id, timeout=180)
                        article_id = str(publish_result.get("article_id") or "")
                        if article_id:
                            mass_media_id = article_id
                            result.publish_id = publish_id
                            result.article_id_wechat = article_id
                        else:
                            raise WechatAPIError(
                                -1,
                                "发布结果中没有 article_id",
                                path="/cgi-bin/freepublish/get",
                            )
                    except WechatAPIError as exc:
                        if plan.mass_media_id_source == "article_id" or not exc.is_permission_error:
                            raise
                        # 账号没有发布能力时降级：用草稿 media_id 直接群发
                        self.logger.warning(
                            "账号缺少发布能力，改用草稿 media_id 群发",
                            extra={
                                "context": {
                                    "plan": plan.id,
                                    "title": article.title,
                                    "code": exc.code,
                                }
                            },
                        )
                        mass_media_id = media_id
                send_time = self._mass_send_time(plan, article)
                client.mass_send(
                    mass_media_id,
                    is_to_all=bool(plan.select.get("is_to_all", True)),
                    tag_id=int(plan.select.get("tag_id", 0) or 0),
                    send_time=send_time,
                    title=article.title,
                )
                result.status = STATUS_MASS_SENT
                result.ok = True
                self.store.update_article(
                    article.id,
                    status=STATUS_MASS_SENT,
                    wechat_article_id=result.article_id_wechat,
                    error="",
                )
                self.logger.info(
                    "群发已提交",
                    extra={
                        "context": {
                            "title": article.title,
                            "media_id": mass_media_id,
                            "scheduled": bool(send_time),
                        }
                    },
                )
                self._mark_published(article, account, plan, result)
                return result

            raise WechatAPIError(-1, f"未知的发布模式: {plan.mode}")

        except QuotaExceeded as exc:
            result.status = STATUS_SKIPPED
            result.error = str(exc)
            self._record_failure(article, account, plan, result, exc)
        except GzhError as exc:
            result.status = STATUS_FAILED
            result.error = str(exc)
            self._record_failure(article, account, plan, result, exc)
        except Exception as exc:  # noqa: BLE001 - 兜底，保证调度器不中断
            result.status = STATUS_FAILED
            result.error = f"{type(exc).__name__}: {exc}"
            self._record_failure(article, account, plan, result, exc)
        return result

    # ------------------------------------------------------------------ 辅助
    def _render_for_publish(self, article: Article, account: Account, plan: Plan, *, dry_run: bool):
        """渲染文章；dry-run 模式下跳过所有素材上传。"""
        renderer = self._renderer(account)
        if dry_run:
            renderer.allow_missing_cover = True
            rendered = renderer.render_content_only(article)
            return rendered
        return renderer.render(article, account)

    def quota_limit(self, account: Account, mode: str) -> int:
        """计算某账号在指定模式下的当日配额。"""
        key = QUOTA_KEYS.get(mode, "publish_per_day")
        account_quota = account.quota.get(key)
        if account_quota is not None:
            return int(account_quota)
        policies_quota = self.config.policies.get("quota", {}) or {}
        value = policies_quota.get(key)
        if value is not None:
            return int(value)
        return DEFAULT_QUOTA.get(key, 1)

    def quota_used(self, account: Account, mode: str) -> int:
        """统计某账号当日在指定模式下已消耗的配额。"""
        status = QUOTA_STATUS.get(mode, STATUS_PUBLISHED)
        return self.store.count_status_today(account.id, status)

    def _mass_send_time(self, plan: Plan, article: Article) -> int | None:
        """计算定时群发时间（可选）。"""
        raw = plan.mass_send_at or plan.select.get("mass_send_at") or article.publish_at
        if not raw:
            return None
        from .timeutil import parse_datetime

        moment = parse_datetime(str(raw), timezone=self.config.timezone)
        if moment is None:
            return None
        return int(moment.timestamp())

    def _mark_published(
        self, article: Article, account: Account, plan: Plan, result: PublishResult
    ) -> None:
        """记录发布成功。"""
        from .store import now_iso

        self.store.update_article(article.id, published_at=now_iso())
        self.store.add_event(
            "INFO",
            "发布成功",
            component="publish",
            account_id=account.id,
            plan_id=plan.id,
            article_id=article.id,
            data=result.as_dict(),
        )

    def _record_failure(
        self, article: Article, account: Account, plan: Plan, result: PublishResult, exc: Exception
    ) -> None:
        """记录发布失败。"""
        attempts = article.attempts + 1
        self.store.update_article(
            article.id,
            status=result.status,
            error=result.error[:2000],
            attempts=attempts,
        )
        self.store.add_event(
            "ERROR",
            "发布失败",
            component="publish",
            account_id=account.id,
            plan_id=plan.id,
            article_id=article.id,
            data={"error": result.error, "attempts": attempts, "mode": plan.mode},
        )
        self.logger.error(
            "发布失败",
            extra={
                "context": {
                    "plan": plan.id,
                    "title": article.title,
                    "attempts": attempts,
                    "error": result.error,
                }
            },
        )

    # ------------------------------------------------------------------ 预览
    def preview(self, article: Article, account: Account) -> dict[str, Any]:
        """生成预览信息（不调用任何写接口）。"""
        renderer = self._renderer(account)
        html, warnings = renderer.render_content(article)
        from .pipeline.markdown import make_digest

        return {
            "title": article.title,
            "digest": (article.digest or "").strip() or make_digest(html, 120),
            "content_html": html,
            "warnings": warnings,
            "cover": article.cover,
        }
