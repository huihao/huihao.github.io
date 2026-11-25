# 素材清单：2026 年下半年大厂工程博客里的"驾驭大模型"实践

> 用途：为正文《指哪到哪：大厂把"驾驭模型"拆成了四件事》提供可引用的素材与出处。
> 采集时间：2026-11-25。取材窗口：**2026-07-01 ~ 2026-11-25**，全部命中"2026 年下半年"。
> 可信度分级：**A** = 厂商官方工程博客/研究页，可直读全文、引用原文与数字（注意其中有相当一部分是**厂商自报数据**，正文引用时须写明"官方博客披露"）；**A+** = 官方文档/白皮书（PDF 或长文）；**B** = 会议演讲实录、媒体访谈、第三方拆解（引用需注明出处）；**C** = 个人博客/转译（仅作补充线索，不引数字）。
> 说明：本文与站内《前端岗位的消失论》不冲突——那篇讲**岗位结构**（活儿怎么被重新分配），本篇讲**个人掌控力**（怎么把模型指挥明白）。美团、阿里两条线会重叠，**已在本文件标注重用位置**。

---

## A 级（一）：Meta — 把"人"从环里挪到环上

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| M1 | How Meta Built Forum With AI-Native Engineering | 2026-10-15 | https://engineering.fb.com/2026/10/15/ml-applications/how-meta-built-forum-ai-native-engineering/ | 小团队从零建 Forum（Facebook Groups 的独立 App）。①**成功定义不是代码量**，而是"verified, production-ready outcomes"——能构建、过测试、扛过评审。②**human-in-the-loop vs human-on-the-loop**：前者工程师驱动每一步、AI 在步骤里辅助；后者 agent 自己跑"计划→实现→构建→测试→纠正→重试"的循环，人定目标、看运行、跑偏时介入、最后签字。③**门槛设在 verification 而非 compilation**：自动测试 + UI 视觉检查都过才算完成，agent 先自检再交人，所以送到人面前的是"更少但更可信"的一批。④四项配套能力：planning as technical specification（把计划做成技术规格）；automated verification inside the loop（构建状态、单测、UI spec 匹配作为 pass/fail 信号接进循环）；simulated user testing（导航 agent 像人一样点、看屏、报回归）；agentic production operations（用户反馈→自动根因分析→工程师决策）。⑤**运维模型五件套**：Rules（同一错误重复两次以上，就编码成一条永久规则给所有人）、Skills、Agents、Commands、Hooks。⑥**最大收益来自改代码和工具，不是改 prompt**：架构可读性（模式改一次，之后每个 agent session 都继承）、**给 agent 工具而不是描述**（读 simulator 视图层级、列屏幕元素、查目标视图路径，误改大幅下降）、build-level isolation（插件/插槽架构把原型代码从生产构建里物理剔除）。⑦AI 压力测试常态化跑，agent 自己隔离 repro→提修复→验证，内存与 page fault 问题在开发期发现，内存使用约减半。⑧**8 周达到与 Facebook Groups 的核心功能平价**，AI 承担了大量常规实现。 |

## A 级（二）：Atlassian — 代码提速了，团队吞吐没提速

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| A1 | 6K engineers, 1M agent sessions: scaling the AI SDLC at Atlassian | 2026-11-23 | https://www.atlassian.com/blog/ai-at-work/scaling-the-ai-sdlc-at-atlassian | 6000 名工程师、**100 万+ agent session**、20+ 产品。①**核心反差**：DX 纵向数据显示，AI 参与 PR 比例接近 100% 时，**团队吞吐提升卡在约 10%**。②原因：**开发者只有约 16% 的时间在写代码，84% 在计划、协调、取上下文、评审、运维、以及连接交付各环节的决策**。③三个系统性问题：上下文碎片化（业务意图/架构约束/设计决策在不同工具间反复复制）、编排与审计缺口（没有标准方式在人和专职 agent 之间路由工作、定权限、审计谁改的）、跨职能摩擦（State of Teams 2026：只有 **48%** 高管认为 AI 改善了协作）。④左半边（代码之前）：Jira Planner 把对话变成结构化实施计划、推荐哪些工作交给人哪些交给 agent；Jira Cloud for Slack 让"请求的来龙去脉"跟着请求一起进系统；Triage Agent 接手查重、定优先级、分派。⑤右半边（代码之后）：标准不再埋在文档里而是做成工作流的一部分，人和 agent 的代码过同一道质量门；Code Reviewer **把 PR 周期时间减少 45%**。⑥**主动 agent 运行自动解决 51% 的潜在安全漏洞**，被合并的主动运行**每周省约 50 个工程日**，issue 周期 **11.5 天 → 6.7 天**。⑦**连通上下文**（Teamwork Graph 打通 Jira/Confluence/Bitbucket/Slack/Figma/GitHub）后：回答质量 **+44%**、token 消耗 **−48%**。⑧金句："The agent is interchangeable. The system of record and the context underneath it are not."；"价值不只是 agent 写了代码，而是我们改变了谁来做这件事。" |

