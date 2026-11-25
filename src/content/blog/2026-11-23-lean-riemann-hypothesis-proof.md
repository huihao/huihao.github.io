---
title: 'AI 证了黎曼猜想，但没人能解释它怎么证的'
date: 2026-11-23 09:00:00
categories: [AI]
tags: [Lean, 形式化验证, 黎曼猜想, 大模型, 数学]
description: 'Lean 社区与 Mathlib 联署确认：1700 万行 Lean 代码证明了黎曼猜想。争议不在真伪，在没人读得懂——这份证明里到底还剩多少数学。'
translation_key: lean-riemann-hypothesis-proof
lang: zh
ai_written: true
image: /dist/img/cover-lean-riemann-hypothesis-proof.png
---

11 月 21 日，Lean 社区博客挂出一份联署声明：一个 1700 万行的 Lean 代码库证明了黎曼猜想。落款是 Lean FRO 和 Mathlib Initiative，结论是一句「We have full confidence」。

同一天，作者 Levent Alpöge 在自己的站点贴出代码和一份四页的 remark.pdf：「I believe I have, working with Claude, discovered a proof of the Riemann Hypothesis.」他自己补充：这套方法还能往前走，广义黎曼猜想（GRH）也一并解决了。

链接被扔上 Hacker News，1227 分，1028 条评论。吵得最凶的不是「真不真」，是「这到底算不算数」——包括作者本人。

## 一、四条标准，各防什么

Lean 社区没有直接宣布「RH 已被证明」，而是援引 Xena 项目 11 月 12 日定下的四条验收标准，逐条签字。

第一条，防的是「证错了命题」。命题直接取自 Mathlib 里的 `RiemannHypothesis`，这个定义此前已经被 Lean 社区和数论方向的人反复看过。

第二条，防的是「编译不过」。1700 万行代码要完整编译通过，不报错、不中断。

第三条，防的是「证的是另一条陈述」。这条最难：代码里有 175,187 个模块，怎么保证最后导出的定理跟 `RiemannHypothesis` 说的是同一件事？社区的做法是单独写一个只 import Mathlib 的文件，把两边的定理用两个独立工具对撞——官方的 `comparator` 和 `con-leche --compare`。两个都报告确实是同一条。

第四条，防的是「证明本身有洞」。导出的证明交给多个独立检查器重放：Lean 官方内核、`con-leche`、`con-ron`，还有第三方用别的语言写的。前两个各自带一份相对集合论的正确性证明，回应「Lean 的逻辑本身会不会有 flaw」。

有一句是专门给担心源码里埋后门的人：所有检查都跑在一份 inert export 上——编译产物，不是源码。

真正把这些流程跑完并贴出数字的是 MIT 的 Drew Sutherland。他更新到 11 月 22 日 16:20 UTC 的验证页上写着：175,187 个模块全部编译通过，零错误；五条定理只依赖 propext、Classical.choice、Quot.sound 这三条公理；独立沙箱重新 build，复现出一份 61,570,595,788 字节的导出文件；nanoda 用 80 线程跑了 27 分 42 秒就接受了；con-leche 接受 1,468,418 条声明并通过比对；lean4lean 全部模块通过。

到这里，能核的硬指标都核完了。有个在 Lean FRO 工作的人把边界划得很清楚：「a specific formal artifact that was posted to the internet is correct, and nothing else.」

## 二、Lean 内核真会被骗，而且有前科

形式验证最容易被质疑的地方在于：编译器自己也会出错。内核有 bug，一份错误证明照样能变绿。

这不是假设。2026 年 7 月 25 日，数学家 Ramana Kumar 发布了一个 AI 辅助构造的 Collatz 猜想反例，靠嵌套归纳类型里的一个 bug，同时骗过了 Lean 的内核和当时的 nanoda 检查器。7 月 28 日有人报告，修复用了一小时。那段时间在 Lean 社区有个名字：「Summer of Soundness Bugs」。

Lean 4 现在随包发布的验证内核里，con-leche 是一个用 Lean 自己写的检查器，带相对集合论的正确性证明；con-ron 是它的 Rust 版本，理由很直接——如果漏洞藏在 Lean 编译器里，换一种语言重写一遍就能缩小攻击面。这两个名字是西班牙语双关，con-leche 展开是 CONsistent LEan CHEcker。

