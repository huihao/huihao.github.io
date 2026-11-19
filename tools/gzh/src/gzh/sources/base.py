"""内容源基类。

一个「内容源」把外部资源（本地目录、订阅源、网页列表）抽象成
:class:`~gzh.models.Article` 列表，其余环节与来源无关。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Iterable

from ..models import Article


class Source(ABC):
    """内容源接口。"""

    #: 来源类型标识。
    type: str = "base"

    def __init__(
        self,
        spec: dict[str, Any],
        *,
        roots: Iterable[Path] = (),
        http: Any = None,
        logger: Any = None,
    ) -> None:
        self.spec = dict(spec or {})
        self.roots = [Path(p) for p in roots]
        self.http = http
        self.logger = logger

    @abstractmethod
    def fetch(self) -> list[Article]:
        """抓取内容，返回文章列表。"""

    # ------------------------------------------------------------------ 工具
    def resolve_path(self, relative: str) -> Path | None:
        """在候选根目录里查找相对路径。"""
        if not relative:
            return None
        candidate = Path(relative)
        if candidate.is_absolute():
            return candidate if candidate.exists() else None
        for root in self.roots:
            resolved = root / candidate
            if resolved.exists():
                return resolved
        return None
