---
title: "When will ordinary people be able to run frontier models at home?"
date: 2026-11-16 02:00:00
categories: [AI]
tags: [LLM, local deployment, GPU, VRAM, hardware]
description: "GPU prices may not loosen until late 2028, but if the question is framed as \"can an ordinary person run a genuinely useful large model locally\", the answer is already yes in 2026. This article lays out the institutional forecasts for memory and GPU prices, explains why this cycle will not collapse the way the mining boom did, and turns a VRAM budget table into a concrete buy-or-wait decision."
translation_key: local-frontier-llm
lang: en
permalink: /en/2026/11/16/local-frontier-llm.html
image: /dist/img/cover-local-frontier-llm.png
---

"When will ordinary people be able to run frontier large models at home?"

The question is usually reduced to a price chart: *when do GPUs get cheaper?* But as of November 2026 the reality is more interesting than that: **the price inflection point for graphics cards is still far away — late 2028 at best, 2029 in all likelihood — while "an ordinary person can run a genuinely useful large model locally" is already true today.**

Those two statements are not in conflict, because they answer two different questions:

- If you frame it as "**wait for the GPU price drop**", the earliest turning point is late 2028, most likely 2029, and even then prices only fall back to a "new normal" that sits **30%–50% above 2025** — they will not return to 2025 levels.
- If you frame it as "**can an ordinary person run a daily-driver large model locally**", the bar was lowered by **Q4 quantization, distillation and small models** — not by cheaper hardware.

This article lays out the price timeline, explains why this cycle will not collapse the way the crypto-mining boom did, and ends with a VRAM budget and a set of decisions you can act on.

## 1. The direct answer: when do prices drop?

| Window | What the major analysts say | What it means for buyers |
| --- | --- | --- |
| 2026 Q4 (now) | Conventional DRAM contract prices rise another 10%–15% QoQ; GDDR7 keeps climbing | High-level chop; November's dip was just speculative inventory unwinding |
| 2027 | The tightest year on record: Micron says 2027/28 is tighter than 2026, SK Hynix calls it "the worst supply situation ever"; Samsung has sold ~80% of its 2027 capacity, with 70% of that locked into five-year LTA contracts | Waiting a year most likely means paying more |
| H1 2028 | First output from new fabs — Micron ID1, SK Hynix M15X / Yongin — but it flows to HBM and server first | Consumer cards still have their turn to wait |
| H2 2028 – 2029 | Supply and demand finally approach balance; Counterpoint expects 2028 DRAM prices to fall ~23% versus 2027 | This is the real window for cards to loosen |
| 2029–2030 | Capacity comes online in force; oversupply (8%–12%) and even price wars become possible | Yet prices stay far above 2025 levels |

Do not expect a return to 2025 pricing. IDC treats mid-2026 levels as the "new baseline" rather than a temporary deviation, and Counterpoint calculates that 2028 DRAM prices will still be roughly **230% above 2025**. Several Chinese institutions likewise push the GPU price inflection point out to 2028.

Put differently, **waiting has a clearly quoted price**: every card bought today is more likely to become a more expensive asset over the next three years than a cheaper one.

## 2. Why this is not a mining-boom-style bust

### The bottleneck is memory, not GPU compute

This is the single most important fact about the current cycle. What constrains graphics card supply is not leading-edge logic, it is **memory dies** — and the industry's capacity for those dies is being absorbed wholesale by AI datacenters:

- Samsung, SK Hynix and Micron have moved **70%–90% of advanced capacity to HBM**. HBM carries roughly a 30% premium and consumes **3–4× more wafer** for the same capacity, so the most profitable slice of the memory industry has been reserved for AI silicon;
- In 2026, **AI datacenters absorb about 70% of global DRAM**;
- the direct consequence: GDDR7 has risen nearly **$20 per 2GB die**. On an 8GB card, **the memory bill alone is roughly ¥560 higher**;
- on high-end cards memory now makes up **more than 80% of the BOM**, so vendors have **nowhere to hide the cost** — this is a bill-of-materials problem, not a pricing strategy.

### NVIDIA has no incentive to give ground

In its FY2027 Q2, NVIDIA's data-center business was **92.5% of revenue** while the gaming/PC GPU segment was down to roughly **5.45%**. Consumer allocation is being compressed on purpose. Even the RTX 50 Super was shelved over the cost of 3GB of GDDR7, and NVIDIA brought the RTX 3060 back into production to fill the mid-range gap.

### The generational refresh that normally triggers price cuts is broken

Normally the launch of a new generation pushes the previous one down. **But the RTX 60 series is rumoured for 2028**, so the "new launch, old cards crash" mechanism barely functions for the next two years.

### Actual prices right now (November 2026)

- China (Huaqiangbei): RTX 5080 roughly **¥14,000–18,000**, RTX 5090 roughly **¥46,000–55,000**; across the line, average street prices sit at about **1.7× MSRP**;
- Overseas: RTX 5090 roughly **$4,920–5,750** (MSRP $1,999), RTX 5080 roughly **$1,700** (MSRP $999).

Anyone hoping to "bottom-fish" a card is facing a supply chain **locked down by long-term contracts, by AI demand, and by the refresh cycle** — all at once.

