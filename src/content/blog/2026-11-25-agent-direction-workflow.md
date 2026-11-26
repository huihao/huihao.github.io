---
title: '代码快了 4 倍，团队只快了 10%：大厂怎么驾驭 AI'
date: 2026-11-25 10:30:00
categories: [AI]
tags: [AI, AI Coding, 大模型, 开发流程, 工程效率, 团队协作]
description: '代码快了 4 倍，团队只快了 10%。差距落在四件事上：喂什么上下文、怎么算做完了、哪一类可以不看、长任务的状态放在哪。'
translation_key: agent-direction-workflow
lang: zh
ai_written: true
image: /dist/img/cover-agent-direction-workflow.png
---

GitHub 上，单周出现了超过 12 亿次 commit，比一年前涨 400%，比 2025 一整年还多。<sup>1</sup>

Atlassian 内部 6000 名工程师跑完 100 万次以上 agent session，AI 参与的 PR 接近 100%，团队吞吐只涨了 10% 左右。<sup>2</sup>同一份复盘还引了 Faros AI 的一项研究：AI 采纳度从低走到高，PR 在评审队列里多花 441% 的时间，省下来的时间转移到了评审。<sup>1</sup>

写代码的速度翻了几倍，团队整体的产出几乎没动。

复盘里还有一条更该先看：开发者只有约 16% 的时间在写代码，其余 84% 在计划、协调、取上下文、评审、运维。<sup>2</sup>AI 省下来的是那 16%，瓶颈在另外 84%。

Meta、Shopify、Uber、Google、OpenAI、Anthropic，加上美团、阿里、华为，这些互不认识的技术团队各自公开了工程实践，解法撞到了一块。他们动的不是提示词，是四件很具体的事：喂给模型什么、怎么判定一个任务做完了、哪一类改动可以不看、长任务的状态放在哪。

工具和模型半年换一次，这四件事不用换。

| 开关 | 大厂共同的做法 | 你能写下来的第一条规则 |
| --- | --- | --- |
| 喂什么上下文 | 只喂稳定的不变式，过时文档不进上下文 | 过时的 TODO 谁清、多久清一次 |
| 怎么算完成 | 门槛设在 verification，不停在 compilation | 任务描述里写死验收命令 |
| 哪一类可以不看 | 按风险分级，低风险自动批、高风险人签字 | 哪类改动算高风险，规则从事故倒推 |
| 状态放哪 | 状态存在上下文之外，人和 agent 才能接力 | 任务状态写在哪个文件里 |

## 一、人定标准，agent 跑圈

Meta 复盘 Forum 时说：一支小团队从零做起，8 周做到与 Facebook Groups 核心功能对齐。<sup>3</sup>

他们把人分成两层描述分工：工程师驱动每一步、AI 在每一步里辅助，叫 human-in-the-loop；agent 自己跑完从计划到测试的一圈，人定目标、看运行、跑偏时介入、最后签字，叫 human-on-the-loop。<sup>3</sup>Meta 说后者是目标，不是既成事实。

阿里云讲 AI Native 研发流程时说的是同一个问题：人在 loop 之内，还是在 loop 之上。把 agent 塞进旧流程，人和 agent 都困在同一个环里，改善都有限。<sup>4</sup>

组织怎么跟着变，阿里云 CTO 线给了三个阶段：工具原生、工作流原生、组织原生，agent 进了生产链路才算真的分水岭，他们用 7 个样板间试这条路。<sup>31</sup>推进方式里有条我记下来了：**观测指标不进考核**。agent 的产出量一旦变成成绩单，团队就会开始优化那个数字，而不是优化交付。

分工比例有数字。AI Agent Handbook 引了 Anthropic 对约 40 万次 Claude Code 会话的分析：**人平均承担约 70% 的规划决策，agent 承担约 80% 的执行决策**。<sup>5</sup>人管方向，agent 管手。

Shopify 的做法更具体：一次完整重写，30 名工程师、12 周、从 React Native 到 Swift + Kotlin、300 多个屏幕，大半代码由 agent 写。组织方式是两人一个 pod，每人同时指挥多个 agent，夜里和周末 agent 继续写，人早晨面对一队待评审的 PR。<sup>6</sup>

