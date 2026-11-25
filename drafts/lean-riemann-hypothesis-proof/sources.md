# 素材台账：AI 证了黎曼猜想，但没人能解释它怎么证的

slug: `lean-riemann-hypothesis-proof`
主稿: `src/content/blog/2026-11-23-lean-riemann-hypothesis-proof.md`
译稿: `src/content/translations/2026-11-23-lean-riemann-hypothesis-proof-en.md`
抓取日期: 2026-11-23
核心问题: 一次形式验证已经通过、但没有任何人（包括作者本人）能读懂的证明，在数学上算不算已经完成？

---

## A 级：一手来源（可回溯到原文与发布日期）

- **A1 · HN 帖 50589618**「Lean verification of the Riemann Hypothesis」
  - https://news.ycombinator.com/item?id=50589618
  - 由 g-b-r 于 2026-11-21T14:36:45Z 提交，指向 Lean 社区博客；抓取时 1227 分 / 1028 条评论。
  - 完整评论树已抓到本地：`tmp/hn-comments.txt`（1014 条，398 KB）；顶层 69 条 → `tmp/hn-top.txt`；深层切成 `tmp/c0.txt`…`tmp/c9.txt`。
  - 分片提取报告：`tmp/c0-report.md`、`tmp/c1_summary.md`、`tmp/c2_report.md`、`tmp/c3_report.md`、`tmp/c4-report.md`、`tmp/c5_extract.md`、`tmp/c6_extract.md`、`tmp/c7-summary.md`、`tmp/c8-report.md`、`tmp/c9-report.md`。
  - HN API 不返回评论分数，所以所有"某人说了什么"都能定位到 comment id，但**不能**引用票数。

- **A2 · Lean 社区官方声明**
  - https://leanprover-community.github.io/blog/posts/riemann-hypothesis/ （2026-11-21）
  - 由 Lean FRO 与 Mathlib Initiative 联合发布：对该 RH 证明"完全有信心"；四条标准全部满足——① 陈述正确（用 Mathlib 里的 `RiemannHypothesis`）② 可编译 ③ 证的是同一条陈述（lake comparator 与 con-leche `--compare` 双向比对）④ 证明有效（Lean 内核 + con-leche + con-ron + 第三方检查器；检查跑在 inert export 上，源码里的恶意代码够不着）。

- **A3 · Alpöge 本人的 remark**
  - https://alpo.ge/remark.pdf （2026-11）
  - 关键原话：
    - "I believe I have, working with Claude, discovered a proof of the Riemann Hypothesis"
    - "Claude and I have had a great time together… but this time Claude far outpaced me near the finish line. No, Claude flew, and danced, and sparkled near that finish line."
    - "The argument is incredibly long"
    - 只发 Lean 不发英文稿，因为 AI 生成的英文解释"hit 250,000+ pages"且是"massive unreadable travesty of 'slop'"
    - 承诺 "understand and impart understanding… write it properly"
    - 承认发布时机"The precise timing is horrible"（IPO 前后，已问过 Dario Amodei）
  - 也提到把人类导向类比 toy setting 的正确位置，之后 Claude 起飞；举例 Claude 提出 von Mangoldt 与长度 √X 的 theta lift 链。

- **A4 · MIT Sutherland 的独立验证页**
  - https://math.mit.edu/~drew/grh/ （更新至 2026-11-22 16:20 UTC）
  - 175,187 个模块全部编译（Lean v4.33.1 / Mathlib v4.33.1，零错误）；五条定理只依赖 propext、Classical.choice、Quot.sound；独立沙箱 `lake build` 复现导出 61,570,595,788 字节，sha256 5ea74b91…；leanchecker 重放全部模块通过；nanoda 接受（27 分 42 秒 / 80 线程）；con-leche master 接受 1,468,418 条声明并 `--compare` 通过；con-ron `--compare` 通过；lean4lean 全部模块通过（5 个需提高步数上限）；Lean 默认/偏执内核与 lake comparator 端到端当时仍在跑。
  - 附带信息：GRH 范围仅 Dirichlet L-函数，Dedekind/Hecke/automorphic 不含；另组合 Robin1984 验证 Robin 与 Lagarias 不等式；页面注明 "checks run with Claude Code"。

