---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Vision Re-Audit — Doctrine ↔ Implementation Reconciliation (post Wave 25)

> **Evidence bundle**: this craft's source evidence lives in notes/n\_20260412T\*\*\*\_\*\*\*\*.md (eaten alongside this craft's landing; tagged `wave26-seed`, `vision-reaudit`, `forage-digest`).
>
> **Parent anchor document**: `docs/primordia/vision_recovery_craft_2026-04-10.md` (Wave 10, re-read in full as Round 1 input). This craft does NOT supersede the Wave 10 recovery — it *reconciles* the 8 anchors with the 15 waves of implementation state (W11–W25) that have accumulated since.
>
> **Supersedes**: `docs/primordia/hermes_absorption_craft_2026-04-12.md §4.1 D3` (the "friction-driven Wave 26+ ordering" decision). New D3 text lives in §3 below.

## 0. Problem definition

After Wave 25 landed (v0.24.0, tests infrastructure seed), the kernel-agent and the
user engaged in a methodological dialogue that exposed a fundamental incompatibility
between (a) Wave 25 craft §4.1 D3 as written and (b) the user's explicitly stated
top-down work methodology:

> *"我是那种自上而下的人 —— 从抽象阶梯的上方开始实现，直至落实到具体实现细节.
> 只有在高抽象层面确认清楚了，逐步往下理顺实现，才能够更好的实现任何事情."*

Wave 25 craft §4.1 D3 reads:

> *"D3 — Wave 26+ ordering is friction-driven, NOT schedule-driven. The Wave 25
> test suite will catch bugs. The first caught bug determines Wave 26's subject.
> The catalog's T1 items (atomic writes, error taxonomy, structured logging,
> hot-gate compression) are candidates but not commitments."*

