"""配置加载与校验。

配置为 JSON（标准库即可解析，避免额外依赖），支持在字符串中引用环境变量：

    "app_secret": "${env:WECHAT_APPSECRET}"

环境变量缺失时直接报错，避免把空凭据带到线上才发现。
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .errors import ConfigError

ENV_PATTERN = re.compile(r"\$\{env:([A-Za-z_][A-Za-z0-9_]*)\}|\$\{([A-Za-z_][A-Za-z0-9_]*)\}")

#: 默认发布策略，可被 config/policies.json 覆盖。
DEFAULT_POLICIES: dict[str, Any] = {
    "timezone": "Asia/Shanghai",
    "publish_window": {"start": "07:00", "end": "22:30"},
    "quota": {
        "mass_per_day": 1,
        "publish_per_day": 4,
        "draft_per_day": 50,
    },
    "retry": {"max_attempts": 3, "backoff_seconds": 60},
    "dry_run": False,
    "blackout_dates": [],
    "digest_max_length": 120,
    "author": "",
}

VALID_MODES = ("draft", "publish", "mass")
VALID_SOURCE_TYPES = ("local", "rss", "jsonfeed", "http")


def _expand(value: Any, missing: set[str] | None = None) -> Any:
    """递归展开配置中的环境变量引用。

    缺失的环境变量会被记录到 ``missing`` 集合中，值置为空字符串——
    这样 ``gzh check`` 能在一次运行里报告全部缺失项，而不是遇到第一个就退出。
    """

    def expand_str(text: str) -> str:
        found: list[str] = []

        def repl(match: re.Match[str]) -> str:
            name = match.group(1) or match.group(2)
            if name not in os.environ or os.environ[name] == "":
                found.append(name)
                return ""
            return os.environ[name]

        result = ENV_PATTERN.sub(repl, text)
        if missing is not None and found:
            missing.update(found)
        return result

    if isinstance(value, str):
        return expand_str(value)
    if isinstance(value, dict):
        return {k: _expand(v, missing) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v, missing) for v in value]
    return value


def _read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError as exc:
        raise ConfigError(f"配置文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"配置文件不是合法 JSON: {path} ({exc})") from exc


def resolve_root(explicit: str | os.PathLike[str] | None = None) -> Path:
    """定位项目根目录（含 config/、content/、var/ 的那一层）。"""
    if explicit:
        return Path(explicit).expanduser().resolve()
    env_home = os.environ.get("GZH_HOME")
    if env_home:
        return Path(env_home).expanduser().resolve()

    cwd = Path.cwd().resolve()
    for candidate in [cwd, *cwd.parents]:
        if (candidate / "config").is_dir():
            return candidate
    # 回退到包所在的项目根（src/gzh -> src -> project root）
    return Path(__file__).resolve().parents[2]


@dataclass
class Account:
    """一个公众号账号的配置。"""

    id: str
    name: str = ""
    app_id: str = ""
    app_secret: str = ""
    mode: str = "draft"
    author: str = ""
    content_source_url: str = ""
    cover: str = ""
    quota: dict[str, int] = field(default_factory=dict)
    need_open_comment: int = 0
    only_fans_can_comment: int = 0

    @property
    def label(self) -> str:
        return self.name or self.id


@dataclass
class Plan:
    """一个发布计划（一个内容源 + 一套排期 + 一种发布模式）。"""

    id: str
    account: str
    enabled: bool = True
    at: list[str] = field(default_factory=list)
    cron: str | None = None
    interval_minutes: int | None = None
    source: dict[str, Any] = field(default_factory=dict)
    select: dict[str, Any] = field(default_factory=dict)
    mode: str = "draft"
    window: dict[str, str] = field(default_factory=dict)
    require_approval: bool = False
    dry_run: bool = False
    timezone: str = ""
    catch_up: bool = True
    misfire_grace_minutes: int = 120
    mass_media_id_source: str = "auto"
    mass_send_at: str = ""

    @property
    def source_type(self) -> str:
        return str(self.source.get("type", "local"))

    @property
    def limit(self) -> int:
        return int(self.select.get("limit", 1))

    @property
    def strategy(self) -> str:
        return str(self.select.get("strategy", "oldest"))


@dataclass
class Config:
    """全局配置聚合。"""

    root: Path
    accounts: dict[str, Account] = field(default_factory=dict)
    plans: list[Plan] = field(default_factory=list)
    policies: dict[str, Any] = field(default_factory=dict)
    missing_env: list[str] = field(default_factory=list)

    # ---- 常用目录 ----
    @property
    def config_dir(self) -> Path:
        return self.root / "config"

    @property
    def content_dir(self) -> Path:
        return self.root / "content"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def var_dir(self) -> Path:
        return self.root / "var"

    @property
    def logs_dir(self) -> Path:
        return self.root / "logs"

    @property
    def db_path(self) -> Path:
        return self.var_dir / "state.db"

    @property
    def lock_path(self) -> Path:
        return self.var_dir / "scheduler.lock"

    @property
    def timezone(self) -> str:
        return str(self.policies.get("timezone", "Asia/Shanghai"))

    def plan(self, plan_id: str) -> Plan:
        for plan in self.plans:
            if plan.id == plan_id:
                return plan
        raise ConfigError(f"找不到发布计划: {plan_id}（可用: {', '.join(p.id for p in self.plans) or '无'}）")

    def account(self, account_id: str) -> Account:
        if account_id not in self.accounts:
            raise ConfigError(f"找不到账号: {account_id}")
        return self.accounts[account_id]


def _parse_accounts(raw: dict[str, Any]) -> dict[str, Account]:
    items = raw.get("accounts")
    if not isinstance(items, list) or not items:
        raise ConfigError("config/accounts.json 需要包含非空的 accounts 数组")
    accounts: dict[str, Account] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ConfigError("accounts 数组的每一项必须是对象")
        account_id = str(item.get("id") or "").strip()
        if not account_id:
            raise ConfigError("每个账号必须有唯一 id")
        if account_id in accounts:
            raise ConfigError(f"账号 id 重复: {account_id}")
        mode = str(item.get("mode", "draft"))
        if mode not in VALID_MODES:
            raise ConfigError(f"账号 {account_id} 的 mode 非法: {mode}（可选 {VALID_MODES}）")
        accounts[account_id] = Account(
            id=account_id,
            name=str(item.get("name", "")),
            app_id=str(item.get("app_id", "")),
            app_secret=str(item.get("app_secret", "")),
            mode=mode,
            author=str(item.get("author", "")),
            content_source_url=str(item.get("content_source_url", "")),
            cover=str(item.get("cover", "")),
            quota=dict(item.get("quota", {}) or {}),
            need_open_comment=int(item.get("need_open_comment", 0)),
            only_fans_can_comment=int(item.get("only_fans_can_comment", 0)),
        )
    return accounts


def _parse_plans(raw: dict[str, Any]) -> list[Plan]:
    items = raw.get("plans")
    if not isinstance(items, list):
        raise ConfigError("config/scheduler.json 需要包含 plans 数组")
    plans: list[Plan] = []
    seen: set[str] = set()
    for item in items:
        if not isinstance(item, dict):
            raise ConfigError("plans 数组的每一项必须是对象")
        plan_id = str(item.get("id") or "").strip()
        if not plan_id:
            raise ConfigError("每个发布计划必须有唯一 id")
        if plan_id in seen:
            raise ConfigError(f"发布计划 id 重复: {plan_id}")
        seen.add(plan_id)

        mode = str(item.get("mode", "draft"))
        if mode not in VALID_MODES:
            raise ConfigError(f"计划 {plan_id} 的 mode 非法: {mode}（可选 {VALID_MODES}）")
        source = dict(item.get("source", {}) or {})
        source_type = str(source.get("type", "local"))
        if source_type not in VALID_SOURCE_TYPES:
            raise ConfigError(
                f"计划 {plan_id} 的 source.type 非法: {source_type}（可选 {VALID_SOURCE_TYPES}）"
            )
        if source_type == "local" and not source.get("path"):
            raise ConfigError(f"计划 {plan_id} 使用 local 源时必须提供 source.path")
        if source_type in ("rss", "jsonfeed", "http") and not source.get("url"):
            raise ConfigError(f"计划 {plan_id} 使用 {source_type} 源时必须提供 source.url")

        at_times = item.get("at") or []
        if isinstance(at_times, str):
            at_times = [at_times]
        cron = item.get("cron")
        interval = item.get("interval_minutes")
        if not at_times and not cron and not interval:
            raise ConfigError(
                f"计划 {plan_id} 至少需要 at / cron / interval_minutes 之一作为触发方式"
            )
        if cron:
            from .scheduler import CronSchedule  # 延迟导入避免循环

            CronSchedule.parse(cron)  # 提前校验表达式

        plans.append(
            Plan(
                id=plan_id,
                account=str(item.get("account", "")),
                enabled=bool(item.get("enabled", True)),
                at=[str(t) for t in at_times],
                cron=str(cron) if cron else None,
                interval_minutes=int(interval) if interval else None,
                source=source,
                select=dict(item.get("select", {}) or {}),
                mode=mode,
                window=dict(item.get("window", {}) or {}),
                require_approval=bool(item.get("require_approval", False)),
                dry_run=bool(item.get("dry_run", False)),
                timezone=str(item.get("timezone", "") or ""),
                catch_up=bool(item.get("catch_up", True)),
                misfire_grace_minutes=int(item.get("misfire_grace_minutes", 120)),
                mass_media_id_source=str(item.get("mass_media_id_source", "auto")),
                mass_send_at=str(item.get("mass_send_at", "") or ""),
            )
        )
    return plans


def load_config(root: str | os.PathLike[str] | None = None) -> Config:
    """加载并校验全部配置。"""
    base = resolve_root(root)
    config_dir = base / "config"

    missing: set[str] = set()
    accounts = _parse_accounts(_expand(_read_json(config_dir / "accounts.json"), missing))
    plans = _parse_plans(_expand(_read_json(config_dir / "scheduler.json"), missing))

    policies = dict(DEFAULT_POLICIES)
    policies_path = config_dir / "policies.json"
    if policies_path.exists():
        loaded = _expand(_read_json(policies_path), missing)
        if not isinstance(loaded, dict):
            raise ConfigError("config/policies.json 必须是对象")
        for key, value in loaded.items():
            if isinstance(value, dict) and isinstance(policies.get(key), dict):
                policies[key].update(value)
            else:
                policies[key] = value

    for plan in plans:
        if plan.account and plan.account not in accounts:
            raise ConfigError(f"计划 {plan.id} 引用了不存在的账号: {plan.account}")

    cfg = Config(
        root=base,
        accounts=accounts,
        plans=plans,
        policies=policies,
        missing_env=sorted(missing),
    )
    for directory in (cfg.var_dir, cfg.logs_dir):
        directory.mkdir(parents=True, exist_ok=True)
    return cfg


def dump_json(path: Path, payload: Any) -> None:
    """以 UTF-8 + 缩进写出 JSON（供 init 生成示例配置）。"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
        fh.write("\n")
