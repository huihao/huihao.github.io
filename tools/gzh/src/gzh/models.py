"""领域模型。

``Article`` 是贯穿「内容源 → 流水线 → 发布器 → 存储」的唯一载体。
"""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from typing import Any

#: 文章在存储中的状态机（DB 中 articles.status）。
STATUS_PENDING = "pending"          # 已入池，等待排期发布
STATUS_APPROVED = "approved"        # 人工审核放行
STATUS_RENDERED = "rendered"        # 已渲染出公众号 HTML，待发布
STATUS_DRAFTED = "drafted"          # 已进入公众号草稿箱
STATUS_PUBLISHED = "published"      # 已通过发布能力发布
STATUS_MASS_SENT = "mass_sent"      # 已群发
STATUS_FAILED = "failed"            # 失败，可重试
STATUS_SKIPPED = "skipped"          # 主动跳过（如窗口期外、配额耗尽）
STATUS_BLOCKED = "blocked"          # 命中合规/审核门禁，等待人工处理

ALL_STATUSES = (
    STATUS_PENDING,
    STATUS_APPROVED,
    STATUS_RENDERED,
    STATUS_DRAFTED,
    STATUS_PUBLISHED,
    STATUS_MASS_SENT,
    STATUS_FAILED,
    STATUS_SKIPPED,
    STATUS_BLOCKED,
)

#: 终态：不再参与自动发布。
TERMINAL_STATUSES = (STATUS_PUBLISHED, STATUS_MASS_SENT, STATUS_SKIPPED)


def content_hash(*parts: str) -> str:
    """按内容计算稳定指纹，用于跨源去重与幂等。"""
    h = hashlib.sha256()
    for part in parts:
        h.update((part or "").strip().encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


@dataclass
class Article:
    """一篇待发布的内容。

    Attributes:
        title: 公众号标题。
        author: 作者署名。
        digest: 摘要（留空时由正文自动截取）。
        markdown: 原始 Markdown 正文（HTML 源可为空）。
        source_html: 原始 HTML 正文（HTML 源走这条路，跳过 Markdown 转换）。
        cover: 封面图本地路径或远程 URL。
        tags: 标签，用于选稿过滤。
        source_url: 原文链接（写进 content_source_url）。
        source_type: 来源类型：local/rss/jsonfeed/http。
        source_key: 来源内唯一键（文件路径、条目 GUID 等）。
        plan_id: 归属的发布计划。
        account_id: 目标账号。
        extra: 其它透传字段（front matter 里的自定义键）。
    """

    title: str
    source_type: str = "local"
    source_key: str = ""
    plan_id: str = ""
    account_id: str = ""
    author: str = ""
    digest: str = ""
    markdown: str = ""
    source_html: str = ""
    cover: str = ""
    tags: list[str] = field(default_factory=list)
    source_url: str = ""
    publish_at: str = ""
    need_open_comment: int = 0
    only_fans_can_comment: int = 0
    content_source_url: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    id: str = field(default_factory=lambda: uuid.uuid4().hex)
    status: str = STATUS_PENDING
    content_hash: str = ""
    content_html: str = ""
    thumb_media_id: str = ""
    media_id: str = ""
    publish_id: str = ""
    article_id: str = ""
    error: str = ""
    attempts: int = 0
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if not self.content_hash:
            self.content_hash = content_hash(
                self.title,
                self.source_key or self.source_url,
                self.body_text,
            )

    @property
    def body_text(self) -> str:
        """正文纯文本，用于摘要截取与查重。"""
        return _strip_html(self.source_html) or self.markdown


@dataclass
class PublishResult:
    """一次发布动作的结果。"""

    plan_id: str
    article_id: str
    title: str
    status: str
    mode: str
    ok: bool = False
    media_id: str = ""
    publish_id: str = ""
    article_id_wechat: str = ""
    error: str = ""
    dry_run: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "plan_id": self.plan_id,
            "article_id": self.article_id,
            "title": self.title,
            "status": self.status,
            "mode": self.mode,
            "ok": self.ok,
            "media_id": self.media_id,
            "publish_id": self.publish_id,
            "wechat_article_id": self.article_id_wechat,
            "error": self.error,
            "dry_run": self.dry_run,
        }


def _strip_html(html: str) -> str:
    """粗略去标签，用于摘要与指纹计算。"""
    if not html:
        return ""
    import re

    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    return re.sub(r"\s+", " ", text).strip()
