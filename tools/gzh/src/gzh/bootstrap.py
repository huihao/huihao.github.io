"""项目初始化：生成示例配置、内容资源库骨架与默认封面。

``gzh init`` 会创建（已存在则跳过）：

* ``config/accounts.json``  —— 账号与凭据引用
* ``config/scheduler.json`` —— 发布计划
* ``config/policies.json``  —— 发布策略
* ``content/``、``assets/``、``var/``、``logs/`` 目录
* ``assets/cover-default.png`` —— 默认封面
* ``content/README.md``、``content/sample/001-hello.md`` —— 示例稿件
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import dump_json
from .pipeline.render import make_placeholder_png

ACCOUNTS_TEMPLATE: dict[str, Any] = {
    "accounts": [
        {
            "id": "main",
            "name": "主号",
            "app_id": "${env:WECHAT_APPID}",
            "app_secret": "${env:WECHAT_APPSECRET}",
            "mode": "draft",
            "author": "运营团队",
            "content_source_url": "",
            "cover": "assets/cover-default.png",
            "quota": {
                "mass_per_day": 1,
                "publish_per_day": 4,
                "draft_per_day": 50,
            },
            "need_open_comment": 0,
            "only_fans_can_comment": 0,
        }
    ]
}

SCHEDULER_TEMPLATE: dict[str, Any] = {
    "timezone": "Asia/Shanghai",
    "plans": [
        {
            "id": "daily-draft",
            "account": "main",
            "enabled": True,
            "at": ["08:10", "20:30"],
            "source": {"type": "local", "path": "content/sample"},
            "select": {
                "limit": 1,
                "strategy": "oldest",
                "require_tags": [],
                "exclude_tags": [],
            },
            "mode": "draft",
            "window": {"start": "07:00", "end": "22:30"},
            "require_approval": False,
            "dry_run": False,
            "catch_up": True,
            "misfire_grace_minutes": 120,
        },
        {
            "id": "rss-digest",
            "account": "main",
            "enabled": False,
            "cron": "30 9 * * 1-5",
            "source": {
                "type": "rss",
                "url": "https://example.com/feed.xml",
                "limit": 5,
            },
            "select": {"limit": 1, "strategy": "newest"},
            "mode": "draft",
            "window": {"start": "08:00", "end": "20:00"},
            "require_approval": True,
        },
    ],
}

POLICIES_TEMPLATE: dict[str, Any] = {
    "timezone": "Asia/Shanghai",
    "publish_window": {"start": "07:00", "end": "22:30"},
    "quota": {"mass_per_day": 1, "publish_per_day": 4, "draft_per_day": 50},
    "retry": {"max_attempts": 3, "backoff_seconds": 60},
    "digest_max_length": 120,
    "upload_remote_images": True,
    "allow_missing_cover": False,
    "blackout_dates": [],
    "forbidden_keywords": ["最强", "第一", "国家级", "永久", "包治", "稳赚"],
    # 语境白名单：关键词的每一次出现都落在这些语境里就放行。
    # 广告法要拦的是「行业第一」这种最高级表述，不是「第一条」「第一次」这种行文。
    "forbidden_keyword_safe_contexts": {
        "第一": [
            r"\s*(?:条|件|次|级|位|人|轮|批|手|财|时|间|行|版|天|场|步|站|篇|道|类|种|份|张|的|点|代|届|波|款|项|则|要|梯|圈|个|句|反|直)",
        ],
    },
}

CONTENT_README = """# 内容资源库

把要发布的稿件放在这里，系统会按 `config/scheduler.json` 里的计划自动取用。

## 目录约定

```
content/
└── 2026-11/            # 按月份分目录（可选，递归扫描）
    ├── 001-标题.md
    └── 002-标题.md
```

## 稿件格式

Markdown 文件 + YAML front matter：

```markdown
---
title: "文章标题"
author: 张三
digest: 一句话摘要（留空会自动截取正文）
cover: assets/cover-default.png
tags: [AI, 效率]
source_url: https://example.com/original
publish_at: 2026-11-06T08:00
need_open_comment: 0
only_fans_can_comment: 0
---

正文从这里开始，支持标题、列表、表格、引用、代码块与图片。
```

