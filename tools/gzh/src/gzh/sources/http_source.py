"""HTTP 抓取内容源。

适用于「一个列表页 → 若干篇详情页」的场景，例如公司内部资讯页、
竞品专栏页。配置示例：

```json
{
  "type": "http",
  "url": "https://example.com/blog",
  "selector": {
    "item": "article.post",
    "title": "h2",
    "link": "a",
    "content": { "tag": "div", "class": "post-content" }
  },
  "limit": 5
}
```

若列表页本身就是一篇文章，可用 ``"single": true`` 直接抓当前页。
"""

from __future__ import annotations

from typing import Any

from ..errors import SourceError
from ..models import Article
from .base import Source
from .htmlutil import (
    absolute_url,
    clean_text,
    element_title,
    first_link,
    select_elements,
    select_first,
)

DEFAULT_ITEM_SELECTOR = "article"


class HttpSource(Source):
    """网页抓取源。"""

    type = "http"

    def fetch(self) -> list[Article]:
        url = str(self.spec.get("url") or "")
        if not url:
            raise SourceError("http 源必须提供 url")
        if self.http is None:
            raise SourceError("http 源需要 HTTP 客户端")

        response = self.http.request(
            "GET", url, headers={"Accept": "text/html,application/xhtml+xml,application/json,*/*"}
        )
        content_type = (response.headers.get("content-type") or "").lower()

        # 页面其实是 JSON → 交给 JSON Feed 处理
        if "json" in content_type or response.text().lstrip()[:1] in ("{", "["):
            from .jsonfeed import JsonFeedSource

            feeder = JsonFeedSource(self.spec, roots=self.roots, http=self.http, logger=self.logger)
            return feeder.fetch()

        if self.spec.get("single"):
            return self._single_article(url, response.text())

        selector = self.spec.get("selector") or {}
        item_selector = str(selector.get("item") or DEFAULT_ITEM_SELECTOR)
        items = select_elements(response.text(), item_selector)
        if not items and item_selector != DEFAULT_ITEM_SELECTOR:
            items = select_elements(response.text(), DEFAULT_ITEM_SELECTOR)
        if not items:
            raise SourceError(
                f"未从 {url} 解析到任何条目（选择器 item={item_selector}），请调整 source.selector 配置"
            )

        limit = int(self.spec.get("limit", 5))
        articles: list[Article] = []
        for item in items[:limit]:
            article = self._item_to_article(item, url, selector)
            if article:
                articles.append(article)
        return articles

    # ------------------------------------------------------------------ 条目
    def _item_to_article(self, item: Any, base_url: str, selector: dict[str, Any]) -> Article | None:
        title_selector = str(selector.get("title") or "h1,h2,h3,a")
        title = element_title(item.inner, tuple(s.strip() for s in title_selector.split(",") if s.strip()))
        if not title:
            title = element_title(item.outer)
        link_selector = str(selector.get("link") or "a")
        href = first_link(item.inner, link_selector) or first_link(item.outer, link_selector)
        link = absolute_url(base_url, href)

        if not title and not link:
            return None

        content_html = ""
        if link and not self.spec.get("no_fetch"):
            content_html = self._fetch_content(link, selector.get("content"))

        return Article(
            title=title or link or "(无标题)",
            source_type=self.type,
            source_key=link or title,
            digest=clean_text(item.text())[:200],
            source_html=content_html,
            source_url=link,
            content_source_url=link,
        )

    def _fetch_content(self, url: str, content_selector: Any) -> str:
        try:
            response = self.http.request("GET", url, headers={"Accept": "text/html,*/*"})
        except Exception as exc:  # noqa: BLE001 - 单篇抓取失败不影响其它条目
            if self.logger:
                self.logger.warning(
                    "详情页抓取失败",
                    extra={"context": {"url": url, "error": str(exc)}},
                )
            return ""
        html = response.text()

        if content_selector:
            selector_text = (
                content_selector
                if isinstance(content_selector, str)
                else f"{content_selector.get('tag', '')}.{content_selector.get('class', '')}".strip(".")
            )
            element = select_first(html, selector_text)
            if element is not None:
                return element.inner

        for selector_text in ("article", "main", "body"):
            element = select_first(html, selector_text)
            if element is not None and element.inner.strip():
                return element.inner
        return html

    # ------------------------------------------------------------------ 单篇
    def _single_article(self, url: str, html: str) -> list[Article]:
        title = element_title(html)
        content_html = ""
        for selector_text in ("article", "main", "body"):
            element = select_first(html, selector_text)
            if element is not None and element.inner.strip():
                content_html = element.inner
                break
        if not content_html:
            content_html = html
        if not title:
            title = url
        return [
            Article(
                title=title,
                source_type=self.type,
                source_key=url,
                digest=clean_text(content_html)[:200],
                source_html=content_html,
                source_url=url,
                content_source_url=url,
            )
        ]
