"""微信公众平台 API 客户端。

关键实现要点（详见 docs/api-notes.md）：

* 令牌统一走 **stable_token** 稳定版接口，避免同一主体多应用互相顶号。
* 令牌本地缓存（SQLite ``kv``），过期前 5 分钟自动续期；遇到 40001 强制刷新并重试一次。
* 草稿 → 发布 → 群发 三条链路各自封装，调用方只关心业务语义。
* 所有错误统一抛出 :class:`WechatAPIError`，携带错误码与处置建议。
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config import Account
from ..errors import ConfigError, WechatAPIError
from ..http import HttpClient, guess_content_type, safe_filename

API_BASE = "https://api.weixin.qq.com"

#: 令牌提前续期的时间余量（秒）。
TOKEN_REFRESH_MARGIN = 300

#: 永久缩略图素材（封面）建议体积上限：64KB。
THUMB_MAX_BYTES = 64 * 1024

#: 正文图片建议体积上限：1MB。
IMAGE_MAX_BYTES = 1024 * 1024

#: freepublish/get 的发布状态。
PUBLISH_STATUS = {
    0: "发布成功",
    1: "发布中",
    2: "原样返回",
    3: "发布失败",
    4: "成功但无实际内容",
}


@dataclass
class WeChatResult:
    """微信接口的原始返回（已剥离 errcode/errmsg）。"""

    data: dict[str, Any]
    raw: dict[str, Any]


class WeChatClient:
    """单个公众号账号的接口客户端。"""

    def __init__(
        self,
        account: Account,
        store: Any,
        http: HttpClient,
        logger: Any = None,
        *,
        base_url: str = API_BASE,
    ) -> None:
        self.account = account
        self.store = store
        self.http = http
        self.logger = logger
        self.base_url = base_url.rstrip("/")
        self._token_value: str = ""
        self._token_expires_at: float = 0.0

    # -------------------------------------------------------------- 令牌
    def _token_cache_key(self) -> str:
        return f"token:{self.account.id}"

    def token(self, force: bool = False) -> str:
        """获取（必要时刷新）access_token。"""
        if not self.account.app_id or not self.account.app_secret:
            raise ConfigError(
                f"账号 {self.account.id} 的凭据未就绪（app_id/app_secret 为空）。"
                f"请注入 WECHAT_APPID / WECHAT_APPSECRET 等环境变量。"
            )
        if not force and self._token_value and self._token_expires_at - time.time() > TOKEN_REFRESH_MARGIN:
            return self._token_value

        cached = self.store.kv_get(self._token_cache_key()) or {}
        now = time.time()
        if (
            not force
            and cached.get("token")
            and float(cached.get("expires_at", 0)) - now > TOKEN_REFRESH_MARGIN
        ):
            self._token_value = cached["token"]
            self._token_expires_at = float(cached["expires_at"])
            return self._token_value

        payload = {
            "grant_type": "client_credential",
            "appid": self.account.app_id,
            "secret": self.account.app_secret,
            "force_refresh": bool(force),
        }
        response = self.http.post_json(
            f"{self.base_url}/cgi-bin/stable_token", payload, retries=2
        )
        if not isinstance(response, dict):
            raise WechatAPIError(-1, f"stable_token 返回异常: {response!r}", path="/cgi-bin/stable_token")
        if int(response.get("errcode", 0)) != 0:
            raise WechatAPIError(
                int(response.get("errcode", -1)),
                str(response.get("errmsg", "获取 access_token 失败")),
                path="/cgi-bin/stable_token",
                payload={"appid": self.account.app_id},
            )

        token = str(response.get("access_token", ""))
        if not token:
            raise WechatAPIError(-1, "stable_token 未返回 access_token", path="/cgi-bin/stable_token")
        expires_in = int(response.get("expires_in", 7200))
        expires_at = now + max(60, expires_in - 60)
        self._token_value = token
        self._token_expires_at = expires_at
        self.store.kv_set(
            self._token_cache_key(),
            {
                "token": token,
                "expires_at": expires_at,
                "obtained_at": now,
                "appid": self.account.app_id,
            },
        )
        if self.logger:
            self.logger.info(
                "access_token 已刷新",
                extra={
                    "context": {
                        "account": self.account.id,
                        "expires_in": expires_in,
                        "forced": bool(force),
                    }
                },
            )
        return token

    # -------------------------------------------------------------- 底层调用
    def _call(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json_body: Any = None,
        files: list[tuple[str, str, bytes, str]] | None = None,
        fields: dict[str, str] | None = None,
        retry_on_token_error: bool = True,
    ) -> WeChatResult:
        """调用微信接口并处理错误码。"""
        token = self.token()
        query = {"access_token": token, **(params or {})}
        url = f"{self.base_url}{path}"

        if files is not None:
            response = self.http.upload_multipart(url, fields=fields, files=files, params=query)
            body_text = response.text()
        elif method.upper() == "GET":
            response = self.http.request("GET", url, params=query)
            body_text = response.text()
        else:
            response = self.http.request("POST", url, json_body=json_body, params=query)
            body_text = response.text()

        try:
            import json as _json

            payload = _json.loads(body_text)
        except ValueError as exc:
            raise WechatAPIError(
                -1, f"接口返回非 JSON 内容: {body_text[:200]}", path=path, payload=body_text[:200]
            ) from exc

        if not isinstance(payload, dict):
            raise WechatAPIError(-1, f"接口返回结构异常: {payload!r}", path=path)

        code = int(payload.get("errcode", 0) or 0)
        if code != 0:
            message = str(payload.get("errmsg", "未知错误"))
            if code in WechatAPIError.TOKEN_ERROR_CODES and retry_on_token_error:
                if self.logger:
                    self.logger.warning(
                        "access_token 失效，强制刷新后重试",
                        extra={"context": {"account": self.account.id, "path": path, "code": code}},
                    )
                self.token(force=True)
                return self._call(
                    method,
                    path,
                    params=params,
                    json_body=json_body,
                    files=files,
                    fields=fields,
                    retry_on_token_error=False,
                )
            raise WechatAPIError(code, message, path=path, payload=_safe_payload(payload))

        data = {k: v for k, v in payload.items() if k not in ("errcode", "errmsg")}
        return WeChatResult(data=data, raw=payload)

    # -------------------------------------------------------------- 素材/图片
    def upload_thumb(self, path: Path | str) -> dict[str, str]:
        """上传永久缩略图素材（封面），返回 media_id 与 url。"""
        file_path = Path(path)
        if not file_path.is_file():
            raise WechatAPIError(-1, f"封面文件不存在: {file_path}", path="/cgi-bin/material/add_material")
        content = file_path.read_bytes()
        if len(content) > THUMB_MAX_BYTES:
            raise WechatAPIError(
                -1,
                f"封面文件 {len(content) / 1024:.0f}KB 超过微信 64KB 限制，请压缩后重试",
                path="/cgi-bin/material/add_material",
            )
        result = self._call(
            "POST",
            "/cgi-bin/material/add_material",
            params={"type": "thumb"},
            files=[("media", safe_filename(file_path.name), content, guess_content_type(file_path))],
        )
        return {"media_id": str(result.data.get("media_id", "")), "url": str(result.data.get("url", ""))}

    def upload_content_image(self, path: Path | str) -> str:
        """上传正文图片，返回微信域名 URL（正文 img 的 src 必须是该 URL）。"""
        file_path = Path(path)
        if not file_path.is_file():
            raise WechatAPIError(-1, f"图片文件不存在: {file_path}", path="/cgi-bin/media/uploadimg")
        content = file_path.read_bytes()
        if len(content) > IMAGE_MAX_BYTES:
            raise WechatAPIError(
                -1,
                f"图片文件 {len(content) / 1024:.0f}KB 超过微信 1MB 限制，请压缩后重试",
                path="/cgi-bin/media/uploadimg",
            )
        result = self._call(
            "POST",
            "/cgi-bin/media/uploadimg",
            files=[("media", safe_filename(file_path.name), content, guess_content_type(file_path))],
        )
        return str(result.data.get("url", ""))

    # -------------------------------------------------------------- 草稿/发布
    def add_draft(self, article: dict[str, Any]) -> str:
        """创建草稿，返回草稿 media_id。"""
        result = self._call("POST", "/cgi-bin/draft/add", json_body={"articles": [article]})
        media_id = str(result.data.get("media_id", ""))
        if not media_id:
            raise WechatAPIError(-1, "draft/add 未返回 media_id", path="/cgi-bin/draft/add")
        return media_id

    def submit_publish(self, media_id: str) -> str:
        """提交发布，返回 publish_id。"""
        result = self._call(
            "POST", "/cgi-bin/freepublish/submit", json_body={"media_id": media_id}
        )
        publish_id = str(result.data.get("publish_id", ""))
        if not publish_id:
            raise WechatAPIError(-1, "freepublish/submit 未返回 publish_id", path="/cgi-bin/freepublish/submit")
        return publish_id

    def get_publish(self, publish_id: str) -> dict[str, Any]:
        """查询发布结果（publish_status / article_id）。"""
        result = self._call("GET", "/cgi-bin/freepublish/get", params={"publish_id": publish_id})
        return result.data

    def wait_publish(
        self, publish_id: str, *, timeout: float = 120.0, interval: float = 5.0
    ) -> dict[str, Any]:
        """轮询直到发布完成或超时。"""
        deadline = time.time() + timeout
        last: dict[str, Any] = {}
        while time.time() < deadline:
            last = self.get_publish(publish_id)
            status = int(last.get("publish_status", -1))
            if status == 0:
                return last
            if status in (3, 4):
                raise WechatAPIError(
                    -1,
                    f"发布未成功（publish_status={status} {PUBLISH_STATUS.get(status, '')}）",
                    path="/cgi-bin/freepublish/get",
                    payload=last,
                )
            time.sleep(interval)
        raise WechatAPIError(
            -1,
            f"等待发布结果超时（{int(timeout)}s），publish_id={publish_id}",
            path="/cgi-bin/freepublish/get",
            payload=last,
        )

    def mass_send(
        self,
        media_id: str,
        *,
        is_to_all: bool = True,
        tag_id: int = 0,
        send_time: int | None = None,
        title: str = "",
    ) -> dict[str, Any]:
        """群发图文消息。

        Args:
            media_id: 要群发的图文消息 id（草稿 media_id 或已发布文章的 article_id）。
            is_to_all: 是否群发给全部用户。
            tag_id: 目标标签 id（is_to_all=False 时生效）。
            send_time: 定时群发时间（Unix 秒），为空表示立即群发。
            title: 新版群发接口可携带的标题（部分账号要求）。
        """
        article: dict[str, Any] = {"media_id": media_id}
        if title:
            article["title"] = title
        body: dict[str, Any] = {
            "filter": {"is_to_all": bool(is_to_all), "tag_id": int(tag_id)},
            "mpnews": {"articles": [article]},
            "msg_type": "mpnews",
        }
        if send_time:
            body["send_time"] = int(send_time)
        result = self._call("POST", "/cgi-bin/message/mass/send", json_body=body)
        return result.data

    # -------------------------------------------------------------- 运维辅助
    def callback_ips(self) -> list[str]:
        """查询服务器 IP 白名单。"""
        result = self._call("GET", "/cgi-bin/getcallbackip")
        return list(result.data.get("ip_list", []) or [])

    def clear_quota(self) -> dict[str, Any]:
        """清空调用次数（用于调试）。"""
        result = self._call("POST", "/cgi-bin/clear_quota")
        return result.data

    def material_count(self, media_type: str = "image") -> dict[str, int]:
        """查询素材总量。"""
        result = self._call("GET", "/cgi-bin/material/get_materialcount", params={"type": media_type})
        return {k: int(v) for k, v in result.data.items() if isinstance(v, (int, float))}


def _safe_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """裁剪错误响应，避免把大对象写进日志。"""
    return {k: v for k, v in payload.items() if k not in ("access_token", "secret", "appid")}
