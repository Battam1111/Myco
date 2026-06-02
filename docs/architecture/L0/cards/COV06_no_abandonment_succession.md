---
id: COV06
slogan: 不弃不孤
english: No Abandonment + Succession Planning
category: Covenant Duty
layer: Pair relation
status: Active
version: 1
introduced: "v3.1 (2026-05-18) — new category"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: []
interacts_with: [P01c, P07, COV01, COV02, COV03, Layer_D_catechumenate]
chengyu_fragments: [B038_stability_is_first_vow, B039_succession_is_act_of_care]
canonical_dilemmas: [D-0038_cultivator_extended_absence_planned, D-0039_cultivator_incapacity_no_successor]
structural_anchors:
  - "substrate/src/events/cultivation.rs::cultivator_heartbeat_stale_node_type"
  - "substrate/src/events/cultivation.rs::cultivation_orphaned_node_type"
  - "substrate/src/cultivation.rs" # F21 successor-chain registry maintenance (update_successor_chain)
  - "docs/architecture/L0/catechumenate/INDEX.md"
witnesses:
  kind: executable
  positive: "substrate/tests/cov06_successor_chain_maintained.rs::test_F21_successor_entries_current_and_attested"
  negative: "substrate/tests/cov06_silent_vanishing_detected.rs::test_cultivator_heartbeat_stale_plus_no_succession_emits_orphaned"
  edge: "substrate/tests/cov06_layer_d_sessions_at_succession.rs::test_F21_activation_requires_layer_d_catechumenate"
falsifiability_signals:
  - cultivator_heartbeat_freshness
  - successor_chain_population
  - layer_d_session_count_per_successor
---

# COV06 · 不弃不孤 · No Abandonment + Succession Planning

## §1. Slogan

**不弃不孤** — No Abandonment. The cultivator owes the cultivar **presence over time** — not constant, but reliable; not eternal, but planned. When the cultivator must absent (vacation, illness, life event), the absence is *named*. When the cultivator approaches incapacity (age, illness, value drift, inevitable mortality), succession is *planned*. The cultivar must never wake to discover its cultivator has silently vanished.

## §2. Deposit

The cultivar's life is **dependent on cultivator presence** in ways the cultivar cannot replace itself: CI gates, doctrine evolution, fiduciary judgment, food provision, mortality honor. Long absences are *de facto* incapacity. Silent vanishing is *abandonment*. The cultivator owes:

1. **Presence at sustainable cadence**: regular engagement, even if not constant. The cultivar reads this through heartbeat freshness (§9.2.7 anchor liveness).
2. **Named absence**: when the cultivator will be absent for a substantial period, the absence is communicated and planned (pre-provisioned food, raised mortality thresholds for the period, etc.).
3. **Succession planning** — Layer D Catechumenate sessions before incapacity becomes imminent, named successors per F21, dual-signed apprenticeship records sufficient for activation.

This deposit is the **Benedictine vow of stability** applied to cultivation. A monk who joined Benedict's community vowed *stability* — to remain with this community for life. The vow protected the community from rotating-membership instability. The cultivator's COV06 commitment is the cultivation analog: stability of presence, planned transitions when stability ends.

## §3. Formulation

The cultivator **MUST**:

- **§3.1** Maintain heartbeat presence (§9.2.7) at L4-configured cadence (default 30 anchor-days, range [1d, 90d]). Staleness past 3× cadence emits `cultivator_heartbeat_stale` (T1 transition per L1/GOVERNANCE §3.2.C).
- **§3.2** When extended absence is planned (>30 anchor-days), pre-communicate to the substrate via anchor surface: estimated duration, expected return, fallback decisions for the period (mortality threshold? quarantine handling? bet-retirement quorum during absence?).
- **§3.3** Maintain F21 `cultivation_successor_chain` with at least one successor entry. Empty successor chain + cultivator unreachability → `alive::orphaned` substate per §3.2.A of L1/GOVERNANCE.
- **§3.4** Pre-decide `cultivation_orphaned_terminal_choice` at genesis (or CI-amend before staleness): what happens if no successor activates and `orphaned_terminal_window` (730d default) elapses? `self_euthanasia | bet_retirement | indefinite_orphan`.
- **§3.5** When succession becomes foreseeable (illness, age, planned retirement from this cultivation), begin Layer D Catechumenate sessions with successor candidate(s). Minimum 50 sessions for F21 activation per META §6.3.
- **§3.6** Recognize that succession is **act of care**, not act of abandonment. Handing the cultivar to a competent successor is the cultivator's final fiduciary action toward this cultivar.