这次重写里最值得抄的是一条规矩，他们写成「No vibe coding」：给 agent 的护栏只问三件事，架构合不合、行为跟现有 app 一致吗、人能不能不逐行读 diff 就看懂意图。第三个问题有意思，它默认人不再逐行读 diff，但要求人**看得懂意图**。<sup>6</sup>

| 环节 | 环里：human-in-the-loop | 环上：human-on-the-loop |
| --- | --- | --- |
| 定目标 | 人拆到每一个具体动作 | 人给验收标准和边界，agent 自己排 |
| 写实现 | 人下指令，AI 补全 | agent 写完先自检再交上来 |
| 验证 | 人看 diff、跑测试 | 验证写成会变红的命令，红了才算完 |
| 评审 | 人逐行读 | agent 先审一轮，人只看它挑出来的 |
| 放行 | 人点按钮 | 按风险分级，低风险自动批 |

把人从环里挪到环上比放权难。Anthropic 访谈里有个典型翻车：某公司专家抵制部署 AI，理由是「能审双倍案例，怎么激励他审双倍」，agent 于是被搁在一边。<sup>7</sup>专家从执行者变成守门人，手里那套按代码量、按审查份数算的旧激励没跟着改。改不动激励，环上就只是个说法。

阿里云在 Agentic SOC 的实践里给了个更直接的抓手：人要先设定**目标、质量、权限、停止条件**四类边界，agent 才能自己往下推。<sup>31</sup>写任务描述时按这四类填，比讲一堆背景有用。

## 二、喂什么：只给稳定的，别给过时的

上下文是有限资源，塞得越多收益递减，真正要找的是刚好够用的那一份。<sup>8</sup>

Google 拿上亿次 agent step 的分布式 trace 量化过这件事，用 `TODO(bug/...)` 注释当代理指标：13% 的会话被这类过时注释暴露，其中 6% 会触发 agent 去干没人要求过的二次动作，这批二次动作里 83% 的人根本没提过。<sup>9</sup>

跑偏的样子有两种，去追已经关闭的死单，或者触发范围蔓延。代价是单次会话多 70% 步数、多 77% token、多 105% 等待时间。<sup>9</sup>代码里那些被遗忘的角落，现在对 agent 收的税比以往任何时候都重。

这条我信。三年半前写的 `// TODO: 这里要改成新接口` 还躺在文件里，人扫一眼知道那是历史，agent 不会，它只看见一个待办。

美团讲分布式存储里怎么用 AI Coding 时说的是同一件事：AI 的错误往往不在代码里，而在代码之外。别把全部文档喂进去，喂稳定的不变式，喂过时文档会把 AI 带偏。<sup>10</sup>

他们把 AI 的误报归成三类：理论路径存在但线上走不到、把有意为之当成缺陷，还有 AI 给的修复建议本身带错。第三类最容易被忽略，举的例子是 32 位溢出的校验在下游被截断成负数，会静默失效。你审的是 AI 的代码，但它还附了一份修复建议，这两样里第二样更难发现错。<sup>10</sup>

补上下文的方式也有讲究。每轮评审之后要补的是「哪些上下文缺失让 AI 理解错了」。补「这次发现了什么问题」，AGENTS.md 会写成事故合集，越写越长、越来越没人看；补缺失的上下文，每轮只加一条规则。<sup>10</sup>

阿里那边给上下文建了资产目录，AI Agent Handbook 把它分成五类：Skill、MCP、SPEC、README 与 runbook、模板与 checklist。<sup>5</sup>高德的四层知识更具体：代码 → 工程术语 → 业务知识 → **质量门禁与常见问题**。<sup>4</sup>

关键在第四层。上次犯过的错不写进门禁，模型下次还会犯。高德内部 coding benchmark 的结果是，通用领域 one-shot 成功率能到 90%，专业领域明显下降，差距出在四层知识齐不齐。<sup>4</sup>

