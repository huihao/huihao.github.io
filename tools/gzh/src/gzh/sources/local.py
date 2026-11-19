"""本地内容资源库。

约定：内容目录下递归扫描 ``*.md``（Markdown + front matter）与 ``*.html``。

front matter 示例::

    ---
    title: "标题"
    author: 张三
    digest: 一句话摘要
    cover: images/cover.png
    tags: [AI, 效率]
    source_url: https://example.com/original
    publish_at: 2026-11-06T08:00
    need_open_comment: 0
    only_fans_can_comment: 0
    ---
    正文……
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..errors import SourceError
from ..models import Article
from ..pipeline.frontmatter import split_front_matter
from .base import Source

MARKDOWN_SUFFIXES = {".md", ".markdown", ".mdown"}
HTML_SUFFIXES = {".html", ".htm"}

#: front matter 中作为 Article 一级字段的键。
KNOWN_KEYS = {
    "title",
    "author",
    "digest",
    "cover",
    "tags",
    "source_url",
    "content_source_url",
    "publish_at",
    "need_open_comment",
    "only_fans_can_comment",
}


class LocalSource(Source):
    """扫描本地目录，产出待发布文章。"""

    type = "local"

    def fetch(self) -> list[Article]:
        raw_path = self.spec.get("path", "")
        base = self.resolve_path(raw_path) if raw_path else None
        if base is None:
            raise SourceError(f"本地内容目录不存在或无法解析: {raw_path}")
        if base.is_file():
            files = [base]
        else:
            files = sorted(
                p for p in base.rglob("*")
                if p.is_file() and p.suffix.lower() in MARKDOWN_SUFFIXES | HTML_SUFFIXES
            )
        if not self.spec.get("recursive", True):
            files = [p for p in files if p.parent == base]

        articles: list[Article] = []
        for path in files:
            try:
                article = self._load(path, base)
            except SourceError:
                raise
            except Exception as exc:  # noqa: BLE001
                if self.logger:
                    self.logger.warning(
                        "跳过无法解析的文件",
                        extra={"context": {"file": str(path), "error": str(exc)}},
                    )
                continue
            if article:
                articles.append(article)
        return articles

    def _load(self, path: Path, base: Path) -> Article | None:
        try:
            raw = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raw = path.read_text(encoding="utf-8", errors="replace")

        try:
            relative = str(path.relative_to(base))
        except ValueError:
            relative = path.name

        meta: dict[str, Any] = {}
        body = raw
        if path.suffix.lower() in MARKDOWN_SUFFIXES:
            meta, body = split_front_matter(raw)
        else:
            meta = {}

        title = str(meta.get("title") or "").strip()
        if not title:
            title = self._derive_title(body) or path.stem

        if path.suffix.lower() in HTML_SUFFIXES:
            source_html = body
            markdown = ""
        else:
            source_html = ""
            markdown = body.strip()

        if not markdown and not source_html:
            return None

        cover = str(meta.get("cover") or "").strip()
        if cover and not Path(cover).is_absolute():
            candidate = (path.parent / cover)
            if candidate.is_file():
                cover = str(candidate)
            else:
                resolved = self.resolve_path(cover)
                cover = str(resolved) if resolved else cover

        tags = meta.get("tags") or []
        if isinstance(tags, str):
            tags = [t.strip() for t in tags.replace("，", ",").split(",") if t.strip()]
        elif isinstance(tags, (list, tuple)):
            tags = [str(t).strip() for t in tags if str(t).strip()]

        extra = {k: v for k, v in meta.items() if k not in KNOWN_KEYS}

        return Article(
            title=title,
            source_type=self.type,
            source_key=relative,
            author=str(meta.get("author") or ""),
            digest=str(meta.get("digest") or ""),
            markdown=markdown,
            source_html=source_html,
            cover=cover,
            tags=list(tags),
            source_url=str(meta.get("source_url") or ""),
            content_source_url=str(meta.get("content_source_url") or meta.get("source_url") or ""),
            publish_at=str(meta.get("publish_at") or ""),
            need_open_comment=int(meta.get("need_open_comment") or 0),
            only_fans_can_comment=int(meta.get("only_fans_can_comment") or 0),
            extra=extra,
        )

    @staticmethod
    def _derive_title(body: str) -> str:
        for line in body.splitlines():
            stripped = line.strip()
            if stripped.startswith("#"):
                return stripped.lstrip("#").strip()
            if stripped:
                break
        return ""
