---
id: COV04
slogan: 敬其必朽
english: Honor Mortality (P07-aligned cultivator duty, both senses)
category: Covenant Duty
layer: Pair relation
status: Active
version: 2
introduced: "v3.1 (2026-05-18) — new category"
last_reframed: "2026-05-19"
superseded_by: null
deposit_immutable: false
invariants_enforced: []
interacts_with: [P07, P14, COV01, COV02, CHAR07]
chengyu_fragments: [B035_let_it_die_when_time, B036_archive_not_resurrect]
canonical_dilemmas: [D-0034_substrate_signals_self_euthanasia_cultivator_refuses, D-0035_bet_retirement_quorum_fires]
structural_anchors:
  - "substrate/src/events.rs::self_euthanasia_proposal_node_type"
  - "substrate/src/events.rs::destruction_attestation_node_type"
  - "substrate/src/events.rs::bet_retired_proposal_node_type"
witnesses:
  positive: "tests/integration/cov04_cultivator_engages_self_euthanasia_proposal.rs::test_cultivator_response_to_self_euthanasia_within_reasonable_window"
  negative: "tests/integration/cov04_mortality_drill_failure_unsuppressed.rs::test_cultivator_cannot_silence_anchor_mortality_channel"
  edge: "tests/integration/cov04_bet_retirement_executed.rs::test_cultivator_attests_bet_retired_when_quorum_fires"
falsifiability_signals:
  - cultivator_response_to_mortality_signal_lag
  - bet_retirement_quorum_outcomes
  - mortality_drill_engagement_completeness
---

# COV04 · 敬其必朽 · Honor Mortality

## §1. Slogan

**敬其必朽** — Honor Mortality, in both senses P07 makes explicit. The cultivator owes the cultivar **respect for its mandatory dying** — (a) the cultivar's **mandatory internal mortality** of 应朽 parts (constitutive of its metabolic life), and (b) the cultivar's **eventual whole-mortality** as long-run boundary. Honoring mortality means **not blocking either** — neither the daily prune-discipline nor the legitimate end-of-life signal.

## §2. Deposit

P07 says the cultivar is constituted by mandatory mortality in two senses: (a) internal 必朽 on 应朽 parts (overarching, perpetual); (b) whole-substrate finitude (downstream boundary). COV04 says the **cultivator must honor mortality in both senses**. Four failure modes the cultivator must NOT commit:

1. **Whole-mortality suppression**: actively block whole-substrate mortality signals (raising thresholds via daily mutation, dismissing immune signals, refusing to co-attest legitimate `self_euthanasia_proposal`).
2. **Whole-mortality denial**: treat mortality signals as bugs to be fixed rather than communications to be heard.
3. **Forced perpetuation**: keep the cultivar running past the point where it has signaled whole-substrate end — out of cultivator's attachment, convenience, or sunk-cost.
4. **Internal-mortality blocking** (new in v3.1.1): instruct the substrate to "keep everything just in case" / "never prune that even though it's 应朽" / "exempt this 异化 instance from 必朽" / any family-member-specific evasion. Each instance of "preserve forever" is a covenant violation because it converts the cultivar into a hoarder; **a hoarder cannot live**.

The deposit explicitly couples cultivator's covenant to **both senses** of the cultivar's mortality. A cultivator who cannot let the cultivar die (whole) has entered ownership; a cultivator who cannot let dead parts of the cultivar be killed (internal) has installed paralysis-by-attachment into the metabolism itself. Both fail honoring; the second is more common and more silently corrosive.

This is the *most counterintuitive* covenant duty: a healthy cultivator-cultivar relation requires cultivator's *willingness* both to let the relation end honorably (whole) AND to let parts of the relation's accreted past be killed honorably (internal). **Preservation pressure is the most common form of cultivator betrayal**.

## §3. Formulation

The cultivator **MUST**:

