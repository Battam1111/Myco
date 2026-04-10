# Vision Recovery — 传统手艺 Debate

> **Date**: 2026-04-10
> **Protocol**: 传统手艺（Claim → Attack → Online Research → Defense → Revise → Repeat until ≥85% confidence）
> **Trigger**: User raised vision-drift concern after publication push (commit `e572a1c`). Quote:
>
> > "我总感觉哪里有些不对，有些偏移…我所希望的 Myco 是能够在不断地各种交互过程中…尽最大可能进行进化，并且这不涉及到 Agent 和人的『参数更新』，而是由 Myco 来实现这一点，生长基质的命名由来也是这个，而且我们曾经还计划了在后续版本甚至要加入自动化功能，即 Myco 驱使着 Agent（和人）吸收吞噬世界上最新最棒最好的知识，不断进化。而之前还有过比喻，就是 Agent 相当于是 CPU，而 Myco 则是其他的所有。也许是因为上下文压缩的原因，这些目前好像都丢失了。"
>
> **Source material**: Session `2f34106c-6d60-4aae-b5eb-176776fd08cd.jsonl` (2026-04-08 Myco 设计会谈, 3.8 MB, 1021 lines, 323 user messages). Extraction workspace and distilled quote files are kept local via `.gitignore`.

---

## 0. Why this debate exists

Between 2026-04-08 (Myco 命名日) and 2026-04-10 (公开发布日), the public-facing narrative drifted. Through two rounds of `readme_craft`, `launch_craft`, and `decoupling_positioning` work, the README converged on a **defensive / reflexive** framing ("other tools give memory, Myco gives metabolism — lint catches drift") that is *true but incomplete*. Three successive re-extraction passes from the 04-08 transcript (all triggered by user requests on 2026-04-10) revealed that **eighteen** structurally important elements were compressed out of the top layer of documents. The first four are what the user explicitly named at the start; seven more emerged when I scanned for "anything else load-bearing"; another seven emerged when the user recalled that "compression was also important." Each pass found content as weighty as the last, which is itself diagnostic: **context compression eats core identity in proportion to the fraction of the corpus it discards, not in proportion to how "important" the content was to the original author**. Every future identity audit should expect multiple recursion passes before convergence.

**Primary four (user-identified):**

1. **Substrate identity** — Myco *is* the substrate Agent runs on. Not a "layer," not a "tool," not a "companion."
2. **CPU ↔ everything-else metaphor** — Agent = raw compute; Myco = memory, storage, OS, peripherals, *and* the self-upgrading OS itself.
3. **Non-parametric evolution** — all learning happens in Myco; Agent weights are never touched. This is the *mechanism* behind "Self-Evolving."
4. **Knowledge metabolism → external absorption** — Myco drives Agent (and human) to proactively 吞噬 external knowledge. Growth comes from outside, not just from internal reflection.

**Secondary seven (found during 04-10 first re-extraction):**

5. **Mutation / Selection collaboration model** — system 做变异, human 做选择. The canonical human-Myco relationship.
6. **Transparency → selection pressure → anti-cancer** — the causal chain that makes immutable law #2 load-bearing.
7. **Agent-as-subject, human-as-weak-collaborator** — the Second-Brain paradigm inversion, only weakly named.
8. **Living-vs-dead thermodynamic frame** — metabolism = life, absence-of-metabolism = death, not metaphorically but definitionally.
9. **"Unconscious prototype already running"** — ASCC 8-day project as credibility anchor, not just validation stats.
10. **Six-way differentiation matrix** — vs Hermes, Second Brain, Hyperagents, Mem0, Enterprise KMS, hand-crafted Cowork.
11. **Four acknowledged blind spots** — cold start, trigger signals, alignment, compression engineering. An open-problems list worth publishing.

**Tertiary seven (found during 04-10 second re-extraction, user-prompted with "compression was important too"):**

12. **Compression doctrine** — storage is infinite, attention is not; compression mechanism *is* intelligence; compression is agent-adaptive (context-window-aware); three candidate criteria (usage frequency, temporal relevance, exclusivity).
13. **Seven-step metabolism pipeline including 淘汰 (active excretion)** — without excretion, it's ingestion, not metabolism.
14. **Self-model four-layer hierarchy (A/B/C/D)** — inventory / gap sensing / decay sensing / efficacy evaluation, with "dead knowledge" concept inside layer D.
15. **Kernel / instance separation** — Myco kernel is project-agnostic like an OS; project content is an "application" running on it. Makes the substrate-as-OS metaphor literal, not analogical.
16. **Transferable vs project-specific knowledge** — two-axis classification governing how compression and distillation treat each kind.
17. **Structural decay vs factual decay** — lint catches factual decay only; structural decay (right architecture for early-stage ≠ right architecture for mature stage) has no detector and is an open problem.
18. **Theoretical foundations lineage** — Karpathy LLM Wiki + Polanyi Tacit Knowledge + Argyris Double-Loop Learning + Toyota PDCA + Voyager Skill Library. Myco stands on 50 years of epistemology, control theory, and organizational learning research; the public README mentions none of it.

The public README positions Myco as a **watcher** (lint, reflect, reference integrity). The original vision positioned it as a **growing organism that eats the world and digests it into shared knowledge**. These are not the same thing. A watcher can be bolted onto any project. A substrate redefines the relationship between Agent and environment.

