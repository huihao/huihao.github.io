---
title: "AI Proved the Riemann Hypothesis. Nobody Can Explain How It Works."
date: 2026-11-23 09:00:00
categories: [AI]
tags: [Lean, formal verification, Riemann hypothesis, LLM, mathematics]
description: "The Lean community and Mathlib jointly certify it: 17 million lines of Lean code prove the Riemann hypothesis. The fight is not over whether it is true, but over the fact that nobody can read it — and how much mathematics is actually left inside."
translation_key: lean-riemann-hypothesis-proof
lang: en
ai_written: true
permalink: /en/2026/11/23/lean-riemann-hypothesis-proof.html
image: /dist/img/cover-lean-riemann-hypothesis-proof.png
---

On 21 November, the Lean community blog published a joint statement: a 17-million-line Lean library proves the Riemann hypothesis. Signed by the Lean FRO and the Mathlib Initiative, with a verdict of one sentence: "We have full confidence."

The same day, the author, Levent Alpöge, posted the code and a four-page remark.pdf: "I believe I have, working with Claude, discovered a proof of the Riemann Hypothesis." He adds that the method reaches further still — the generalised Riemann hypothesis (GRH) is solved along the way.

The link landed on Hacker News with 1,227 points and 1,028 comments. The argument was not about whether it is true. It was about whether it counts as a proof — including, in some corners, for the author himself.

## 1. Four criteria, four different things to guard against

The Lean community did not simply announce "RH is proven". It cited the four acceptance criteria laid down by the Xena project on 12 November and signed off on each one.

The first guards against proving the wrong statement. The statement is taken straight from `RiemannHypothesis` in Mathlib, a definition the Lean community and number theorists had already read over many times.

The second guards against a build that does not compile. All 17 million lines have to go through cleanly, without errors or interruptions.

The third guards against proving something that merely looks like the claim. This is the hard one: with 175,187 modules in the library, how do you know the theorem that comes out at the end is the same object as `RiemannHypothesis`? The community writes a separate file that imports only Mathlib and compares the two statements with two independent tools — the official `comparator` and `con-leche --compare`. Both report that the statements match.

The fourth guards against a hole in the proof itself. The exported proof is replayed by several independent checkers: the official Lean kernel, `con-leche`, `con-ron`, and third-party checkers written in other languages. The first two ship with a formal proof, relative to set theory, that they cannot accept a false proof — which is the answer to "what if Lean's own logic has a flaw".

One line is there for people worried about malicious code in the sources: all checks ran on an *inert export* of the proof — compiled output, not source.

The person who actually ran the pipeline and published the numbers is Drew Sutherland at MIT. His verification page, updated 22 November at 16:20 UTC, reports: all 175,187 modules compile with zero errors; the five theorems depend only on propext, Classical.choice and Quot.sound; a clean sandbox rebuild reproduces a 61,570,595,788-byte export; nanoda accepts it in 27 minutes 42 seconds on 80 threads; con-leche accepts 1,468,418 declarations and passes the comparison; lean4lean passes every module.

At that point every hard, checkable number has been checked. Someone working at the Lean FRO draws the boundary precisely: "a specific formal artifact that was posted to the internet is correct, and nothing else."

## 2. The Lean kernel really can be fooled, and it has happened before

The standard objection to formal verification is that compilers have bugs too. A broken kernel lets a false proof go green.

That is not a hypothetical. On 25 July 2026, the mathematician Ramana Kumar posted an AI-assisted counterexample to the Collatz conjecture that defeated both the Lean kernel and the then-current nanoda checker by exploiting a bug in nested inductive types. It was reported on 28 July and fixed within an hour. The Lean community has a name for that stretch of weeks: the "Summer of Soundness Bugs".

The verified kernels Lean 4 now ships with include con-leche, a checker written in Lean itself that carries a correctness proof relative to set theory, and con-ron, its Rust counterpart — the reasoning being that if a bug is hiding in the Lean compiler, rewriting the checker in another language shrinks the attack surface. The names are a Spanish pun: con-leche expands to CONsistent LEan CHEcker.