## 图片

- 正文里的相对路径图片会自动上传到微信并替换为微信域名链接。
- 单图建议小于 1MB；封面图必须小于 64KB（微信硬限制）。
- 封面可以用 `cover` 指定；不指定则使用账号配置的默认封面。
"""

SAMPLE_ARTICLE = """---
title: "示例文章：公众号自动发布是怎么做的"
author: 运营团队
digest: 这是一篇示例稿件，用来验证内容采集、排版与发布链路是否正常。
cover: assets/cover-default.png
tags: [示例, 自动化]
source_url: https://example.com/sample
---

## 为什么需要自动化发布

公众号运营里最耗时间的往往不是写作，而是**排期、排版、发布、留痕**这四件重复劳动。

自动化之后，人只做真正需要判断的事：选题、写作、审校、合规把关与复盘。

## 本次发布要做什么

1. 从本地内容资源库采集这篇稿件；
2. 渲染成微信兼容的内联样式 HTML；
3. 上传正文图片与封面素材；
4. 创建草稿（`draft/add`），按计划模式继续发布或群发；
5. 把每一步写进 SQLite，任何人可以在 `gzh status` 里查到。

> 发布前请务必完成人工审校：自动化只解决执行，不替代判断。

```python
# 伪代码：完整的发布链路
article = source.fetch()
html = render(article)
media_id = wechat.draft_add(html)
publish_id = wechat.submit(media_id)
wechat.wait(publish_id)
```

| 步骤 | 负责人 | 耗时基准 |
| --- | --- | --- |
| 选题 | 编辑 | 30 分钟 |
| 写作 | 作者 | 2 小时 |
| 审校 | 审核 | 30 分钟 |
| 发布 | 系统 | 秒级 |
"""

DEFAULT_COVER_NOTE = "assets/cover-default.png 由 `gzh init` 自动生成的占位封面，请替换为真实封面素材。"


def init_project(root: Path, *, force: bool = False) -> list[str]:
    """初始化项目结构，返回实际创建/更新的文件列表。"""
    created: list[str] = []
    config_dir = root / "config"
    content_dir = root / "content"
    assets_dir = root / "assets"
    for directory in (config_dir, content_dir, assets_dir, root / "var", root / "logs"):
        directory.mkdir(parents=True, exist_ok=True)

    def write_json(path: Path, payload: dict[str, Any]) -> None:
        if path.exists() and not force:
            return
        dump_json(path, payload)
        created.append(str(path.relative_to(root)))

    write_json(config_dir / "accounts.json", ACCOUNTS_TEMPLATE)
    write_json(config_dir / "scheduler.json", SCHEDULER_TEMPLATE)
    write_json(config_dir / "policies.json", POLICIES_TEMPLATE)

    readme = content_dir / "README.md"
    if not readme.exists():
        readme.write_text(CONTENT_README, encoding="utf-8")
        created.append(str(readme.relative_to(root)))

    sample_dir = content_dir / "sample"
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample = sample_dir / "001-hello.md"
    if not sample.exists():
        sample.write_text(SAMPLE_ARTICLE, encoding="utf-8")
        created.append(str(sample.relative_to(root)))

    cover = assets_dir / "cover-default.png"
    if not cover.exists():
        cover.write_bytes(make_placeholder_png())
        created.append(str(cover.relative_to(root)))

    env_example = root / ".env.example"
    if not env_example.exists():
        env_example.write_text(
            "# 复制为 .env 并填入真实凭据（.env 不要提交到代码仓库）\n"
            "WECHAT_APPID=wx0000000000000000\n"
            "WECHAT_APPSECRET=00000000000000000000000000000000\n"
            "# 可选：项目根目录（默认自动向上查找 config/ 目录）\n"
            "# GZH_HOME=/opt/gzh\n",
            encoding="utf-8",
        )
        created.append(str(env_example.relative_to(root)))

    gitignore = root / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(
            ".env\nvar/\nlogs/\n__pycache__/\n*.pyc\n", encoding="utf-8"
        )
        created.append(str(gitignore.relative_to(root)))
    return created