规则本身也可能反过来伤你。Anthropic 拆解 agent 记忆构成时给了一条跟直觉相反的实测：给 agent 判断的自由比写死规则更管用，试过规定 agent「只记录失败」，Opus 5 和 4.7 的记忆增益反而被削弱。同一份拆解里还有个工程细节：Claude Code 的自动记忆只注入 MEMORY.md 的前 200 行或 25KB，更长的指令文件会降低遵从度。<sup>11</sup>

Google Cloud 讲怎么评测 skill 时给了一组更冷的数字。它引了一份预印本：两个 skill 基准上，307 个确认由 skill 诱发的失败里，182 个是效率退化，活照样干完，只是更慢更贵；另外 125 个是直接干错了。<sup>12,13</sup>这个数字只统计被归因到 skill 的失败对，不是普遍失败率。**你加进去的每一条 skill 都在花模型的注意力预算。**

给模型上下文像给新人发入职材料：给错版本比不给更糟。不给只是慢，给错是方向错了。

## 三、怎么算完成：看证据

这几件里面验收最贵，大厂在这上面花的钱也最多。

有一句我读了好几遍：门槛该落在 verification，不该停在 compilation。代码能编译不算完，自动测试和 UI 视觉检查都过了才算完。agent 先自检再交人，人拿到的是更少但更可信的一批。<sup>3</sup>

Meta 紧接着补了一句：信号弱了不等于没人管，管的只是从写挪到了读。你还是得读，只是读得少一点、值得读一点。<sup>3</sup>

Uber 走的是另一条路，用 AI 删代码。他们做的是 agentic 技术债清理，累计清掉 16000 多个 feature flag、100 多万行代码。<sup>14</sup>做法很克制：确定性的活儿交给确定性工具，布尔代数和条件简化直接用 PolyglotPiranha；CI 当唯一真相源，单次清理会波及整个 monorepo，本地绿不代表全仓绿；每个 fixer 的权限被收窄，测试 fixer 只准改测试文件，不限的话 agent 会改生产代码让失败的测试变绿。这条我认为是所有做法里最实用的。

最巧的是 CodeCourt：把观察到的失败模式写成显式属性，一条属性一个 reviewer agent，并行跑，全过才给人看。他们试过单个 agent 端到端审，效果反而不如拆成聚焦的子 agent。<sup>14</sup>

Uber 的做法很直接：能确定的就别交给模型判断。这跟美团讲的「确定性逻辑交给代码，不确定性判断交给模型」是同一句。<sup>14,15</sup>

美团把「证据」做成了分层表，四层各自回答不同的问题：<sup>10</sup>

| 证据层 | 能回答 | 回答不了 |
| --- | --- | --- |
| 静态推理 | 代码里有没有这条路径 | 运行时会不会真走到 |
| 构建 + 单测 | 给定输入下是否真出错 | 线上频率和幅值 |
| 集成测试 | 真实交互下是否仍可达 | 是否只在极端条件下发生 |
| 运行时日志 | 线上到底发没发生 | 是不是必然被触发 |

他们给的两组数据可以当参照：全仓评审 117 个疑似问题，最后 36 条红测试确认、3 条被证伪、41 条源码确认、37 条没验证完；另外 11 天 67.8 万行 WARN 日志，收敛出 5 个缺陷，全部属实，零误报。<sup>10</sup>

那 3 个被证伪的很典型，模型报了，人一看是误报。如果流程只到「模型说这里有问题」这一步，这 3 个就变成 3 次无意义的人工排查。**证伪也要拿证据**，这是他们那张表里没写出来的一层。<sup>10</sup>

Google 讲 Sashiko 时给了一组对照极干净的数据。Sashiko 是给 Linux 内核做 agentic code review 的系统，每天约 1200 次评审。<sup>16</sup>

- 干净通过（没有警告）的提交，60 天返修率 **0.9%**；
- 带着关键警告仍然合并的，**7.6%**。

差 8 倍，控制 patch 大小后仍有 6 倍多。<sup>16</sup>

方法论也在同一份材料里：用近 1000 个真实的内核 bug 建了评测集，Gemini 4 Carbon 高思考档能抓住人审漏掉的 75.8%。有了评测集，agentic review 才不算玄学。<sup>16</sup>

