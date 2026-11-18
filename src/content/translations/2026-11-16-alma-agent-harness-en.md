---
title: "Alma: the agent harness that makes \"who needs you\" a first-class citizen"
date: 2026-11-16 16:30:00
categories: [thinking]
tags: [AI agent, harness, local-first, desktop app, open source, productivity]
description: "Alma is yetone's desktop-and-mobile agent harness, and simultaneously the graphical client for the open-source herdr project. What matters most about it is not one more chat window but three things: \"who needs you\" becomes a pushable state stream, tool selection is delegated to a separate lightweight model, and browser actions come back as auditable receipts. This article unpacks those designs and weighs them against Claude Code, Codex, Cursor, OpenCode and Goose — where Alma is genuinely stronger, and where it is not."
translation_key: alma-agent-harness
lang: en
ai_written: true
permalink: /en/2026/11/16/alma-agent-harness.html
image: /dist/img/cover-alma-agent-harness.png
---

Over the past two years I have taken apart a fair number of agent tools. They all share one trait: they turn the agent into a **smarter terminal**. You type a sentence; it calls tools, reads files, writes code.

But one problem has never been solved: **the agent is running, and the human is sitting there waiting.** Three tasks means three terminal windows; ten tasks means ten streams of messages. The human becomes the bottleneck — and the dumbest kind of bottleneck, since most of the time is spent waiting and every so often you have to switch to some window and type "yes, continue".