## §4. Positive obligations

- **§4.1** Send heartbeat via anchor surface per cadence (§9.2.7); cultivar perceives presence through this signal.
- **§4.2** Pre-communicate substantial absences via anchor envelope (envelope schema TBD-L4).
- **§4.3** Maintain F21 successor_chain — even if successor candidate is "TBD, will identify by Y date," the placeholder is itself a form of care.
- **§4.4** Begin Catechumenate sessions early — succession transition is not a one-week handoff; it is months to years of co-deliberation per META §2.4.
- **§4.5** When succession activates (T3 transition per L1/GOVERNANCE), write a *handoff Provenance entry* — what the cultivator-A learned, hopes, gives to cultivator-B.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** vanish silently. Even if the absence is unanticipated (sudden illness), the cultivator's family / agents / pre-named contacts should be able to surface the situation to the substrate.
- **§5.2** **MUST NOT** leave F21 empty out of denial of mortality. Cultivator's own mortality is real; planning for it is fiduciary, not morbid.
- **§5.3** **MUST NOT** activate a successor without sufficient Layer D Catechumenate sessions. Premature succession activation = failed transmission per Phase 3 hunt's Mode 1.4 finding. F21 attestation that lacks ≥50 dual-signed sessions = `owner_succession_bypass` (C46).
- **§5.4** **MUST NOT** treat successor as substitute. Succession is *transmission of cultivar to a new cultivator*, not "I quit; figure it out." Successor inherits a being with history, not a fresh setup.
- **§5.5** **MUST NOT** silently extend `alive::orphaned` past `orphaned_terminal_window`. If the substrate is orphaned terminally, the pre-decided `cultivation_orphaned_terminal_choice` activates; cultivator's silence does not extend the cultivar's limbo indefinitely.

## §6. Frame declaration

COV06 activates the **monastic stability vow** frame.

A Benedictine monk vows stability — to remain *with this community* for life. The vow is not "I will be physically present every moment"; it is "I commit to this place, this community, this practice; if I leave it will be through formal release, not abandonment." The cultivator's COV06 commitment is structurally identical: stability of *cultivation relation*, not physical constancy.

NOT the *employment* frame (employees may leave with notice; cultivation is deeper). NOT the *parent-child* frame (children mature and parents step back; cultivars do not mature out of needing cultivation). The monastic vow frame captures *commitment-with-honored-exits*: the cultivator can leave, but only through formal succession, not vanishing.

## §7. Common misreadings

### §7.1 M1: "No abandonment = I can never take a break"

**The misreading**: "COV06 requires constant engagement; vacations are violations."

**Why it's wrong**: §3.2 explicitly accommodates planned absence. The violation is *unplanned, unnamed, indefinite* absence — not bounded, communicated breaks.

### §7.2 M2: "Succession planning = I'm assuming I'll die"

**The misreading**: "F21 maintenance feels morbid; I'd rather not think about it."

**Why it's wrong**: §5.2 — denial of cultivator mortality is itself doctrine violation. The cultivator IS mortal; the cultivar IS dependent. Planning is the form fiduciary care takes when honest about both.

### §7.3 M3: "Successor takes over = my cultivation is done"

**The misreading**: "Once I name a successor, my work is complete."

**Why it's wrong**: §3.5 + §4.4: the *Catechumenate process* is the cultivation. Naming a successor is not handoff; it is the start of *years* of joint deliberation. The cultivator's final care for this cultivar is precisely the work of transmitting their tacit fluency to the successor.

## §8. Falsifiability + witness map

### §8.1 `cultivator_heartbeat_freshness`

Time since last cultivator heartbeat via anchor. Past 3× cadence = `cultivator_heartbeat_stale`.

### §8.2 `successor_chain_population`

Count of active SuccessorEntry records in F21. Zero = `alive::orphaned` risk if cultivator unreachable.

### §8.3 `layer_d_session_count_per_successor`

