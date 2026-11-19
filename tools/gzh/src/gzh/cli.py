"""命令行入口。

常用命令::

    gzh init                      # 初始化项目结构与示例配置
    gzh check                     # 环境与配置体检
    gzh collect --plan daily      # 采集内容入库
    gzh list --status queue       # 查看待发布队列
    gzh preview --id <article_id> # 预览渲染后的正文
    gzh publish --plan daily      # 立即发布（可加 --dry-run 演练）
    gzh approve --id <article_id> # 人工审核放行
    gzh status                    # 查看计划状态、配额与最近执行记录
    gzh plan                      # 查看排期概览
    gzh run                       # 前台运行调度器
    gzh daemon                    # 后台运行调度器
    gzh logs --lines 50           # 查看运行日志
    gzh retry --id <article_id>   # 重试失败的文章
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from . import __version__
from .bootstrap import init_project
from .config import Config, load_config, resolve_root
from .errors import GzhError
from .http import HttpClient
from .logging_setup import get_logger, setup_logging
from .models import STATUS_APPROVED, STATUS_FAILED, Article
from .publisher import Publisher
from .scheduler import Scheduler, SingleInstanceLock, describe_schedule
from .store import Store

BANNER = f"gzh — 公众号管理 SOP 自动化套件 v{__version__}"


# ---------------------------------------------------------------------- 工具
def _print_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> None:
    """打印简单表格。columns 为 (标题, 字段名) 列表。"""
    if not rows:
        print("（无数据）")
        return
    widths = {
        key: max(len(title), *(len(str(row.get(key, ""))) for row in rows))
        for title, key in columns
    }
    header = "  ".join(title.ljust(widths[key]) for title, key in columns)
    print(header)
    print("  ".join("-" * widths[key] for _, key in columns))
    for row in rows:
        print("  ".join(str(row.get(key, "")).ljust(widths[key]) for _, key in columns))


def _resolve_plan(config: Config, plan_id: str | None):
    if plan_id:
        return config.plan(plan_id)
    enabled = [p for p in config.plans if p.enabled]
    if len(enabled) == 1:
        return enabled[0]
    if not enabled:
        raise GzhError("没有启用的发布计划，请检查 config/scheduler.json")
    raise GzhError("存在多个启用的发布计划，请用 --plan 指定，例如: " + ", ".join(p.id for p in enabled))


def _build(args: argparse.Namespace) -> tuple[Config, Store, Publisher, Any]:
    config = load_config(getattr(args, "root", None))
    logger = setup_logging(
        log_dir=config.logs_dir,
        level=getattr(args, "log_level", "INFO"),
        console=not getattr(args, "quiet", False),
    )
    store = Store(config.db_path)
    publisher = Publisher(config, store, logger, HttpClient(logger=logger))
    return config, store, publisher, logger


def _find_article(store: Store, article_id: str) -> Article:
    """按文章 ID / ID 前缀 / 标题片段 / 来源键查找文章。"""
    article = store.get_article(article_id)
    if article is not None:
        return article
    needle = article_id.lower()
    for candidate in store.list_articles():
        if (
            candidate.id.startswith(needle)
            or needle in candidate.title.lower()
            or needle in (candidate.source_key or "").lower()
        ):
            return candidate
    raise GzhError(f"找不到文章: {article_id}（可用 `gzh list` 查看 ID 与标题）")


# ---------------------------------------------------------------------- 子命令
def cmd_init(args: argparse.Namespace) -> int:
    root = resolve_root(getattr(args, "root", None))
    created = init_project(root, force=getattr(args, "force", False))
    print(BANNER)
    print(f"项目根目录: {root}")
    if created:
        print("已创建/更新：")
        for item in created:
            print(f"  + {item}")
    else:
        print("所有文件均已存在，未做修改（--force 可覆盖示例配置）")
    print("\n下一步：")
    print("  1) cp .env.example .env && 编辑 .env 填入 WECHAT_APPID / WECHAT_APPSECRET")
    print("  2) export $(grep -v '^#' .env | xargs)   # 或在 systemd/启动脚本中注入")
    print("  3) gzh check                            # 体检")
    print("  4) gzh publish --plan daily-draft --dry-run   # 演练，不真实发布")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "root", None))
    logger = setup_logging(log_dir=config.logs_dir, level="INFO", console=False)
    store = Store(config.db_path)
    http = HttpClient(logger=logger)
    publisher = Publisher(config, store, logger, http)

    print(BANNER)
    print(f"项目根目录: {config.root}")
    print(f"配置文件  : {config.config_dir}")
    print(f"内容资源库: {config.content_dir}")
    print(f"状态数据库: {config.db_path}")
    print(f"日志目录  : {config.logs_dir}")
    print(f"时区      : {config.timezone}")
    print()

    problems = 0
    warnings = 0

    # 账号
    print("[账号]")
    if config.missing_env:
        print(f"  ! 以下环境变量未注入或为空: {', '.join(config.missing_env)}")
        print("    修复: cp .env.example .env && 编辑后 source .env；或在 systemd/启动脚本中 export")
        problems += 1
    for account in config.accounts.values():
        status = "OK"
        detail = ""
        if not account.app_id:
            status, detail = "缺少", "app_id 未注入环境变量"
            problems += 1
        elif not account.app_secret:
            status, detail = "缺少", "app_secret 未注入环境变量"
            problems += 1
        print(f"  - {account.id} ({account.label}) app_id={account.app_id or '-'} 凭据={status} {detail}")

    # 计划
    print("\n[发布计划]")
    for row in describe_schedule(config):
        flag = "启用" if row["enabled"] else "停用"
        print(
            f"  - {row['id']} 账号={row['account']} 模式={row['mode']} 触发={row['trigger']}:{row['expression']} "
            f"窗口={row['window'] or '不限'} {flag}"
        )
        print(f"      下次触发: {row['next_at'] or '（无法计算）'}")

    # 目录
    print("\n[目录与资源]")
    for label, path in (
        ("内容资源库", config.content_dir),
        ("素材目录", config.assets_dir),
        ("状态目录", config.var_dir),
        ("日志目录", config.logs_dir),
    ):
        exists = path.exists()
        mark = "OK" if exists else "缺失"
        print(f"  - {label}: {path} [{mark}]")
        if not exists:
            problems += 1
    markdown_count = len(list(config.content_dir.rglob("*.md"))) if config.content_dir.exists() else 0
    print(f"  - Markdown 稿件数量: {markdown_count}")
    if markdown_count == 0:
        print("    提示: 内容资源库为空，发布计划将没有可发布内容")
        warnings += 1

    # 内容池
    stats = store.stats()
    print(f"\n[内容池] {stats or '空'}")

    # 网络与凭据
    print("\n[连通性]")
    if getattr(args, "no_network", False):
        print("  - 已跳过（--no-network）")
    else:
        for account in config.accounts.values():
            if not account.app_id or not account.app_secret:
                print(f"  - {account.id}: 跳过（凭据未注入）")
                continue
            try:
                client = publisher.client(account)
                client.token(force=True)
                print(f"  - {account.id}: access_token 获取成功")
                try:
                    ips = client.callback_ips()
                    print(f"    IP 白名单: {', '.join(ips) if ips else '（未返回）'}")
                except GzhError as exc:
                    print(f"    IP 白名单查询失败: {exc}")
                    warnings += 1
            except GzhError as exc:
                print(f"  - {account.id}: 失败 → {exc}")
                if getattr(exc, "hint", None):
                    print(f"    建议: {exc.hint()}")
                problems += 1
            except Exception as exc:  # noqa: BLE001
                print(f"  - {account.id}: 异常 → {exc}")
                problems += 1

    print()
    if problems:
        print(f"检查结果: {problems} 项必须修复, {warnings} 项需关注")
        return 1
    print(f"检查结果: 全部通过（{warnings} 项提示）")
    return 0


def cmd_collect(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    plans = [config.plan(args.plan)] if getattr(args, "plan", None) else [p for p in config.plans if p.enabled]
    total_new = 0
    for plan in plans:
        try:
            created, duplicated = publisher.collect(plan)
        except GzhError as exc:
            print(f"[{plan.id}] 采集失败: {exc}")
            logger.error("采集失败", extra={"context": {"plan": plan.id, "error": str(exc)}})
            continue
        total_new += created
        print(f"[{plan.id}] 新增 {created} 篇，重复跳过 {duplicated} 篇")
    print(f"合计新增 {total_new} 篇")
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    status = getattr(args, "status", None)
    articles = store.list_articles(status=status, plan_id=getattr(args, "plan", None), limit=getattr(args, "limit", None))
    rows = []
    for article in articles:
        rows.append(
            {
                "id": article.id[:10],
                "title": article.title[:38],
                "status": article.status,
                "plan": article.plan_id,
                "tags": ",".join(article.tags[:3]),
                "created": (article.created_at or "")[:16].replace("T", " "),
                "error": article.error[:40],
            }
        )
    _print_table(
        rows,
        [("ID", "id"), ("标题", "title"), ("状态", "status"), ("计划", "plan"), ("标签", "tags"), ("创建时间", "created"), ("错误", "error")],
    )
    print(f"\n共 {len(rows)} 条")
    return 0


def cmd_preview(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    article = _find_article(store, args.id)
    account = config.account(article.account_id or config.plans[0].account)
    preview = publisher.preview(article, account)
    if getattr(args, "html", False):
        print(preview["content_html"])
    else:
        print(f"标题: {preview['title']}")
        print(f"摘要: {preview['digest']}")
        print(f"封面: {preview['cover'] or '（未指定）'}")
        for warning in preview["warnings"]:
            print(f"警告: {warning}")
        print("-" * 60)
        print(preview["content_html"][: int(getattr(args, "chars", 4000))])
        print("-" * 60)
        print("提示: 加 --html 输出完整正文")
    return 0


def cmd_publish(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    plan = _resolve_plan(config, getattr(args, "plan", None))
    account = config.account(plan.account)
    if not getattr(args, "dry_run", False) and (not account.app_id or not account.app_secret):
        raise GzhError(
            f"账号 {account.id} 的凭据未就绪，无法真实发布。"
            f"请先注入环境变量（缺失: {', '.join(config.missing_env) or 'app_id/app_secret'}），"
            f"或先使用 --dry-run 演练。"
        )
    dry_run = bool(getattr(args, "dry_run", False))
    results = publisher.publish(plan, limit=getattr(args, "limit", None), dry_run=dry_run, trigger="cli")
    if not results:
        print("没有需要发布的内容")
        return 0
    rows = []
    for result in results:
        rows.append(
            {
                "标题": result.title[:30],
                "结果": "演练" if result.dry_run else ("成功" if result.ok else "失败"),
                "状态": result.status,
                "publish_id": result.publish_id,
                "article_id": result.article_id_wechat,
                "错误": result.error[:60],
            }
        )
    _print_table(rows, [("标题", "标题"), ("结果", "结果"), ("状态", "状态"), ("publish_id", "publish_id"), ("article_id", "article_id"), ("错误", "错误")])
    failed = [r for r in results if not r.ok and not r.dry_run]
    return 1 if failed else 0


def cmd_approve(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    article = _find_article(store, args.id)
    store.update_article(article.id, status=STATUS_APPROVED, error="")
    store.add_event(
        "INFO",
        "人工审核放行",
        component="approve",
        account_id=article.account_id,
        plan_id=article.plan_id,
        article_id=article.id,
        data={"title": article.title},
    )
    print(f"已放行: {article.title} ({article.id})")
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    print(BANNER)
    print(f"时区: {config.timezone}\n")

    print("[排期]")
    rows = []
    for row in describe_schedule(config):
        rows.append(
            {
                "计划": row["id"],
                "账号": row["account"],
                "模式": row["mode"],
                "触发": f"{row['trigger']}:{row['expression']}",
                "窗口": row["window"] or "不限",
                "状态": "启用" if row["enabled"] else "停用",
                "下次触发": row["next_at"][:16].replace("T", " "),
            }
        )
    _print_table(
        rows,
        [("计划", "计划"), ("账号", "账号"), ("模式", "模式"), ("触发", "触发"), ("窗口", "窗口"), ("状态", "状态"), ("下次触发", "下次触发")],
    )

    print("\n[内容池]")
    stats = store.stats()
    for key in sorted(stats):
        print(f"  - {key}: {stats[key]}")

    print("\n[今日配额]")
    quota_rows = []
    for account in config.accounts.values():
        for mode in ("draft", "publish", "mass"):
            limit = publisher.quota_limit(account, mode)
            used = publisher.quota_used(account, mode)
            quota_rows.append(
                {
                    "账号": account.id,
                    "模式": mode,
                    "已用": used,
                    "上限": limit,
                    "剩余": max(0, limit - used),
                }
            )
    _print_table(quota_rows, [("账号", "账号"), ("模式", "模式"), ("已用", "已用"), ("上限", "上限"), ("剩余", "剩余")])

    print("\n[最近执行]")
    run_rows = []
    for run in store.recent_runs(limit=10):
        run_rows.append(
            {
                "计划": run["plan_id"],
                "模式": run["mode"],
                "触发": run["trigger"],
                "结果": run["status"],
                "发布": run["published"],
                "跳过": run["skipped"],
                "失败": run["failed"],
                "开始": (run["started_at"] or "")[:16].replace("T", " "),
                "错误": (run["error"] or "")[:50],
            }
        )
    _print_table(
        run_rows,
        [("计划", "计划"), ("模式", "模式"), ("触发", "触发"), ("结果", "结果"), ("发布", "发布"), ("跳过", "跳过"), ("失败", "失败"), ("开始", "开始"), ("错误", "错误")],
    )

    print("\n[最近事件]")
    event_rows = []
    for event in store.recent_events(limit=10):
        event_rows.append(
            {
                "时间": (event["ts"] or "")[:19].replace("T", " "),
                "级别": event["level"],
                "组件": event["component"],
                "计划": event["plan_id"],
                "消息": (event["message"] or "")[:60],
            }
        )
    _print_table(event_rows, [("时间", "时间"), ("级别", "级别"), ("组件", "组件"), ("计划", "计划"), ("消息", "消息")])
    return 0


def cmd_plan(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    rows = []
    for row in describe_schedule(config):
        rows.append(
            {
                "计划": row["id"],
                "账号": row["account"],
                "模式": row["mode"],
                "触发方式": row["trigger"],
                "表达式": row["expression"],
                "窗口": row["window"] or "不限",
                "时区": row["timezone"],
                "下次触发": row["next_at"][:19].replace("T", " "),
                "状态": "启用" if row["enabled"] else "停用",
            }
        )
    _print_table(
        rows,
        [("计划", "计划"), ("账号", "账号"), ("模式", "模式"), ("触发方式", "触发方式"), ("表达式", "表达式"), ("窗口", "窗口"), ("时区", "时区"), ("下次触发", "下次触发"), ("状态", "状态")],
    )
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    scheduler = Scheduler(config, publisher, store, logger)
    try:
        with SingleInstanceLock(config.lock_path):
            scheduler.run_forever(interval=int(getattr(args, "interval", 20)), once=bool(getattr(args, "once", False)))
    except RuntimeError as exc:
        print(str(exc))
        return 1
    return 0


def cmd_daemon(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    lock = SingleInstanceLock(config.lock_path)
    if not lock.acquire():
        print(f"已有调度进程在运行（锁文件 {config.lock_path}）")
        return 1
    lock.release()

    pid_file = config.var_dir / "scheduler.pid"
    log_file = config.logs_dir / "daemon.out"
    command = [sys.executable, "-m", "gzh.cli", "run", "--interval", str(int(getattr(args, "interval", 20)))]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(Path(__file__).resolve().parents[1]) + os.pathsep + env.get("PYTHONPATH", "")
    with log_file.open("a", encoding="utf-8") as out:
        process = subprocess.Popen(  # noqa: S603 - 命令由本程序构造
            command,
            stdout=out,
            stderr=out,
            env=env,
            start_new_session=True,
        )
    pid_file.write_text(str(process.pid), encoding="utf-8")
    print(f"调度器已在后台启动：pid={process.pid}")
    print(f"日志: {log_file}")
    print(f"停止: kill {process.pid}")
    return 0


def cmd_logs(args: argparse.Namespace) -> int:
    config = load_config(getattr(args, "root", None))
    log_path = config.logs_dir / "gzh.log"
    if not log_path.exists():
        print(f"日志文件不存在: {log_path}")
        return 1
    lines = log_path.read_text(encoding="utf-8", errors="replace").splitlines()
    tail = lines[-int(getattr(args, "lines", 50)) :]
    for line in tail:
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            print(line)
            continue
        if getattr(args, "level", None) and payload.get("level") != args.level:
            continue
        context = {
            k: v
            for k, v in payload.items()
            if k not in ("ts", "level", "logger", "msg")
        }
        suffix = " " + " ".join(f"{k}={v}" for k, v in context.items()) if context else ""
        print(f"{payload.get('ts')} {payload.get('level'):<5} {payload.get('msg')}{suffix}")
    if getattr(args, "follow", False):
        print("（跟随日志中，Ctrl-C 退出）")
        try:
            with log_path.open("r", encoding="utf-8", errors="replace") as fh:
                fh.seek(0, os.SEEK_END)
                while True:
                    line = fh.readline()
                    if not line:
                        time.sleep(0.5)
                        continue
                    print(line.rstrip())
        except KeyboardInterrupt:
            print()
    return 0


def cmd_retry(args: argparse.Namespace) -> int:
    config, store, publisher, logger = _build(args)
    if getattr(args, "id", None):
        articles = [_find_article(store, args.id)]
    else:
        articles = store.list_articles(status=STATUS_FAILED)
    if not articles:
        print("没有需要重试的文章")
        return 0
    results = []
    for article in articles:
        plan = config.plan(article.plan_id) if article.plan_id else _resolve_plan(config, None)
        account = config.account(article.account_id or plan.account)
        store.update_article(article.id, status="pending")
        article.status = "pending"
        results.append(
            publisher.publish_article(article, plan=plan, account=account, dry_run=False, trigger="retry")
        )
    for result in results:
        mark = "成功" if result.ok else "失败"
        print(f"[{mark}] {result.title} {result.error}")
    return 0 if all(r.ok for r in results) else 1


# ---------------------------------------------------------------------- 解析器
def build_parser() -> argparse.ArgumentParser:
    # 全局选项既可以写在子命令前，也可以写在子命令后
    # （用 SUPPRESS 保证「没写」时不覆盖主解析器已经解析出的值）
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=argparse.SUPPRESS, help="项目根目录")
    common.add_argument(
        "--log-level",
        default=argparse.SUPPRESS,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别",
    )
    common.add_argument("--quiet", action="store_true", default=argparse.SUPPRESS, help="不输出控制台日志")

    parser = argparse.ArgumentParser(
        prog="gzh",
        description="公众号管理 SOP 自动化套件：定时采集、排版并发布指定资源中的内容。",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--version", action="version", version=BANNER)
    parser.add_argument("--root", help="项目根目录（默认自动查找包含 config/ 的目录）")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--quiet", action="store_true", help="不输出控制台日志")

    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init", parents=[common], help="初始化项目结构与示例配置")
    init_parser.add_argument("--force", action="store_true", help="覆盖已存在的示例配置")
    init_parser.set_defaults(func=cmd_init)

    check_parser = subparsers.add_parser("check", parents=[common], help="环境与配置体检")
    check_parser.add_argument("--no-network", action="store_true", help="跳过网络与凭据检查")
    check_parser.set_defaults(func=cmd_check)

    collect_parser = subparsers.add_parser("collect", parents=[common], help="采集内容入池")
    collect_parser.add_argument("--plan", help="只采集指定计划")
    collect_parser.set_defaults(func=cmd_collect)

    list_parser = subparsers.add_parser("list", parents=[common], help="查看内容池")
    list_parser.add_argument("--status", help="按状态过滤（pending/approved/rendered/drafted/published/mass_sent/failed/blocked/skipped/queue）")
    list_parser.add_argument("--plan", help="按计划过滤")
    list_parser.add_argument("--limit", type=int, help="最多显示多少条")
    list_parser.set_defaults(func=cmd_list)

    preview_parser = subparsers.add_parser("preview", parents=[common], help="预览渲染后的正文")
    preview_parser.add_argument("--id", required=True, help="文章 ID 或标题片段")
    preview_parser.add_argument("--html", action="store_true", help="输出完整 HTML")
    preview_parser.add_argument("--chars", type=int, default=4000, help="非 --html 模式下输出的字符数")
    preview_parser.set_defaults(func=cmd_preview)

    publish_parser = subparsers.add_parser("publish", parents=[common], help="立即执行发布")
    publish_parser.add_argument("--plan", help="发布计划 id")
    publish_parser.add_argument("--limit", type=int, help="本次最多发布几篇")
    publish_parser.add_argument("--dry-run", action="store_true", help="演练：只渲染不发布")
    publish_parser.set_defaults(func=cmd_publish)

    approve_parser = subparsers.add_parser("approve", parents=[common], help="人工审核放行")
    approve_parser.add_argument("--id", required=True, help="文章 ID 或标题片段")
    approve_parser.set_defaults(func=cmd_approve)

    status_parser = subparsers.add_parser("status", parents=[common], help="查看整体状态")
    status_parser.set_defaults(func=cmd_status)

    plan_parser = subparsers.add_parser("plan", parents=[common], help="查看排期概览")
    plan_parser.set_defaults(func=cmd_plan)

    run_parser = subparsers.add_parser("run", parents=[common], help="前台运行调度器")
    run_parser.add_argument("--interval", type=int, default=20, help="调度检查间隔（秒）")
    run_parser.add_argument("--once", action="store_true", help="只检查一次就退出")
    run_parser.set_defaults(func=cmd_run)

    daemon_parser = subparsers.add_parser("daemon", parents=[common], help="后台运行调度器")
    daemon_parser.add_argument("--interval", type=int, default=20, help="调度检查间隔（秒）")
    daemon_parser.set_defaults(func=cmd_daemon)

    logs_parser = subparsers.add_parser("logs", parents=[common], help="查看运行日志")
    logs_parser.add_argument("--lines", type=int, default=50, help="显示最近多少行")
    logs_parser.add_argument("--level", help="只显示指定级别（INFO/WARNING/ERROR）")
    logs_parser.add_argument("--follow", action="store_true", help="持续跟随")
    logs_parser.set_defaults(func=cmd_logs)

    retry_parser = subparsers.add_parser("retry", parents=[common], help="重试失败的文章")
    retry_parser.add_argument("--id", help="文章 ID；不填则重试全部失败文章")
    retry_parser.set_defaults(func=cmd_retry)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args) or 0)
    except GzhError as exc:
        print(f"错误: {exc}", file=sys.stderr)
        hint = getattr(exc, "hint", None)
        if callable(hint):
            print(f"建议: {hint()}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("已中断", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
