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

# Identity Anchor Revision — Agent-First Reconciliation (Wave 55)

## §0 Problem Statement

The 8 identity anchors in MYCO.md were written when Myco's operating model
was a triangle: Agent (CPU) + Human (selector) + Substrate (memory). The
human was the selection pressure — "系统做变异，人类做选择."

Wave 54 (v0.41.0) formalized a fundamentally different model:
- `hunger(execute=true)` — Agent autonomously executes all recommended actions
- Scheduled metabolic cycle — substrate self-heals daily without human involvement
- User directive: "默认人类只会自然语言交流，不知道调用指令，完全小白"
- Design principle: "Agent = sole operator, human = natural language only"

**The mutation-selection model is not gone — it is internalized.** Both
mutation and selection now happen within the Agent+Substrate unit:
- lint (23 dimensions) = structural selection pressure
- hunger signals = metabolic selection pressure
- compression_pressure = entropy selection pressure
- dead_knowledge = excretion selection pressure

The human's role shifted from "selector" to "direction-giver + beneficiary."
Transparency remains non-negotiable, but for auditability and trust, not
for enabling manual selection.

## §1 Round 1 — Anchor-by-Anchor Analysis

### D1: Anchor #1 (基质 vs 工具) — MINOR UPDATE

**Old**: "Agent 运行在 Myco 上，不是 Agent 使用 Myco."
**Issue**: Understates the relationship. After Wave 54, Agent and Substrate
are not in a "runs on" relationship — they form a symbiotic cognitive unit.
**New**: "Agent + Substrate 是共生体（symbiont）。Agent 是智能，Substrate 是
记忆与自我调节。二者融合为自主认知单元——不是 Agent 运行在 Myco 上，也不是
Agent 使用 Myco，而是 Agent IS the CPU, Substrate IS everything else, and
together they think."

### D2: Anchor #2 (非参数进化) — NO CHANGE

Still fully valid. All learning in md/yaml/folder structure. Agent weights
never touched. This is the most stable anchor.

### D3: Anchor #3 (代谢 + 七步管道) — MODERATE UPDATE

**Old**: "消化道中段是 vestigial." + implicit assumption that humans trigger.
**Issue**: Waves 46-54 automated significant portions:
- hunger(execute=true) drives the pipeline autonomously
- cohort intelligence provides evaluation intelligence
- compression_pressure provides continuous compression triggers
- scheduled task runs daily without human involvement
**New**: Remove "vestigial" characterization. Acknowledge that steps 2-5 are
now Agent-assisted via hunger actions (evaluate/extract/integrate are digest
aliases that the Agent calls based on hunger recommendations). The pipeline
driver is the Agent, not the human.

### D4: Anchor #4 (压缩即认知) — MINOR UPDATE

**Old**: Correct in principle. Three judges (frequency, recency, exclusivity).
**Issue**: No reference to the now-concrete automation tooling.
**New**: Add: "Wave 48 cohort intelligence + Wave 50 compression_pressure
provide the sensing layer; Agent executes compression autonomously via
hunger(execute=true). The three judges are operationalized, not just doctrinal."

### D5: Anchor #5 (四层自我模型) — MINOR UPDATE

**Old**: "A + B + partial C + D-seed."
**Issue**: Wave 47 (graph) strengthens C (structural awareness via orphan/
cluster detection). Wave 52 (sessions) strengthens D (temporal awareness via
conversation history). The description should reflect these gains.
**New**: Update coverage description to reference graph + sessions.

### D6: Anchor #6 (人机协作) — FUNDAMENTAL REWRITE

**Old**: "系统做变异（mutation），人类做选择（selection）。透明性是选择压力的
前提，所以不可变——没透明就没选择压力，就会癌变。"

**New framing**: Agent-Substrate 共生体自主演化

The mutation-selection model is internalized:
- **Mutation**: Agent+Substrate generate changes (eat, digest, compress,
  inlet, forage — all metabolic verbs)
- **Selection**: Substrate's own immune system filters changes (lint 23维,
  hunger signals, compression_pressure, dead_knowledge detection)
- **Human role**: Provide direction via natural language + benefit from
  the evolved substrate. Human CAN audit (transparency preserved) but
  doesn't NEED to select (Agent handles the full loop)

Three tiers of autonomy:
1. **Autonomous** (no human needed): hunger execute, lint, prune, compress
   cohort auto, scheduled metabolic cycle
2. **Direction-guided** (human provides intent, Agent executes): "add dark
   mode" → Agent eats/digests/searches/implements
