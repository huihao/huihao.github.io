---
title: "Octop: One Deployment, a Whole House of AI Colleagues Who Only Remember Their Own Business"
date: 2026-11-16 16:45:00
categories: [thinking]
tags: [AI Agent, Self-hosted, Multi-user, MCP, Open Source, Productivity]
description: "Octop is Tencent's MIT-licensed, self-hosted AI assistant platform. One deployment gives every family member and colleague an expert that only remembers their own business; those experts live inside Feishu, WeChat and DingTalk, take over a real browser, terminal and desktop, and can both recruit coding CLIs over ACP and be called by other agents over MCP. A document-based teardown of the seven designs worth copying, plus how it compares to Claude Code, Codex, Open WebUI and Dify."
translation_key: octop-self-hosted-assistant
lang: en
permalink: /en/2026/11/16/octop-self-hosted-assistant.html
image: /dist/img/cover-octop-self-hosted-assistant.png
---

Most self-hosted AI tools are a chat box with a thin layer of RAG on top: run a model locally, drop in a few PDFs, ask it questions.

[Octop](https://octop.cloud/) (from Tencent, `TencentCloud/Octop`) is trying to solve a different problem: **when a household or a small team owns exactly one machine, how do you give every person their own assistant without their memories, files and permissions bleeding into each other?**

It describes itself as "A smarter, self-hosted AI assistant — multi-user, multi-agent", and the README insists it is "not just a tool — it's a digital life form that can operate in parallel". The homepage is blunter about the point: **one machine runs one service, and family and colleagues each get an assistant that only remembers their own business; switching roles does not mean switching environments.**

That sentence is the key to the whole product. Octop does not compete on whether its agent can write good code. It competes on whether one instance can become a room full of colleagues.

This is a teardown based on Octop's public documentation, README and changelog. First what it is, then the seven designs I think are worth copying, then how it stacks up against comparable tools — where it wins, where it does not.

## 1. What Octop Is

MIT licensed, Python 3.12+, a `FastAPI + uvicorn` backend behind a `React + TypeScript + Vite + Ant Design` frontend, with APScheduler for cron. The homepage claims 12100+ stars.

Five parts make up the whole thing:

| Part | What it does |
| --- | --- |
| **Expert** | Your digital colleague. One expert owns one workspace, with its own files, model, history and memory |
| **Model** | The mind behind an expert. Any OpenAI-compatible / Anthropic / DashScope / Ollama endpoint, poolable with automatic routing |
| **Knowledge base** | PDFs, Word docs, spreadsheets. Answers cite the exact passages they used |
| **Connector** | The apps an expert can operate: Tencent Docs, meetings, Notion, Qichacha… authorize once, then just talk |
| **Channel** | The doors in: WeChat, Feishu, DingTalk, QQ, Telegram, Discord |

The most important architectural detail: **one process runs every entry point.** `octop run` brings up the web panel, the IM channels and the scheduler together, all routed through the same in-process HarnessProcessor, and state is rebuilt from the control-plane database after a restart. The control plane lives in SQLite (WAL) or PostgreSQL; the workspace backend is pluggable and separate.

## 2. The Seven Designs Worth Copying

### 2.1 Many people, one machine, and nobody sees anyone else's business

Octop's multi-user model is not a shared space. It is **separate desks**:

- One instance serves many accounts with JWT isolation; admins can authorize per user group and per page tab — skill packs, knowledge bases, connectors, models, storage and experts can each be opened up individually.
- The expert is the isolation unit: its workspace files, model, chat history and memory are its own.
- An expert can be shared via **Share with other users**: colleagues can talk to the very same running expert, but only the owner can change its settings and files.
- Knowledge bases can be shared read-only. Connector instances can be shared for use while only the owner edits the configuration.

Compared with Open WebUI's multi-user story (closer to one shared space) and Dify's (really "publish apps to different users"), Octop's model matches reality better: teammates can use the expert you wrote, but they cannot edit it.

### 2.2 An Expert Is a Job Description, Not a Chat Window

An expert stands for a **relatively stable kind of work** — weekly reports, research, code review — rather than a throwaway conversation. Its defaults are explicit:

- **Ask**: read-only — read files, search the web;
- **Plan**: write the plan into the workspace;
- **Craft**: operate tools, skills and connectors.

Above that sits personality: 16 MBTI types plus an interactive quiz decide tone and reasoning style. `Discover Experts` ships 22 expert templates with the installer, ready for ops, research and other business workflows. Sub-agents live here too: an expert can `@` another running expert, or open a side thread with `ask_agent`.

One step further is **expert teams** (Beta): a host expert dispatches work to members, every reply lands on the same timeline. The constraints are stated plainly — members must be local plain experts, teams cannot nest, and channels bind to the host only.

The 2026-11-15 release (1.0.3b6) added **hosted experts**: hand the whole conversation to a backend agent such as OpenCode. A product willing to say "this is not my job, I will delegate" is more honest than one that insists on doing everything itself.

### 2.3 It Lives Inside the IM You Already Use

Feishu, WeCom, DingTalk, QQ, WeChat, Telegram, Discord — scan a code and it is bound. The channel's job is deliberately narrow: **carry messages in, carry replies out.**

Once bound, things like "send yesterday's meeting summary to the group at nine every morning" need no interface at all — cron jobs and proactive push deliver to WeChat or Feishu for you. Voice input and output are there too.

This is the real gap between Octop and the web chat box: **Dify and Open WebUI only exist once you open the browser; Octop exists inside your WeChat.**

### 2.4 It Actually Uses Your Computer

This layer is more complete than its peers:

- **Browser workbench**: real Chromium over CDP with a persistent profile (logins survive on disk), one isolated profile per user, reaped after 30 idle minutes (`OCTOP_BROWSER_IDLE_TIMEOUT_MINUTES`). While the agent drives the browser you can **take over the same session at any moment**; your clicks and keystrokes take precedence until you hand control back.
- **Terminal AI+**: full interactive shells in the browser, multiple tabs, and they **share one session with the terminal in the chat dock** — commands and output never disagree between two views.
- **Remote desktop**: watch and drive the host desktop from the browser, with adjustable resolution and frame rate, keyboard shortcuts and full screen. Up to **3 people** connect at once. macOS requires Screen Recording and Accessibility for the process running Octop; on Linux without a graphical session you can install a virtual desktop.
- **Remote phone** (experimental): view and operate a USB-attached Android device or container.

The security centre has six tabs: tool approval, file access, sensitive-information masking, command guardrails (allow/deny), skill scanning and audit log. The four highest-risk tools — `bash`, `execute`, `write_file`, `edit_file` — are on the approval list by default, but the master switch, **Enable manual tool approval, is off by default** (see the caveats later).

### 2.5 Connectors: Your Apps Become the Expert's Hands

The built-in catalog reads like a mix of the Tencent ecosystem and generic SaaS:

- **Office**: Tencent Docs, Tencent Meeting, Tencent Lexiang, Weiyun, Tencent ima, Feishu CLI, WeCom CLI, DingTalk CLI, Agent Mail;
- **Notes and knowledge**: Youdao Note, Notion, Yuque, Obsidian, OpenAlex, WeKnora, RAGFlow;
- **Travel**: Fliggy, Baidu Maps, Meituan, DiDi;
- **Mail and tasks**: personal mailboxes (QQ Mail, NetEase, Gmail, IMAP/SMTP), TickTick;
- **News**: Tencent News, Weixin Reading, QQ Music;
- **Professional**: Qichacha (Yuandian), Dify (through its MCP Server URL).

Authorizing means scanning a code, clicking through an OAuth prompt or pasting a key, then **Probing** to verify, with tokens stored in `~/.octop/secrets/`. After that you do not need tool names — you say "check tomorrow's meetings" and it does the rest.

When the built-ins are not enough, register any MCP server (HTTP or stdio), with OAuth support: Octop can discover the authorization server from a 401 or via RFC 9728, or take a pre-registered client ID/secret. The callback is `<public base>/api/connectors/oauth/callback`. You can also stand up your own plugin, expert and skill marketplace on the intranet — the docs specify the HTTP API for private marketplaces.

### 2.6 A Two-Way Protocol: It Can Recruit Coding CLIs and Be Called by Other Agents

This is the most ambitious piece of Octop's architecture.

**Outbound (ACP):**

- `octop acp` exposes your experts to IDEs and terminals.
- In reverse, its built-in `acp_runner` tool can **delegate** coding subtasks to external CLIs: OpenCode, Claude Code, Codex, Cursor CLI, Kimi Code, CodeBuddy, Pi — seven built-in runners, custom ones allowed. Permission requests surface inline in the conversation; you can answer them yourself, or let the agent reply with `action=respond`.

```text
action=list | start | message | respond | status | close
```

**Outbound (MCP):** `/api/mcp/agents` is a Streamable HTTP endpoint, so any MCP client can call the experts you installed:

| Tool | What it does |
| --- | --- |
| `list_octop_experts` | List the experts visible to the caller |
| `call_octop_expert` | Open an isolated conversation; returns a `thread_id` |
| `resume_octop_expert` | Continue a call parked on an approval or a question |

Tokens are valid for 24 hours by default.

Together, the two directions position Octop as **a routing layer between agents**: it can pull coding CLIs in as subcontractors, and it can expose its own experts outward for other agents to call. Claude Code, Codex and OpenCode occupy none of that position.

### 2.7 Your Data Stays Home, and the Backend Can Change

- Everything lives under `~/.octop/`: database, workspaces, secrets, logs, plugins.
- **The workspace backend is pluggable**: local disk, Docker sandbox, OpenSandbox, PostgreSQL, COS/S3, Volcengine TOS. Sandbox scope can be per expert, per user or fixed. Since 1.0.3b6 admins can restrict which backends users may pick.
- **Memory is portable** and travels with the workspace. `Personalization → Memory` lets you hand-edit the user profile and strong memories; when a new memory contradicts an old one, it **asks you first** instead of silently overwriting, and while compacting memory the chat shows a progress banner and pauses sending.
- **Knowledge bases index locally**: local ONNX (`BAAI/bge-small-zh-v1.5` recommended for Chinese) or online embeddings; scans and images go through OCR (local RapidOCR or an online vision model). 1.0.3b5 added reranking, 1.0.3b6 added knowledge graphs.
- **Multiple instances** can share one PostgreSQL to share cron jobs, channels, plugins and published experts (since 1.0.3b3); 1.0.3b6 filled in the Helm chart.
- The operational details are there too: TOTP and Passkey, LDAP accounts, real backup and restore, and `octop update` swaps the wheel without touching your data.

## 3. How It Compares

A shape comparison first (information as of November 2026, from each project's public docs):

| Project | Positioning | Deployment | Multi-user & permissions | IM channels | Drives a real computer | Protocol role | License |
| --- | --- | --- | :-: | :-: | :-: | --- | --- |
| Claude Code | Coding harness | Terminal / desktop / web | Single user | ❌ | ❌ | Client | Closed source |
| Codex CLI | Coding harness | Local + cloud tasks | Single user | ❌ | ❌ | Client | Apache-2.0 |
| Open WebUI | A home for AI | Self-hosted | Yes, shared space | ❌ | Terminal extension + Computer (ecosystem) | Client | Must retain branding |
| Dify | LLM app platform | Self-hosted / cloud | App-publishing dimension | ❌ | Sandboxed agent | Server API | Apache-2.0 + conditions |
| **Octop** | **Self-hosted AI colleague platform** | **Self-hosted / Helm** | **Multi-user + group auth + shared experts** | **✅ Feishu/WeChat/DingTalk/QQ/TG/Discord** | **✅ Browser / terminal / remote desktop** | **Two-way ACP + Agent MCP** | **MIT** |

Three differences that actually hold up:

**First, it competes on collaboration, not capability.** Everyone else asks "can my agent write code?"; Octop asks "can this instance become a room full of colleagues with divided responsibilities?" Multi-tenant isolation, shared experts and group-level authorization are product design, not something you bolt on with a login page.

**Second, it does both the entry ecosystem and the connector ecosystem.** IM channels (Feishu, WeChat, DingTalk…) and a full connector catalog (Tencent Docs, Notion, Yuque, Qichacha…) live in one product. Others pick a side: a front end (Open WebUI), a workflow engine (Dify), or a terminal harness (Claude Code, Codex).

**Third, on the protocol layer it is aiming for the middle.** One side recruits coding CLIs as subtask runners via ACP; the other exposes its own experts to external agents via Agent MCP. The 1.0.3b6 "hosted expert" pushes further: hand a whole conversation to a backend agent like OpenCode. Almost nobody else is working that line.

Licensing belongs in the comparison too: Dify ships Apache 2.0 with extra conditions under the Dify Open Source License, Open WebUI requires you to keep its branding, and **Octop is plain MIT**. Combined with pluggable storage backends and the ability to run your own marketplace, that gives it more control than its peers.

## 4. The Caveats Worth Stating

**The versioning is still on a beta track.** The changelog is already at `1.0.3b6` (2026-11-15), while the stable release on PyPI is still `1.0.2` (2026-10-18). Sixty-eight releases on PyPI in that window means fast iteration — and means interfaces will change. Leave slack in any automation you build on top.

**Security is loose by default.** The master switch for manual tool approval is off, high-risk tools are listed but the gate is yours to open, and only 1.0.3b6 stopped host directories from being mounted into Docker experts. Before you let a production box run shell commands, tighten the command guardrails and file-access rules yourself.

**Some hard limits.** Three concurrent remote-desktop connections; the browser needs the extra `browser` package and the Docker image ships no Playwright Chromium; some connectors (Feishu CLI, WeCom CLI, DingTalk CLI) need the matching CLI installed on the host.

**Plenty of Beta and experimental labels.** Expert teams, cloud bridging and the knowledge-base page carry BETA; remote phone is experimental. The features are real, but the interfaces and rough edges are still moving.

**There is an ops tax.** A single-machine script install is smooth, but LDAP, multi-instance PostgreSQL and Helm deployment are sysadmin work — and this is a full Python 3.12+ service, not something you tuck into a corner.

**Small naming traps.** The "Extensions" entry in the site navigation currently 404s. And to be clear about the name: the PyPI package `octop` is this project; the npm package of the same name is something else entirely (a GitHub API wrapper).

## 5. Who It Fits, Who It Does Not

**Good fit:**

- People who want "one assistant each" for a household or small team without handing their conversations to someone else's cloud;
- People who live in Feishu, WeChat or DingTalk all day and want the assistant inside that flow;
- People who need it to genuinely operate their machine — browser, terminal, desktop — with auditable actions;
- People willing to own a machine: a home server, a NAS, a Feiniu box, a VPS.

**Poor fit:**

- If all you want is a web chat box;
- If you only write code and need neither multiple users nor IM — Claude Code or Codex is the shorter path;
- If you need enterprise workflow orchestration and LLMOps observability — that is Dify's road;
- If you need a commercial edition, an SLA or vendor support — Octop has none.

## 6. Getting Started

1. **Install**: `curl -fsSL https://download.octop.cloud/octop/scripts/install.sh | bash` (Windows: `install.ps1` / `install.bat`), or `pip install octop`, or Docker Compose, or Helm.
2. **Initialize**: `octop init` creates the database, generates a JWT and makes the first admin; `octop run` runs in the foreground (`127.0.0.1:8088` by default); `octop service start` registers it as a system service.
3. **Shape your expert**: pick a template from `Discover Experts` or build one, choose Ask / Plan / Craft, and bind a model (local Ollama is fine).
4. **Load knowledge**: upload documents, index with local ONNX (`BAAI/bge-small-zh-v1.5` for Chinese), and enable OCR if you need to read scans.
5. **Wire up your apps**: authorize the connectors you actually use; custom MCP servers can carry OAuth; tokens land in `~/.octop/secrets/`.
6. **Open the doors**: bind Feishu, DingTalk, WeCom or QQ under Channels, then add a cron job for a daily push.
7. **Let it act**: install the `browser` extra to unlock the workbench browser; remote desktop needs Screen Recording and Accessibility for the process running Octop.
8. **Back up**: `octop backup`, especially before moving machines.

## Conclusion

Octop's contribution is not a prettier chat box. It is turning **"one assistant serving a whole household"** into a product: one person installs it, a room full of people each claim an expert, each with their own memory, their own files and their own IM accounts — and nobody sees anybody else's business.

Only under that premise do its more engineering-looking pieces make sense: two-way ACP and Agent MCP, OAuth discovery for MCP connectors, pluggable storage backends, local ONNX indexing, a six-tab security centre. They do not answer "can AI do the work"; they answer **"when a room of AI colleagues works together, whose job is it, whose permissions are in play, and who is accountable."**

If you happen to have an idle machine at home or in the team, Octop is worth half an hour of installation. If you just want a comfortable coding assistant, it is probably a detour.