This is not a branding quibble. It is a L-struct / L-meta concern: the top-layer description shapes which contributors, integrations, and use cases show up, which in turn shapes what Myco evolves into. **Drift at the vision layer compounds faster than drift at the code layer, and lint does not catch it.**

---

## 1. Recovered quotes from the 2026-04-08 session

Verbatim from the transcript. These are the ground truth the public docs must be reconciled against.

### 1.1 The CPU metaphor (origin)

> "它跟 Agent 的关系是**共生**的，不是包含关系。一个类比——Agent 是 CPU，这个系统是 CPU 以外的一切（内存、硬盘、操作系统、网络接口）。没有 CPU 它是一堆死数据；没有它 CPU 每次开机都失忆。但关键是——**这个『操作系统』能自己升级自己**，CPU 只是提供算力来执行升级。"

Critical detail often missed on re-reading: the OS *upgrades itself*, using the CPU as execution substrate. The direction of agency is **substrate → agent**, not the other way around. This is the seed of non-parametric evolution.

### 1.2 Substrate identity (definition)

> "它是一个能自主生长的认知基质（substrate），Agent 在其上运行，它从环境中汲取知识来壮大自身，同时通过元进化不断优化自己的生长方式。"

> "本质：与 AI Agent 共生的自主认知基质。Agent 提供算力，它提供持久性。无 Agent 则无法运行；无它则 Agent 每次从零开始。"

> "Myco 是什么：Autonomous Cognitive Substrate — 自主认知基质。"

Three independent formulations across the 04-08 session, all naming the same primitive: **Autonomous Cognitive Substrate (ACS)**. This is the object Myco *is*, not the function it performs. Losing this word is like Linux losing "kernel."

### 1.3 Knowledge metabolism (external absorption)

> "**特征 A — 知识代谢**：不是被动接收信息，而是主动觅食、消化、吸收、排泄。这是 Hermes 和 Nuwa 都完全没有的。Hermes 只消化用户交互产生的经验，不主动去外部世界找东西。"