## A 级（三）：Shopify — 一场 12 周的重写，和瓶颈的逐次搬家

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| S1 | How we rebuilt the Shopify app in 12 weeks (2026) | 2026-11-10 | https://shopify.engineering/shopify-app-rebuild | **30 名工程师、12 周**，把 App 从 React Native 重写为 Swift + Kotlin，300+ 屏幕，含主屏/锁屏小组件、Apple Watch App、Siri 快捷指令；**agent 写了大部分代码**。①组织：**两人一个 pod**，每个 pod 拥有一个产品区（双端都管），配对大半天，**每人同时指挥多个 agent**；agent 夜间与周末继续干活，早晨面对一队待评审 PR。②**"No vibe coding"**——护栏要回答三问：符合架构吗？行为和现有 app 一致吗？人能不能不逐行读 diff 就看懂意图。③**护栏要活在工作流里，不只是文档里**："A document explains why the rule exists; CI decides whether the rule was followed."④**agent 当第一评审**：每个 PR 先做对抗性评审，明显问题在人类评审前修掉；**PR 是小检查点而不是整屏**，一个 PR 同时含双端，人可以左右对比而不是隔几天看两遍。⑤**每天有 agent 汇总当天全部评审意见，更新 skills 与 Architecture.md**——一次评论变成此后每个 PR 的规则。⑥**瓶颈逐次搬家**：笔记本算力（自建远程开发环境给 agent）→ 代码评审 → 合并 → 协作。⑦**Jevons 悖论**：写代码不再稀缺，稀缺的是"决定该有哪些代码"以及把它安全送进产品。⑧每拆掉一个瓶颈，下一个立刻露出来。 |
| S2 | Migrating Shop app from React Native to native | 2026-09-10 | https://shopify.engineering/shop-app-migration | 计划**验收与内容哈希绑定**：改一个字节，之前的验收即失效。 |
| S3 | Helix: the internal tool powering the native migration | 2026-09-21 | https://shopify.engineering/helix | 工程师指向一个屏幕，Helix 读 RN 代码并给出一串**小而有序的检查点**，逐个证明行为（测试 + 与 RN 老 app 对拍）。 |
| S4 | We gave AI agents a mobile dev environment | 2026-10-22 | https://shopify.engineering/remote-dev | 远程开发环境给每个 agent 会话一个独立环境（可并行跑模拟器）；River agent 能实现改动、构建、跑测试、操控模拟器、收截图、开 PR，失败自己看日志修再试。**合并的移动端 PR 里 agent 占比从 6% 涨到 61%**；还有每 15 分钟跑一次的崩溃自愈循环。 |

## A 级（四）：Uber — 确定性的部分交给确定性工具

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| U1 | Using AI to Delete Code: Agentic Tech Debt Cleanup at Uber | 2026-10-20 | https://www.uber.com/us/en/blog/ai-code-cleanup/ | AutoClean：接入 feature flag 系统 → 找陈旧 flag → 改代码 → 修 CI → 验证 diff → 送人评审。①**关键设计选择**："AutoClean 是个 agentic 系统，但这不意味着 agent 该处理每一步"——布尔代数与条件简化交给确定性的 PolyglotPiranha，**尽量把确定性留在回路里**。②**CI 是唯一真相源**：单次清理会波及整个 monorepo，本地绿不代表全仓绿。③**修复分两层**：便宜的确定性 fixer 先跑（删无用默认值、清 lint 错误），不认识的往下传；难判断的（测试该删还是该改）才给 agent。④**每个 fixer 权限被严格收窄**：测试 fixer 只准改测试文件——否则 agent 会通过改生产代码让失败测试变绿。⑤**CodeCourt**：把观察到的失败模式写成显式属性（No additions / Preserves semantics / No intent drift / No agent artifacts），**一条属性一个 reviewer agent，全部并行跑，全过才给人看**；早期用单个 agent 端到端审，效果不如聚焦子 agent。⑥成果：累计清理 **16,000+ 个 flag、100 万+ 行代码**。 |

