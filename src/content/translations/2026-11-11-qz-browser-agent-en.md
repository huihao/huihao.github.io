---
title: "Qingzhou qz — an open-source agent that lives in your own browser: forms, page reading, UI regression"
date: 2026-11-11 07:00:00
categories: [thinking]
tags: [browser automation, AI agent, open source, productivity, testing]
description: "qz (Qingzhou) is Alibaba's open-source, local-first browser agent: a Chrome extension that runs inside the browser you already use, with a model-agnostic skill system plus a CLI and MCP bridge. This article unpacks its central idea and architecture, then lands on three concrete scenarios — filling out complex forms, extracting key information from pages, and running UI tests that leave screenshots and an operation log behind."
translation_key: qz-browser-agent
lang: en
permalink: /en/2026/11/11/qz-browser-agent.html
image: /dist/img/cover-qz-browser-agent.png
---

For the past two years "browser agent" has been an overused phrase: record a video, move a cursor, let a model guess what to click next. The demos look great and then fail the same way in real work — **login walls, infinite scrolling, deeply nested forms, and the maddening case where the script clicks the right thing but the page state is wrong**.

Alibaba's open-source project [qz (Qingzhou)](https://github.com/alibaba/qz-browser-agent) takes a different route: **instead of a cloud browser, it puts the agent inside the Chrome you are already using**. It inherits your logged-in session, your cookies and your extensions; it takes the whole task rather than a single click; and — the most interesting part — **it turns a flow that worked once into a reusable Skill**.

This article first unpacks the central idea and the architecture, then lands on three concrete scenarios: filling out complex forms, extracting key information from a page, and running a UI test end to end while keeping screenshots and a record of every operation.

## 1. The central idea: hand over the task, not the clicks