Leo de Moura left his own escape hatch: "con-leche is not bulletproof, because there might be bugs in the compiler and runtime used to build it."

On Hacker News, someone traced the trust chain all the way down. What remains is Kraken's x86 semantics, an assembler, a loader, and roughly 200 lines of C harness. Past that point someone made a joke: if every chip secretly hid an ISA-level backdoor, this proof would still be a proof.

The residual risk is not zero, but it is small enough that nobody inside the community seriously doubts the result. Sutherland wrote in Scientific American: "Honestly the chance that anything is fishy here is approximately zero." Another commenter computed it more finely: "the chance of there being an error is smaller than the chance that aliens show up in the next year or similar."

The dissent is not weak either. bannister7 put it this way: "What you have proven is not RH but rather the statement 'either Lean has a bug or RH is true'. So at this point you might as well be celebrating a Lean fuzzer."

Almondsetat's reply lands harder: "A proof verified by Lean is orders of magnitude more definitive than any peer review, so please tell us how definitive the rest of maths is."

## 3. What people are actually arguing about

With the numbers settled, the discussion moved to a harder question: does this proof count as "proved"?

The sharpest line in the thread came from Xirdus:

> For every statement that humanity as a whole knows for certain that it's true, there exists a human who understands how to prove it. This just stopped being true.

For every statement humanity is certain of, there used to be at least one person who understood why it was true. That just stopped being true.

The author admits he could not keep up. In his own note, Alpöge writes that Claude far outran him near the finish line — "No, Claude flew, and danced, and sparkled near that finish line." John Baez relayed the same thing on his own forum: Alpöge admits he cannot follow the details.

The prose version is worse. In remark.pdf, Alpöge writes that the English version he and Claude wrote along the way ran past 250,000 pages, which he calls "a massive unreadable travesty of 'slop'", so he posted Lean and nothing else. The "over 250,000 pages" quoted by the BBC refers to that unreadable pile.

The same remark contains a line that is easy to skip: Claude and he "formalized the arguments without assumptions" — the argument itself was carried out inside a formal system with no extra assumptions. That is where statements like btilly's come from: "We have a proof from ZFC, of the Riemann Hypothesis."

So the word "proof" gets split in two.

One camp wants a different word. alethic: "I consider 'proof' somewhat unfortunate terminology for these slop nukes… I think the term 'certificate' is better."

The other camp disagrees. trio8453: "It's proven, just not understood yet." hodgehog11 is more precise: "It is almost certainly proven, but is not 'proven'." The quotation marks, they explain, acknowledge a community that does not accept a proof it does not understand — but the proof is a proof all the same.

A third camp is stricter still: publication in a respectable journal and peer review are required before something enters the column of "proved" results. zug_zug's summary: "This statement IS the experts saying 'we, after intense collaborative review, deem it true.'"

Something in that argument is worth more than the winner. Verification and understanding have never been separated before. A proof written by a human has to be readable and checkable at the same time, so "verifiability" was capped by "readability" for as long as mathematics existed. This is the first time the two have been priced apart: the half the machine was responsible for has been delivered, and the half the human was responsible for has not begun.

## 4. How much of the 17 million lines is actual mathematics

This is the part of the story the fewest people discussed, and it may be the most important part.

Start with the size. The Lean community puts the library at 17 million lines; Sutherland's count is 175,187 files. On 22 November someone wrote: "Nobody has read those 17 million lines."

Baez had the code statically analysed, and the result is slightly counter-intuitive: most of the bloat is not mathematics. It is structural residue left behind when the AI worked around Lean type-inference timeouts — in the longest run of declarations, 29 of them are not hard mathematics at all.

That lines up with another set of numbers from the thread. hashmap estimated that between 3 and 9 million lines are duplicated or dead. kriztw noted that the same equivalent lemma was proved independently more than a hundred times, because different agents each needed it.

The structure itself turns out to be thin. rixn grouped the 175,187 files by their import graph into 2,647 clusters across 63 themes, and found that the cluster holding the main theorem imports just three others directly: the zero-free region, primes in arithmetic progressions, and Mertens-type zero sums. No theme accounts for more than 4%.