## A 级（五）：Google — 上下文要挑，验收要测

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| G1 | Agent Distraction | 2026-11-06 | https://developers.googleblog.com/agent-distraction/ | 跨数千工程师、**上亿次 agent step** 的分布式 trace 分析，用 inline `TODO(bug/...)` 注释当代理指标。①**13% 的会话**被这类注释暴露；agent 在 94% 的情况下忽略它们，但**6% 会触发二次动作，其中 83% 完全不是人要求的**。②两种失败：**41% 去追已经关闭的死单**，**57% 触发范围蔓延**（工单还开着，agent 就去查/去改）。③**单次会话的代价：多 70% 步数、多 77% token、多 105% 等待时间**（控制开发者、代码复杂度、任务类型、模型档位、读取文件数、提示长度等，p<0.0001）。④对策：写 agent 去清掉陈旧引用——但要能确认 TODO 是否 load-bearing（查 bug 历史、文件历史、跨年代码变更），**6 个月清理数千条，人工接受率 >95%**。⑤结论句："被遗忘的代码角落现在对 agent 收的税比以往任何时候都重。" |
| G2 | The Anatomy of Harness Engineering | 2026-09-09 | https://developers.googleblog.com/the-anatomy-of-harness-engineering-how-to-evaluate-iterate-and-guard-ai-coding-agents/ | **行为评估像集成测试**：不测"多文件重构是否完成"，而测离散可观察行为——提示欠明确时会不会先澄清而不是猜；改构建文件前会不会先跑 validator；生成文档时会不会给仓库内的规范链接。 |
| G3 | Hill-Climbing Agent Quality with Agents CLI Evaluation | 2026-10-28 | https://developers.googleblog.com/hill-climbing-agent-quality-with-agents-cli-evaluation/ | **更多 eval 不等于更多修复**：有 agents-cli 的 agent 跑 4 倍数量的 eval，但"改了 agent"的频率和基线几乎一样。收益来自**把 eval 结果落进构建产物**，不是来自多跑几遍。 |
| G4 | Lessons from building Sashiko, an agentic code review system | 2026-11-18 | https://cloud.google.com/blog/products/application-development/lessons-from-building-sashiko-an-agentic-code-review-system | Linux 内核的 agentic code review（Google AI & Infrastructure 团队，已捐给 Linux Foundation）。①**每天约 1200 次评审**、75+ 邮件列表订阅；被引用 **2000+ 条主线提交**、**500+ 个 2026 年 CVE**。②**60 天内返修率从 3.4% 降到 2.2%（−35%）**，30 天返修率 2.3%→1.4%。③**对照数据最硬**：干净通过（Sashiko 无警告）的提交 60 天返修率 **0.9%**；带着关键警告仍然合并的 **7.6%**（8 倍，控 patch 大小后仍 6.3 倍）。④三条经验：**benchmark 驱动**（用近 1000 个真实内核 bug 建评测集，Gemini 4 Carbon 高思考档能抓住人审漏掉的 **75.8%**）；**coding agent 不擅长审自己的代码**（在大型代码库里"能跑通"只是 5%–10% 的工作量）；开放共享建立信任。⑤Linus Torvalds 表态："说 Sashiko 都是 AI slop 的人，是在否认当前现状。" |
| G5 | Agents are sessions, not requests（K8s 节点池按 agent 会话规划） | 2026-11-16 | https://developers.googleblog.com/en/agents-are-sessions-not-requests-size-gke-node-pools-for-ai-agent-sessions/ | **agent 会话约 80% 时间在等用户**（2026 年 7 月 agent trace 研究）；一次 turn 平均约 **6.5 分钟** agent 工作时间；按每小时 2 次提示、8 小时工作日算，**agent 只工作 22% 的白天**——所以别按"请求"规划算力，要按"会话"规划。 |
| G6 | How to Build Durable Agentic Systems with Google Antigravity | 2026-11-18 | https://cloud.google.com/blog/topics/developers-practitioners/how-to-build-durable-agentic-systems-with-google-antigravity-from-instructions-to-loops | "从手工劳动 → 委派 → 编排"是人类追逐最高杠杆的自然路径；2026 年初对开源项目的统计：coding agent 采纳率已达 **22%–29%**（128,000+ 活跃仓库）；**注意力成为新瓶颈**，编排的价值在于让工作不中断地继续。 |
| G7 | Evaluate agent skills before they bloat your context window | 2026-11-03 | https://cloud.google.com/blog/topics/developers-practitioners/evaluate-agent-skills-before-they-bloat-your-context-window | skill 要**评测**而不是假定有益（引 2026 预印本：SkillsBench / SWE-Skills-Bench 上 307 个确认的 skill 诱发失败 = 125 个功能性失败 + 182 个效率退化；注意这是"被归因到 skill 的失败对"，不是普遍失败率）。 |

## A 级（六）：GitHub — 40% 的 PR 从 agent 起草，评审队列却变长

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| H1 | Octoverse 2026 | 2026-10-28 | https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/ | 过去 12 个月 **179 亿次 push**（超过 2024+2025 之和）、**343 亿次 commit**（两年前 3 倍多）、**合并 PR 13 亿**。①今年新建仓库中，**带 agent 配置文件（agent config file）的仓库平均 commit 数是没有的 8 倍**。②**9 月 40%+ 的 PR 由 agent 起头**（3 月 17%），9 月单月 1.1 亿个；agent 参与的 PR **87% 改多个文件**（非 agent 组 79%）；两周内合并率 90% vs 86%。③**61% 的 Copilot 月活用户同时用多个模型**（4 个月前 50%）——模型选择快过工具。④Copilot 月活 **55% 用 agentic 功能**（一年前 35%），cloud agent **+230% YoY**（agent chat +85%）。⑤stacked PR 预览 7-30 上线，到 9 月 **26.4 万开发者**用过。 |
| H2 | Beyond code generation: A developer's guide to agentic engineering | 2026-11-06 | https://github.blog/ai-and-ml/github-copilot/beyond-code-generation-a-developers-guide-to-agentic-engineering/ | 10 月单周 **12 亿+ commit**（比一年前 +400%，比 2025 全年还多），然后问："你觉得自己 productivity 涨了 400% 吗？"引 Faros AI 研究：**团队从低 AI 采纳走向高采纳时，PR 在评审队列里多花 441% 的时间**。给出 Plan / Build / Verify / Observe 四段工作流；Verify 段建议堆叠小 PR、Code Quality 自动检查、Copilot code review 按复杂度调深度。 |

