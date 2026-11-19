"""内容源、存储与发布流程测试（使用假的微信客户端，不触网）。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.config import Account, Config, Plan
from gzh.errors import WechatAPIError
from gzh.http import HttpResponse
from gzh.models import STATUS_APPROVED, STATUS_BLOCKED, STATUS_DRAFTED, STATUS_FAILED, STATUS_MASS_SENT, STATUS_PUBLISHED
from gzh.publisher import Publisher
from gzh.sources import build_source
from gzh.sources.rss import RssSource
from gzh.store import Store

SAMPLE = """---
title: "单元测试稿件"
author: 测试
digest: 摘要
tags: [测试]
---

正文段落。

- 列表项一
- 列表项二
"""


class FakeHttp:
    """返回固定内容的假 HTTP 客户端。"""

    def __init__(self, body: str = "", content_type: str = "application/xml") -> None:
        self.body = body
        self.content_type = content_type
        self.requests: list[str] = []

    def request(self, method, url, **kwargs):
        self.requests.append(url)
        return HttpResponse(
            status=200,
            headers={"content-type": self.content_type},
            body=self.body.encode("utf-8"),
            url=url,
        )


class FakeWeChat:
    """假微信客户端，记录调用并可模拟失败。"""

    def __init__(self, fail_on: str | None = None) -> None:
        self.drafts: list[dict] = []
        self.published: list[str] = []
        self.passed: list[str] = []
        self.thumbs = 0
        self.images = 0
        self.fail_on = fail_on

    def _maybe_fail(self, stage: str) -> None:
        if self.fail_on == stage:
            raise WechatAPIError(48001, "api unauthorized", path="/cgi-bin/draft/add")

    def upload_thumb(self, path):
        self._maybe_fail("thumb")
        self.thumbs += 1
        return {"media_id": "thumb_media_1", "url": "https://mmbiz.qpic.cn/thumb"}

    def upload_content_image(self, path):
        self._maybe_fail("image")
        self.images += 1
        return "https://mmbiz.qpic.cn/image"

    def add_draft(self, article):
        self._maybe_fail("draft")
        self.drafts.append(article)
        return "media_id_1"

    def submit_publish(self, media_id):
        self._maybe_fail("submit")
        return "publish_id_1"

    def wait_publish(self, publish_id, timeout=120, interval=5):
        self._maybe_fail("wait")
        return {"publish_status": 0, "article_id": "article_id_1"}

    def mass_send(self, media_id, **kwargs):
        self._maybe_fail("mass")
        self.passed.append(media_id)
        return {"msg_id": 1}


class BaseCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "content").mkdir()
        (self.root / "assets").mkdir()
        (self.root / "content" / "001.md").write_text(SAMPLE, encoding="utf-8")

        self.account = Account(
            id="main",
            name="主号",
            app_id="wx_test",
            app_secret="secret",
            mode="draft",
            author="测试",
            cover="assets/cover.png",
        )
        (self.root / "assets" / "cover.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 64)
        self.config = Config(
            root=self.root,
            accounts={"main": self.account},
            plans=[],
            policies={
                "publish_window": {"start": "00:00", "end": "23:59"},
                "quota": {"draft_per_day": 50, "publish_per_day": 4, "mass_per_day": 1},
                "digest_max_length": 120,
                "allow_missing_cover": True,
            },
        )
        self.store = Store(self.root / "state.db")
        self.publisher = Publisher(self.config, self.store, logger=None)
        self.fake = FakeWeChat()
        self.publisher._clients["main"] = self.fake

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _plan(self, **kwargs) -> Plan:
        defaults = dict(
            id="p1",
            account="main",
            at=["08:00"],
            source={"type": "local", "path": "content"},
            select={"limit": 1, "strategy": "oldest"},
            mode="draft",
        )
        defaults.update(kwargs)
        return Plan(**defaults)


class TestStore(BaseCase):
    def test_upsert_is_idempotent(self):
        from gzh.models import Article

        article = Article(title="标题", source_key="k1", markdown="正文")
        self.assertTrue(self.store.upsert_article(article))
        duplicate = Article(title="标题", source_key="k1", markdown="正文")
        self.assertFalse(self.store.upsert_article(duplicate))

    def test_status_transitions(self):
        from gzh.models import Article

        article = Article(title="状态流转", source_key="k2", markdown="正文", plan_id="p1")
        self.store.upsert_article(article)
        self.store.update_article(article.id, status=STATUS_APPROVED)
        self.assertEqual(self.store.get_article(article.id).status, STATUS_APPROVED)

    def test_quota_counting(self):
        from gzh.models import Article
        from gzh.store import now_iso

        for index in range(3):
            article = Article(title=f"稿件{index}", source_key=f"k{index}", markdown="正文", account_id="main")
            self.store.upsert_article(article)
            self.store.update_article(article.id, status=STATUS_DRAFTED, published_at=now_iso())
        self.assertEqual(self.store.count_status_today("main", STATUS_DRAFTED), 3)


class TestLocalSource(BaseCase):
    def test_fetch_and_parse(self):
        source = build_source({"type": "local", "path": "content"}, roots=[self.root / "content", self.root])
        articles = source.fetch()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "单元测试稿件")
        self.assertEqual(articles[0].tags, ["测试"])
        self.assertIn("正文段落", articles[0].markdown)

    def test_missing_directory(self):
        source = build_source({"type": "local", "path": "不存在"}, roots=[self.root])
        with self.assertRaises(Exception):
            source.fetch()


class TestRssSource(unittest.TestCase):
    RSS = """<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0"><channel>
      <title>示例订阅</title>
      <item>
        <title>第一条</title>
        <link>https://example.com/1</link>
        <guid>guid-1</guid>
        <description><![CDATA[<p>正文内容</p>]]></description>
        <category>技术</category>
      </item>
      <item>
        <title>第二条</title>
        <link>https://example.com/2</link>
        <guid>guid-2</guid>
        <description>纯文本摘要</description>
      </item>
    </channel></rss>"""

    def test_fetch(self):
        source = RssSource({"type": "rss", "url": "https://example.com/feed"}, http=FakeHttp(self.RSS))
        articles = source.fetch()
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "第一条")
        self.assertEqual(articles[0].source_url, "https://example.com/1")
        self.assertIn("正文内容", articles[0].source_html)
        self.assertIn("<p>", articles[1].source_html)

    def test_invalid_feed(self):
        source = RssSource({"type": "rss", "url": "https://example.com/feed"}, http=FakeHttp("不是 xml"))
        with self.assertRaises(Exception):
            source.fetch()


class TestPublisher(BaseCase):
    def test_collect_and_publish_draft(self):
        plan = self._plan()
        created, duplicated = self.publisher.collect(plan)
        self.assertEqual(created, 1)
        self.assertEqual(duplicated, 0)

        # 再次采集应被去重
        created, duplicated = self.publisher.collect(plan)
        self.assertEqual(created, 0)
        self.assertEqual(duplicated, 1)

        results = self.publisher.publish(plan)
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].status, STATUS_DRAFTED)
        self.assertEqual(len(self.fake.drafts), 1)
        self.assertEqual(self.fake.drafts[0]["title"], "单元测试稿件")

        article = self.store.list_articles()[0]
        self.assertEqual(article.status, STATUS_DRAFTED)
        self.assertTrue(article.media_id)
        self.assertEqual(self.publisher.quota_used(self.account, "draft"), 1)

    def test_publish_mode_creates_publish_id(self):
        plan = self._plan(mode="publish")
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].status, STATUS_PUBLISHED)
        self.assertEqual(results[0].publish_id, "publish_id_1")
        self.assertEqual(results[0].article_id_wechat, "article_id_1")

    def test_mass_mode_sends(self):
        plan = self._plan(mode="mass")
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].status, STATUS_MASS_SENT)
        self.assertEqual(len(self.fake.passed), 1)

    def test_mass_mode_falls_back_when_no_publish_permission(self):
        """账号没有发布能力时，自动降级为用草稿 media_id 群发。"""
        fake = FakeWeChat(fail_on="submit")
        self.publisher._clients["main"] = fake
        plan = self._plan(mode="mass")
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertTrue(results[0].ok)
        self.assertEqual(results[0].status, STATUS_MASS_SENT)
        self.assertEqual(fake.passed, ["media_id_1"])

    def test_mass_mode_strict_article_id_fails_on_permission_error(self):
        fake = FakeWeChat(fail_on="submit")
        self.publisher._clients["main"] = fake
        plan = self._plan(mode="mass", mass_media_id_source="article_id")
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertFalse(results[0].ok)
        self.assertEqual(results[0].status, STATUS_FAILED)

    def test_quota_blocks_second_publish(self):
        plan = self._plan(mode="mass")
        self.config.policies["quota"]["mass_per_day"] = 0
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertEqual(results, [])

    def test_approval_gate(self):
        plan = self._plan(require_approval=True)
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertEqual(results[0].status, STATUS_BLOCKED)
        self.assertEqual(len(self.fake.drafts), 0)

        article = self.store.list_articles()[0]
        self.store.update_article(article.id, status=STATUS_APPROVED)
        article.status = STATUS_APPROVED
        results = self.publisher.publish(plan)
        self.assertTrue(results[0].ok)

    def test_failure_is_recorded(self):
        self.publisher._clients["main"] = FakeWeChat(fail_on="draft")
        plan = self._plan()
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertFalse(results[0].ok)
        self.assertEqual(results[0].status, STATUS_FAILED)
        article = self.store.list_articles()[0]
        self.assertEqual(article.status, STATUS_FAILED)
        self.assertEqual(article.attempts, 1)
        self.assertIn("48001", article.error)

    def test_dry_run_does_not_call_api(self):
        plan = self._plan()
        self.publisher.collect(plan)
        results = self.publisher.publish(plan, dry_run=True)
        self.assertTrue(results[0].dry_run)
        self.assertEqual(len(self.fake.drafts), 0)
        self.assertEqual(self.fake.thumbs, 0)

    def test_render_inlines_styles(self):
        plan = self._plan()
        self.publisher.collect(plan)
        self.publisher.publish(plan)
        draft = self.fake.drafts[0]
        self.assertIn("style=", draft["content"])
        self.assertNotIn("<script", draft["content"])

    def test_forbidden_keyword_blocks_publish(self):
        """命中红线关键词的稿件在写操作之前被拦下。"""
        self.config.policies["forbidden_keywords"] = ["正文段落"]
        plan = self._plan()
        self.publisher.collect(plan)
        results = self.publisher.publish(plan)
        self.assertFalse(results[0].ok)
        self.assertEqual(results[0].status, STATUS_BLOCKED)
        self.assertIn("正文段落", results[0].error)
        self.assertEqual(len(self.fake.drafts), 0)


if __name__ == "__main__":
    unittest.main()
