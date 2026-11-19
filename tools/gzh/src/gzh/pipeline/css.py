"""CSS 内联。

微信公众号正文会剥离 ``<style>`` 标签与外链样式，所有排版必须写成
元素上的 ``style="..."`` 属性。本模块把一份 CSS 规则表应用到 HTML 字符串上。

支持的选择器（够用即可）：

* ``p``            —— 标签选择器
* ``p.gzh-p``      —— 标签 + class
* ``.gzh-img``     —— class 选择器
* ``#cover``       —— id 选择器

同一元素命中多条规则时按出现顺序合并，后面的覆盖前面的。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TAG_RE = re.compile(r"<([A-Za-z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)(/?)>")
ATTR_RE = re.compile(r"([A-Za-z_:][\w:.-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s\"'>]+)")
CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)

#: 公众号通用排版风格（可被 policies.styles 覆盖）。
DEFAULT_CSS = """
p.gzh-p {
    font-size: 16px;
    line-height: 1.8;
    color: #3f3f3f;
    margin: 0 0 18px;
    letter-spacing: 0.5px;
    text-align: justify;
}
h1.gzh-h1 { font-size: 21px; line-height: 1.5; color: #1a1a1a; margin: 28px 0 16px; font-weight: 700; }
h2.gzh-h2 { font-size: 19px; line-height: 1.5; color: #1a1a1a; margin: 26px 0 14px; font-weight: 700; }
h3.gzh-h3 { font-size: 17px; line-height: 1.5; color: #222; margin: 24px 0 12px; font-weight: 600; }
h4.gzh-h4 { font-size: 16px; line-height: 1.5; color: #333; margin: 20px 0 10px; font-weight: 600; }
h5.gzh-h5 { font-size: 15px; line-height: 1.5; color: #444; margin: 18px 0 10px; font-weight: 600; }
h6.gzh-h6 { font-size: 14px; line-height: 1.5; color: #555; margin: 16px 0 8px; }
strong.gzh-strong { font-weight: 700; color: #1a1a1a; }
em.gzh-em { font-style: italic; }
del.gzh-del { text-decoration: line-through; color: #999; }
a.gzh-a { color: #576b95; text-decoration: none; }
blockquote.gzh-quote {
    margin: 18px 0;
    padding: 12px 16px;
    border-left: 3px solid #576b95;
    background: #f7f8fa;
    color: #5a5a5a;
    font-size: 15px;
    line-height: 1.75;
}
ul.gzh-list, ol.gzh-list { margin: 0 0 18px; padding-left: 22px; color: #3f3f3f; font-size: 16px; line-height: 1.8; }
li.gzh-li { margin: 6px 0; }
pre.gzh-pre {
    margin: 16px 0;
    padding: 14px 16px;
    background: #f6f8fa;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 13px;
    line-height: 1.6;
}
code.gzh-code { font-family: Menlo, Consolas, monospace; color: #24292e; white-space: pre-wrap; }
code.gzh-inline-code {
    font-family: Menlo, Consolas, monospace;
    font-size: 14px;
    background: #f2f3f5;
    color: #c7254e;
    padding: 2px 5px;
    border-radius: 3px;
}
img.gzh-img { max-width: 100%; height: auto; display: block; margin: 16px auto; border-radius: 4px; }
table.gzh-table { width: 100%; border-collapse: collapse; margin: 16px 0; font-size: 14px; }
th.gzh-th { background: #f7f8fa; font-weight: 600; }
th.gzh-th, td.gzh-td { border: 1px solid #e5e6eb; padding: 8px 10px; text-align: left; }
hr.gzh-hr { border: none; border-top: 1px solid #e5e6eb; margin: 26px 0; }
section.gzh-section { margin: 0 0 18px; }
"""


@dataclass
class CssRule:
    """一条 CSS 规则。"""

    selector: str
    declarations: dict[str, str] = field(default_factory=dict)
    specificity: tuple[int, int, int] = (0, 0, 0)

    def matches(self, tag: str, attrs: dict[str, str]) -> bool:
        """判断该规则是否命中元素。"""
        selector = self.selector.strip()
        if not selector:
            return False
        # 只取第一个简单选择器（逗号分隔的多个选择器已在上游拆分）
        parts = re.findall(r"[.#]?[A-Za-z0-9_-]+", selector)
        if not parts:
            return False
        for part in parts:
            if part.startswith("."):
                classes = set((attrs.get("class") or "").split())
                if part[1:] not in classes:
                    return False
            elif part.startswith("#"):
                if attrs.get("id") != part[1:]:
                    return False
            else:
                if tag.lower() != part.lower():
                    return False
        return True


def parse_css(css_text: str) -> list[CssRule]:
    """解析 CSS 文本为规则列表。"""
    rules: list[CssRule] = []
    for match in CSS_RULE_RE.finditer(css_text or ""):
        selector_text = match.group(1).strip()
        body = match.group(2)
        declarations: dict[str, str] = {}
        for declaration in body.split(";"):
            if ":" not in declaration:
                continue
            name, _, value = declaration.partition(":")
            name = name.strip().lower()
            value = value.strip()
            if name and value:
                declarations[name] = value
        for selector in selector_text.split(","):
            selector = selector.strip()
            if not selector:
                continue
            rules.append(
                CssRule(
                    selector=selector,
                    declarations=declarations,
                    specificity=_specificity(selector),
                )
            )
    return rules


def _specificity(selector: str) -> tuple[int, int, int]:
    ids = selector.count("#")
    classes = selector.count(".")
    tags = len([p for p in re.findall(r"(^|\s|>)\s*([A-Za-z][\w-]*)", selector) if p[1]])
    return (ids, classes, tags)


def _parse_attributes(raw: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    for match in ATTR_RE.finditer(raw or ""):
        name = match.group(1).lower()
        value = match.group(2)
        if value[:1] in ("\"", "'") and value[-1:] == value[:1]:
            value = value[1:-1]
        attrs[name] = value
    return attrs


def _render_style(declarations: dict[str, str]) -> str:
    return "; ".join(f"{name}: {value}" for name, value in declarations.items())


def inline_css(html: str, css_text: str = DEFAULT_CSS) -> str:
    """把 CSS 规则内联到 HTML 元素上。

    Args:
        html: HTML 片段。
        css_text: CSS 文本；为空时使用内置默认样式。

    Returns:
        内联样式后的 HTML。
    """
    rules = parse_css(css_text or DEFAULT_CSS)
    if not rules:
        return html

    def replace(match: re.Match[str]) -> str:
        tag = match.group(1)
        raw_attrs = match.group(2)
        self_closing = match.group(3)
        attrs = _parse_attributes(raw_attrs)

        matched = [rule for rule in rules if rule.matches(tag, attrs)]
        if not matched:
            return match.group(0)

        merged: dict[str, str] = {}
        existing = attrs.get("style", "")
        for declaration in existing.split(";"):
            if ":" in declaration:
                name, _, value = declaration.partition(":")
                merged[name.strip().lower()] = value.strip()

        for rule in sorted(matched, key=lambda r: r.specificity):
            merged.update(rule.declarations)

        style_attr = _render_style(merged)
        new_attrs = raw_attrs
        if re.search(r"\sstyle\s*=", raw_attrs, re.IGNORECASE):
            new_attrs = re.sub(
                r"\sstyle\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)",
                f' style="{style_attr}"',
                raw_attrs,
                flags=re.IGNORECASE,
            )
        else:
            new_attrs = f'{raw_attrs} style="{style_attr}"'
        return f"<{tag}{new_attrs}{self_closing}>"

    return TAG_RE.sub(replace, html or "")