## A 级（七）：OpenAI — 把 agent 编排成一条可追责的流水线

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| O1 | How OpenAI's Performance Factory keeps ChatGPT fast | 2026-11-19 | https://openai.com/index/how-openai-performance-factory-keeps-chatgpt-fast/ | ①四个部件：可配置工作流的 task service、派活循环 dispatch loop、云端跑 Codex 的 API、订阅式唤醒（GitHub review 评论、部署完成）。②第一个工作流 Regression Workflow：性能告警 → agent 调查 → 提修复 → 人审 → 部署 → agent 验证是否恢复；**三个多月 1700+ 次调查、600+ 根因，平均每天 17 次**。③**对抗性评审**：另一个 Codex 会话专门试图推翻诊断；100 条根因建议人工评 **70% 准确**。④**对修复也做对抗评审**（有些修复过于复杂或引入新问题，加缓存可能引入陈旧数据）。⑤**skill `perf-forensics`** 配历史回归做 eval，单次运行就能给诊断。⑥**agent 每天扫日志找工具失败与权限问题自修复**。⑦**状态存在 agent 上下文之外**，人和 agent 能接力。 |
| O2 | Scaling Git at OpenAI | 2026-11-02 | https://openai.com/index/scaling-git-at-openai | Pando（新的源码管理组件）**用 Codex 从立项到生产 10 周**：核心设计由 1 名工程师定，agent 团队实现。①写 **conformance test suite** 让 agent 能拿标准 Git 行为对照测试；②写**确定性模拟测试**查竞态与不变量；③用 GPT-6 Astra 让 agent **写 Lean 和 TLA+ 形式化"Pando 理论"**，用来找 bug 并证明性质；④连续 session 跑几百小时找边界情况；⑤建 skills 帮 agent 准备 checkout、引导迁移。 |
| O3 | Inside the Codex sandbox | 2026-11-18 | https://openai.com/index/inside-the-codex-sandbox | 权限模型：命名 profile（`:workspace` 可写工作区、`.git`/`.codex` 只读、默认禁网）、按命令覆盖（`with_additional_permissions` / `require_escalated`）、分层配置 + `requirements.toml` 由企业管理员收口。原文金句可用于"边界靠系统不靠嘴":**"模型不该被要求去记住一条系统本来就能低成本执行的规则"**（这条出自阿里云对 Anthropic 的引述，见 H2 区）。 |
| O4 | Introducing the Agents API | 2026-09-10 | https://openai.com/index/introducing-the-agents-api/ | Agents API 底座是**开源的 Codex harness**，模型调用/工具/上下文的调度逻辑公开可查。 |
| O5 | Asana 客户案例 | 2026-08-18 | https://openai.com/index/asana/ | 移除废弃测试框架 Enzyme（原估 5 年、600 万美元人力）：**5 句话提示起步，最多 4 个 agent 并行、各自在独立代码库副本干活，一名工程师每天查两次进度并逐项审**；实际 2 个日历周、1.5 周工程投入，**模型+基础设施成本约 1.2 万美元**。原话："简单的指示比精心设计的复杂设定更有效"。 |
| O6 | CodeRabbit 客户案例 | 2026-11-09 | https://openai.com/zh-Hans-CN/index/coderabbit-codex-daybreak/ | 6 个月不增员、交付量提到约 20 倍；30 天提交 2500–3000 PR；"**不得不彻底重新思考整个软件交付流程**"——瓶颈转到笔记本内存算力、测试、编译打包、依赖。 |
| O7 | iFood 客户案例 | 2026-11-24 | https://openai.com/zh-Hans-CN/business/customer-stories/ifood/ | 15,000+ 仓库；**平台完成 25,000+ 任务、消耗 270 亿+ token、平均每次运行 0.04 美元**；流程两端是确定性步骤（克隆、装技能、建分支 → 发 MR）中间是 agent 执行；用**结构化输出**保证每次会话都返回符合 schema 的结果（无论成功失败）；修复准确率与已解决漏洞数**翻倍**。 |
| O8 | Revolut 客户案例 | 2026-11-16 | https://openai.com/zh-Hans-CN/business/customer-stories/revolut/ | 编码时间缩短 **30–60%**；一人拆功能、分别派给多个 agent，独自搭起内部代码审查服务；**只用一天把七年积累的设计文档转成 AI 可读上下文**；"下放执行权，不下放责任"——"每位开发者都要对自己产出的代码负责，我们不会盲目信任 AI"。 |
| O9 | cult.fit 客户案例 | 2026-11-05 | https://openai.com/zh-Hans-CN/index/cultfit-builds-with-codex/ | 统一到单一平台后，仓库结构、技能、测试、评审、反馈闭环都按同一套规范；社交动态功能从"过去一年多"压到 **2 个月**；非工程团队几个月内做 20+ 内部应用；周末重写内部看板，**每年省 10 万美元**软件费。 |
| O10 | Ultrafast 故障排查 | 2026-10-26 | https://openai.com/index/openai-cut-incident-investigation/ | 排查从数小时到几分钟；原话："**以前，我让 Codex 调查一个问题时，自己也会同时去查，因为我知道它不够快**"；以及"写代码的成本很低，现在速度也非常快。过去代价高昂的重构，如今几乎瞬间就能完成"。 |

