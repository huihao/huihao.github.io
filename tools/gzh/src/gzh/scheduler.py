"""调度器：按排期自动触发发布。

支持三种触发方式：

* ``at`` —— 每日固定时刻，例如 ``["08:10", "20:30"]``。
* ``cron`` —— 五段式 cron 表达式（分 时 日 月 周）。
* ``interval_minutes`` —— 固定间隔。

调度器还负责三件「运维语义」的事：

* **发布窗口**：窗口外触发的计划会顺延到窗口内的第一个可用时刻。
* **错过触发补跑**：进程重启后会补跑 grace 期内错过的触发（可关闭）。
* **单实例锁**：同一台机器上只允许一个调度进程，避免重复发布。
"""

from __future__ import annotations

import errno
import os
import signal
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Iterable

from .config import Config, Plan
from .logging_setup import get_logger
from .store import Store
from .timeutil import get_timezone, in_window, next_clock_time, now as now_in, parse_datetime

MONTH_NAMES = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}
DOW_NAMES = {"sun": 0, "mon": 1, "tue": 2, "wed": 3, "thu": 4, "fri": 5, "sat": 6}


class CronSchedule:
    """五段式 cron 表达式。"""

    def __init__(self, minutes: set[int], hours: set[int], doms: set[int], months: set[int], dows: set[int]) -> None:
        self.minutes = minutes
        self.hours = hours
        self.doms = doms
        self.months = months
        self.dows = dows

    # ------------------------------------------------------------------ 解析
    @classmethod
    def parse(cls, expression: str) -> "CronSchedule":
        """解析 cron 表达式，非法表达式直接报错。"""
        parts = (expression or "").strip().split()
        if len(parts) != 5:
            raise ValueError(f"cron 表达式必须是 5 段（分 时 日 月 周），收到: {expression!r}")
        minutes = cls._parse_field(parts[0], 0, 59, "分钟")
        hours = cls._parse_field(parts[1], 0, 23, "小时")
        doms = cls._parse_field(parts[2], 1, 31, "日")
        months = cls._parse_field(parts[3], 1, 12, "月")
        dows = cls._parse_field(parts[4], 0, 7, "周")
        dows = {0 if d == 7 else d for d in dows}
        return cls(minutes, hours, doms, months, dows)

    @staticmethod
    def _parse_field(field: str, low: int, high: int, label: str) -> set[int]:
        values: set[int] = set()
        for chunk in (field or "").split(","):
            chunk = chunk.strip().lower()
            if not chunk:
                continue
            step = 1
            if "/" in chunk:
                chunk, _, step_text = chunk.partition("/")
                try:
                    step = int(step_text)
                except ValueError as exc:
                    raise ValueError(f"{label}字段的步长非法: {step_text!r}") from exc
                if step <= 0:
                    raise ValueError(f"{label}字段的步长必须大于 0")
            if chunk in ("*", "?"):
                start, end = low, high
            elif "-" in chunk:
                start_text, _, end_text = chunk.partition("-")
                start = CronSchedule._to_int(start_text, label)
                end = CronSchedule._to_int(end_text, label)
            else:
                start = CronSchedule._to_int(chunk, label)
                end = high if step > 1 else start
            if start < low or end > high or start > end:
                raise ValueError(f"{label}字段取值超出范围 [{low},{high}]: {chunk!r}")
            values.update(range(start, end + 1, step))
        if not values:
            raise ValueError(f"{label}字段解析结果为空")
        return values

    @staticmethod
    def _to_int(text: str, label: str) -> int:
        text = text.strip().lower()
        if text in MONTH_NAMES:
            return MONTH_NAMES[text]
        if text in DOW_NAMES:
            return DOW_NAMES[text]
        try:
            return int(text)
        except ValueError as exc:
            raise ValueError(f"{label}字段包含非法取值: {text!r}") from exc

    # ------------------------------------------------------------------ 匹配
    def _day_matches(self, moment: datetime) -> bool:
        if moment.month not in self.months:
            return False
        # cron 语义：日与周都被限定时取「或」
        dom_restricted = len(self.doms) != 31
        dow_restricted = len(self.dows) != 7
        dom_ok = moment.day in self.doms
        dow_ok = ((moment.weekday() + 1) % 7) in self.dows
        if dom_restricted and dow_restricted:
            return dom_ok or dow_ok
        return dom_ok and dow_ok

    def matches(self, moment: datetime) -> bool:
        """判断某个分钟是否命中。"""
        return (
            moment.minute in self.minutes
            and moment.hour in self.hours
            and self._day_matches(moment)
        )

    def next_after(self, start: datetime) -> datetime:
        """返回 start 之后的下一个命中时刻。"""
        current = (start + timedelta(minutes=1)).replace(second=0, microsecond=0)
        for _ in range(366 * 4):
            if not self._day_matches(current):
                current = (current + timedelta(days=1)).replace(hour=0, minute=0)
                continue
            hours = sorted(h for h in self.hours if h >= current.hour)
            if not hours:
                current = (current + timedelta(days=1)).replace(hour=0, minute=0)
                continue
            hour = hours[0]
            if hour == current.hour:
                minutes = sorted(m for m in self.minutes if m >= current.minute)
            else:
                minutes = sorted(self.minutes)
            if not minutes:
                current = (current + timedelta(days=1)).replace(hour=0, minute=0)
                continue
            return current.replace(hour=hour, minute=minutes[0])
        return start + timedelta(days=365)


