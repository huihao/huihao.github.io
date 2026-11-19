# gzh — 微信公众号管理 SOP 自动化套件

把「选题—写作—审校—排版—排期—发布—留痕—复盘」这条链路里**可自动化的部分**做成系统，
把**需要判断的部分**留给人。

系统会从你指定的**内容资源库**（本地 Markdown 目录 / RSS 订阅 / JSON Feed / 网页列表）
按时取稿，自动排版成微信兼容的内联样式 HTML，上传封面与正文图片，创建草稿，
并按计划**发布**或**群发**到公众号；全过程写入 SQLite，任何一步都可追溯、可重试、可回滚。

> 纯 Python 3.10+ 标准库实现，**零第三方依赖**，内网/离线环境可直接部署。

---

## 目录结构

```
gzh/
├── bin/gzh                     # 命令行入口（无需安装即可用）
├── config/
│   ├── accounts.json           # 账号与凭据引用
│   ├── scheduler.json          # 发布计划（排期 / 内容源 / 模式 / 窗口）
│   └── policies.json           # 发布策略（时段 / 配额 / 重试 / 黑名单）
├── content/                    # ★ 内容资源库：Markdown 稿件（带 front matter）
├── assets/                     # 封面等素材
├── src/gzh/
│   ├── cli.py                  # 命令行
│   ├── config.py               # 配置加载与校验
│   ├── publisher.py            # 发布编排
│   ├── scheduler.py            # 排期引擎（at / cron / interval）
│   ├── store.py                # SQLite 持久化
│   ├── wechat/client.py        # 微信开放接口封装
│   ├── sources/                # 内容源：local / rss / jsonfeed / http
│   └── pipeline/               # front matter → Markdown → CSS 内联 → 清洗 → 图片
├── scripts/                    # 备份 / 健康检查 / cron 安装
├── systemd/                    # systemd 单元
├── tests/                      # 55 个单元测试
└── docs/                       # SOP 手册、接口笔记、运维手册、内容规范
```

---

## 快速开始

```bash
cd /opt/gzh

# 1. 生成配置与示例稿件
./bin/gzh init

# 2. 注入凭据（不要把 AppSecret 写进代码仓库）
cp .env.example .env && vi .env
#   WECHAT_APPID=wx...
#   WECHAT_APPSECRET=...

# 3. 体检：配置、目录、凭据连通性、IP 白名单
./bin/gzh check

# 4. 演练：不真实发布，只走一遍排版与摘要
./bin/gzh publish --plan daily-draft --dry-run

# 5. 后台启动调度器
./bin/gzh daemon
```

`./bin/gzh` 会自动加载项目根目录的 `.env`；也可以直接用
`export PYTHONPATH=src && python3 -m gzh.cli ...`，或 `pip install -e .` 后使用 `gzh` 命令。

---

## 微信后台准备清单

自动化跑得通的前提是把公众号后台该开的都开好：

| 事项 | 位置 | 说明 |
| --- | --- | --- |
| IP 白名单 | 设置与开发 → 基本配置 → IP 白名单 | 加入服务器**出口 IP**，否则报 40164 |
| AppID / AppSecret | 设置与开发 → 基本配置 | 写入 `.env`，不要提交到仓库 |
| 发布能力 | 设置与开发 → 公众号设置 → 功能设置 | `publish` / `mass` 模式需要开通 |
| 素材与草稿权限 | 素材管理 / 草稿箱 | 图文封面素材与草稿接口需要该权限 |
| 群发次数 | 订阅号/服务号权益页 | 认证订阅号通常 1 次/天，服务号 4 次/天（以后台为准） |

---

## 三种发布模式

| 模式 | 做什么 | 适用阶段 | 风险 |
| --- | --- | --- | --- |
| `draft` | 只进草稿箱，人工在后台确认后发布 | **上线初期推荐** | 最低，可随时人工干预 |
| `publish` | 走发布能力，文章进入「已发表」 | 稳定期 | 中，不占用群发次数 |
| `mass` | 群发给粉丝，真正触达 | 成熟期 | 高，受每日群发次数限制 |

配置在计划里切换：`"mode": "draft" | "publish" | "mass"`。

---

## 内容资源库

内容放在 `content/`，Markdown + YAML front matter：

```markdown
---
title: "文章标题"
author: 张三
digest: 一句话摘要（留空自动截取正文）
cover: assets/cover-default.png
tags: [AI, 效率]
source_url: https://example.com/original
publish_at: 2026-11-06T08:00
---

正文，支持标题、列表、表格、引用、代码块与图片……
```