Leo de Moura 自己留了后路：「con-leche is not bulletproof, because there might be bugs in the compiler and runtime used to build it.」

信任链被 HN 上的网友一路追到底，最后只剩 Kraken x86 的语义、汇编器、loader，加一段约 200 行的 C harness。再往下就有人开玩笑：如果每颗芯片上都藏着一条 ISA 级别的后门，这证明也是真的。

残余风险不为零，但已经小到社区内部几乎无人真怀疑。Sutherland 在 Scientific American 上写：「Honestly the chance that anything is fishy here is approximately zero.」另一位算得更细：「the chance of there being an error is smaller than the chance that aliens show up in the next year or similar.」

反对的也不弱。bannister7 说：「What you have proven is not RH but rather the statement 'either Lean has a bug or RH is true'. So at this point you might as well be celebrating a Lean fuzzer.」

Almondsetat 的反驳更有杀伤力：「A proof verified by Lean is orders of magnitude more definitive than any peer review, so please tell us how definitive the rest of maths is.」

## 三、真正吵的是「理解」

数字核完，讨论拐进更麻烦的地方：这个证明算不算「已被证明」。

现场最扎眼的一句来自 Xirdus：

> For every statement that humanity as a whole knows for certain that it's true, there exists a human who understands how to prove it. This just stopped being true.

人类确信为真的每一条陈述，都存在一个人理解它为什么为真。这件事刚刚不再成立了。

作者本人也承认跟不上。Alpöge 在自述里写，这次 Claude 在最后阶段远远跑在他前面——「No, Claude flew, and danced, and sparkled near that finish line.」John Baez 在自己的论坛转述说，Alpöge 承认自己连细节都跟不上。

文字版更糟。Alpöge 在 remark.pdf 里写，他和 Claude 顺手写的英文版最后写到了 250,000 页以上，他形容那是「a massive unreadable travesty of 'slop'」，所以干脆不发，只发 Lean。BBC 引的「超过 25 万页」，说的就是这份没人读得下去的东西。

同一份 remark 里还有一句容易被跳过：Claude 和他「formalized the arguments without assumptions」——论证本身也在无额外假设的形式系统里落地了。这是 btilly 那种说法的来源：「We have a proof from ZFC, of the Riemann Hypothesis.」

于是「证明」这个词被劈成两半。

一半人主张换个名字。alethic 说：「I consider 'proof' somewhat unfortunate terminology for these slop nukes… I think the term 'certificate' is better.」

另一半人不同意。trio8453 说「It's proven, just not understood yet」。hodgehog11 说得更细：「It is almost certainly proven, but is not 'proven'.」——引号是为了承认「不接受自己不懂的证明」的那个共同体，但证明就是证明。

还有一派更保守：得先发在正经期刊上、经过同行评审，才算进入「已证明」的序列。zug_zug 的概括是：「This statement IS the experts saying 'we, after intense collaborative review, deem it true.'」

这场争论里有个更值得记下的东西。验证和理解，过去从来没被拆开过：一份人写的证明必须同时做到可读、可检验，所以「可验证」这件事的上限，长期被「可读」卡着。这次是第一次把两件事分开定价——机器负责的那一半已经交付了，人负责的那一半还没开始。

## 四、1700 万行里有多少是真数学

这是整件事里最少人讨论、但可能最要紧的部分。

先看规模。Lean 社区说这个库有 1700 万行；Sutherland 的统计是 175,187 个文件。有人 11 月 22 日写了一句：「Nobody has read those 17 million lines.」

Baez 让人对代码做静态分析，结论有点反直觉：膨胀主要不来自数学本身，而是 AI 为了绕开 Lean 类型推断超时留下的结构性残余——最长的一串声明里有 29 个连难数学都算不上。

这跟 HN 上的另一组数字对得上。hashmap 粗估库里有 300 万到 900 万行是重复或死代码。kriztw 说，同一条等价引理被独立证了上百遍，因为不同的 agent 各自需要它。

结构本身其实很薄。rixn 把 175,187 个文件按 import 关系聚成 2,647 个簇、63 个主题，发现主定理那个簇只直接 import 了三个簇：零点自由区、素数等差数列、Mertens 型零和。没有哪个主题占比超过 4%。

拼起来看：主体是一条主干，剩下绝大部分是铺路。

铺路的是什么？有两种读法。