# ---------------------------------------------------------------------- 触发器
@dataclass
class TriggerContext:
    """触发判定所需的上下文。"""

    plan: Plan
    now: datetime
    store: Store


class Trigger:
    """触发器基类。"""

    name = "trigger"

    def key(self, context: TriggerContext) -> str:
        return f"trigger:{context.plan.id}:{context.now:%Y%m%d%H%M}"

    def due(self, context: TriggerContext) -> tuple[bool, str]:
        """返回 (是否触发, 原因)。"""
        raise NotImplementedError

    def mark_fired(self, context: TriggerContext) -> None:
        context.store.kv_set(self.key(context), context.now.isoformat())

    def previous_before(self, context: TriggerContext) -> datetime | None:
        """返回最近一个「本应触发但未触发」的时刻（用于补跑）。"""
        return None


class DailyTimesTrigger(Trigger):
    """每日固定时刻。"""

    name = "at"

    def due(self, context: TriggerContext) -> tuple[bool, str]:
        clock = context.now.strftime("%H:%M")
        if clock not in context.plan.at:
            return False, ""
        if context.store.kv_get(self.key(context)):
            return False, "今日该时刻已触发"
        return True, f"到达计划时刻 {clock}"

    def previous_before(self, context: TriggerContext) -> datetime | None:
        candidates = []
        for clock in context.plan.at:
            moment = next_clock_time(context.now - timedelta(days=1), clock)
            candidates.append(moment)
        if not candidates:
            return None
        latest = max(candidates)
        return latest if latest <= context.now else None


class CronTrigger(Trigger):
    """cron 表达式触发。"""

    name = "cron"

    def __init__(self, expression: str) -> None:
        self.expression = expression
        self.schedule = CronSchedule.parse(expression)

    def due(self, context: TriggerContext) -> tuple[bool, str]:
        if not self.schedule.matches(context.now):
            return False, ""
        if context.store.kv_get(self.key(context)):
            return False, "本分钟已触发"
        return True, f"命中 cron 表达式 {self.expression}"

    def previous_before(self, context: TriggerContext) -> datetime | None:
        candidate = context.now.replace(second=0, microsecond=0)
        for _ in range(60 * 24 * 40):
            candidate -= timedelta(minutes=1)
            if self.schedule.matches(candidate):
                return candidate
        return None


class IntervalTrigger(Trigger):
    """固定间隔触发。"""

    name = "interval"

    def due(self, context: TriggerContext) -> tuple[bool, str]:
        interval = int(context.plan.interval_minutes or 60)
        last = context.store.kv_get(f"trigger:{context.plan.id}:last")
        if last:
            try:
                last_time = parse_datetime(str(last), timezone_name="Asia/Shanghai")
            except Exception:  # noqa: BLE001
                last_time = None
            if last_time:
                current = context.now
                if current.tzinfo is None:
                    current = current.replace(tzinfo=last_time.tzinfo)
                elapsed = (current - last_time).total_seconds() / 60
                if elapsed < interval:
                    return False, ""
                return True, f"距上次触发已过 {int(elapsed)} 分钟（间隔 {interval} 分钟）"
        return True, "首次触发"

    def mark_fired(self, context: TriggerContext) -> None:
        context.store.kv_set(f"trigger:{context.plan.id}:last", context.now.isoformat())

    def previous_before(self, context: TriggerContext) -> datetime | None:
        last = context.store.kv_get(f"trigger:{context.plan.id}:last")
        if not last:
            return None
        try:
            return parse_datetime(str(last), timezone_name="Asia/Shanghai")
        except Exception:  # noqa: BLE001
            return None


def build_trigger(plan: Plan) -> Trigger:
    """根据计划配置构造触发器。"""
    if plan.cron:
        return CronTrigger(plan.cron)
    if plan.at:
        return DailyTimesTrigger()
    if plan.interval_minutes:
        return IntervalTrigger()
    raise ValueError(f"计划 {plan.id} 没有配置任何触发方式")


