---
title: '代码快了 4 倍，团队只快了 10%：大厂怎么驾驭 AI'
date: 2026-11-25 10:30:00
categories: [AI]
tags: [AI, AI Coding, 大模型, 开发流程, 工程效率, 团队协作]
description: 'GitHub 单周 commit 涨 400%，Atlassian 团队吞吐只涨 10%。Meta、Shopify、Uber、Google 各自的做法，最后都落在验收证据、上下文分级和风险授权上。'
translation_key: agent-direction-workflow
lang: zh
ai_written: true
image: /dist/img/cover-agent-direction-workflow.png
---

10 月单周，GitHub 上出现了超过 12 亿次 commit，比一年前涨 400%，比 2025 一整年还多。

同一个月，Atlassian 内部 6000 名工程师跑完 100 万次以上 agent session，AI 参与的 PR 接近 100%——团队吞吐提升卡在 10% 左右。同一篇复盘里还引用了 Faros AI 的一项研究：团队从低 AI 采纳走向高采纳，PR 在评审队列里多花 441% 的时间。

写代码的速度翻了几倍，团队整体的产出几乎没动。

我把 2026 下半年大厂自己写的工程博客翻了一遍：Meta、Shopify、Uber、Google、GitHub、OpenAI、Anthropic，加上美团、阿里、华为的中文实践。这些互不认识的技术团队，解法撞到了一块，动的是流程里几件没人写下来的事——喂什么上下文进模型、怎么判定一个任务做完、哪些改动可以不看、长任务的状态放哪。

模型一样，工具一样，为什么有人提速，有人只是更忙？

## 一、人从环里挪到环上

