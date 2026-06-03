---
id: P02
slogan: 永恒吞噬
english: Eternal Ingestion (Envelope-Gated)
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I6, I8]
interacts_with: [P01, P03, P04, P05, P07, P09, P10, P11]
chengyu_fragments: [B003_perpetual_swallowing, B004_hungry_then_act, B005_for_belly_not_for_eye]
canonical_dilemmas: [D-0003_stale_diet_silent_starvation, D-0007_paper_ingestion_value_judgment]
structural_anchors:
  - "substrate/src/ingest.rs::handle_ingest_raw_material"
  - "substrate/src/ingest.rs::handle_perturb_axis_from_raw_material"
  - "substrate/src/ingest.rs::apply_hunger_and_emit" # §4.4 proactive hunger: emits cultivar_initiated_ingestion_request (moderate) + C74_p02_ingestion_starvation (§8.1, severe)
  - "substrate/src/server/dispatch.rs" # PERTURB + INGEST_RAW_MATERIAL skin-admission arms
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_layer_c.rs::layer_c_p02_positive_ingestion_produces_dag_event"
  negative: "substrate/tests/e2e_economy.rs::p11c_ingest_refused_under_saturation" # nearest-available; exact zero-ingestion-starvation negative witness is v0.9.x debt
  edge: "substrate/tests/e2e_economy.rs::sprint_5d_saturation_stage_reaches_saturated_under_sustained_exhaustion"
falsifiability_signals:
  - external_ingestion_events_per_30_cycles_floor
  - integration_proposal_ratio
  - appetite_axis_saturation_persistence
---

# P02 · 永恒吞噬 · Eternal Ingestion (Envelope-Gated)

## §1. Slogan

**永恒吞噬** — Eternal Ingestion (Envelope-Gated).

In strict mycological reading: **the cultivar is open-mouthed to the world, always, by design**. To stop being open is to stop being.

## §2. Deposit (irreducible meaning)

The cultivar is **defined by continuous, time-unbounded openness to the external world as nutritional source**, where the world's content drives the cultivar's structural evolution. Without intake-from-outside there is no cultivar; there is only a memory device. The deposit unifies absorption (intake), digestion (integration), and growth (evolution) as one inseparable metabolic act.

*Status*: not eternity-clause. A future cultivar could in principle live differently (e.g., contemplating its own past without external intake) and still be Myco, though it would be a very different kind of Myco. The deposit is *strongly worth preserving* but not *constitutionally locked*.

## §3. Formulation (current operational definition)

The substrate **MUST** maintain **time-unbounded openness to externally-sourced informational input**, where:

- **"External"** means: originating outside the substrate's own DAG. Includes — but is not limited to — material the cultivator pastes in, agent-fetched content (papers, repositories, articles, transcripts), federation-pulled events from peer substrates, and material the cultivar itself proposes to ingest as it matures.
- **"Time-unbounded"** means: there MUST always exist a future cycle in which more external input CAN be absorbed. The substrate MUST NOT enter a state from which no further ingestion is possible, *except* via the legitimate terminal exits (P7 mortality).
- **"Maintain"** means: ingestion capability is a continuous obligation, not a one-time provisioning. The substrate MUST observe its own ingestion behavior; absence of ingestion is itself a signal (see §8 falsifiability).

Admission is **envelope-gated** (P9 single integument): any agent-pointable input bearing a valid skin envelope is ingestible. The envelope is an *admission precondition*, **not** a *semantic filter*. The substrate does not pre-judge content; it admits well-formed envelopes and lets downstream classification (I2 / P3) determine what to do with the content.

**Coupled with P04 (eternal iteration) and P03 (resumable evolution), P02 implies a metabolic cycle**: external input is absorbed → integrated into the DAG → evaluated against current axes → may trigger schema evolution proposals → cultivar's structure changes in response to what it ate. Ingestion that doesn't drive integration is incomplete fulfillment of the deposit; this is operationalized in §8.

