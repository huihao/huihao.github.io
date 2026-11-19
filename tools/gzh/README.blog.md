# gzh —— 微信公众号自动发布工具（本仓库内的代码副本）

> 这份副本用于**版本管理**：原始工作副本在 `/root/code/opc/gzh`，那里没有 git 仓库，
> 改动会先落在原处，再同步到这里。二者同源，但**本目录不是运行时**——
> 日常发布仍在 `/root/code/opc/gzh` 执行。

## 副本与原处的差异

同步时刻：2026-11-18。按约定**不含**以下内容：

| 未纳入 | 原因 |
|---|---|
| `docs/` | 内部运维手册（runbook / SOP / api-notes），不适合公开仓库 |
| `content/` | 已转好的稿件与封面素材，属运营内容；原稿在博客仓库的 `drafts/` 里 |
| `var/` | 运行时状态库（`state.db`），含草稿 media_id 等机器状态 |
| `logs/` | 运行日志 |
| `.env` | 凭据，永不入库 |
| `__pycache__/` | 编译缓存 |

纳入的是：`src/`、`bin/`、`config/`、`tests/`、`scripts/`、`assets/`、`systemd/`、
`Makefile`、`pyproject.toml`、`.env.example`、`README.md`。

`config/accounts.json` 里凭据是 `${env:WECHAT_APPID}` / `${env:WECHAT_APPSECRET}`
占位符，真凭据只在本机 `~/.config/wechat-publish/credentials.json`（仓库外）。

## 同步方式

原处改了之后，用 tar 覆盖式同步（排除项同上）：

```bash
cd /root/code/project/huihao.github.io
tar -C /root/code/opc/gzh --exclude='__pycache__' --exclude='*.pyc' \
    -cf - src bin config tests scripts assets systemd \
    Makefile README.md pyproject.toml .gitignore \
  | tar -C tools/gzh -xf -
```

## 跑测试

```bash
cd tools/gzh && python3 -m unittest discover -s tests -q
```

（Python 3.11 标准库即可，无第三方依赖。当前 81 个用例全绿。）

## 本仓库已应用的相关改动（2026-11-18）

- `src/gzh/store.py`：修字段丢失 bug —— `articles` 表没有 `content_source_url` /
  `need_open_comment` / `only_fans_can_comment` / `publish_at` 列，原实现写库只存
  `extra`、读回也不还原，导致「阅读原文」链接与留言开关在入库那一步丢掉。
  现在由 `store.article_extra()` 落库、`_row_to_article()` 还原。
- `tests/test_store_roundtrip.py`：配套回归测试（4 个用例）。
- `src/gzh/pipeline/sanitize.py`、`src/gzh/publisher.py`：合规检查加语境白名单，
  改用 `plain_text()` 扫描正文，避免「第一条」「第一财经」被广告法红线误伤。
- `src/gzh/cli.py`：修连通性体检恒跳过的 bug —— 判据写成了
  `if not account.app_id or account.app_secret:`（有 secret 就成立），
  导致 `gzh check` 永远打印「跳过（凭据未注入）」，从不真正探活。
  改为 `not account.app_secret` 后，check 会真的取 access_token 并列出回调 IP。
- `bin/gzh`：凭据回落 —— 没有项目根 `.env` 时读 `~/.config/wechat-publish/credentials.json`。
- `scripts/set-credentials.py`：getpass 不回显写凭据。
- `scripts/import-blog-post.py`：站内博客 Markdown → gzh 稿件（宽表转竖排卡片、
  加粗收敛、外链清成纯文本）。
