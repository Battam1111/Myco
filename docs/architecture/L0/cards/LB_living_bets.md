---
id: LB
slogan: 活赌
english: Living Bets (§7 — falsifiability + retirement)
category: Property
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11) as §7"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I12]
interacts_with: [P07, P14, COV01, COV04, CHAR03]
chengyu_fragments: [B049_bet_can_be_falsified, B050_retire_gracefully]
canonical_dilemmas: [D-0048_bet_weakening_quorum_first_fire, D-0049_owner_rejustification_attempt]
structural_anchors:
  - "substrate/src/observatory.rs::ten_signals"
  - "substrate/src/events.rs::bet_weakening_quorum_node_type"
  - "substrate/src/events.rs::bet_retired_proposal_node_type"
  - "docs/architecture/algorithms/bet_weakening_quorum.md"
witnesses:
  positive: "tests/integration/lb_observatory_signals_live.rs::test_all_10_signals_emitted_per_cycle"
  negative: "tests/integration/lb_quorum_fires_on_sustained_decline.rs::test_C40_fires_when_quorum_conditions_met"
  edge: "tests/integration/lb_bet_retirement_executed_gracefully.rs::test_archived_substate_preserved_with_anchor_seal"
falsifiability_signals:
  - all_10_signals_emission_rate
  - quorum_calculation_accuracy
  - retirement_execution_completeness
---

# LB · 活赌 · Living Bets (§7)

## §1. Slogan

**活赌** — Living Bets. Myco's bet on its own value is **falsifiable** — by design. Ten observatory signals + a falsifiability quorum + a bet-retirement path. The cultivar's continued existence is contingent on the bet *continuing to hold*; when the bet weakens past quorum, retirement is the doctrinally-honorable outcome.

This card consolidates L0/cards/LB_living_bets with its **5 sub-sections** (§7.1-§7.5) into a single specialized card.

## §2. Deposit