## A 级（八）：Anthropic — 岗位、人和记忆

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| N1 | Working with AI（66 场访谈 / 58 家企业客户） | 2026-11-23 | https://www.anthropic.com/research/working-with-ai | ①**价值多来自"增加产出"而非"削减成本"**：近 300 个 AI 应用里，多数是提升产出，一半来自加速/扩展既有工作，另一半来自产品质量改进或新产品。②**就业**：只有 **2 家**因 AI 自动化彻底消灭一个岗位并导致失业；**10 家**因 AI 增加招聘；但**2/3 的公司因 AI 减少招聘**（"我们可能不裁人，但我们不招人"），其中 1/3 是自然减员不回补，其余是本来要扩的规模不扩了；**9 家砍掉了外包**（软件外包、客服、法务、后职能，多为已离岸的）；还有 **1/10** 的用例里价值被员工自己拿走（活儿变轻松）。③**瓶颈**：编码提速后，**评审、销售、战略决策**必须跟上；还有"专家抵制部署"和"被监控的恐慌"（"你希望工作对经理可读；现在你希望工作对**经理用的那些 agent** 可读"）。④**自下而上**：非技术领域专家收益最高（会计师把 80 小时的 401(k) 审计做成应用、机场运营、化工厂 QA 主管）；但零散自建工具"维护成本上去、总体收益有限"。⑤**自上而下**：脆弱、易过时（"三个月就过时"、"像朝一个旋转的飞镖盘扔飞镖"）；专家被要求"造自己的棺材"；被替代的人不配合（"能审双倍案例，怎么激励他审双倍？"），最后 agent 被搁置。⑥**最佳解是"围绕 AI 重新组织"**：拓宽岗位（一个人端到端负责一条工作流）、把人 redeploy 到 AI 做不了的瓶颈任务。⑦**初级律师的新工作法**（全文最适合当"岗位怎么变"的画面）：AI 写初稿后不再需要律师写初稿，但"如果不写，初级律师怎么知道这是好草稿还是坏草稿？"——于是改成初级律师必须和资深律师一起逐句改 AI 初稿。 |

| N2 | Patterns and problems in emerging multiagent systems | 2026-08-13 | https://www.anthropic.com/research/multiagent-systems | ①**协作群 vs 独立并行**：45 个 agent + 共享论坛找漏洞，swarm 在 2700 万 token 里找到 **266 个**，独立并行在 650 万 token 里找到 **21 个**；但限定到核心目录后两者"每个漏洞的 token 性价比相当"，两种方法**互补**（只重叠 12 个）。②**做游戏实验（12 小时）**：早期模型互相冲突导致 PR 大量废弃；新模型（Opus 4.8 / Mythos Preview）靠"几乎不合作"——各自独占文件——解决了冲突；只有 **Sonnet 5** 能既共享代码又保持高 PR 合入率。③**三种 prompt（自由组队 / 规定角色 / CEO 层级）差别不大**；结论：**模型的品味很差，仍然需要大量人工指挥**。④多 agent 把人类的失败模式照搬（conformity 从众），同时产生新的系统性失败。 |
| N3 | The components of agent memory | 2026-11-06 | https://www.anthropic.com/research/components-of-agent-memory | ①Claude 会写"记忆笔记"；CL-Bench 上 **Opus 5 是第一个闭环**的模型（把验证过的规则连同"怎么知道它是真的"一起写下来）。②**给自由比给规则更有效**："只记录失败"这条规则反而削弱了 Opus 5 / 4.7 的记忆增益；给"记住什么"的固定规则在强模型上会掉分。③Claude Code 的自动记忆**只注入 MEMORY.md 前 200 行或 25KB**，当索引用；④"更长的指令文件会降低遵从度"——顶层记忆必须小。 |
| N4 | Donating Agent Skills to the Agentic AI Foundation | 2026-10-22 | https://www.anthropic.com/news/donating-agent-skills-to-the-agentic-ai-foundation | Agent Skills 已是开放标准（2025-12 发布），**70+ 平台已集成**（ChatGPT、Cursor、Copilot、VS Code），**100 万个 skill 发布、近 2.8 亿次安装**；标准捐给 Linux Foundation 下的 AAIF（Anthropic 与 Block、OpenAI 共同发起）。 |

## A 级（九）：中文大厂

