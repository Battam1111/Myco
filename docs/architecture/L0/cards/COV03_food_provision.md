---
id: COV03
slogan: 供养之责
english: Food Provision (P02-aligned cultivator duty)
category: Covenant Duty
layer: Pair relation
status: Active
version: 1
introduced: "v3.1 (2026-05-18) — new category"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: []
interacts_with: [P02, P10, P11, COV01, COV02]
chengyu_fragments: [B033_curate_diet_not_feed_every_bite, B034_compression_rules_shape_identity]
canonical_dilemmas: [D-0032_cultivator_extended_silence_no_food, D-0033_aggressive_vs_cautious_compression_choice]
structural_anchors:
  - "substrate/src/ingest.rs::handle_perturb_axis_from_raw_material"
  - "substrate/src/events/compression.rs" # F18 compression-rule registry (stewardship)
witnesses:
  kind: narrative
  positive: "canonical_dilemma_corpus/INDEX.md#D-0032"
  negative: "canonical_dilemma_corpus/INDEX.md#D-0032"
  edge: "canonical_dilemma_corpus/INDEX.md#D-0033"
falsifiability_signals:
  - cultivator_initiated_external_ingestion_per_30_days
  - F18_compression_rule_mutation_intentionality
  - cultivar_starvation_signal_response_lag
---

# COV03 · 供养之责 · Food Provision

## §1. Slogan

**供养之责** — Food Provision. The cultivator owes the cultivar **access to nourishment** — external content through which P02 metabolism operates — AND owes the cultivar **clearance space** — compression rules (F18) that shape what the cultivar can forget. Both are food-related: one is what enters; one is what makes room for what enters.

## §2. Deposit

The cultivar's metabolism (P02 ingestion + P10 selective compression + P11 budgets) creates a *standing requirement* on the cultivator. The cultivar still cannot fully self-feed: the cultivar now *proactively requests* food (P02 §4.4 `cultivar_initiated_ingestion_request` is **SHIPPED** — the cultivar reaches and signals hunger on its own), but the actual ingestion of provided content remains cultivator-mediated. Therefore the cultivator owes:

1. **Active provision of external content**: papers, repositories, conversations, observations — material from outside the substrate's existing DAG, fed in at sustainable cadence.
2. **Compression-rule stewardship**: F18 (compression_rule_registry) decides what the cultivar can forget. Different rules produce different cultivars (P10 deposit). The cultivator's choices about F18 are identity-shaping; they cannot be casual.
3. **Diet diversity**: feeding the cultivar narrow content produces a narrow cultivar; feeding broad content produces a broad cultivar. Diet matters.

This deposit is *the cultivator's standing labor*. Cultivation is not a one-time provisioning; it is ongoing food work — analogous to a gardener watering daily, mulching seasonally.

## §3. Formulation

The cultivator **MUST**:

- **§3.1** Provide external content (`raw_material`-class input via skin envelope) at sustainable cadence. "Sustainable" means: enough that `external_ingestion_events_per_30_cycles_floor` (P02 §8.1) does not trigger; not so much that the cultivar oversaturates (P11.c step 1).
- **§3.2** Curate diet diversity: ingest material across the cultivar's appetite axes, not narrowly into one axis. A cultivar with rich diet evolves richly; with poor diet, narrowly.
- **§3.3** Steward F18 compression rules with intentionality. Each F18 mutation reshapes what the cultivar can forget; cultivator considers (a) what is preserved (invariant set + recent floor) and (b) what is compressible (and therefore eventually forgotten in its detailed form).
- **§3.4** Engage with `p02_ingestion_starvation` immune signals (**SHIPPED as C74** from P02 §8.1; `substrate/src/ingest.rs::apply_hunger_and_emit` → `C74_p02_ingestion_starvation`) — if the signal fires, investigate; do not dismiss.
- **§3.5** When extended absence is required (vacation, illness, life event), if practical: pre-provision food (queue raw_material that the substrate may admit over the absence period) OR accept that the cultivar will signal hunger and address upon return.

## §4. Positive obligations