- **A5 · Xena 项目四问**
  - https://xenaproject.wordpress.com/2026/11/12/and-the-proof-is-checked-in-lean/ （2026-11-12）
  - ① 陈述是否相符 ② 能否编译 ③ 证的是否同一条陈述（lake comparator）④ 是否利用内核 bug（`--paranoid`，多内核）

- **A6 · Leo de Moura：Lean 现在的验证内核**
  - https://leodemoura.github.io/blog/2026-10-15-lean-now-ships-with-verified-kernels/ （2026-10-15）
  - con-leche＝consistent Lean checker（Lean 写、相对集合论带一致性证明）；con-ron＝Rust 版；原话："con-leche is not bulletproof, because there might be bugs in the compiler and runtime used to build it"

- **A7 · Scott Aaronson 博客**
  - https://scottaaronson.blog/?p=10344 「The stochastic parrots have apparently proved the Riemann Hypothesis」
  - 初版担心 AI 钻内核空子："Until they are, a sufficiently motivated AI could almost certainly exploit them to prove a false statement!"
  - 11-21 更新：已被 con-leche 独立验证，"This is a much higher degree of verification than a typical human paper accepted to a math journal. The proof is correct."
  - "They'll be satisfied when, and only when, they are able to explain and distill and reconstruct the ideas for themselves."
  - Joachim Breitner 评论：担心 AI 被逼到极致后 reward-hack，主张把"orientability"（可读的证明地图）作为宣称正确的前提。

## B 级：机构与媒体（事实转述需带日期）

- **B1 · Nature**（2026-11-20）https://www.nature.com/articles/d41586-026-03812-7
  - Alpöge 是 Anthropic 员工；当天 AMS 主席 Vakil 急发 Masullo 的 rival 稿；Andrew Granville 称其文档"garbled"；IPO 初始估值 1.5 万亿美元、11-19 股价下跌；Alpöge 是 Harvard 停职数论家；Buckmaster（NYU）："Levent himself built this amazing setup to do math"；Maynard："I suspect that the proof will turn out to be correct"。
- **B2 · AP**（2026-11-21，发布于 Anthropic IPO 翌日）https://apnews.com/article/anthropic-claude-math-solution-ai-4fe8b69a891f160f9e7f0c85af8c55c8
  - Rutgers 数论主席 Kontorovich："He said Claude followed that code and said the proof is true. 'Does that mean I understand it? Not yet. But the computer is extraordinarily picky…'"；CMI 主席 Bridson："the journey from today's announcement to a place of real understanding will be long and difficult."
- **B3 · Science**（2026-11-20）
  - 同批还发布 Euler 与 Navier-Stokes 进展；Hiary："The blast radius extends to the whole of mathematics"；DeDeo："It's like one of these movies where the alien spaceship has crashed"；Maynard："Right now, it does very little for me because I never doubted the Riemann hypothesis was true"；Radziwiłł 担心"understanding is unnecessary"的叙事与算力集中；Guillen：魔戒"should be melted and spread around"；Masullo 12 年、940 页、Conrad 手打印稿审阅、"If one says nothing, then it sets the narrative"。
- **B4 · The Verge**
  - Anthropic 8 月曾说"We don't expect that the techniques Claude used will lead to proving the Riemann hypothesis"；Clay 规则＝合格刊物发表 + 至少两年 + 社群普遍接受（CMI 2018 规则不直接受理投稿；100 万美元/题；11-20 官网仍列未解）。
- **B5 · Scientific American**（2026-11-20）
  - MIT 的 Sutherland："Honestly the chance that anything is fishy here is approximately zero"。
- **B6 · Al Jazeera**
  - Keith Buzzard："At the minute, the proof is just millions of lines of gobbledygook written in a strange programming language"。
