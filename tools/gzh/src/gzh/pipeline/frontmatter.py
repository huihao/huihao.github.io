"""YAML front matter 解析（YAML 子集）。

支持内容资源库常用的写法：

    ---
    title: "标题"
    author: 张三
    digest: 摘要
    tags: [AI, 效率]
    need_open_comment: 0
    publish_at: 2026-11-06T08:00
    ---

支持行内列表 ``[a, b]``、块状列表（``- item``）、一层嵌套映射、
引号字符串、数字、布尔与 null。完整 YAML 特性（如锚点、多行块标量）不在支持范围内，
遇到时按原样当字符串处理。
"""

from __future__ import annotations

import re
from typing import Any

FRONT_MATTER_RE = re.compile(r"^﻿?---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|$)", re.DOTALL)


def _split_top_level_commas(text: str) -> list[str]:
    """按顶层逗号切分，忽略引号与括号内的逗号。"""
    parts: list[str] = []
    depth = 0
    quote: str | None = None
    current: list[str] = []
    for char in text:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in "\"'":
            quote = char
            current.append(char)
            continue
        if char in "[{":
            depth += 1
        elif char in "]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    if current:
        parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()]


def _parse_scalar(text: str) -> Any:
    """把标量文本转换成 Python 值。"""
    text = text.strip()
    if not text:
        return ""
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        return [_parse_scalar(p) for p in _split_top_level_commas(text[1:-1])]
    if text.startswith("{") and text.endswith("}"):
        mapping: dict[str, Any] = {}
        for part in _split_top_level_commas(text[1:-1]):
            if ":" in part:
                key, _, value = part.partition(":")
                mapping[key.strip()] = _parse_scalar(value)
        return mapping
    lowered = text.lower()
    if lowered in ("true", "yes", "on"):
        return True
    if lowered in ("false", "no", "off"):
        return False
    if lowered in ("null", "none", "~"):
        return None
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def parse_simple_yaml(text: str) -> dict[str, Any]:
    """解析 YAML 子集为字典。"""
    result: dict[str, Any] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if raw[:1] in (" ", "\t"):
            # 顶层 key 之后的缩进内容在上一轮已被消费，这里是多余的缩进块，跳过
            index += 1
            continue
        if ":" not in raw:
            index += 1
            continue

        key, _, value = raw.partition(":")
        key = key.strip()
        value = value.strip()
        if not key:
            index += 1
            continue

        if value:
            result[key] = _parse_scalar(value)
            index += 1
            continue

        # 值为空：向下收集列表或嵌套映射
        items: list[Any] = []
        nested: dict[str, Any] = {}
        cursor = index + 1
        while cursor < len(lines):
            candidate = lines[cursor]
            if not candidate.strip():
                cursor += 1
                continue
            if candidate[:1] not in (" ", "\t"):
                break
            content = candidate.strip()
            if content.startswith("- "):
                items.append(_parse_scalar(content[2:]))
            elif content == "-":
                items.append(None)
            elif ":" in content:
                sub_key, _, sub_value = content.partition(":")
                nested[sub_key.strip()] = _parse_scalar(sub_value)
            cursor += 1

        if items:
            result[key] = items
        elif nested:
            result[key] = nested
        else:
            result[key] = None
        index = cursor
    return result


def split_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """拆分 front matter 与正文。

    Returns:
        (元数据字典, 正文)
    """
    match = FRONT_MATTER_RE.match(text or "")
    if not match:
        return {}, text or ""
    meta = parse_simple_yaml(match.group(1))
    body = text[match.end():]
    return meta, body


def render_front_matter(meta: dict[str, Any]) -> str:
    """把元数据渲染回 front matter（供预览/调试使用）。"""
    lines = ["---"]
    for key, value in meta.items():
        if isinstance(value, list):
            rendered = ", ".join(str(v) for v in value)
            lines.append(f"{key}: [{rendered}]")
        elif isinstance(value, dict):
            lines.append(f"{key}:")
            for sub_key, sub_value in value.items():
                lines.append(f"  {sub_key}: {sub_value}")
        elif value is None:
            lines.append(f"{key}:")
        else:
            lines.append(f"{key}: {value}")
    lines.append("---")
    return "\n".join(lines) + "\n"