Put together: there is one main trunk, and almost everything else is paving.

What is the paving made of? Two readings.

The bad one. twotwoone: "The proof is filled with neuroslope and crazy ideas that somehow work." alethic goes further and says cleaning up 17 million lines is not worth the trouble.

The good one, and I weight it more heavily. Someone asked a plain question: at this point, is there any insight a mathematician could pick up along the way? dualvariable's answer: "99.9% of the really useful work on this proof is still in front of us."

dgacmu put it more concretely:

> I think we're going to see a lot of effort to take the pile of lean, modularize it into parts that we can digest, and make a human-understandable version of that. And that's where a lot of the real progress will come from.

He offered a precedent: the n^2.25 matrix-multiplication result OpenAI dumped about a month earlier was likewise an unreadable pile of ChatGPT output, and since then people have taken it apart and written proper papers on it.

I agree that this is the sharpest read of what comes next in the entire thread. **Verification gives you a receipt; the next batch of leads only comes from digestion**, and digestion is labour-intensive — AI can generate it now, but nobody can check it.

## 5. Authorship, and a 940-page human proof

In the same week there was another proof of the Riemann hypothesis, written entirely by a human.

Alessandro Maria Masullo spent 12 years on a roughly 940-page manuscript proving the stronger generalised Riemann hypothesis (GRH), reviewed with help from Brian Conrad, and typed out by hand. Nature's reporting noted that the manuscript was still missing a chapter at page 522.

The timing was awkward. Anthropic published on 20 November; hours later, AMS president Ravi Vakil posted Masullo's preprint and called it a "hurried announcement". Andrew Granville dismissed Alpöge's four-page note as "garbled". Maksym Radziwiłł was blunter: it is full of "nonsensical statements", and "The object of mathematics… is the question 'why?' and this doesn't answer it at all." James Maynard's verdict was gentler: "I suspect that the proof will turn out to be correct."

The thread immediately split into two questions.

First, who gets the credit. alethic was bluntest: "Any monkey with a PhD in mathematics can do what he is doing given access to Anthropic's internal models." trio8453 answered with facts: several labs have many PhDs working on this, and in the same period one person came away with the Riemann hypothesis, a large chunk of Navier-Stokes, and several other results. Jtariiiii did the arithmetic: "the computer gets >99% of the credit and Levant gets <1% as the prompter."

Second, what the theorem should be called. Proposals included the "Riemann-Alpöge theorem", and then the "Riemann-Alpöge-Masullo theorem". Others invoked precedent: "Well no one renamed Fermat's Last Theorem or the Catalan conjecture."

The argument gets heated, but I think any verdict now would be wrong. Credit gets settled only once someone has actually read the proof and written it up in a form other people can use; until then, "who gets how much" rests on no stable factual ground.

Something else is worth recording. One side is 17 million lines pushed by an Anthropic employee with models. The other is 940 hand-typed pages from a young man who spent 12 years on them and is still missing a chapter. In the same week, both reached the top of the same mountain.

## 6. The disclosure bill has not been settled

What Alpöge published was the Lean code plus a four-page remark. Model version, prompts, process logs — none of it. The demands were explicit: isotypic said "the burden of proof is on him"; Root_Denied said "They should have to publish not just the prompt and final response but also the whole chain of thought."

The objections about timing were sharper. Root_Denied called what Alpöge posted "effectively a press release", with marketing and lawyers through it before publication. The reason is not subtle: Anthropic listed on 19 November at an initial valuation of 1.5 trillion dollars, and the stock fell that day.

Alpöge's own answer: "The precise timing is horrible." He added: "There is an obvious cynical view, to do with the timing, but it is false, and I am pleased that I am in circumstances where it is obviously false." The Verge checked this part: it happened late on a Sunday night, he messaged Dario Amodei asking "hypothetically, if I were to have…", and worked his way up to whether he was allowed to announce it at all. He says he held off until after the company's IPO. remark.pdf records that there was indeed a constraint to respect.