[Alma](https://alma.now/) (by yetone / Hao Chen) aims at exactly that layer. It is a desktop-and-mobile agent harness that is also the graphical client for the open-source [herdr](https://herdr.dev/) project. That dual identity is not a gimmick; it is the key to reading the whole thing.

This write-up is based on the public documentation of Alma and herdr. First what it is, then the six designs I think are worth stealing, then where it beats or loses to other harnesses.

## 1. First, what Alma actually is

It has two identities.

**One: a complete harness in its own right.** 20+ built-in tools, MCP, skills, semantic memory, artifacts, a built-in browser plus Chrome Relay, a local database, multiple models (OpenAI / Anthropic / Gemini / DeepSeek / OpenRouter / anything API-compatible), and the ability to switch models mid-thread.

**Two: the graphical client for herdr.** It reads the Claude Code / Codex / pi panels running inside herdr as conversations — tool calls, sub-agents and file edits laid out in order, with the real terminal always one click away.

One counter-intuitive fact: **Alma itself is not open source.** The main application has no public repository; what is public is the release repo `yetone/alma-releases` and the MIT-licensed plugin API package `alma-plugin-api` (latest on npm: 0.1.2). The open half is herdr — Apache 2.0, across three repos: `herdrdev/herdr`, `herdrdev/herdr-app` and `herdrdev/herdr-core`.

Keep that in mind: the line between Alma and herdr falls exactly between "general-purpose harness" and "specialised client".

## 2. The six features I find most useful

### 1. "Who needs you" becomes a state, not a window

Alma's agent view groups the sidebar by status: **Needs input / Working / Done**.

That may be the single most important line in this article. The difference from "yet another terminal window" is fundamental:

- In the terminal model, status is buried in a title bar or a progress spinner, or you have to switch back and scan it yourself.
- In Alma, status is **first-class and pushable**. When an agent stalls and needs a decision, a desktop notification arrives; the iPhone build receives the push and lets you answer from there.

On the herdr side there is also the **OSC 7501** open status protocol: any program can report its own status with `printf '\e]7501;state=blocked:app=my-agent\e\'`. It is not a private API but a public convention inside a terminal — your scripts, your CI, your hand-rolled little agent can all land in the same inbox.

And there is one easily missed detail: agents in herdr run inside the resident **herdr-core** service. Close the window, upgrade the client, even let the client crash, and the agent keeps running. It is still alive when you come back.

### 2. Tool calls get their own model

Alma takes four jobs out of the main model and hands them to a separate lightweight model: **choosing tools, extracting parameters, reading and writing memory, and naming threads automatically**.

The payoff shows up directly in the bill and in latency:

- the main model only thinks and answers;
- the tool model is a cheap fast model (official recommendations: gpt-4o-mini / claude-haiku-4-5 / gemini-2.0-flash), and the docs require a response **under 2.5s** and explicitly warn **not** to use a reasoning model (o1 / o3 / extended thinking) here — that would make every tool selection slower and dearer.

Most harnesses today let one big model do everything, so every tool call costs a round trip through the expensive model. Alma effectively applies a discount to the scheduling layer of the harness. It lives in Settings → General → Tool Model, and is auto-detected by default.

### 3. Memory you can actually see

Alma's memory follows **extract → embed semantically → retrieve before every answer**, and every single entry is laid out in front of you: edit the content, set an importance (0–1, higher wins retrieval), tag it, choose a durability (Permanent is never pruned automatically, Temporary may be pruned during maintenance), see where it came from (Chat / Manual / Auto), delete it, or clear everything at once.

Defaults: Max Retrieved = 10, similarity threshold 0.7, query rewriting on. The embedding model defaults to `text-embedding-3-small`, and you can switch to 3-large, Google, or any OpenAI-compatible endpoint — or rebuild the embeddings.

Compare the common alternatives:

| Approach | What memory looks like | Who maintains it |
| --- | --- | --- |
| `CLAUDE.md` / `AGENTS.md` | a file you write by hand | you |
| session memory in most harnesses | a chunk auto-injected into context | a black box |
| Alma | auto-extracted + semantically retrieved, every entry a **visible, editable, deletable** row | you, with an audit trail |

That is not "smarter memory" — it is **memory as public infrastructure**. There is also Incognito Mode, where a thread neither creates nor retrieves memory.

To be fair, Alma's memory also lands in files, and Claude Code has file-backed auto memory too — both are visible. The real difference is not whether it can be stored but **how it gets found**: Alma does semantic retrieval over embeddings, with the similarity threshold, importance and durability as tunable parameters, whereas file-based memory only applies if you happened to write it down.

### 4. Chrome Relay: browser actions come back with receipts

This is where I think Alma's engineering is strongest. It does not "spin up a remote browser and show you a stream"; it **takes over the Chrome you are already using** (through a CDP extension), inheriting your logged-in sessions. The chain is:

```text
AI Chat → ChromeRelay tools → Alma Server → WebSocket → Chrome Extension → chrome.debugger → Your Tab
```

The part I would actually steal is the **receipt semantics**.

ReadDom does not return a DOM dump; it returns a **map of interactive elements**:

```text
e11 link "Pull requests" <a#pr-nav> href=/pulls sel=#pr-nav
```

A ref like `e11` can be used directly as a selector, and occluded elements are labelled explicitly: `[hidden: covered at its click point by <div.modal-overlay>]`.

And Click returns structured data:

```json
{
  "success": true,
  "matchCount": 1,
  "matchedIndex": 0,
  "element": { "tag": "a", "id": "pr-nav", "text": "Pull requests", "href": "/pulls" },
  "navigated": { "from": "...", "to": "..." },
  "openedTabs": []
}
```

`matchCount` tells you the selector was too loose (hitting several elements means ambiguity). Type distinguishes "does not exist / not typeable / disabled / readonly / write did not take effect" instead of a generic error. Eval awaits promises and hands back the real value with its JS type.

The heaviest rule is this: **if a human could not click it, the agent may not click it.** `display:none`, `visibility:hidden`, `opacity:0`, `transform:scale(0)`, zero-size elements, click points covered by an overlay, `left:-9999px` screen-reader tricks — all rejected; forcing it requires an explicit `allowHidden: true`. Merely being scrolled out of the viewport does not count (it scrolls first).

The classic browser-agent failure mode is "clicked something invisible, then reported success". Alma defines a successful click as an auditable fact: which element was hit, how many matched, whether navigation happened, which tabs opened.

The other ten tools: ListTabs / Navigate / Click / Type / Screenshot / Read (Readability to Markdown) / ReadDom / Eval / Scroll / Back / Forward. The local WebSocket defaults to port 23001 with an auth token, and one-click launch requires quitting Chrome completely (it needs `--load-extension`).

### 5. Artifacts: the answer is something you can run

HTML (in an isolated iframe sandbox), React (JSX compilation, hooks, Tailwind built in), Mermaid, SVG and syntax-highlighted code all open in an interactive preview pane next to the conversation: refresh, fullscreen, download, view source, drag to resize. React and HTML projects can even spin up a dev server (Bun + Vite) with status, logs and hot reload.

That kills an old LLM-UI problem: the model hands you some HTML, you copy it into a file, open it in a browser, edit it, paste it back. Artifacts compresses that round trip into "it's right there".

### 6. Local-first, with an end-to-end encrypted relay

Conversations live in a database on your own machine, and API keys talk straight to the providers — nothing goes through Alma's cloud. Pairing the phone through the Alma relay is end-to-end encrypted, or you can connect directly over the same Wi-Fi; on iPhone you can also watch and operate the Mac screen (Remote Screen, requiring Screen Recording plus Accessibility permissions, Mac only).

Two smaller Alma-specific designs deserve a mention:

- **MCP output safety modes**: an MCP tool can declare `exact` (keep verbatim), `compact` (large text may be compressed) or `passthrough` (skip compression, for binary payloads) in `_meta["alma/outputSafetyMode"]`, with `[alma-output-safety: exact]` in the description as a fallback. Source code, IDs and structured data must be `exact`; logs and search results may be `compact`. This solves a real and widely ignored problem in the MCP ecosystem.
- **Prompt Apps**: turn a recurring prompt into a form (Text / Select / Checkbox / Date / File…), pin the model, tool set, reasoning level and incognito flag, bind a shortcut, export as JSON to share.

## 3. Against the other harnesses

A shape comparison first (information as of November 2026, based on each project's public documentation):

| Tool | Form | Multiple models | Memory | MCP | Drives your real browser | Reachable from a phone | Can it take over *other* agents? | Open source |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| Claude Code | terminal + desktop + web | own models only (a base URL override can swap them) | `CLAUDE.md` + file-backed auto memory | ✅ | ❌ | indirectly via cloud tasks | ❌ | ❌ |
| Codex CLI | terminal + cloud tasks | ❌ | `AGENTS.md` | ✅ | ❌ | indirectly via cloud tasks | ❌ | ✅ Apache-2.0 |
| Cursor / Cline / Roo | inside the IDE | ✅ | rules files | ✅ | partial | ❌ | ❌ | Cline / Roo ✅ |
| OpenCode | terminal + desktop + web | ✅ | session files + instructions | ✅ | ❌ | `opencode pair` link (no push) | ❌ | ✅ |
| Goose | desktop + CLI | ✅ | built in | ✅ (native extensions) | limited | ❌ | ❌ | ✅ Apache-2.0 |
| Alma | desktop + mobile | ✅ | semantic retrieval, per-entry visible | ✅ | ✅ with receipts | ✅ (push + remote screen) | ✅ | plugin API only |

(Built from each project's public docs and repositories: [Claude Code](https://code.claude.com/docs/en/overview), [Codex CLI](https://github.com/openai/codex), [OpenCode](https://opencode.ai/docs/), [Goose](https://goose-docs.ai/docs/getting-started/installation). As of November 2026.)

One thing has to be cleared up first: **"it has a GUI" is no longer a difference on its own.** As of November 2026 Claude Code ships a desktop app and a web app, Codex has cloud tasks, OpenCode comes as terminal, desktop and web (`opencode pair` prints a one-time link so you can open its web UI from another device), and Goose has both a desktop app and a CLI. Everybody shipped a screen; Alma does not get credit for one.

Only three differences are really worth arguing about.

**First, Alma competes on attention scheduling, not model capability.** Everyone else is comparing "who writes better code"; Alma is comparing "how do you know which agent needs you right now". Once you run ten agents instead of one, waiting becomes the job. Almost nobody is working on that layer — OpenCode's pair link lets you drive one agent from your phone, but that is remote control of a single agent, not an inbox of agents waiting for your reply.

**Second, Alma is the one that pulls *other people's* agent processes into a single UI.** IDE plugins add an agent to your editor; Alma adds a UI *around all agents*. Claude Code, Codex and pi transcripts are read directly, and you do not have to reconfigure any of them — Alma finds the socket on its own (`HERDR_SOCKET_PATH` → `<config>/herdr/sessions/<name>/herdr.sock` → `<config>/herdr/herdr.sock`) and also reads your login shell environment.

**Third, local-first with your own keys is already a scarce property in 2026.** Conversations, settings and memory stay on the machine; Alma is only the UI layer. Combined with iOS push notifications answering "who needs you", Alma is one of very few agent harnesses that let you leave the desk without losing control.

One more note on herdr itself, which is more radical than Alma: inside herdr, agents can spawn agents (`hc run --bg codex "review my diff. Done: hc send t1"`), and a finished sub-agent reports back into the main agent (`<hc from="t3 reviewer">`). One agent reviewing another's output is where an agent stops being a tool caller and starts being a colleague.

This is where "which half is open" starts to pay off: **Alma is just one of herdr's clients.** herdr-core is open source, so you can compile your own and let Alma connect to read its panels; tomorrow someone can write a different client — a pure TUI, a little daemon that only sends you notifications — and it talks to the same socket. Read the other way: if Alma ever stops shipping, your agent infrastructure is still intact inside herdr.

And Alma's "body" is precisely the general-purpose harness: it works standalone without herdr. That is the confidence behind putting two identities into one product — **one is a replaceable frontend, the other is a workbench that stands on its own.**

## 4. The weaknesses, stated plainly

**The client is closed source.** Changing core behaviour means plugins (TypeScript, MIT), and the ecosystem is still tiny: `alma-plugin-api` is at 0.1.2 with 89 downloads in the last 30 days, and the registry `yetone/alma-plugins` has barely started. The whole herdr stack is Apache 2.0 and can be compiled yourself; Alma you have to wait for.

**The docs lag the features.** The reasoning page still lists o1-preview, o1-mini and Claude 3.5 Sonnet; the installation guide still says Linux is "coming soon" while the download page already ships AppImage / deb / rpm. Trusting the docs alone will trip you up.

**herdr's limits are real.** Agents running inside tmux cannot report status; after a machine restart or a service crash, agents are not restored (only the panel shell is); the TUI and the new app are separate programs that do not share agents.

**Chrome Relay has prerequisites.** It needs an extension, one-click launch requires quitting Chrome, and fresh tabs are not attached to the debugger by default — Chrome wants per-tab authorization. That is Chrome's security model rather than an Alma bug, but automated flows that cross tab boundaries do get stuck there.

**Understand the dependency.** Alma's herdr view requires herdr-core running locally. Without herdr, Alma is an ordinary desktop harness — and the author's own line, "it is strong on its own even without herdr", is accurate rather than promotional.

## 5. Who it fits, who it does not

**Good fit if you:**

- run several coding agents at once and want one inbox for them;
- want to receive "I need your confirmation" on your phone and reply there;
- want to build a local-first desktop workbench with MCP, skills and auditable memory;
- want an agent working in your **real Chrome** — with your logins — while every step stays auditable.

**Poor fit if you:**

- live in the terminal and dislike GUIs — the herdr TUI suits you better;
- require auditable, self-hostable source for the whole stack — OpenCode or Goose suit you better;
- live in diff review inside an IDE — Cursor or Cline are more natural;
- just want to chat — a browser tab beats it.

## 6. Getting started

1. Install the desktop app: macOS dmg / Windows x64.exe / Linux AppImage·deb·rpm, or `alma --install`;
2. Install herdr: `curl -fsSL https://releases.herdr.dev/app/install.sh | sh`, then run Claude Code / Codex inside its panels;
3. Switch Alma's sidebar to the agents view (⌘⇧A on macOS) — it finds the local herdr service automatically, without changing how you use herdr;
4. Install the iOS build from TestFlight, scan to pair, and start receiving pushes;
5. Chrome Relay: install the extension → enter the auth token → authorize the tabs you want driven.

**One disambiguation**: the `@alma-harness/*` packages on npm (loop / memory / runtime / conversation / batch / execution / single-call, 0.41.0, Apache-2.0, from the repo `FabioFernandesCarneiro/alma`) have nothing to do with yetone's Alma. Different author, same name — do not mix them up.

## Closing thoughts

Alma's real contribution is not one more chat window. It is a **human–agent interface** for the era of parallel agents: who is running, who is stuck, who is waiting for you, all visible on one screen and answerable from your phone.

Given that, the rest of the features — the separate tool model, visible memory, browser actions with receipts, artifacts — start to hold up: they are not about what the agent *can* do, but about whether the bill adds up, whether the actions can be traced, and whether the interface survives the load.

If you already have three or four terminal windows open running your own agent orchestration, Alma is worth twenty minutes of your afternoon. If you would rather just write code in silence, both the TUI alternative and the old way of doing things are still there.