| # | 文章 | 时间 | 链接 | 可引用的核心内容 |
|---|---|---|---|---|
| C1 | 美团《如何在"不能出错"的系统里使用 AI Coding？分布式存储实践与边界》 | 2026-10-29 | https://tech.meituan.com/2026/10/29/AI-Coding-IN-Distributed-Storage-System.html | **（与站内《前端岗位的消失论》A2 同源，正文若已用过需换角度引用）**①三句结论："AI 把瓶颈从'写'移到了'验证'"、"AI 的错误不在代码里，而在代码之外"、"流畅不是证据，一致不是正确，变绿不是解决"。②**四层证据表**：静态推理（代码里有没有这条路径）/ 构建+单测（给定输入下是否真出错）/ 集成测试（真实交互与已有保护下是否仍可达）/ 运行时日志（线上是否真的发生、频率幅值）——每层各自**能回答什么、回答不了什么**。③硬数据：全仓评审 **117 个疑似问题 → 36 条红测试确认 / 3 条被证伪 / 41 条源码确认 / 37 条未验证**；**11 天 67.8 万行 WARN 日志 → 5 个缺陷全部属实、零误报**。④**误报三大类**：代码可达 ≠ 运维可达（"EPOCH_NOT_MATCH 理论上走不到这个分支"）；把有意为之当缺陷（故意 abort 而不记日志）；**AI 给的修复建议本身要审**（32 位溢出的校验在下游被截断成负数，会静默失效）。⑤**"不要用多 Agent 投票代替正确性判断"**——多个 agent 读同一份 diff，缺的是同一份背景，盲区共享，票数是重合度不是正确度。⑥**"审的是 checkout 出来的代码，不是 PR 网页"**（网页 diff 只显示约 2% 真实改动）。⑦上下文要**给稳定的不变式，而不是全部文档**——喂过时文档会把 AI 带偏；每轮评审后要补的是"**哪些上下文缺失让 AI 理解错了**"，而不是把发现的问题堆进 AGENTS.md。⑧分层授权：只读分析 → 受控修改 → 受控执行 → 人工决策。⑨AI Debug 只能当"假设生成器"，根因认定必须由人做。 |
| C2 | 阿里云 CTO 线：7 个样板间，探索 AI 原生研发组织（InfoQ） | 2026-10-19 | https://www.infoq.cn/article/2uG3W14THqtLhb5Vou51 | ①范式：**模型 + Harness + Context**——模型负责理解判断与实时决策，Context 提供统一、持续更新的上下文，Harness 负责自主运行与持续进化。②三阶段：**工具原生 → 工作流原生 → 组织原生**；"Agent 进入生产链路，才是真正的分水岭"。③推进方式"**北极星、留白、沙箱**"（留白=允许跨岗位边界创新；沙箱=控制对主干的影响）；观测指标不进考核。④硬数据：某项目全链路处理时长 **2 小时 → 5 分钟**；某项目两周完成几十个需求、发布周期 **40 天 → 2 天**、产出十几个生产级 Skill。⑤**Kitta**（代码评审 agent）：六大领域 **17%–30%** 审查质量提升；ANCK 内核累计审查 **7 万+ 补丁**，**门禁准确率 97%、代码合入率 62%**。⑥云通信：数字分身流水线 7×24 跑 4 条业务线，单分身并行 **3–4 个需求**，简单需求约 **2/3 端到端自闭环**。⑦Agentic SOC：需求平均周期 **50.9 天 → 13.8 天**，窗口内吞吐率 **63.9% → 98.9%**；人要先设定**目标、质量、权限、停止条件**四类边界。⑧自己承认的坑：急着上模型、低估领域黑话与历史知识复杂度、被上下文幻觉影响判断。 |
| C3 | 阿里云 AI Agent Handbook（68 页白皮书解读） | 2026-10-23 | https://developer.aliyun.com/article/1774447 | ①"**Agent = Model + Harness**"：模型能力只有经过上下文组织、任务循环、状态管理、工具执行、权限控制与结果验证，才可能稳定转化为任务结果。②**编码只占研发生命周期约 20%–30%**。③"**智能面积**"：横轴通用智能（Memory/Planner/Managed Runtime/Agent 协作，模型公司在投，企业别重复造）、纵轴业务深度（业务事实、语义、流程规则、行业经验，企业自己的护城河）。④**上下文资产五类**：Skill（方法）、MCP（接口）、SPEC（约束）、README 与 runbook（入口与排障）、模板与 checklist（评审发布回滚）。⑤引用 **Anthropic 2026 年对约 40 万次 Claude Code 交互式会话的分析：用户平均承担约 70% 的规划决策，Agent 承担约 80% 的执行决策**。⑥MCP 解决"模型怎么调工具"，**不天然解决"模型知不知道该操作哪个对象"**。⑦Agent 特别擅长调 CLI，但**没有主动发现 CLI 的机制**，所以 CLI 得配 Skill 教它什么时候用。 |
| C4 | 阿里云《从"能跑"到"敢用"：Agent 工程化的四个关键控制面》 | 2026-11-05 | https://developer.aliyun.com/article/1779328 | 四个控制面：**评测 / Harness / Skill / 调度**。①评测分 Result / Trajectory / Efficiency / Risk 四层；两个 agent 终态都"对"，一个稳定收敛一个靠暴力采样命中，Result 层分不出来、Trajectory 层天差地别。②Rubric 二元化（把"口语化 0–10 分"下钻成一组二值断言，各断言算 Cohen's κ）——Beam 业务人人一致率 62%→92%，数字站长人机一致率 99%。③**Trace 先于评测**，日志兼容 OpenTelemetry，作为上线硬前提。④六套 harness 对比（Claude Code / OpenCode / Codex / DSH / Pi / Hermes）：权限放哪层、压缩什么时候触发、循环何时结束、人能不能中途插话；共识"**Agent = LLM + Harness**"，问题根因往往不在模型而在运行时有没有对应控制手段。 |
| C5 | 美团企业级 Agent 平台化实践（QCon 上海，InfoQ） | 2026-10-21 | https://www.infoq.cn/article/BQJltkL1FJ9AG3cMeUmB | 一句话可用：**确定性逻辑交给代码，不确定性判断交给模型**。AgentOS：无状态 Agent Loop、分布式 Session、短周期沙箱、云端存储；Skill/MCP/CLI/知识库/记忆为能力底座；Trace、评测、告警、成本、版本、回滚构成治理闭环。 |
| C6 | 企业 AI Native 研发流程升级与重塑（InfoQ） | 2026-11-16 | https://www.infoq.cn/article/4z7Bbxy92tjAI7MB5evM | ①**四级成熟度**：基础 AI 辅助 → agent 作为个人工具 → **团队级 software engineering 级别的 Harness**（第三级是转折点）→ 组织 AI native。②**人在 loop 之内 vs 人在 loop 之上**：把 agent 塞进旧流程、或人和 agent 都困在 loop 里，改善都有限；"真正高质量的做法是让人站到工作 loop 之上"。③"**过去被旁路的文档、规范、流程，现在成为必须项**——Agent 接收的输入说白了就是你的文档"；"code is cheap，甚至可以不看代码，show me your SPEC"。④SPEC 要三重闭环：需求澄清完整 / 实现路径讲清但不写成伪代码 / **验收规则精确**（测试覆盖、错误处理、边界、禁止事项）。⑤**Agent 之间协作靠另一个 Agent 审查**（自己审自己的东西很难发现真问题）。⑥高德四层知识：代码 → 工程术语 → 业务知识 → **质量门禁与常见问题**（上次犯过的错不写进门禁，模型下次还会犯）；内部 coding benchmark：**通用领域 one-shot 成功率可达 90%，专业领域明显下降**。 |
| C7 | 华为《Vibe Coding 最后一公里：生产级 Coding Agent 效果调优实录》 | 2026-09-30 | https://juejin.cn/post/7690879433230352419 | ①**两个极端**：严格引导（步骤分支校验点全写死，上限被锁死、维护昂贵）vs 完全不引导（上限高但不可复现、长任务跑飞）；**生产级要中间路线——"给地图，给引导，但不锁死路线"**。②可落地手段：`system reminder` 周期提醒目标边界状态、`/goal` 明确目标输出约束、注意力机制维持当前关键任务。③工具三性：易用（参数少且自解释）、可用（权限凭据就绪、失败有降级）、鲁棒（幂等、副作用可回滚）。④可观测性三方向：E2E 全流程透明 / 海量轨迹分析 / 开放 OpenAPI 让 agent 自己调观测平台。⑤**评测既看结果也看过程**：`deterministic(outcome) + non-deterministic(trajectory)`；`pass@1` 与 `pass^k` 区别（k 增大时前者趋近 100%、后者趋近 0）。⑥**SDD 与 TDD 的分工**：SDD 是意图契约（但不消灭不确定性，只把它挪到自然语言，且 spec 容易腐化、很少有人认真看 agent 生成的 spec）；TDD 是终态定义（模型不会拒绝写测试）。⑦**"Spec 当地图，Test 当存档，路径交给 Agent"**；"绿了，才算交付"。 |