# ---------------------------------------------------------------------- 调度器
class SingleInstanceLock:
    """基于文件锁的单实例保护。"""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._fd: int | None = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._fd = os.open(str(self.path), os.O_CREAT | os.O_RDWR, 0o644)
        try:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            os.close(self._fd)
            self._fd = None
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                return False
            raise
        os.write(self._fd, str(os.getpid()).encode())
        return True

    def release(self) -> None:
        if self._fd is None:
            return
        try:
            import fcntl

            fcntl.flock(self._fd, fcntl.LOCK_UN)
        finally:
            os.close(self._fd)
            self._fd = None

    def __enter__(self) -> "SingleInstanceLock":
        if not self.acquire():
            raise RuntimeError(f"已有调度进程在运行（锁文件 {self.path}）")
        return self

    def __exit__(self, *exc: object) -> None:
        self.release()


class Scheduler:
    """排期引擎。"""

    def __init__(
        self,
        config: Config,
        publisher: Any,
        store: Store,
        logger: Any = None,
    ) -> None:
        self.config = config
        self.publisher = publisher
        self.store = store
        self.logger = logger or get_logger("gzh.scheduler")
        self._stopping = False

    # ------------------------------------------------------------------ 触发器
    def trigger_for(self, plan: Plan) -> Trigger:
        return build_trigger(plan)

    def _plan_timezone(self, plan: Plan) -> str:
        return plan.timezone or self.config.timezone

    # ------------------------------------------------------------------ 窗口
    def _window(self, plan: Plan) -> tuple[str, str]:
        window = plan.window or {}
        policies_window = self.config.policies.get("publish_window", {}) or {}
        start = str(window.get("start") or policies_window.get("start") or "")
        end = str(window.get("end") or policies_window.get("end") or "")
        return start, end

    def _blackout(self, plan: Plan, moment: datetime) -> bool:
        blackout = self.config.policies.get("blackout_dates", []) or []
        return moment.strftime("%Y-%m-%d") in blackout

    def _defer_to_window(self, plan: Plan, moment: datetime) -> datetime | None:
        """窗口外：计算顺延到窗口内的下一个时刻。"""
        start, end = self._window(plan)
        if not start or not end:
            return None
        if in_window(moment, start, end):
            return None
        if not in_window(moment, start, end):
            # 当前在窗口之前 → 今天/明天的开始时刻；否则 → 明天的开始时刻
            candidate = next_clock_time(moment, start)
            if candidate.time().isoformat() < end:
                return candidate
            return next_clock_time(candidate + timedelta(days=1), start)
        return None

    # ------------------------------------------------------------------ 补跑
    def catch_up(self) -> list[str]:
        """补跑进程停机期间错过的触发。"""
        caught: list[str] = []
        for plan in self.config.plans:
            if not plan.enabled:
                continue
            try:
                trigger = self.trigger_for(plan)
            except ValueError:
                continue
            timezone_name = self._plan_timezone(plan)
            moment = now_in(timezone_name)
            previous = trigger.previous_before(TriggerContext(plan=plan, now=moment, store=self.store))
            if previous is None:
                continue
            grace = timedelta(minutes=plan.misfire_grace_minutes)
            if moment - previous > grace:
                continue
            if trigger.due(TriggerContext(plan=plan, now=moment, store=self.store))[0]:
                continue  # 本来就会触发，不必补跑
            self.logger.warning(
                "补跑错过的触发",
                extra={
                    "context": {
                        "plan": plan.id,
                        "missed_at": previous.isoformat(),
                        "grace_minutes": plan.misfire_grace_minutes,
                    }
                },
            )
            self._execute(plan, trigger="catch_up")
            caught.append(plan.id)
        return caught

    # ------------------------------------------------------------------ 主循环
    def tick(self, moment: datetime | None = None) -> list[str]:
        """检查一次所有计划，返回本次触发的计划 id 列表。"""
        fired: list[str] = []
        for plan in self.config.plans:
            if not plan.enabled:
                continue
            timezone_name = self._plan_timezone(plan)
            current = moment or now_in(timezone_name)
            if current.tzinfo is None:
                current = current.replace(tzinfo=get_timezone(timezone_name))

            if self._blackout(plan, current):
                continue

            try:
                trigger = self.trigger_for(plan)
            except ValueError as exc:
                self.logger.error("计划触发器配置错误", extra={"context": {"plan": plan.id, "error": str(exc)}})
                continue

            context = TriggerContext(plan=plan, now=current, store=self.store)
            is_due, reason = trigger.due(context)
            if not is_due:
                continue

            deferred = self._defer_to_window(plan, current)
            if deferred is not None:
                pending_key = f"pending:{plan.id}"
                self.store.kv_set(pending_key, deferred.isoformat())
                self.logger.info(
                    "不在发布时段，已顺延",
                    extra={
                        "context": {
                            "plan": plan.id,
                            "window": self._window(plan),
                            "deferred_to": deferred.isoformat(),
                        }
                    },
                )
                continue

            pending_key = f"pending:{plan.id}"
            pending = self.store.kv_get(pending_key)
            if pending:
                pending_time = parse_datetime(str(pending), timezone_name=timezone_name)
                if pending_time and current < pending_time:
                    continue
                self.store.kv_set(pending_key, "")

            self.logger.info(
                "计划触发",
                extra={"context": {"plan": plan.id, "reason": reason, "mode": plan.mode}},
            )
            self._execute(plan, trigger="schedule")
            fired.append(plan.id)
        return fired

    def _execute(self, plan: Plan, *, trigger: str) -> None:
        """执行一个计划的发布流程并记录运行结果。"""
        account = self.config.account(plan.account)
        run_id = self.store.start_run(plan.id, account.id, plan.mode, trigger)
        published = skipped = failed = 0
        error = ""
        try:
            self.publisher.collect(plan)
            results = self.publisher.publish(plan, trigger=trigger)
            for result in results:
                if result.ok:
                    published += 1
                elif result.status == "skipped" or result.status == "blocked":
                    skipped += 1
                else:
                    failed += 1
        except Exception as exc:  # noqa: BLE001 - 单个计划异常不能拖垮整个调度
            error = f"{type(exc).__name__}: {exc}"
            failed += 1
            self.logger.error(
                "计划执行异常",
                extra={"context": {"plan": plan.id, "error": error}},
                exc_info=True,
            )
            self.store.add_event(
                "ERROR",
                "计划执行异常",
                component="scheduler",
                account_id=account.id,
                plan_id=plan.id,
                data={"error": error},
            )
        finally:
            self.store.finish_run(
                run_id,
                status="error" if error else ("partial" if failed else "ok"),
                published=published,
                skipped=skipped,
                failed=failed,
                error=error,
            )
            trigger = self.trigger_for(plan)
            trigger.mark_fired(TriggerContext(plan=plan, now=now_in(self._plan_timezone(plan)), store=self.store))

    # ------------------------------------------------------------------ 常驻
    def run_forever(self, *, interval: int = 20, once: bool = False) -> None:
        """前台运行调度循环。"""
        self._install_signals()
        self.logger.info(
            "调度器启动",
            extra={
                "context": {
                    "plans": [p.id for p in self.config.plans if p.enabled],
                    "timezone": self.config.timezone,
                    "interval": interval,
                }
            },
        )
        self.catch_up()
        while not self._stopping:
            started = time.time()
            try:
                self.tick()
            except Exception as exc:  # noqa: BLE001
                self.logger.error("调度循环异常", extra={"context": {"error": str(exc)}}, exc_info=True)
            if once:
                break
            elapsed = time.time() - started
            time.sleep(max(1.0, interval - elapsed))
        self.logger.info("调度器已停止")

    def stop(self) -> None:
        """请求调度器退出。"""
        self._stopping = True

    def _install_signals(self) -> None:
        def handler(signum: int, _frame: Any) -> None:
            self.logger.info("收到停止信号，准备退出", extra={"context": {"signal": signum}})
            self._stopping = True

        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, handler)
            except (ValueError, OSError):
                pass