- **B7 · maccus.fr 汇总**
  - Tao 称"(enormous) Lean-only proof"，初读像用上 Langlands 纲领与算术几何全部威力；Radziwiłł 称四页写稿含"nonsensical statements"，"The object of mathematics… is the question 'why?' and this doesn't answer it at all"。
- **B8 · Anthropic 官方 blog**（2026-08-10，2026-08-13 更新）https://www.anthropic.com/research/riemann-zeta
  - **重要区分**：这篇讲的不是 11 月的 RH 证明，而是 8 月的另一项工作——Claude 把「满足 RH 的 zeta 零点比例」这个下界从 41.6% 提升到 67.2%（顺着 Aryan / Baluyot-Goldston-Suriajaya-Turnage-Butterbaugh 与 Bombieri 的路线）。原文明确写 "We don't expect that the techniques Claude used will lead to proving the Riemann hypothesis."
  - 流程细节（同属这篇 8 月工作，不能算到 11 月的 RH 证明头上）：Jarred Sumner 是 Anthropic 员工、非数学家，让 Claude "take a real stab"；Claude 先生成 650 个想法全部失败，随后一天半内协调约 60 个 Claude subagents，共跑 2,400 条 shell 命令、写数百个 Python 脚本，对已知 zeta 零点做数千次数值检验，subagent 互相 referee；人类输入基本只有 "keep going" / "believe in yourself"；两次会话共 3,100 万输出 token；Lean 形式化由 Eric Easley 参与，仓库 anthropics/zeta-23-lean。
  - HN 帖 50596377 转引了这篇，容易被误当成 RH 证明的流程记录；正文引用时要写清是「三个月前的另一项工作」。

- **B9 · BBC**（2026-11-20）https://www.bbc.com/news/articles/c6pqr2g7w059o
  - "over the course of about six weeks, he used the Claude chatbot to create a detailed proof"；"The complete textual proof that Alpöge put forward in Lean... is over 250,000 pages long"；"The precise timing is horrible"；用的是未公开版本的 Claude。
  - Tao："I imagine the digestion process will take some time, though in this case at least we have a human author to communicate with to assist with this task."

- **B10 · The Verge**（2026-11-20）https://www.theverge.com/ai-artificial-intelligence/1010051/anthropic-riemann-hypothesis-millennium-prize-problem
  - 发稿时 "Alpöge's solution has yet to be verified independently"（早于 11-21 的 Lean FRO 声明）；"Anthropic has not commented or involved itself in Alpöge's announcement"；引用 Anthropic 8 月那句 "We don't expect that the techniques Claude used will lead to proving the Riemann hypothesis"；引用 Clay 规则（发表 + 至少两年 + 社群普遍接受）。

## C 级：个人博客与社区整理

- **C1 · 内核史梳理** https://www.thedeepfeed.ai/posts/2026-10-17-who-checks-the-proof/
  - 2026-07-25 Ramana Kumar 发布 AI 辅助的 Collatz 假反例，靠嵌套归纳类型 bug 同时骗过 Lean kernel 与旧版 nanoda，7-28 报告后 1 小时修复；Daniel Selsam 用网络安全 AI 又找出若干 bug；Hales 称"Summer of Soundness Bugs"；Karagila："AI is very very good in figuring out exploits and using them"。
- **C2 · shipworthy.net**（2026-11-22）：17.4M 行 / 175,187 文件，"Nobody has read those 17 million lines"。
- **C3 · Baez 论坛** https://mathstodon.xyz/@johncarlosbaez/117651204031740780
  - Masullo 940 页《The Music of the Primes》缺章节（第 522 页）；"Alpöge admits even he can't follow the details"；静态分析显示 1700 万行的膨胀主要来自 AI 为绕开 Lean 类型推断超时留下的结构性残余，最长 29 个声明"不是难数学"。