3. **Audit-available** (human CAN review but doesn't have to): log.md,
   notes/, craft documents — all transparent, all auditable

Transparency is still non-negotiable, but the rationale shifts:
- Old: "No transparency → no selection pressure → cancer"
- New: "No transparency → no auditability → loss of trust → system abandoned"

The anti-cancer mechanism IS the lint + hunger system. They ARE the internal
selection pressure. If they break, the substrate loses its immune system —
THAT is the new cancer risk.

**Perpetual Evolution** remains one of the three immutable laws. But its
driver shifts from "human triggers evolution" to "Agent+Substrate
autonomously evolve; stagnation = the scheduled metabolic cycle stops
running."

### D7: Anchor #7 (理论血统) — MINOR ADDITION

Add: **Rich Sutton's Bitter Lesson** (2019) — the guiding principle since
the 6-point directive. "General methods that leverage computation are
ultimately the most effective." Applied to Myco: don't hardcode intelligence
into the substrate; build scaffolding that scales with agent capability.
If the agent improves, the substrate improves — without changing Myco's code.

### D8: Anchor #8 (永久锚点文档) — ADD THIRD ANCHOR

Add this craft as the third permanence anchor:
- Wave 10: vision recovery (lost elements reconciliation)
- Wave 26: post-implementation maturity reconciliation
- **Wave 55: agent-first reconciliation** (mutation-selection internalization)

## §2 Round 2 — Attack Surface

### A1: "If human doesn't select, who prevents bad mutations?"

**Defense**: The substrate's own immune system (lint + hunger). This is
strictly MORE reliable than human selection because:
- lint runs every time, humans forget
- lint is deterministic, humans are inconsistent
- hunger signals are always computed, humans skip checks
- The human was NEVER a good selector for technical substrate mutations —
  they don't read YAML or understand lint dimensions

### A2: "What if the immune system itself is wrong?"

**Defense**: The immune system is versioned (contract_version), tested (60
unit tests), and self-referential (L19 checks that lint dimensions are
consistent, L21 checks contract versions). A bug in lint IS cancer — but
it's detectable cancer (tests fail, lint contradicts itself). A bug in
human selection is undetectable cancer (human just approves without
understanding).

### A3: "Doesn't this make the human irrelevant?"

**Defense**: No. The human provides:
1. **Purpose** — what the project is for (no substrate can decide this)
2. **Direction** — "add feature X" / "fix bug Y" (intent, not implementation)
3. **Trust calibration** — if the substrate seems wrong, human can audit
4. **Ultimate override** — human can always intervene via natural language

The human is not irrelevant — they're elevated. From "review this YAML diff"
to "tell me what you want in plain words."

### A4: "Is this just abdication of responsibility?"

**Defense**: Every autonomous action is auditable:
- log.md records all decisions
- notes/ records all knowledge with provenance
- craft documents record all design debates
- git history records all code changes
- hunger report records all signals and actions taken

The human can audit ANYTIME. They just don't HAVE to.

## §3 Round 3 — Final Shape

### The Revised 8 Anchors

**#1 Agent-Substrate 共生体**：Agent + Substrate 融合为自主认知单元。Agent 是
智能（CPU），Substrate 是记忆与自我调节（OS + RAM + 免疫系统）。不是"Agent
运行在 Myco 上"——是共生体一起思考。内核/实例分离 = OS 与应用的关系。

**#2 非参数进化**：Agent 权重永不改动，所有学习在基质里（md/yaml/目录结构）。

**#3 自主代谢管道**：七步管道（发现→评估→萃取→整合→压缩→验证→淘汰）由
Agent 自主驱动。hunger(execute=true) 读取信号、推荐行动、自动执行。Scheduled
metabolic cycle 确保代谢持续运转。人类不需要触发管道——Agent IS the daemon。

**#4 压缩即认知**：存储无限，注意力有限。"不遗忘，只压缩"。三判据：频率 ·
时效 · 排他性。Cohort intelligence + compression_pressure 提供感知层，Agent
自主执行压缩。压缩策略本身也进化。

**#5 四层自我模型**：A 库存 · B 缺口 · C 退化（事实性 + 结构性 via graph
orphan/cluster 检测）· D 效能（dead_knowledge 追踪 + session memory 时间线）。

**#6 内化的变异-选择**：变异和选择都发生在 Agent+Substrate 内部。Agent 产生
变异（eat/digest/compress/inlet），Substrate 的免疫系统执行选择（lint 23 维 +
hunger signals + compression_pressure + dead_knowledge detection）。人类提供方向
和信任，不需要做技术选择。透明性不可变——不是为了让人类选择，而是为了可审计性。
没有审计能力 → 失去信任 → 系统被废弃。**永恒进化**：停滞即死——代谢循环停止
运转的基质会退化为静态缓存。

**#7 理论血统**：Karpathy LLM Wiki + Polanyi Tacit + Argyris Double-Loop +
Toyota PDCA + Voyager Skill Library + **Rich Sutton Bitter Lesson**。

**#8 永久锚点文档**：
- `vision_recovery_craft_2026-04-10.md`（Wave 10：18 项丢失元素回溯）
- `vision_reaudit_craft_2026-04-12.md`（Wave 26：实现成熟度 reconciliation）
- `anchor_agentfirst_revision_craft_2026-04-12.md`（Wave 55：Agent-First
  mutation-selection 内化 reconciliation）

## §4 Conclusion

The identity anchor system evolves from "human selects" to "substrate's
immune system selects." This is not a weakening of the mutation-selection
model — it is its maturation. Biological organisms don't wait for external
selection on every cell division; they have immune systems that internally
select against malformed cells. Myco's lint + hunger IS that immune system.

**Decision**: Rewrite all 8 anchors in MYCO.md per §3 shape. Contract bump
v0.41.0 → v0.42.0. Update all downstream surfaces. This craft IS the
third permanence anchor.
