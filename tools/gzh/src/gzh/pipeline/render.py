"""渲染层：把 :class:`~gzh.models.Article` 变成可直接投喂微信接口的稿件。

流程：

    Markdown/HTML → 内联样式 → 清洗 → 图片转存 → 生成摘要 → 封面素材

输出 :class:`RenderedArticle`，其中 ``payload`` 可直接作为 ``draft/add`` 的
articles 元素。
"""

from __future__ import annotations

import hashlib
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from ..config import Account
from ..errors import RenderError
from ..models import Article
from .css import DEFAULT_CSS, inline_css
from .images import ImageUploader
from .markdown import build_article_payload, make_digest, markdown_to_html
from .sanitize import sanitize_html


@dataclass
class RenderedArticle:
    """渲染结果。"""

    title: str
    digest: str
    content_html: str
    thumb_media_id: str = ""
    cover_url: str = ""
    warnings: list[str] = field(default_factory=list)
    payload: dict[str, Any] = field(default_factory=dict)


def make_placeholder_png(width: int = 900, height: int = 383, rgb: tuple[int, int, int] = (31, 41, 55)) -> bytes:
    """生成一张纯色占位封面 PNG（无需第三方库）。"""
    raw = bytearray()
    for _ in range(height):
        raw.append(0)  # filter type 0
        for _ in range(width):
            raw.extend(rgb)

    def chunk(tag: bytes, data: bytes) -> bytes:
        return (
            struct.pack(">I", len(data))
            + tag
            + data
            + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


class Renderer:
    """内容渲染器。"""

    def __init__(
        self,
        *,
        client: object,
        store: object,
        logger: object = None,
        http: object = None,
        css_text: str = DEFAULT_CSS,
        digest_max_length: int = 120,
        content_roots: Iterable[Path] = (),
        upload_remote_images: bool = True,
        allow_missing_cover: bool = False,
    ) -> None:
        self.client = client
        self.store = store
        self.logger = logger
        self.http = http
        self.css_text = css_text or DEFAULT_CSS
        self.digest_max_length = digest_max_length
        self.content_roots = [Path(p) for p in content_roots]
        self.upload_remote_images = upload_remote_images
        self.allow_missing_cover = allow_missing_cover

    # ------------------------------------------------------------------ 正文
    def render_content(self, article: Article) -> tuple[str, list[str]]:
        """生成正文 HTML（含图片转存，会调用微信上传接口）。"""
        warnings: list[str] = []

        if article.source_html.strip():
            html = article.source_html
        elif article.markdown.strip():
            html = markdown_to_html(article.markdown)
        else:
            raise RenderError(f"文章《{article.title}》既没有 Markdown 也没有 HTML 正文")

        html = inline_css(html, self.css_text)
        html = sanitize_html(html)

        uploader = ImageUploader(
            client=self.client,
            store=self.store,
            logger=self.logger,
            http=self.http,
            content_roots=self.content_roots,
            upload_remote=self.upload_remote_images,
        )
        html = uploader.process(html)
        return html, warnings

    def render_content_only(self, article: Article) -> RenderedArticle:
        """只做排版与清洗，不触碰任何微信接口（dry-run 用）。"""
        if article.source_html.strip():
            html = article.source_html
        elif article.markdown.strip():
            html = markdown_to_html(article.markdown)
        else:
            raise RenderError(f"文章《{article.title}》既没有 Markdown 也没有 HTML 正文")

        html = inline_css(html, self.css_text)
        html = sanitize_html(html)
        digest = (article.digest or "").strip() or make_digest(html, self.digest_max_length)
        return RenderedArticle(
            title=article.title,
            digest=digest,
            content_html=html,
            warnings=["dry-run 模式：未上传图片与封面，未真实发布"],
        )

    # ------------------------------------------------------------------ 封面
    def _resolve_cover(self, article: Article, account: Account) -> Path | None:
        candidates = [article.cover, account.cover]
        for candidate in candidates:
            if not candidate:
                continue
            path = Path(candidate)
            if path.is_absolute() and path.is_file():
                return path
            for root in self.content_roots:
                resolved = root / candidate
                if resolved.is_file():
                    return resolved
        return None

    def ensure_cover(self, article: Article, account: Account) -> tuple[str, str, list[str]]:
        """确保封面素材存在，返回 (thumb_media_id, cover_url, warnings)。"""
        warnings: list[str] = []
        cover_path = self._resolve_cover(article, account)

        if cover_path is None:
            if not self.allow_missing_cover:
                raise RenderError(
                    f"文章《{article.title}》缺少封面图。"
                    f"请在 front matter 里设置 cover，或在账号配置里配置默认封面。"
                )
            warnings.append("未找到封面，已生成占位封面，请尽快补齐封面素材")
            import tempfile

            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(make_placeholder_png())
                placeholder = Path(tmp.name)
            try:
                result = self.client.upload_thumb(placeholder)
            finally:
                placeholder.unlink(missing_ok=True)
            return result["media_id"], result.get("url", ""), warnings

        content = cover_path.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        cached = self.store.get_blob("thumb", digest)
        if cached and cached.get("remote_id"):
            return cached["remote_id"], cached.get("url", ""), warnings

        result = self.client.upload_thumb(cover_path)
        self.store.put_blob(
            "thumb",
            digest,
            remote_id=result["media_id"],
            url=result.get("url", ""),
            meta={"name": cover_path.name},
        )
        if self.logger:
            self.logger.info(
                "封面素材已上传",
                extra={"context": {"cover": cover_path.name, "media_id": result["media_id"]}},
            )
        return result["media_id"], result.get("url", ""), warnings

    # ------------------------------------------------------------------ 入口
    def render(self, article: Article, account: Account) -> RenderedArticle:
        """渲染文章，产出可直接提交给微信的稿件。"""
        content_html, warnings = self.render_content(article)
        digest = (article.digest or "").strip() or make_digest(content_html, self.digest_max_length)
        thumb_media_id, cover_url, cover_warnings = self.ensure_cover(article, account)
        warnings.extend(cover_warnings)

        payload = build_article_payload(
            title=article.title,
            digest=digest,
            content_html=content_html,
            thumb_media_id=thumb_media_id,
            author=article.author or account.author,
            content_source_url=article.content_source_url or account.content_source_url,
            need_open_comment=article.need_open_comment or account.need_open_comment,
            only_fans_can_comment=article.only_fans_can_comment or account.only_fans_can_comment,
        )

        return RenderedArticle(
            title=article.title,
            digest=digest,
            content_html=content_html,
            thumb_media_id=thumb_media_id,
            cover_url=cover_url,
            warnings=warnings,
            payload=payload,
        )