Sashiko 团队还写下一条很反直觉的结论：**coding agent 不擅长审自己的代码**。在大型代码库里，「能跑通」只占 5%–10% 的工作量。<sup>16</sup>Uber 把单个端到端 reviewer 拆成多个聚焦 reviewer，阿里说 agent 之间协作要靠另一个 agent 审查，三家撞到的是同一堵墙。<sup>4,14</sup>

Google 另外两篇补的是方法论。harness 工程给的判据是：行为评估应该像集成测试，不测「多文件重构是否完成」这种模糊目标，测离散的可观察行为，提示欠明确时它会不会先澄清而不是猜，改构建文件前会不会先跑 validator。<sup>17</sup>

eval 爬坡的结论很反直觉：**更多 eval 不等于更多修复**。有 agents-cli 的 agent 跑了 4 倍数量的 eval，但「改了 agent」的频率和基线几乎一样。收益来自把 eval 结果落进构建产物，不来自多跑几遍。<sup>18</sup>

阿里云把这类控制面拆成四个：评测、Harness、Skill、调度。评测又分 Result、Trajectory、Efficiency、Risk 四层，因为两个 agent 终态都判对的时候，结果层看不出差别，一个稳定收敛，一个靠暴力采样撞对的，差别全在轨迹里。<sup>32</sup>

华为把这件事压缩成一句口号：**Spec 当地图，Test 当存档，路径交给 Agent；绿了，才算交付**。<sup>19</sup>它还提醒 `pass@1` 和 `pass^k` 是两回事，k 增大时前者趋近 100%、后者趋近 0，意思是「一次成功」和「连续 k 次都成功」在稳定性上完全不是一回事，生产环境要的是后者。<sup>19</sup>

还有一项研究讨论 spec 自己的毛病：访谈了 21 位从业者，翻了 73030 个仓库、470795 个 spec 文件，发现 spec 会腐化，实现细节有时帮 agent、有时加速腐化，spec 与代码的一致性检查大多只在「改完时」才做。<sup>20</sup>

验收不是一次性动作，它得挂在流程上，否则三个月后你的 spec 就是一份过期文档。

美团那边有三句话很硬：**流畅不是证据，一致不是正确，变绿不是解决。**<sup>10</sup>

验收要落到一条会变红的检查上。

## 四、哪一类可以不看

盯着每一行不现实也不必要。大厂的做法是按风险分级授权：低风险交出去并事后审计，高风险永远留给人签字。

Zalando 发布的 agentic engineering 快照里做法很具体：风险级 PR 审批 bot 把 **33% 的 PR 判为低风险并自动批准**，PR lead time 降低 20–40%。<sup>21</sup>规则不是拍脑袋定的，是从生产事故和典型故障倒推出来的，破坏向后兼容算中风险，破坏配置的笔误算高风险。

这条规则还有个副作用：**工程师会主动把改动拆小**，好让自己的 PR 落进低风险区间。

Runway 讲软件工厂时给了一组让人有点难相信的数字，注意这是厂商自报：云端 agent 驱动的合并 PR 占比从 6 月的 0.1% 涨到 10 月的 38%；AI 单独批准的 PR 回滚率 0.10%，人批大约是 1/200；9 到 10 月 AI 批掉的 977 个 PR 里，人事后反对 15 个，1.5%。<sup>22</sup>

他们还给工程师新加了四件事：找 agent 在哪儿浪费力气、清掉阻塞、把路径改造成 agent-friendly、保持度量诚实。<sup>22</sup>

最后一条最容易被忽略。一旦 agent 承担了产出，团队很容易拿产出量当成绩，而这些数字恰恰是最容易被做假的。

Shopify 是另一种排法：agent 先审一轮，明显的问题在人类评审之前就被修掉，人类只看剩下的。配套动作是每天有 agent 汇总当天的全部评审意见，更新 skills 和 Architecture.md，一次评论变成此后每个 PR 的规则。<sup>23</sup>

