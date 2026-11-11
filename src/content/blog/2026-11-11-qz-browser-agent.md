---
title: 轻舟 qz：跑在你自己浏览器里的开源 Agent，能填表单、能读页面、能做 UI 回归测试
date: 2026-11-11 07:00:00
categories: [工具]
tags: [浏览器自动化, AI Agent, 开源, 效率工具, 测试]
description: qz（轻舟）是阿里巴巴开源的本地优先浏览器 Agent：以 Chrome 扩展的形式跑在你自己的浏览器里，自带模型无关的技能体系与 CLI/MCP。本文拆解它的中心思想与架构，并落到三个具体场景——填写复杂表单、提取页面关键信息、把 UI 测试跑通并留下截图与操作记录。
translation_key: qz-browser-agent
lang: zh
image: /dist/img/cover-qz-browser-agent.png
---

过去两年，"浏览器 Agent" 这个词被用得很滥：录屏、放一个光标、让模型猜下一步要点什么。这类演示看起来很酷，落到真实工作里却经常卡在同一个地方——**登录墙、滚动加载、层层嵌套的表单，以及那种"脚本点得对但页面状态不对"的诡异失败**。

阿里的开源项目 [qz（轻舟）](https://github.com/alibaba/qz-browser-agent) 换了一个思路：**不做云端浏览器，而是把 Agent 装进你自己正在用的那个 Chrome 里**。它继承你已有的登录态、Cookie 和扩展，把任务交出去而不是把点击交出去，并且——这是最有意思的部分——**把跑通的工作流沉淀成可复用的 Skill**。

本文先拆解它的中心思想与架构，再落到三个具体场景：填写复杂表单、提取页面关键信息、把 UI 测试跑通并留下截图与操作记录。

## 一、中心思想：交出任务，而不是交出点击

qz 在 README 里放了一张对比表，把自己和 Nanobrowser、Browser Use、agent-browser、Playwright MCP 放在同一张表里比（截至 2026 年 10 月，依据各项目的公开文档）。五列里，qz 拿满 ✅ 的有五项：

| 能力 | qz | Nanobrowser | Browser Use | agent-browser | Playwright MCP |
| --- | :-: | :-: | :-: | :-: | :-: |
| 交出整件事，而不是每一次点击 | ✅ | ◐ | ◐ | ◐ | ❌ |
| 跑在你自己已登录的 Chrome 里 | ✅ | ✅ | ◐ | ◐ | ◐ |
| 人类与 Agent 都能实时接管每一步 | ✅ | ◐ | ◐ | ◐ | ◐ |
| 多任务并行，每个任务还能再分子任务 | ✅ | ◐ | ◐ | ◐ | ◐ |
| 把一次跑通存成可复用的 Skill | ✅ | ❌ | ◐ | ❌ | ❌ |

这张表其实概括了 qz 的全部设计取向：

- **交出整件事。** 你描述"帮我把绩效配置的表单填完并提交"，而不是"点开菜单、找到复选框、逐个勾选"。前者是任务，后者是脚本；前者由模型规划，后者由人维护。qz 里模型拿到的是一整套工具（打开标签页、读正文、找元素、截图、执行脚本、写数据表……），最终动作是它自己排出来的。
- **跑在真实浏览器里。** 你的登录态、企业内网的 SSO、你装的那些油猴脚本、那些"必须用真实 UA 才能看到"的页面——全都在。因为它就是你的 Chrome，不是它租来的一台云主机。
- **人和 Agent 共享同一扇门。** qz 的 Side Panel（侧边栏）里每一步都可见：跑到哪一步、调了哪个工具、返回了什么。任务跑偏了，你可以直接打断它、补一句话纠偏，或者干脆停掉——这是"Agent 给人当副驾驶"，而不是"Agent 自己关起门来乱点"。
- **跑通过一次，就沉淀成 Skill。** 这是我认为最有价值的设计：今天你让它把某个复杂的业务流程走通，明天只要说一句"再跑一次上次的流程"，它加载对应的 Skill 继续干活。Skill 可以存本地，也可以从一个 Git 仓库直接安装给别人用。

再叠上 **Local First**：会话、Skill、采集到的数据都存在你自己的浏览器里，qz 没有自己的服务器，数据只会去你配置的那个模型服务和你要访问的网站。模型也是你自己带的——OpenAI Codex、DeepSeek、Kimi For Coding、OpenRouter、Fireworks，甚至任意一个支持 tool calling 的本地模型服务都行。

## 二、架构：五个上下文，一条主线

qz 是一个 Manifest V3 的 Chrome 扩展，但它的架构并不是"一个巨大的 service worker"。官方 `docs/architecture.md` 里画了一张运行时图，这张图基本就是理解 qz 的钥匙：

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

逐层展开：

**1. Background（`src/background/service-worker.ts`）** 是大脑。它持有任务状态与持久化：一个 Session 对应一串对话、一份记录、一条队列。外部来的请求都要穿过 `Background API`，再进入 Session 命令队列——同一时间一个 Session 只跑一件事，重复的 `clientMessageId` 会被去重，重试可以复用已接受的消息。

**2. Agent Host** 负责把一次运行"装配"起来：注入仓库（历史、检查点、文档）、模型服务、工具运行时以及一把**写租约**（write lease）。写租约的意义在于：同一时刻只有一个执行流有资格写入会话记录，因此不会出现两个并发调用把对话写花。停机、取消、超时都通过 `AbortSignal` 传递，异步操作返回后还要再复核一次租约。

**3. Model Gateway** 负责把各家模型的差异抹平：消息格式、工具调用、流式、错误、用量统计。Agent 自己管语义恢复和重试预算。

**4. Tool Runtime** 是工具目录的执行层：参数校验、权限、安全护栏、限流，然后才是真正执行。模型一次可以返回多个工具调用，运行时最多允许 10 个在途调用并发；同一个标签页上的动作会串行，不同标签页可以并行。

**5. Side Panel（`src/sidepanel/`）** 只负责呈现。Agent 产生的事件被投影成 UI 状态，人看到的是一条可读的时间线，而不是原始事件流。

**6. Content Script（`src/content/content-script.ts`）** 在隔离世界里读 DOM、点元素、填表单。它拿到的是 `uid:` 开句柄（形如 `uid:t3.s7.12`），这样即使页面结构变了，引用也不会张冠李戴。

**7. Offscreen + 沙箱 Worker（`src/offscreen.ts`、`src/runner-sandbox.ts`）** 承担需要 DOM 的重活，并把脚本执行放进隔离的 Worker。

**8. MCP Bridge（`services/mcp-bridge/`）** 是一个本地服务，把扩展暴露给外部客户端（MCP 协议，HTTP）。

还有一个容易被忽略但很关键的设计：**能力（capability）系统**。`src/capabilities/` 目录有 577 个文件，每一个子目录（tabs、skills、sessions、documents、accessibility、media、mcp、providers……）都是一个独立的能力包，通过生成的目录把自己注册进各个运行时。新增一个工具、一个视图、一个模型供应商，都应该是加一个能力包，而不是改核心代码。这也是它能同时支持 Chrome、Edge 和正在推进的 Firefox 的原因——共享代码是主干，差异被收在各能力包里。

## 三、三种用法，从"聊天"到"写脚本"

qz 的用法分三层，可以按你的需要从浅到深：

### 1. 侧边栏：像聊天一样交代任务

装好扩展、配好模型，点开侧边栏直接说人话：

> 找出今年诺贝尔奖各奖项的获奖者，整理成一张带来源链接的表格。

任务跑起来的过程中你能看到每一步；跑偏了可以直接追加一句"只查物理学奖"；看着不对可以点停。

### 2. CLI：用脚本把浏览器变成可编排的 API

这是我认为更适合工程场景的一层。安装：

```bash
npm install --global qz-browser-agent
qz session create --title "Inspect example page" --json
```

拿到 `sessionId` 之后，用 `qz script` 往会话里投一段 JavaScript：

```bash
qz script --session "$SID" - <<'JS'
// 并行读三个文档，把结果存进 qz 的数据表
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

脚本跑完，stdout 是一段 JSON：`{ok, result, trace}`。`result` 是你 return 的业务数据，`trace` 是脚本自己写的检查点和错误。

这一层的 SDK 覆盖了完整的浏览器操作面：

| 目的 | 方法 |
| --- | --- |
| 标签页 | `qz.openTab({url, tabAlias})`、`qz.tab(tabRef\|alias)`、`qz.listTabs()`、`page.goto()`、`page.setMode("mobile")` |
| 读取 | `page.read({limit})`、`page.find({role\|tag\|type\|pattern})`、`page.axTree({scope})`、`page.screenshot()` |
| 执行 | `page.evaluate(code, args)`、`page.locator(q).click()/fill()/select()/check()/press()/hover()/dragTo()` |
| 等待 | `page.waitForURL()`、`page.waitForLoad()`、`page.waitForFunction()`、`locator.wait({state\|count})` |
| 能力调用 | `qz.call(name, args)`、`qz.listTools()`、`qz.call("load_skill", {name})` |

几个细节值得留意，因为它们决定了脚本好不好写：

- **外层脚本没有 `document`/`window`/Node API**，它只能通过 SDK 操作浏览器；但 `page.evaluate` 里的页面函数有完整 DOM，且拿不到 SDK。边界很干净。
- **动作只派发一次，永不重放。** 元素操作会先定位到唯一匹配、等到可用状态，再派发一次。如果返回 `confirmationRequired: true`，意味着这次操作可能已经生效，需要你本地确认——工具不会自作主张再点一次。
- **需要触发跳转时，用 `waitFor: "navigation"` 或 `waitFor: "popup"`**，监听器会在派发之前就装好。失败的等待同样不会重放动作。
- **结果超过约 48,000 字符会被截断**成 `{truncated, totalChars, limitChars, preview}`，所以大数据要分页拿，不要指望一次全量返回。

### 3. 让别的 Agent 来开：Skill、MCP，以及 DSH 插件

如果你已经在用编码 Agent，可以直接让它学会开浏览器：

```bash
npx skills add alibaba/qz-browser-agent -g
```

装完这个 Skill，你的 Agent 就掌握了 `qz script` 的正确姿势：怎么建会话、怎么绑定页面、怎么观察再操作、怎么处理失败恢复。也可以起一个 MCP 服务（`qz mcp`）让任何支持 MCP 的客户端连上来。

顺带一提，qz 仓库里还带了一个 **DeepSeek Harness 插件**（`services/dsh-plugin/`）：`qz_browser` 工具通过 qz CLI 执行脚本，把结果、trace、脚本和截图整理成一张随主题变化的会话卡片。目前 `dsh-browser-qz` 这个 npm 包还没发布（仓库 README 里写的是"包发布之后即可安装"），但源码就在仓库里，跟着 README 里的 `dsh plugin --profile web add dsh-browser-qz` 就能对上号。

## 四、场景一：把没人愿意点的表单填完

先说你提的那个例子：**公司的绩效配置页面**——配置项本身要填，但真正折磨人的是"给周边同事的评审打等级"这一类**跨行操作**：几十行员工、每行一个下拉框、点开还要在浮层里选、选完页面还要重绘，很容易漏掉一两个。

这类表单正好落在 qz 的甜点上：

1. **先观察，再动作。** `page.read()` 读正文，`page.find({role:"combobox"})` 或 `page.axTree()` 把这一页的控件列出来，每个控件带着 `target`（`uid:` / `css:`）、`rect` 和语义角色。模型不需要猜选择器，它看着一份结构化的控件清单来决策。
2. **动作有唯一匹配要求。** `page.locator({role:"option", name:"A+"})` 必须解析到唯一元素，匹配多个就报歧义——这在批量填表时是一种保护：它宁可停下来让你明确，也不替你猜一个。
3. **填完要验。** `locator.inspect()` 读当前状态，`locator.read()` 读文本，`locator.wait({count: 30})` 等到期望的行数出现。绩效这种"提交之后不可撤回"的场景，这一步比填表本身更重要。
4. **跑一次，存成 Skill。** "把本季度绩效表填完并提交"这套流程一旦走通，下次说一句"填上季度绩效"就能复用——连"哪一列要填 A、哪一列要填 B、哪一格要留空"这种隐性知识都被固化在 Skill 里。

需要注意的现实边界：**登录、验证码、人机校验必须你自己在浏览器里过**；原生 `alert`/`confirm` 弹窗 qz 不会替你点，会留给你；提交前它会给出 `confirmationRequired` 提示，让你确认结果。这是有意为之——涉及写操作时，把最后一步留给人。

## 五、场景二：从散落的页面里把关键信息抽出来

qz 官方给的例子很典型：读 Playwright、Puppeteer、Selenium 三份官方文档，各自提炼摘要，存成一张带来源链接的表，然后导出成 CSV：

```bash
qz data export "browser_automation_tool_comparison" --format csv
```

它在这件事上的能力来自三个组合：

- **`read_article`** 用 Readability 抽取正文（依赖 `@mozilla/readability` ✓），把一个复杂页面压成干净文本；
- **`data_store`** 把结构化结果写进具名数据表，之后可以查、可以导出、可以在会话里复用；
- **并行子任务**。一个大调研会被拆成多个子任务同时跑，每个子任务自己找资料，最后合并。官方的"京都景点相册"例子就是 5 个子任务并行找图，合并成一个相册。

再往上还有一层：**报告和表格可以被存成 Skill**，也可以直接做成"自定义结果卡片"（摘要卡、图片网格、表格）在会话里展示。也就是说，"每周读 GitHub Trending 出一份周报"这类重复的调研工作，跑通一次之后就是一个可复用的 Skill。

## 六、场景三：把 UI 测试跑通，并留下证据

开发阶段最容易偷懒的两件事，一是重复点同一个流程，二是说不清"我到底测了什么"。qz 在这两件事上都能给出比较完整的答案：

**执行完整的测试流程。** `qz script` 里可以写出任意编排：打开测试环境、登录、等某个元素出现、点、填、断言、截图。`Promise.all` 可以并行跑多个页面的流程（同一标签页上的动作会自动串行），`Promise.allSettled` 可以保留每一条分支的结果。

**截图。** `page.screenshot()` 的图片被规范到长边 2048px、单张不超过 2MiB；**可交互元素的截图会带上坐标**，这意味着"截图 + 坐标"可以直接喂给下一轮操作。工具还会处理一个很实际的细节：截图后等 200ms 再比对当前状态，如果画面变了就自动重试一次——避免把一张过期截图当成事实。

**记录操作内容。** 这一层由三部分拼起来：Side Panel 里那条按时间排列的调用记录（工具名、参数、结果）；每一步的 `trace()` 检查点与错误；以及会话的导出能力（文本、表格、公式——公式会以自包含 SVG 嵌进去，导出后离线也能看）。

于是"这次回归跑了什么"就有答案了：不是一句"我点过了"，而是可导出的记录、截图和每一步的断言结果。

需要提醒的是，qz 目前的定位更偏"**人工主导的自动化**"而不是"CI 里的无人值守测试"：它跑在你自己的浏览器里、依赖你的登录态、弹窗和验证码要人处理。真要放进 CI，还需要配合 Playwright 那套（qz 自己也用 Playwright 1.61 做它自己的测试套件）。但对于"开发中我自己要反复验证这个页面流程"，它比写一堆选择器更省事。

## 七、边界、代价与我的判断

最后说几句实际使用前该知道的事。

**它是模型驱动的，准确率取决于你配的模型和页面的清晰度。** 页面结构混乱、控件没有语义标签（`role`/`name` 缺失）时，观察结果会变差，这时候给 Skill 里写好明确的 CSS 选择器和步骤，比让模型自由发挥可靠得多。

**数据流向要算清楚。** Local First 指的是"qz 自己没有服务器"，不是"数据不出你的机器"。任务上下文会发给你配置的模型服务，Skill 和 MCP 连接也可能和你配置的服务交换数据——这一点官方在 `docs/permissions.md` 里写得很直白。涉密场景要自己评估。

**权限是分级的。** 首次使用有数据同意记录；定位信息有单独的授权；导航、执行脚本、调用 Skill、MCP 都有共享的安全护栏，用户的授权是"授予某个目标"而不是一把万能钥匙。

**成熟度。** Chrome 和 Edge 已经发布，Firefox 还在推进（有未签名的 `.xpi` 便于本地验证）；npm 包 `qz-browser-agent` 最新版 0.1.5（2026-11-08），月下载量约 1.2k——这是一个非常年轻、但架构和文档都相当扎实的项目。仓库 1658 个文件里，测试占了 639 个。

**用法选择建议。** 想要"像人一样指挥一个会干活的浏览器"，用侧边栏；想要"把浏览器操作写进脚本、接进自己的工具链"，用 CLI + Skill；已经在用编码 Agent，就装那个 Skill，让它去驱动 qz。

## 结语

qz 最有价值的地方，可能不是它能点按钮，而是它把"**人做过的流程**"变成"**可复用的资产**"。表单填得对不对、页面信息抽得准不准，这些是一次性的；但"绩效配置这套流程我们已经走通过三遍了"这种经验，被固化成一个 Skill 之后，就变成了团队资产。

从这个角度看，它和 Playwright 那套自动化不是替代关系：Playwright 解决的是"如何稳定复现一条确定的路径"，qz 解决的是"如何让一个不确定的、活的页面上的模糊任务被完成，并且下一次还能再来一遍"。前者是工程师写给机器的剧本，后者更像是一个住在浏览器里、干完活还会把活儿记下来的助手。

如果你正在被某个"表格 + 浮层 + 几十行"的内部系统折磨，或者每周都要从十个网站拼一份周报，值得花二十分钟装上试试。