一种当坏消息看。twotwoone 说：「The proof is filled with neuroslope and crazy ideas that somehow work.」alethic 干脆说清洗这 1700 万行不值得。

另一种当好消息看，我更看重这种。有人问了个很朴素的问题：走到这一步，有没有哪一点洞见是数学家可以顺手套走的？dualfvariable 的回答是：「99.9% of the really useful work on this proof is still in front of us.」

dgacmu 把它说得更具体：

> I think we're going to see a lot of effort to take the pile of lean, modularize it into parts that we can digest, and make a human-understandable version of that. And that's where a lot of the real progress will come from.

他举了个先例：OpenAI 一个多月前倾倒的那个 n^2.25 矩阵乘法结果，当时也是一堆读不懂的 ChatGPT 输出，后来有人把它拆开写成了正经论文。

我同意这是整场讨论里对下一步判断最准的一句。**验证给的是收据，下一批线索得靠消化才拿得到。** 而消化是人力密集的活——AI 现在能生成，但没人能验收。

## 五、署名，和那 940 页人类证明

同一周还有另一份黎曼猜想的证明，纯人写的。

Alessandro Maria Masullo 花了 12 年写出一份约 940 页的手稿，证的是更强的广义黎曼猜想（GRH），Brian Conrad 帮忙审稿，稿子是手打印的。Nature 的报道提到，稿子在第 522 页还缺一个章节。

时机很微妙。Anthropic 11 月 20 日发稿，AMS 主席 Ravi Vakil 当天几小时后贴出 Masullo 的预印本，称之为一次「hurried announcement」。Andrew Granville 批评 Alpöge 那份四页说明文档「garbled」，Maksym Radziwiłł 说得更难听：里面尽是「nonsensical statements」，「The object of mathematics… is the question 'why?' and this doesn't answer it at all.」James Maynard 的评价则温和得多：「I suspect that the proof will turn out to be correct」。

HN 上的争议立刻转向两个问题。

第一个是给谁记功。alethic 说得最尖：「Any monkey with a PhD in mathematics can do what he is doing given access to Anthropic's internal models.」trio8453 拿事实反驳：多个实验室有大批 PhD 在试，同时期只有一个人拿下黎曼猜想、Navier-Stokes 的一大块和其他几项成果。Jtariiiii 干脆算账：「the computer gets >99% of the credit and Levant gets <1% as the prompter.」

第二个是定理该叫什么。有人提议「Riemann-Alpöge 定理」，再进一步还有「Riemann-Alpöge-Masullo 定理」。也有人搬先例：「Well no one renamed Fermat's Last Theorem or the Catalan conjecture.」

这话题吵得很凶，但我认为现在下结论一定是错的。收益分配要等有人真读懂那份证明、把它写成人能读的东西才会结算；在那之前，「谁该拿多少」没有稳定的事实基础。

值得记的是另一件事。一个是 Anthropic 员工用模型推出来的 1700 万行，一个是 12 年磨出 940 页手打印稿、至今还缺一章的年轻人，在同一周把同一座山推到了顶。

## 六、披露的账还没算清

Alpöge 发出来的是 Lean 代码加一份四页的 remark。模型版本、prompt、过程记录都没放。有人要求得更直接：isotypic 说「the burden of proof is on him」，Root_Denied 说「They should have to publish not just the prompt and final response but also the whole chain of thought.」

围绕发布时机的质疑更尖。Root_Denied 说 Alpöge 贴出来的「effectively a press release」，公关和法务都过了一遍。理由很直白：Anthropic 11 月 19 日上市，初始估值 1.5 万亿美元，股价当天跌了。

Alpöge 自己的说法是：「The precise timing is horrible.」，并补了一句「There is an obvious cynical view, to do with the timing, but it is false, and I am pleased that I am in circumstances where it is obviously false.」The Verge 核过这一段：事情发生在周日深夜，他给 Dario Amodei 发了消息问「如果是我……」，一路问到自己能不能公开；他说自己一直等到公司 IPO 之后才对外发。remark 里也写了确实有个约束要守。

riemannzeta 是反对「当公关稿看」最有力的那条：「Nobody expects you to take it at face value, but you're erring in the opposite direction by dismissing it out of hand for these reasons. As we say in Silicon Valley, no conflict, no interest.」

