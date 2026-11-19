"""内容处理流水线测试。"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.pipeline.css import DEFAULT_CSS, inline_css, parse_css
from gzh.pipeline.frontmatter import parse_simple_yaml, split_front_matter
from gzh.pipeline.markdown import make_digest, markdown_to_html
from gzh.pipeline.render import make_placeholder_png
from gzh.pipeline.sanitize import sanitize_html


class TestFrontMatter(unittest.TestCase):
    def test_split_and_parse(self):
        text = """---
title: "测试标题"
author: 张三
tags: [AI, 效率]
need_open_comment: 0
published: true
---

正文第一行
正文第二行
"""
        meta, body = split_front_matter(text)
        self.assertEqual(meta["title"], "测试标题")
        self.assertEqual(meta["author"], "张三")
        self.assertEqual(meta["tags"], ["AI", "效率"])
        self.assertEqual(meta["need_open_comment"], 0)
        self.assertIs(meta["published"], True)
        self.assertTrue(body.strip().startswith("正文第一行"))
        self.assertNotIn("---", body)

    def test_no_front_matter(self):
        meta, body = split_front_matter("只有正文\n")
        self.assertEqual(meta, {})
        self.assertEqual(body, "只有正文\n")

    def test_block_list(self):
        meta, _ = split_front_matter("---\ntags:\n  - 甲\n  - 乙\n---\n正文")
        self.assertEqual(meta["tags"], ["甲", "乙"])

    def test_nested_mapping(self):
        result = parse_simple_yaml("meta:\n  author: 李四\n  id: 7")
        self.assertEqual(result["meta"], {"author": "李四", "id": 7})

    def test_comma_in_quotes(self):
        result = parse_simple_yaml('title: "逗号, 在里面"')
        self.assertEqual(result["title"], "逗号, 在里面")


class TestMarkdown(unittest.TestCase):
    def test_headings_and_paragraph(self):
        html = markdown_to_html("# 标题\n\n一段话。")
        self.assertIn("<h1", html)
        self.assertIn("标题", html)
        self.assertIn("<p", html)

    def test_bold_italic_link_image(self):
        html = markdown_to_html("**粗** *斜* [链接](https://a.com) ![图](a.png)")
        self.assertIn("<strong", html)
        self.assertIn("<em", html)
        self.assertIn('href="https://a.com"', html)
        self.assertIn('<img', html)
        self.assertIn('src="a.png"', html)

    def test_lists(self):
        html = markdown_to_html("- 甲\n- 乙\n\n1. 一\n2. 二")
        self.assertIn("<ul", html)
        self.assertIn("<ol", html)
        self.assertEqual(html.count("<li"), 4)

    def test_quote_and_code_and_table(self):
        html = markdown_to_html("> 引用\n\n```py\nprint(1)\n```\n\n| a | b |\n| --- | --- |\n| 1 | 2 |")
        self.assertIn("<blockquote", html)
        self.assertIn("<pre", html)
        self.assertIn("<table", html)
        self.assertIn("<td", html)

    def test_script_is_escaped(self):
        html = markdown_to_html("<script>alert(1)</script>")
        self.assertNotIn("<script", html)

    def test_allowed_raw_html_preserved(self):
        html = markdown_to_html("<span class=\"x\">保留</span>")
        self.assertIn("<span", html)

    def test_digest(self):
        digest = make_digest("<p>" + "这是一段很长很长的中文摘要。" * 20 + "</p>", 50)
        self.assertLessEqual(len(digest), 51)
        self.assertTrue(digest.endswith("…") or digest.endswith("。"))


class TestCss(unittest.TestCase):
    def test_inline_applies_to_matching_tags(self):
        html = inline_css('<p class="gzh-p">正文</p>', DEFAULT_CSS)
        self.assertIn("style=", html)
        self.assertIn("font-size: 16px", html)

    def test_inline_merges_existing_style(self):
        html = inline_css('<p class="gzh-p" style="color: red;">正文</p>', "p.gzh-p { font-size: 15px; }")
        self.assertIn("color: red", html)
        self.assertIn("font-size: 15px", html)

    def test_parse_rules(self):
        rules = parse_css("p { color: #333; } .x { margin: 0; }")
        self.assertEqual(len(rules), 2)
        self.assertEqual(rules[0].declarations["color"], "#333")

    def test_id_selector(self):
        html = inline_css('<p id="lead">正文</p>', "#lead { color: blue; }")
        self.assertIn("color: blue", html)


class TestSanitize(unittest.TestCase):
    def test_removes_script_with_content(self):
        html = sanitize_html("<p>安全</p><script>alert(1)</script>")
        self.assertNotIn("script", html)
        self.assertIn("安全", html)

    def test_removes_event_handlers(self):
        html = sanitize_html('<p onclick="evil()">文本</p>')
        self.assertNotIn("onclick", html)

    def test_removes_javascript_url(self):
        html = sanitize_html('<a href="javascript:alert(1)">点</a>')
        self.assertNotIn("javascript:", html)

    def test_keeps_safe_links(self):
        html = sanitize_html('<a href="https://a.com">点</a>')
        self.assertIn("https://a.com", html)

    def test_strips_fixed_position(self):
        html = sanitize_html('<p style="position: fixed; color: red;">文本</p>')
        self.assertNotIn("fixed", html)
        self.assertIn("color: red", html)


class TestPlaceholder(unittest.TestCase):
    def test_png_signature(self):
        data = make_placeholder_png(16, 8)
        self.assertTrue(data.startswith(b"\x89PNG\r\n\x1a\n"))
        self.assertGreater(len(data), 50)


if __name__ == "__main__":
    unittest.main()
