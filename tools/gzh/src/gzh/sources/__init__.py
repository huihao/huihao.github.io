"""内容源工厂。"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from ..errors import ConfigError
from .base import Source
from .http_source import HttpSource
from .jsonfeed import JsonFeedSource
from .local import LocalSource
from .rss import RssSource

SOURCE_CLASSES: dict[str, type[Source]] = {
    "local": LocalSource,
    "rss": RssSource,
    "jsonfeed": JsonFeedSource,
    "http": HttpSource,
}


def build_source(
    spec: dict[str, Any],
    *,
    roots: Iterable[Path] = (),
    http: Any = None,
    logger: Any = None,
) -> Source:
    """根据配置构造内容源实例。"""
    source_type = str(spec.get("type") or "local")
    source_class = SOURCE_CLASSES.get(source_type)
    if source_class is None:
        raise ConfigError(
            f"未知内容源类型: {source_type}（可选 {', '.join(sorted(SOURCE_CLASSES))}）"
        )
    return source_class(spec, roots=roots, http=http, logger=logger)


__all__ = ["Source", "build_source", "SOURCE_CLASSES"]
