"""统一异常体系。

区分三类问题，便于调度器决定「重试 / 跳过 / 立刻人工介入」：

* :class:`ConfigError`   —— 配置问题，重试无意义，必须人工修配置。
* :class:`WechatAPIError` —— 微信接口返回了错误码，按错误码决定是否重试。
* :class:`SourceError`   —— 内容源不可用，可退避重试。
"""

from __future__ import annotations

from typing import Any


class GzhError(Exception):
    """所有业务异常的基类。"""


class ConfigError(GzhError):
    """配置文件缺失、字段非法或凭据未注入。"""


class SourceError(GzhError):
    """内容源抓取/解析失败，通常是临时故障，可退避重试。"""


class RenderError(GzhError):
    """内容渲染（Markdown→HTML、图片上传）失败。"""


class PublishError(GzhError):
    """发布流程失败（草稿创建、发布提交、结果核验、群发）。"""


class QuotaExceeded(PublishError):
    """触发配额限制（群发次数、发布次数、素材条数等）。"""


class WechatAPIError(GzhError):
    """微信接口返回了错误码。

    Attributes:
        code: 微信返回的 errcode（0 表示无错误，调用方不应构造该异常）。
        message: 微信返回的 errmsg。
        path: 出错的接口路径，便于排查。
        payload: 出错时的请求/响应摘要。
        retryable: 是否值得原样重试（限流类错误为 True）。
    """

    #: 令牌相关错误码：出现即应强制刷新 access_token 后重试一次。
    TOKEN_ERROR_CODES = frozenset({40001, 40014, 41001, 42001})

    #: 限流类错误码：应退避后重试。
    RATE_LIMIT_CODES = frozenset({45009, 45011})

    #: 权限类错误码：重试无意义，需要后台开通能力。
    PERMISSION_ERROR_CODES = frozenset({48001, 48002, 48003, 48004, 48101, 60011})

    def __init__(
        self,
        code: int,
        message: str,
        *,
        path: str | None = None,
        payload: Any = None,
        retryable: bool | None = None,
    ) -> None:
        self.code = int(code)
        self.message = message
        self.path = path
        self.payload = payload
        self.retryable = (
            retryable
            if retryable is not None
            else (self.code in self.RATE_LIMIT_CODES)
        )
        location = f" [{path}]" if path else ""
        super().__init__(f"微信接口错误 {self.code}{location}: {message}")

    @property
    def is_token_error(self) -> bool:
        """是否为令牌失效类错误。"""
        return self.code in self.TOKEN_ERROR_CODES

    @property
    def is_permission_error(self) -> bool:
        """是否为权限不足类错误。"""
        return self.code in self.PERMISSION_ERROR_CODES

    @property
    def is_rate_limit(self) -> bool:
        """是否为调用频率超限。"""
        return self.code in self.RATE_LIMIT_CODES

    def hint(self) -> str:
        """返回面向运维的可执行处置建议。"""
        if self.code in (40013,):
            return "AppID 不正确，请核对 config/accounts.json 与公众平台后台。"
        if self.code in (40125,):
            return "AppSecret 不正确或已被重置，请重新获取并注入环境变量。"
        if self.code == 40164:
            return "调用出口 IP 不在白名单，请把服务器出口 IP 加入「基本配置→IP 白名单」。"
        if self.code in self.TOKEN_ERROR_CODES:
            return "access_token 失效，系统会自动强制刷新；若持续出现请检查是否有多个应用共用同一主体。"
        if self.is_permission_error:
            return "当前账号缺少该接口权限，请在公众平台后台开通对应能力（如发布能力/群发权限）。"
        if self.is_rate_limit:
            return "接口调用频率超限，系统已退避重试；持续超限请降低发布频率或联系微信提升配额。"
        return "查看 docs/api-notes.md 错误码对照表，或在公众平台后台核对账号状态。"
