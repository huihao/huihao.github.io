"""JSON Feed 内容源。

兼容三种常见形态：

1. 标准 JSON Feed 1.1：``{"items": [...]}``
2. 通用博客 API：``{"articles": [...]}`` / ``{"posts": [...]}`` / ``{"data": [...]}``
3. 裸数组：``[ {...}, {...} ]``

字段缺失时按「标题 + 摘要 + 正文」的常见命名做兼容映射。
"""

from __future__ import annotations

from typing import Any

from ..errors import SourceError
from ..models import Article
from .base import Source

LIST_KEYS = ("items", "articles", "posts", "entries", "data", "list", "results")

TITLE_KEYS = ("title", "name", "headline")
BODY_KEYS = ("content_html", "html", "content", "body", "body_html", "raw_html")
TEXT_KEYS = ("content_text", "text", "body_text", "plain")
SUMMARY_KEYS = ("summary", "digest", "excerpt", "description", "subtitle")
LINK_KEYS = ("url", "link", "permalink", "href")
DATE_KEYS = ("date_published", "published", "date", "created_at", "pubDate")
TAG_KEYS = ("tags", "categories", "keywords")
ID_KEYS = ("id", "guid", "uuid")


def _pick(data: dict[str, Any], keys: tuple[str, ...], default: Any = "") -> Any:
    for key in keys:
        if key in data and data[key] not in (None, ""):
            return data[key]
    return default


class JsonFeedSource(Source):
    """JSON Feed / 通用 JSON 列表源。"""

    type = "jsonfeed"

    def fetch(self) -> list[Article]:
        url = str(self.spec.get("url") or "")
        if not url:
            raise SourceError("jsonfeed 源必须提供 url")
        if self.http is None:
            raise SourceError("jsonfeed 源需要 HTTP 客户端")

        payload = self.http.get_json(url)
        items = self._extract_items(payload)
        limit = int(self.spec.get("limit", 20))
        articles: list[Article] = []
        for item in items[:limit]:
            if not isinstance(item, dict):
                continue
            article = self._to_article(item)
            if article:
                articles.append(article)
        return articles

    def _extract_items(self, payload: Any) -> list[Any]:
        if isinstance(payload, list):
            return payload
        if isinstance(payload, dict):
            for key in LIST_KEYS:
                value = payload.get(key)
                if isinstance(value, list):
                    return value
            # 单篇文章对象
            if any(key in payload for key in TITLE_KEYS):
                return [payload]
        raise SourceError("JSON 响应中找不到条目列表（期望 items/articles/posts/data 之一）")

    def _to_article(self, item: dict[str, Any]) -> Article | None:
        title = str(_pick(item, TITLE_KEYS)).strip()
        link = str(_pick(item, LINK_KEYS)).strip()
        if not title and not link:
            return None

        html = str(_pick(item, BODY_KEYS)).strip()
        if not html:
            text = str(_pick(item, TEXT_KEYS)).strip()
            if text:
                html = "<p>" + text.replace("\n\n", "</p><p>").replace("\n", "<br />") + "</p>"

        summary = str(_pick(item, SUMMARY_KEYS)).strip()

        tags_value = _pick(item, TAG_KEYS, [])
        if isinstance(tags_value, str):
            tags = [t.strip() for t in tags_value.replace("，", ",").split(",") if t.strip()]
        elif isinstance(tags_value, list):
            tags = [str(t).strip() for t in tags_value if str(t).strip()]
        else:
            tags = []

        author = ""
        author_value = item.get("author")
        if isinstance(author_value, dict):
            author = str(author_value.get("name") or "")
        elif author_value:
            author = str(author_value)

        identifier = str(_pick(item, ID_KEYS)) or link or title

        return Article(
            title=title or "(无标题)",
            source_type=self.type,
            source_key=identifier,
            author=author,
            digest=summary[:200],
            source_html=html,
            source_url=link,
            content_source_url=link,
            tags=tags,
            publish_at=str(_pick(item, DATE_KEYS)),
        )