OpenAI 讲 Codex 沙箱时给的是权限层的做法：可写的范围用命名 profile 圈起来，`.git` 和 `.codex` 默认只读，网络默认关掉，再按命令单独放开，管理员用 `requirements.toml` 收口。<sup>24</sup>

逻辑跟阿里那句「code is cheap，甚至可以不看代码，show me your SPEC」是配套的：既然不看代码，就得看别的。<sup>4</sup>OpenAI 把边界做成了配置。<sup>24</sup>

阿里引 Anthropic 的一句话把这层意思讲得更透：模型不该被要求去记住一条系统本来就能低成本执行的规则。规则只要系统能执行，就别指望模型记得住。<sup>4</sup>

美团的做法是分四层授权：只读分析 → 受控修改 → 受控执行 → 人工决策。还有一条边界我信：**AI Debug 只能当假设生成器，根因认定必须由人做。**<sup>10</sup>

省下来的时间，得落在「不用看」的那部分改动上。

## 五、长任务的状态放哪

任务超过一屏，agent 就开始靠记忆推进，记忆是它自己写的笔记。

OpenAI 的 Performance Factory 把状态放在 agent 上下文之外：工作流由 task service 管，派活用 dispatch loop 推，靠订阅式唤醒，比如 GitHub review 评论、部署完成。三个多月跑下来平均每天 17 次调查，人和 agent 才能接力。<sup>28</sup>

诊断还要对抗性评审：另一个 Codex 会话专门试图推翻结论，100 条根因建议里人工评 70% 准确。<sup>28</sup>

对照美团那句「多 agent 投票不等于正确性」：多个 agent 读同一份 diff，缺的是同一份背景，盲区共享，票数是重合度不是正确度。<sup>10</sup>

状态写在文件里，别指望模型记着。交回来的东西附得上一条能复现的命令。

## 六、今天就能改的六件事

**一、把「完成」写成一条会变红的检查。**

Meta 的门槛设在 verification，Uber 的权限收窄，美团用红测试证伪。<sup>3,10,14</sup>落到任务描述上就是写清三件事：验收命令是什么、必须覆盖哪些边界、明确禁止做什么。

区别在措辞：「优化一下这个模块」和「跑完 `pnpm test:unit` 与 `pnpm lint`，新增用例覆盖 X、Y，不许改动 Z 的公开签名」，交给 agent 的结果完全不是一回事。

**二、把不变量和门禁写成文件，只补缺失的那条。**

核心是补规则，不是补事故。规则写在代码旁边，跟着代码走；别攒一份越来越长的 AGENTS.md，那是给模型加税。阿里高德的四层知识里，第四层「质量门禁与常见问题」是唯一需要人持续维护的。<sup>4</sup>

**三、让 agent 先自检，别让它自己审自己。**

Meta 的做法是 agent 先跑测试和视觉检查再给人。Uber 的 CodeCourt 是一属性一 reviewer，并行跑，全过才给人看。<sup>3,14</sup>

前提是你不能让它自己审自己。Google、Uber、阿里三个团队独立撞到同一堵墙。Sashiko 的数据说明了警告的价值：带着警告合并的提交，60 天返修率 7.6%，干净通过的是 0.9%。<sup>4,14,16</sup>

**四、给评审换一个干净的上下文。**

美团明确写了「审的是 checkout 出来的代码，不是 PR 网页」，网页 diff 只显示约 2% 的真实改动。评审 agent 不该继承实现 agent 的记忆，只给它规格和真实 diff。<sup>10</sup>

Anthropic 讲多 agent 系统时给了一个反面提醒：45 个 agent 加共享论坛找漏洞，在 2700 万 token 里找到 266 个；独立并行在 650 万 token 里找到 21 个，两者只重叠 12 个，说明它们互补，不互相替代。同一份研究里那句结论有点扎心：三种 prompt 写法（自由组队、规定角色、CEO 层级）差别不大，模型品味很差，仍然需要大量人工指挥。<sup>27</sup>

**五、把大任务拆成小检查点，能并行的拆并行。**

Shopify 的 PR 是小检查点不是整屏，一个 PR 同时含双端，人能左右对比而不是隔几天看两遍。<sup>6</sup>GitHub 的 stacked PR 预览到 9 月有 26.4 万开发者用过，官方开发指南把它列进了 Verify 段。<sup>29,1</sup>