def describe_schedule(config: Config) -> list[dict[str, Any]]:
    """给 CLI 用的排期概览。"""
    result: list[dict[str, Any]] = []
    for plan in config.plans:
        timezone_name = plan.timezone or config.timezone
        moment = now_in(timezone_name)
        next_at = ""
        try:
            trigger = build_trigger(plan)
            if isinstance(trigger, CronTrigger):
                next_at = trigger.schedule.next_after(moment).isoformat()
            elif isinstance(trigger, DailyTimesTrigger):
                candidates = [
                    next_clock_time(moment, clock) for clock in plan.at
                ]
                next_at = min(candidates).isoformat() if candidates else ""
            elif isinstance(trigger, IntervalTrigger):
                next_at = (moment + timedelta(minutes=plan.interval_minutes or 60)).isoformat()
        except Exception:  # noqa: BLE001
            next_at = ""
        result.append(
            {
                "id": plan.id,
                "account": plan.account,
                "enabled": plan.enabled,
                "mode": plan.mode,
                "trigger": "at" if plan.at else ("cron" if plan.cron else "interval"),
                "expression": ", ".join(plan.at) or plan.cron or f"{plan.interval_minutes}min",
                "window": " ".join(part for part in self_window(config, plan) if part),
                "timezone": timezone_name,
                "next_at": next_at,
            }
        )
    return result


def self_window(config: Config, plan: Plan) -> tuple[str, str]:
    window = plan.window or {}
    policies_window = config.policies.get("publish_window", {}) or {}
    return (
        str(window.get("start") or policies_window.get("start") or ""),
        str(window.get("end") or policies_window.get("end") or ""),
    )


def iter_plan_ids(config: Config) -> Iterable[str]:
    for plan in config.plans:
        yield plan.id
