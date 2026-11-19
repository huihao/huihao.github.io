"""调度与时间相关测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.config import Config, Plan
from gzh.scheduler import (
    CronSchedule,
    DailyTimesTrigger,
    IntervalTrigger,
    SingleInstanceLock,
    TriggerContext,
)
from gzh.store import Store
from gzh.timeutil import in_window, next_clock_time, parse_datetime, parse_clock


class TestCron(unittest.TestCase):
    def test_parse_star(self):
        schedule = CronSchedule.parse("* * * * *")
        self.assertEqual(len(schedule.minutes), 60)
        self.assertEqual(len(schedule.hours), 24)

    def test_parse_specific(self):
        schedule = CronSchedule.parse("30 9 * * 1-5")
        self.assertEqual(schedule.minutes, {30})
        self.assertEqual(schedule.hours, {9})
        self.assertEqual(schedule.dows, {1, 2, 3, 4, 5})

    def test_parse_step(self):
        schedule = CronSchedule.parse("*/15 * * * *")
        self.assertEqual(schedule.minutes, {0, 15, 30, 45})

    def test_invalid_expression(self):
        for expression in ("* * *", "60 * * * *", "* 25 * * *", "abc * * * *"):
            with self.assertRaises(ValueError):
                CronSchedule.parse(expression)

    def test_matches(self):
        schedule = CronSchedule.parse("30 9 * * 1-5")
        monday = datetime(2026, 11, 2, 9, 30)  # 周一
        sunday = datetime(2026, 11, 1, 9, 30)  # 周日
        self.assertTrue(schedule.matches(monday))
        self.assertFalse(schedule.matches(sunday))
        self.assertFalse(schedule.matches(datetime(2026, 11, 2, 9, 31)))

    def test_next_after(self):
        schedule = CronSchedule.parse("30 9 * * 1-5")
        moment = datetime(2026, 11, 1, 12, 0)  # 周日
        nxt = schedule.next_after(moment)
        self.assertEqual(nxt, datetime(2026, 11, 2, 9, 30))

    def test_dom_dow_or_semantics(self):
        # 日与周都受限时取「或」
        schedule = CronSchedule.parse("0 0 1 * 0")
        self.assertTrue(schedule.matches(datetime(2026, 11, 1, 0, 0)))  # 1 号
        self.assertTrue(schedule.matches(datetime(2026, 11, 8, 0, 0)))  # 周日


class TestTimeUtil(unittest.TestCase):
    def test_parse_datetime(self):
        moment = parse_datetime("2026-11-06 08:30", timezone_name="Asia/Shanghai")
        self.assertIsNotNone(moment)
        self.assertEqual(moment.hour, 8)
        self.assertEqual(moment.minute, 30)

    def test_parse_datetime_with_timezone(self):
        moment = parse_datetime("2026-11-06T08:30:00+08:00")
        self.assertIsNotNone(moment)
        self.assertEqual(moment.utcoffset(), timedelta(hours=8))

    def test_invalid_datetime(self):
        self.assertIsNone(parse_datetime("不是时间"))

    def test_parse_clock(self):
        self.assertEqual(parse_clock("08:30").hour, 8)
        self.assertIsNone(parse_clock("乱写"))

    def test_in_window(self):
        moment = datetime(2026, 11, 6, 9, 0)
        self.assertTrue(in_window(moment, "07:00", "22:30"))
        self.assertFalse(in_window(moment, "10:00", "22:30"))
        # 跨零点窗口
        self.assertFalse(in_window(moment, "22:00", "06:00"))
        self.assertTrue(in_window(datetime(2026, 11, 6, 3, 0), "22:00", "06:00"))
        self.assertTrue(in_window(datetime(2026, 11, 6, 23, 0), "22:00", "06:00"))

    def test_next_clock_time(self):
        moment = datetime(2026, 11, 6, 9, 0)
        self.assertEqual(next_clock_time(moment, "08:10").day, 7)
        self.assertEqual(next_clock_time(moment, "10:10").hour, 10)


class TestTriggers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _context(self, plan: Plan, moment: datetime) -> TriggerContext:
        return TriggerContext(plan=plan, now=moment, store=self.store)

    def test_daily_trigger_fires_once(self):
        plan = Plan(id="p1", account="main", at=["08:10"])
        moment = datetime(2026, 11, 6, 8, 10)
        trigger = DailyTimesTrigger()
        context = self._context(plan, moment)
        self.assertTrue(trigger.due(context)[0])
        trigger.mark_fired(context)
        self.assertFalse(trigger.due(context)[0])

    def test_daily_trigger_ignores_other_time(self):
        plan = Plan(id="p1", account="main", at=["08:10"])
        trigger = DailyTimesTrigger()
        self.assertFalse(trigger.due(self._context(plan, datetime(2026, 11, 6, 9, 10)))[0])

    def test_interval_trigger(self):
        plan = Plan(id="p2", account="main", interval_minutes=30)
        trigger = IntervalTrigger()
        moment = datetime(2026, 11, 6, 8, 0)
        context = self._context(plan, moment)
        self.assertTrue(trigger.due(context)[0])
        trigger.mark_fired(context)
        later = self._context(plan, moment + timedelta(minutes=10))
        self.assertFalse(trigger.due(later)[0])
        much_later = self._context(plan, moment + timedelta(minutes=31))
        self.assertTrue(trigger.due(much_later)[0])


class TestLock(unittest.TestCase):
    def test_single_instance(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "lock"
            first = SingleInstanceLock(path)
            self.assertTrue(first.acquire())
            second = SingleInstanceLock(path)
            self.assertFalse(second.acquire())
            first.release()
            self.assertTrue(second.acquire())
            second.release()


class TestConfigPlan(unittest.TestCase):
    def test_plan_helpers(self):
        plan = Plan(id="p", account="main", select={"limit": 3, "strategy": "newest"})
        self.assertEqual(plan.limit, 3)
        self.assertEqual(plan.strategy, "newest")
        self.assertEqual(plan.source_type, "local")


if __name__ == "__main__":
    unittest.main()
