#!/usr/bin/env python3
"""交互式写入微信公众号凭据。

    python3 scripts/set-credentials.py

把 AppID / AppSecret 写进 ~/.config/wechat-publish/credentials.json（权限 600）。
secret 走 getpass 输入，不回显、不落进 shell 历史。

也可以用项目根目录的 .env：
    WECHAT_APPID=...   WECHAT_APPSECRET=...
bin/gzh 会先读 .env，再回落到上面这个 json。
"""

from __future__ import annotations

import getpass
import json
import os
import pathlib
import sys

DEFAULT_PATH = pathlib.Path.home() / ".config" / "wechat-publish" / "credentials.json"


def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    current: dict = {}
    if path.exists():
        try:
            current = json.loads(path.read_text(encoding="utf-8")) or {}
        except Exception:
            current = {}

    appid = (current.get("appid") or "").strip()
    if not appid:
        appid = input("AppID（公众号 设置与开发 → 基本配置）: ").strip()
    else:
        print(f"AppID 已存在：{appid[:6]}…（回车沿用）")
        appid = input("AppID: ").strip() or appid

    secret = getpass.getpass("AppSecret（不回显）: ").strip()
    if not secret:
        secret = (current.get("appsecret") or "").strip()
        if secret:
            print("沿用原有 AppSecret")

    if not appid or not secret:
        print("AppID 与 AppSecret 都不能为空")
        return 1

    path.write_text(
        json.dumps({"appid": appid, "appsecret": secret}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o600)
    print(f"已写入 {path}（权限 600）")
    print("下一步：./bin/gzh check  然后  ./bin/gzh publish --plan frontend-role-202611")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
