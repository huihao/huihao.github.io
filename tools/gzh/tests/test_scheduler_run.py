"""调度器端到端行为测试（触发、顺延、去重、留痕）。"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.config import load_config
from gzh.publisher import Publisher
from gzh.scheduler import Scheduler
from gzh.store import Store


class TestSchedulerTick(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        for name in ("config", "content", "assets"):
            (self.root / name).mkdir()
        (self.root / "content" / "a.md").write_text(
            "---\ntitle: 调度测试\n---\n正文内容\n", encoding="utf-8"
        )
        (self.root / "assets" / "c.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        self.now = datetime.now(ZoneInfo("Asia/Shanghai"))
        self._write_config()

    def tearDown(self):
        self.tmp.cleanup()

    def _write_config(self, window: dict[str, str] | None = None) -> None:
        window = window or {"start": "00:00", "end": "23:59"}
        (self.root / "config" / "accounts.json").write_text(
            json.dumps(
                {
                    "accounts": [
                        {
                            "id": "main",
                            "app_id": "",
                            "app_secret": "",
                            "mode": "draft",
                            "cover": "assets/c.png",
                            "quota": {"draft_per_day": 5},
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        (self.root / "config" / "scheduler.json").write_text(
            json.dumps(
                {
                    "timezone": "Asia/Shanghai",
                    "plans": [
                        {
                            "id": "at-plan",
                            "account": "main",
                            "enabled": True,
                            "at": [self.now.strftime("%H:%M")],
                            "source": {"type": "local", "path": "content"},
                            "select": {"limit": 1},
                            "mode": "draft",
                            "dry_run": True,
                            "window": window,
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        (self.root / "config" / "policies.json").write_text(
            json.dumps({"allow_missing_cover": True}), encoding="utf-8"
        )

    def _scheduler(self):
        config = load_config(self.root)
        store = Store(config.db_path)
        publisher = Publisher(config, store, logger=None)
        return Scheduler(config, publisher, store, logger=None), store

    def test_tick_triggers_and_records(self):
        scheduler, store = self._scheduler()
        fired = scheduler.tick()
        self.assertEqual(fired, ["at-plan"])

        runs = store.recent_runs(5)
        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0]["plan_id"], "at-plan")
        self.assertEqual(runs[0]["status"], "ok")
        store.close()

    def test_tick_does_not_fire_twice_in_same_minute(self):
        scheduler, store = self._scheduler()
        self.assertEqual(scheduler.tick(), ["at-plan"])
        self.assertEqual(scheduler.tick(), [])
        store.close()

    def test_out_of_window_is_deferred(self):
        self._write_config(window={"start": "03:00", "end": "04:00"})
        scheduler, store = self._scheduler()
        fired = scheduler.tick()
        self.assertEqual(fired, [])
        pending = store.kv_get("pending:at-plan")
        self.assertIsNotNone(pending)
        self.assertIn("T03:00:00", pending)
        store.close()

    def test_disabled_plan_never_fires(self):
        path = self.root / "config" / "scheduler.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["plans"][0]["enabled"] = False
        path.write_text(json.dumps(payload), encoding="utf-8")
        scheduler, store = self._scheduler()
        self.assertEqual(scheduler.tick(), [])
        store.close()

    def test_blackout_date_blocks(self):
        path = self.root / "config" / "policies.json"
        path.write_text(
            json.dumps(
                {
                    "allow_missing_cover": True,
                    "blackout_dates": [self.now.strftime("%Y-%m-%d")],
                }
            ),
            encoding="utf-8",
        )
        scheduler, store = self._scheduler()
        self.assertEqual(scheduler.tick(), [])
        store.close()

    def test_cron_plan_evaluates(self):
        path = self.root / "config" / "scheduler.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["plans"][0].pop("at")
        payload["plans"][0]["cron"] = f"{self.now.minute} {self.now.hour} * * *"
        path.write_text(json.dumps(payload), encoding="utf-8")
        scheduler, store = self._scheduler()
        fired = scheduler.tick()
        self.assertEqual(fired, ["at-plan"])
        store.close()


if __name__ == "__main__":
    unittest.main()
