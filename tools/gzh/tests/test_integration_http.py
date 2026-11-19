"""端到端联调测试：用本地 HTTP 服务器验证网页源与订阅源。

这些测试会真的起一个 socket，因此比纯单元测试慢一点，但能覆盖
「抓取 → 解析 → 字段映射」这条最容易出问题的链路。
"""

from __future__ import annotations

import http.server
import socketserver
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from gzh.http import HttpClient
from gzh.sources import build_source

LISTING = """<html><body>
<article class="post"><h2>第一篇：联调文章</h2><a href="/a1.html">阅读全文</a></article>
<article class="post"><h2>第二篇：表格</h2><a href="/a2.html">阅读全文</a></article>
</body></html>"""

ARTICLE_1 = """<html><body><article class="post-content"><h1>联调文章</h1>
<p>这是<strong>正文</strong>内容。</p><ul><li>要点一</li><li>要点二</li></ul>
<img src="/img/pic.png" /></article></body></html>"""

ARTICLE_2 = """<html><body><div class="post-content"><h1>第二篇</h1>
<table><tr><th>列A</th><th>列B</th></tr><tr><td>1</td><td>2</td></tr></table></div></body></html>"""

FEED = """<?xml version="1.0"?><rss version="2.0"><channel><title>本地订阅</title>
<item><title>订阅条目一</title><link>http://127.0.0.1:{port}/a1.html</link><guid>g1</guid>
<description><![CDATA[<p>来自 RSS 的正文</p>]]></description><category>技术</category></item>
</channel></rss>"""

JSON_FEED = """{"version":"https://jsonfeed.org/version/1.1","items":[
 {"id":"j1","url":"http://127.0.0.1:__PORT__/a1.html","title":"JSON 条目",
  "content_html":"<p>JSON 正文</p>","summary":"JSON 摘要","tags":["测试"]}]}"""

PLAIN_PAGE = """<html><body><p>没有任何条目块</p></body></html>"""


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, *args):  # noqa: D102 - 静默日志
        pass

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler 约定
        path = self.path.split("?")[0]
        port = self.server.server_address[1]
        if path == "/":
            body, ctype = LISTING, "text/html; charset=utf-8"
        elif path == "/a1.html":
            body, ctype = ARTICLE_1, "text/html; charset=utf-8"
        elif path == "/a2.html":
            body, ctype = ARTICLE_2, "text/html; charset=utf-8"
        elif path == "/feed.xml":
            body, ctype = FEED.replace("{port}", str(port)), "application/xml"
        elif path == "/feed.json":
            body, ctype = JSON_FEED.replace("__PORT__", str(port)), "application/json"
        elif path == "/plain.html":
            body, ctype = PLAIN_PAGE, "text/html; charset=utf-8"
        else:
            body, ctype = "", "text/plain"
        data = body.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


class TestSourcesOverHttp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = socketserver.TCPServer(("127.0.0.1", 0), Handler)
        cls.port = cls.server.server_address[1]
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.http = HttpClient(timeout=10, min_interval=0)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()

    def _url(self, path: str) -> str:
        return f"http://127.0.0.1:{self.port}{path}"

    def test_http_listing_source(self):
        source = build_source(
            {
                "type": "http",
                "url": self._url("/"),
                "selector": {
                    "item": "article.post",
                    "title": "h2",
                    "link": "a",
                    "content": {"tag": "article", "class": "post-content"},
                },
                "limit": 5,
            },
            roots=[],
            http=self.http,
        )
        articles = source.fetch()
        self.assertEqual(len(articles), 2)
        self.assertEqual(articles[0].title, "第一篇：联调文章")
        self.assertTrue(articles[0].source_url.endswith("/a1.html"))
        self.assertIn("要点一", articles[0].source_html)
        self.assertIn('<img src="/img/pic.png"', articles[0].source_html)
        self.assertIn("<table", articles[1].source_html)

    def test_http_single_page(self):
        source = build_source(
            {"type": "http", "url": self._url("/a1.html"), "single": True}, roots=[], http=self.http
        )
        articles = source.fetch()
        self.assertEqual(len(articles), 1)
        self.assertIn("要点一", articles[0].source_html)

    def test_rss_source(self):
        source = build_source({"type": "rss", "url": self._url("/feed.xml")}, roots=[], http=self.http)
        articles = source.fetch()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "订阅条目一")
        self.assertIn("RSS", articles[0].source_html)
        self.assertEqual(articles[0].tags, ["技术"])

    def test_jsonfeed_source(self):
        source = build_source({"type": "jsonfeed", "url": self._url("/feed.json")}, roots=[], http=self.http)
        articles = source.fetch()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0].title, "JSON 条目")
        self.assertIn("JSON 正文", articles[0].source_html)
        self.assertEqual(articles[0].tags, ["测试"])

    def test_http_source_reports_failure(self):
        """页面上没有任何条目块时应明确报错，而不是静默返回空列表。"""
        source = build_source(
            {"type": "http", "url": self._url("/plain.html"), "selector": {"item": "article.post"}},
            roots=[],
            http=self.http,
        )
        with self.assertRaises(Exception):
            source.fetch()


if __name__ == "__main__":
    unittest.main()