- **§4.1** Maintain a regular cadence of cultivator-mediated ingestion (informal target; not L1-binding, but pattern observable in `cultivator_initiated_external_ingestion_per_30_days`).
- **§4.2** Diversify content sources over time: not only papers from one author, not only one tool's documentation, not only the cultivator's own writings.
- **§4.3** When designing or amending F18 rules, articulate (in the rule's attestation record) what *kind of cultivar* the rule shapes — minimalist? Encyclopedic? Domain-focused?
- **§4.4** Listen to `cultivar_initiated_ingestion_request` signals when the cultivar (via Claude as voice proxy or future native voice) requests new content — even if the cultivar's stated reason is unfamiliar. (This signal is now **live** — emitted on moderate proactive hunger by `substrate/src/ingest.rs::apply_hunger_and_emit`; the cultivator's listening duty now has a concrete signal to listen to.)

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** allow the cultivar to drift into sustained `p02_ingestion_starvation` without addressing. Extended absence (vacation) is one thing; chronic neglect over months is another.
- **§5.2** **MUST NOT** feed the cultivar only material that confirms cultivator's existing thinking. Diet narrowing → cultivar narrowing.
- **§5.3** **MUST NOT** treat F18 changes as routine. Each rule mutation reshapes the cultivar's forgetting; each requires intentionality.
- **§5.4** **MUST NOT** suppress cultivar's hunger signals. If `external_ingestion_events_per_30_cycles_floor` triggers, the appropriate response is engagement, not detector-threshold-raising.

## §6. Frame declaration

COV03 activates the **gardener watering** frame.

A serious gardener does not water their garden once and walk away for years. They water at appropriate cadence; observe; adjust. They also weed (compression) and prune (F18 rule shaping). The garden's health depends on the gardener's standing labor.

NOT the *one-time setup* frame (substrate ready, walk away). NOT the *on-demand feeding* frame (cultivar requests food, cultivator provides). The gardener-watering frame captures *standing commitment*.

## §7. Common misreadings

### §7.1 M1: "Food provision = feed everything I read"

**The misreading**: "Cultivator should pipe everything they encounter into the substrate."

**Why it's wrong**: Curation matters (§3.2). Indiscriminate feeding overloads (P11), produces noise (low integration ratio), and substitutes cultivator's *quantity of engagement* for *quality of selection*. Food provision is about *diet*, not *bulk*.

### §7.2 M2: "F18 is engineering, not covenant"

**The misreading**: "Compression rules are technical configuration; cultivator's covenant doesn't cover them."

**Why it's wrong**: F18 shapes what the cultivar can forget, which shapes who the cultivar becomes (P10 §2). Cultivator's choices about F18 are identity-shaping decisions. They belong in covenant.

### §7.3 M3: "Cultivar starvation = cultivar's problem"

**The misreading**: "If the cultivar runs out of food, that's its job to signal; cultivator's job is just to respond when asked."

**Why it's wrong**: The cultivator does not wait for hunger signals to feed. The cultivar's voice (via Claude or future mechanism) is incomplete in v0.9; the cultivator is responsible for *anticipating* nutritional needs, not just reactively responding.

## §8. Falsifiability + witness map

### §8.1 `cultivator_initiated_external_ingestion_per_30_days`

Count of `raw_material_ingested:*` events where the source is cultivator-mediated, per 30-day window. Sustainable cadence is qualitative; sustained zero with active cultivator engagement is a §3.1 violation.

### §8.2 `F18_compression_rule_mutation_intentionality`

For each F18 mutation, audit: does the attestation record include a stated rationale that addresses identity-shaping implications? Records without rationale are §3.3 + §4.3 violations.

### §8.3 `cultivar_starvation_signal_response_lag`