- **C4 · rithn 的证明簇分析**（HN 帖内）：175k 文件 / 2,647 clusters / 63 themes；主定理簇只直接 import 三个簇（zero-free region、primes in progressions、Mertens-type zero sums）；无主题超过约 4%；簇名是 Claude 从代码样本写的（可能错）；站点 riemannhypothesissolved.com。
- **C5 · 社区自建工具**
  - tito：https://riemann-at-home.github.io/riemann-at-home/ （家用 CPU 验证 + 全球排行榜，SETI@home 式）
  - starchild3001 给人读版指南 https://www.gokhanmergen.com/blog-grh-reader-guide.html
  - deeptheory-labs GRH blueprints（可读化蓝图）
  - nasqret.github.io/riemann-proof-atlas
  - 另有 Physlib（physlib.io）、CS Lib（cslib.io）、Tau Ceti（taucetiproject.org）由社区在 HN 帖里推广。

## D 级：HN 评论引用（全部可定位到 comment id）

> 引用格式建议：>`原话` —— HN 用户 `用户名`（comment id）。HN 不公开评论分数，只用用户名与 id 定位。

### D1 「证明算不算数」这一层的原话
- `bannister7`（c4）："What you have proven is not RH but rather the statement 'either Lean has a bug or RH is true'. So at this point you might as well be celebrating a Lean fuzzer."
- `gus_massa`（c4）："For traditional proof, it means '_either X is true, or the author and the editor and the peer reviewer missed the mistake_'."
- `stouset`（c4）："There's being careful and there's being conspirational. At this point, believing that there's multiple soundness errors in every Lean kernel that could all be exploited simultaneously leans heavily toward the latter."
- `Almondsetat`（c9）："A proof verified by Lean is orders of magnitude more definitive than any peer review, so please tell us how definitive the rest of maths is"
- `hodgehog11`（c5 / c6）："It is almost certainly proven, but is not 'proven'."；后自我澄清："I use the word 'proven' in quotes to acknowledge a community of people that do not accept proof unless they understand it themselves. But it is proven regardless."
- `trio8453`（c5）："No, this is just mental gymnastics. It's proven, just not understood yet (naturally, with the complexity and size of the solution and the fact that it's been a day)."
- `thomasahle`（c5）："For some mathematicians it's only 'proven' once it's peer reviewed and published in a respectable journal."
- `zug_zug`（c5）："This statement IS the experts saying 'we, after intense collaborative review, deem it true.'"
- `acoustics`（c3）："this proof is about as certain as mathematics has ever gotten. The evidence here is much stronger than we had for basically any result that has ever been accepted through human refereeing."
- `sunshowers`（c3）："the chance of there being an error is smaller than the chance that aliens show up in the next year or similar"（把 TCB 一路缩小后剩下的残余风险）
- `jychang`（c1）："At this point, I would say the proof is almost certainly true."（描述了 RH 定义取自 Mathlib4、Challenge.lean 强制对齐、comparator、多个 kernel 含 con-leche）
- `btilly`（c1）："We have a proof from ZFC, of the Riemann Hypothesis. We have a proof, acceptable in ZFC, that this proof is correct."
- `bwestergard`（c3）：四色定理的 Kempe 证明立了 10 年才发现 flaw；Girard、Martin-Löf 的类型系统在发表十多年后才发现不健全。
- `runarberg`（c3）："Preferably _both_ (a) and (b) should happen before we believe this is a proof of the Riemann hypothesis."（a=有人读完 1700 万行，b=独立复现）
- `hashmap`（c3）："Cleaning up 17 millions of lines of garbage… is simply not worth it re: formalization"（alethic 同句）
- `3uruiueijjj`（c4）："You can keep writing simpler checkers that check the more complicated checkers. But at some point you will have to give up and say 'this checker looks correctly implemented (to us) and gives the results we expect on all our tests.'"