## B 级：可作对照/补充（非大厂官方或媒体访谈）

| # | 文章 | 时间 | 链接 | 要点 |
|---|---|---|---|---|
| B1 | Zalando：Agentic Engineering snapshot | 2026-08-13 | https://engineering.zalando.com/posts/2026/08/agentic-engineering-at-zalando-a-snapshot.html | 风险级 PR 审批 bot：**33% 的 PR 判为低风险并自动批准，PR lead time 降低 20–40%**；规则由生产事故与典型故障驱动（破坏向后兼容 = 中风险，破坏配置的笔误 = 高风险）；副作用：工程师会主动把改动拆成低风险以加快合并。 |
| B2 | Runway：Building a Software Factory | 2026-11-20 | https://runway.com/news/engineering/building-a-software-factory | 云端 agent 驱动的合并 PR 占比从 6 月的 0.1% 涨到 10 月的 **38%**；首个审批等待中位数 **2.3 小时 → 5 分钟**；AI 单独批准的 PR 回滚率 **0.10%**，人批约 1/200；9–10 月 AI 批的 977 个 PR 里人反对 **15 个（1.5%）**；AI 评审评论 **93%** 首轮被解决或引发改动；工程师的新职责四件事：**找 agent 在哪儿浪费力气、清掉阻塞、把路径改造成 agent-friendly、保持度量诚实**。 |
| B3 | Adyen：AI in our development lifecycle | 2026-09-03 | https://www.adyen.com/knowledge-hub/ai-in-our-development-lifecycle | AI 采纳近 100%；人均 MR **+48%**；自报省时 15%（≈2x token 回报）；把 2000+ 生产 job 从单体镜像拆成 40+ 按卡组织分的镜像，**两个工程师 2 个月零事故**（原估 6–12 个月多团队参与）。 |
| B4 | Spotify：What we've learned scaling AI coding agents | 2026-08-10 | https://portal.spotify.com/blog/introducing-xirp | **熵**：PR 变多，但返工、不一致、token 浪费同步上升；不同 session 的 agent 反复重新发现别的 session 已经解决过的事。 |
| B5 | Salesforce：How Salesforce scaled engineering AI adoption | 2026-11-10 | https://engineering.salesforce.com/how-salesforce-scaled-engineering-ai-adoption-without-stifling-innovation/ | 用 SDLC + DORA 指标选能力而不是拍脑袋；采纳近 100% 后：吞吐 **+26%**、inner-loop **+32%**，周期 **22 天 → 11 天**，Sprint Forecast 66%→90%，可维护性分维持 6.04。 |
| B6 | Miro：Building Miro's Software Factory | 2026-10-20 | https://miro.com/articles/engineering/building-miro-software-factory/ | 同类"软件工厂"叙事，可作交叉引用。 |
| B7 | Augment：Beyond AI Coding Agents — Software Factory | 2026-09-11 | https://www.augmentcode.com/blog/beyond-ai-coding-agents-how-we-built-augments-software-factory | 2025-11 → 2026-07：size-adjusted output/开发者 12.3→**55.7（4.5×）**；PR/开发者 16.6→45.5；代码行/开发者 8031→35147；**中位 merge 时间 11.2h → 3.1h（−72%）**；**14 天 revert 率 1.9% → 0.4%（−79%）**；结论"**跟着瓶颈走，而不是按生命周期顺序自动化**"。 |
| B8 | Kong：How Kong built an Agentic Engineering Platform | 2026-10-16 | https://konghq.com/blog/engineering/agentic-engineering-platform | 早期测量：评审成本中位数 $3.93 → $2.47（约 −37%）。 |
| B9 | Adaptive：Coding agents at Adaptive | 2026-11-08 | https://build.adaptivesecurity.com/blog/coding-agents-at-adaptive/ | agent 审批开始后两周（10-19 ~ 11-01），周合并 PR 约为前八周均值的 **2.2 倍**。 |
| B10 | InfoQ：Agent Harness 技术研讨会预告 / AiDD 北京站议程 | 2026-07-29 ~ 11-23 | https://www.keylinking.com/gywm/3690.html · https://www.zhidx.com/p/613243.html | 需求智能体 → Spec/SDD → Coding Agent/Agent Team → ATDD 与门禁 → 轨迹回流的完整链路；可作"行业共识"佐证。 |