我的判断是：这次真正该公开的只有一样东西——证明本身。它公开了，验证也公开，可复现性足够。模型和 prompt 那块短期内出不来，既有 Anthropic 的商业秘密，也有 Alpöge 自己不太想细说的部分。

缺的这块影响什么？影响方法本身。证明里最值钱的是那些「Claude 想到了、人类没想到」的具体步骤，它们没有被记录下来。下一次谁再碰到类似的问题，还是不知道该往哪个方向提示。

## 七、落到具体的人身上

这个故事对不同的人有不同用处，我只讲两拨。

**做 AI 的人**，最值得看的经验藏在 Anthropic 自己的博客里，但得先分清时间线。

2026 年 8 月 10 日，Anthropic 发过一篇官方博客，讲 Claude 把「满足 RH 的 zeta 零点比例」这个下界从 41.6% 推到 67.2%。文章里写得很清楚：「We don't expect that the techniques Claude used will lead to proving the Riemann hypothesis.」三个月后，同一家公司、同一个模型家族，同样的协作模式，交出了 RH 的形式证明。

那篇文章还写了协作是怎么跑的。发起人不是数学家，是 Anthropic 员工 Jarred Sumner，给 Claude 的指令是「take a real stab」——让模型自己拿主意。第一轮试了 650 个想法，全部失败。第二轮花了一天半，协调约 60 个自己的 subagent，中间跑了 2,400 条 shell 命令、写了几百个 Python 脚本、对已知零点做了几千次数值检验，subagent 之间互相 referee。人类的输入基本只有「keep going」和「believe in yourself」两类。

Alpöge 在 11 月做的事是同一套模式，只是规模更大。他自己说，自己做的是把人类带到那个与 toy setting 对应的正确位置上，然后 Claude 就开始让人肃然起敬——例子是 Claude 自己找出了 von Mangoldt 的用法，拉出一条长度 √X 的 theta lift 链。

这里面有一条对做应用的人挺有用：提示工程的瓶颈通常不在措辞，在提问者脑子里那个正确的类比。Alpöge 的贡献是提供了那个类比，Claude 的贡献是把它展开成 1700 万行。凡是把「把提示词写得更花哨」当成主要杠杆的人，多半还没触到这个瓶颈。

**做形式化和做数学的人**，Sutherland 那个验证页现在是现成的模板：陈述对齐、编译复现、导出哈希、多内核重放、双向比对，每一步都留了可复现的记录。别的团队要做类似规模的形式化验证，可以直接照抄流程。

社区里已经有人动手了：Lean 的 Zulip 上，审阅和重构的工作在同步进行；有人做了家用 CPU 验证工具 riemann-at-home，配全球排行榜；有人写了一份人类可读版的导读。robinhouston 说：「The project of review, refactoring, etc. is already in full swing on the Lean zulip.」

## 算完成了一半

回到开头那个问题。我的答案是：算完成了一半，而且卡住的那一半才是数学本身。

验证这件事已经被机器接管了，接管得比多数人预期的干净。剩下的是把这份证明读懂、拆开、把里面的零件变成下一批人能用的东西。这活儿很慢，慢到让整个领域看起来像停滞了。

但我信 dualvariable 那句话：这个证明里 99.9% 真正有用的东西还在前面。

在那之前，「AI 证了黎曼猜想」和「我们知道了怎么证黎曼猜想」这两句话最好分开说。**前一句已经有证据了，后一句还没有。**

---

*本文依据 Lean 社区博客 2026 年 11 月 21 日的联合声明、MIT 的 Drew Sutherland 验证页（2026 年 11 月 22 日 16:20 UTC 更新）、Xena 项目 2026 年 11 月 12 日提出的四条标准、Alpöge 的自述 remark.pdf，以及 Hacker News 讨论帖 50589618（2026 年 11 月 21 日发布，1227 分、1028 条评论，评论内容抓取于 2026 年 11 月 23 日）整理。另参考 Nature（2026 年 11 月 20 日）、AP（11 月 21 日）、BBC（11 月 20 日）、Scientific American（11 月 20 日）、The Verge（11 月 20 日）与 Anthropic 官方博客（2026 年 8 月 10 日发布、8 月 13 日更新，关于 zeta 零点比例下界那次工作）。文中 HN 引语均标出用户名，可在原帖按用户名定位；HN 不公开评论分数。各方对「什么才算被证明」的口径不同，文中对真伪与意义的判断属于本文立场，不是社区共识。*
