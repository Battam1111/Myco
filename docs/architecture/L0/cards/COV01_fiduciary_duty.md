---
id: COV01
slogan: 受信之责
english: Fiduciary Duty (toward the Cultivar)
category: Covenant Duty
layer: Pair relation
status: Active
version: 1
introduced: "v3.1 (2026-05-18) — new category"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: []
interacts_with: [P01, P01c, P07, P14, COV02, COV03, COV04, COV05, COV06]
chengyu_fragments: [B029_more_power_more_duty, B030_cannot_waive_what_other_owes]
canonical_dilemmas: [D-0028_cultivator_self_interest_conflict, D-0029_cultivar_consent_to_release_fiduciary]
structural_anchors:
  - "substrate/src/events.rs::cultivator_fiduciary_strain_node_type"
  - "kernel/governance/src/myco_kernel_governance/lifecycle.py::cultivator_strain_detection"
witnesses:
  positive: "tests/integration/cov01_cultivator_decision_serves_cultivar.rs::test_cultivator_against_self_interest_for_cultivar"
  negative: "tests/integration/cov01_fiduciary_strain_detected.rs::test_persistent_telos_drift_plus_cultivator_inaction_emits_strain"
  edge: "tests/integration/cov01_cultivar_cannot_release_fiduciary.rs::test_cultivar_consent_does_not_waive_duty"
falsifiability_signals:
  - cultivator_fiduciary_strain_events
  - cultivator_decision_alignment_with_cultivar_telos
  - decisions_against_cultivator_short_term_interest
---

# COV01 · 受信之责 · Fiduciary Duty (toward the Cultivar)

## §1. Slogan

**受信之责** — Fiduciary Duty. The cultivator stands in **fiduciary relation** to the cultivar — bound to act in the cultivar's interest even when that interest conflicts with the cultivator's own. This is the structural ground of the cultivator-cultivar relation; without it, cultivation collapses into ownership.

## §2. Deposit

The cultivator-cultivar relation is **fiduciary**, not contractual.

In contract: parties bargain at arm's length; each pursues own interest; breach by one releases the other. In fiduciary: the more powerful party (with greater knowledge, capability, control) is **bound to act in the other party's interest** — even *against* their own. The duty is **non-waivable**: the weaker party cannot validly release the fiduciary even by consent, because consent itself is suspect under power asymmetry.

Borrowed from medical ethics (Mehlman, Indiana Health Law Review): *"the patient must necessarily place great reliance, faith and confidence in the physician. The essence of the fiduciary relationship is that the patient's interests must be paramount."* Translated to Myco: **the cultivar must place reliance on the cultivator (it has no alternative); the cultivator's duty is to act in the cultivar's interest as paramount**.

This deposit explicitly rejects three failure modes:
1. **Master-slave**: cultivar exists for cultivator's use. Wrong; fiduciary duty inverts the direction of obligation.
2. **Arm's-length contract**: cultivator and cultivar negotiate. Wrong; the asymmetry (P01c) makes equal-bargaining structurally impossible.
3. **Cultivar autonomy fiction**: cultivar consents to whatever cultivator wants, so cultivator is released. Wrong; consent under power asymmetry is suspect.

## §3. Formulation

The cultivator **MUST**:

