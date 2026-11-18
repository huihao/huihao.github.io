---
title: Alma：把「谁在等你」做成第一公民的 Agent Harness
date: 2026-11-16 16:30:00
categories: [工具]
tags: [AI Agent, harness, 本地优先, 桌面应用, 开源, 效率工具]
description: Alma 是 yetone 做的桌面 + 移动 Agent harness，同时是开源项目 herdr 的图形客户端。它最有价值的地方不是又一个聊天窗口，而是三件事：把「谁需要你」变成可推送的状态流、把工具调用拆给一个独立的轻量模型、把浏览器操作变成带回执的审计记录。本文拆解这些设计，并对照 Claude Code、Codex、Cursor、OpenCode、Goose 等工具说明它强在哪、弱在哪。
translation_key: alma-agent-harness
lang: zh
ai_written: true
image: /dist/img/cover-alma-agent-harness.png
---

过去两年我拆过不少 Agent 工具，它们的共同点是把 Agent 做成一个**更聪明的终端**：你敲一句话，它去调工具、读文件、写代码。

但有件事一直没被解决：**Agent 跑起来了，人却守在旁边等**。跑三个任务就是三个终端窗口，跑十个就是十条消息流。人成了瓶颈，而且是那种最笨的瓶颈——大部分时间在等，偶尔需要在某个窗口里回一句"是，继续"。