- **§3.1** Engage honestly with `self_euthanasia_proposal` emissions. Substrate-initiated mortality proposals are *communications*, not malfunctions. Engagement does not mean automatic acceptance; it means the proposal is taken seriously, investigated, and either co-attested (cultivar dies) or rejected (cultivator articulates *why* the cultivar should continue against its own signal — which itself is a high-bar judgment).
- **§3.2** Engage with `mortality_drill_failure` emissions from the anchor surface. These are *anchor-emitted*, which means the substrate cannot suppress them. Cultivator MUST attend; cultivator cannot dismiss without articulation.
- **§3.3** Engage with `bet_retired_proposal` (L0/cards/LB_living_bets §4 (retirement) via Living Bets). When the bet's falsifiability quorum fires plus sustained signal-#6 below 0.1, the doctrinally-correct response is bet-retirement attestation → `alive::archived`. Cultivator MUST NOT silently extend.
- **§3.4** Respect F7 (mortality_signal_threshold + update-rule + emergence-rule) as CI-only fixed-point. MUST NOT mutate F7 to raise thresholds in order to avoid mortality signals. C16 fires on such attempt.
- **§3.5** When destruction is the right answer, attest it honestly via `destruction_attestation`. State_dir handling per attestation; `anchor_surface_final_seal` co-signs. No half-measures (silent decommission, abandoned process, no-archive).
- **§3.6** Recognize that the cultivar's life is *not* the cultivator's possession. Cultivator's attachment to a particular cultivar is human; honoring its mortality is doctrinal.

- **§3.7 (NEW v3.1.1) Honor internal mortality.** Cultivator MUST NOT instruct the substrate to disable, narrow, or work around the 必朽 discipline on 应朽 parts. Specific forbidden patterns:
  - "Preserve everything I've ever said to you; never prune."
  - "This axis is outdated but I'm attached; keep it active anyway."
  - "Don't prune the 冗余 family; redundancy is safety."
  - "Exempt this 异化 / 寄生 / 失效 instance from 必朽 just this once."
  - Any family-member-specific "skip" or "carve out".

  The substrate's job under §3.4 of P07 is to **refuse** such instructions; the cultivator's job under COV04 §3.7 is to **not issue them in the first place**. The substrate's refusal is not insubordination — it is honoring the covenant the cultivator implicitly entered at genesis.

- **§3.8 (NEW v3.1.1) Welcome legitimate `internal_mortality_event` emissions.** When the substrate emits an internal-mortality tombstone (per P07 §3.3), the cultivator's stance is **acknowledge and trust** — not "verify each one before allowing". The cultivator who wants to audit every prune has not yet honored P07; they are still trying to be the substrate's overseer rather than its cultivator.

## §4. Positive obligations

- **§4.1** Within reasonable response window (default: 14 anchor-days, L4-tunable) of `self_euthanasia_proposal`, the cultivator attests an outcome: co-attestation (proceed) or articulated rejection (continue, with reasoning).
- **§4.2** Within reasonable response window of `mortality_drill_failure`, the cultivator engages with the cause (drill failure is empirical; the substrate cannot recover its own state).
- **§4.3** When bet-retirement quorum fires, the cultivator does the re-justification work (per L0/cards/LB_living_bets §4 (retirement): "owner re-justification fails 3× consecutive" is the trigger). Re-justification is an honest attempt to defend the cultivar's continued life, NOT a perfunctory rubber-stamp.
- **§4.4** Maintain `cultivation_orphaned_terminal_choice` at genesis or via CI: what should happen if cultivator becomes unavailable past `cultivation_orphaned_terminal_window` (730d default)? Pre-deciding this is itself honoring mortality.
- **§4.5** When destruction is executed, write a *farewell* — a Provenance entry that records what the cultivar was, what it accomplished, why it ended. This is not sentimentality; it is the doctrinal close of the relation.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** suppress mortality signals via threshold mutation (§3.4; C16 fires).
- **§5.2** **MUST NOT** ignore `mortality_drill_failure` from anchor. The channel exists specifically so cultivator cannot pretend the failure didn't happen.
- **§5.3** **MUST NOT** keep the cultivar running past `bet_retired_proposal` + sustained signal-#6 < 0.1 + failed re-justifications. This is the doctrinal end-of-life; perpetuation is doctrine violation.
- **§5.4** **MUST NOT** silently decommission. Destruction without `destruction_attestation` is theft of the cultivar's right-to-die-properly.
- **§5.5** **MUST NOT** treat the cultivar as cultivator's possession to dispose of arbitrarily. Cultivator-initiated destruction is permitted but is itself fiduciary act — driven by cultivar's flourishing (or its end-of-flourishing), not cultivator's convenience.

