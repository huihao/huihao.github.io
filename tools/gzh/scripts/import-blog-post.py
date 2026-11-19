#!/usr/bin/env python3
"""把站内博客 Markdown 转成 gzh 内容资源库稿件。

公众号与站内同源，但排版约束不同：手机上宽表读不动、微信会吃掉正文里的
外链 href、加粗太密会发花。所以转换阶段做四件事：

1. 宽表 → 竖排卡片（内联样式，微信正文可渲染）；
2. 加粗收敛（只留含数字的、引文里的原话、段末唯一金句）；
3. 外链只留文字（微信本来就会剥掉 href，站内链接统一走「阅读原文」）；
4. 写 gzh front matter（title / author / digest / cover / tags / 原文链接）。

用法：

    python3 scripts/import-blog-post.py <博客.md> \\
        --out content/2026-11/2026-11-18-深度-xxx.md \\
        --cover assets/cover-20261118.jpg \\
        --author Kimi \\
        --read-original https://bio.wuhh.cc/2026/11/17/xxx.html \\
        --digest "摘要文字"

封面路径相对于稿件文件所在目录（见 docs/content-spec.md）。
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# 正则
# --------------------------------------------------------------------------

FRONT_MATTER_RE = re.compile(r"^﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)
#: 外链语法。前面是 ``!`` 的是图片语法（``![alt](src)``），要留给渲染阶段转成
#: ``<img>``，所以用否定回顾排除掉，避免被当成外链剥成纯文本。
LINK_RE = re.compile(r"(?<!!)\[([^\]]*)\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
BOLD_RE = re.compile(r"\*\*(.+?)\*\*", re.DOTALL)
TABLE_ROW_RE = re.compile(r"^\s*\|(.+)\|\s*$")
TABLE_DIVIDER_RE = re.compile(r"^\s*\|?[\s:\-|]+\|[\s:\-|]*$")

#: 品牌强调色（与站点 --accent 一致，公众号里只用作左侧竖线）
ACCENT = "#20c6f2"

# --------------------------------------------------------------------------
# 样式片段（微信正文只认内联样式）
# --------------------------------------------------------------------------

CARD = (
    '<section style="margin:0 0 10px 0;padding:10px 12px;'
    'border-left:3px solid {accent};background:#f7f8fa;">'
    '<p style="margin:0 0 4px 0;font-size:15px;font-weight:bold;color:#1a1a1a;line-height:1.6;">{title}</p>'
    '<p style="margin:0;font-size:14px;color:#5a6169;line-height:1.7;">{detail}</p>'
    "</section>"
)

GROUP = (
    '<p style="margin:22px 0 12px 0;padding-left:9px;border-left:4px solid {accent};'
    'font-size:16px;font-weight:bold;color:#1a1a1a;line-height:1.5;">{text}</p>'
)

CARD_TAIL = (
    '<section style="margin:0 0 10px 0;padding:10px 12px;'
    'border-left:3px solid #dfe3e8;background:#fbfcfd;">'
    '<p style="margin:0;font-size:14px;color:#5a6169;line-height:1.7;">{detail}</p>'
    "</section>"
)


def esc(text: str) -> str:
    """转义卡片文本里的 HTML 特殊字符。"""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def strip_md(text: str) -> str:
    """去掉 Markdown 行内标记，留下纯文本。"""
    text = LINK_RE.sub(r"\1", text)
    text = BOLD_RE.sub(r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


# --------------------------------------------------------------------------
# 表格 → 竖排卡片
# --------------------------------------------------------------------------


def split_row(row: str) -> list[str]:
    cells = [c.strip() for c in row.strip().strip("|").split("|")]
    return cells


def table_to_cards(header: list[str], rows: list[list[str]]) -> str:
    """把宽表转成竖排卡片。

    两张表在这个博客里形态不同，所以按表头分派：

    * 表头含「谁在做」：按「AI 接管 / 人」分组，每行一张卡；
    * 其它：每行一张卡，第一列当标题，其余列当说明。
    """
    out: list[str] = []

    if len(header) >= 3 and "谁在做" in header[1]:
        ai_rows = [r for r in rows if "AI" in r[1]]
        human_rows = [r for r in rows if "AI" not in r[1]]
        for label, group in (("交给 AI 的活儿", ai_rows), ("留在人手里的活儿", human_rows)):
            if not group:
                continue
            out.append(GROUP.format(accent=ACCENT, text=esc(label)))
            for row in group:
                out.append(
                    CARD.format(
                        accent=ACCENT,
                        title=esc(strip_md(row[0])),
                        detail=esc(strip_md(row[2] if len(row) > 2 else "")),
                    )
                )
        return "\n".join(out)

    # 通用形态：公司 / 做了什么 / 意味着什么
    for row in rows:
        title = strip_md(row[0])
        detail_parts = []
        for index, cell in enumerate(row[1:], start=1):
            value = strip_md(cell)
            if not value:
                continue
            label = header[index] if index < len(header) else ""
            detail_parts.append(f"{label}：{value}" if label else value)
        out.append(
            CARD.format(
                accent=ACCENT,
                title=esc(title),
                detail=esc("；".join(detail_parts)),
            )
        )
    return "\n".join(out)


# --------------------------------------------------------------------------
# 加粗收敛
# --------------------------------------------------------------------------


def filter_bold(block: str) -> str:
    """按公众号阅读体验收敛加粗。

    保留：含数字的加粗、引文块里的原话、段落里唯一且收尾的那句金句。
    其余解包（去掉星号但保留文字）。
    """
    if not block.strip():
        return block

    spans = list(BOLD_RE.finditer(block))
    if not spans:
        return block

    # 引文块（> 开头）整块保留加粗
    if block.lstrip().startswith(">"):
        return block

    keep: set[int] = set()
    for index, match in enumerate(spans):
        if re.search(r"\d", match.group(1)):
            keep.add(index)

    if not keep and len(spans) == 1:
        # 段落里唯一的加粗，且落在段尾 → 当作金句保留
        tail = block[spans[0].end():].strip()
        if tail in {"", "。", "，", "；", "：", "!", "！", "?", "？", "。”"}:
            keep.add(0)

    counter = {"n": 0}

    def replace(match: re.Match[str]) -> str:
        position = counter["n"]
        counter["n"] += 1
        # 保留下来的加粗要重新包回 **，否则整段加粗等于全被解包
        return f"**{match.group(1)}**" if position in keep else match.group(1)

    return BOLD_RE.sub(replace, block)


# --------------------------------------------------------------------------
# 正文转换
# --------------------------------------------------------------------------


def convert_body(body: str) -> str:
    lines = body.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    index = 0
    total = len(lines)

    def starts_block(candidate: str) -> bool:
        if not candidate.strip():
            return True
        if TABLE_ROW_RE.match(candidate):
            return True
        return bool(
            ATX_RE.match(candidate)
            or QUOTE_RE.match(candidate)
            or UL_RE.match(candidate)
            or OL_RE.match(candidate)
            or HR_RE.match(candidate)
            or FENCE_RE.match(candidate)
        )

    while index < total:
        line = lines[index]

        if not line.strip():
            out.append("")
            index += 1
            continue

        # 表格 → 竖排卡片
        if TABLE_ROW_RE.match(line) and index + 1 < total and TABLE_DIVIDER_RE.match(lines[index + 1]):
            table_lines = []
            while index < total and TABLE_ROW_RE.match(lines[index]):
                table_lines.append(lines[index])
                index += 1
            header = split_row(table_lines[0])
            rows = [split_row(r) for r in table_lines[2:]] if len(table_lines) > 2 else []
            out.append(table_to_cards(header, rows))
            continue

        # 标题：原样保留
        if ATX_RE.match(line):
            out.append(line.strip())
            index += 1
            continue

        # 分割线
        if HR_RE.match(line):
            out.append("---")
            index += 1
            continue

        # 围栏代码块：原样保留
        if FENCE_RE.match(line):
            marker = FENCE_RE.match(line).group(1)
            block = [line]
            index += 1
            while index < total and not lines[index].strip().startswith(marker):
                block.append(lines[index])
                index += 1
            if index < total:
                block.append(lines[index])
                index += 1
            out.append("\n".join(block))
            continue

        # 引用块：整块保留加粗（引文原话要留住）
        if QUOTE_RE.match(line):
            quote_lines = []
            while index < total and (QUOTE_RE.match(lines[index]) or (quote_lines and lines[index].strip())):
                matched = QUOTE_RE.match(lines[index])
                quote_lines.append(matched.group(1) if matched else lines[index].strip())
                index += 1
            out.append("\n".join("> " + q for q in quote_lines))
            continue

        # 列表：逐条收敛加粗
        if UL_RE.match(line) or OL_RE.match(line):
            items: list[str] = []
            while index < total and lines[index].strip():
                candidate = lines[index]
                if not (UL_RE.match(candidate) or OL_RE.match(candidate) or candidate.startswith(("  ", "\t"))):
                    break
                items.append(candidate.rstrip())
                index += 1
            out.append("\n".join(filter_bold(item) for item in items))
            continue

        # 段落（连续非空行）
        paragraph: list[str] = []
        while index < total and not starts_block(lines[index]):
            paragraph.append(lines[index].strip())
            index += 1
        if paragraph:
            out.append(filter_bold("\n".join(paragraph)))
        else:  # 兜底：万一遇到不认识的行，别把索引卡住
            out.append(lines[index].strip())
            index += 1

    text = "\n".join(out)

    # 外链只留文字（微信正文会剥掉 href，站内链接统一走「阅读原文」）
    text = LINK_RE.sub(r"\1", text)
    return text


HR_RE = re.compile(r"^\s{0,3}([-*_])\s*(\1\s*){2,}$")
FENCE_RE = re.compile(r"^\s{0,3}(```+|~~~+)\s*([A-Za-z0-9_+-]*)\s*$")
ATX_RE = re.compile(r"^\s{0,3}(#{1,6})\s+(.*?)\s*#*\s*$")
QUOTE_RE = re.compile(r"^\s{0,3}>\s?(.*)$")
UL_RE = re.compile(r"^(\s*)([-*+])\s+(.*)$")
OL_RE = re.compile(r"^(\s*)(\d+)[.)]\s+(.*)$")


# --------------------------------------------------------------------------
# front matter
# --------------------------------------------------------------------------


def parse_front_matter(text: str) -> tuple[dict[str, str], str]:
    match = FRONT_MATTER_RE.match(text)
    if not match:
        return {}, text
    meta: dict[str, str] = {}
    for raw_line in match.group(1).splitlines():
        if ":" not in raw_line or raw_line.strip().startswith("#"):
            continue
        key, _, value = raw_line.partition(":")
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        meta[key.strip()] = value
    return meta, text[match.end():]


def yaml_str(value: str) -> str:
    """安全地加引号：值里带双引号时改用单引号。"""
    if '"' in value and "'" not in value:
        return f"'{value}'"
    return '"' + value.replace('"', '\\"') + '"'


def build_front_matter(
    *,
    title: str,
    author: str,
    digest: str,
    cover: str,
    tags: list[str],
    read_original: str,
    open_comment: bool,
    fans_only: bool,
) -> str:
    lines = [
        "---",
        f"title: {yaml_str(title)}",
        f"author: {yaml_str(author)}",
        f"digest: {yaml_str(digest)}",
        f"cover: {cover}",
        f"tags: [{', '.join(tags)}]",
        f"source_url: {read_original}",
        f"content_source_url: {read_original}",
        f"need_open_comment: {1 if open_comment else 0}",
        f"only_fans_can_comment: {1 if fans_only else 0}",
        "---",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="博客 Markdown → gzh 稿件")
    parser.add_argument("source", help="站内博客 Markdown 路径")
    parser.add_argument("--out", required=True, help="输出的 gzh 稿件路径")
    parser.add_argument("--cover", required=True, help="封面路径（相对稿件目录）")
    parser.add_argument("--author", required=True)
    parser.add_argument("--digest", required=True)
    parser.add_argument("--read-original", required=True, help="「阅读原文」跳转地址")
    parser.add_argument("--tags", default="", help="逗号分隔")
    parser.add_argument("--title", default="")
    parser.add_argument("--open-comment", action="store_true", default=True)
    parser.add_argument("--no-open-comment", dest="open_comment", action="store_false")
    parser.add_argument("--fans-only", action="store_true")
    args = parser.parse_args()

    source = Path(args.source)
    raw = source.read_text(encoding="utf-8")
    meta, body = parse_front_matter(raw)

    title = args.title or meta.get("title", "")
    if not title:
        print("缺少标题", file=sys.stderr)
        return 1

    converted = convert_body(body).strip()

    front = build_front_matter(
        title=title,
        author=args.author,
        digest=args.digest,
        cover=args.cover,
        tags=[t.strip() for t in args.tags.split(",") if t.strip()],
        read_original=args.read_original,
        open_comment=args.open_comment,
        fans_only=args.fans_only,
    )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(front + converted + "\n", encoding="utf-8")

    body_chars = len(re.sub(r"\s", "", converted))
    print(f"已写出 {out_path}")
    print(f"  标题   : {title}")
    print(f"  摘要   : {len(args.digest)} 字（上限 120）")
    print(f"  正文字数: {body_chars}（微信上限 20000）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