The README puts qz in a comparison table next to Nanobrowser, Browser Use, agent-browser and Playwright MCP (based on each project's public docs, as of October 2026). qz takes all five ✅ in this list:

| Capability | qz | Nanobrowser | Browser Use | agent-browser | Playwright MCP |
| --- | :-: | :-: | :-: | :-: | :-: |
| Delegate the whole task, not every click | ✅ | ◐ | ◐ | ◐ | ❌ |
| Runs in your own logged-in Chrome | ✅ | ✅ | ◐ | ◐ | ◐ |
| Real-time control of every step, for humans and agents | ✅ | ◐ | ◐ | ◐ | ◐ |
| Many tasks in parallel, each with subtasks | ✅ | ◐ | ◐ | ◐ | ◐ |
| Save a run as a reusable Skill | ✅ | ❌ | ◐ | ❌ | ❌ |

That table is really the whole design brief:

- **Delegate the task.** You describe "fill in the performance-review form and submit it", not "open the menu, find the checkbox, tick each one". The first is a task, the second is a script. The first is planned by the model, the second is maintained by a human. Inside qz the model gets a whole tool catalog (open a tab, read the article, find elements, screenshot, run a script, write a data table…) and plans the final actions itself.
- **Run in a real browser.** Your login state, your enterprise SSO, the userscripts you installed, the pages that only show up under a real UA — all of it works, because it *is* your Chrome, not a rented cloud host.
- **Humans and agents share the same door.** Every step is visible in the qz side panel: which step it reached, which tool it called, what came back. If the task drifts you can interrupt it, add a corrective sentence, or stop it outright. This is an agent as copilot, not an agent locked in a room clicking on its own.
- **Save what worked as a Skill.** To me this is the most valuable idea of the set: today you get a gnarly business flow through once; tomorrow one sentence — "run last quarter's flow again" — loads the matching Skill and keeps going. Skills live locally, or install straight from a Git repository so the whole team can use them.

Add **Local First** on top: sessions, Skills and collected data live inside your browser. qz runs no server of its own, so your data only travels to the model service you configured and to the sites you work on. The model is yours to choose too — OpenAI Codex, DeepSeek, Kimi For Coding, OpenRouter, Fireworks, or any local server that speaks tool calling.

## 2. Architecture: five contexts, one main line

qz is a Manifest V3 Chrome extension, but its architecture is not "one giant service worker". The official `docs/architecture.md` draws a runtime map, and that map is basically the key to understanding qz:

```text
Side Panel / Chrome message / MCP
                 |
           Background API
                 |
       Session commands and supervisor
          /                    \
   Repositories              Agent
                        /             \
                 Model gateway     Tool runtime
                                       |
                           Content / Chrome / services
```

Layer by layer:

**1. Background** (`src/background/service-worker.ts`) is the brain. It owns task state and persistence: a Session holds a conversation, a record and a queue. Every external request passes through the `Background API` and into the Session command queue — one Session runs one thing at a time, duplicate `clientMessageId`s are deduplicated, and a retry reuses an already accepted message.

**2. The Agent Host** assembles a run: repositories (history, checkpoints, documents), model and tool services, and a **write lease**. The lease matters: at any moment only one execution flow may write the session record, so two concurrent calls can never garble the conversation. Stop, cancel and timeout all travel via `AbortSignal`, and the lease is re-checked after every asynchronous step.

**3. The Model Gateway** flattens the differences between providers: message format, tool calls, streaming, errors, usage accounting. The Agent owns semantic recovery and retry budgets.

**4. The Tool Runtime** executes the catalog: argument validation, permissions, security guardrails, rate limits — then the actual work. A model response may contain several tool calls; the runtime allows up to ten in-flight calls concurrently. Actions on the same tab serialize; different tabs advance in parallel.

**5. The Side Panel** (`src/sidepanel/`) only presents. Agent events are projected into UI state, so what you see is a readable timeline rather than a raw event stream.

**6. The Content Script** (`src/content/content-script.ts`) reads the DOM, clicks and fills inside an isolated world. Elements are handed back as `uid:` handles (for example `uid:t3.s7.12`), so a reference still points at the same node even if the page structure shifts.

**7. Offscreen plus a sandboxed Worker** (`src/offscreen.ts`, `src/runner-sandbox.ts`) take on DOM-heavy work and keep script execution inside an isolated worker.

**8. The MCP Bridge** (`services/mcp-bridge/`) is a local service that exposes the extension to external clients over MCP.

One more piece is easy to miss but central: the **capability system**. `src/capabilities/` holds 577 files, and each subdirectory (tabs, skills, sessions, documents, accessibility, media, mcp, providers…) is an independent capability package that registers its contributions through generated catalogs. Adding a tool, a view or a model provider is supposed to mean adding a capability package, not touching the core. It is also why the same codebase can target Chrome, Edge and the Firefox build that is still in progress.

## 3. Three ways in: from chatting to scripting

qz exposes three layers, and you can pick how deep to go.

### 1. Side panel: hand over the task like a chat message

Install the extension, connect a model, open the side panel and just say it:

> Find this year's Nobel Prize winners in every category and put them in a table with source links.

You watch every step while it runs, you can append "only physics this time" if it drifts, and you can stop it if it looks wrong.

### 2. CLI: turn the browser into an API you can orchestrate

This is the layer I find better suited to engineering work. Install:

```bash
npm install --global qz-browser-agent
qz session create --title "Inspect example page" --json
```

With the `sessionId` in hand you push JavaScript into the session:

```bash
qz script --session "$SID" - <<'JS'
// Read three docs in parallel; save a sourced table in qz.
const docs = {
  Playwright: "https://playwright.dev/docs/intro",
  Puppeteer: "https://pptr.dev/guides/what-is-puppeteer",
  Selenium: "https://www.selenium.dev/documentation/webdriver/",
};
const rows = await Promise.all(
  Object.entries(docs).map(async ([Tool, Source]) => {
    const page = qz.tab(await qz.openTab({ url: Source }));
    const { text } = await page.read();
    return { Tool, Summary: text.split("\n\n").find(p => !p.startsWith("#")), Source };
  }),
);
await qz.call("data_store", { action: "insert", table: "browser_automation_docs", rows });
return { rows: rows.length };
JS
```

stdout comes back as JSON: `{ok, result, trace}` — `result` is the business value you returned, `trace` holds the checkpoints and errors the script wrote.

The SDK covers the full browser surface:

| Purpose | Methods |
| --- | --- |
| Tabs | `qz.openTab({url, tabAlias})`, `qz.tab(tabRef\|alias)`, `qz.listTabs()`, `page.goto()`, `page.setMode("mobile")` |
| Reading | `page.read({limit})`, `page.find({role\|tag\|type\|pattern})`, `page.axTree({scope})`, `page.screenshot()` |
| Acting | `page.evaluate(code, args)`, `page.locator(q).click()/fill()/select()/check()/press()/hover()/dragTo()` |
| Waiting | `page.waitForURL()`, `page.waitForLoad()`, `page.waitForFunction()`, `locator.wait({state\|count})` |
| Capabilities | `qz.call(name, args)`, `qz.listTools()`, `qz.call("load_skill", {name})` |

A few details decide how pleasant the scripts are to write:

- **The outer script has no `document`, `window` or Node APIs.** It reaches the browser only through the SDK; the page function inside `page.evaluate` has full DOM but cannot call the SDK. The boundary is clean.
- **Actions dispatch once and are never replayed.** An element operation first resolves a single match, waits until it is usable, then dispatches exactly once. If it comes back with `confirmationRequired: true`, the action may already have taken effect and you should verify locally — the tool will not click again on its own.
- **When an action must trigger navigation, pass `waitFor: "navigation"` or `waitFor: "popup"`.** The listener is installed before the dispatch. A failed wait still does not replay the action.
- **Results longer than roughly 48,000 characters are truncated** into `{truncated, totalChars, limitChars, preview}`, so page large results instead of expecting one giant return value.

### 3. Let another agent drive: Skills, MCP and the DSH plugin

If you already work with a coding agent, teach it to drive the browser:

```bash
npx skills add alibaba/qz-browser-agent -g
```

That Skill teaches your agent the correct way to use `qz script`: how to create a session, bind a page, observe before acting, and recover from failures. You can also run an MCP server (`qz mcp`) for any MCP-capable client.

Worth noting: the repository also ships a **DeepSeek Harness plugin** (`services/dsh-plugin/`). Its `qz_browser` tool runs scripts through the qz CLI and renders results, traces, scripts and screenshots as a compact conversation card. The `dsh-browser-qz` npm package is not published yet (the README says "after this package is published"), but the source is in the repository, next to the `dsh plugin --profile web add dsh-browser-qz` command.

## 4. Scenario one: filling in a form nobody wants to touch

Take your example: **the company performance-allocation page**. Filling the main field is trivial; the tedious part is rating the reviews of the colleagues around you — dozens of rows, a dropdown per row, a popover to choose from, and a repaint after every pick. It is extremely easy to miss one or two.

That is exactly where qz is at its best:

1. **Observe first, then act.** `page.read()` gets the text, `page.find({role:"combobox"})` or `page.axTree()` lists the controls, each with a `target` (`uid:` / `css:`), a `rect` and a semantic role. The model does not guess selectors; it decides while looking at a structured inventory of controls.
2. **Actions require a unique match.** `page.locator({role:"option", name:"A+"})` must resolve to exactly one element, and an ambiguous match is reported as such. In a bulk-fill job that is a safety feature: it would rather stop and let you disambiguate than quietly pick one.
3. **Verify after filling.** `locator.inspect()` reads the current state, `locator.read()` reads the text, `locator.wait({count: 30})` waits until the expected number of rows is there. For something as irreversible as a submitted review, that step matters more than the filling.
4. **Save it as a Skill.** Once "fill in and submit this quarter's review table" works, "fill last quarter's review" reuses it — including the tacit knowledge of which column takes an A, which takes a B and which stays blank.

The practical boundaries: **logins, captchas and challenges must be completed by you** in the browser; native `alert`/`confirm` dialogs are left for you to answer; and before a submit that writes, you get a `confirmationRequired` prompt. That is deliberate — for write operations the last step stays human.

## 5. Scenario two: pulling key information out of scattered pages

The project's own example is representative: read the Playwright, Puppeteer and Selenium documentation, extract one summary per project, store it as a sourced table, and export it:

```bash
qz data export "browser_automation_tool_comparison" --format csv
```

Three things combine to make this work:

- **`read_article`** extracts the main content with Readability (`@mozilla/readability`), reducing a messy page to clean text.
- **`data_store`** writes structured results into a named table that can be queried, exported and reused inside the session.
- **Parallel subtasks.** A big research job is split into several subtasks that run at once, each gathering its own material, and the results are merged. The official "Kyoto attractions gallery" example runs five subtasks in parallel and merges them into one gallery.

One level up, the report or table itself can be saved as a **Skill**, and results can be rendered as custom cards (summary cards, image grids, tables) inside the conversation. In other words, "read GitHub Trending and write a weekly report" is a repeated chore that becomes a reusable Skill after the first run.

## 6. Scenario three: running a UI test and keeping the evidence

Two things developers habitually skip: repeating the same flow over and over, and being able to say exactly what was tested. qz has a reasonable answer to both.

**Running the full flow.** `qz script` accepts arbitrary orchestration: open the staging environment, sign in, wait for an element, click, type, assert, screenshot. `Promise.all` runs several page flows in parallel (actions on one tab serialize automatically), and `Promise.allSettled` keeps every branch's outcome.

**Screenshots.** `page.screenshot()` images are normalized to a 2048px long edge and 2MiB per image; **screenshots of interactive elements carry coordinates**, which means "screenshot plus coordinates" can feed the next action directly. There is a practical detail handled for you: after capturing, the tool waits 200ms and compares the current state, retrying once if the frame changed — so a stale screenshot never becomes a fact.

**Recording the operations.** Three pieces combine: the call timeline in the side panel (tool, arguments, result), the `trace()` checkpoints and errors of each run, and the session export (text, tables, and formulas — formulas are embedded as self-contained SVG, so the export reads correctly offline).

"what did this regression run actually cover" then has an answer: not "I clicked through it", but an exportable log, screenshots and the result of every assertion.

Worth keeping in mind: qz is currently positioned more as **human-driven automation** than as unattended testing in CI. It runs in your own browser, relies on your login state, and leaves dialogs and captchas to you. For real CI you would still pair it with the Playwright stack (qz uses Playwright 1.61 for its own test suites). But for "I have to verify this page flow again while I develop", it saves a pile of selector maintenance.

## 7. Boundaries, costs and my own read

A few things worth knowing before you install it.

**It is model-driven, so accuracy follows your model and the clarity of the page.** When the markup is messy and controls carry no semantics (`role`/`name` missing), the observations degrade. In that case, writing explicit CSS selectors and steps into the Skill beats letting the model improvise.

**Do the data-flow arithmetic.** "Local first" means "qz itself runs no server" — not "data never leaves your machine". Task context is sent to the model service you configured, and Skills and MCP connections may exchange data with services you configure. The project says this plainly in `docs/permissions.md`; assess it yourself for sensitive scenarios.

**Permissions are layered.** There is a first-use data consent record; location needs its own approval; navigation, script execution, Skill calls and MCP all sit behind shared security guardrails, and a user grant applies to the named target rather than being a master key.

**Maturity.** Chrome and Edge are shipped; Firefox is in progress (an unsigned `.xpi` exists for local checks). The npm package `qz-browser-agent` is at 0.1.5 (2026-11-08) with roughly 1.2k downloads per month — a very young project with a notably solid architecture and documentation set. Of the 1658 files in the repository, 639 are tests.

**Which layer to use.** Want to "direct a browser that does the work"? Use the side panel. Want the browser in your own tooling? Use the CLI plus Skills. Already running a coding agent? Install the Skill and let it drive qz.

## Closing thoughts

The most valuable part of qz may not be that it can click buttons. It is that it turns "**a flow a human has done**" into "**a reusable asset**". Whether a form is filled correctly or a page is read accurately is a one-off; but "we have already walked this performance process three times" — once that experience is captured as a Skill, it becomes something a team owns.

In that light it is not a replacement for Playwright. Playwright answers "how do I reproduce one known path reliably"; qz answers "how does an ambiguous, live task on a messy page get finished — and how do I run it again tomorrow". The first is a script a machine follows, the second is more like an assistant that lives in your browser, does the work, and remembers how it did it.

If some internal system made of "a table, a popover and thirty rows" is currently draining your afternoon, or you assemble the same weekly report from ten websites every Friday, it is worth twenty minutes to install it and try.
