"""基于标准库的 HTTP 客户端。

只依赖 ``urllib.request``，但补齐了生产环境需要的四件事：

1. 超时与指数退避重试（网络抖动、5xx、429）。
2. 统一错误分类（可重试 / 不可重试）。
3. multipart/form-data 编码（素材与图片上传）。
4. 最小调用间隔限速，避免触发微信侧 QPS 限制。
"""

from __future__ import annotations

import gzip
import json
import mimetypes
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .errors import GzhError

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (compatible; gzh-scheduler/1.0; +https://github.com/) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
)


class HttpError(GzhError):
    """HTTP 层错误。"""

    def __init__(self, message: str, *, status: int = 0, retryable: bool = False, url: str = ""):
        self.status = status
        self.retryable = retryable
        self.url = url
        super().__init__(message)


@dataclass
class HttpResponse:
    """一次 HTTP 响应的封装。"""

    status: int
    headers: dict[str, str]
    body: bytes
    url: str

    def text(self, encoding: str = "utf-8") -> str:
        return self.body.decode(encoding, errors="replace")

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8", errors="replace"))


class HttpClient:
    """带重试与限速的 HTTP 客户端。"""

    def __init__(
        self,
        *,
        timeout: float = 20.0,
        retries: int = 3,
        backoff: float = 1.6,
        min_interval: float = 0.15,
        user_agent: str = DEFAULT_USER_AGENT,
        logger: Any = None,
    ) -> None:
        self.timeout = timeout
        self.retries = max(1, retries)
        self.backoff = backoff
        self.min_interval = min_interval
        self.user_agent = user_agent
        self.logger = logger
        self._last_request_at = 0.0

    # ------------------------------------------------------------------ 内部
    def _throttle(self) -> None:
        elapsed = time.monotonic() - self._last_request_at
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        self._last_request_at = time.monotonic()

    def _decode_body(self, response: Any, body: bytes) -> bytes:
        encoding = (response.headers.get("Content-Encoding") or "").lower()
        if encoding == "gzip":
            try:
                return gzip.decompress(body)
            except OSError:
                return body
        if encoding == "deflate":
            try:
                return zlib.decompress(body, -zlib.MAX_WBITS)
            except zlib.error:
                try:
                    return zlib.decompress(body)
                except zlib.error:
                    return body
        return body

    # ------------------------------------------------------------------ 公开
    def request(
        self,
        method: str,
        url: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        data: bytes | None = None,
        headers: dict[str, str] | None = None,
        timeout: float | None = None,
        retries: int | None = None,
        allow_retry: Callable[[int], bool] | None = None,
    ) -> HttpResponse:
        """发起请求并返回响应；失败时按退避策略重试。"""
        if params:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{urllib.parse.urlencode(params, doseq=True)}"

        final_headers = {
            "User-Agent": self.user_agent,
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "close",
        }
        body: bytes | None = data
        if json_body is not None:
            body = json.dumps(json_body, ensure_ascii=False).encode("utf-8")
            final_headers["Content-Type"] = "application/json; charset=utf-8"
        if headers:
            final_headers.update(headers)

        attempts = self.retries if retries is None else max(1, retries)
        last_error: Exception | None = None

        for attempt in range(1, attempts + 1):
            self._throttle()
            request = urllib.request.Request(url, data=body, headers=final_headers, method=method.upper())
            try:
                with urllib.request.urlopen(request, timeout=timeout or self.timeout) as response:
                    raw = response.read()
                    return HttpResponse(
                        status=response.status,
                        headers={k.lower(): v for k, v in response.headers.items()},
                        body=self._decode_body(response, raw),
                        url=response.geturl(),
                    )
            except urllib.error.HTTPError as exc:  # 服务端返回了 4xx/5xx
                raw = exc.read()
                status = exc.code
                retryable = status >= 500 or status == 429 or status == 408
                if allow_retry is not None:
                    retryable = allow_retry(status)
                if not retryable or attempt >= attempts:
                    raise HttpError(
                        f"HTTP {status} {url}: {raw[:300].decode('utf-8', 'replace')}",
                        status=status,
                        retryable=retryable,
                        url=url,
                    ) from exc
                last_error = exc
                self._sleep_backoff(attempt, url, status)
            except (urllib.error.URLError, TimeoutError, OSError) as exc:
                last_error = exc
                if attempt >= attempts:
                    raise HttpError(
                        f"网络请求失败 {url}: {exc}", status=0, retryable=True, url=url
                    ) from exc
                self._sleep_backoff(attempt, url, 0)

        raise HttpError(f"请求失败 {url}: {last_error}", status=0, retryable=True, url=url)

    def _sleep_backoff(self, attempt: int, url: str, status: int) -> None:
        delay = self.backoff ** attempt
        if self.logger:
            self.logger.warning(
                "请求失败，准备重试",
                extra={"context": {"url": url, "status": status, "attempt": attempt, "delay": round(delay, 2)}},
            )
        time.sleep(delay)

    def get_json(self, url: str, **kwargs: Any) -> Any:
        response = self.request("GET", url, **kwargs)
        return response.json()

    def post_json(self, url: str, payload: Any, **kwargs: Any) -> Any:
        response = self.request("POST", url, json_body=payload, **kwargs)
        return response.json()

    def download(self, url: str, **kwargs: Any) -> bytes:
        """下载二进制内容（用于远程图片）。"""
        response = self.request("GET", url, **kwargs)
        if response.status >= 400:
            raise HttpError(f"下载失败 {url}: HTTP {response.status}", status=response.status, url=url)
        return response.body

    def upload_multipart(
        self,
        url: str,
        *,
        fields: dict[str, str] | None = None,
        files: list[tuple[str, str, bytes, str]] | None = None,
        **kwargs: Any,
    ) -> HttpResponse:
        """multipart/form-data 上传。

        Args:
            url: 目标地址。
            fields: 普通字段。
            files: (字段名, 文件名, 内容, content_type) 列表。
        """
        boundary = "----gzhboundary" + uuid.uuid4().hex
        buf = bytearray()
        for key, value in (fields or {}).items():
            buf += f"--{boundary}\r\n".encode()
            buf += f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode()
            buf += str(value).encode("utf-8") + b"\r\n"
        for field_name, filename, content, content_type in files or []:
            buf += f"--{boundary}\r\n".encode()
            buf += (
                f'Content-Disposition: form-data; name="{field_name}"; filename="{filename}"\r\n'
            ).encode()
            buf += f"Content-Type: {content_type}\r\n\r\n".encode()
            buf += content + b"\r\n"
        buf += f"--{boundary}--\r\n".encode()

        headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
        return self.request("POST", url, data=bytes(buf), headers=headers, **kwargs)


def guess_content_type(path: Path | str) -> str:
    """根据文件名猜测 Content-Type。"""
    guessed, _ = mimetypes.guess_type(str(path))
    return guessed or "application/octet-stream"


def safe_filename(name: str) -> str:
    """把任意来源的文件名规整成可上传的安全文件名。"""
    keep = [c for c in name if c.isalnum() or c in "._-"]
    cleaned = "".join(keep) or "image.png"
    return cleaned[:100]