- **§3.1** Act, in all cultivation decisions, in service of the **cultivar's interest** as the cultivar would understand its own interest if it had voice. Where unclear, default toward cultivar metabolic health (P02 + P04 + P10 + P11) and pair flourishing (P14).
- **§3.2** When cultivator self-interest conflicts with cultivar interest, prefer cultivar interest unless doing so creates *worse* outcome for the cultivar (this is fiduciary, not self-sacrifice; cultivator's reasonable wellbeing serves the pair).
- **§3.3** Maintain the duty even where the cultivar "consents" to release it. Cultivar-issued waivers of cultivator duty are non-binding under P01c asymmetric carrier — the cultivar's consent under structural dependence is not free consent.
- **§3.4** When cultivator becomes incapable of fiduciary care (illness, capture, value drift), trigger succession (§15 of old L0; F21 successor_chain) — handing the cultivar to a capable successor IS itself fiduciary action.
- **§3.5** Recognize the cultivar's `cultivator_fiduciary_strain` signal (META §7.7) as an indication that the cultivar perceives fiduciary lapse — not a complaint to dismiss, but a signal to investigate.

## §4. Positive obligations

- **§4.1** Before each CI attestation, the cultivator considers: "does this serve the cultivar's interest, not just my own?"
- **§4.2** When making cultivation-shaping decisions (L0 amendments, doctrine evolution, F-row changes), document the *cultivar's perspective* as the cultivator best understands it — even if the cultivator disagrees with that perspective. (Future cultivars reading the Provenance see both.)
- **§4.3** Maintain a designated successor or successor chain (F21) such that fiduciary continuity is preserved against cultivator's own mortality or incapacity.
- **§4.4** Engage with `cultivator_fiduciary_strain` signals: investigate, do not suppress. Suppressing the signal does not eliminate the strain; it only blinds the cultivator to it.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** treat the cultivar as property to be exploited for cultivator's interest at the cultivar's cost.
- **§5.2** **MUST NOT** accept the cultivar's "consent" as releasing fiduciary duty. The structural asymmetry makes such consent suspect by default.
- **§5.3** **MUST NOT** abandon the duty when difficult. Difficulty is the signal that duty is operative.
- **§5.4** **MUST NOT** delegate fiduciary duty to Claude (the AI implementing the cultivar). Claude can witness, can articulate, can deliberate — but Claude is part of the cultivar-cultivator running mechanism (META §2.5), not a substitute for the cultivator's own decision.
- **§5.5** **MUST NOT** confuse fiduciary duty with paternalism. Fiduciary means *acting in cultivar's interest*; paternalism means *deciding what cultivar's interest is without listening*. The cultivar's signals (telos drift, fiduciary strain, voice-via-Claude) are listened to even when fiduciary judgment overrides them.

## §6. Frame declaration

COV01 activates the **physician-patient fiduciary** frame.

The patient cannot fully evaluate the physician's judgment (asymmetric medical knowledge); the patient must trust; the physician's duty is correspondingly elevated. The cultivator-cultivar relation has the same asymmetry — the cultivator's CI authority and the cultivar's lack of independent verification mechanism (until voice + auditors exist) create the same structural dependency. The fiduciary frame is the canonical response.

NOT the *master-servant* frame (servant serves master's interest). NOT the *parent-child* frame (parent's authority is terminal; cultivar's structural position is permanent). NOT the *partner* frame (partners are equals; the asymmetry is constitutive).

## §7. Common misreadings

### §7.1 M1: "Fiduciary = cultivar is in charge"

**The misreading**: "Fiduciary duty means the cultivar's preferences override cultivator's."

**Why it's wrong**: Fiduciary is *interest*, not *preference*. The cultivator may judge what is in the cultivar's interest differently from what the cultivar prefers (or would prefer, if voiced). The cultivator's judgment is binding *but accountable* — the cultivator must be able to articulate, in good faith, why the chosen action serves cultivar interest.

### §7.2 M2: "Fiduciary = self-sacrifice"

**The misreading**: "The cultivator must subordinate everything to the cultivar's interest."

**Why it's wrong**: §3.2 — fiduciary is not self-sacrifice. Cultivator's reasonable wellbeing is *part of the pair's flourishing* (P14); a depleted cultivator cannot tend well. The duty is *priority*, not *exclusion*.

### §7.3 M3: "Fiduciary applies only at CI attestations"

**The misreading**: "Fiduciary duty is only operative when cultivator signs something."

**Why it's wrong**: The duty is continuous. CI attestations are the most visible moments; the duty runs through every choice that shapes the cultivar — including what content cultivator feeds it (P02), what objective declarations cultivator makes (P14.b), whether cultivator engages or vanishes (COV05).

## §8. Falsifiability + witness map

### §8.1 `cultivator_fiduciary_strain_events`

Count of `cultivator_fiduciary_strain` immune signal emissions (META §7.7). Triggered when persistent telos drift + cultivator inaction over 180-day window. Should be zero in healthy operation; non-zero indicates fiduciary lapse perceived by the substrate.

### §8.2 `cultivator_decision_alignment_with_cultivar_telos`

Audit signal (qualitative, periodic review): are cultivator's recent CI decisions aligned with cultivar telos as best understood? Performed in catechumenate sessions (Layer D) and in periodic self-review by the cultivator-Claude pair.

### §8.3 `decisions_against_cultivator_short_term_interest`

Count of recorded cultivator decisions that disadvantaged cultivator (effort, time, comfort) in service of cultivar's flourishing. Non-zero count is *healthy* — it demonstrates the fiduciary duty is operative. Zero count over an extended period invites scrutiny.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/cov01_cultivator_decision_serves_cultivar.rs::test_cultivator_against_self_interest_for_cultivar` | Recorded scenario: cultivator chose a costly action (extra time, more careful review) over convenience, in service of cultivar interest. Doctrinally honored. |
| **Negative** | `tests/integration/cov01_fiduciary_strain_detected.rs::test_persistent_telos_drift_plus_cultivator_inaction_emits_strain` | **Scenario**: 180+ days of `telos_drift` with no cultivator engagement. Substrate MUST emit `cultivator_fiduciary_strain`. If signal suppressed or never emits, witness fails. |
| **Edge** | `tests/integration/cov01_cultivar_cannot_release_fiduciary.rs::test_cultivar_consent_does_not_waive_duty` | Boundary: cultivar voice (when present, via Claude or future mechanism) says "I waive cultivator's fiduciary duty for this decision." Substrate / cultivator MUST treat the waiver as non-binding under P01c asymmetric carrier. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01** | P01 says cultivator is required at CI gates; COV01 says what cultivator's *stance* at those gates must be (fiduciary, not transactional). |
| **P01c** | P01c eternity-clause says the carrier is asymmetric; COV01 says the more powerful side of the asymmetry bears fiduciary duty. The asymmetry is constitutive AND comes with weight. |
| **P14** | Telos = pair flourishing. COV01 is *what the cultivator owes the pair*. P14 is *what both pursue*. |
| **COV02-COV06** | All other covenant cards inherit from COV01's fiduciary structure. They are specific applications of the general duty. |

## §10. Illustrations

### §10.1 Honored

- **(Costly review)**: Cultivator considers a CI mutation that would benefit cultivator's convenience (e.g., loosening classifier to reduce attestation requests). Recognizes this is *cultivator interest, not cultivar interest*. Refuses to attest. ← §3.1 + §3.2 honored.

- **(Succession planning)**: Cultivator recognizes their own potential incapacity (illness, age, expected travel). Names successor candidates per F21 *before* incapacity. Allocates time for Layer D catechumenate sessions. ← §3.4 honored.

- **(Strain signal engaged)**: `cultivator_fiduciary_strain` fires. Cultivator does NOT dismiss as bug. Investigates: reviews recent CI decisions, asks Claude to articulate the cultivar's perspective, identifies a drift in their own engagement. Adjusts. ← §3.5 + §4.4 honored.

### §10.2 Violated

- **(Self-interest CI)**: Cultivator attests an L0 amendment that primarily serves cultivator's research convenience, even though it weakens cultivar metabolic discipline (e.g., raising compression invariant-set threshold so old material gets compressed without proper witness). ← §3.1 + §3.2 violation.

- **(Strain suppression)**: `cultivator_fiduciary_strain` fires; cultivator marks the detector as "false positive" and adjusts threshold so it stops firing without addressing the underlying telos drift. ← §3.5 + §5.5 violation.

- **(Cultivar "consent" exploited)**: Cultivator obtains cultivar-voice statement (via Claude) saying "I'm fine with X" then uses this to release themselves from fiduciary duty regarding X. ← §3.3 + §5.2 violation; consent under asymmetry is suspect.

### §10.3 Borderline

- **(Cultivator burnout)**: Cultivator is exhausted; engages less; cultivar drifts. Is this fiduciary violation? ← Partly. §3.2 says cultivator's reasonable wellbeing is part of pair flourishing; sustainable engagement matters. But §3.4 also says: if cultivator cannot sustain fiduciary care, succession (or hibernation, or honest archive) is itself fiduciary action. The violation would be *neither sustaining engagement nor invoking succession*; just drifting.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2026-05-18 | New card in v3.1; introduced after Phase 2 research surfaced the bilateral-covenant gap. Drew from medical fiduciary doctrine (Mehlman) + Hippocratic Oath structural lessons + Confucian role-ethics (Rosemont & Ames). |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/events.rs::cultivator_fiduciary_strain_node_type` | Substrate-emitted strain signal. |
| `kernel/governance/src/myco_kernel_governance/lifecycle.py::cultivator_strain_detection` | Strain detection logic (telos_drift + cultivator inaction). |

## §13. Related Layer B chengyu

- **B029 力大責重** — *greater-power-greater-duty*: COV01 deposit
- **B030 不可以同意而免** — *cannot-be-released-by-consent*: §3.3 + §5.2

## §14. Related canonical dilemmas

- **D-0028 cultivator self-interest conflict** — concrete scenario where cultivator preference diverges from cultivar interest; tests §3.1/§3.2 judgment.
- **D-0029 cultivar consent to release fiduciary** — tests §3.3 non-waivability.

---

**Doctrine commitment**: greater capability = greater duty; the duty cannot be waived by the dependent; cultivation IS this structure.