- 正文里的**相对路径图片会自动上传到微信**并替换为微信域名链接（避免裂图/防盗链）。
- 封面走永久缩略图素材接口，**必须小于 64KB**（微信硬限制），建议 900×383。
- 字段与规范详见 [docs/content-spec.md](docs/content-spec.md)。

---

## 常用命令

| 命令 | 用途 |
| --- | --- |
| `gzh init` | 初始化项目结构与示例配置 |
| `gzh check` | 环境、配置、凭据、IP 白名单体检 |
| `gzh collect --plan <id>` | 采集内容入池（去重） |
| `gzh list --status queue` | 查看待发布队列 |
| `gzh preview --id <id>` | 预览渲染后的正文 HTML |
| `gzh publish --plan <id> [--dry-run]` | 立即发布 / 演练 |
| `gzh approve --id <id>` | 人工审核放行（配合 `require_approval`） |
| `gzh status` | 排期、配额、内容池、最近执行与事件 |
| `gzh plan` | 排期概览（下次触发时间） |
| `gzh run` / `gzh daemon` | 前台 / 后台运行调度器 |
| `gzh logs --lines 50 [--follow]` | 查看结构化日志 |
| `gzh retry [--id <id>]` | 重试失败文章 |

---

## 排期配置示例

```jsonc
{
  "timezone": "Asia/Shanghai",
  "plans": [
    {
      "id": "daily-draft",
      "account": "main",
      "enabled": true,
      "at": ["08:10", "20:30"],          // 或 "cron": "30 9 * * 1-5"，或 "interval_minutes": 60
      "source": { "type": "local", "path": "content" },
      "select": { "limit": 1, "strategy": "oldest", "require_tags": ["日报"] },
      "mode": "draft",
      "window": { "start": "07:00", "end": "22:30" },   // 窗口外自动顺延
      "require_approval": false,                         // true 则必须人工 gzh approve
      "catch_up": true,                                  // 停机期间错过的触发在宽限期内补跑
      "misfire_grace_minutes": 120
    }
  ]
}
```

四种内容源：

| type | 说明 | 关键字段 |
| --- | --- | --- |
| `local` | 本地 Markdown 目录（递归扫描） | `path` |
| `rss` | RSS / Atom 订阅 | `url`、`limit` |
| `jsonfeed` | JSON Feed / 通用 JSON 列表 | `url`、`limit` |
| `http` | 网页列表页 → 详情页 | `url`、`selector.item/title/link/content` |

---

## 可靠性设计

- **幂等**：文章按内容 SHA-256 去重，重复采集不会重复发布。
- **配额**：按账号 × 模式分别统计当日用量，超限自动跳过而不是硬发。
- **时段**：窗口外触发自动顺延到窗口内；`blackout_dates` 支持节假日静默。
- **失败处理**：失败记录错误码与重试次数，`gzh retry` 可重放；微信侧错误码分类处置（令牌/权限/限流各自不同策略）。
- **令牌**：统一走 `stable_token` 稳定版接口并本地缓存，40001 时强制刷新重试一次。
- **单实例**：文件锁保证同一台机器只有一个调度进程，避免重复发布。
- **全量留痕**：文章池、执行记录、事件流水、素材缓存都落 SQLite，`gzh status` 一览。

---

## 测试

```bash
make test          # 55 个单元测试，纯标准库 unittest
make lint          # 语法检查
```

测试覆盖 front matter 解析、Markdown 渲染、CSS 内联、微信清洗、cron 语义、
时间窗口、存储幂等、内容源解析，以及用假客户端跑通的完整发布链路（草稿/发布/群发/审核门禁/配额/失败重试）。

---

## 文档

| 文档 | 面向谁 | 内容 |
| --- | --- | --- |
| [docs/SOP.md](docs/SOP.md) | 运营 | 完整操作 SOP：角色分工、生产流水线、合规红线、发布策略、应急处置、复盘指标 |
| [docs/runbook.md](docs/runbook.md) | 运维 | 部署、命令速查、监控告警、故障处置手册、备份恢复、变更与升级 |
| [docs/api-notes.md](docs/api-notes.md) | 开发 | 微信接口清单、令牌策略、错误码对照、幂等与限流、正文 HTML 兼容规则 |
| [docs/content-spec.md](docs/content-spec.md) | 编辑 | 内容资源库目录约定、front matter 字段表、图片规范、标签体系 |

---

## 许可

MIT