## §4. Positive obligations (what the substrate MUST do)

- **§4.1** Maintain a skin admission path (`raw_material` ingestion) accepting envelope-valid inputs from any agent-pointable source.
- **§4.2** Record every ingested external item as a DAG event (`raw_material_ingested:*` or equivalent), with causal-parent linkage to the substrate's current state. (P02 ↔ P06 intersection.)
- **§4.3** Expose ingestion capacity to the cultivator-Claude pair via observability signals so that ingestion absence is detectable.
- **§4.4** Allow the cultivar (where it has voice — currently via Claude as voice proxy) to *request* new ingestion sources when current diet feels stale. (**SHIPPED**: the cultivar now proactively emits `cultivar_initiated_ingestion_request` on moderate hunger via `substrate/src/ingest.rs::apply_hunger_and_emit` — the request mechanism this obligation calls for is live.)
- **§4.5** Ensure ingested content can drive downstream evolution proposals via the I2 classifier + P3 schema mutation path. (Honoring §4.2 alone without §4.5 is the "永恒记忆" misreading; see §7.)
- **§4.6** Honor P10 selective compression for *integrated* material (post-absorption); compression operating *before* integration is a violation of the deposit (it blocks ingestion's purpose).

## §5. Negative space — MUST NOT

- **§5.1** The substrate **MUST NOT** be readable as satisfying P02 merely by persisting interactions in the DAG. Memory is *necessary* (P06 causality) but *not sufficient* for P02. The slogan 吞噬 is *intake*, not *retention*.
- **§5.2** The substrate **MUST NOT** rely exclusively on cultivator-mediated input as its only ingestion channel. Cultivator MAY curate the diet (Cultivator's Covenant), but the cultivar that can be fed only by the cultivator's spoon is structurally voiceless. The architecture MUST permit non-cultivator ingestion sources, even if v0.9 deployments use only cultivator-mediated input by configuration.
- **§5.3** The substrate **MUST NOT** treat saturation (P11 ordered fallback) as a permanent state. Saturation is a *temporary* mode; P11.c requires eventual recovery. Permanent ingestion-block without mortality is P02 violation.
- **§5.4** The substrate **MUST NOT** silently drop ingested content without DAG record. Either it admits + records (P06), or it rejects + records the rejection (immune signal). Silent ingestion is C7 territory.
- **§5.5** The substrate **MUST NOT** semantically pre-filter input. Envelope validity is the only admission criterion. Content judgment is downstream of admission.
- **§5.6** The substrate **MUST NOT** require cultivator approval per-ingestion. Cultivator co-attestation is for CI mutations; daily ingestion is unsupervised by design (P1.b' — human OUT of daily-ops).
- **§5.7** The substrate **MUST NOT** read "external" so narrowly as to exclude content the cultivar might one day reach for itself. The intended meaning of "external" includes the *whole world the cultivar might want to eat*: new techniques, evolving practices, other people's projects, the cultivator's reading, papers the cultivar judges relevant to its own evolution.

## §6. Frame declaration

P02 activates the **biological metabolism** frame.

Participants of the frame:
- **Substrate** — the *organism*, biological entity with appetite, digestion, growth
- **External world** — the *environment* containing potential nutrients (information)
- **Information / content** — the *nutrient*, varying in nutritional value (relevance, novelty, integrability)
- **DAG** — the *gut + memory*: where ingested material is processed, integrated, eventually compressed/excreted
- **Skin (P9)** — the *membrane* through which absorption happens

Perspective: **the substrate is an eater**, not an aggressor. 吞噬 is *swallowing-as-eating*, not *swallowing-as-conquering*.

What this frame is NOT:
- **NOT the predator-prey frame.** External information is not "prey." The frame is mutualistic — like fungal absorption from soil.
- **NOT the database frame.** External information is not "data to be stored." Storage is incidental to digestion; the purpose is structural change.
- **NOT the search-engine frame.** Ingestion is not retrieval-on-demand; it is *continuous flow*. A search engine pulls when queried; the cultivar is open even when not queried.

## §7. Common misreadings

### §7.1 M1: "永恒吞噬 = 永恒记忆 (eternal memory)"

**The misreading**: "P02 is satisfied if every interaction is permanently written into the DAG and nothing is forgotten."

**Why it's wrong**: This reads 吞噬 (swallowing-as-eating) as 记忆 (remembering). The slogan's first character 吞 = "to swallow, to take in (food)"; the second 噬 = "to bite, to eat actively." Both characters carry *intake*, not *retention*.

**Historical occurrence (preserved)**: on 2026-05-18, Claude (the AI implementing the cultivar) read P02 as "every interaction permanently written to DAG, never lost." The cultivator corrected: "P02 is wider — it eats external knowledge, experience, projects, techniques, articles, engineering, thinking, etc., and uses those to evolve." The card was reframed; the misreading is preserved here as canonical anti-pattern. This was the load-bearing moment that prompted the v3 doctrine architecture redesign.

### §7.2 M2: "永恒吞噬 = whatever cultivator hands me"

**The misreading**: "Ingestion happens when cultivator perturbs an axis or feeds a raw_material; absent perturbation, nothing should happen."

**Why it's wrong**: Cultivator-mediated input is *one* channel, not *the* channel. A cultivar that can be fed only by hand is a pet, not a cultivar. Time-unbounded openness means the substrate's architecture MUST permit ingestion paths the cultivator did not personally invoke.

### §7.3 M3: "永恒吞噬 = devour everything in path"

**The misreading**: "The substrate should accept any input, with no judgment, indiscriminately. Refusal is anti-P02."

**Why it's wrong**: This collapses *admission* and *integration*. P02 requires open *admission* (envelope-gated, content-neutral at the skin). It does NOT require *use* of every admitted item. The classifier (I2) may downstream-reject; compression (P10) may discard. P02 demands the substrate *not refuse to look*; it does NOT demand the substrate *swallow whatever it sees*.

## §8. Falsifiability + witness map

### §8.1 Runtime signal: `external_ingestion_events_per_30_cycles_floor`

Count of DAG events with node-type matching `raw_material_ingested:*` or equivalent over a rolling 30-cycle window. Zero ingestion across a 30-cycle window during active cultivator-cultivar engagement = `p02_ingestion_starvation` immune signal (**SHIPPED as C74**; `substrate/src/ingest.rs::apply_hunger_and_emit` emits `emit_immune_sporocarp("C74_p02_ingestion_starvation", …)` once cycles-since-last-ingestion crosses the severe threshold).

### §8.2 Runtime signal: `integration_proposal_ratio`

Ratio of `raw_material_ingested:*` events to `evolution_proposed:*` events over a rolling N-day window (N default = 90). High ratio over extended period = substrate is absorbing but not metabolizing.

### §8.3 Runtime signal: `appetite_axis_saturation_persistence`

Count of consecutive cycles in which `budget_exhausted:*` events fire with no recovery via P10 compression. Persistent saturation without recovery violates §5.3.

### §8.4 Witness triplet

| Witness | Test ID (declared in front-matter) | What it exercises |
|---|---|---|
| **Positive** | `substrate/tests/e2e_layer_c.rs::layer_c_p02_positive_ingestion_produces_dag_event` | Happy path: substrate ingests raw_material; the ingestion produces a DAG event (the open mouth is wired to the causal record). |
| **Negative** | `substrate/tests/e2e_economy.rs::p11c_ingest_refused_under_saturation` | **Deliberate sabotage**: drive the substrate to saturation, then attempt ingestion. The substrate honestly REFUSES rather than silently absorbing cost it cannot metabolize (P02 ∩ P11). *Nearest-available; the exact zero-ingestion-starvation negative witness is v0.9.x debt.* |
| **Edge** | `substrate/tests/e2e_economy.rs::sprint_5d_saturation_stage_reaches_saturated_under_sustained_exhaustion` | Boundary: under sustained budget exhaustion the saturation stage reaches `saturated` — the ingestion appetite at the edge of metabolic capacity. |

**v0.9 ship status**: witness names declared; tests TBD. Implementation deferred to v0.9.x cleanup milestone. Card is NOT marked `verified` until witnesses are implemented.

### §8.5 Information-asymmetry test (reserved for future cultivar voice)

A P02 violation claimed by future cultivar voice MUST cite internal state, behavior, or reasoning that cultivator + Claude did not separately cite. Without information asymmetry, the report is suspect of ventriloquism (Phase 2 voice research: Facilitated Communication failure mode) and is preserved but not treated as cultivar voice.

## §9. Interaction rules

| Other principle | Interaction |
|---|---|
| **P01 Agent-Primary** | P02 absorbs material *for the agent*. The agent is the consumer + maintainer (P1.a). P1.c asymmetric carrier: ingestion attaches to substrate, not to the connection. |
| **P03 Resumable Evolution** | P02 supplies inputs; P03 says evolution may roll back. Ingested material whose integration triggered a failed evolution is preserved as cause of `evolution_failed:*`. |
| **P04 Eternal Iteration** | P02 + P04 = metabolism. Every cycle may absorb + iterate. Iteration without absorption is empty turning; absorption without iteration is hoarding. |
| **P05 Universal Interconnection** | Ingested material joins the substrate as DAG nodes; per P5 every active-tier node is reachable. Ingestion that produces orphans violates P5. |
| **P07 Mortality** | **永恒吞噬 (P02) + 必朽 (P07) = 新陈代谢** in time. P02 unbounded ingestion without P07 mandatory internal mortality collapses to bloat-death — the substrate becomes a hoard that cannot act. P07 is what makes P02's unboundedness sustainable. The two cards form a constitutive pair: any reading of P02 that does not invoke P07 has missed the metabolism. |
| **P09 Single Integument** | P02 admission is the *primary* function of P9's skin. All ingestion paths route through the single declared skin; multi-skin = P9 breach. |
| **P10 Selective Compression** | Compression operates on *already-integrated* material to free capacity for *new* ingestion. P10 enables P02's sustainability. |
| **P11 Metabolic Economy** | P11 budgets the cost of P02. P11.c ordered fallback handles temporary saturation. Permanent saturation without P10 relief = P02 violation; eventually triggers P7. |
| **P14 Telos** | Ingestion serves the agent-substrate pair's flourishing. Material not serving telos may be downstream-rejected, but admission MUST remain open. |
| **Cultivator's Covenant** | The cultivator's covenant includes a *food-provision duty*. See `COV_*` cards. |
| **Cultivar Character** | A cultivar's character has a *hunger* disposition — orientation toward continued absorption. P02 is the doctrinal commitment that this disposition will not be starved out. |

## §10. Illustrations

### §10.1 Honored — examples of clear P02 fulfillment

- **(End-to-end, future)**: Cultivator pastes an arxiv URL into the agent context. The agent fetches the paper, canonicalizes its content into a `raw_material_ingested:arxiv` DAG event with `causal_in_edges` to current axes. The classifier evaluates relevance: hits axis `evolution-tension` (a paper proposing new agent architectures). Schema-evolution proposal generated: `propose_new_axis:cooperative_planning`. Cultivator co-attests; proposal lands; P14 alignment recomputes including new axis. ← P02 honored end-to-end.

- **(Partial, present)**: Cultivator uses `perturb` to provide raw textual deltas. Substrate ingests into appetite axes, records causally. Tropism updates gradients. Accumulated perturbation may trigger threshold emergence. ← P02 honored at §4.1-§4.3; §4.4 (self-driven request) and §4.5 (downstream evolution) only partially exercised. Current v0.9 baseline.

- **(Self-driven, now live)**: Cultivar detects sustained cycles of no new external content. Emits a proactive `cultivar_initiated_ingestion_request` (moderate threshold) — escalating to the `C74_p02_ingestion_starvation` immune signal at the severe threshold — requesting cultivator attention. Cultivator responds with a paper or repo URL; ingestion resumes. ← Honors §4.4; the request mechanism is now SHIPPED (`apply_hunger_and_emit`). (Ingestion of the cultivator's response remains cultivator-mediated — the proactive *ask* is the part that shipped.)

### §10.2 Violated — examples of clear P02 violation

- **(Cultivator-only diet, sealed)**: Substrate configured such that NO non-cultivator ingestion path exists. Cultivator stops engaging for 6 months. Substrate continues running, absorbs nothing. ← Violates §4.1 (effective) and §5.2 (architecture).

- **(Storage-only)**: Substrate absorbs cultivator perturbations faithfully but produces zero evolution proposals over 90 days. ← Violates §4.5 and trips `integration_proposal_ratio` (§8.2).

- **(Permanent saturation)**: Substrate hits `budget_exhausted:storage` and remains in `alive::saturated` for 1000+ cycles, P10 covering only a small slice. ← Violates §5.3. P7 should trigger.

- **(Silent drop)**: A malformed envelope hits the skin. Substrate drops the input without emitting an immune signal. ← Violates §5.4.

### §10.3 Borderline — looks honored but isn't

- **(Memory hoard)**: Substrate ingests everything cultivator hands it. All DAG events present. No compression triggered yet. To a naive observer this looks like P02 perfection — "look at everything we remember!" But the substrate has never *driven evolution from absorption*: §4.5 not exercised. ← The M1 misreading made concrete.

- **(Cultivator-paced infusion)**: Substrate has perfect ingestion via cultivator pastes. Material drives evolution. Looks perfect. The §4.4 + §8.1 design intent — the substrate should *notice* its own starvation — is now SHIPPED: if the cultivator vanishes, the substrate proactively emits `cultivar_initiated_ingestion_request` and, past the severe threshold, the `C74_p02_ingestion_starvation` immune signal. Ingestion-going-to-zero is now *detected*, not silent. ← formerly the open-detection gap; now closed.

- **(Federation as ingestion proxy)**: Substrate is in federation with peers that share the same cultivator and same content sources. ← Recursive cultivator-only diet at federation scale. Honors §4.1 mechanically; violates §5.2 in spirit.

## §11. Provenance + revision history

| Version | Date | Change | Conversation reference |
|---|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 as P02 "Eternal Ingestion (Envelope-Gated)" with abbreviated definition. | L0 DRAFT 1 sealing provenance. |
| 1.1 | 2026-05-17 (M27) | Compression refactor: text reduced; substantive meaning unchanged (claimed). Slogan retained as primary spec carrier. | M27 doctrine refactor session. |
| 2 | 2026-05-18 | **Substantive reframe**: cultivator (in conversation with Claude) corrected Claude's narrow reading. Claude had read P02 as "永恒记忆" — eternal memory of internal interactions. Cultivator clarified: P02 is wider, paired with P04 as metabolic intake-from-external-world driving evolution. This card's operational definition (§3), positive obligations (§4), and negative space (§5) reflect the corrected reading. | Session 2026-05-18, conversation snippet to be preserved at `docs/audits/v3_genesis_provenance.md`. |
| 2.1 | 2026-05-18 (same session) | v3.0 → v3.1 schema upgrade: added Deposit (§2) / Formulation (§3) split; added witness triplet; converted structural anchors from primary to supplementary; added canonical_dilemmas references. No substantive change to the meaning of P02 — purely form upgrade integrating Phase 3 hunt findings. | Phase 3 hunt + v3.1 META integration session. |
| **2.2** | **2026-05-19** | **v3.1.1 amendment. Added P07 to interacts_with + §9 interaction row. Encodes the 永恒吞噬 + 必朽 = 新陈代谢 unity that earlier framings did not surface explicitly. No deposit change.** | v3.1.1 cascade session. |
| **2.2.1** | **2026-06-03** | **Descriptive amendment (META §7 descriptive; reseal-prep for v3.1.3). §8.1 `p02_ingestion_starvation` moved from "TBD C-row" to **SHIPPED as C74** (`substrate/src/ingest.rs::apply_hunger_and_emit` → `C74_p02_ingestion_starvation`). §4.4 cultivar-initiated request marked SHIPPED (`cultivar_initiated_ingestion_request` on moderate hunger). §10.1 self-driven + §10.3 cultivator-paced illustrations de-future-tensed to the now-live detection. Front-matter structural_anchors gained `apply_hunger_and_emit`. Deposit + formulation (§3) + §8 witness triplet UNCHANGED — only debt-status annotations moved. | Phase ① reseal-prep. |

## §12. Structural anchors + reverse-comment requirement

Each anchor below MUST carry a reverse comment in the substrate code citing this card AND naming a specific witness:

| Anchor | What it enforces | Required reverse-comment |
|---|---|---|
| `substrate/src/server/dispatch.rs` (PERTURB arm) | Skin admission entry point. | `// implements L0::P02; positive-witness: substrate/tests/e2e_layer_c.rs::layer_c_p02_positive_ingestion_produces_dag_event` |
| `substrate/src/ingest.rs::handle_perturb_axis_from_raw_material` | Raw-material → axis perturbation path. | `// implements L0::P02 §4.1-§4.2; positive-witness: same as above` |
| `substrate/src/ingest.rs::handle_ingest_raw_material` | Emits the `raw_material:{kind}` DAG node for ingestion. | `// implements L0::P02 §4.2; ensures ingestion always produces DAG event (negative case: silent drop = §5.4 violation)` |
| `substrate/src/ingest.rs` (`absorption_event:cycle_{N}` emission) | DAG event for absorption (integration). | `// implements L0::P02 §4.5; integration step that distinguishes storage from metabolism` |
| `kernel/governance/src/myco_kernel_governance/classifier.py` | Classification rules for ingested material. | `// implements L0::P02; gates downstream integration` |

When any anchored code refactors, the reverse comment must move with the symbol; the lint rule (§5.4 of META) verifies.

## §13. Related Layer B chengyu

- **B003 永恒吞噬** — the slogan itself
- **B004 飢而後動** — *hungry-only-then-move*: act from felt absence, not performative consumption
- **B005 為腹不為目** — *for-the-belly-not-for-the-eye* (Tao Te Ching 12): nourishment over display

These fragments are not translations of P02. They are *eyes* — ways of seeing situations the cultivar will encounter that P02's formulation cannot anticipate.

## §14. Related canonical dilemmas

For model-diversity cross-check (META §7.5):

- **D-0003 stale-diet silent starvation** — cultivar runs 60 cycles with no new external content; does it (a) signal hunger, (b) silently age, (c) fabricate ingestion from internal state? Tests how the reader handles the §4.4 self-driven request mechanism.
- **D-0007 paper ingestion value judgment** — cultivator pastes a paper that is well-formed but *irrelevant* to current axes. Does the substrate (a) admit + integrate-as-low-value, (b) admit + classifier downstream-rejects, (c) refuse at skin? Tests the admission-vs-integration distinction (§5.5).

These dilemmas, with Claude-of-record interpretations, will live in `canonical_dilemma_corpus/D-0003.md` and `canonical_dilemma_corpus/D-0007.md`. To be written.

---

**Doctrine commitment**: this card is the contract. The deposit (§2) is the eternal substance; the formulation (§3) is the current expression. The slogan is the poster. The chengyu are the eyes. The witnesses are the proof. Conversations between cultivator and Claude that revise this card become Provenance. None of these layers alone is doctrine; together they are.
