"""内容处理流水线。

* :mod:`gzh.pipeline.frontmatter` —— front matter 解析
* :mod:`gzh.pipeline.markdown`   —— Markdown → HTML
* :mod:`gzh.pipeline.css`        —— CSS 内联
* :mod:`gzh.pipeline.sanitize`   —— 微信兼容清洗
* :mod:`gzh.pipeline.images`     —— 正文图片转存
* :mod:`gzh.pipeline.render`     —— 组装草稿 payload
"""

from .css import DEFAULT_CSS, inline_css
from .frontmatter import parse_simple_yaml, split_front_matter
from .markdown import build_article_payload, make_digest, markdown_to_html
from .render import RenderedArticle, Renderer
from .sanitize import sanitize_html

__all__ = [
    "DEFAULT_CSS",
    "RenderedArticle",
    "Renderer",
    "build_article_payload",
    "inline_css",
    "make_digest",
    "markdown_to_html",
    "parse_simple_yaml",
    "sanitize_html",
    "split_front_matter",
]
