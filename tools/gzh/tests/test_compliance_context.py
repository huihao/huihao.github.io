"""红线关键词的语境判断测试。

广告法要拦的是「行业第一」这种最高级表述；「第一条」「第一次」「第一财经」
是普通行文，不该被拦。靠语境区分，而不是把词整个去掉。
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.pipeline.sanitize import check_compliance, plain_text

SAFE_CONTEXTS = {
    "第一": [
        r"\s*(?:条|件|次|级|位|人|轮|批|手|财|时|间|行|版|天|场|步|站|篇|道|类|种|份|张|的|点|代|届|波|款|项|则|要|梯|圈|个|句|反|直)",
    ]
}


class TestPlainText(unittest.TestCase):
    def test_strips_html_and_markdown_markers(self):
        text = plain_text("<p>是<strong>第一条</strong></p>", "**第一件**")
        self.assertIn("第一条", text)
        self.assertIn("第一件", text)

    def test_keeps_link_text(self):
        self.assertIn("原文", plain_text("看 [原文](https://example.com) 这里"))


class TestComplianceContext(unittest.TestCase):
    def test_ordinal_usage_passes(self):
        text = "只满足第一条、丢掉第二条的人。这是第一次，也是第一财经的报道。"
        hits = check_compliance(
            text, forbidden_keywords=["第一"], safe_contexts=SAFE_CONTEXTS
        )
        self.assertEqual(hits, [])

    def test_superlative_is_flagged(self):
        hits = check_compliance(
            "我们是行业第一。", forbidden_keywords=["第一"], safe_contexts=SAFE_CONTEXTS
        )
        self.assertIn("第一", hits)

    def test_mixed_usage_is_flagged(self):
        hits = check_compliance(
            "第一次见，但它确实是第一。",
            forbidden_keywords=["第一"],
            safe_contexts=SAFE_CONTEXTS,
        )
        self.assertIn("第一", hits)

    def test_without_safe_contexts_everything_is_flagged(self):
        hits = check_compliance("第一条", forbidden_keywords=["第一"])
        self.assertIn("第一", hits)

    def test_other_keywords_still_flagged(self):
        hits = check_compliance(
            "永久包治稳赚", forbidden_keywords=["最强", "第一", "永久", "包治", "稳赚"],
            safe_contexts=SAFE_CONTEXTS,
        )
        self.assertEqual(sorted(hits), sorted(["永久", "包治", "稳赚"]))

    def test_empty_inputs(self):
        self.assertEqual(check_compliance("", forbidden_keywords=["第一"]), [])
        self.assertEqual(check_compliance("随便", forbidden_keywords=[]), [])


if __name__ == "__main__":
    unittest.main()
