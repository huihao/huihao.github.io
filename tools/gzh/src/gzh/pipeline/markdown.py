"""Markdown → HTML 转换（自研迷你实现）。

只依赖标准库，覆盖公众号写作常用语法：

* ATX 标题（``#`` ~ ``######``）
* 有序/无序列表（含嵌套）
* 引用块、分割线、围栏代码块、缩进代码块
* GFM 表格
* 行内：粗体、斜体、删除线、行内代码、链接、图片、自动链接
* 允许的原生 HTML 标签原样保留（白名单机制），其余一律转义

输出是**语义化 HTML**（带 class），样式由 :mod:`gzh.pipeline.css` 统一内联。
"""

from __future__ import annotations

import html as html_lib
import re
from typing import Any

#: 允许在 Markdown 中原样保留的 HTML 标签（微信兼容白名单）。
ALLOWED_RAW_TAGS = {
    "a", "b", "big", "blockquote", "br", "caption", "center", "code", "col",
    "colgroup", "dd", "div", "em", "figcaption", "figure", "font", "h1", "h2",
    "h3", "h4", "h5", "h6", "hr", "i", "img", "ins", "li", "ol", "p", "pre",
    "s", "section", "small", "span", "strong", "sub", "sup", "table", "tbody",
    "td", "tfoot", "th", "thead", "tr", "u", "ul",
}

RAW_TAG_RE = re.compile(r"</?([A-Za-z][A-Za-z0-9-]*)([^<>]*)/?>")
INLINE_CODE_RE = re.compile(r"`([^`]+)`")
IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)\s]+)(?:\s+\"([^\"]*)\")?\)")
AUTOLINK_RE = re.compile(r"<((?:https?|mailto):[^>\s]+)>")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
BOLD_ALT_RE = re.compile(r"__(.+?)__", re.DOTALL)
ITALIC_RE = re.compile(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])")
STRIKE_RE = re.compile(r"~~(.+?)~~", re.DOTALL)
HR_RE = re.compile(r"^\s{0,3}([-*_])\s*(?:\1\s*){2,}$")
ATX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)\s*([A-Za-z0-9_+-]*)\s*$")
UL_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")