## 3. And yet, running a useful model locally is already possible

Price and capability are two different variables. What changed in 2026 is the second one.

### Start with the VRAM budget

With Q4_K_M quantization you can estimate requirements roughly as:

```
VRAM ≈ parameters(B) × 0.58 bytes + KV cache / context headroom
```

0.58 bytes per parameter is the typical weight footprint for Q4_K_M (quantization metadata included); the rest is for KV cache, context length and runtime overhead.

| VRAM | Models that fit (Q4) | Cheapest realistic path today | What it is good for |
| --- | --- | --- | --- |
| 8–12GB | 7B–8B (Qwen3 8B, Gemma 3 12B) | Older cards / integrated GPUs, a few hundred yuan | Summaries, translation, simple completion |
| 16GB | 14B–20B (Qwen3 14B, gpt-oss-20b) | RX 9060 XT 16G and similar, about ¥3,000–4,000 | **Daily usable**: chat, long documents, light coding |
| 24GB | 27B–32B (Qwen3 32B, R1-Distill-32B) | Used RTX 3090, about ¥3,000–4,000 in China ($1,050–1,260 overseas) | Close to mid-tier cloud models; the single-card sweet spot |
| 48GB+ | 70B | Two 3090s / 48GB pro cards / 64GB Macs | Value degrades quickly |
| 128GB unified memory | 100B+ sparse MoE models | Ryzen AI Max+ 395 mini PCs ($1,999–3,449), DGX Spark ($4,699) | Fits, but bandwidth-bound: dense models run at ~5 tok/s |

### The real change happened on the model side

What collapsed the entry barrier was not hardware, but **distillation, synthetic data and MoE**:

- a 3B model in 2026 matches a 7B from 2024;
- 20B–35B class models can already do **agentic coding and reasoning on a single 24GB card**;
- in other words, the bar for "usable" keeps rising while **the VRAM required to clear it does not**.

Symmetrically, **frontier-scale models will never be solved by cheaper consumer cards**: hundred-billion-parameter MoE weights run to 400GB–1TB, and MoE has to be budgeted by **total** parameters rather than activated ones — which is exactly why a 128GB unified-memory mini PC only manages ~5 tok/s.

### How to actually do it

- **Models**: prefer weights that ship with official Q4_K_M builds — the Qwen3 family, the gpt-oss family;
- **Runtime**: Ollama or LM Studio; the former is less fuss, the latter gives you more knobs;
- **Headroom**: leave **2–4GB for the KV cache** — a long context can eat that very quickly;
- **Validate first**: run a small 8B model in Ollama to measure throughput before committing to a bigger one.

## 4. What to actually do

### If you need it now → do not wait

Buy a 16GB card, or a used RTX 3090. **Prefer weaker cores with more memory** — local inference is almost always limited by memory capacity and bandwidth rather than raw compute. The opportunity cost of waiting is high, because 2027 only gets tighter.

### If you want frontier-tier capability → don't buy a card, use an API

DeepSeek V4 Flash runs about $0.22 / $0.66 per million tokens; GLM-5.3-Flash about $0.15 / $0.50; Chinese models generally land at ¥0.14–2 for input and ¥2–6 for output per million tokens. A used 3090, depreciated over 36 months plus electricity, costs roughly **$36–55 per month** — while serving you a *weaker* model.

On pure economics, local almost never wins. **The real reasons to run locally are privacy, offline operation, control, and immunity to vendor changes** — if none of those are on your list, the answer is an API.

### Watch three verifiable signals before committing to a large build

1. **TrendForce quarterly DRAM contract prices** turning from "up QoQ" to flat or down (Q4 is still +10%–15%);
2. **Micron ID1, SK Hynix Yongin Y1** and other new fabs ramping on schedule in H2 2027 – 2028;
3. the **RTX 60 / 50 Super** launches arriving on schedule and dragging older cards down with them.

Chinese memorymakers (CXMT, YMTC) scaling up is the main variable that could pull the inflection point forward — Acer's Jonney Chen has argued 2027 could stabilise because of it.

### The reverse risk

If AI capital spending hits an air pocket just as 2028's new capacity lands, memory has historically (2019, 2022) fallen **fast rather than slowly**. This time, though, so much volume is locked in long-term contracts through 2028–29 that a crash is harder to produce than in previous cycles.

## Closing thoughts

Separate the two questions and the answer becomes clear:

- **"Running frontier-scale models locally" is a supply-side problem.** The answer is 2028–2029, and even then prices only fall to a new normal that is lower than today but well above 2025.
- **"Running a genuinely useful model locally" is a solved problem.** The answer is now: a 16GB card or a used 3090, Q4 quantization, Ollama.

The decision worth making is not "wait or not" — it is **what you actually need: capability (buy an API), privacy (run locally), or both (split it: keep sensitive workloads local, route the rest through an API)**.

> All prices above are channel/retail quotes from the first half of November 2026; Chinese pricing swings much harder than overseas pricing because of cross-border procurement and hoarding. The 2028–2030 timeline is an institutional expectation, not an accomplished fact. Order at the day's actual price.
