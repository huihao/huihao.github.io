"""文章池字段的落库—读回往返测试。

articles 表没有 content_source_url / need_open_comment / only_fans_can_comment
这几列，写库时塞进 extra，读回时必须还原——否则「阅读原文」链接和留言开关
会在入库那一刻丢掉（草稿里就成空的了）。
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.models import Article
from gzh.store import Store, article_extra


class TestArticleRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = Store(Path(self.tmp.name) / "state.db")

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def _article(self) -> Article:
        return Article(
            title="前端岗位的消失论",
            source_key="k-round-trip",
            markdown="正文",
            content_hash="hash-round-trip",
            source_url="https://bio.wuhh.cc/2026/11/17/ai-frontend-role-evolution.html",
            content_source_url="https://bio.wuhh.cc/2026/11/17/ai-frontend-role-evolution.html",
            need_open_comment=1,
            only_fans_can_comment=0,
            publish_at="2026-11-18 21:30",
            extra={"自定义键": "值"},
        )

    def test_fields_survive_upsert_and_load(self):
        article = self._article()
        self.assertTrue(self.store.upsert_article(article))

        loaded = self.store.get_article(article.id)
        self.assertIsNotNone(loaded)
        assert loaded is not None
        self.assertEqual(loaded.content_source_url, article.content_source_url)
        self.assertEqual(loaded.need_open_comment, 1)
        self.assertEqual(loaded.only_fans_can_comment, 0)
        self.assertEqual(loaded.publish_at, "2026-11-18 21:30")
        self.assertEqual(loaded.extra.get("自定义键"), "值")

    def test_extra_keeps_custom_keys(self):
        extra = article_extra(self._article())
        self.assertEqual(extra["自定义键"], "值")
        self.assertEqual(extra["content_source_url"], self._article().content_source_url)
        self.assertEqual(extra["need_open_comment"], 1)

    def test_extra_omits_defaults(self):
        extra = article_extra(Article(title="普通文章", source_key="k-plain"))
        self.assertNotIn("content_source_url", extra)
        self.assertNotIn("need_open_comment", extra)
        self.assertNotIn("publish_at", extra)

    def test_missing_columns_do_not_break_load(self):
        """旧库里的行没有这些字段，读回也不该报错。"""
        article = Article(title="旧数据", source_key="k-old", markdown="正文")
        self.store.upsert_article(article)
        loaded = self.store.get_article(article.id)
        assert loaded is not None
        self.assertEqual(loaded.content_source_url, "")
        self.assertEqual(loaded.need_open_comment, 0)


if __name__ == "__main__":
    unittest.main()