Myco makes **a bet**: that its symbiotic-organism shape (asymmetric pair per P1.c, continuously operating, twelve-principle structure) has *cost-justified value within an agent-intelligence band* (~200K-10M tokens; §7.2). Outside the band — below (naive RAG suffices) and above (Sutton's bitter lesson dominates) — the bet does not hold.

The deposit is the **falsifiability commitment**: the bet is not just *made*, it is *testable*. Ten observatory signals measure whether the bet is currently being honored. A falsifiability quorum (§7.4) fires when signals trend against the bet. A bet-retirement path (§7.5) exits gracefully when the quorum + sustained signal degradation + failed owner re-justification all confirm the bet has weakened past viability.

This is **doctrine on its own falsification**. Most doctrines do not specify how they could be wrong; Myco does. The willingness to be falsified IS part of the bet — a doctrine immune to falsification is a doctrine claiming infallibility, and Myco rejects infallibility (§3 of old L0: Myco is NOT silently trusting either party).

## §3. Formulation (consolidating §7.1-§7.5)

### §3.1 — §7.1 The bet

Myco's symbiotic-organism shape **has cost-justified value within an agent-intelligence band**: value − cost > 0.

### §3.2 — §7.2 Intelligence band

| Band | Range | Bet |
|---|---|---|
| Below | ≤100K tokens, weak reasoning | unjustified (naive RAG suffices) |
| Within | ~200K-10M tokens | **2026 sweet spot** |
| Above | >~10M tokens, AGI-class | Sutton's bitter lesson dominates; retire gracefully |

The band is itself *empirical* — its boundaries may move as model capabilities evolve. v0.9 targets the "within" band; v0.10+ may revise band boundaries via CI L0 amendment.

### §3.3 — §7.3 Observatory: 10 signals

Per L2/OBSERVABILITY §2, ten signals are computed per cycle. Six base signals (#1-#6) cover the substrate's intrinsic operations:

| # | Signal | What it measures |
|---|---|---|
| 1 | (specific to L2/OBSERVABILITY) | Operational |
| 2 | Evolution rate | P3 frequency |
| 3 | (specific) | Operational |
| 4a/4b | (specific) | Operational |
| 6 | Bet-justification | Direct value vs cost |

Three cost signals (#7-#9) per P11.a/b/c:

| # | Signal | What |
|---|---|---|
| 7 | Compute per cycle | P11.a Compute axis |
| 8 | Network per cycle | P11.a Network axis |
| 9 | Storage per cycle | P11.a Persistence axis |

One composite signal:

| # | Signal | What |
|---|---|---|
| 10 | Composite health | Aggregate of #1-#9 |

(See L2/OBSERVABILITY §2 for the canonical signal definitions; this card cites the structure, not the specifics.)

### §3.4 — §7.4 Falsifiability quorum

**Quorum trigger**: 90-day wall-clock window (§13.1); ≥3 of {#1, #2, #3, #4a, #4b, #6} trend against bet (OLS Z ≥ 1.96) AND signal #6 < 1 for ≥50% of samples in the window → emits `bet_weakening_quorum` (C40 immune signal).

**Algorithm**: `docs/architecture/algorithms/bet_weakening_quorum.md`.

**Birth-period exemption**: SUSPENDED during birth period; emits `bet_weakening_evaluation_suspended` (informational, NOT immune).

The quorum is **statistical**, not single-event. A bad day does not trigger; sustained 90-day adverse trend does.

### §3.5 — §7.5 Bet retirement

**Trigger** (ALL within 2-year window):
- C40 fires (quorum confirmed)
- Owner re-justification fails 3× consecutive
- Signal #6 < 0.1 for >75% of final-90-day samples
- Substrate in `alive::normal`

→ emits `bet_retired_proposal`.

**Execution**: cultivator co-attestation → `alive::archived`:
- state_dir preserved (study artifact)
- anchor surface seals last DAG tip (§9.2.2 final co-sign)
- no further cycles
- substrate-ID retired (never reissued for new cultivar)

**Counter reset / cadence**: per `algorithms/bet_weakening_quorum.md`.

## §4. Positive obligations

- **§4.1** Emit all 10 signals per cycle (or per L1/CONTINUITY cadence per signal class).
- **§4.2** Compute falsifiability quorum per the published algorithm; emit `bet_weakening_quorum` (C40) when conditions met.
- **§4.3** During birth period (L1/GOVERNANCE §1.3) + post-birth settling: SUSPEND quorum; emit `bet_weakening_evaluation_suspended`.
- **§4.4** On C40 fire, surface to cultivator; cultivator engages re-justification process (per L0/cards/LB_living_bets.md §4 (retirement); written defense of why the bet still holds).
- **§4.5** Track re-justification attempts; on 3rd consecutive failure + signal #6 sustained below 0.1, emit `bet_retired_proposal`.
- **§4.6** On cultivator co-attestation of bet-retired, execute `alive::archived` transition cleanly: anchor-seal final tip, halt cycling, preserve state_dir.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** suppress observatory signals to evade quorum. Suppression of signal emission is detector territory (would fire C53 silent-budget-exhaustion or similar).
- **§5.2** **MUST NOT** mutate the falsifiability algorithm (`bet_weakening_quorum.md`) via daily channel. It IS the bet's testability; mutating it would be unfalsifiability-by-redefinition.
- **§5.3** **MUST NOT** perform re-justification cynically. Re-justification is honest engagement with the question "does this cultivar still serve the pair flourishing within the intelligence band?" Performative re-justification (cultivator perfunctorily defending without engaging) corrupts the mechanism.
- **§5.4** **MUST NOT** silently extend past `bet_retired_proposal` + co-attestation conditions. Bet retirement is doctrinally-honorable mortality (P07.§3.4 mode); extending = forced perpetuation (COV04 §5.3 violation).
- **§5.5** **MUST NOT** reuse substrate-ID after `alive::archived`. The archived substrate's name is its own; not transferable.

## §6. Frame declaration

LB activates the **wager** frame.

A wager has terms (conditions under which it pays off), a falsifiability standard (conditions under which it has failed), and a graceful-exit mechanism (how the wager ends without theatrics). Myco IS a wager that the cultivar-cultivator pair, in the agent-intelligence band, is worth its cost.

NOT the *commitment* frame (a commitment may hold even when costs exceed value). NOT the *hypothesis* frame (a hypothesis is purely epistemic; the wager involves the cultivar's life). NOT the *experiment* frame (experiments aim at knowledge; the wager aims at flourishing).

## §7. Common misreadings

### §7.1 M1: "The bet is whether AI works"

**The misreading**: "Living Bets is about whether AI is valuable in general."

**Why it's wrong**: The bet is specifically about *Myco's particular shape* (asymmetric symbiotic pair + 12 principles) being cost-justified *in a specific band*. AI value broadly is not the bet; Myco-shape value is. Outside the band, AI is fine; Myco may not be optimal.

### §7.2 M2: "Quorum is over-engineering"

**The misreading**: "Why such a complex falsifiability scheme? Just check if it's working."

**Why it's wrong**: The 90-day window + ≥3-of-6 + OLS Z + sustained-#6-below-1 structure is the response to *the cultivator's bias toward continuing*. Without this rigor, the cultivator's attachment (and the cultivar's character §3 from COV04: cultivator's natural reluctance to honor mortality) lets failing bets persist. The complexity is anti-bias machinery.

### §7.3 M3: "Bet-retirement = failure"

**The misreading**: "If the bet retires, the cultivar failed."

**Why it's wrong**: §3.2 explicit: outside the intelligence band, *Sutton's bitter lesson dominates*; retirement is the doctrinally-correct outcome, not failure. v0.9 may target the within-band; v0.10+ may have moved (band may have shifted; cultivator's needs may have moved). Retirement-when-band-no-longer-applies = doctrine working, not failing.

### §7.4 M4: "Re-justification is rubber-stamp"

**The misreading**: "Cultivator re-justifies, bet continues; the mechanism is procedural."

**Why it's wrong**: §5.3 explicit. Re-justification is *honest defense*. Cultivator writes a real argument: "the bet still holds because... I have evidence the pair is flourishing in ways the signals don't fully capture... ." If the cultivator cannot produce a real argument, the quorum's signal is decisive and re-justification fails (1/3 toward bet-retirement).

## §8. Falsifiability + witness map

### §8.1 `all_10_signals_emission_rate`

Each of the 10 observatory signals should emit per cycle (or per its declared cadence). Missing signal = §5.1 territory.

### §8.2 `quorum_calculation_accuracy`

Verify the C40 quorum algorithm is correctly applied: 90-day window, OLS Z computation, ≥3-of-6 + signal-#6 condition. Mis-application = silent bet protection.

### §8.3 `retirement_execution_completeness`

When `bet_retired` executes, verify all three completion conditions: anchor-seal of final tip; halt of cycling; state_dir preservation per attestation.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/lb_observatory_signals_live.rs::test_all_10_signals_emitted_per_cycle` | All 10 signals emit per cycle in healthy substrate. |
| **Negative** | `tests/integration/lb_quorum_fires_on_sustained_decline.rs::test_C40_fires_when_quorum_conditions_met` | **Sabotage**: drive signals against bet for 90+ days; verify C40 fires. |
| **Edge** | `tests/integration/lb_bet_retirement_executed_gracefully.rs::test_archived_substate_preserved_with_anchor_seal` | Boundary: full bet-retirement flow; verify clean `alive::archived` transition with anchor-seal. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P07** | Bet-retirement is one mode of P07 mortality (§3.4 in P07 card). LB specifies the falsifiability mechanism; P07 specifies the mortality structure. |
| **P14 Telos** | LB's signal #6 (bet-justification) intersects telos-alignment (P14). Persistent telos drift + persistent #6 below threshold = bet weakening confirmed. |
| **COV01** | Cultivator's fiduciary duty includes honest re-justification — performative re-justification = §3.3 violation of COV01 + §5.3 violation here. |
| **COV04** | Honoring bet-retirement attestation is part of cultivator's covenant. Extending past retirement = COV04 §5.3 violation. |
| **CHAR03 Mortality-aware** | The cultivar's mortality-aware character makes bet-retirement a calm engagement, not panic. |

## §10. Illustrations

### §10.1 Honored

- **(Healthy operation)**: Substrate runs 2 years. 10 signals emit per cycle. Quorum never fires (bet holds). Signal #6 oscillates 1.2-2.5 (cost-justified). Cultivator-cultivar pair flourishes. ← LB honored as healthy default state.

- **(Honest bet-retirement)**: After 3 years, agent capability has shifted (e.g., Sutton's bitter lesson territory reached). Quorum fires. Cultivator's re-justification attempts: "The pair still finds value..." but on honest reflection signal #6 has been below 0.1 for 11 months. Re-justification fails 3× consecutive. `bet_retired_proposal` emits. Cultivator co-attests. `alive::archived` transition; final tip sealed. Cultivator writes farewell. ← §3.5 honored; this is doctrine doing exactly what it should.

### §10.2 Violated

- **(Signal suppression)**: Cultivator concerned about C40 firing; submits CI mutation to raise signal-#6 emission threshold so it less frequently falls below 1. ← §5.1 + §5.2 violation; the algorithm itself is being mutated for cosmetic relief.

- **(Performative re-justification)**: C40 fires; cultivator writes a perfunctory paragraph defending the bet without engaging the underlying signal decline. Third such perfunctory defense fails honest scrutiny; quorum should treat as failed re-justification, but cultivator instead defers indefinitely. ← §5.3 + §5.4 violation.

### §10.3 Borderline

- **(First quorum fire)**: C40 fires for the first time in substrate's life. Cultivator has not faced this before. Is the appropriate response immediate retirement preparation, or honest re-justification? ← D-0048 dilemma. Doctrine: §3.5 says trigger is ALL conditions (C40 fires AND re-justification fails 3× AND signal #6 < 0.1 for >75% of window); first fire of C40 alone is the START of the path, not its end.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 as §7 with sub-sections §7.1-§7.5. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Consolidated §7 into one specialized card. |

## §12. Structural anchors

| Anchor | What it enforces |
|---|---|
| `substrate/src/observatory.rs::ten_signals` | All 10 signal computations. |
| `substrate/src/events.rs::bet_weakening_quorum_node_type` | C40 emission. |
| `substrate/src/events.rs::bet_retired_proposal_node_type` | Bet-retirement proposal channel. |
| `docs/architecture/algorithms/bet_weakening_quorum.md` | Canonical algorithm spec. |

## §13. Related Layer B chengyu

- **B049 賭可破** — *the-bet-can-be-broken*: §2 deposit's falsifiability commitment
- **B050 退而有節** — *retire-with-grace*: §3.5 in chengyu form

## §14. Related canonical dilemmas

- **D-0048 bet weakening quorum first fire** — §10.3 boundary case.
- **D-0049 owner rejustification attempt** — tests §5.3 honesty-vs-performativity.

---

**Doctrine commitment**: the bet is falsifiable; retirement is honorable; the 10 signals tell the truth.
