"""时间工具。

统一处理「时区 + 各类时间字符串」，避免发布时段判断出现时区错乱。
"""

from __future__ import annotations

import re
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

#: 常见时间字符串格式。
DATETIME_FORMATS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
    "%Y/%m/%d %H:%M:%S",
    "%Y/%m/%d %H:%M",
    "%Y/%m/%d",
    "%H:%M:%S",
    "%H:%M",
)

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def get_timezone(name: str) -> ZoneInfo:
    """获取时区对象，失败时回退到 Asia/Shanghai。"""
    if not name:
        name = "Asia/Shanghai"
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return ZoneInfo("Asia/Shanghai")


def now(tz: str = "Asia/Shanghai") -> datetime:
    """当前时间（指定时区）。"""
    return datetime.now(get_timezone(tz))


def parse_datetime(value: str, *, timezone_name: str = "Asia/Shanghai") -> datetime | None:
    """解析时间字符串，返回带时区的 datetime。"""
    if not value:
        return None
    value = value.strip()
    tz = get_timezone(timezone_name)

    # ISO 8601 带时区
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tz)
        return parsed
    except ValueError:
        pass

    for fmt in DATETIME_FORMATS:
        try:
            parsed = datetime.strptime(value, fmt)
        except ValueError:
            continue
        if fmt in ("%H:%M:%S", "%H:%M"):
            today = now(timezone_name).date()
            parsed = datetime.combine(today, parsed.time())
        return parsed.replace(tzinfo=tz)
    return None


def parse_clock(value: str) -> time | None:
    """解析 ``HH:MM`` / ``HH:MM:SS``。"""
    if not value:
        return None
    for fmt in ("%H:%M", "%H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt).time()
        except ValueError:
            continue
    return None


def in_window(moment: datetime, start: str, end: str) -> bool:
    """判断时刻是否落在 ``[start, end]`` 窗口内（支持跨零点，如 22:00-06:00）。"""
    start_time = parse_clock(start)
    end_time = parse_clock(end)
    if start_time is None or end_time is None:
        return True
    current = moment.timetz().replace(tzinfo=None)
    if start_time <= end_time:
        return start_time <= current <= end_time
    return current >= start_time or current <= end_time


def next_clock_time(moment: datetime, clock: str) -> datetime:
    """返回 moment 之后的下一个 ``HH:MM`` 时刻（今天或明天）。"""
    target = parse_clock(clock)
    if target is None:
        return moment
    candidate = moment.replace(
        hour=target.hour, minute=target.minute, second=0, microsecond=0
    )
    if candidate <= moment:
        candidate += timedelta(days=1)
    return candidate


def format_duration(seconds: float) -> str:
    """把秒数格式化成人类可读文本。"""
    seconds = int(max(0, seconds))
    if seconds < 60:
        return f"{seconds}秒"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}分{sec}秒"
    hours, minutes = divmod(minutes, 60)
    if hours < 24:
        return f"{hours}小时{minutes}分"
    days, hours = divmod(hours, 24)
    return f"{days}天{hours}小时"


def utc_now() -> datetime:
    """当前 UTC 时间。"""
    return datetime.now(timezone.utc)