"Friction-driven" is a **bottom-up** commitment. It says: let the implementation
surface decide which anchor gets worked on next. "Top-down" from the user's
methodology statement says: let the doctrine decide which anchor gets worked on
next. These are not compatible — one must supersede the other. The kernel-agent
(me) chose friction-driven in Wave 25 craft Round 3 not because the user had
asked for it, but as a safety mechanism against scope creep. That reasoning was
partially right (Round 2's capacity attack is real) but wrong about the conclusion
(capacity is about intra-wave scope, not inter-wave ordering).

However, before simply replacing D3 with a new top-down ordering derived from
the 8 identity anchors in `MYCO.md §身份锚点`, a second question arose: **are
the 8 anchors themselves still right?** They were re-audited at Wave 10
(`vision_recovery_craft_2026-04-10.md`), before most of the substrate's current
implementation existed. Since Wave 10, the following load-bearing waves landed:

- **Wave 11** — L15 craft reflex + hunger signal `craft_reflex_missing` (contract v0.10.0)
- **Wave 12** — Craft reflex arc upgraded LOW → HIGH; agent-autonomous craft obligation (v0.11.0)
- **Wave 13** — Boot Reflex Arc (contract_drift, raw_backlog, boot hunger wiring; v0.12.0)
- **Wave 14** — Session-End Reflex Arc (gear2/gear4 drift; v0.13.0)
- **Wave 15** — L13 body schema enforcement (v0.14.0)
- **Wave 16** — Upstream scan timestamp write path (v0.15.0)
- **Wave 17** — Boot brief injector + `upstream_scan_stale` reader (v0.16.0)
- **Wave 18** — L15 surface expansion + git hook installer + **D-layer dead_knowledge seed** (v0.17.0)
- **Wave 19** — `myco correct` self-correction shortcut (v0.18.0)
- **Wave 20** — Silent-fail elimination: grandfather ceiling + strict project-dir (v0.19.0)
- **Wave 21** — Observability integrity: L16 brief freshness + `myco view --next-raw` (v0.20.0)
- **Wave 22** — Primordia compression workflow + W13 principle (v0.21.0)
- **Wave 23** — Pre-commit hook blocking-path dogfood + opt-in pytest gate (v0.22.0)
- **Wave 24** — L17 Contract Drift lint (v0.23.0)
- **Wave 25** — Tests infrastructure seed (v0.24.0)

If the 8 anchors' *wording* has drifted out of sync with what these 15 waves
actually built, then deriving Wave 27+ ordering from the current anchors would
commit to an ordering based on 15-wave-old state.

**The problem this craft must solve**:

1. Re-audit each of the 8 anchors against the **current** implementation state,
   identifying any wording that has silently become stale.
2. Produce a dependency graph between anchors so implementation ordering can be
   derived top-down rather than bottom-up.
3. Formally supersede Wave 25 D3 with a new ordering discipline.
4. Lock Wave 27's scope so the next wave has a clear, defensible subject.

The outcome determines everything downstream. If the anchors are stable, Wave 26
lands as an exploration-class craft. If the anchors need refinement (even minor),
this upgrades to kernel_contract class with a v0.24.0 → v0.25.0 contract bump.

## 1. Round 1 — Per-anchor audit

Each of the 8 anchors from `MYCO.md §身份锚点` is quoted verbatim and traced to
its current implementation (code path + lint dimension + notes lifecycle stage).
Scoring: `doctrine_clarity` (wording ambiguity), `implementation_coverage`
(0.0–1.0), `gap_type` (wiring / research / structural / non-portable).

### 1.1 Anchor #1 — 基质 vs 工具

> *"Myco 是基质（substrate），不是工具。Agent 运行在 Myco 上，不是 Agent 使用 Myco。
> 架构上：项目无关的**内核**（本仓库）+ 项目**实例**（你的项目目录），正如 OS 与应用的关系。"*

**Implementation trace**:
- Kernel-instance split: realized via `_canon.yaml::system.upstream_channels` class_x/y/z + `src/myco/templates/` + Upstream Protocol v1.0 (`docs/agent_protocol.md §8`)
- Substrate reliability: tests/ infrastructure landed in Wave 25 (`tests/conftest.py::_isolate_myco_project`) — regression-testable for the first time
- Write surface discipline: L11 `lint_write_surface` (`src/myco/lint.py`) enforces the whitelist
- Per-instance verification: ASCC has been running as the downstream instance since Wave 9

**Drift since Wave 10**: none in wording. The anchor's claim was true at Wave 10 and is strictly more true after Wave 25 (the substrate now carries the machinery to *detect* its own tool-regressions via pytest). No refinement needed.

**Score**:
- doctrine_clarity: high (unambiguous, well-defined boundary)
- implementation_coverage: **0.72** (substantial, but substrate reliability has 7 uncovered holes per `hermes_absorption_craft §0` — no atomic writes except 1 site, no file locking, no error taxonomy, no structured logging, no command registry, no doctor, no release notes per-wave)
- gap_type: **wiring** (known patterns, known gaps, enumerable fixes)

### 1.2 Anchor #2 — 非参数进化

> *"Agent 权重永不改动，所有学习在基质里（md/yaml/目录结构）。"*

**Implementation trace**:
- Non-parametric learning surfaces: notes/\*.md lifecycle (raw → integrated/excreted), docs/primordia/\*\_craft\_\*.md debate record, `_canon.yaml` schema evolution, `log.md` append-only history
- Self-rewriting rulebook: L0–L17 lint dimensions (18 total), each defined in `src/myco/lint.py` as Python code — itself in the substrate
- Agent-autonomous mutation: Wave 12 `craft_autonomy_craft` upgraded L15 reflex severity LOW → HIGH, making craft an agent-autonomous obligation rather than advisory

**Drift since Wave 10**: none in wording. Wave 12 materially strengthened the anchor by making agent-autonomous mutation a *reflex* (not a voluntary act). The anchor language ("所有学习在基质里") already covered this, but the implementation arc added real teeth.

**Score**:
- doctrine_clarity: high
- implementation_coverage: **0.85** (architecturally in place; verification gap is that "evolution produces useful evolution" has not been empirically tested over long time spans — only one real agent-autonomous craft so far, which is this one + Wave 25's absorption craft)
- gap_type: **research** (requires long-run evidence from multiple instances)

### 1.3 Anchor #3 — 代谢 + 七步管道

> *"齿轮 1-4 是自主神经系统（内向稳态）；代谢入口是消化系统（外向摄取，v2.0 原语）。
> 完整管道：发现→评估→萃取→整合→压缩→验证→**淘汰**。没有第七步就不是代谢，是消化。"*

**Implementation trace**:
- **Step 1 (发现)**: `myco eat` + `myco forage add` CLI verbs → present
- **Step 2 (评估)**: implicit, no verb, no state machine. Agent judgment at `myco digest` time
- **Step 3 (萃取)**: state transition `raw → extracted` via `myco digest --to extracted` — NO dedicated verb
- **Step 4 (整合)**: state transition `raw/extracted → integrated` via `myco digest --to integrated` — NO dedicated verb
- **Step 5 (压缩)**: NO verb, NO state, NO scheduled pass. The only compression that exists is (a) `docs/primordia/` COMPILED/SUPERSEDED state machine (Wave 22 W13 principle) and (b) the manual `scripts/compress_original.py` batch tool. Neither is a substrate-level compress operation on notes/\*.md.
- **Step 6 (验证)**: `myco lint` (L0–L17) ✅ present
- **Step 7 (淘汰)**: `myco digest --excrete REASON` ✅ present with mandatory audit trail

Gears 1-4 are the internal nervous system (partial; §evolution_engine.md). Metabolic Inlet (outward gear) is declared but unbuilt (`docs/open_problems.md §1-4` register 4 distinct sub-problems).

**Drift since Wave 10**: **significant**. Wave 10 stated "没有第七步就不是代谢，是消化" — a strong claim about pipeline completeness. But today's implementation is missing verbs for **steps 2, 3, 4, 5** (all of the middle). The pipeline has mouth (eat) and anus (excrete) but the digestive tract between them is vestigial — status flips without dedicated operations. The anchor's language makes it sound like only step 7 is load-bearing, when in fact **step 5 (压缩)** is where the most doctrine weight sits (cross-reference anchor #4).

**Refinement needed**: The anchor should explicitly call out that steps 2-5 are currently vestigial, not just step 7. This is a **scope clarification**, not a semantic change — the anchor's intent is preserved; its honesty about current state is restored.

**Proposed refinement** (append at end of anchor #3):
> *"今天的 Myco 在步骤 1 (eat/forage)、步骤 6 (lint)、步骤 7 (digest --excrete) 有专属动词；步骤 2-5（评估/萃取/整合/压缩）只是状态标签或缺席。消化道中段是 vestigial。"*

**Score**:
- doctrine_clarity: **medium** (wording suggests completeness; reality is 3/7 steps have verbs)
- implementation_coverage: **0.43** (3/7 steps × various partials)
- gap_type: **structural** (need new verbs + new state machine entries)

### 1.4 Anchor #4 — 压缩即认知

> *"存储无限，注意力有限。『不遗忘，只压缩』是 doctrine 不是工程细节 —— 压缩决策是
> 基质的首要认知行为。三条判据：频率 · 时效 · 排他性。压缩是 Agent-adaptive 的
> （32K vs 200K 策略不同），压缩策略本身也进化。"*

**Implementation trace**:
- Reverse compression (excretion): ✅ `notes_schema.excrete_reason` required field + L10 lint + `digest --excrete` audit trail
- Forward compression (extracted synthesis): ❌ **nothing**. There is no operation that takes N raw notes and produces 1 extracted note referencing them. Agents do this manually when they feel like it.
- Frequency criterion: seeded via `view_count` (Wave 18 v0.4.0) — read path is wired (`record_view()`), but no compression uses it yet
- Temporal criterion: seeded via `dead_knowledge_threshold_days` (Wave 18) — used by `myco hunger` to report dead knowledge, but no compression acts on the signal
- Exclusivity criterion: NOT seeded anywhere. No wiki page deduplication, no cross-reference graph, no "already-known-to-this-Agent-type" filter
- Agent-adaptive: NOT implemented. No 32K-vs-200K strategy switching

**Drift since Wave 10**: **none in wording, substantial in implementation urgency**. Wave 10 named compression as the "primary cognitive act". The anchor's `compression_discipline_maturity = 0.40` in MYCO.md §指标面板 is the self-reported acknowledgment. Since Wave 10 landed, 15 waves have passed and zero of them touched forward compression. The gap has widened relative to the rest of the substrate — the **most doctrine-weighted anchor has the lowest implementation coverage**.

**Score**:
- doctrine_clarity: high (the wording is clear and loaded with meaning)
- implementation_coverage: **0.35** (excrete reason + D-layer seed for frequency/temporal criteria; forward compression entirely absent)
- gap_type: **structural + research** (need new verb `myco compress`, need to design the unit-of-compression, need to design the audit trail, need to decide triggers)

### 1.5 Anchor #5 — 四层自我模型

> *"A 库存 · B 缺口 · C 退化（仅事实性，结构性退化是开放问题）· D 效能（『死知识』追踪，未实现）。
> 今天 Myco 实现 A+B+partial C。"*

**Implementation trace**:
- **A inventory**: ✅ `myco view` (list/single-note/tag modes) + `compute_hunger_report` totals + forage manifest + `docs/primordia/` index
- **B gap**: ✅ `myco hunger` reports `raw_backlog`, `stale_raw`, `upstream_inbox_pressure`, `notes_digestion_pressure`, `forage_backlog_pressure`, `structural_bloat`
- **C factual decay**: ✅ `myco lint` L2 stale_patterns, L3 orphans, L17 contract_drift, L16 boot_brief_freshness — but all operate on static invariants
- **C structural decay**: ❌ registered in `docs/open_problems.md §5`, no metric proposed
- **D dead_knowledge**: ✅ **SURPRISE — more complete than anchor wording suggests**
  - `record_view()` at `src/myco/notes.py:340-368` wired into `run_view()` single-note mode
  - `compute_hunger_report()` computes dead_knowledge signal from 5 conditions (terminal status + age + last_touched + last_viewed_at + view_count < 2)
  - `_canon.yaml::notes_schema.dead_knowledge_threshold_days = 30` (configurable)
  - `_canon.yaml::notes_schema.terminal_statuses = [extracted, integrated]`
  - `_canon.yaml::notes_schema.optional_fields = [view_count, last_viewed_at]` L10-recognized
  - Wave 18 craft: `docs/primordia/archive/dead_knowledge_seed_craft_2026-04-11.md` (v1.4.0 landed)

**Drift since Wave 10**: **major drift in #5 wording**. The anchor currently says "D 效能（『死知识』追踪，未实现）" and "今天 Myco 实现 A+B+partial C". **Both clauses are factually wrong**. Wave 18 landed a working D-layer minimum seed. The hunger signal fires and the frontmatter fields are written by `record_view()`. What's still missing from full D-layer is: (a) view audit log (who read what in what context), (b) cross-reference graph, (c) adaptive threshold, (d) automatic excretion workflow. These are residuals, not the core D-layer.

**Refinement needed**: Update wording to "D 效能：**dead_knowledge 最小种子已落（v1.4.0）** — `record_view()` + hunger signal + 5-condition detection接通；完整 D 层仍需 view 审计日志 + cross-ref graph + 自适应阈值 + 自动淘汰工作流。今天 Myco 实现 **A + B + partial C + D-seed**。"

**Score**:
- doctrine_clarity: **low** (anchor text is factually wrong about D-layer status)
- implementation_coverage: **A=1.0, B=0.85, C factual=1.0 / structural=0, D=0.45 (seed not full)** — aggregate ~0.66
- gap_type: **wiring (for C structural) + research (for full D)**

### 1.6 Anchor #6 — 人机协作 (mutation-selection + transparency + perpetual evolution)

> *"系统做变异（mutation），人类做选择（selection）。透明性是选择压力的前提，所以不可变 ——
> 没透明就没选择压力，就会癌变。永恒进化（Perpetual Evolution）是三条不可变律之一：
> 停滞即死，停止代谢的基质会退化为静态缓存。"*

**Implementation trace**:
- Mutation channel: Wave 12 agent-autonomous craft reflex arc (`docs/craft_protocol.md §3.1`)
- Selection channel: git commit review by human + `log.md` append-only + `docs/open_problems.md` self-registration
- Transparency mechanism: every craft in git, every note in git, every decision linked via craft_reference
- Perpetual evolution immutable law: `_canon.yaml::system.vision_anchors.groups` includes `perpetual-evolution` group → L9 lint enforces presence in public-facing files

**Drift since Wave 10**: none in wording. Wave 12 strengthened the mutation side. The selection side is still single-point (user only) — this is an acknowledged structural weakness but not anchor drift.

**Score**:
- doctrine_clarity: high
- implementation_coverage: **0.70** (mutation fully wired; selection is single-user; transparency is git-based but git-log reading is voluntary)
- gap_type: **structural** (need more selection pressure sources — automated tests as selection are a start, but most selection still depends on human audit)

### 1.7 Anchor #7 — 理论血统

> *"Karpathy LLM Wiki + Polanyi Tacit + Argyris Double-Loop + Toyota PDCA + Voyager Skill Library.
> 详见 `docs/theory.md`。"*

**Implementation trace**:
- `docs/theory.md` — 128 lines, covers the five sources
- `README.md` credibility anchor line (Wave 10 recovery)

**Drift since Wave 10**: none. This is a stable anchor, not under implementation pressure.

**Score**:
- doctrine_clarity: high
- implementation_coverage: **1.0** (fully documented, nothing more to build)
- gap_type: **none** (anchor is a citation anchor, not an implementation target)

### 1.8 Anchor #8 — 永久锚点文档

> *"详细愿景恢复记录见 `docs/primordia/vision_recovery_craft_2026-04-10.md` ——
> 这是防漂移的永久锚点，18 项丢失元素全部在里面有原文引证。
> **任何一次上下文压缩后第一件事是重读它。**"*

**Implementation trace**:
- File exists: `docs/primordia/vision_recovery_craft_2026-04-10.md` (503 lines, read in full as Round 1 input to this craft)
- Cross-references from MYCO.md + docs/theory.md + docs/vision.md
- L9 vision_anchors lint uses the 12 groups declared in the craft's §7

**Drift since Wave 10**: none in the anchor itself. But the anchor's *claim* that vision_recovery is "the permanent anchor" now has a sibling: **this very craft (Wave 26) is now also a permanent anchor**, specifically the anchor for post-implementation-maturity re-reconciliation. The Wave 10 document is still authoritative for the 18 elements (what was lost); this Wave 26 document is authoritative for the 8-anchor ↔ implementation reconciliation (what has been built since).

**Refinement needed**: Add a cross-reference from anchor #8 pointing to this Wave 26 craft as the "post-Wave-25 reconciliation anchor". Append: *"— 补充锚点：`docs/primordia/vision_reaudit_craft_2026-04-12.md` 记录 Wave 26 post-impl doctrine reconciliation，服务于 'doctrine ↔ implementation 对齐' 维度."*

**Score**:
- doctrine_clarity: high
- implementation_coverage: **1.0** (file exists, L9 lint enforces anchor presence, cross-references live)
- gap_type: **none** (documentation-only)

### 1.9 Audit summary table

| # | Anchor | doctrine_clarity | impl_coverage | gap_type | refinement? |
|---|--------|------------------|---------------|----------|-------------|
| 1 | 基质 vs 工具 | high | 0.72 | wiring | no |
| 2 | 非参数进化 | high | 0.85 | research | no |
| 3 | 代谢 + 七步管道 | **medium** | **0.43** | **structural** | **yes (steps 2-5 vestigial)** |
| 4 | 压缩即认知 | high | **0.35** | structural + research | no (wording is right; impl is the gap) |
| 5 | 四层自我模型 | **low** | 0.66 | wiring + research | **yes (D-seed landed, wording stale)** |
| 6 | 人机协作 | high | 0.70 | structural | no |
| 7 | 理论血统 | high | 1.0 | none | no |
| 8 | 永久锚点文档 | high | 1.0 | none | **yes (add Wave 26 cross-reference)** |

**Three anchors need refinement**: #3 (scope clarification on vestigial steps), #5 (D-seed status correction), #8 (new cross-reference). All three are **refinements, not replacements**. Anchor #3 adds honesty about current state; #5 corrects a factual error introduced by Wave 18 progress not being reflected; #8 adds a sibling anchor document.

**Two anchors have the lowest implementation coverage**: #3 (0.43) and #4 (0.35). These are the top candidates for Wave 27+ ordering. Note that #3 and #4 are **intertwined**: fixing #3 (adding verbs for steps 2-5) is essentially fixing #4 (the missing middle is mostly the compression step). Doing both together is natural.

**Also drifted** (minor, outside anchor text but inside MYCO.md):
- `§指标面板` row `lint_coverage_confidence` rationale says "15 维 L0-L14 全绿" — we are at L0-L17 (18 dims) + Wave 25 tests. Stale.
- `§任务队列` row 2 references contracts v1.2.0/v1.3.0/v1.4.0/v1.5.0 which are pre-Wave-8 re-baseline identifiers. Post-rebaseline the actual lands are v0.11.0/v0.13.0/v0.17.0/v0.18.0/v0.19.0/v0.20.0/v0.21.0/v0.22.0/v0.23.0/v0.24.0. The task queue row 2 should reflect this.
- `§任务 4 详述 · Metabolic Inlet` mentions "现有 14 维 lint" — stale (we have 18).

These are **§指标面板 + §任务队列 refinements**, adjacent to §身份锚点 but not the anchors themselves. They are still under the MYCO.md public_claim surface, so touching them triggers the Wave 12 craft reflex arc. This craft pre-authorizes them.

## 2. Round 2 — Dependency graph and ordering

From Round 1's coverage scores and gap_types, we can build a dependency DAG
over the 8 anchors with edges meaning "fixing anchor X is blocked on anchor Y
being in a usable state".

### 2.1 Dependency graph (anchors as nodes, edges = "needs this first")

```
Anchor #7 (理论血统) ──────────── leaf (no dependencies, already 1.0)
Anchor #8 (永久锚点文档) ──────── leaf (doc-only, already 1.0)
Anchor #2 (非参数进化) ────────── needs: #1 engineering reliability so mutation doesn't corrupt
Anchor #1 (基质 vs 工具) ──────── needs: nothing (foundational), but benefits from #6 selection pressure
Anchor #6 (人机协作) ──────────── needs: #1 (substrate reliable enough to trust as mutation log), #2 (mutation machinery)
Anchor #5 (四层自我模型) ──────── needs: #1 (storage reliability for view_count/audit log), mostly D-wiring
Anchor #3 (代谢 + 七步管道) ────── needs: #1 (step verbs need atomic writes), intertwined with #4
Anchor #4 (压缩即认知) ────────── needs: #1 (compression is multi-file mutation), #3 (step 5 is in the pipeline)
```

Topologically sorted (least dependent → most dependent):

1. **#7** (理论血统) — already 1.0, no action
2. **#8** (永久锚点文档) — already 1.0, add Wave 26 cross-ref only
3. **#1** (基质 vs 工具) — foundation, but current 0.72 is "good enough for next-wave work if we don't simultaneously tax the substrate with complex operations"
4. **#2** (非参数进化) — architecturally done, evidence-gathering
5. **#6** (人机协作) — architecturally done, evidence-gathering
6. **#5** (四层自我模型) — refinement (wording) + full-D-layer completion (long tail)
7. **#3** (代谢 + 七步管道) — structural addition (verbs for steps 2-5)
8. **#4** (压缩即认知) — structural addition (forward compression), intertwined with #3

**Observations**:

- #3 and #4 are not separable. Anchor #3 step 5 IS anchor #4's concern. Any Wave that adds forward compression necessarily fills in anchor #3's step 5, and any Wave that fixes anchor #3's middle pipeline must address compression (the heaviest step).

- #1 is "good enough to move forward" at 0.72 but "ought to be 0.85+ before shipping new doctrine verbs". The hermes absorption catalog C2 (atomic writes) is the single biggest lift — and compression is a multi-file mutation that **requires** atomic writes to be safe. So C2 becomes a natural precondition of any Wave that services #3/#4.

- #5 D-layer completion is **not urgent** post-audit. Wave 18 already seeds what matters (frequency + temporal criteria for compression). Full D-layer (view audit log, cross-ref graph, adaptive threshold, auto-excretion) is long-tail polish that should wait until compression exists and can consume the signals.

- #2 and #6 are evidence-gathering, not implementation. Every wave that lands produces evidence for these two anchors (Wave 12 reflex arc, Wave 25 tests, this Wave 26 craft). They improve monotonically without dedicated waves.

- #7 and #8 are stable. No ordering implications.

### 2.2 Attack the ordering

**Attack A**: "Why not start with #1 alone? Fix engineering reliability (hermes absorption C2–C4) first, then do doctrine work on a rock-solid base. This is the 'fix the foundation' argument."

**Defense**: Wave 25 already landed C1 (tests). One more dedicated engineering wave (C2 atomic writes as standalone) would consume an entire wave slot without serving any specific anchor, which is exactly the bottom-up trap this craft is rejecting. The top-down move is: the first doctrine wave (anchor #3/#4 service) pulls in C2 as supporting infrastructure **because it needs it**, not because "engineering must be good". This keeps each wave anchored to doctrine while still getting the engineering win. Wave 25's C1 was an exception because tests are the regression memory that **every** future wave benefits from — tests don't serve a specific anchor, they serve all future anchors.

Attack A partially lands: C2 is inevitable and important. But it should land as part of the first compression wave, not as a solo wave.

**Attack B**: "Why not start with #5 D-layer completion? It's the most concrete and measurable anchor — finish it, check a box, move on."

**Defense**: #5 D-layer completion is already in a "good enough for now" state. The seeded signals (dead_knowledge hunger) are available for compression to consume. Completing full D-layer (audit log + cross-ref graph + adaptive threshold + auto-excretion) before compression exists would be **building consumers for a producer that doesn't exist yet** — the compression operation would eventually want to use dead_knowledge signal, so if dead_knowledge is improved without a consumer, the improvements ossify in a vacuum. Completing #5 AFTER compression lands gives the full D-layer a real workload to tune against.

Attack B lands as "not yet, later". Not as "never".

**Attack C**: "Why not start with Metabolic Inlet (part of #3)? That's the biggest gap, the most doctrine-weighty, the v2.0 promise."

**Defense**: Metabolic Inlet has 4 registered open problems (`docs/open_problems.md §1-4`): cold-start, trigger signals, alignment, compression engineering. Problem #4 (compression engineering) is a **prerequisite** for Metabolic Inlet — inlet without compression = bloat spiral in days. So Metabolic Inlet is downstream of compression. Compression must land first before Metabolic Inlet is even designable without hitting known traps.

Attack C lands as "compression is upstream of Metabolic Inlet". Ordering holds.

**Attack D**: "The ordering is biased by recency. I (the kernel agent) just spent a whole session reading about hermes's compression patterns, so compression is top-of-mind. If I had spent the session reading about Metabolic Inlet, that would be on top. This ordering is not doctrine-driven, it's context-driven."

**Defense**: This is the strongest attack and it's partially right. Recency bias is real and worth calling out. Counter-evidence:

1. `compression_discipline_maturity = 0.40` is the **lowest** indicator on MYCO.md's dashboard. This is user-authored, pre-dates this session's hermes read, and independently converges on the same conclusion.
2. Wave 10 vision_recovery tertiary elements #12 (compression doctrine) + #13 (seven-step with 淘汰) + #14 (four-layer model with dead_knowledge) + #17 (structural vs factual decay) all cluster around the same gap: **compression is the substrate's primary cognitive act, and it is the most underserved**.
3. `docs/open_problems.md` has 4 out of 8 open problems in the Metabolic Inlet cluster, and problem #4 is explicitly "compression engineering (bloat失控)". Compression is blocking Metabolic Inlet.
4. The dependency graph in §2.1 was constructed by reading code paths, not by reading hermes. The top-down derivation converges on #3/#4 regardless of the kernel agent's pre-reading.

Attack D lands as "be aware of the bias, but the evidence converges independently". Acknowledgment is the response, not reordering.

### 2.3 Citable priority ordering

Based on Round 1 coverage + Round 2 DAG + attack resolutions:

**Top priority (Wave 27 target)**: **Anchor #4 (压缩即认知)** — highest doctrine weight, lowest implementation coverage, intertwined with anchor #3. Wave 27 will be a design craft for forward compression as a primitive.

**Second priority (Wave 28–29 target)**: **Anchor #4 implementation + #3 partial fulfillment** — `myco compress` MVP implementation wave (kernel_contract, brings in C2 atomic writes from hermes catalog as supporting infrastructure).

**Third priority (Wave 30+ target)**: **Anchor #3 full completion** — verbs for steps 2, 3, 4 (evaluate, extract, integrate). Each step gets its own design+impl wave pair.

**Long-tail priority**: **Anchor #5 D-layer full completion** — after compression lands, D-layer gets real workload; design view audit log + cross-ref graph + adaptive threshold + auto-excretion as a follow-up wave.

**Deferred**: Anchor #6 (selection pressure broadening), #1 (engineering reliability) — they are addressed *incidentally* by each doctrine wave. No dedicated anchor-serving wave for these.

**Held open**: Metabolic Inlet (part of anchor #3 doctrine). 4 open problems still unresolved. Compression must exist as a real operation (Wave 28+) before Metabolic Inlet's compression engineering problem is even addressable.

## 3. Round 3 — Supersession of Wave 25 D3 + Wave 27 scope lock

### 3.1 Old D3 (from `docs/primordia/hermes_absorption_craft_2026-04-12.md §4.1`)

> *"D3 — Wave 26+ ordering is friction-driven, NOT schedule-driven. The Wave 25
> test suite will catch bugs. The first caught bug determines Wave 26's subject.
> The catalog's T1 items (atomic writes, error taxonomy, structured logging,
> hot-gate compression) are candidates but not commitments. Each wave runs its
> own craft."*

### 3.2 New D3 (as decided by this craft, replacing the above)

> **D3 — Wave 26+ ordering derives from the doctrine dependency graph in
> `vision_reaudit_craft_2026-04-12.md §2`, not from friction signals or the
> hermes-absorption catalog's historical sequence. Each wave services one
> identity anchor (or advances a specific aspect of one anchor). Hermes
> catalog items C2–C20 are pulled in as supporting infrastructure when the
> doctrine wave explicitly requires them, not as standalone engineering
> waves. Waves alternate craft → impl → craft → impl: odd-numbered waves
> are design crafts (exploration class, 3 rounds, no code); even-numbered
> waves are implementations (kernel_contract class, 3 rounds, code + tests
> + contract bump). Friction between waves produces hot-fix waves that do
> not displace the planned ordering."*

### 3.3 Wave 27 scope lock

**Wave 27 target**: design craft for **anchor #4 (压缩即认知)** — forward compression as a substrate primitive.

**Wave 27 class**: `exploration` (target 0.85, 3 rounds, no code).

**Wave 27 output**: a single craft document `docs/primordia/compression_primitive_craft_2026-04-12.md` answering:

1. **What is the unit of forward compression?** A raw note group by tag? A time-windowed cohort? A semantic cluster? A manually-specified bundle?
2. **What is the trigger?** Manual (`myco compress <tag>`), scheduled (`myco compress --auto` cron), or friction-driven (hunger signal fires `compression_ripe`)?
3. **What is the output?** A single new extracted note with links back to N originals? The originals marked `excreted` with cross-reference? A wiki page synthesized from multiple notes?
4. **What is the audit trail?** How does a human verify that a compression was not hallucination? What frontmatter fields record provenance?
5. **What is the reversibility contract?** Can a compressed group be "re-expanded" (the originals are still on disk with `excreted` status)? Or is compression destructive?
6. **How does compression interact with anchor #3 steps 2-5?** Does compression subsume steps 2 (evaluate), 3 (extract), and 4 (integrate)? Or are those separate verbs that compression calls?
7. **What are the non-functional requirements?** Idempotence, atomicity, concurrent safety, cost bound.

**Wave 27 is NOT**: an implementation wave. No code lands. The craft is allowed to cite the hermes-absorption catalog (C2 atomic writes will become a Wave 28 dependency once the design is locked) but must not prescribe specific code.

**Wave 27 craft reflex arc**: the design craft itself is the reflex arc. Writing it satisfies the Wave 12 obligation that any kernel-contract-shaping decision must be crafted before commit.

### 3.4 Round 3 attack: scope leakage

**Attack E**: "Wave 27 as a pure design craft without any MVP is wasted effort. Users don't want design documents, they want working code."

**Defense**: Wave 27's output is the input to Wave 28's implementation. If Wave 27 is skipped, Wave 28 implements blindly — half of Wave 28 would be design decisions made under implementation pressure, and those decisions would be worse than what 3 rounds of structured debate can produce. Top-down methodology explicitly values "get the abstraction right before building" because the cost of a wrong abstraction is bigger than the cost of one wave's delay. The user's top-down statement (§0) is the decisive evidence.

Attack E lands as "this is a methodology choice, not a optimality claim". Accepted.

## 4. Conclusion extraction

### 4.1 Decisions (become canon)

**D1**: The 8 identity anchors in `MYCO.md §身份锚点` remain structurally sound. Three need refinement (not replacement): #3 (add scope clarification about vestigial middle steps), #5 (correct D-layer status to reflect Wave 18 v0.4.0 seed), #8 (add cross-reference to this Wave 26 craft).

**D2**: Wave 25 craft §4.1 D3 (friction-driven ordering) is **superseded** by D3 of this craft (doctrine-dependency-graph ordering). The old D3 is preserved in git for audit but is no longer in force.

**D3**: Wave 26+ ordering = doctrine-dependency-graph-derived, craft → impl rhythm, one anchor per wave pair, hermes catalog C2–C20 pulled in as supporting infrastructure on demand. Friction between waves produces hot-fix waves that do not displace the ordering. (Full text in §3.2 above.)

**D4**: Wave 27 = exploration class design craft for **forward compression as a substrate primitive** (anchor #4 service). No code. Output = `compression_primitive_craft_YYYY-MM-DD.md` answering 7 specific design questions (see §3.3). Wave 28 will be the implementation of Wave 27's design.

**D5**: MYCO.md refinements (anchors #3, #5, #8 + §指标面板 row `lint_coverage_confidence` rationale + §任务队列 row 2 + §任务 4 详述 "14 维 lint" → "18 维 lint") are authorized by this craft and will land as part of Wave 26's landing list. These are minimum-scope refinements — each change is traceable to a Round 1 finding.

**D6**: The Wave 10 `vision_recovery_craft_2026-04-10.md` is **not** superseded. It remains authoritative for the 18-element anchor set. This Wave 26 craft is a **sibling anchor document**, authoritative for the post-implementation-maturity reconciliation dimension. Both crafts are permanent anchors per anchor #8.

**D7**: Contract bump v0.24.0 → v0.25.0 lands in Wave 26 because MYCO.md is a public_claim surface touched by refinements D5, AND `_canon.yaml::system.indicators` values are being updated (substrate-level schema hygiene). The bump is real kernel-contract work, not bookkeeping.

**D8**: `docs/open_problems.md §6` (D-layer dead_knowledge) should have its status updated to reflect Wave 18 minimum seed landing (already updated ✓ verified during Round 1) — no action needed, just confirming the registry is current.

### 4.2 Landing list (Wave 26 scope, ≤ 15 items)

1. Write `docs/primordia/vision_reaudit_craft_2026-04-12.md` (this file) to disk with valid L13 frontmatter
2. Refine `MYCO.md §身份锚点 #3` by appending the scope clarification about vestigial steps 2-5 (see §1.3 proposed refinement)
3. Refine `MYCO.md §身份锚点 #5` by correcting the D-layer status line (see §1.5 proposed refinement)
4. Refine `MYCO.md §身份锚点 #8` by adding the Wave 26 cross-reference (see §1.8 proposed refinement)
5. Update `MYCO.md §指标面板` row `lint_coverage_confidence` rationale: "15 维 L0-L14 全绿" → "18 维 L0-L17 全绿 + Wave 25 tests/ 基础设施落地" (value can stay 0.68 pending Wave 27+ friction data)
6. Update `MYCO.md §任务队列` row 2 to reflect Waves 11-25 actual lands (replace stale v1.2.0-v1.5.0 reference with the actual v0.11.0-v0.24.0 sequence + note that Phase ② is running via Wave-numbered discipline)
7. Update `MYCO.md §任务 4 详述 · Metabolic Inlet` "现有 14 维 lint" → "现有 18 维 lint (L0-L17)"
8. Bump `_canon.yaml::system.contract_version` v0.24.0 → v0.25.0
9. Bump `_canon.yaml::system.synced_contract_version` v0.24.0 → v0.25.0
10. Bump `src/myco/templates/_canon.yaml::system.synced_contract_version` v0.24.0 → v0.25.0
11. Add v0.25.0 entry to `docs/contract_changelog.md` (documenting §身份锚点 refinements + D3 supersession + Wave 27 scope lock + MYCO.md §指标面板/§任务队列 updates)
12. `myco eat` this craft's evidence bundle (pointer to all 5 doctrinal files read, 15-wave scar trace, per-anchor coverage scores) as raw note tagged `wave26-seed vision-reaudit forage-digest`
13. `myco eat` + `myco digest --to integrated` Wave 26 decisions note (D1–D8) for canon
14. Append Wave 26 milestone entry to `log.md` (standard 5-point format, includes the note IDs + craft reference + doctrine)
15. `myco lint` 18/18 dimensions PASS + `pytest tests/ -q` 4/4 PASS before proposing commit

### 4.3 Known limitations

**L1 — Single-agent audit ceiling**: per `docs/craft_protocol.md §4`, a craft whose attack rounds are all generated by a single agent should report `current_confidence ≤ target_confidence` unless external research elevates the evidence base. This craft's external research consists of: (a) re-reading Wave 10 vision_recovery in full, (b) reading docs/vision.md + docs/open_problems.md + MYCO.md §身份锚点 in full, (c) reading 15 waves of `log.md` milestone entries, (d) reading `src/myco/notes.py::record_view` + `compute_hunger_report` + `src/myco/lint.py::main` + `_canon.yaml::system.*` to verify each anchor's implementation trace, (e) an Explore subagent task that verified D-layer's actual state (result: more complete than anchor #5 suggests — this surprise is the biggest single finding of the audit). Given that evidence base, target 0.90 with current 0.90 is defensible. If future audit finds the evidence thin, confidence should drop to ≤0.88.

**L2 — No independent verification of coverage scores**: the 0.0–1.0 coverage numbers in Round 1 are the kernel-agent's subjective judgment. There is no algorithmic definition of "anchor coverage". A future craft could legitimately challenge any individual score. The scores are *ordinal* more than *cardinal* — #4 (0.35) is genuinely worse than #1 (0.72), but whether #1 is 0.72 vs 0.68 vs 0.75 is not load-bearing on the ordering.

**L3 — Recency bias (Attack D)**: the audit was performed 48 hours after a deep hermes-absorption session. Even after acknowledging the bias and cross-validating against independent evidence (dashboard values, Wave 10 recovery, open_problems registration), the priority on compression could still be biased upward by recency. Mitigation: if Wave 27's design craft discovers that compression is harder to design than expected, the ordering should be re-visited in that craft's Round 3, not taken as gospel.

**L4 — Scope creep risk in Wave 26 landing**: this craft authorizes 7 text edits across MYCO.md + 3 contract bump sites + 1 changelog entry + 2 notes + 1 log entry + 1 craft file = 15 landing items. This is at the high end of Round 2 capacity limit (observed max was 2 subsystems/wave). Mitigation: all 15 items are trivial text refinements or schema updates (no code, no lint rule changes, no test additions). A single subsystem being refined ("MYCO.md doctrine reconciliation") is still one subsystem even when it touches multiple files.

**L5 — Wave 27 scope is locked but Wave 28+ is not**: Attack E acknowledges that Wave 27 without Wave 28 produces design-only output. Wave 28 is intended but not pre-scoped — it will be scoped in Wave 27's conclusion. This keeps the top-down commitment clean (Wave 27's output determines Wave 28, not this craft) but introduces a one-wave-ahead visibility horizon. The user should be aware that the roadmap is "committed Wave 27 + declared intent Wave 28" not "fully planned W27 and W28".

**L6 — Metabolic Inlet remains blocked**: this craft does not advance Metabolic Inlet's 4 open problems. The ordering places Metabolic Inlet downstream of compression (compression engineering is problem #4), but that only postpones the problem; it doesn't solve it. Cold start, trigger signals, and alignment remain open after compression lands.

### 4.4 Supersession pointer

- Supersedes: `docs/primordia/hermes_absorption_craft_2026-04-12.md §4.1 D3` (friction-driven Wave 26+ ordering). The rest of the Wave 25 craft (C1 landing, catalog C2–C20 inventory, Round 1-3 attacks on absorption shape) remains in force.
- Does NOT supersede: `docs/primordia/vision_recovery_craft_2026-04-10.md` (sibling anchor document).
- Does NOT supersede: Wave 25 D1/D2/D4/D5/D6 (those remain in force — only D3 changes).

### 4.5 Provenance + next step

- **Craft authored**: 2026-04-12, kernel-agent autonomous run under explicit user grant
- **Trigger**: user methodology statement post-Wave-25 dialogue
- **Decision class**: kernel_contract (MYCO.md refinements require the upgrade from exploration)
- **Target confidence**: 0.90 (kernel_contract floor)
- **Current confidence**: 0.90 (target met; evidence base supports the target per L1)
- **Rounds executed**: 3 (per §1, §2, §3)
- **L13 schema**: compliant (frontmatter has all 7 required fields with valid values)
- **L15 reflex arc**: satisfied (craft materializes within the session that plans to touch MYCO.md + _canon.yaml surfaces)
- **Next step**: execute landing list §4.2 items 1–15, verify §4.2 item 15 green, then present diff to user for commit approval (commit blocked pending explicit user grant per Wave 25 D2 convention).