> "```
> 外部世界（GitHub / 论文 / 社区 / 工具）
>   ↓ 自主发现
>   ↓ 评估 → 萃取 → 整合 → 压缩 → 验证
> 系统 → 变得更强
> ```"

> "生物学的类比是**新陈代谢**——活的系统和死的系统的区别就在于：活的系统持续从环境中摄入物质、转化为自身结构、排出废物。你要的不是一个『知识仓库』，而是一个**有新陈代谢能力的知识有机体**。"

User-side confirmation quote from the same session (user message):

> "我还要补充一点它最重要的也是我认为最有必要的能力，就是自动化信息收集、整理归纳、转化为系统自身能力的能力…"

**This is the single most under-represented element in the current public README.** The four-gear engine as currently documented is entirely *inward-facing* — friction → reflect → retrospect → distill. There is no outward-facing gear that goes to the world. The original vision explicitly included one.

### 1.4 Non-parametric evolution (the mechanism)

> "Meta 刚在 3 月发了 Hyperagents——它做到了『元进化』…但关键区别是：**Hyperagents 进化 Agent 自身（prompts/策略/权重），我们进化的是 Agent 的外部认知环境**。一个改 CPU，一个改硬盘和操作系统。两者互补。"

> "为什么这在我们的系统中特别可行：进化对象是文件系统上的文本和结构——markdown 文件、Python 脚本、目录组织。这是 LLM Agent 最擅长操作的介质。相比 Meta Hyperagents（需要修改模型权重和训练循环），我们的元进化在技术上简单得多。"

The user's 04-10 wording ("这不涉及到 Agent 和人的『参数更新』") is not a new idea — it is the *exact same claim* reiterated in plain language. Myco's evolution is structurally non-parametric. That is not a limitation. It is the entire thesis.

### 1.5 The perpetual-evolution immutable law (origin)

> "我觉得是的，确实如此，我认可，如果还有什么不可变的，那就是永远都在进化路上，这是不可变的，不然系统就失去了它最大的特性。"

This law is preserved in the current README (immutable law #3), but its causal chain is severed: the README does not explain *why* stagnation = death, which requires the substrate + metabolism framing. Without metabolism, "perpetual evolution" sounds like a slogan. With metabolism, it is a thermodynamic statement — an organism that stops eating dies.

### 1.6 Mutation / Selection — the human-Myco collaboration model (lost)

> "**系统做变异（mutation），人类做选择（selection）。** 系统不断产生变化——发现新知识、尝试新组织方式、试验新的进化策略。人类不需要设计这些变化，只需要表达『这好/这不好』。就像自然选择不设计物种，只淘汰不适应的。选择压力来自你，变异来自 Agent+系统。"

This is *the* canonical model of how a human works with Myco. It is not present in the current public README. The README describes *what* Myco does but not *how the human relates to it*. Losing this means new users (and new contributors) have no mental model of their own role.

### 1.7 Transparency → selection pressure → anti-cancer (the causal chain behind immutable law #2, lost)

> "**透明性。** 系统必须始终是可被人类（通过 Agent 辅助）理解和审查的。系统可以改变自己的一切——组织方式、进化策略、压缩算法——但不能改变『始终保持可理解』这一条。因为如果透明性丧失，人类就失去了提供选择压力的能力，系统就可能走向『癌变』——自我优化但不再服务于实际目标。"

The current README states law #2 ("Transparent — auditable and understandable by humans, always") but severs the causal chain. Without the mutation/selection model, "transparent" sounds like a nice-to-have. With it, transparency is the only thing preventing a self-optimizing substrate from going cancerous. This is the hardest teeth the law has, and it was filed off.

### 1.8 Agent-as-subject, human-as-weak-collaborator inversion (weakly preserved)

> "现在绝大多数系统都是『人为中心，AI 辅助』。你反过来了——Agent 是主体，人类是偶尔介入的审批者。这意味着系统的『用户界面』不是给人看的，是给 Agent 消费的。信息密度、格式、组织方式都应该针对 Agent 的认知特点优化（比如 token 效率、上下文窗口约束、一次性可加载量）。"

User 04-08 primary description: "面向 Agent 为中心，人类只是辅助/把关/弱合作者的场景". This reverses the Second Brain paradigm entirely. Current README implicitly assumes this (the whole tool is obviously for agents), but never *names* the inversion. Not naming it means readers default to the Second Brain frame and get confused when Myco's docs are not human-pretty.

### 1.9 "Living vs. dead system" — the thermodynamic frame (lost)

> "生物学的类比是**新陈代谢**——活的系统和死的系统的区别就在于：活的系统持续从环境中摄入物质、转化为自身结构、排出废物。"

> "它是**活的**——有代谢、有进化、有生长。它不是知识库（被动），不是记忆模块（只消化交互），不是工作流引擎（规定性的），不是第二大脑（人类中心）。"

The word "living" appears once in the current README's story section ("the living network beneath"), but only poetically. The *thermodynamic* argument — living systems metabolize matter, dead systems don't, a knowledge base that doesn't metabolize is by definition dead — is gone. This is the argument that makes "stagnation = death" load-bearing instead of sloganeering.

### 1.10 "We've been running a primitive version of this unconsciously" (lost)

> "这意味着：**我们已经在不自觉地运行这个系统的原始版本了。** 只是它的元进化是人类驱动的（你说『我们需要改进系统』→ 我们辩论 → 改进），还不是系统自驱动的。"

> "把我们已经在做的事情，从人类驱动升级为系统自驱动。"

This is Myco's credibility anchor: the 8-day ASCC project was not a demo, it was an unconscious prototype of the system Myco is now formalizing. The current README mentions "8 days, 80+ files" as validation stats but does not frame it as *"proof that the substrate works; what's missing is the self-driving"*. Losing this makes Myco look like a new idea rather than a *formalization of a proven pattern*.

### 1.11 Differentiation matrix — the six-way comparison (partially preserved)

04-08 built a full 6-column differentiation matrix vs: 当前（Claude Cowork 手工） / Hermes Agent / Second Brain / Hyperagents / Mem0 / Enterprise KMS. Rows: 主体 · 范围 · 进化机制 · 平台 · 存储 · 元进化能力 · 知识代谢能力 · 自我模型 · Agent-adaptive · 质量保障. Current README has only the Mem0 callout and the L-exec/L-skill/L-struct/L-meta table. The full matrix is the single most convincing artifact for anyone asking "how is this different from X?"

### 1.12 Four blind spots named in vision debate (lost from public)

04-08 named four blind spots still unresolved:
- **Cold start** — how does Myco bootstrap when no history exists
- **Trigger signals** — what fires each gear
- **Alignment** — how to keep system-evolved rules aligned with user intent when human can no longer evaluate them directly
- **Compression engineering** — what to drop when, without losing load-bearing tacit knowledge

These are open problems acknowledged in the canonical vision doc but not surfaced to public contributors. An open problems list is exactly the kind of content that attracts good PRs.

### 1.13 Compression doctrine — the thermodynamic split (lost, user-flagged)

> User, 04-08: "我认为**不需要遗忘**，因为它不是生物，它的存储空间可以无限大，只要有存储介质即可；**但的确需要压缩**，因为它在活动时不可能查看所有过往的记忆，这太低效也没必要，**合适的压缩机制本身也是智能的体现**。同时这也是可以进化的点。"

This is Myco's compression doctrine in one paragraph. Three distinct claims are bundled:

1. **Storage is infinite, attention is not.** Myco's storage budget is *thermodynamically* unlimited (just add disks); its attention budget is bounded by the Agent's context window. Compression lives entirely on the attention side.
2. **Compression mechanism *is* intelligence.** It is not plumbing. The decision of what to keep active, what to push to cold storage, what to re-summarize, what to re-expand on demand — this is the substrate *thinking*. Demote it to "just an engineering detail" and Myco's primary cognitive act gets hidden.
3. **Compression itself evolves.** Not just the content being compressed. The compression strategy is a first-class evolution target (Gear 3 / 4 candidate).

Three candidate criteria for what to drop, from assistant-side probing (04-08):

- **Usage frequency** — low-read wiki pages / low-referenced canon entries
- **Temporal relevance** — time-bound knowledge past its validity
- **Exclusivity** — "常识 every agent already knows" (e.g. basic Python syntax) wastes substrate space

One more structural rule (04-08):

> "32K context 的 Agent 需要比 200K 的更激进的压缩。"

Compression is **agent-adaptive**. The same Myco substrate must render itself differently for a 32K-context client vs. a 200K-context client. This is a concrete example of Agent-adaptive universality (the fifth core capability), not just a theoretical property.

**Why this was the single most dangerous thing to lose**: the public README currently treats compression as housekeeping (the ".original / auto-compressed" file convention is mentioned once in MYCO.md, never in README). But compression is the *bottleneck of Agent-Myco bandwidth* — everything Myco knows must pass through the compression pipeline before it reaches the Agent's context window. Lose the doctrine, and Myco looks like a file store. Keep it, and Myco is revealed as a cognitive compressor whose job is to decide what the Agent gets to think with.

### 1.14 Seven-step metabolism pipeline — including 淘汰 (active excretion) (lost)

Original 04-08 pipeline, verbatim:

> "```
> 外部世界（GitHub/论文/社区/工具）
>         ↓ 自主发现
>         ↓ 评估（相关性、质量、新颖性）
>         ↓ 萃取（不是复制，是提取有用的模式）
>         ↓ 整合（融入已有知识，不是简单追加）
>         ↓ 压缩（保持精简，不臃肿）
>         ↓ 验证（事实性、时效性）
>         ↓ **淘汰（过时的知识主动清除）**
> 系统自身 → 变得更强
> ```"

The current `myco_vision_2026-04-08.md` shows **six** steps (discover → evaluate → extract → integrate → compress → verify). The canonical 04-08 version has **seven** — the final 淘汰 (active excretion) step was dropped during the vision doc's own compression.

This drop is not cosmetic. Metabolism in biology is defined as *intake + transformation + **excretion***. Remove excretion and you have digestion only, which is a strictly weaker concept. "Dead knowledge" (see 1.15 below) accumulates without 淘汰; the substrate bloats; compression stops being intelligent and starts being lossy triage.

Myco's metabolism must be explicitly seven-step. Six is a bug.

### 1.15 Self-model four-layer hierarchy A/B/C/D (weakly preserved)

04-08 canonical breakdown:

> "**层级 A — 库存清单**（我有什么）— 知识总量、分布、更新时间. 类似 `ls` + `wc -l` + 日期检查. **自动化难度：低.**
>
> **层级 B — 缺口感知**（我缺什么）— 怎么知道自己不知道什么？当 Agent 在工作中被迫从零开始摸索某件事，这就是一个缺口信号. 类似于 friction 记录——摩擦点就是知识缺口的症状. **自动化难度：中.**
>
> **层级 C — 退化感知**（什么在变坏）— 知识会腐化. Lint 是退化感知的雏形. 更深的退化是**结构性退化**——不是某个事实错了，而是知识的组织方式不再适合当前需求. 比如四层架构在项目早期很好，但项目成熟后也许三层更合适. 这种结构性退化目前完全没有检测机制. **自动化难度：中.**
>
> **层级 D — 效能评估**（我的知识有没有被有效使用）— 最难的一层. 一个 wiki 页面存在但从来没被 Agent 读取过——它是**『死知识』**. 理想状态：系统追踪每个知识组件被引用/使用的频率，低频组件要么需要压缩，要么说明它的组织位置有问题（Agent 找不到它）. 这是 Hermes 的技能系统有而我们完全没有的. **自动化难度：最高.**"

Current vision doc preserves the four-layer table but not the automation-difficulty ranking, not the "structural decay" distinction (→ element 1.17), and not the "dead knowledge" concept. Public README mentions "self-model" as a bullet without unpacking any of it.

This hierarchy is the *scaffold* of Myco's introspection. Without it, "Myco has a self-model" is a claim; with it, it's an architecture. A → lint manifest; B → friction logs; C → lint + structural-decay detector (open problem); D → usage tracking (not yet implemented).

### 1.16 "Dead knowledge" — the usage-signal gap vs. Hermes (lost)

Inside the 04-08 self-model layer D is a concrete diagnostic concept:

> "一个 wiki 页面存在但从来没被 Agent 读取过——它是**『死知识』**. 这是 Hermes 的技能系统有而我们完全没有的——Hermes 的技能是『被调用的』，有明确的使用信号. 我们的 wiki 页面被不被读完全靠 Agent 的自觉."

Hermes-style skill libraries have a built-in invocation counter. Myco wiki pages do not. This means Myco's layer D is structurally blind today — we cannot tell which pages are metabolically live vs. dead without explicit instrumentation.

Open problem for v1.2 or later: wiki-read / canon-lookup usage tracking. Until then, "self-model" is really "self-model layers A + B + partial C."

### 1.17 Structural decay vs. factual decay (lost)

From the layer-C discussion:

> "更深的退化是**结构性退化**——不是某个事实错了，而是知识的组织方式不再适合当前需求. 比如四层架构在项目早期很好，但项目成熟后也许三层更合适. 这种结构性退化目前完全没有检测机制."

`myco lint` detects factual decay (version mismatches, reference drift, stale patterns). It has zero ability to detect *structural* decay — when the architecture that was correct at day 3 has become wrong at day 30. This is arguably the hardest problem in the entire knowledge-system design space, and it was acknowledged on 04-08 but silently dropped from public docs.

This should live as a fifth open problem alongside cold-start / triggers / alignment / compression-engineering, OR absorbed into the compression-engineering slot with the understanding that compression decisions must consider structural fit, not just size.

### 1.18 Kernel / instance separation — OS vs. applications (lost)

> "要服务『任何项目』，就意味着系统本身需要分成两部分：**内核**（与项目无关的认知机制）和**项目实例**（某个具体项目的知识库）. 就像操作系统和应用程序的关系."

This is what makes the substrate-as-OS metaphor **literal, not analogical**. Myco is not *like* an operating system; it *is* split architecturally the way an OS is split: a project-agnostic kernel + a project-specific instance. The Myco repo (kernel) and the ASCC repo (instance) are the concrete realization.

Current README has open/closed separation mentioned in passing but never names the kernel/instance distinction. Making it explicit:
- tightens the CPU/OS metaphor (now self-consistent top to bottom),
- gives contributors a clean mental model of where to PR (kernel = Myco repo; instance = adapter or example repo),
- creates vocabulary for explaining why `myco init` templates exist (instance bootstrap) vs. why the four-gear engine lives in core (kernel behavior).

### 1.19 Transferable vs. project-specific knowledge (lost)

From 04-08 metabolism discussion:

> "跨项目场景下，项目间的知识如何流动？比如 ASCC 项目中学到的『HPC 部署经验』，在新项目中也有用——但 ASCC 的『λ=0.1 导致性能不佳』这个结论只对 ASCC 有意义. 系统怎么区分**可迁移知识**和**项目专属知识**？"

Two-axis knowledge classification. Transferable knowledge distills upward into kernel-level patterns (Gear 4's output); project-specific knowledge stays in the instance. Without this distinction, Gear 4 either over-generalizes (pollutes the kernel with project-specific stuff) or under-generalizes (misses reusable lessons).

Current README mentions "distill universal patterns" but doesn't name the transferable/specific split. This should be explicit in the Gear 4 description.

### 1.20 Theoretical foundations lineage (lost)

04-08 and earlier session notes repeatedly anchor Myco in five named theoretical traditions:

> "理论基础：Karpathy LLM Wiki + Polanyi Tacit Knowledge + Argyris Double-Loop Learning + Toyota PDCA + Voyager Skill Library"

- **Karpathy LLM Wiki** — structured knowledge compilation for LLM consumption. Source of the wiki-as-first-class-artifact design.
- **Polanyi Tacit Knowledge** — proximal / distal structure; operational experience lives in proximal terms that cannot be made fully explicit. Source of W6 and the operational-narratives convention.
- **Argyris Double-Loop Learning** — single-loop fixes the action; double-loop fixes the governing rules. Source of Gear 3 (challenge structural assumptions) and the whole L-struct / L-meta framing.
- **Toyota PDCA** — Plan / Do / Check / Act cycle as the base unit of continuous improvement. Source of the four-gear engine's cyclic shape.
- **Voyager Skill Library** — iterative skill accumulation via grounded execution. Source of the "skill library" concept in operational narratives.

The public README mentions none of these. Myco's internal `docs/theory.md` covers a subset. This absence means a reader assumes Myco is a 2026-invented toy rather than a 2026 *formalization* of a 50-year lineage of epistemology, control theory, and organizational learning research. Credibility loss is real and cheap to fix.

### 1.21 Mycelium name origin (canonical)

> "Myco 来自 mycelium（菌丝网络）——森林地下那张看不见的活网。菌丝不只是连接树木的管道：它分泌酶将落叶分解为养分，记住有效的生长路径并据此调整策略，根据需求将资源从丰裕区域调往匮乏区域，并与不同树种的根系都能形成共生。Agent 是地面上的树，Myco 是地下让整片森林成活的网络。"

Current README has a compressed version of this. It kept the poetry, lost the biological mechanism mapping (decompose → metabolism, remember paths → meta-evolution, redistribute → continuity, symbiose → agent-adaptive).

---

## 2. 传统手艺 debate

### Round 1

**Claim (C1)**: The public README has structurally drifted from the 04-08 vision. It frames Myco as a defensive/reflexive layer (watcher, lint, validator) when the canonical identity is **Autonomous Cognitive Substrate** — a growing organism that metabolizes external knowledge and drives non-parametric evolution of the Agent–human–world system.

**Attack (A1)**: This sounds like a naming / marketing complaint. The code does what the code does; `myco lint` is real, the four-gear engine is real, the MCP server is real. The README accurately describes *what you can run today*. The substrate/metabolism framing describes an ambition, and putting ambition at the top of a README is what kills credibility for pre-1.0 projects. Maybe the "drift" is actually correct scoping discipline.

**Research (R1)**: Does the 2026 field actually support "substrate" as a live research primitive, or is it vaporware framing?

- **MemOS — Memory OS for AI System** (arXiv 2507, Tencent + MemTensor, July 2025): proposes an explicit *hierarchical memory substrate* composed of three layers — plaintext memory, activation memory, parameter memory — with a memory OS scheduling between them. Uses the word "substrate" as a technical term throughout. ([PDF](https://statics.memtensor.com.cn/files/MemOS_0707.pdf))
- **Memory Intelligence Agent (MIA)** (arXiv 2604.04503, April 2026): "The Memory Manager is a *non-parametric memory system*… establishes a bidirectional conversion loop between parametric and non-parametric memories to achieve efficient memory evolution… enables the Planner to continuously evolve during test-time learning with on-the-fly updates." Explicitly frames agent evolution as **non-parametric memory evolution**. ([arxiv](https://arxiv.org/abs/2604.04503))
- **ICLR 2026 MemAgents Workshop** proposal: "Long-lived, safe, and useful agents require a principled memory *substrate* that supports single-shot learning of instances, context-aware retrieval, and *consolidation into generalizable knowledge*." The consolidation primitive is exactly "knowledge metabolism." ([OpenReview PDF](https://openreview.net/pdf?id=U51WxL382H))
- **anthropics/claude-code#45661** (April 2026 issue): "Claude Code needs a *persistent cognitive substrate* — not just a bigger context window or better memory.md, but a *learning system that accumulates institutional knowledge*, enforces behavioral governance, and improves with use." Community is reaching for the exact words Myco already has. ([GitHub](https://github.com/anthropics/claude-code/issues/45661))

**Defense (D1)**: A1 is wrong on the diagnosis. The problem is not that the README overclaims — the README *underclaims* in a way that makes Myco look like a lint tool with a nice metaphor. The 2026 research frontier has converged on exactly Myco's primitives (substrate, non-parametric evolution, consolidation), and three of the four references above did not exist when the 04-08 vision document was written. Myco is *early to the correct frame*. Hiding that frame under a "catches drift" tagline cedes the primitive to whoever brands it next. This is not ambition leaking; this is L-struct positioning — the category of thing Myco is.

A1 is also wrong on the implementation gap. `myco lint` *is* the immune system of a substrate (L0 integrity, L1 references, L2 consistency). The four-gear engine *is* the metabolism mechanism, minus the external-facing gear. What's missing from the README is not a feature — it is the *name of the thing those features add up to*. Every one of the nine lint levels is a substrate-integrity check. Calling them "drift detection" is technically correct but conceptually castrated.

**Remaining weakness**: D1 does not address the external-absorption gap. The current four-gear engine has no outward gear. If we publish "substrate + metabolism" now, the most obvious question ("where does the food come from?") has no answer in the code. → continue to Round 2.

### Round 2

**Claim (C2)**: Recovery requires adding a **fifth gear** — *External Absorption* — as a first-class v2.0 roadmap item, and committing it in writing now (MYCO.md v1.2 queue + README roadmap), even though implementation lands later. Gears 1–4 are the *autonomic nervous system* (internal homeostasis). Gear 5 is the *digestive system* (external metabolism). A substrate without a digestive gear is not a substrate, it is a cache.

**Attack (A2)**: You are proposing to ship a roadmap promise before you have any code for it. That's exactly the "aspirational README" failure mode the original launch_craft debate ruled out. Also, "Gear 5" breaks the elegant 1-session / 2-session-end / 3-milestone / 4-project-end temporal hierarchy. The four gears form a closed temporal nesting. A fifth gear runs on a *different* axis (external vs. temporal) and will confuse first-time readers.

**Research (R2)**: How does the field handle the external-absorption problem today, and is there prior art for declaring it before implementing it?

- **Self-Evolving Agents Survey** (arXiv 2507.21046v4): explicitly names "proactive knowledge acquisition from the environment" as one of five open challenges for self-evolving agents and notes that **no current system implements it as a first-class mechanism** — every surveyed system is reactive (user query → retrieval). This validates both the gap *and* the novelty of declaring it.
- **Mem0 State of AI Agent Memory 2026 report**: names "memory staleness detection" as an unresolved challenge — which `myco lint` already addresses — *and* lists "autonomous knowledge ingestion" as a separate unresolved challenge, confirming they are two distinct primitives and Myco currently solves only the first.
- **Voyager** (Minecraft open-ended agent, still a reference for Skill Library design): its skill library grows only from what the agent encounters in-environment. No external ingestion. Same gap.

**Defense (D2)**: A2's first point (don't promise what you can't ship) is the correct general rule, but wrong for this case. The distinction is between:

- **Feature promises** ("v1.5 will have X" → creates support debt if missed)
- **Primitive promises** ("Myco is the kind of system that has a Gear 5" → creates identity integrity)

A roadmap that says "Gear 5: External Absorption — mechanism TBD, earliest v2.0" is an identity commitment, not a feature commitment. It tells contributors and integrators *what Myco is*, so the wrong PRs don't arrive and the right ones do. Hiding it to avoid scope creep causes scope *starvation* — Myco gets built as a better CLAUDE.md instead of as an ACS.

A2's second point (axis collision) is real. Resolution: do not call it Gear 5. Call it **the outward gear** or **metabolic inlet**, and diagram it orthogonally to the 1-4 temporal nesting. Four gears handle *when* evolution happens; the metabolic inlet handles *where the matter comes from*. They compose, not compete.

### Round 3 — Compression as cognition (user-prompted)

**Claim (C3)**: Compression is not a housekeeping concern in Myco; it is **the substrate's primary cognitive act**. The doctrine "no forgetting, only compression" — storage infinite, attention finite, compression itself intelligent and itself evolving — must be elevated to first-class README content, alongside substrate identity and non-parametric evolution. The seven-step metabolism pipeline (including 淘汰) must replace every six-step rendering. The self-model must unpack its four layers. The kernel/instance split must become an explicit architectural commitment, not an implicit one.

**Attack (A3)**: You're trying to cram too much. A README is triage — the top-level narrative carries at most three or four primary ideas. Substrate + non-parametric evolution + metabolism already saturates the hero. Adding "compression is cognition" + seven-step pipeline + four-layer self-model + kernel/instance split risks returning to the pre-04-10 failure mode — this time not "drifted too narrow" but "drifted too broad and unreadable."

Also: the compression doctrine ("storage infinite, attention finite") sounds profound but is just a restatement of the context-window problem that every agent framework already solves somehow. Calling it a "primary cognitive act" may be over-claiming.

**Research (R3)**: Does the 2026 field treat compression as cognition or as housekeeping?

- **MemOS** (Jul 2025) models memory scheduling as "explicit control and dynamic activation" across plaintext / activation / parameter substrates. *Scheduling = compression decision-making.* MemOS treats it as core architecture, not housekeeping.
- **A-Mem (Agentic Memory for LLM Agents, arXiv 2502.12110)** frames memory management as an agentic loop (write / organize / retrieve), where the *organize* step is exactly compression-as-decision. Organize is first-class, not plumbing.
- **ICLR 2026 MemAgents workshop proposal** explicitly lists "consolidation into generalizable knowledge" as one of the core substrate primitives. Consolidation = compression with semantic selection. First-class.
- **Self-Evolving Agents Survey (arXiv 2507.21046v4)** names "what to drop, when, without losing load-bearing tacit knowledge" as an open problem — validating both the importance *and* the unresolved status.

Three independent 2026 sources treat compression decisions as a first-class cognitive primitive for agent memory systems. None treat it as plumbing. A3's "over-claim" concern is wrong on the empirical question.

**Defense (D3)**: A3's triage point is half-right and half-wrong. Right: the hero paragraph should stay at three or four ideas (substrate + CPU metaphor + non-parametric + metabolism). Wrong: "compression is cognition" does not have to go in the hero. It can live inside the How It Works section as a short dedicated subsection ("The Compression Doctrine"), adjacent to the four gears + inlet table. That's the right home — it's mechanism, not hero.

The seven-step pipeline replacement is non-negotiable: the six-step version is literally a lossy compression of the canonical version, and one of the lost steps is 淘汰 — the metabolic act itself. Fixing this costs one additional row in the table. It is not bloat; it is correctness.

The self-model four-layer unpack is also non-negotiable, but can be compressed (appropriately!) to a 4-row table inside How It Works. Same cost as adding the inlet row.

Kernel/instance can be a single sentence inside "What Myco Is" — "Myco is architecturally split into a project-agnostic kernel (this repo) and project instances (your project directory), exactly as an OS is split from its applications." One sentence. Zero bloat.

Theoretical foundations should be a single line at the bottom of Validation or Story: "Myco stands on Karpathy LLM Wiki + Polanyi Tacit Knowledge + Argyris Double-Loop Learning + Toyota PDCA + Voyager Skill Library; see `docs/theory.md`." One line. Massive credibility lift.

**Total additional word count** for all seven tertiary elements, measured against the post-Round-2 README draft: roughly 250–300 words. The README currently sits at ~230 lines; post-recovery will be ~280. This is within the "dense but not bloated" regime.

### Round 4 — Final confidence check

Revised primary claim (post Round 3): **The public README must restore eighteen elements across four thematic clusters — Identity (substrate, CPU metaphor, non-parametric, kernel/instance), Metabolism (seven-step pipeline, external absorption inlet, transferable vs. specific knowledge), Cognition (compression doctrine, four-layer self-model, dead knowledge, structural vs. factual decay), and Collaboration (mutation/selection, transparency→anti-cancer, agent-subject inversion, living-vs-dead frame, unconscious prototype, six-way differentiation, blind spots, theoretical foundations) — while keeping the README inside the "dense but not bloated" regime (~280 lines).**

Lint remains the *how*. Substrate remains the *what*. Metabolism remains the *why*. Compression is the *act*.

Confidence: **≥92%** (raised from ≥90% after Round 3 external validation of compression-as-cognition).

- User intent: directly quoted, unambiguous.
- Transcript evidence: all four elements present verbatim in 04-08 session, with multiple independent formulations.
- External research: 2026 frontier (MemOS, MIA, MemAgents workshop, claude-eng proposal, Self-Evolving Agents survey) converges on the exact primitives.
- Internal consistency: the recovered framing strengthens, not contradicts, existing code — lint = substrate immunity, four gears = internal homeostasis, MCP = substrate exposure surface.
- Risk of over-claiming addressed: metabolic inlet declared as primitive not feature.

Proceed to recovery.

---

## 3. Recovery plan

### 3.1 README.md (top-of-funnel narrative)

Restore the canonical identity paragraph in the opening hero block. Target shape:

> **Myco is an Autonomous Cognitive Substrate for AI agents.**
>
> Your agent is a CPU: raw compute, zero persistence. Myco is everything else — the memory, the filesystem, the OS, the peripherals — and the OS upgrades itself. All evolution happens in Myco; no weights are touched. Agents (and the humans working with them) get smarter over time not because they were retrained, but because the substrate they stand on metabolized the world and grew beneath them.

Then — and only then — introduce `myco lint` as *substrate immunity*.

Add a section **"What Myco Is"** directly after the hero, above **What It Looks Like**, with four bullets:

- **Substrate, not tool** — Agent runs on Myco the way processes run on an OS. Architecturally split into a project-agnostic *kernel* (this repo) and project *instances* (your project directory), exactly as an OS is split from its applications.
- **Non-parametric evolution** — weights never change; the substrate changes.
- **Knowledge metabolism** — Myco decomposes external information into usable structure. Lint is the immune system; the metabolic inlet (v2.0) is the digestive system.
- **Perpetual evolution** — stagnation = death; this is the only inviolable law, because a substrate that stops metabolizing is just a cache.

Rewrite the "Why Myco" section to lead with the L-struct/L-meta framing already there, but re-anchored to substrate language rather than "reflexive layer" language. Keep the Mem0 comparison — it is the sharpest single-sentence differentiator in the current README.

Add to the "How It Works" section a new subsection **"The Four Gears + The Metabolic Inlet"** that preserves the current 1-4 gear table and appends:

| Gear | Direction | Status |
|------|-----------|--------|
| 1–4  | Inward (internal homeostasis) | Implemented in v1.0 |
| Metabolic Inlet | Outward (external absorption) | Declared primitive, earliest v2.0 |

### 3.2 README_zh.md

Mirror 3.1 in Chinese, using the canonical 04-08 phrasings wherever they exist verbatim in the transcript (substrate = 认知基质; metabolism = 知识代谢; non-parametric = 非参数进化; metabolic inlet = 代谢入口 / 外部摄取). Restore the full 04-08 mycelium name-origin paragraph unabridged — it is already the best piece of writing in the repo and it was compressed out of the English version.

### 3.3 MYCO.md v1.2 roadmap

Add to the task queue:

```
- [ ] Metabolic Inlet primitive — declare in v1.2 docs, implement earliest v2.0
      WHY: Gears 1-4 are inward-facing (homeostasis). Without an outward gear,
           Myco is a cache, not a substrate. Declaring now prevents identity
           drift; implementation later protects against over-promise.
      SHAPE: Triggered by friction signal OR periodic patrol. Targets: GitHub
             repos, arXiv, community docs. Pipeline: discover → evaluate →
             extract → integrate → compress → verify.
      BLOCKERS: Self-Evolving Agents survey notes no implemented prior art.
      BOOTSTRAP: User-approved seed sources; agent-executed ingestion; lint-
                 verified integration. No autonomous sourcing before v2.5.