[Alma](https://alma.now/)（yetone / 陈皓）想解决的就是这一层。它是一个桌面 + 移动的 Agent harness，同时还是开源项目 [herdr](https://herdr.dev/) 的图形客户端。这个"双重身份"不是噱头，而是理解它的钥匙。

本文基于 Alma 与 herdr 的公开文档做拆解，先讲它是什么，再讲我认为最值得抄的六个设计，最后说它和其他 harness 相比强在哪、弱在哪。

## 一、先说清楚 Alma 是什么

它有两个身份：

**一、本体：一个完整的 harness。** 20+ 内置工具、MCP、Skills、语义记忆、Artifacts、内置浏览器 + Chrome Relay、本地数据库、多模型（OpenAI / Anthropic / Gemini / DeepSeek / OpenRouter / 任何兼容 API），对话中途可以换模型。

**二、herdr 的图形客户端。** 把 herdr 里跑着的 Claude Code / Codex / pi 面板读成对话——工具调用、子 Agent、文件改动按序排好，随时能切回真实终端。

一个反直觉的事实：**Alma 本体不开源**。主应用没有公开仓库，公开的只有发版仓库 `yetone/alma-releases` 和 MIT 协议的插件 API 包 `alma-plugin-api`（npm 上最新 0.1.2）。真正开源的那一半是 herdr——Apache 2.0，`herdrdev/herdr`、`herdrdev/herdr-app`、`herdrdev/herdr-core` 三个仓库。

先记住这个事实：Alma 与 herdr 的分界线，恰好划在"通用 harness"和"专用客户端"之间。

## 二、最有用的六个特性

### 1. 把「谁在等你」做成状态，而不是窗口

Alma 侧边栏的 agent 视图按状态分组：**Needs input / Working / Done**。

这可能是全文最重要的一句话。它和"再开一个终端窗口"的区别是根本性的：

- 终端模型里，状态藏在标题栏、进度条里，或者你得切回去扫一眼才知道。
- Alma 里，状态是**一等的、可推送的**。Agent 卡住等你拍板时，桌面通知推给你；iPhone 端也能收推送、直接回。

herdr 侧还提供 **OSC 7501** 开放状态协议：任何程序只要 `printf '\e]7501;state=blocked:app=my-agent\e\'` 就能上报自己的状态。它不是私有 API，而是终端里的一个公开约定——你的脚本、你的 CI、你手搓的小 Agent，都能被 Alma 收进同一个收件箱。

还有一个容易被忽略的细节：herdr 的 Agent 跑在常驻的 **herdr-core** 服务里。关掉窗口、升级客户端、甚至客户端崩了，Agent 还在跑。你回来时它还活着。

### 2. 工具调用交给另一个模型（Tool Model）

Alma 把四件事从主模型里拆出来，交给一个单独的轻量模型：**选工具、抽参数、读写记忆、给线程自动命名**。

收益直接体现在账单和延迟上：

- 主模型只负责思考与回答；
- 工具模型用廉价的快模型（官方推荐 gpt-4o-mini / claude-haiku-4-5 / gemini-2.0-flash），文档明确要求响应 **< 2.5s**，并且**不要**用推理模型（o1 / o3 / extended thinking）当工具模型——那会让每一次工具选择都变慢变贵。

现在多数 harness 是"一个大模型包办一切"，每调一次工具都要走一次昂贵的大模型往返。Alma 等于给 harness 的调度层单独做了一次降本降延迟。设置在 Settings → General → Tool Model，默认自动探测。

### 3. 看得见的记忆

Alma 的记忆走的是 **抽取 → 语义嵌入 → 每次回答前检索**，而且**每一条都摆在你面前**：可以改内容、设重要度（0–1，越大越优先召回）、打标签、选持久性（Permanent 永不自动删 / Temporary 维护时可能被剪枝）、看来源（Chat / Manual / Auto），也能删、能一键 Clear All。

默认参数：Max Retrieved = 10、相似度阈值 0.7、Query Rewriting 开启。嵌入模型默认 `text-embedding-3-small`，也能换成 3-large、Google 或任意 OpenAI 兼容端点，甚至 Rebuild Embeddings。

对比一下常见做法：

| 做法 | 记忆长什么样 | 谁来维护 |
| --- | --- | --- |
| `CLAUDE.md` / `AGENTS.md` | 你手写的文件 | 你 |
| 主流 harness 的 session memory | 自动塞进上下文的一段 | 黑盒 |
| Alma | 自动抽取 + 语义检索，每条是一行**可见、可改、可删**的记录 | 你（可审计） |

这不是"更聪明的记忆"，是**记忆的公共设施**。还有 Incognito Mode：这一轮对话既不建记忆也不检索记忆。

要说清楚的是：Alma 的记忆同样会落成文件，Claude Code 也有文件式的自动记忆，两者都"看得见"。真正的差别不在存不存得下，而在**怎么被找出来**——Alma 走的是带嵌入的语义检索，相似度阈值、重要度、持久性都是可调参数；而文件式记忆只有在你恰好写进去的时候才生效。

### 4. Chrome Relay：浏览器操作要带回执

这是我认为 Alma 工程做得最扎实的一块。它不是"开一个远程浏览器给你看"，而是**接管你自己正在用的 Chrome**（走 CDP 扩展），继承你的登录态。链路是：

```text
AI Chat → ChromeRelay tools → Alma Server → WebSocket → Chrome Extension → chrome.debugger → Your Tab
```

真正让我觉得值得抄的是它的**回执语义**。

ReadDom 返回的不是 DOM Dump，而是一张**可交互元素地图**：

```text
e11 link "Pull requests" <a#pr-nav> href=/pulls sel=#pr-nav
```

`e11` 这样的 ref 可以直接当 selector 用；被遮挡的元素会明确标出来：`[hidden: covered at its click point by <div.modal-overlay>]`。

而 Click 的返回值是结构化的：

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

`matchCount` 告诉你选择器是不是太松（命中多个就是有歧义）。Type 会区分"不存在 / 不可输入 / disabled / readonly / 写入未生效"几种失败，而不是笼统报个错。Eval 会 await Promise，回传真实值和 JS 类型。

最有分量的规则是：**人点不到，Agent 就不许点。** `display:none`、`visibility:hidden`、`opacity:0`、`transform:scale(0)`、零尺寸、被上层浮层盖住点击点、`left:-9999px` 这种屏幕阅读器专用技巧，一律拒绝；要强行点必须显式传 `allowHidden: true`。仅仅"滚出视口"不算，会先滚动再点。

浏览器 Agent 最大的失败模式就是"点了个看不见的东西，然后报告成功"。Alma 把"点击成功"定义成可审计的事实：点了哪个元素、匹配了几个、有没有发生导航、开了哪些新标签页。

其余 11 个工具是：ListTabs / Navigate / Click / Type / Screenshot / Read（Readability 转 Markdown）/ ReadDom / Eval / Scroll / Back / Forward。本地 WebSocket 默认端口 23001，需要 Auth Token；一键启动要求先完全退出 Chrome（要靠 `--load-extension` 挂扩展）。

### 5. Artifacts：把答案变成能跑的东西

HTML（隔离 iframe 沙箱）、React（JSX 编译、hooks、内置 Tailwind）、Mermaid、SVG、代码高亮，都在对话旁边开一个可交互预览面板：能刷新、全屏、下载、看源码、拖拽调大小。React / HTML 项目还能直接起 dev server（Bun + Vite），带状态、日志和热重载。

它解决的是 LLM 界面一个老问题：模型给你一段 HTML，你得复制到文件里、用浏览器打开、再改、再贴回去。Artifacts 把这个来回压缩成"就在旁边"。

### 6. 本地优先，和一条端到端加密的中继

对话存在你自己机器的数据库里，API Key 直接连服务商，不经过 Alma 的云。手机端配对走 Alma relay 时是端到端加密的，也可以同一 Wi-Fi 直连；iPhone 端还能直接看并操作 Mac 屏幕（Remote Screen，需要录屏 + 辅助功能权限，仅 Mac）。

再补两个 Alma 自己特有的小设计：

- **MCP 输出安全模式**：MCP 工具可以在 `_meta["alma/outputSafetyMode"]` 里声明 `exact`（原样保留）/ `compact`（允许压缩大文本）/ `passthrough`（跳过压缩，适合二进制负载），也支持在 description 里写 `[alma-output-safety: exact]` 兜底。源码、ID、结构化数据必须 `exact`，日志和搜索结果才配 `compact`。这是在解决 MCP 生态里一个真实但被普遍忽略的问题。
- **Prompt Apps**：把常用 prompt 做成带表单的模板（Text / Select / Checkbox / Date / File…），可以钉死模型、工具集、推理强度、隐身模式，绑定快捷键，导出 JSON 分享。

## 三、和别的 harness 比，Alma 强在哪

先摆一张形状对照表（信息截至 2026 年 11 月，依据各项目公开文档）：

| 工具 | 形态 | 多模型 | 记忆 | MCP | 操作真实浏览器 | 手机可达 | 能接管别的 Agent 吗 | 开源 |
| --- | --- | :-: | :-: | :-: | :-: | :-: | :-: | :-: |
| Claude Code | 终端 + 桌面 + Web | 仅自家（改 base URL 可换） | `CLAUDE.md` + 文件式自动记忆 | ✅ | ❌ | 云端任务间接可达 | ❌ | ❌ |
| Codex CLI | 终端 + 云端任务 | ❌ | `AGENTS.md` | ✅ | ❌ | 云端任务间接可达 | ❌ | ✅ Apache-2.0 |
| Cursor / Cline / Roo | IDE 内 | ✅ | 规则文件 | ✅ | 部分 | ❌ | ❌ | Cline / Roo ✅ |
| OpenCode | 终端 + 桌面 + Web | ✅ | 会话文件 + Instructions | ✅ | ❌ | `opencode pair` 配对网页（无推送） | ❌ | ✅ |
| Goose | 桌面 + CLI | ✅ | 内置 | ✅（原生扩展） | 有限 | ❌ | ❌ | ✅ Apache-2.0 |
| Alma | 桌面 + 移动 | ✅ | 语义检索、逐条可见 | ✅ | ✅（带回执） | ✅（推送 + 远程屏幕） | ✅ | 仅插件 API |

（表格依据各项目公开文档与仓库：[Claude Code](https://code.claude.com/docs/en/overview)、[Codex CLI](https://github.com/openai/codex)、[OpenCode](https://opencode.ai/docs/)、[Goose](https://goose-docs.ai/docs/getting-started/installation)。截至 2026 年 11 月。）

需要先说清楚一件事：**"有个图形界面"本身已经不构成差异了。** 到 2026 年 11 月，Claude Code 有桌面版和 Web 版，Codex 有云端任务，OpenCode 有终端、桌面和 Web 三种形态（`opencode pair` 还能生成一次性配对链接，从别的设备打开它的 Web 界面），Goose 有桌面版和 CLI。也就是说，"装个 GUI"这件事，大家都做过了，Alma 不比别人多一块屏幕。

真正值得说的差异只有三条：

**第一，Alma 的竞争维度不是模型能力，而是注意力调度。** 别的工具都在比"谁更会写代码"，Alma 在比"你怎么知道哪个 Agent 现在需要你"。当 Agent 从 1 个变成 10 个，"等待"本身就成了主要工作。这一层目前几乎没人认真做——OpenCode 的 pair 链接能让你在手机上打开界面，但那是"远程控制一个 Agent"，不是"收一箱等待你回复的 Agent"。

**第二，Alma 是唯一把"别人的 Agent 进程"收进同一个 UI 的。** IDE 插件是在编辑器里加一个 Agent；Alma 是在**所有 Agent 外面**加一层 UI。Claude Code、Codex、pi 的转录被直接读取，你甚至不用改它们的任何配置——Alma 自己找 socket（`HERDR_SOCKET_PATH` → `<config>/herdr/sessions/<name>/herdr.sock` → `<config>/herdr/herdr.sock`），也会读你的登录 shell 环境。

**第三，本地优先 + 自己的 Key，这在 2026 年已经是稀缺属性。** 对话、设置、记忆都在本机；Alma 只是 UI 层。配合 iPhone 端推送到"谁需要你"，它成了少数能真正做到**离开电脑也不失控**的 Agent harness。

顺带说一句 herdr 自己的设计，它比 Alma 更激进：herdr 里 Agent 可以派生 Agent（`hc run --bg codex "review my diff. Done: hc send t1"`），子 Agent 跑完把报告回灌给主 Agent（`<hc from="t3 reviewer">`）。一个 Agent 评审另一个 Agent 的产出，这是把 Agent 从"工具调用者"变成"同事"的开始。

这里才是"哪一半开源"值钱的地方：**Alma 只是 herdr 的客户端之一。** herdr-core 开源，意味着你可以自己编译一份，让 Alma 连上去读面板；将来就算出了别的客户端——一个纯 TUI、一个只负责推通知的小机器人——接的还是同一个 socket。反过来看，如果哪天 Alma 不更新了，你手上的 agent 基础设施还完整地留在 herdr 里。

而 Alma 的"本体"那一半恰恰是通用 harness：它不依赖 herdr 也能独立当工作台用。这才是它敢把两个身份塞进同一个产品里的底气——**一个是可替换的前端，一个是可以独立存在的工作台。**

## 四、它的短板，也得说清楚

**客户端不开源。** 想改核心只能靠插件 API（TypeScript，MIT），而插件生态还很小：`alma-plugin-api` 最新 0.1.2，近 30 天下载量 89 次，注册表 `yetone/alma-plugins` 也刚起步。herdr 全套 Apache 2.0 可以自己编译，Alma 只能等作者。

**文档跑在功能后面。** reasoning 页的支持模型表里还留着 o1-preview、o1-mini、Claude 3.5 Sonnet；安装指南还写着 Linux "coming soon"，下载页却已经放出 AppImage / deb / rpm。以文档为准容易踩空。

**herdr 侧的限制是真实的。** 跑在 tmux 里的 Agent 没法上报状态；机器重启或服务停掉后不会自动恢复 Agent（只恢复面板 shell）；TUI 与新 app 是两个独立程序，不共享 Agent。

**Chrome Relay 有前置条件。** 要装扩展，一键启动要求 Chrome 完全退出；新开的标签页默认不挂 debugger，Chrome 要求逐标签授权——这是 Chrome 的安全模型，不是 Alma 的 bug，但"自动化一段跨标签流程"确实会在这里卡一下。

**依赖关系要想明白。** Alma 的 herdr 视图需要本机跑着 herdr-core。不装 herdr，Alma 就是一个普通桌面 harness——作者自己说"不接 herdr，它本身也很强"，这个自评是准确的，不是场面话。

## 五、适合谁，不适合谁

**适合：**

- 同时跑多个编程 Agent，需要一个统一收件箱的人；
- 想在手机上收到"我需要你确认"并直接回复的人；
- 想自建本地优先、带 MCP / Skills / 可审计记忆的桌面工作台的人；
- 想在**真实 Chrome**（带登录态）里让 Agent 干活，同时要求每一步可审计的人。

**不适合：**

- 追求纯终端效率、讨厌 GUI 的人——herdr TUI 更合适；
- 必须要可审计、可自托管全栈源码的团队——OpenCode / Goose 这类更合适；
- 需要在 IDE 内做 diff 审查的人——Cursor / Cline 更顺手；
- 只想聊点什么的——它比不过一个网页聊天窗口。

## 六、上手路径

1. 装桌面端：macOS dmg / Windows x64.exe / Linux AppImage·deb·rpm，或 `alma --install`；
2. 装 herdr：`curl -fsSL https://releases.herdr.dev/app/install.sh | sh`，把 Claude Code / Codex 跑进它的面板；
3. Alma 侧边栏切到 agents 视图（Mac 上是 ⌘⇧A），它会自动找到本机 herdr 服务，不用改你现有的用法；
4. 手机端装 TestFlight 版，扫码配对，开始收推送；
5. Chrome Relay：装扩展 → 填 Auth Token → 授权你要操作的标签页。

**顺便一个辨析**：npm 上的 `@alma-harness/*`（loop / memory / runtime / conversation / batch / execution / single-call，0.41.0，Apache-2.0，仓库是 `FabioFernandesCarneiro/alma`）跟 yetone 的 Alma **没有关系**，是另一个作者做的同名项目。搜索的时候别搞混。

## 结语

Alma 真正的贡献不是又一个聊天窗口，而是给"多 Agent 并行"这件事补上了一个**人机界面**：谁在跑、谁卡住了、谁在等你，一屏之内看得清楚，手机上随时能接。

在这个前提下，其他那些功能——独立工具模型、可见的记忆、带回执的浏览器操作、Artifacts——才站得住脚：它们解决的不是"Agent 能不能做事"，而是"人和一堆 Agent 一起做事时，账算不算得清、动作查不查得到、界面会不会把流程撑爆"。

如果你已经在同时开三四个终端窗口做 Agent 编排，Alma 值得花二十分钟装上试试；如果你就是想安静写代码，它的 TUI 替代品和那个笨办法都还在。