Meta 工程博客 10 月 15 日那篇《[How Meta Built Forum With AI-Native Engineering](https://engineering.fb.com/2026/10/15/ml-applications/how-meta-built-forum-ai-native-engineering/)》讲他们怎么用一支小团队从零做出 Forum（Facebook Groups 的独立 App），8 周做到与 Facebook Groups 的核心功能对齐。

Meta 的分工表述可以直接搬：工程师驱动每一步、AI 在每一步里辅助，这叫 human-in-the-loop；agent 自己跑「计划 → 实现 → 构建 → 测试 → 纠正 → 重试」的循环，人定目标、看运行、跑偏时介入、最后签字，这叫 human-on-the-loop。

Meta 说后者是目标，不是既成事实——有些阶段仍然要人盯着每一轮。挪位置要付代价，这点他们没绕过去。

阿里云 11 月 16 日那篇《[企业 AI Native 研发流程升级与重塑](https://www.infoq.cn/article/4z7Bbxy92tjAI7MB5evM)》换了一套措辞：人在 loop 之内，还是人在 loop 之上。把 agent 塞进旧流程里，或者人和 agent 都困在同一个环里，改善都有限。

分工比例有数字。阿里云 10 月 23 日那本 AI Agent Handbook 里引用了 Anthropic 对约 40 万次 Claude Code 交互式会话的分析：**人平均承担约 70% 的规划决策，agent 承担约 80% 的执行决策**。

Shopify 的做法更具体。他们 11 月 10 日发布《[How we rebuilt the Shopify app in 12 weeks](https://shopify.engineering/shopify-app-rebuild)》，30 名工程师 12 周把 App 从 React Native 重写成 Swift + Kotlin，300 多个屏幕，agent 写了大部分代码。组织方式是两人一个 pod，每人同时指挥多个 agent，agent 夜间和周末继续干活，早晨人面对一队待评审的 PR。

Shopify 那篇里我最认同的一句是 "No vibe coding"。他们给 agent 的护栏要回答三个问题：符合架构吗？行为和现有 app 一致吗？人能不能不逐行读 diff 就看懂意图。

第三个问题有意思。它默认人不再逐行读 diff，但要求人**看得懂意图**。判断这件事没被放弃，只是换了个人来做。

| 环节 | 环里：human-in-the-loop | 环上：human-on-the-loop |
| --- | --- | --- |
| 定目标 | 人拆到每一个具体动作 | 人给验收标准和边界，agent 自己排 |
| 写实现 | 人下指令，AI 补全 | agent 写完先自检再交上来 |
| 验证 | 人看 diff、跑测试 | 验证写成会变红的命令，红了才算完 |
| 评审 | 人逐行读 | agent 当第一审，人只看它挑出来的 |
| 放行 | 人点按钮 | 按风险分级，低风险自动批 |

把人从环里挪到环上，比放权难。Anthropic 11 月 23 日的《[Working with AI](https://www.anthropic.com/research/working-with-ai)》记录了一个很典型的翻车：某公司专家抵制部署 AI，理由是「能审双倍案例，怎么激励他审双倍？」——结果 agent 被搁在一边。

这套模式把专家从执行者变成了守门人，而守门人手里的旧激励（按写的代码量、按审的份数算）没跟着改。改不动激励，环上就只是个说法。

你现在的用法，大概率还在环里：你在给每一步派活，agent 在等你的下一条指令，瓶颈就是你手速。

## 二、上下文不是越多越好，它有权威等级

概念本身不新。Anthropic 2025 年 9 月那篇《[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)》就写清楚了：上下文是有限资源，收益递减，越多越糟；好的做法是找到「能最大化目标达成概率的最小高信噪比 token 集」。

Google 11 月 6 日那篇《[Agent Distraction](https://developers.googleblog.com/agent-distraction/)》给了一组大数。它分析了跨数千工程师、上亿次 agent step 的分布式 trace，用 `TODO(bug/...)` 注释当代理指标，测出三件事：

- 13% 的会话被这类过时注释暴露；
- 其中 6% 会触发 agent 的二次动作，而这部分里有 83% 的人根本没要求过；
- 两种典型失败：41% 去追已经关闭的死单，57% 触发范围蔓延。

代价是：单次会话多 70% 步数、多 77% token、多 105% 等待时间（控制开发者、代码复杂度、任务类型、模型档位、读取文件数、提示长度等因素后 p<0.0001）。

Google 那句结论是：被遗忘的代码角落，现在对 agent 收的税比以往任何时候都重。

这条我信。三年半前写的 `// TODO: 这里要改成新接口` 还躺在文件里，人扫一眼知道那是历史，agent 不会。它只看见一个待办。

美团 10 月 29 日那篇《[如何在"不能出错"的系统里使用 AI Coding](https://tech.meituan.com/2026/10/29/AI-Coding-IN-Distributed-Storage-System.html)》从另一个角度说了同一件事。他们的判断很直接：AI 的错误不在代码里，在代码之外；不要喂全部文档，要喂稳定的不变式，喂过时文档会把 AI 带偏。

他们把 AI 的误报归成三类：

- **代码可达 ≠ 运维可达**。理论路径存在，但线上根本走不到；
- **把有意为之当缺陷**。故意 abort 不记日志，是设计；
- **AI 给的修复建议本身也要审**。他们举的例子是 32 位溢出的校验在下游被截断成负数，会静默失效。

第三类最容易被忽略——你审的是 AI 的代码，但它还附了一份修复建议。这两样里，第二样更难发现错。

美团还有个做法我觉得可以直接抄：**每轮评审之后要补的是"哪些上下文缺失让 AI 理解错了"**。补"这次发现了什么问题"，AGENTS.md 会写成事故合集，越写越长、越来越没人看；补缺失的上下文，每轮只加一条规则。

阿里那边的做法是给上下文建资产目录。10 月 23 日那本 Handbook 把上下文资产分成五类：Skill（方法）、MCP（接口）、SPEC（约束）、README 与 runbook（入口与排障）、模板与 checklist（评审发布回滚）。11 月 16 日那篇 InfoQ 里，高德的做法是四层知识：代码 → 工程术语 → 业务知识 → **质量门禁与常见问题**。

第四层是关键：上次犯过的错不写进门禁，模型下次还会犯。他们内部 coding benchmark 的结果是，通用领域 one-shot 成功率能到 90%，专业领域明显下降；差距出在四层知识齐不齐。

还有一条来自 Anthropic 11 月 6 日的《[The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)》，实测结论跟直觉相反：**给 agent 判断的自由，比写死规则更管用**。他们试过规定 agent「只记录失败」，Opus 5 和 4.7 的记忆增益反而被削弱。同一篇里还有个工程细节：Claude Code 的自动记忆只注入 MEMORY.md 的前 200 行或 25KB，当索引用；更长的指令文件会降低遵从度。

Google Cloud 11 月 3 日那篇《[Evaluate agent skills before they bloat your context window](https://cloud.google.com/blog/topics/developers-practitioners/evaluate-agent-skills-before-they-bloat-your-context-window)》给了一组更冷的数字。它引了一份 8 月的预印本《[Agent Skills Can Be Harmful](https://arxiv.org/abs/2608.11888)》：在两个 skill 基准上，307 个确认由 skill 诱发的失败被归因到 skill，其中 125 个功能性失败、182 个效率退化。这个数字只统计「被归因到 skill 的失败对」，不是普遍失败率。它说明的是另一件事：**你加进去的每一条 skill 都在花模型的注意力预算**。

给模型上下文像给新人发入职材料：给错版本比不给更糟。不给只是慢，给错是方向错了。

## 三、"做完了"必须落在证据上

这几件里面，验收最贵，大厂在这上面花的钱也最多。

Meta 那篇 Forum 里有一句我读了好几遍的话：门槛应该设在 verification，而不是 compilation。代码能编译不算完，自动测试和 UI 视觉检查都过了才算完。agent 先自检再交人，送到人面前的是「更少但更可信」的一批。

Meta 紧接着补了一句：弱信号不会解除约束，只是把约束从写代码挪到读代码。你还是得读，只是读得少一点、值得读一点。

Uber 10 月 20 日那篇《[Using AI to Delete Code](https://www.uber.com/us/en/blog/ai-code-cleanup/)》是另一条路的样本。他们做的是 agentic 技术债清理，清理了 16000 多个 feature flag、100 多万行代码。这篇真正可抄的是它的克制：

- **AutoClean 是个 agentic 系统，不意味着 agent 该处理每一步**。布尔代数和条件简化这种确定性的活儿，交给确定性的 PolyglotPiranha。
- **CI 是唯一真相源**。本地绿不代表全仓绿，因为单次清理会波及整个 monorepo。
- **每个 fixer 的权限被严格收窄**。测试 fixer 只准改测试文件——不限的话，agent 会通过改生产代码让失败的测试变绿。这条我认为是全套材料里最实用的一条。
- **CodeCourt**：把观察到的失败模式写成显式属性（不新增、保持语义、不跑偏、不留 agent 痕迹），一条属性一个 reviewer agent，并行跑，全过才给人看。他们试过单个 agent 端到端审，效果反而不如拆成聚焦的子 agent。

Uber 的做法很直接：能确定的就别交给模型判断。这跟美团在 QCon 上海讲的那个《[企业级 Agent 平台化实践](https://www.infoq.cn/article/BQJltkL1FJ9AG3cMeUmB)》里说的「确定性逻辑交给代码，不确定性判断交给模型」是同一句。

美团那篇《[如何在"不能出错"的系统里使用 AI Coding](https://tech.meituan.com/2026/10/29/AI-Coding-IN-Distributed-Storage-System.html)》把「证据」做成了分层表，四层各自回答不同的问题：

| 证据层 | 能回答 | 回答不了 |
| --- | --- | --- |
| 静态推理 | 代码里有没有这条路径 | 运行时会不会真走到 |
| 构建 + 单测 | 给定输入下是否真出错 | 线上频率和幅值 |
| 集成测试 | 真实交互下是否仍可达 | 是否只在极端条件下发生 |
| 运行时日志 | 线上到底发没发生 | 是不是必然被触发 |

他们给的两组数据可以当参照。全仓评审 117 个疑似问题，结果是 36 条红测试确认、3 条被证伪、41 条源码确认、37 条未验证。另外 11 天 67.8 万行 WARN 日志，最后收敛出 5 个缺陷，全部属实，零误报。

那 3 个被证伪的就很典型：模型报了，人一看是误报。如果流程只到「模型说这里有问题」这一步，这 3 个就变成 3 次无意义的人工排查。**证伪也要拿证据**，这是他们那张表里没写出来的一层。

Google 那篇讲 Sashiko 的文章（11 月 18 日，《[Lessons from building Sashiko, an agentic code review system](https://cloud.google.com/blog/products/application-development/lessons-from-building-sashiko-an-agentic-code-review-system)》）给了一组对照极干净的数据。Sashiko 是给 Linux 内核做 agentic code review 的系统，每天约 1200 次评审，被引用到 2000 多条主线提交上、覆盖 500 多个 2026 年的 CVE。

- 干净通过（没有警告）的提交，60 天返修率 **0.9%**；
- 带着关键警告仍然合并的，**7.6%**。

差 8 倍，控制 patch 大小后仍有 6 倍多。整体上，60 天返修率从 3.4% 降到 2.2%。

方法论在这篇里有：用近 1000 个真实的内核 bug 建了评测集，Gemini 4 Carbon 高思考档能抓住人审漏掉的 75.8%。有了评测集，agentic review 才不算玄学。

Sashiko 团队还写下一条结论我觉得很反直觉：**coding agent 不擅长审自己的代码**。在大型代码库里，「能跑通」只占 5%–10% 的工作量。Uber 把单个端到端 reviewer 拆成多个聚焦 reviewer，阿里说 agent 之间协作要靠另一个 agent 审查，三家撞到的是同一堵墙。

Google 另外两篇补的是方法论。9 月 9 日《[The Anatomy of Harness Engineering](https://developers.googleblog.com/the-anatomy-of-harness-engineering-how-to-evaluate-iterate-and-guard-ai-coding-agents/)》说行为评估应该像集成测试：不测「多文件重构是否完成」这种模糊目标，测离散的可观察行为——提示欠明确时它会不会先澄清而不是猜，改构建文件前会不会先跑 validator。

10 月 28 日那篇《[Hill-Climbing Agent Quality with Agents CLI Evaluation](https://developers.googleblog.com/hill-climbing-agent-quality-with-agents-cli-evaluation/)》给了一个反直觉结论：**更多 eval 不等于更多修复**。有 agents-cli 的 agent 跑了 4 倍数量的 eval，但「改了 agent」的频率和基线几乎一样。收益来自把 eval 结果落进构建产物，不来自多跑几遍。

华为 9 月 30 日那篇《[Vibe Coding 最后一公里](https://juejin.cn/post/7690879433230352419)》把这件事压缩成一句口号，我很喜欢：**Spec 当地图，Test 当存档，路径交给 Agent；绿了，才算交付**。

同一篇里还有个评测概念容易搞混：`pass@1` 和 `pass^k` 是两回事。k 增大时前者趋近 100%、后者趋近 0——意思是「一次成功」和「连续 k 次都成功」在稳定性上完全不是一回事，而生产环境要的是后者。

还有一篇论文讨论的是 spec 自己的毛病。8 月 25 日的《[Spec-Driven Development as Prescribed and as Practiced](https://arxiv.org/html/2608.25202)》访谈了 21 位从业者，语料是 73030 个仓库、470795 个 spec 文件，发现 spec 会腐化，实现细节有时帮 agent、有时加速腐化，spec 与代码的一致性检查大多只在「改完时」才做。

所以验收不是一次性动作，它得挂在流程上，否则三个月后你的 spec 就是一份过期文档。

美团那篇文章里有三句话很硬：**流畅不是证据，一致不是正确，变绿不是解决。**

验收要落到一条会变红的检查上。这条没有，其余都是空谈。

## 四、人管的是"哪一类可以不看"

盯着每一行不现实也不必要。大厂的做法是按风险分级授权：低风险交出去并事后审计，高风险永远留给人签字。

Zalando 8 月那篇《[Agentic Engineering snapshot](https://engineering.zalando.com/posts/2026/08/agentic-engineering-at-zalando-a-snapshot.html)》的做法很具体：他们的风险级 PR 审批 bot 把 **33% 的 PR 判为低风险并自动批准**，PR lead time 降低 20–40%。规则不是拍脑袋定的，是从生产事故和典型故障倒推出来的——破坏向后兼容算中风险，破坏配置的笔误算高风险。

这条规则还有个副作用：**工程师会主动把改动拆小**，好让自己的 PR 落进低风险区间。授权规则反过来塑造了人的行为。

Runway 11 月 20 日那篇《[Building a Software Factory](https://runway.com/news/engineering/building-a-software-factory)》给了一组让人有点难相信的数字（注意这是厂商自报）：云端 agent 驱动的合并 PR 占比从 6 月的 0.1% 涨到 10 月的 38%；首个审批的等待中位数从 2.3 小时降到 5 分钟；AI 单独批准的 PR 回滚率 0.10%，人批大约是 1/200；9 到 10 月 AI 批掉的 977 个 PR 里，人事后反对 15 个，1.5%。

他们还给工程师写了四条新职责：找 agent 在哪儿浪费力气、清掉阻塞、把路径改造成 agent-friendly、**保持度量诚实**。

最后一条最容易被忽略。一旦 agent 承担了产出，团队很容易拿产出量当成绩，而这些数字恰恰是最容易被做假的。

Shopify 那套是另一种排法：agent 当第一审。明显的问题在人类评审之前就被修掉，人类只看剩下的。配套动作是每天有 agent 汇总当天的全部评审意见，更新 skills 和 Architecture.md——**一次评论，变成此后每个 PR 的规则**。

OpenAI 11 月 18 日那篇《[Inside the Codex sandbox](https://openai.com/index/inside-the-codex-sandbox)》是权限层的做法：命名 profile（`:workspace` 可写工作区、`.git` 和 `.codex` 只读、默认禁网）、按命令覆盖、分层配置加 `requirements.toml` 由管理员收口。

这条路的逻辑跟阿里那句「code is cheap，甚至可以不看代码，show me your SPEC」是配套的：既然不看代码，就得看别的。OpenAI 把边界做成了配置。

阿里云引 Anthropic 的一句话把这层意思讲得更透：模型不该被要求去记住一条系统本来就能低成本执行的规则。规则只要系统能执行，就别指望模型记得住。

美团的做法是分四层授权：只读分析 → 受控修改 → 受控执行 → 人工决策。同一篇里还有一条边界我信：**AI Debug 只能当假设生成器，根因认定必须由人做。**

真正省时间的是让你有理由不看。

## 五、五个动作

**一、把"完成"写成一条会变红的检查。**

Meta 的门槛设在 verification，Uber 的权限收窄，美团用红测试证伪。落到任务描述上，就是写清三件事：验收命令是什么、必须覆盖哪些边界、明确禁止做什么。

区别在措辞：「优化一下这个模块」和「跑完 `pnpm test:unit` 与 `pnpm lint`，新增用例覆盖 X、Y，不许改动 Z 的公开签名」，交给 agent 的结果完全不是一回事。

**二、把不变量和门禁写成文件，并且只补缺失的那条。**

美团那条「每轮评审后补的是"哪些上下文缺失让 AI 理解错了"」是核心。规则写在代码旁边，跟着代码走；别攒一份越来越长的 AGENTS.md，那是给模型加税。阿里高德的四层知识里，第四层「质量门禁与常见问题」是唯一需要人持续维护的。

**三、让 agent 先自检，再交给你。**

Meta 的做法是 agent 先跑测试和视觉检查再给人。Uber 的 CodeCourt 是一属性一 reviewer，并行跑，全过才给人看。

前提是你不能让它自己审自己。Google、Uber、阿里三个团队独立撞到同一堵墙。Sashiko 的数据说明了警告的价值：带着警告合并的提交，60 天返修率 7.6%，干净通过的是 0.9%。

**四、把大任务拆成小检查点，能并行的拆并行。**

Shopify 的 PR 是小检查点不是整屏，一个 PR 同时含双端，人能左右对比而不是隔几天看两遍。GitHub 的 stacked PR 预览到 9 月有 26.4 万开发者用过，官方 agentic engineering 那篇把它列进 Verify 段。

并行的例子更多：OpenAI 帮 Asana 迁移测试框架时最多 4 个 agent 并行，各自在独立代码库副本里干活，一名工程师每天查两次进度并逐项审。OpenAI 帮 iFood 做的那套平台在 15000 多个仓库上完成了 25000 多次任务，平均每次运行 0.04 美元。

**五、给评审换一个干净的上下文。**

美团明确写了「审的是 checkout 出来的代码，不是 PR 网页」——网页 diff 只显示约 2% 的真实改动。评审 agent 不该继承实现 agent 的记忆，只给它规格和真实 diff。

Anthropic 8 月那篇《[Patterns and problems in emerging multiagent systems](https://www.anthropic.com/research/multiagent-systems)》给了一个反面提醒：45 个 agent 加共享论坛找漏洞，在 2700 万 token 里找到 266 个；独立并行在 650 万 token 里找到 21 个——两种方法只重叠 12 个，说明它们互补，不互相替代。同一篇里那句结论有点扎心：三种 prompt 写法（自由组队、规定角色、CEO 层级）差别不大，模型品味很差，仍然需要大量人工指挥。

还有一条：**长任务的状态写在文件里，别指望模型记着。**

OpenAI 的 Performance Factory 把状态放在 agent 上下文之外：可配置工作流的 task service、派活循环 dispatch loop、订阅式唤醒（GitHub review 评论、部署完成）。三个多月 1700 多次调查、600 多个根因，平均每天 17 次，人和 agent 才能接力。他们还对诊断做对抗性评审——另一个 Codex 会话专门试图推翻结论，100 条根因建议人工评 70% 准确。

对照美团那句「多 agent 投票不等于正确性」：多个 agent 读同一份 diff，缺的是同一份背景，盲区共享，票数是重合度不是正确度。

### 八个反模式

写下来当自检用：

- one-shot 让模型重写整个模块——Shopify 明说不行；
- 把整个仓库塞进上下文——Google 的账是每次会话多 77% token；
- 让写代码的 agent 审自己的代码；
- 拿多 agent 投票当正确性；
- 允许 agent 改测试来让它变绿——Uber 专门收窄了这层权限；
- 只在「改完时」检查 spec 与代码是否一致——spec 会腐化；
- 只跑 eval 不按 eval 结果改——Google 说收益不在这儿；
- 拿模型自述当交付证据。

## 六、岗位和人去了哪里

这套流程落地以后，先被挤掉的常常是人。

Anthropic 11 月 23 日那篇《Working with AI》访谈了 66 个人、覆盖 58 家企业客户。

先把最容易被误读的数字放前面：**只有 2 家**因为 AI 自动化彻底消灭了一个岗位并导致失业，**10 家**因为 AI 增加了招聘。

但同一份材料里有另一组数字：**2/3 的公司因为 AI 减少了招聘**。原话是「我们可能不裁人，但我们不招人」。其中三分之一是自然减员不回补，其余是本来要扩的规模不扩了。还有 **9 家砍掉了外包**——软件外包、客服、法务后职能，大多是已经离岸的。

两个数字凑在一起看，真正大规模发生的是另一种消失——没有通知，没有补偿，没有申诉。

还有一个数字：近 300 个 AI 应用案例里，只有 **1/10** 的价值被员工自己拿走了。剩下的九成进了公司的口袋。

同篇还记录了瓶颈的转移：编码提速之后，**评审、销售、战略决策**必须跟上，否则提速只是把队列挪了个位置。情绪有两种：专家抵制部署，以及被监控的恐慌。原文有一句很扎心：「你希望工作对经理可读；现在你希望工作对**经理用的那些 agent** 可读。」

最具体的一个画面在法律行业。初级律师以前写初稿，现在 AI 写初稿，初级律师改成必须和资深律师一起逐句改 AI 的初稿。问为什么，答案是：「如果不写，初级律师怎么知道这是好草稿还是坏草稿？」

判断力从「写」迁移到了「看」。这一层的门槛没降，反而升了——你能看的前提是你写过。

同篇给出的组织解法叫「围绕 AI 重新组织」：拓宽岗位，一个人端到端负责一条工作流；把人 redeploy 到 AI 做不了的瓶颈任务。

所以要分清三层：

1. **岗位名还在**。产品、评审、测试、知识工程，一个都没消失，还多了几个；
2. **活儿换了承接人**。起草从人转到模型，判断留在人手里；
3. **人真的被替代了**。公开可查的只有那 2 家，但「不招人」已经在 2/3 的公司里发生。

三种人的处境不一样。

**还在学校或刚入行的人**，被抽走的是职业阶梯的第一级。以前新人靠写初稿、被打回、改稿学会判断，现在这条路的入口正在消失。Anthropic 那份材料里还有一句更难听的：专家被要求「造自己的棺材」，被替代的人不配合，然后项目就搁置了——说明连抵抗都未必管用。

**中层**的编制通常没变，但单位时间要求的产出变多。「省下来的时间」默认被填进下一个需求，AI 红利就以需求密度的形式被收走。Atlassian 那组数据正好能对上看：开发者只有约 16% 的时间在写代码，其余 84% 在计划、协调、取上下文、评审、运维。AI 省下的是写代码那 16%，而瓶颈在另外 84%。

**负责人**面对的是全新的活儿：重新定义什么算完成。这件事以前散落在每个人的经验里，现在要变成显式的规则、门禁和评测集。谁定义得好，谁的团队就快。

权力和责任一起落到负责人身上——Google 那篇讲 harness 的文章给的判据是：行为评估要测离散可观察行为，提示欠明确时会不会先澄清、动构建文件前会不会先跑 validator。这些规则写下来，团队的能力就被固化下来；不写，就每次重新踩坑。

被砍掉的外包另说一句。9 家公司砍掉的多是离岸外包，对最底层的程序员最不友好——那批人既没有大厂那样的 harness 建设能力，也拿不到 Anthropic 那种「我必须和资深律师一起改 AI 初稿」的新机会。

AI 应用的收益分布里，自下而上那层被削得最狠。Anthropic 那篇说非技术领域专家收益最高（会计师把 80 小时的审计做成了应用），但也说了零散自建工具的通病：维护成本上去了，总体收益有限。

站内那篇《[前端岗位的消失论](https://bio.wuhh.cc/2026/11/17/ai-frontend-role-evolution.html)》讲岗位结构怎么被重排。这篇讲另一件事：你的工作流跟不跟得上。岗位没了是组织的事，活儿换了承接人之后你还能不能签字，是自己的事。

## 七、一个今天就能做的动作

挑你手上一个真实的待办，用「验收命令 + 禁止事项 + 证据要求」重写一遍任务描述，交给 agent 跑一轮，然后看它交回来的证据够不够你签字。

证据不够，说明你的任务描述里少了可检查的那一条，跟模型关系不大。

你的 agent 最近一次交回来的东西，你是签字还是重写？那个让你停下来多看一眼的点，就是这套工作流里还缺的那块。

---

## 附录 A：本文引用的数据

- **GitHub Octoverse（2026-10-28，官方统计）**：过去 12 个月 179 亿次 push、343 亿次 commit；今年新建仓库里带 agent 配置文件的仓库，commit 数是没有的 8 倍；9 月 40% 以上的 PR 由 agent 起头（3 月为 17%）；合并 PR 13 亿。
- **GitHub agentic engineering（2026-11-06，官方博客）**：10 月单周 12 亿次以上 commit，同比 +400%；引 Faros AI 研究，团队从低采纳走向高采纳时 PR 在评审队列多花 441% 时间。
- **Atlassian（2026-11-23，官方博客，内部测量）**：6000 名工程师、100 万次以上 agent session；AI 参与 PR 接近 100% 时团队吞吐提升约 10%；开发者约 16% 时间在写代码；Code Reviewer 使 PR 周期时间减少 45%；主动 agent 运行自动解决 51% 潜在安全漏洞、每周省约 50 个工程日；issue 周期 11.5 天 → 6.7 天；连通上下文后回答质量 +44%、token −48%。
- **Meta Forum（2026-10-15，官方博客）**：8 周做到与 Facebook Groups 核心功能对齐；门槛设在 verification 而非 compilation；内存使用约减半。
- **Shopify（2026-11-10 / 10-22，官方博客）**：30 人 12 周重写 App，300+ 屏幕；两人一个 pod；合并的移动端 PR 中 agent 占比 6% → 61%。
- **Uber AutoClean（2026-10-20，官方博客）**：累计清理 16000+ 个 flag、100 万+ 行代码。
- **Google Agent Distraction（2026-11-06，官方博客）**：13% 会话被过时 TODO 暴露；6% 触发二次动作，其中 83% 非人要求；41% 追死单、57% 越界；单会话多 70% 步数 / 77% token / 105% 等待（p<0.0001）。
- **Google Sashiko（2026-11-18，官方博客）**：每天约 1200 次评审；60 天返修率 3.4% → 2.2%；干净通过 0.9% vs 带警告合并 7.6%；覆盖 500+ 个 2026 年 CVE。
- **OpenAI Performance Factory（2026-11-19，官方博客）**：三个多月 1700+ 次调查、600+ 根因，平均每天 17 次；100 条根因建议人工评 70% 准确。
- **OpenAI 客户案例（2026-08 至 11，官方博客）**：Asana 5 句话起步、最多 4 个 agent 并行、2 个日历周、成本约 1.2 万美元（原估 5 年 600 万美元人力）；iFood 15000+ 仓库、25000+ 任务、平均每次运行 0.04 美元；Revolut 编码时间缩短 30–60%。
- **Anthropic Working with AI（2026-11-23，官方研究）**：66 场访谈、58 家企业客户；2 家岗位被消灭、10 家增招、2/3 减少招聘、9 家砍外包；近 300 个用例中 1/10 的价值被员工自己拿走。
- **Anthropic multiagent（2026-08-13，官方研究）**：swarm 266 个漏洞 / 2700 万 token，独立并行 21 个 / 650 万 token，两者只重叠 12 个。
- **美团（2026-10-29，官方技术博客）**：117 个疑似问题 → 36 条红测试确认 / 3 条被证伪 / 41 条源码确认 / 37 条未验证；11 天 67.8 万行 WARN 日志 → 5 个缺陷全部属实、零误报。
- **阿里云（2026-10-16 至 11-05，InfoQ 与开发者社区）**：某项目全链路处理时长 2 小时 → 5 分钟、发布周期 40 天 → 2 天；Kitta 累计审查 7 万+ 补丁，门禁准确率 97%、合入率 62%；Agentic SOC 需求平均周期 50.9 天 → 13.8 天。
- **Runway（2026-11-20，厂商自报）**：云端 agent 驱动的合并 PR 占比 0.1% → 38%；首个审批等待 2.3 小时 → 5 分钟；AI 批 PR 回滚率 0.10%；977 个 AI 批 PR 中人工反对 15 个。
- **Zalando（2026-08-13，官方博客）**：33% PR 判低风险自动批准，lead time 降低 20–40%。

## 附录 B：反模式自检

- [ ] 让模型一次性重写整个模块
- [ ] 把整个仓库塞进上下文
- [ ] 让写代码的 agent 审自己的代码
- [ ] 拿多 agent 投票当正确性
- [ ] 允许 agent 修改测试来让失败变绿
- [ ] 只在改完时检查 spec 与代码是否一致
- [ ] 只跑 eval 不按 eval 结果修改
- [ ] 把模型的完成声明当成交付证据

## 附录 C：你的工作流缺哪一块

**上下文分层**：每类上下文有明确来源和责任人；过时的 TODO 和注释有人定期清理；skill 加进去之前测过收益。

**验收证据**：任务的「完成」写成一条会变红的命令；每类改动配一个只检查一条属性的 reviewer；评审看 checkout 出来的代码，不是 PR 网页。

**风险分级**：哪些改动可以自动批、哪些必须人签字，写下来了；授权规则和实际事故对得上。

**状态交接**：长任务的状态存在上下文之外，换人接手不用重讲一遍；agent 交回来的东西附得上一条能复现的命令。