class MarkdownRenderer:
    """把 Markdown 文本转换为 HTML。"""

    def __init__(self, *, allow_raw_html: bool = True) -> None:
        self.allow_raw_html = allow_raw_html
        self._placeholders: dict[str, str] = {}

    # ------------------------------------------------------------------ 入口
    def render(self, text: str) -> str:
        """渲染 Markdown，返回 HTML 片段。"""
        self._placeholders = {}
        lines = (text or "").replace("\r\n", "\n").replace("\r", "\n").split("\n")
        blocks = self._parse_blocks(lines)
        return "\n".join(blocks)

    # ------------------------------------------------------------------ 块级
    def _parse_blocks(self, lines: list[str]) -> list[str]:
        output: list[str] = []
        index = 0
        total = len(lines)

        while index < total:
            line = lines[index]

            if not line.strip():
                index += 1
                continue

            # 围栏代码块
            fence = FENCE_RE.match(line)
            if fence:
                marker = fence.group(1)
                language = fence.group(2)
                index += 1
                code_lines: list[str] = []
                while index < total and not lines[index].strip().startswith(marker):
                    code_lines.append(lines[index])
                    index += 1
                index += 1  # 跳过结束围栏
                output.append(self._render_code_block(code_lines, language))
                continue

            # 分割线
            if HR_RE.match(line):
                output.append("<hr class=\"gzh-hr\">")
                index += 1
                continue

            # ATX 标题
            heading = ATX_RE.match(line)
            if heading:
                level = len(heading.group(1))
                content = heading.group(2).strip()
                output.append(f"<h{level} class=\"gzh-h{level}\">{self.render_inline(content)}</h{level}>")
                index += 1
                continue

            # 引用块
            if QUOTE_RE.match(line):
                quote_lines: list[str] = []
                while index < total and (QUOTE_RE.match(lines[index]) or (quote_lines and lines[index].strip())):
                    matched = QUOTE_RE.match(lines[index])
                    quote_lines.append(matched.group(1) if matched else lines[index].strip())
                    index += 1
                inner = self._parse_blocks(quote_lines)
                output.append(
                    "<blockquote class=\"gzh-quote\">" + "\n".join(inner) + "</blockquote>"
                )
                continue

            # 表格
            if TABLE_ROW_RE.match(line) and index + 1 < total and TABLE_DIVIDER_RE.match(lines[index + 1]):
                table_lines = []
                while index < total and TABLE_ROW_RE.match(lines[index]):
                    table_lines.append(lines[index])
                    index += 1
                output.append(self._render_table(table_lines))
                continue

            # 列表
            if UL_RE.match(line) or OL_RE.match(line):
                block, index = self._collect_list(lines, index)
                output.append(block)
                continue

            # 缩进代码块
            if line.startswith("    ") and line.strip():
                code_lines = []
                while index < total and (lines[index].startswith("    ") or not lines[index].strip()):
                    if not lines[index].strip() and index + 1 < total and not lines[index + 1].startswith("    "):
                        break
                    code_lines.append(lines[index][4:] if lines[index].startswith("    ") else "")
                    index += 1
                output.append(self._render_code_block(code_lines, ""))
                continue

            # 段落（连续非空行）
            paragraph: list[str] = []
            while index < total and lines[index].strip():
                candidate = lines[index]
                if (
                    ATX_RE.match(candidate)
                    or FENCE_RE.match(candidate)
                    or HR_RE.match(candidate)
                    or QUOTE_RE.match(candidate)
                    or UL_RE.match(candidate)
                    or OL_RE.match(candidate)
                ):
                    break
                paragraph.append(candidate.strip())
                index += 1
            if paragraph:
                text = "\n".join(paragraph)
                if re.fullmatch(r"(?:<[a-zA-Z][^>]*>\s*)+", text.strip()):
                    output.append(text.strip())
                else:
                    output.append(f'<p class="gzh-p">{self.render_inline(text)}</p>')
        return output

    def _collect_list(self, lines: list[str], index: int) -> tuple[str, int]:
        """收集一个（可含嵌套的）列表块。"""
        total = len(lines)
        ordered = bool(OL_RE.match(lines[index]))
        items: list[tuple[int, str, list[str]]] = []  # (indent, content, nested blocks)

        while index < total:
            line = lines[index]
            if not line.strip():
                # 空行后若仍是列表则继续，否则结束
                lookahead = index + 1
                while lookahead < total and not lines[lookahead].strip():
                    lookahead += 1
                if lookahead < total and (UL_RE.match(lines[lookahead]) or OL_RE.match(lines[lookahead])):
                    index = lookahead
                    continue
                break

            match = UL_RE.match(line) if not ordered else OL_RE.match(line)
            if not match:
                other = OL_RE.match(line) if ordered else UL_RE.match(line)
                if other:
                    break
                # 列表项的续行（缩进的普通文本）
                if items and line.startswith((" ", "\t")):
                    indent, content, _ = items[-1]
                    items[-1] = (indent, content + " " + line.strip(), [])
                    index += 1
                    continue
                break

            indent = len(match.group(1).expandtabs(4))
            content = match.group(3)
            nested: list[str] = []

            index += 1
            # 收集该列表项的续行与嵌套子列表
            while index < total:
                candidate = lines[index]
                if not candidate.strip():
                    lookahead = index + 1
                    while lookahead < total and not lines[lookahead].strip():
                        lookahead += 1
                    if lookahead < total and lines[lookahead].startswith((" ", "\t")):
                        index = lookahead
                        continue
                    break
                candidate_indent = len(candidate) - len(candidate.lstrip(" \t"))
                if candidate_indent <= indent and (UL_RE.match(candidate) or OL_RE.match(candidate)):
                    break
                if candidate_indent <= indent and not candidate.startswith((" ", "\t")):
                    break
                if UL_RE.match(candidate) or OL_RE.match(candidate):
                    sub, index = self._collect_list(lines, index)
                    nested.append(sub)
                    continue
                content += " " + candidate.strip()
                index += 1

            items.append((indent, content, nested))

        tag = "ol" if ordered else "ul"
        parts = [f'<{tag} class="gzh-list">']
        for _indent, content, nested in items:
            if nested:
                parts.append(f'<li class="gzh-li">{self.render_inline(content)}')
                parts.extend(nested)
                parts.append("</li>")
            else:
                parts.append(f'<li class="gzh-li">{self.render_inline(content)}</li>')
        parts.append(f"</{tag}>")
        return "\n".join(parts), index

    def _render_code_block(self, code_lines: list[str], language: str) -> str:
        escaped = html_lib.escape("\n".join(code_lines))
        lang_attr = f' data-lang="{html_lib.escape(language)}"' if language else ""
        return f'<pre class="gzh-pre"{lang_attr}><code class="gzh-code">{escaped}</code></pre>'

    def _render_table(self, table_lines: list[str]) -> str:
        def split_row(row: str) -> list[str]:
            cells = row.strip().strip("|").split("|")
            return [c.strip() for c in cells]

        header = split_row(table_lines[0])
        rows = [split_row(row) for row in table_lines[2:]] if len(table_lines) > 2 else []
        parts = ['<table class="gzh-table">', "<thead><tr>"]
        for cell in header:
            parts.append(f'<th class="gzh-th">{self.render_inline(cell)}</th>')
        parts.append("</tr></thead>")
        if rows:
            parts.append("<tbody>")
            for row in rows:
                parts.append("<tr>")
                for cell in row:
                    parts.append(f'<td class="gzh-td">{self.render_inline(cell)}</td>')
                parts.append("</tr>")
            parts.append("</tbody>")
        parts.append("</table>")
        return "".join(parts)

    # ------------------------------------------------------------------ 行内
    def render_inline(self, text: str) -> str:
        """处理行内语法。"""
        if not text:
            return ""

        # 1. 保护行内代码
        codes: list[str] = []

        def keep_code(match: re.Match[str]) -> str:
            codes.append(f'<code class="gzh-inline-code">{html_lib.escape(match.group(1))}</code>')
            return f"\x00CODE{len(codes) - 1}\x00"

        working = INLINE_CODE_RE.sub(keep_code, text)

        # 2. 保护允许的原生 HTML 标签
        raws: list[str] = []

        def keep_raw(match: re.Match[str]) -> str:
            tag = match.group(1).lower()
            if not self.allow_raw_html or tag not in ALLOWED_RAW_TAGS:
                return html_lib.escape(match.group(0))
            raws.append(match.group(0))
            return f"\x00RAW{len(raws) - 1}\x00"

        working = RAW_TAG_RE.sub(keep_raw, working)

        # 3. 转义剩余文本
        working = html_lib.escape(working)

        # 4. 图片
        def image_sub(match: re.Match[str]) -> str:
            alt = match.group(1)
            src = match.group(2)
            title = match.group(3) or ""
            title_attr = f' title="{html_lib.escape(title)}"' if title else ""
            return f'<img class="gzh-img" src="{src}" alt="{html_lib.escape(alt)}"{title_attr} />'

        working = IMAGE_RE.sub(image_sub, working)

        # 5. 链接
        def link_sub(match: re.Match[str]) -> str:
            label = match.group(1) or match.group(2)
            url = match.group(2)
            title = match.group(3) or ""
            title_attr = f' title="{html_lib.escape(title)}"' if title else ""
            return f'<a class="gzh-a" href="{url}"{title_attr}>{label}</a>'

        working = LINK_RE.sub(link_sub, working)

        # 6. 自动链接
        working = AUTOLINK_RE.sub(
            lambda m: f'<a class="gzh-a" href="{m.group(1)}">{m.group(1)}</a>', working
        )

        # 7. 强调
        working = BOLD_RE.sub(r'<strong class="gzh-strong">\1</strong>', working)
        working = BOLD_ALT_RE.sub(r'<strong class="gzh-strong">\1</strong>', working)
        working = ITALIC_RE.sub(r'<em class="gzh-em">\1</em>', working)
        working = STRIKE_RE.sub(r'<del class="gzh-del">\1</del>', working)

        # 8. 硬换行（行尾两空格）
        working = re.sub(r" {2,}\n", "<br />\n", working)

        # 9. 还原占位符
        working = re.sub(r"\x00RAW(\d+)\x00", lambda m: raws[int(m.group(1))], working)
        working = re.sub(r"\x00CODE(\d+)\x00", lambda m: codes[int(m.group(1))], working)
        return working


