"""轻量 HTML 解析工具（仅标准库）。

用于「网页列表 → 文章」类内容源：从列表页里切出条目块，再从条目里
取标题与链接，最后从详情页里切出正文。足够覆盖常见的博客/资讯列表页，
又不必引入 lxml/bs4 之类的第三方依赖。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

TAG_RE = re.compile(r"<(/?)([A-Za-z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)(/?)>", re.DOTALL)
ATTR_RE = re.compile(r"([A-Za-z_:][\w:.-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s\"'>]+)")
HREF_RE = re.compile(r"""href\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE)
TEXT_RE = re.compile(r"(?s)<[^>]+>")

#: 不需要闭合标签的 void 元素。
VOID_TAGS = {
    "area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
    "param", "source", "track", "wbr",
}


@dataclass
class Element:
    """一个 HTML 元素。"""

    tag: str
    attrs: dict[str, str]
    inner: str
    outer: str

    def text(self) -> str:
        return clean_text(self.inner)

    def has_class(self, name: str) -> bool:
        return name in (self.attrs.get("class") or "").split()


def parse_attributes(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(raw or ""):
        name = match.group(1).lower()
        value = match.group(2)
        if value[:1] in ("\"", "'") and value[-1:] == value[:1]:
            value = value[1:-1]
        attrs[name] = value
    return attrs


def parse_elements(html: str) -> list[Element]:
    """把 HTML 解析成元素列表（按结束顺序）。"""
    elements: list[Element] = []
    # 栈元素：(标签名, 开标签结束位置, 开标签起始位置, 属性)
    stack: list[tuple[str, int, int, dict[str, str]]] = []

    for match in TAG_RE.finditer(html or ""):
        closing, name, raw_attrs, self_closing = match.groups()
        tag = name.lower()
        if closing:
            for position in range(len(stack) - 1, -1, -1):
                if stack[position][0] == tag:
                    open_tag, content_start, open_start, attrs = stack[position]
                    inner = html[content_start : match.start()]
                    elements.append(
                        Element(
                            tag=open_tag,
                            attrs=attrs,
                            inner=inner,
                            outer=html[open_start : match.end()],
                        )
                    )
                    del stack[position:]
                    break
            continue
        if self_closing or tag in VOID_TAGS:
            elements.append(
                Element(tag=tag, attrs=parse_attributes(raw_attrs), inner="", outer=match.group(0))
            )
            continue
        stack.append((tag, match.end(), match.start(), parse_attributes(raw_attrs)))
    return elements


def clean_text(html: str) -> str:
    """HTML → 纯文本。"""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|li|h[1-6]|tr|blockquote)>", "\n", text)
    text = TEXT_RE.sub("", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
        .replace("&#34;", '"')
    )
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def matches_selector(element: Element, selector: str) -> bool:
    """判断元素是否命中简单选择器：``tag`` / ``.class`` / ``tag.class`` / ``#id``。"""
    selector = (selector or "").strip()
    if not selector:
        return False
    parts = re.findall(r"[.#]?[A-Za-z0-9_-]+", selector)
    if not parts:
        return False
    for part in parts:
        if part.startswith("."):
            if not element.has_class(part[1:]):
                return False
        elif part.startswith("#"):
            if element.attrs.get("id") != part[1:]:
                return False
        else:
            if element.tag != part.lower():
                return False
    return True


def select_elements(html: str, selector: str, *, limit: int | None = None) -> list[Element]:
    """选出命中选择器的元素（取最外层，避免父子重复）。"""
    matches = [el for el in parse_elements(html) if matches_selector(el, selector)]
    if limit:
        matches = matches[:limit]
    return matches


def select_first(html: str, selector: str) -> Element | None:
    elements = select_elements(html, selector, limit=1)
    return elements[0] if elements else None


def first_link(html: str, selector: str = "a") -> str:
    """取第一个链接。"""
    element = select_first(html, selector)
    if element is None:
        return ""
    match = HREF_RE.search(element.outer)
    if not match:
        return ""
    return next((g for g in match.groups() if g), "")


def element_title(html: str, selectors: tuple[str, ...] = ("h1", "h2", "h3", "h4", "a", "title")) -> str:
    """按优先级从 HTML 中取标题文本。"""
    for selector in selectors:
        element = select_first(html, selector)
        if element is not None:
            text = element.text()
            if text:
                return text
    return ""


def absolute_url(base: str, target: str) -> str:
    """把相对链接补全为绝对地址。"""
    if not target:
        return ""
    if target.startswith(("http://", "https://", "//")):
        return target
    from urllib.parse import urljoin

    return urljoin(base, target)