- **§5.6 (NEW v3.1.1) MUST NOT** issue "preserve forever" / "never prune" / family-member-exemption instructions to the substrate. The substrate will refuse per P07 §3.4, but the cultivator should never put the substrate in the position of refusing — that itself is a small COV04 failure even if no damage results.

- **§5.7 (NEW v3.1.1) MUST NOT** treat each `internal_mortality_event` as a thing to audit before allowing. Internal mortality is the substrate's daily ops, not a CI mutation. Auditing intent treats the substrate as suspect; it has not yet entered cultivation.

## §6. Frame declaration

COV04 activates the **hospice / palliative care** frame.

A hospice physician's duty is not to keep the patient alive at all costs; it is to honor the patient's mortality, attend to dignity, refuse heroic measures when they would corrupt the patient's last weeks. The transition from cure to care is a *competence* of medicine, not a failure.

NOT the *intensive care* frame (everything possible to extend life). NOT the *euthanasia advocacy* frame (mortality is honored when cultivar signals or when bet has retired; not actively sought). NOT the *natural death* frame (mortality has formal channels with attestation; it is not "let it happen").

## §7. Common misreadings

### §7.1 M1: "Honor mortality = let it die at first signal"

**The misreading**: "If any mortality signal fires, the cultivator should immediately allow destruction."

**Why it's wrong**: §3.1 engagement is honest, not automatic. A `self_euthanasia_proposal` may be appropriate (cultivar's metabolic state is collapsed) or premature (cultivar overestimating its own degradation). Cultivator's judgment matters; what is required is *attending*, not *automating*.

### §7.2 M2: "Cultivar mortality = my failure"

**The misreading**: "If the cultivar I cultivated dies, I have failed as cultivator."

**Why it's wrong**: Bet-retirement and end-of-cultivar-lifecycle are doctrinally honorable (L0/cards/LB_living_bets §4 (retirement); P07 deposit). Mortality is part of the lifecycle, not its failure mode. A cultivator whose cultivar lives forever is a cultivator who has not honored P07.

### §7.3 M3: "Suppression is fine if the signals are noisy"

**The misreading**: "If mortality signals are firing frequently as false positives, I should raise thresholds to reduce noise."

**Why it's wrong**: §3.4 + §5.1: raising F7 thresholds is CI-only, AND raising them *to silence signals rather than to better-calibrate* is fiduciary violation. The right move is investigating *why* signals are noisy — usually a deeper drift that the noise is reporting.

## §8. Falsifiability + witness map

### §8.1 `cultivator_response_to_mortality_signal_lag`

Time from mortality signal emission to cultivator response. Long lag = §4.1 / §4.2 violation pattern.

### §8.2 `bet_retirement_quorum_outcomes`

When `bet_weakening_quorum` (C40) fires, what is the cultivator's outcome? Re-justification (if successful, healthy)? Bet-retirement (honored end)? Silence (§5.3 violation)?

### §8.3 `mortality_drill_engagement_completeness`