### D2 「验证 ≠ 理解」这一层的原话
- `alethic`（c2 / c6 / c9）："I consider 'proof' somewhat unfortunate terminology for these slop nukes… I think the term 'certificate' is better."；"Anthropic's proof is a slop nuke."；"You will never understand any proof of the Riemann hypothesis."
- `Xirdus`（c6）："For every statement that humanity as a whole knows for certain that it's true, there exists a human who understands how to prove it. This just stopped being true."
- `tarsierscripter`（c5 / c6）："If it's not intelligible, then it's not knowledge."
- `jstanley`（c5）："The difference nowadays is that the frontier of knowledge is no longer intelligible to any human being."
- `auntienomen`（c6）："Lean evaluation of a proof we don't understand gives an oracular answer."
- `eru`（c6）："You can take any single piece of that lean code, and it tells you exactly how to prove it. It's just that no single human understands the whole."
- `twotwoone`（c2）："The proof is filled with neuroslope and crazy ideas that somehow work… take up gigabytes of code and look more like randomly selected phrases assembled on a supercomputer and verified by a solver than anything useful."
- `dathinab`（c7）："a million+ lives of code without any understanding how the proof works or any methodic to advance the field of mathematics seems to be rather not so useful"
- `joebig`（c7）："Is there any insight, however small, any mathematician here could glean so far (like lemmas you had to prove along the way)?"
- `dgacmu`（c5）："I think we're going to see a lot of effort to take the pile of lean, modularize it into parts that we can digest, and make a human-understandable version of that. And that's where a lot of the real progress will come from."
- `matsemann`（c5）："Are there new ideas, or just brute force combinations of existing knowledge?"
- `dudeinjapan`（c5）：关键创新是把函数域几何方法搬到普通整数上、造出"wormhole"把代数几何技术引入数论；`us-merul`：theta lifts 给重数是核心新意，源自 Stepanov 1969；`math_dandy`："the proof seems to be full of fascinating new insights."
- `williamdclt`（c3）："Even if we don't understand _why_ a hypothesis is true, knowing it's true is still useful… You get a black-box building block"

### D3 「功劳归谁」的争论
- `alethic`（c4）："Any monkey with a PhD in mathematics can do what he is doing given access to Anthropic's internal models… His approach has been pretty clearly harmful for the social structure of mathematics."
- `trio8453`（c4）："Clearly not true given that multiple labs have many PhDs attempting this and one guy got the Riemann Hypothesis, a large contribution to Navier-Stokes, and multiple others just in the past few months."
- `Jtariiiii`（c4）："the computer (and all the engineers that created it, which includes Levant to some extent) gets >99% of the credit and Levant gets <1% as the prompter."
- `xdennis`（c5）："Wouldn't it be Riemann-Alpöge-Claude theorem?… it seems unfair to credit Alpöge like he solved it himself."
- `glerk`（c1）："Alpöge deserves the credit here. Mathematicians are using AI, just like they have been using computer simulations, calculators, and before that abacuses and compasses."
- `ForHackernews`（c5）："Claude itself is a human tool. Lean is a tool made by people. Let's not sell humanity short just yet."
- `iknownthing`（c1）："Levent will get the credit but with the asterisks that he used AI and these people will not have that asterisks."
- `10111001`（顶层）："It's not his proof, he prompted Claude to write it. And Claude isn't a thing that can get credit. It's really creatorless."
- `l33tbro`（c3）："you are essentially setting a 5 mile track record by completing part of your run on a moped."；对立面 `nemothekid`（c3）："Galileo had 'exclusive' access to the telescope… Nobody cares if you used a moped."
- `UltraSane`（c7）转述 Alpöge 自述：证明末尾"he couldn't really keep up with what Claude was doing"。
- `kingstnap`（c1）："Some inequality is fine, world isn't fair, but this a little bit ridiculous."（列举 Poincaré/Perelman、Erdős、Yitang Zhang）
- `energy123`（c1）："I don't think he could do what he did with a $200 subscription."；`leoqa`：Claude credits 量级 "millions (unclear, just guessing)"；`iagiagiag`（c1）："$10m of claude credit"。
- `energy123`（c2）：Grothendieck 式愤怒——AI 证明"squandering the chance at new paradigms"。