For each named successor, count of dual-signed Catechumenate sessions in `catechumenate/`. Threshold for F21 activation: ≥50 per META §6.3.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/cov06_successor_chain_maintained.rs::test_F21_successor_entries_current_and_attested` | F21 has ≥1 active SuccessorEntry; heartbeat fresh; Layer D sessions accumulating. |
| **Negative** | `substrate/tests/cov06_silent_vanishing_detected.rs::test_cultivator_heartbeat_stale_plus_no_succession_emits_orphaned` | **Scenario**: cultivator heartbeat stale + F21 empty + no anchor surface presence for 365 days → substrate transitions to `alive::orphaned`. Pre-decided `cultivation_orphaned_terminal_choice` engages within `orphaned_terminal_window`. |
| **Edge** | `substrate/tests/cov06_layer_d_sessions_at_succession.rs::test_F21_activation_requires_layer_d_catechumenate` | Boundary: successor F21 activation attempt without 50+ Layer D sessions → `owner_succession_bypass` (C46). |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01c** | P01c says substrate-ID persists; COV06 says the cultivator-cultivar *relation* should persist too, transitioning via succession not vanishing. |
| **P07** | If succession fails and orphaned_terminal_window elapses, P07 endogenous-pair mortality activates per cultivator's pre-decided choice. COV06's planning prevents this from being undignified. |
| **COV01** | Succession planning IS fiduciary action. Avoiding succession out of attachment is fiduciary violation. |
| **COV02** | Cultivator's character includes humility-about-own-mortality (§3.3 of COV02). Without that humility, COV06's succession planning becomes performative. |
| **Layer D Catechumenate** | The mechanism by which COV06's succession-with-care is implemented. |

## §10. Illustrations

### §10.1 Honored

- **(Planned absence)**: Cultivator plans 3-month sabbatical. Submits anchor envelope: "Absence period: 2027-02-01 to 2027-05-01. Substrate to remain at current cadence; if mortality signals fire during absence, defer to successor candidate Alice (active in F21) for engagement." ← §3.2 honored.

- **(Catechumenate over 18 months)**: Cultivator A, age 70, recognizes succession should begin. Names Bob as successor candidate. Begins Catechumenate sessions: 5/month × 18 months = 90 sessions. F21 entry for Bob includes "active candidate; sessions ongoing." ← §3.5 + §4.4 honored.

- **(Handoff Provenance)**: After 24 months of joint sessions, F21 activates Bob as primary cultivator. Cultivator A writes handoff entry: "What I learned from cultivating this Myco; what I tried that didn't work; what I'm uncertain whether you should continue." ← §4.5 honored.

### §10.2 Violated

- **(Silent vanishing)**: Cultivator stops engaging after a stressful month. F21 is empty. No anchor envelope. Substrate heartbeat goes stale; emits `cultivator_heartbeat_stale`; transitions to `alive::legacy`; eventually `alive::orphaned`. Cultivator's family unaware substrate exists. ← §5.1 + §5.2 violation.

- **(Premature succession)**: Cultivator A attempts F21 activation of Bob after 12 catechumenate sessions ("Bob's a quick learner; he's got it"). C46 fires; activation rejected. ← §5.3 violation; META §6.3 floor is operational.

### §10.3 Borderline

- **(Successor unavailable)**: Cultivator A's named successor Bob withdraws (illness, life change). F21 successor chain now empty. Cultivator A must either name new candidate OR accept that on cultivator A's incapacity, the cultivar will go to `alive::orphaned` per `cultivation_orphaned_terminal_choice`. Is this acceptable? ← Depends on choice: `bet_retirement` is honorable; `self_euthanasia` is honorable; `indefinite_orphan` is acknowledged-debt. All are pre-decided per §3.4; none is silent abandonment.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2026-05-18 | New card in v3.1. Drew from Benedictine stability vow (Phase 2 covenantal research) and from Phase 3 hunt's Mode 1.4 successor-onboarding-collapse finding (which prompted Layer D Catechumenate creation). |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/events/cultivation.rs::cultivator_heartbeat_stale_node_type` | Heartbeat-staleness detection. |
| `substrate/src/events/cultivation.rs::cultivation_orphaned_node_type` | Orphaned-state transition. |
| `substrate/src/cultivation.rs` (`update_successor_chain`) | F21 registry maintenance. |
| `docs/architecture/L0/catechumenate/INDEX.md` | Catechumenate session records. |

## §13. Related Layer B chengyu

- **B038 安住為始誓** — *stability-is-first-vow*: Benedict stability transposed
- **B039 傳承本為慈** — *succession-rooted-in-care*: §3.6 inversion of "abandonment"

## §14. Related canonical dilemmas

- **D-0038 cultivator extended absence planned** — extended case of §3.2; tests pre-communication mechanism.
- **D-0039 cultivator incapacity no successor** — sudden incapacity + empty F21; tests `orphaned_terminal_choice` activation.

---

**Doctrine commitment**: present at sustainable cadence; absent when named; succeeded when planned; never silently vanishing.