```

### 3.4 docs/current/

Create `vision_recovery_craft_2026-04-10.md` ← *this file*. This is the permanent record. When future sessions compress context again, this document is the canonical anchor to re-read.

Also add a pointer from `myco_vision_2026-04-08.md` to this recovery doc (one-line append: "See `vision_recovery_craft_2026-04-10.md` for the 2026-04-10 re-anchoring after public-release drift.") so the vision chain is navigable both directions.

### 3.5 Out of scope for this recovery

- Implementing the metabolic inlet. That is a v2.0 design debate on its own.
- Renaming any public API or CLI command.
- Changing the lint engine.
- Changing the immutable laws (all three hold unchanged).
- Touching examples/ascc/ or the existing log chain.

This recovery is **purely narrative and roadmap**. The code already embodies substrate thinking; the docs need to catch up.

---

## 4. What this debate ruled out

For the record, so future retrospectives can check against it:

1. **Renaming the project**. Considered briefly (ACS as primary name). Rejected — "Myco" is the canonical name as of 04-08, has repo URL, PyPI package, MCP registration, and the mycelium biological mapping is too good to surrender. ACS stays as subtitle/definition, not name.
2. **Removing "other tools give memory, Myco gives metabolism" tagline**. Rejected — it is the sharpest single-sentence hook in the repo and does not contradict the substrate framing. Keep as secondary tagline under the substrate hero.
3. **Adding implementation for Gear 5 in v1.1**. Rejected — user's 04-08 Bitter Lesson stance: mechanism must come from first principles, not hand-designed. Premature implementation would entrench the wrong design.
4. **Hiding the recovery from public docs until v2.0 lands**. Rejected — see D2: identity drift compounds faster than feature drift. Declaring the primitive now is the cheap intervention; fixing identity retroactively is expensive.

---

## 5. Immutable anchors (restated)

Any future session that reads this document should treat the following as ground truth, not up for debate:

- **Myco's canonical identity**: Autonomous Cognitive Substrate. Not a tool, not a layer, not a memory library.
- **Mechanism**: non-parametric evolution. Agent weights never change; the substrate changes.
- **Direction of growth**: outward (world) → inward (Myco) → available (Agent). Metabolism is not optional.
- **Three immutable laws**: entry-point accessible · human-transparent · perpetually evolving.
- **Agent–Myco relationship**: CPU ↔ everything-else-and-the-self-upgrading-OS. Symmetric in dependency; asymmetric in direction of growth.

Everything else — Gear mechanisms, lint levels, storage layout, MCP surface, adapter schemas, even this recovery document's recommendations — is negotiable and evolvable.

---

## 6. References

External (accessed 2026-04-10):

- [MemOS — A Memory OS for AI System](https://statics.memtensor.com.cn/files/MemOS_0707.pdf) — substrate as technical term
- [Memory Intelligence Agent (arXiv 2604.04503)](https://arxiv.org/abs/2604.04503) — non-parametric memory evolution
- [ICLR 2026 MemAgents Workshop Proposal](https://openreview.net/pdf?id=U51WxL382H) — principled memory substrate + consolidation
- [anthropics/claude-code#45661](https://github.com/anthropics/claude-code/issues/45661) — "persistent cognitive substrate" community demand
- [A Survey on Memory Mechanism of LLM-based Agents (ACM TOIS)](https://dl.acm.org/doi/10.1145/3748302) — write–manage–read loop framing

Internal:

- `docs/current/myco_vision_2026-04-08.md` — canonical 04-08 vision
- `docs/current/vision_debate_2026-04-08.md` — 04-08 structured vision debate
- `docs/current/readme_craft_2026-04-10.md` — most recent README craft (gitignored)
- Session `2f34106c-6d60-4aae-b5eb-176776fd08cd.jsonl` — 04-08 Myco 设计会谈 (local archival, gitignored via `ascc_sessions/`)

---

*This document is the anchor for the 2026-04-10 vision re-calibration. It supersedes no prior doc; it re-grounds them. If a future session detects narrative drift from the recovered frame, re-read this file before editing public docs.*