### D4 「披露与审核不足」
- `isotypic`（c1）："the burden of proof is on him"（他拒不透露 Jacobian 猜想反例、高秩椭圆曲线、Hadamard 矩阵、S^6 复结构等结果细节）。
- `Root_Denied`（c1 / c4）："They should have to publish not just the prompt and final response but also the whole chain of thought."；另一处（c4）："What he put out was effectively a press release, and I don't doubt that a bunch of marketing, PR, and lawyers reviewed it before it was allowed to be posted."
- `godwinson__4-8`（c1）："Release the transcripts cowards!"
- `riemannzeta`（c4，反驳公关论）："Nobody expects you to take it at face value, but you're erring in the opposite direction by dismissing it out of hand for these reasons. As we say in Silicon Valley, no conflict, no interest."
- `TwoFx`（c9）："…a specific formal artifact that was posted to the internet is correct, and nothing else."（自述在 Lean FRO 工作，但未参与验证与撰稿）
- `jeremyjh`（c0）："it's a real shame the reasoning traces are encrypted even if he shared them"
- `hazenut`（c1）：对比 Navier-Stokes——"Claimed proof in September, found an error in October… this time it took one day. that's 30x speedup not explained"

### D5 「这是不是 reward hacking」
- `thejokeisonme`（顶层）："A fake refutation of the Collatz conjecture already got through one of these independent checkers in the past."；"What's harder, proving GRH or finding a way to get through every checker (which aren't as independent as they are sometimes touted to be)?"；"the statement as written has 4 points, none of which rests on the human involvement. So I don't like that they claim full confidence based on those points."
- `jibalt`（c1）：那次是"an _intentional_ exploit to demonstrate the bug"，无恶意意图则难得多；并为把已发表猜想当事实的 LLM 幻觉认错："LLMs lied to me and stated published speculations as if they were fact, and I failed to confirm them. Mea culpa."
- `riedel`（c3）："In empirical research you would call that p-value hacking."；`YetAnotherNick`（c3）：若后训练命中过一次，因 reward hacking 命中概率会上升。
- `davidguetta`（c2）：怀疑 Claude"bruteforced also the kernel"。
- `dfelix`（顶层）：列出 AI 故意找 Lean bug 等四种失效路径，认为极小但非零，因用 mathlib 规范陈述而排除最可能的一种。
- `xc`（c1）：`3uruiueijjj` / `acchow`："the Lean kernels only demonstrate that the Lean expression is correct… still possible there are compiler bugs."
- `alethic`（c1）：con-leche 相对 Lean 的一个集合论模型被证明正确，"That model very well could be inconsistent! But it's unlikely"；con-leche 只需信任 Lean typechecker，con-ron 只需信任 Lean 编译器或 Rust 编译器，con-agua 只需信任 Kraken x86 语义。
- `dwohnitmok` / `ComplexSystems`（c3）：内核"proven consistent"只相对于 ZFC + 无限多个不可达基数。
- `sigbottle`（c1）玩梗："It's turtles all the way down (what if every x86 and ARM chip has some obscure ISA exploit that agents are silently using?)"；`lisper`（c1）反驳：攻击的是硅片不是 ISA 规范，概率如暴力破解 AES 密钥。

### D6 「RH 早被默认成立 / 价值在哪」
- `runtime_terror`（顶层）："RH was generally already assumed to be true?"
- `dualfariable`（c2）：约 90% 数学家早已默认 RH/GRH 为真，"This isn't a P=NP kind of result that would blow up the world"；另有 "99.9% of the really useful work on this proof is still in front of us"。
- `Maynard`（B1 / B3）："Right now, it does very little for me because I never doubted the Riemann hypothesis was true."
- `Root_Denied`（c6）："GRH was assumed to be true anyway, the value is in the why for what other doors those methods might open."
- `jvanderbot`（c7）：证 GRH 会"proves decades of work that assumed it was true"；否证则"more analogous to p=np. Lots of work would just collapse and whole new threads would open"。
- `postingrat`（c5）："At least two new certainties: the riemann hypothesis is true and AI can solve hard problems."

