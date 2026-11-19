"""RSS / Atom 订阅源。

用标准库 ``xml.etree`` 解析，兼容 RSS 2.0、Atom 1.0 以及常见的
``content:encoded`` 扩展。条目正文若是 HTML 则走 HTML 渲染通道，
纯文本则转成段落 Markdown。
"""

from __future__ import annotations

import re
from typing import Any
from xml.etree import ElementTree

from ..errors import SourceError
from ..models import Article
from .base import Source

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def _text(element: ElementTree.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _strip_html(html: str) -> str:
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class RssSource(Source):
    """RSS/Atom 订阅源。"""

    type = "rss"

    def fetch(self) -> list[Article]:
        url = str(self.spec.get("url") or "")
        if not url:
            raise SourceError("rss 源必须提供 url")
        if self.http is None:
            raise SourceError("rss 源需要 HTTP 客户端")

        response = self.http.request("GET", url, headers={"Accept": "application/rss+xml, application/xml, text/xml, */*"})
        payload = response.text()
        try:
            root = ElementTree.fromstring(payload)
        except ElementTree.ParseError as exc:
            raise SourceError(f"订阅源解析失败 {url}: {exc}") from exc

        items = self._extract_items(root)
        limit = int(self.spec.get("limit", 20))
        articles: list[Article] = []
        for item in items[:limit]:
            article = self._to_article(item)
            if article:
                articles.append(article)
        return articles

    def _extract_items(self, root: ElementTree.Element) -> list[ElementTree.Element]:
        tag = root.tag.split("}")[-1].lower()
        if tag == "rss":
            channel = root.find("channel")
            if channel is not None:
                return channel.findall("item")
            return []
        if tag == "feed":
            return root.findall("atom:entry", NS) or root.findall("entry")
        if tag == "rdf":
            return root.findall(".//item")
        # 兜底：找所有 item/entry
        return root.findall(".//item") or root.findall(".//entry")

    def _to_article(self, item: ElementTree.Element) -> Article | None:
        title = _text(item.find("title"))
        link = _text(item.find("link"))
        if not link:
            atom_link = item.find("atom:link", NS)
            if atom_link is not None:
                link = atom_link.get("href", "")
        guid = _text(item.find("guid")) or _text(item.find("atom:id", NS)) or link
        if not title and not link:
            return None

        content_html = _text(item.find("content:encoded", NS))
        if not content_html:
            description = _text(item.find("description"))
            if "<" in description and ">" in description:
                content_html = description
            else:
                description = description or _text(item.find("atom:summary", NS))
                content_html = ""
                plain = _strip_html(description)
                if plain:
                    content_html = "<p>" + plain.replace("\n\n", "</p><p>").replace("\n", "<br />") + "</p>"

        summary = _text(item.find("atom:summary", NS)) or _strip_html(content_html)[:200]

        categories = [
            _text(cat)
            for cat in item.findall("category")
            if _text(cat)
        ]

        author = _text(item.find("dc:creator", NS)) or _text(item.find("author"))

        return Article(
            title=title or "(无标题)",
            source_type=self.type,
            source_key=guid or link,
            author=author,
            digest=_strip_html(summary)[:200],
            source_html=content_html,
            source_url=link,
            content_source_url=link,
            tags=categories,
        )
