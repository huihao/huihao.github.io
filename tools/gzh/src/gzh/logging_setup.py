"""结构化日志。

同时输出到控制台（人读）与滚动文件（JSON 行，机器读），
方便值班同学用 ``grep``/``jq`` 快速定位发布链路上的问题。
"""

from __future__ import annotations

import json
import logging
import logging.handlers
import os
import sys
import time
from pathlib import Path
from typing import Any

LOGGER_NAME = "gzh"


class JsonFormatter(logging.Formatter):
    """把日志格式化为单行 JSON。"""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(record.created))
            + f".{int(record.msecs):03d}",
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        context = getattr(record, "context", None)
        if isinstance(context, dict) and context:
            payload.update(context)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


class ContextFormatter(logging.Formatter):
    """控制台用的可读格式。"""

    def format(self, record: logging.LogRecord) -> str:
        base = time.strftime("%H:%M:%S", time.localtime(record.created))
        context = getattr(record, "context", None)
        extra = ""
        if isinstance(context, dict) and context:
            extra = " " + " ".join(f"{k}={v}" for k, v in context.items() if v not in (None, ""))
        return f"{base} {record.levelname:<5} {record.name}: {record.getMessage()}{extra}"


class ContextLogger(logging.LoggerAdapter):
    """带固定上下文的日志适配器。"""

    def process(self, msg, kwargs):  # type: ignore[override]
        context = dict(self.extra or {})
        extra = kwargs.get("extra") or {}
        context.update(extra.get("context", {}) if isinstance(extra, dict) else {})
        kwargs["extra"] = {"context": context}
        return msg, kwargs


def get_logger(name: str = LOGGER_NAME) -> ContextLogger:
    """获取带上下文的 logger。"""
    logger = logging.getLogger(name)
    if isinstance(logger, logging.Logger):
        return ContextLogger(logger, {})
    return logger


def setup_logging(
    log_dir: Path | None = None,
    level: str = "INFO",
    console: bool = True,
    file_logging: bool = True,
) -> logging.Logger:
    """初始化日志系统，返回根 logger。"""
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(getattr(logging, str(level).upper(), logging.INFO))
    logger.handlers.clear()
    logger.propagate = False

    if console:
        stream = logging.StreamHandler(sys.stderr)
        stream.setFormatter(ContextFormatter())
        logger.addHandler(stream)

    if file_logging and log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            log_dir / "gzh.log", maxBytes=10 * 1024 * 1024, backupCount=14, encoding="utf-8"
        )
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

        err_handler = logging.handlers.RotatingFileHandler(
            log_dir / "gzh-error.log", maxBytes=5 * 1024 * 1024, backupCount=14, encoding="utf-8"
        )
        err_handler.setLevel(logging.ERROR)
        err_handler.setFormatter(JsonFormatter())
        logger.addHandler(err_handler)

    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def log_env_summary(logger: logging.Logger) -> None:
    """记录运行环境摘要，便于事后核对「当时跑的是哪套环境」。"""
    logger.info(
        "运行环境",
        extra={
            "context": {
                "python": sys.version.split()[0],
                "pid": os.getpid(),
                "cwd": os.getcwd(),
                "tz": time.strftime("%Z%z"),
            }
        },
    )