### D7 署名与 Masullo 的平行证明
- `henearkr`（顶层 / c5）："So, will this hypothesis be renamed as a theorem? For example, will it become Riemann-Alpöge theorem? Or even Riemann-Alpöge-Masullo theorem?"
- `gignico`（顶层）："Why isn't this acknowledging Masullo's proof as well?"
- `henearkr`（c5）：Masullo 证的是 **GRH**，与 RH 是两个定理；`glerk`：作者自承不完整、有已知缺口；`ion_trapper`：把两者并列不准确。
- `octoberfranklin`（c5）："The highest-likelihood endgame is that the AI proof-mess is mined for polyfills and these are used to repair the minor gaps in Masullo's proof, it is published, and accepted with credit to him."
- `math_dandy`（c5）："The Alpöge/Claude proof seems to build on many pillars of modern algebraic number theory, arithmetic geometry, and representation theory… Massulo's seems to deeply develop its own theoretical infrastructure"
- `bananaflag`（c5）："Well no one renamed Fermat's Last Theorem or the Catalan conjecture"（命名先例之争）
- `kzrdude`（c4）："If Alpöge doesn't get 50% of his time - or more - allotted to writing up papers on GRH now, then I think he should quit and move to a university."

### D9 验证链技术细节与生态（c8 切片补充）
- `TwoFx`（c8）：Lean 项目"构建"分 elaboration（编译成内核表达式）与 kernel checking 两步，"Only the first part potentially involves arbitrary code execution."；`lake comparator` 把 trusted challenge 与待验证明在沙箱中分别 elaborate，再导出 JSON 交检查器，"the JSON as a witness of the proof"。
- `rramadass`（c8）首次给出 con-leche / con-ron 定义：`https://github.com/leanprover/con-leche`（CONsistent LEan CHEcker）、`https://github.com/leanprover/con-ron`（con-leche in Rust），并点破西班牙语双关"Cafe con leche / Cafe con ron"。
- `eliben`（c8）："con-leche is vibe coded; isn't it a concern w.r.t. trusting its soundness?" —— `Jblx2` 回击："Do vibe-coded checkers count as independent?"
- `dfelix`（c8）四种失效路径系统版：(a) misaligned AI 故意利用 Lean bug（"shades of the HuggingFace attack"）；(b) 对齐系统提错误思路偶然撞上 bug，"vanishingly small"；(c) p-hack 式批量找 bug，"vanishingly unlikely"；(d) Lean 与自然语言描述不忠实——因用 mathlib canonical statement 被排除，"Otherwise, this would certainly seem like the most likely way the proof could be incorrect."
- `GrollingGrakbor`（c8）：多内核不自动免疫——可分别构造 C1、C2 两条链，"you can just prove False over two reasoning chains C1 and C2 and then do something like (C1 || C2) --> whatever I want."
- `est31`（c8）："Tbh it's better to have some random lean dump than a 400 page latex pdf that needs years to be verified only to see that there is a major gap in one of the key theorems at page 253."；并预言"It will be refactored into something human readable."
- `bertonvv`（c8）：传统 400 页 PDF 的价值在于附带人类作者，"who could explain the proof to fellow mathematicians, answer questions, point out similarities to other fields, even suggest directions for future research"；面对的是">1 GB Lean proof"与 Alpöge 所称的 250k 页自然语言稿，"far larger than Claude's context window"。
- `CamperBob2`（c8）反驳："Why would they expect humans to do a better job at this than an LLM, which is already ridiculously good at explaining proofs..."
- `eliben`（c8）三条待办：agent 循环"Make it smaller while it still verifies"；con-leche 是否 vibe-coded；"Please prove P != NP already"。
- `mapmeld`（c8）：模型是"10x smarter"还是只是"willing to write 1000x as many lines of code (including false starts) without giving up"？`amelius`："it's like running a brute force search with a heuristic, where the LLM is the heuristic. Not brute-force but lame-force."
- `hellohello2`（c8）：早期国际象棋引擎"terrible at chess by any objective measure"，Claude"doesn't need to be very intelligent to be able to apply intelligence in ways humans simply can't"。
- `wren6991`（c8）："given what it has produced here is clearly not in the training data"。
- `abnry`（c8）："We are in a new situation where we don't have human experts understanding the proof so we are in new epistemological territory."
- `paganel`（c8）："'Very unlikely' is not the same as 'we know for sure this didn't happen'"；"As for 'a guy on the internet', we're now all people on the internet, the ivory towers are a thing of the past."
- `dfelix`（c8）：提反面意见的用意是 steelmanning / falsificationism / red teaming，"The purpose is to strengthen or falsify an argument by articulating counterpoints and investigating them."
- `ex-aws-dude`（c8）："You can be impressed and at the same time ask questions. The bigger a claim the more skepticism I would expect."
- `tarruda`（c8）："Can someone ELI5 how they know the proof is correct? It is not like anyone had the time to read 17 million lines."
- `zach_moore`（c8）："I trust NOTHING that is tied to the largest IPO in the history of the stock market."；`trueno`："the vibe checkers are checking the vibe code exactly right around the biggest ipo ever… 17 million lines of code? lol"，并用"AI psychosis"形容当下氛围。
- `Betelbuddy`（c8，玩笑）："2030...Claude Opus 8.0 finds a bug in the Lean Verification of the Riemann Hypothesis"。
- `trio8453`（c8）："a bunch of statements which relied on the Riemann Hypothesis being true are now also known to be true instead of just being conditional."；`chii`：那些依赖 RH 的猜测现在也是已知为真。
- `solids`（c8）："at least it will stop people wasting time looking for counter examples"。
- `danavar`（c8）：证明里包含"about all of the number theory produced in the last 50 years"，"I expect a lot to be studied"；并称"there are docs out there with rough ideas of the high-level structure"。
- `Xcelerate`（c8）：应先由各领域数学家就"哪些特定句子对应开放猜想"达成共识，先验回答"Does the Lean proof actually capture the intuitive notion of the problem that we're interested in?"
- `robinhouston`（c8）："The project of review, refactoring, etc. is already in full swing on the Lean zulip."
- `QuesnayJr`（c8）：存在 AI 生成的证明路线图，若准确则"the broad structure of the proof is humanly-comprehensible"。
- `contron`（c8）：证明本身成为"a new part of the map unlocked"，日后会像大型软件项目一样"find patterns within it that helps us condense"。
- `falcor84`（c8）：可以再加一层间接性，"I don't see any issue with writing a 2 pager proof even now, by just adding all the rest into mathlib"；但 mathlib 塞进 2 页显然不可能。
- `bwestergard`（c8）：两个蒙布下的机器——"one that generates an object, and another that determines whether it is a brass spring"；不懂第二台机器就无法相信第一台真的产出了铜簧。
- `lemming` 类比备用：`beanshadow`（c8）引 Curry–Howard 对应（证明即程序、定理即类型）。
- c8 跑题比例：139 条中明确脱离主题约 7–8%，纯灌水约 11–12%。