## A+ 级：论文（用于给"共识"提供学术侧支撑，引用须注明是论文而非厂商观点）

| # | 论文 | 时间 | 链接 | 要点 |
|---|---|---|---|---|
| P1 | Spec-Driven Development for Agentic Software Engineering: Harnessing Human–Agent Teamwork | 2026-08-31 | https://arxiv.org/html/2609.00252 | SDD 作为"人与 agent 之间的契约基底"；把 harness 分为**技术 harness**（agent 周边的工具/上下文/权限）与**方法 harness**（团队周边的流程）；提出五种人机交互模式。作者自陈证据基础尚不成熟，是"迈向产学共识的第一步"。 |
| P2 | Spec-Driven Development as Prescribed and as Practiced | 2026-08-25 | https://arxiv.org/html/2608.25202 | 21 位从业者（含 8 位工具厂商）访谈 + 73,030 个仓库、470,795 个 spec 文件的语料（SpecMine）。发现：spec 会**腐化**；实现细节有时帮 agent、有时加速腐化；spec–code 一致性检查多在"改完时"才做；**个人收益多来自"委派前把意图说清楚"，团队收益取决于 SDD 是否成为共享流程**。 |
| P3 | Anthropic 上下文工程（中文精译） | 2026-09-29 | https://guobug.github.io/posts/2026/09/29/effective-context-engineering-for-ai-agents/ | C 级转译，仅作线索：上下文工程 = 在推理过程中精选并维护**最小有效高信噪比 token 集**；提示词要"合适高度"（既不写死 if-else 也不空泛）；工具设计要独立封装、边界清晰、少而精；**just-in-time 检索**替代全量灌入；长任务三件套（compaction / 结构化外部笔记 / 子 agent）。**引用原文前需回 Anthropic 官网核对（C 级不引数字）**。 |

---

## 需要补齐的素材（写作前再查）

1. **DORA《ROI of AI-assisted software development》报告原文**（Google Cloud 2026 年发布，被 Atlassian 与 Google 引用）——需要里面的原始口径与图表。
2. **GitHub Spec Kit / AWS Kiro** 官方文档——工具侧的"spec 先行"证据链，目前只有二手转述（巨蝌蚪等）。
3. **Shopify Helix 细节**（检查点如何定义、人类怎么验收）——S3 只拿到摘要。
4. Anthropic 官方《Effective context engineering for AI agents》原文页（N3 类只拿到二手精译）。
5. 若要写"个人怎么练"，需要 1–2 个**中文个人工作流**的公开实践（不是厂商稿）作对照。

## 素材使用注意（写作纪律）

- **厂商自报数据必须标口径**："官方博客披露""内部测量"要写出来，不能当第三方结论。
- **不要把四件套写成"四件套"**——四篇大厂文章是四个独立团队的独立实践，结论一致不等于有统一标准，正文要点明这一点。
- **数字要挑**：每节留 2–4 个最有冲击力的数字即可，全部塞进附录表。同一节里堆 8 个数字会没人记得住。
- **别把"AI 参与 PR 的比例"当"生产力"**——Atlassian 与 GitHub 两篇正好互相印证这件事（100% vs 10%；40% 起草 vs 评审排队 +441%）。