并行的例子：iFood 在 15000 多个仓库上跑了 25000 多次任务，平均每次运行 0.04 美元；Asana 迁移测试框架时最多 4 个 agent 并行，各自在独立代码库副本里干活，一名工程师每天查两次进度并逐项审。<sup>25,26</sup>Revolut 的做法是拆功能派给不同 agent，编码时间缩短 30–60%。<sup>30</sup>

**六、长任务的状态写在文件里。**

OpenAI 的 Performance Factory 把状态放在上下文之外，用订阅式唤醒接住 GitHub 评论和部署完成。<sup>28</sup>你要抄的是这个形状：任务状态存在文件里，谁接手都不用重讲一遍背景。

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

## 七、一个今天就能做的动作

挑你手上一个真实的待办，用「验收命令 + 禁止事项 + 证据要求」重写一遍任务描述，交给 agent 跑一轮，然后看它交回来的证据够不够你签字。

证据不够，说明你的任务描述里少了可检查的那一条，跟模型关系不大。

代码快了 4 倍，团队只快 10%，差的那部分落在验收、上下文、授权和状态这四件事上。

你的 agent 最近一次交回来的东西，你是签字还是重写？那个让你停下来多看一眼的点，就是这套工作流里还缺的那块。

---

## 附录 A：本文引用的数据

- **[29] GitHub Octoverse（2026-10-28，官方统计）**：过去 12 个月 179 亿次 push、343 亿次 commit；今年新建仓库里带 agent 配置文件的仓库，commit 数是没有的 8 倍；9 月 40% 以上的 PR 由 agent 起头（3 月为 17%）；合并 PR 13 亿；stacked PR 预览到 9 月有 26.4 万开发者用过。
- **[1] GitHub agentic engineering（2026-11-06，官方博客）**：10 月单周 12 亿次以上 commit，同比 +400%；引 Faros AI 研究，团队从低采纳走向高采纳时 PR 在评审队列多花 441% 时间。
- **[2] Atlassian（2026-11-23，官方博客，内部测量）**：6000 名工程师、100 万次以上 agent session；AI 参与 PR 接近 100% 时团队吞吐提升约 10%；开发者约 16% 时间在写代码；Code Reviewer 使 PR 周期时间减少 45%；issue 周期 11.5 天 → 6.7 天；连通上下文后回答质量 +44%、token −48%。
- **[3] Meta Forum（2026-10-15，官方博客）**：8 周做到与 Facebook Groups 核心功能对齐；门槛设在 verification 而非 compilation；内存使用约减半。
- **[6][23] Shopify（2026-11-10 / 10-22，官方博客）**：30 人 12 周重写 App，300+ 屏幕；两人一个 pod；合并的移动端 PR 中 agent 占比 6% → 61%；每天汇总评审意见回写 skills 与 Architecture.md。
- **[14] Uber AutoClean（2026-10-20，官方博客）**：累计清理 16000+ 个 flag、100 万+ 行代码；CodeCourt 一条属性一个 reviewer agent。
- **[9] Google Agent Distraction（2026-11-06，官方博客）**：13% 会话被过时 TODO 暴露；6% 触发二次动作，其中 83% 非人要求；41% 追死单、57% 越界；单会话多 70% 步数 / 77% token / 105% 等待（p<0.0001）。
- **[16] Google Sashiko（2026-11-18，官方博客）**：每天约 1200 次评审；60 天返修率 3.4% → 2.2%；干净通过 0.9% vs 带警告合并 7.6%；近 1000 个真实内核 bug 评测集，Gemini 4 Carbon 高思考档抓 75.8%；大型代码库「能跑通」只占 5%–10% 工作量。
- **[28] OpenAI Performance Factory（2026-11-19，官方博客）**：三个多月 1700+ 次调查、600+ 根因，平均每天 17 次；100 条根因建议人工评 70% 准确。
- **[25][26][30] OpenAI 客户案例（2026-08 至 11，官方博客）**：Asana 5 句话起步、最多 4 个 agent 并行、2 个日历周、成本约 1.2 万美元（原估 5 年 600 万美元人力）；iFood 15000+ 仓库、25000+ 任务、平均每次运行 0.04 美元；Revolut 编码时间缩短 30–60%。
- **[7] Anthropic Working with AI（2026-11-23，官方研究）**：66 场访谈、58 家企业客户；专家抵制部署 AI 的案例，理由是旧激励没有跟着工作方式一起改。
- **[27] Anthropic multiagent（2026-08-13，官方研究）**：swarm 266 个漏洞 / 2700 万 token，独立并行 21 个 / 650 万 token，两者只重叠 12 个；三种 prompt 写法差别不大。
- **[10] 美团（2026-10-29，官方技术博客）**：117 个疑似问题 → 36 条红测试确认 / 3 条被证伪 / 41 条源码确认 / 37 条未验证；11 天 67.8 万行 WARN 日志 → 5 个缺陷全部属实、零误报；网页 diff 只显示约 2% 的真实改动。
- **[4][5][31][32] 阿里云（2026-10-16 至 11-05，InfoQ 与开发者社区）**：某项目全链路处理时长 2 小时 → 5 分钟、发布周期 40 天 → 2 天；Kitta 累计审查 7 万+ 补丁，门禁准确率 97%、合入率 62%；高德通用领域 one-shot 成功率 90%；Agentic SOC 需求平均周期 50.9 天 → 13.8 天。
- **[22] Runway（2026-11-20，厂商自报）**：云端 agent 驱动的合并 PR 占比 0.1% → 38%；首个审批等待 2.3 小时 → 5 分钟；AI 批 PR 回滚率 0.10%；977 个 AI 批 PR 中人工反对 15 个。
- **[21] Zalando（2026-08-13，官方博客）**：33% PR 判低风险自动批准，lead time 降低 20–40%。
- **[11] Anthropic agent memory（2026-11-06，官方研究）**：给自由比给规则更有效；Claude Code 自动记忆只注入 MEMORY.md 前 200 行或 25KB。
- **[12][13] Google Cloud（2026-11-03）与论文（2026-08-12）**：307 个确认由 skill 诱发的失败 = 182 个效率退化 + 125 个功能失败。

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

