"""正文图片处理。

微信公众号正文中的 ``img`` 必须指向微信自己的域名（``mmbiz.qpic.cn`` 等），
否则会裂图或被防盗链拦截。因此本模块把：

* 本地图片（相对内容资源库的路径）→ 通过 ``media/uploadimg`` 上传，替换为微信 URL
* 远程图片（http/https）→ 可选下载后转存到微信，替换为微信 URL

上传结果按内容哈希缓存到 ``blobs`` 表，重复内容不会重复占用素材配额。
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable

from ..errors import RenderError
from ..http import HttpClient

IMG_TAG_RE = re.compile(r"<img\b[^>]*>", re.IGNORECASE)
SRC_ATTR_RE = re.compile(r"""src\s*=\s*(?:"([^"]*)"|'([^']*)'|([^\s>]+))""", re.IGNORECASE)

#: 允许直接保留（不转存）的图片域名白名单。
DEFAULT_KEEP_DOMAINS = ("mmbiz.qpic.cn", "qpic.cn", "wx.qlogo.cn", "res.wx.qq.com")


class ImageUploader:
    """把正文图片转换成微信可用的 URL。"""

    def __init__(
        self,
        *,
        client: object,
        store: object,
        logger: object = None,
        http: HttpClient | None = None,
        content_roots: Iterable[Path] = (),
        upload_remote: bool = True,
        max_bytes: int = 1024 * 1024,
        keep_domains: Iterable[str] = DEFAULT_KEEP_DOMAINS,
    ) -> None:
        self.client = client
        self.store = store
        self.logger = logger
        self.http = http
        self.content_roots = [Path(p) for p in content_roots]
        self.upload_remote = upload_remote
        self.max_bytes = max_bytes
        self.keep_domains = tuple(keep_domains)

    # ------------------------------------------------------------------ 工具
    def _resolve_local(self, src: str) -> Path | None:
        """把相对路径解析为本地文件。"""
        if not src or src.startswith(("http://", "https://", "data:", "//")):
            return None
        candidate = Path(src)
        if candidate.is_absolute():
            return candidate if candidate.is_file() else None
        for root in self.content_roots:
            resolved = (root / candidate).resolve()
            if resolved.is_file():
                return resolved
        return None

    def _is_kept_domain(self, src: str) -> bool:
        return any(domain in src for domain in self.keep_domains)

    def _cached_url(self, digest: str) -> str:
        blob = self.store.get_blob("content_image", digest)
        return blob["url"] if blob else ""

    def _remember(self, digest: str, url: str) -> None:
        self.store.put_blob("content_image", digest, url=url)

    # ------------------------------------------------------------------ 主流程
    def process(self, html: str) -> str:
        """处理 HTML 中的所有图片，返回替换后的 HTML。"""
        if not html or "<img" not in html.lower():
            return html

        def replace(match: re.Match[str]) -> str:
            tag = match.group(0)
            src_match = SRC_ATTR_RE.search(tag)
            if not src_match:
                return tag
            src = next((g for g in src_match.groups() if g), "").strip()
            if not src:
                return tag
            if src.startswith("data:"):
                return tag  # base64 内联图保留原样（体积大，微信可能拒绝）
            if self._is_kept_domain(src):
                return tag

            local = self._resolve_local(src)
            try:
                if local is not None:
                    url = self._upload_file(local)
                elif src.startswith(("http://", "https://")):
                    if not self.upload_remote:
                        return tag
                    url = self._upload_remote(src)
                else:
                    raise RenderError(f"正文图片不存在或路径无法解析: {src}")
            except RenderError:
                raise
            except Exception as exc:  # noqa: BLE001 - 网络类异常统一转成渲染错误
                raise RenderError(f"正文图片处理失败: {src} ({exc})") from exc

            if not url:
                return tag
            return SRC_ATTR_RE.sub(f'src="{url}"', tag, count=1)

        return IMG_TAG_RE.sub(replace, html)

    def _upload_file(self, path: Path) -> str:
        content = path.read_bytes()
        if len(content) > self.max_bytes:
            raise RenderError(
                f"图片 {path.name} 体积 {len(content) / 1024:.0f}KB 超过 {self.max_bytes / 1024:.0f}KB 限制"
            )
        digest = hashlib.sha256(content).hexdigest()
        cached = self._cached_url(digest)
        if cached:
            return cached
        url = self.client.upload_content_image(path)
        if not url:
            raise RenderError(f"图片上传未返回 URL: {path.name}")
        self._remember(digest, url)
        if self.logger:
            self.logger.info(
                "正文图片已上传",
                extra={"context": {"image": path.name, "url": url}},
            )
        return url

    def _upload_remote(self, url: str) -> str:
        if self.http is None:
            return url
        content = self.http.download(url)
        if len(content) > self.max_bytes:
            if self.logger:
                self.logger.warning(
                    "远程图片超过体积上限，保留原链接",
                    extra={"context": {"url": url, "bytes": len(content)}},
                )
            return url
        digest = hashlib.sha256(content).hexdigest()
        cached = self._cached_url(digest)
        if cached:
            return cached

        # 复用本地文件上传通道：先落到临时文件再上传
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".img", delete=False) as tmp:
            tmp.write(content)
            temp_path = Path(tmp.name)
        try:
            uploaded = self.client.upload_content_image(temp_path)
        finally:
            temp_path.unlink(missing_ok=True)
        if not uploaded:
            return url
        self._remember(digest, uploaded)
        return uploaded