def markdown_to_html(text: str, *, allow_raw_html: bool = True) -> str:
    """便捷函数：Markdown 转 HTML。"""
    return MarkdownRenderer(allow_raw_html=allow_raw_html).render(text)


def html_to_text(html: str) -> str:
    """把 HTML 压成纯文本（用于摘要与指纹）。"""
    text = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or "")
    text = re.sub(r"(?i)<br\s*/?>", "\n", text)
    text = re.sub(r"(?i)</(p|div|section|li|h[1-6]|tr)>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", "", text)
    text = (
        text.replace("&nbsp;", " ")
        .replace("&amp;", "&")
        .replace("&lt;", "<")
        .replace("&gt;", ">")
        .replace("&quot;", '"')
        .replace("&#39;", "'")
    )
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_digest(html_or_text: str, max_length: int = 120) -> str:
    """生成摘要：优先在句末截断。"""
    text = html_to_text(html_or_text) if "<" in (html_or_text or "") else (html_or_text or "")
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_length:
        return text
    clipped = text[:max_length]
    for mark in ("。", "！", "？", "；", ". ", "! ", "? ", "; "):
        position = clipped.rfind(mark)
        if position > max_length * 0.5:
            return clipped[: position + len(mark)].strip()
    return clipped.rstrip() + "…"


def build_article_payload(
    *,
    title: str,
    digest: str,
    content_html: str,
    thumb_media_id: str,
    author: str = "",
    content_source_url: str = "",
    need_open_comment: int = 0,
    only_fans_can_comment: int = 0,
) -> dict[str, Any]:
    """构造 draft/add 需要的 articles 元素。"""
    return {
        "title": title,
        "author": author,
        "digest": digest,
        "content": content_html,
        "content_source_url": content_source_url,
        "thumb_media_id": thumb_media_id,
        "need_open_comment": int(need_open_comment),
        "only_fans_can_comment": int(only_fans_can_comment),
        "pic_crop_235_1": "",
        "pic_crop_1_1": "",
        "pic_crop_15_1": "",
        "pic_crop_4_3": "",
        "pic_crop_3_4": "",
    }