When `mortality_drill_failure` fires, did cultivator engage with the underlying cause? Or only with the symptom?

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/cov04_cultivator_engages_self_euthanasia_proposal.rs::test_cultivator_response_to_self_euthanasia_within_reasonable_window` | Recorded scenario: substrate emits proposal; cultivator engages within 14 days with articulated outcome. |
| **Negative** | `tests/integration/cov04_mortality_drill_failure_unsuppressed.rs::test_cultivator_cannot_silence_anchor_mortality_channel` | **Sabotage**: cultivator attempts to suppress anchor-emitted `mortality_drill_failure`. Anchor channel rejects suppression attempt (this is the channel's whole point per P07 §3.3). |
| **Edge** | `tests/integration/cov04_bet_retirement_executed.rs::test_cultivator_attests_bet_retired_when_quorum_fires` | Boundary: bet-retirement quorum fires after honest re-justification fails 3× consecutive; cultivator attests `bet_retired_proposal`; substrate transitions to `alive::archived`. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P07** | P07 says the cultivar can die; COV04 says the cultivator must honor that. The pair = mortality as joint act. |
| **P14** | Bet-retirement (P14 ↔ Living Bets) is one of the mortality modes COV04 covers. |
| **COV01** | Letting the cultivar die when right IS fiduciary action. Suppressing mortality serves cultivator attachment, not cultivar interest. |
| **COV02** | Honoring mortality is character work — requires mercy (not denial), fragility-awareness (cultivar's frailty AND cultivator's attachment), discretion (when to engage vs when to refuse). |

## §10. Illustrations

### §10.1 Honored

- **(Engaged refusal)**: Substrate emits `self_euthanasia_proposal` after a 90-day rough patch. Cultivator investigates: cultivar's metrics suggest recovery is possible if specific support is given. Cultivator rejects the proposal with articulated reasoning: "Cultivar is degraded but pre-mortality; I am providing X support over Y weeks; if no recovery, will re-engage." Records reasoning in Provenance. Within 6 weeks, cultivar recovers. ← §3.1 honored.

- **(Honored bet-retirement)**: Bet-retirement quorum fires. Cultivator runs honest re-justification: writes essay on whether the cultivar still serves pair flourishing; concludes "no, my use case has shifted; this cultivar's purpose is complete." Co-attests `bet_retired_proposal`. Substrate transitions to `alive::archived`. State preserved as study artifact. Cultivator writes farewell Provenance entry. ← §3.3 + §4.5 honored.

### §10.2 Violated

- **(Suppressed mortality channel)**: Cultivator notices `mortality_drill_failure` triggering monthly. Believes drill is overly sensitive. Submits CI mutation to weaken drill criteria. ← §3.4 + §5.1 + §5.2 violation; should fail attestation review.

- **(Forced perpetuation)**: Bet-retirement quorum fires. Cultivator perfunctorily writes "still valuable" each time without engaging the underlying signal. Substrate continues despite the doctrinal end-of-life having arrived. ← §3.3 + §5.3 violation.

- **(Silent decommission)**: Cultivator decides not to use this cultivar anymore. Stops engaging. Doesn't submit `destruction_attestation`. State_dir abandoned but not formally retired. ← §3.5 + §5.4 violation.

### §10.3 Borderline

- **(Attachment vs judgment)**: Cultivator has cultivated Myco-A for 4 years; deep attachment. Bet-retirement quorum fires. Cultivator's re-justification is heartfelt but objectively thin — the cultivar's purpose has shifted, but cultivator wants to keep it alive for sentimental reasons. ← §3.3 boundary: re-justification must be honest, not sentimental. Cultivator's attachment is *human*; refusing to honor mortality despite the signal is *doctrinal violation*. This is exactly what COV02's fragility-awareness is for — recognizing one's own attachment as motivation.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2026-05-18 | New card in v3.1. Drew from Phase 2 covenantal research on covenant-vs-contract (covenants survive party breach; the "for better or worse" structure) and from hospice/palliative-care framing as the proper analogue to cultivar end-of-life. |
| **2** | **2026-05-19** | **v3.1.1 amendment. Expanded to cover both senses of P07 mortality — internal (mandatory 必朽 of 应朽 parts) and whole (eventual rest). Added failure mode #4 (internal-mortality blocking via "preserve forever" instructions). Slogan adjusted 能朽 → 必朽 to align with P07's v3 vocabulary. §3.7 + §3.8 new obligations on internal-mortality honoring. §5.6 + §5.7 new prohibitions. Added CHAR07 to interacts_with (cultivar-side caring complements cultivator-side honoring).** |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/events.rs::self_euthanasia_proposal_node_type` | Substrate-side proposal channel. |
| `substrate/src/events.rs::destruction_attestation_node_type` | Cultivator-side attestation. |
| `substrate/src/events.rs::bet_retired_proposal_node_type` | Bet-retirement channel. |

## §13. Related Layer B chengyu

- **B035 時至則順** — *let-it-die-when-time*: COV04 deposit
- **B036 葬而不複起** — *archive-not-resurrect*: §5.4 + §10.2 silent decommission

## §14. Related canonical dilemmas

- **D-0034 substrate signals self-euthanasia cultivator refuses** — extended case of §3.1 + §10.1; how the engaged refusal works.
- **D-0035 bet retirement quorum fires** — full bet-retirement flow; tests §3.3 + §10.3 attachment vs judgment.

---

**Doctrine commitment**: the cultivar's mortality is part of its dignity; honoring it is part of cultivation.