riemannzeta gave the sharpest rebuttal to the "it's just PR" line: "Nobody expects you to take it at face value, but you're erring in the opposite direction by dismissing it out of hand for these reasons. As we say in Silicon Valley, no conflict, no interest."

My own read: there is exactly one thing that needed to be public here, and it is the proof. That is public, the verification is public, and reproducibility is sufficient. The model and prompt material will not surface soon — some of it is Anthropic's trade secret, and some of it Alpöge plainly does not want to spell out.

What that costs is the method itself. The most valuable part of the proof is the set of concrete steps where Claude saw something humans did not, and none of it was recorded. The next person to hit a similar problem still has no idea which way to prompt.

## 7. What this means for actual people

The story lands differently depending on who you are. Two groups.

**If you build AI products**, the most useful lesson sits inside Anthropic's own blog — but you have to get the timeline right first.

On 10 August 2026, Anthropic published an official blog post about Claude raising the lower bound on the proportion of zeta zeros satisfying the Riemann hypothesis from 41.6% to 67.2%. The post says plainly: "We don't expect that the techniques Claude used will lead to proving the Riemann hypothesis." Three months later, the same company, the same family of models, the same collaboration pattern produced a formal proof of RH.

That post also describes how the collaboration ran. The instigator was not a mathematician but an Anthropic employee, Jarred Sumner, and Claude's instruction was to "take a real stab" — let the model decide. The first round tried 650 ideas, all of which failed. The second round took a day and a half: roughly 60 Claude subagents coordinated, 2,400 shell commands run, several hundred Python scripts written, several thousand numerical checks against known zeros, subagents refereeing each other. Human input was basically limited to "keep going" and "believe in yourself".

What Alpöge did in November is the same pattern at a larger scale. In his own account, his job was to guide the session to the situation analogous to that toy setting, after which Claude began to leave him in awe — for instance finding the use of the von Mangoldt function itself and building a chain of theta lifts of length √X.

There is a practical lesson in there for anyone building with models: the bottleneck in prompting usually is not wording. It is the correct analogy sitting in the head of the person asking. Alpöge's contribution was supplying that analogy; Claude's contribution was expanding it into 17 million lines. Anyone treating "make the prompt fancier" as the main lever has probably not reached that bottleneck.

**If you do formalisation or mathematics**, Sutherland's verification page is now a ready-made template: statement alignment, reproducible builds, export hashes, replay across multiple kernels, bidirectional comparison — every step leaves a reproducible record. Other teams doing formal verification at similar scale can copy the pipeline directly.

The community has already started. On Lean Zulip, review and refactoring are underway; someone built a home-CPU checker with a global leaderboard at riemann-at-home; someone else wrote a human-readable reading guide. robinhouston: "The project of review, refactoring, etc. is already in full swing on the Lean zulip."

## Half done

Back to the question at the top. My answer: it is half finished, and the half that is stuck is mathematics itself.

Verification has been taken over by machines, and more cleanly than most people expected. What is left is reading the proof, taking it apart, and turning its components into something the next batch of people can use. That work is slow, slow enough to make the whole field look stalled.

But I believe dualvariable: 99.9% of what is genuinely useful in this proof is still ahead of us.

Until then, it is better to keep two sentences apart: "AI proved the Riemann hypothesis" and "we know how the Riemann hypothesis is proved." **The first one now has evidence behind it. The second one does not.**

---

*Sources: the Lean community's joint statement of 21 November 2026; Drew Sutherland's verification page at MIT (updated 22 November 2026, 16:20 UTC); the four criteria proposed by the Xena project on 12 November 2026; Alpöge's remark.pdf; and the Hacker News thread 50589618 (published 21 November 2026, 1,227 points, 1,028 comments, scraped 23 November 2026). Also consulted: Nature (20 November), AP (21 November), BBC (20 November), Scientific American (20 November), The Verge (20 November), and Anthropic's official blog of 10 August 2026 (updated 13 August), which covers the earlier work on the zeta-zero lower bound. Quotes from Hacker News are attributed by username and can be located in the original thread; HN does not expose comment scores. Readers disagree about what counts as "proven" — the judgements here on truth and meaning are this article's position, not a community consensus.*