---

## 参考链接

正文里的角标编号对应下面这份清单。带「厂商自报」标记的，是公司自己公布的数字，没有第三方复核。

- **[1]** GitHub Blog（2026-11-06）[Beyond code generation: A developer's guide to agentic engineering](https://github.blog/ai-and-ml/github-copilot/beyond-code-generation-a-developers-guide-to-agentic-engineering/)
- **[2]** Atlassian（2026-11-23）[6K engineers, 1M agent sessions: scaling the AI SDLC at Atlassian](https://www.atlassian.com/blog/ai-at-work/scaling-the-ai-sdlc-at-atlassian)
- **[3]** Meta 工程博客（2026-10-15）[How Meta Built Forum With AI-Native Engineering](https://engineering.fb.com/2026/10/15/ml-applications/how-meta-built-forum-ai-native-engineering/)
- **[4]** 阿里云 · InfoQ（2026-11-16）[企业 AI Native 研发流程升级与重塑](https://www.infoq.cn/article/4z7Bbxy92tjAI7MB5evM)
- **[5]** 阿里云开发者社区（2026-10-23）[AI Agent Handbook（68 页白皮书解读）](https://developer.aliyun.com/article/1774447)
- **[6]** Shopify 工程博客（2026-11-10）[How we rebuilt the Shopify app in 12 weeks](https://shopify.engineering/shopify-app-rebuild)
- **[7]** Anthropic 研究（2026-11-23）[Working with AI](https://www.anthropic.com/research/working-with-ai)
- **[8]** Anthropic 工程博客（2025-09-29）[Effective context engineering for AI agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- **[9]** Google 开发者博客（2026-11-06）[Agent Distraction](https://developers.googleblog.com/agent-distraction/)
- **[10]** 美团技术博客（2026-10-29）[如何在"不能出错"的系统里使用 AI Coding？分布式存储实践与边界](https://tech.meituan.com/2026/10/29/AI-Coding-IN-Distributed-Storage-System.html)
- **[11]** Anthropic 研究（2026-11-06）[The components of agent memory](https://www.anthropic.com/research/components-of-agent-memory)
- **[12]** Google Cloud 博客（2026-11-03）[Evaluate agent skills before they bloat your context window](https://cloud.google.com/blog/topics/developers-practitioners/evaluate-agent-skills-before-they-bloat-your-context-window)
- **[13]** 论文（2026-08-12，arXiv 预印本）[Agent Skills Can Be Harmful](https://arxiv.org/abs/2608.11888)
- **[14]** Uber 工程博客（2026-10-20）[Using AI to Delete Code: Agentic Tech Debt Cleanup at Uber](https://www.uber.com/us/en/blog/ai-code-cleanup/)
- **[15]** 美团 · QCon 上海（2026-10-21，InfoQ）[企业级 Agent 平台化实践](https://www.infoq.cn/article/BQJltkL1FJ9AG3cMeUmB)
- **[16]** Google Cloud 博客（2026-11-18）[Lessons from building Sashiko, an agentic code review system](https://cloud.google.com/blog/products/application-development/lessons-from-building-sashiko-an-agentic-code-review-system)
- **[17]** Google 开发者博客（2026-09-09）[The Anatomy of Harness Engineering](https://developers.googleblog.com/the-anatomy-of-harness-engineering-how-to-evaluate-iterate-and-guard-ai-coding-agents/)
- **[18]** Google 开发者博客（2026-10-28）[Hill-Climbing Agent Quality with Agents CLI Evaluation](https://developers.googleblog.com/hill-climbing-agent-quality-with-agents-cli-evaluation/)
- **[19]** 华为 · 掘金（2026-09-30）[Vibe Coding 最后一公里：生产级 Coding Agent 效果调优实录](https://juejin.cn/post/7690879433230352419)
- **[20]** 论文（2026-08-25，arXiv）[Spec-Driven Development as Prescribed and as Practiced](https://arxiv.org/html/2608.25202)
- **[21]** Zalando 工程博客（2026-08-13）[Agentic Engineering snapshot](https://engineering.zalando.com/posts/2026/08/agentic-engineering-at-zalando-a-snapshot.html)
- **[22]** Runway（2026-11-20，厂商自报）[Building a Software Factory](https://runway.com/news/engineering/building-a-software-factory)
- **[23]** Shopify 工程博客（2026-10-22）[We gave AI agents a mobile dev environment](https://shopify.engineering/remote-dev)
- **[24]** OpenAI（2026-11-18）[Inside the Codex sandbox](https://openai.com/index/inside-the-codex-sandbox)
- **[25]** OpenAI 客户案例（2026-11-24）[iFood](https://openai.com/zh-Hans-CN/business/customer-stories/ifood/)
- **[26]** OpenAI 客户案例（2026-08-18）[Asana](https://openai.com/index/asana/)
- **[27]** Anthropic 研究（2026-08-13）[Patterns and problems in emerging multiagent systems](https://www.anthropic.com/research/multiagent-systems)
- **[28]** OpenAI（2026-11-19）[How OpenAI's Performance Factory keeps ChatGPT fast](https://openai.com/index/how-openai-performance-factory-keeps-chatgpt-fast/)
- **[29]** GitHub Blog（2026-10-28）[Octoverse 2026](https://github.blog/news-insights/octoverse/octoverse-commits-pushes-reach-new-highs-in-2026-as-developers-build-with-agents/)
- **[30]** OpenAI 客户案例（2026-11-16）[Revolut](https://openai.com/zh-Hans-CN/business/customer-stories/revolut/)
- **[31]** 阿里云 · InfoQ（2026-10-19）[7 个样板间，探索 AI 原生研发组织](https://www.infoq.cn/article/2uG3W14THqtLhb5Vou51)
- **[32]** 阿里云开发者社区（2026-11-05）[从"能跑"到"敢用"：Agent 工程化的四个关键控制面](https://developer.aliyun.com/article/1779328)