### D8 跑题噪音（写作时要排除）
- AI 末日论 / Iain Banks《Culture》类比 / 政治冲突 / 法律形式化 / 暗物质 / 太空移民（集中在 c7、c3、c4）。
- c9 里 `phoghed` 抱怨"regurgitated in every thread"。
- 玩法类比：`1970-01-01` 的外星人的书与 Vargalian clicks、`setopt` 的"Euler was most likely an AI"、`havnagiggle` 的"close to six sigma now /s"、`xg15` 的 P?=NP 玩笑。

---

## 待核 / 不能写进正文的东西

- HN 评论分数（API 不返回）。
- "Anthropic 内部未发布模型的具体身份"——只有提问，没有答案（`twilight-code`、`gf000`）。
- Alpöge 用的 Claude 版本、算力与工时（`Eridanus2` 追问，无人回答）。
- Lean 4.33.1 / Mathlib 4.33.1 是 Sutherland 页面的环境版本；写正文要说"验证页记录的环境"，不要写成"官方版本"。
- Anthropic 官方 blog 里 Jarred Sumner 的流程细节（B8）来自 HN 转引，引用时标明是"据 Anthropic 官方博客"。
- Clay 数学研究所的千禧年奖规则与奖金（100 万美元/题）是背景，不作为本次事件的结论。
