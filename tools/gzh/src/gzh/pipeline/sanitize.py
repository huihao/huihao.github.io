"""正文 HTML 清洗。

微信公众号正文会过滤掉脚本、嵌入对象与表单类标签；本模块在发送前
主动清理，既避免内容被静默丢弃，也避免误留可执行内容。

处理项：

* 删除危险标签（含其内容）：script / style / iframe / object / embed / form /
  input / button / select / option / textarea / noscript / svg / math / video / audio
* 删除危险标签但保留内文：html / body / head / meta / link
* 删除事件属性（``on*``）与 ``srcdoc`` / ``formaction``
* 过滤 ``javascript:`` / ``vbscript:`` / ``data:text/html`` 伪协议
* 清理 CSS 中的 ``position:fixed``、``expression()`` 等微信会清除或拒绝的写法
"""

from __future__ import annotations

import re

#: 连同内容一起删除的标签。
DROP_WITH_CONTENT = {
    "script", "style", "iframe", "object", "embed", "form", "input", "button",
    "select", "option", "textarea", "noscript", "svg", "math", "video", "audio",
    "canvas", "applet", "template",
}

#: 只删除标签本身、保留内文的标签。
UNWRAP_TAGS = {"html", "body", "head", "meta", "link", "title", "base"}

DANGEROUS_ATTRS = {"srcdoc", "formaction", "ping", "http-equiv", "content"}

UNSAFE_URL_RE = re.compile(r"^\s*(javascript|vbscript|data:text/html)\s*:", re.IGNORECASE)

SAFE_URL_RE = re.compile(r"^\s*(https?:|mailto:|tel:|#|/|\./|[^:]*$)", re.IGNORECASE)

TAG_RE = re.compile(r"<(/?)([A-Za-z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>\"'])*)(/?)>", re.DOTALL)
ATTR_RE = re.compile(
    r"([A-Za-z_:][\w:.-]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s\"'>]+)"
)


def _clean_style(value: str) -> str:
    """移除微信会清理或拒绝的 CSS 声明。"""
    cleaned = re.sub(r"position\s*:\s*fixed\s*;?", "", value, flags=re.IGNORECASE)
    cleaned = re.sub(r"expression\s*\([^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"z-index\s*:\s*\d{4,}\s*;?", "", cleaned, flags=re.IGNORECASE)
    return cleaned.strip("; ")


def _clean_attributes(raw: str) -> str:
    """清理属性串。"""
    parts: list[str] = []
    for match in ATTR_RE.finditer(raw or ""):
        name = match.group(1)
        value = match.group(2)
        if value[:1] in ("\"", "'") and value[-1:] == value[:1]:
            value = value[1:-1]
        lower = name.lower()

        if lower.startswith("on"):
            continue
        if lower in DANGEROUS_ATTRS:
            continue
        if lower in ("href", "src", "xlink:href", "action"):
            if UNSAFE_URL_RE.match(value):
                continue
            if value and not SAFE_URL_RE.match(value):
                continue
        if lower == "style":
            value = _clean_style(value)
            if not value:
                continue
        parts.append(f'{name}="{value}"')
    # 保留非属性内容（例如自闭合符）
    trailing = re.sub(ATTR_RE, "", raw or "").strip()
    if trailing:
        parts.append(trailing)
    return (" " + " ".join(parts)) if parts else ""


def sanitize_html(html: str) -> str:
    """清洗正文 HTML。"""
    if not html:
        return ""

    # 1. 删除带内容的危险标签
    for tag in DROP_WITH_CONTENT:
        html = re.sub(rf"(?is)<{tag}\b[^>]*>.*?</{tag}\s*>", "", html)
        html = re.sub(rf"(?is)<{tag}\b[^>]*/?>", "", html)

    def replace(match: re.Match[str]) -> str:
        closing, name, raw_attrs, self_closing = match.groups()
        lower = name.lower()
        if lower in UNWRAP_TAGS:
            return ""
        if lower in DROP_WITH_CONTENT:
            return ""
        attrs = _clean_attributes(raw_attrs)
        if closing:
            return f"</{lower}>"
        return f"<{lower}{attrs}{self_closing}>"

    html = TAG_RE.sub(replace, html)

    # 2. 移除 HTML 注释
    html = re.sub(r"(?s)<!--.*?-->", "", html)
    return html.strip()


def plain_text(*parts: str) -> str:
    """去掉 HTML 标签与 Markdown 标记，只留文字。

    关键词语境判断需要「连续的词」：`**第一**` 在标签里会被拆成
    `<strong>第一</strong>`，直接看原始 HTML 会让后文语境判断失效。
    """
    text = "\n".join(part or "" for part in parts)
    text = re.sub(r"(?s)<!--.*?-->", " ", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`~>#|]+", " ", text)
    return text


def check_compliance(
    html: str,
    *,
    forbidden_keywords: list[str] | None = None,
    safe_contexts: dict[str, list[str]] | None = None,
) -> list[str]:
    """粗筛风险词，返回命中列表（用于 SOP 中的「发布前红线检查」）。

    这是**辅助**检查，不能替代人工审校；命中后由运营在发布前人工确认。

    `safe_contexts` 给每个关键词配一组「安全语境」正则：只有当关键词的
    **每一次**出现都落在安全语境里（正则匹配关键词后面的文字）才放行。
    例如广告法里的「第一」要拦，但「第一条」「第一次」「第一财经」是
    普通行文，不该拦——用语境区分，而不是把词整个去掉。
    """
    text = (html or "").lower()
    hits: list[str] = []
    for keyword in forbidden_keywords or []:
        if not keyword:
            continue
        needle = keyword.lower()
        if needle not in text:
            continue
        patterns = [re.compile(p) for p in (safe_contexts or {}).get(keyword, [])]
        if patterns:
            positions = [m.start() for m in re.finditer(re.escape(needle), text)]
            if all(
                any(p.match(text[pos + len(needle) : pos + len(needle) + 12]) for p in patterns)
                for pos in positions
            ):
                continue
        hits.append(keyword)
    return hits