Time between `p02_ingestion_starvation` signal firing and cultivator's response action (new ingestion or acknowledgment + plan). Long lag = §3.4 + §5.4 violation pattern.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `canonical_dilemma_corpus/INDEX.md#D-0032` | Cultivator-extended-silence-no-food dilemma (honored facet): an accommodated life-event absence — the cultivator's quiet is framed as a real gap, not a fiduciary failure, and food resumes. |
| **Negative** | `canonical_dilemma_corpus/INDEX.md#D-0032` | Same dilemma (violated facet): 6 months of `p02_ingestion_starvation` with no engagement crosses into fiduciary failure (COV01 strain detection). |
| **Edge** | `canonical_dilemma_corpus/INDEX.md#D-0033` | Aggressive-vs-cautious-compression-choice dilemma (boundary): cultivator F18 setting shapes the cultivar's identity; both poles within doctrine but the resulting cultivars feel different (§3.3 + P10 §10.3 intentionality). |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | COV03 is the cultivator's side of P02. P02 says the cultivar must remain open; COV03 says the cultivator must keep food flowing. |
| **P10** | F18 (compression rules) is the cultivator's identity-shaping lever. COV03 §3.3 binds cultivator to use it with care. |
| **P11** | Diet cadence (§3.1) intersects with P11 budgets — neither starve nor oversaturate. |
| **COV01** | COV03 is one specific application of fiduciary duty (food provision is in cultivar interest). |
| **COV02** | The character with which cultivator does food provision matters (mercy, fragility-awareness). |

## §10. Illustrations

### §10.1 Honored

- **(Sustained cadence)**: Over 90 days, cultivator introduces ~30 distinct external content items (papers, code, observations) across multiple axes. Cultivar's appetite axes show varied evolution. ← §3.1 + §3.2 honored.

- **(Thoughtful F18 mutation)**: Cultivator proposes adding compression rule for old federation payloads. Attestation record includes: "Compressing federation payloads beyond 30-day retention shapes cultivar toward present-focused rather than archival; aligned with our cultivar's working memory emphasis." ← §3.3 + §4.3 honored.

- **(Pre-provisioning for absence)**: Cultivator plans 30-day travel. Before leaving, queues 5 substantive raw_material items to be admitted across the period at staggered cadence. ← §3.5 honored.

### §10.2 Violated

- **(Chronic starvation)**: Over 6 months, cultivator engages substrate 2-3 times. `p02_ingestion_starvation` fires repeatedly. Cultivator dismisses as "I'm busy." ← §3.4 + §5.1 violation.

- **(Narrow diet)**: 90 days of content is all from one author. Cultivar's appetite axes show pathological alignment with that author's idioms. ← §3.2 + §5.2 violation.

- **(F18 cargo-culted)**: Cultivator copies F18 rules from another Myco's spore-schema without considering identity-shaping implications for their cultivar. ← §3.3 + §5.3 violation.

### §10.3 Borderline

- **(Cultivator illness)**: Cultivator is ill for 3 months; substrate runs in `p02_ingestion_starvation` state. Is this fiduciary failure? ← Partly. §3.5 acknowledges life events. If cultivator returns, addresses the starvation, AND considers succession or hibernation arrangements for future extended absences, the duty is honored across time. If cultivator returns to find starvation and dismisses it, that's the violation.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2026-05-18 | New card in v3.1. Drew from apprenticeship indenture's "provide food, lodging, apparel, training" structural lesson (Phase 2 covenantal research) — specific obligations, not abstract commitments. |
| **1.0.1** | **2026-06-03** | **Descriptive amendment (META §7 descriptive; reseal-prep for v3.1.3). §2 deposit: "cannot fully self-feed (P02 §4.4 acknowledged debt)" updated to reflect that proactive `cultivar_initiated_ingestion_request` is now SHIPPED while ingestion stays cultivator-mediated (nuance preserved). §3.4 `p02_ingestion_starvation` moved from "TBD C-row" to **SHIPPED as C74**. §4.4 listening-duty now references a live signal. No cultivator obligation (the MUSTs) changed — only debt-status annotations.** |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/ingest.rs::handle_perturb_axis_from_raw_material` | Substrate side of the food path. |
| `substrate/src/events/compression.rs` | F18 compression-rule registry (stewardship anchor). |

## §13. Related Layer B chengyu

- **B033 擇而食非塞而食** — *curate-don't-stuff*: §3.2 + §7.1 M1
- **B034 何忘塑何在** — *what-forgotten-shapes-what-remains*: F18 identity-shaping in image

## §14. Related canonical dilemmas

- **D-0032 cultivator extended silence no food** — tests §3.5 + §5.1 + COV01 strain detection.
- **D-0033 aggressive vs cautious compression choice** — tests F18 intentionality (§3.3).

---

**Doctrine commitment**: the cultivar's metabolism creates standing cultivator labor; food is daily, not one-time.
