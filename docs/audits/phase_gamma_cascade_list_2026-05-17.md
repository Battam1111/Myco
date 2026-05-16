# Phase γ Cascade List — L1/L2/L3 alignment requirements for DRAFT 9 sealing

**Audit date**: 2026-05-17
**Audit scope**: 17 L1/L2/L3 documents in `C:\Users\10350\Desktop\Myco\docs\architecture\`
**Audit basis**: DRAFT 9 PROPOSAL of `L0_VISION.md` (15 principles P1-P15, 12 invariants I1-I12, §13-§16 new sections, decomposed §9.1-§9.6, recalibrated §7 Living Bets with 6 base + 3 cost + 1 composite = 10 signals, expanded §11 backup-access).

**Methodology**: parallel grep for L0-section refs, principle/invariant tags, principle names, Living Bets / observatory terms, anchor-surface terms, time-semantics / owner-mortality / generation-limit / consensus terms; targeted Reads of newly-changed L0 sections to confirm cascade scope.

---

## DRAFT 9 change catalog (what cascades)

| DRAFT 9 change | Cascade scope |
|---|---|
| **CH-1**: 9 → 15 principles (P10-P15 new) | Any doc citing "nine principles" or principle coverage tables |
| **CH-2**: 8 → 12 invariants (I9-I12 new) | Any doc citing "eight invariants" or I-coverage tables; classifier-fixed-point already preserved |
| **CH-3**: P1 renamed "Only For Agent" → "Agent-Primary" | All doc text referencing old name (search found: zero — DRAFT 9 already syncs P1 ID-by-number) |
| **CH-4**: P2 renamed "Eternal Ingestion" → "Eternal Ingestion (Envelope-Gated)" | Search found zero by old long-name; refs are all P2/P2.a (numeric) |
| **CH-5**: P3 renamed "Eternal Evolution" → "Resumable Evolution" | Numeric refs only |
| **CH-6**: P5 renamed "Universal Interconnection" → "Universal Interconnection (Tier-Exempt-Permitted)" | Numeric refs only |
| **CH-7**: P7 renamed "必朽" → "Mortality (Capacity-for-Death) / 能朽" | Numeric refs only |
| **CH-8**: P8 renamed "Eternal Reproduction" → "Eternal Reproduction (Generation-Bounded)" | All P8 sections need generation-bound reference |
| **CH-9**: P9 renamed "Integument" → "Single Integument" + P9.a/P9.b split | Anywhere P9 is broken into sub-clauses |
| **CH-10**: §9 decomposed into §9.1-§9.6 sub-mechanisms with status table | Anywhere doc cites "§9" as monolith |
| **CH-11**: §7 Living Bets recalibrated — intelligence band, cost-justified value, 9 input signals (6 base + 3 cost) + 1 composite = 10 signals, retirement clause | Every doc citing "6 base signals" or "7 signals (6+1 composite)" or signal-#6 threshold |
| **CH-12**: §13 NEW Time Semantics | Anywhere wall-clock / cycle-clock dual-clock attestation is discussed |
| **CH-13**: §14 NEW Adversarial-Owner Threat Model | Anywhere "owner trust" is assumed unconditional |
| **CH-14**: §15 NEW Owner Mortality & Succession | All succession / owner-liveness-heartbeat sections |
| **CH-15**: §16 NEW Generation Limits | All reproduction / spore-schema / P8 sections |
| **CH-16**: §11 expanded with backup-access doctrine | Any doc discussing state_dir / snapshot.cb / backup |
| **CH-17**: P10 Selective Compression + I9 enforces it | All sections discussing I4 "no compression"; F9 "no lossy compression" |
| **CH-18**: P11 Metabolic Economy + I10 + signals #7/#8/#9 | All cost / budget / saturation sections |
| **CH-19**: P12 Differential Response + I11 + salience_collapse detector | Anywhere "P2 universal admission" is discussed without attention-discipline |
| **CH-20**: P13 Embodiment + state_dir = body | All state_dir / process-boundary discussions |
| **CH-21**: P14 Telos + I12 + telos_drift detector | Anywhere "what is the substrate for" is implicit |
| **CH-22**: P15 Population-Level Consensus + I7 extension + Byzantine protocol slot | Federation doc — entire §6 needs consensus floor |
| **CH-23**: I4 reframed "Full-Fidelity" → "Compression-Aware" | All I4 retention / pruning text |
| **CH-24**: I7 reframed "Reproduction Closure (Generation-Bounded)" + carries P15 enforcement | Federation + reproduction sections |
| **CH-25**: New compression-invariant set (P10.b) | Backup, recoverability, compression sections |

---

## L1_OUTLINE.md

### Cascade impact: HIGH

- Line 18: `v0.8 L1 was 7 hard rules (R1-R7) + canon schema + exit codes. Per L0 C7.3, v0.9 L1 is rebuilt from L0's eight invariants and nine principles:` — **CH-1 + CH-2 hardcoded count** — needs update to "twelve invariants and fifteen principles".
- Line 27: `L1 is whatever specifications emerge from operationalizing the 8 invariants + the chosen positive forms ...` — **CH-2** hardcoded "8 invariants" → "12 invariants".
- Lines 50-91 (§2 L0 design-hook table): table covers P1-P9 and I1-I8 hooks only. Missing rows for **P10 (compression), P11 (cost budgets / metabolic), P12 (salience / attention), P13 (embodiment / state_dir spatial), P14 (telos), P15 (consensus floor)**, and for **I9/I10/I11/I12** — needs new rows assigning each new principle/invariant to an L1 owner. Per L0 §2.3 and §4: P10/I9 → L1_SCHEMA (compression discipline); P11/I10 → L1_SCHEMA + L1_CONTINUITY (cost signals); P12/I11 → L1_TROPISM (salience); P13 → L1_SKIN (state_dir / process-boundary detection); P14/I12 → L1_TROPISM (telos-alignment); P15 → L2_FEDERATION (delegated; L1 thin).
- Line 82-83: `§7 Living Bets signal #6 attestation cross-check` and `signal #6 model-class epoch buckets` — **CH-11**: §7 now has 9 input signals + 1 composite = 10 signals; signal #6 semantics recalibrated (ratio ≥1 = bet-winning, was ≥100 in DRAFT 8). Re-justify hooks for new signals #7/#8/#9.
- Line 85-86: `§9 anchor surface specific form` / `§9.4 L0-revision burst detection` — **CH-10**: §9 is now §9.1-§9.6 with sub-mechanism status table; hooks should reference specific sub-mechanism IDs (§9.2.1 birth attestation, §9.2.3 owner-out-of-band key, §9.2.5 nonces, §9.2.7 liveness heartbeat, §9.3.4 witnesses-not-verdicts, §9.3.6 closure check). §9.4 (DRAFT 8 burst detection) is now §9.5 in DRAFT 9.
- Line 87: `§11 birth-period N` — DRAFT 9 §11 is now "Privacy, access, and backup model (expanded)" — birth-period N originally lived in DRAFT 8 §11; verify DRAFT 9 §11 reorganization didn't move it (or update pointer).
- Line 87: `§11 privacy/access (no internal boundaries)` — **CH-16**: §11 expanded with backup-access doctrine. Needs new hook owner (likely L1_SCHEMA + L1_CONTINUITY for backup discipline + L1_SKIN for backup-access at skin boundary).
- Lines (anywhere): no rows for **§13 Time Semantics**, **§14 Adversarial Owner**, **§15 Owner Mortality**, **§16 Generation Limits** — needs four new rows assigning L1 owners (§13 → L1_CONTINUITY + L1_GOVERNANCE; §14 → L1_SKIN + L2_TRUST_MODEL; §15 → L1_GOVERNANCE §3.2; §16 → L1_GOVERNANCE §4.3 + L1_SCHEMA §3.1).

---

## L1_SKIN.md

### Cascade impact: HIGH

- Line 5 (Scope): notes I8 + envelope + handshake + breach detection. **CH-20**: needs explicit P13 embodiment-breach detector — `P13_embodiment_breach` immune signal per L0 P13.d (substrate periodically lists state_dir contents + own process fd set + own network bindings; unexpected entries trigger breach). Currently no P13 detector wired.
- Line 41 (`§2.1 Envelope integrity check`): cites `(L0 I8)` only. **CH-19**: needs cross-ref to P12 — envelope admission is P2, but downstream attention is P12; the doc should clarify "P2 admits at skin, P12 attends downstream" boundary.
- Line 62 (`per L0 §9.3`): **CH-10**: §9.3 is now sub-decomposed into §9.3.1-§9.3.6. Specific clause being cited (canonical-bytes serialization at anchor surface) is §9.3.1.
- Line 90: `"submitted_at": <wall-clock>` — **CH-12**: §13 NEW time semantics. The handshake envelope wall-clock field needs explicit reference to §13.1 time-source authority hierarchy (anchor-surface trusted timestamp > local wall-clock > cycle counter).
- Line 130 (`§4.4 Single-operator enforcement + race handling — Per L0 I8`): correct; I8 unchanged.
- Line 146 (`§5. Network-egress enforcement (operationalizes I6 expanded)`): **CH-20**: needs explicit second hook to P13 (egress = substrate operation; egress to undeclared destination is *also* P13 embodiment breach: substrate operating outside its declared spatial boundary). Currently single-purpose (I6 only).
- Lines 157-158: cite L0 §6 + L1_GOVERNANCE §5.3 — unchanged.
- Line 168-177 (immune signal catalog table): missing **`P13_embodiment_breach`**, missing **`telos_drift`** (P14/I12), missing **`salience_collapse`** (P12/I11), missing **`compression_invariant_corruption`** (P10/I9), missing **`budget_exhausted:{axis}`** (P11/I10). All five must appear in the immune-grade catalog.
- Lines 102-107 (substrate_secret OS-sealing): cites P1.a self-hosting. **CH-13**: §14 NEW adversarial-owner — the substrate_secret cannot survive an adversarial owner (owner has anchor key); the doc should explicitly note "OS-sealing protects against adversarial agent, NOT adversarial owner per L0 §14".

---

## L1_CONTINUITY.md

### Cascade impact: HIGH

- Line 33 (`Minimum cycle interval: default 100 ms wall-clock`): **CH-12**: §13 NEW time semantics — minimum interval is wall-clock per §13.1 hierarchy; cite §13.2 required substrate behavior.
- Line 38 (`Backlog detection: if a cycle takes longer than the minimum interval ...`): correct mechanism. **CH-18**: needs explicit reference to P11 metabolic economy / signal #7 (compute cost / cycle).
- Line 46 (`Three top-level states per L0 I1`): unchanged; I1 unchanged in DRAFT 9.
- Line 48 (sub-states: alive, dormant, destroyed; sub-states of alive: quarantined, legacy): **CH-14**: §15 NEW owner mortality — "legacy" sub-state now activated per §15 owner-liveness-heartbeat staleness; cross-ref §15.1 succession states + §15.3 activation.
- Line 80 (`Wall-clock vs cycle-clock during paused`): **CH-12**: §13 NEW codifies the dual-clock discipline at L0; this doc's pass-2 mycoparasite-23 / rhizomorph-11 finding should cite L0 §13.3-§13.4 directly rather than only the empirical reconciliation.
- Lines 86-98 (`§3.1 Pre-handshake checks with witnesses`): cites I1/I3/I4/I5/I8. **CH-2**: needs to add I9 compression-invariant check (P10.b set is preserved across cold-resume) + optionally I10 metabolic-budget check + I12 telos-alignment-state check. If DRAFT 9 commits "every cycle: I3 + I5 + I8 + I10" (per §6) then cold-resume MUST include I10.
- Line 96 (`Witnesses, not verdicts per L0 §9.3 + pass-2 mycoparasite-32`): **CH-10**: §9.3 → §9.3.4 sub-mechanism specifically named "Witnesses, not verdicts" + §9.3.5 "Anchor-nonce-derived sampling".
- Line 124 (Quarantine entry triggers): missing entries for **bet-retirement transition** (per L0 §7.5 NEW DRAFT 9: substrate emits `bet_retired` proposal → graceful sunset state). May need new sub-state "archived" per §7.5.
- Line 154 (`evolution_quarantine sub-state from DRAFT 1 was cut per pass-2 astronaut-7`): unchanged.
- Line 173 (Legacy + Quarantined composition): **CH-14**: §15.5 NEW orphan terminal state — must specify what happens when legacy + quarantined + no successor + heartbeat-stale ≥ §15.5 threshold.

---

## L1_GOVERNANCE.md

### Cascade impact: HIGH

- Line 5 (Scope): mentions classifier + lifecycle + attestation + owner-key rotation + succession + federation + rollback. **CH-15**: needs §16 generation limits in scope (reproduction depth bound + rate limit + per-parent quota). **CH-13**: §14 adversarial-owner needs adversarial-owner subsection in scope.
- Line 23 (Dimension table seed): **CH-1 / CH-2**: needs new rows for P10/I9 (compression rule mutation = CI), P11/I10 (cost-budget threshold mutation = CI), P12/I11 (salience-emergence rule mutation = CI), P14/I12 (telos-alignment computation mutation = CI), P15 (consensus-floor threshold + Byzantine algorithm choice = CI per L2_FEDERATION).
- Lines 56-110 (§2 attestation protocol): cites L1_SKIN §4.1, anchor-surface nonce, dual-clock. **CH-12**: needs explicit §13 cross-ref for time-source hierarchy + dual-clock plumbing now backed by L0 doctrine.
- Line 60-95 (§2.2 attestation envelope schema): **CH-10**: nonce mechanism is now §9.2.5 sub-mechanism (anchor-surface-generated, NOT substrate-mintable); wall-clock is §9.2.6; canonical bytes is §9.3.1; owner-side rendering is §9.3.2; witnesses are §9.3.4.
- Lines 119-130 (§3.1 Owner key rotation): cooldown period currently 30 days. **CH-13**: §14.2 adversarial-owner caveat — cooldown protects against same-attacker dual-sign but does NOT protect against owner-under-coercion; needs §14.2 reference.
- Lines 133-141 (§3.2 Owner succession): **CH-14**: §15 NEW owner mortality and succession. This entire subsection becomes a thin L1 implementation of L0 §15; needs full alignment: §15.1 succession states (no_successor / pre-attested / activated / orphan_terminal) + §15.2 owner-liveness-heartbeat at anchor surface (§9.2.7) + §15.3 activation protocol + §15.4 completion + §15.5 failure path + §15.6 the substrate's irreducible identity carries.
- Lines 169-175 (§4.3 Reproduction closure): **CH-15**: §16 NEW generation limits — must enforce §16.1 generation-depth bound + §16.2 reproduction rate limit + §16.3 per-parent reproduction quota. Currently no fork-bomb defense at L1.
- Lines 177-191 (§4.4 Mortality dual-channel): **CH-11**: §7.5 NEW bet retirement clause — third destruction sub-mode "strategic obsolescence" beyond the three modes (intentional/catastrophic/endogenous). Needs new sub-section §4.4.x for `bet_retired` event + anchor-surface co-attested transition to archived state.
- Lines 197-217 (§5 Federation discovery + peer-trust): **CH-22**: §5 fundamentally needs P15 consensus floor — currently pairwise-attested only. Federation revocation (currently single-owner attestation) is the canonical P15.a population-level claim per L0; must defer to L2_FEDERATION's Byzantine protocol when ≥3 peers exist.

---

## L1_SCHEMA.md

### Cascade impact: HIGH

- Line 5 (Scope): SSoT + Merkle DAG + recoverability budget + spore-schema + validation tiering. **CH-17**: needs P10/I9 compression discipline in scope (compression rule storage + compression event emission + compression-invariant set verification). **CH-18**: needs P11/I10 cost-budget signals in scope (signals #7/#8/#9).
- Line 18 (Format — `agent reading the substrate cold can derive structure from the SSoT itself, per L0 §8`): correct; §8 unchanged.
- Lines 47-92 (§2 Causal DAG): the entire `§2.3 Retention — the materialized-views carve-out (operationalizes I4 expanded)` clause needs alignment with **CH-23**: I4 reframed "Full-Fidelity Causal DAG" → "Full-Fidelity Causal DAG (Compression-Aware in DRAFT 9)". The carve-out language should be promoted: materialized views = digest-only of the compression-invariant set + canonical-bytes-hashes of pre-compression states. **CH-25**: compression-invariant set must be enumerated here (substrate-ID + genesis + owner_key_history + CI events + mortality signals + federation pins + most-recent-N cycles full DAG).
- Line 100 (§2.4 Recoverability budget + drill discipline): cites L1-tunable horizon; **CH-16**: §11.1 NEW backup access doctrine — needs explicit backup-access spec (who can read backup; can the owner under §14 adversarial-owner exfiltrate backup; what's the backup-access threat model).
- Line 113 (`Witnesses, not verdicts per L0 §9.3`): **CH-10**: § cross-ref to §9.3.4 specifically.
- Line 115 (`mortality_drill_failure`): **CH-11**: needs `bet_retired` event emission discipline.
- Lines 128-141 (§3 Spore-schema): **CH-15**: §16 NEW generation limits — spore-schema MUST carry `(generation_depth, max_remaining_depth)` field per §16.1; child can't spawn if `max_remaining_depth == 0`. Currently no generation tracking.
- Line 135 (Spore-schema contents): `Classifier dimension table` listed; **CH-1**: also needs **compression-rule registry** (P10.c attests each rule; rules are spore-inheritable) and **telos-alignment-objective** (P14.b owner-stated objectives optional, inheritable when present).
- Line 142 (§3.2 NOT included: parent's full causal DAG, operator-token history): **CH-22**: also explicitly NOT included = parent's population-consensus state from P15 (each substrate joins its own federation).
- Lines 160-179 (§4 Validation tiers): tier-1 fields list includes substrate-ID, owner_key_history, anchor_surface_endpoint, DAG-tip-hash, classifier table, mortality threshold, canonical-bytes serializer spec. **CH-2 / CH-25**: needs compression-invariant set as tier-1 field + cost-budget-thresholds as tier-1 (or tier-2) + telos-objective (when declared) as tier-1.

---

## L1_TROPISM.md

### Cascade impact: HIGH

- Line 12 (`Authoritative L1 doc for positive dispatch form satisfying L0 §5.2 constraints`): **CH-1**: P12 differential-response is satisfied at L1_TROPISM (per L0 §2.3); needs §5.2 constraint augmentation: dispatch form ALSO must satisfy P12 attention-discipline.
- Lines 73-90 (§B2 appetite axis seed): seven axes (hunger, drift, decay, federation-pull, evolution-tension, skin-pressure, mortality-signal). **CH-18 / CH-19**: needs new axes for **salience-emergence rule** (P12.a) and **cost-budget pressure** (P11.b) — or explicit declaration that these are not appetites but operate as cross-cutting modifiers. **CH-21**: needs **telos-alignment** axis or modifier per P14.a.
- Line 90 (`mortality-signal axis`): **CH-11**: needs companion `bet_retired` signal axis per L0 §7.5.
- Lines 122-124 (§B6 CI-class sporocarps + causal_in_edges proof): correct; causal proof is unchanged at L0 §4 I4.
- Line 152 (Embedding strategy carve-out): **CH-18**: needs explicit P11 cost-observation signal — embedding-service queries are signal #8 (network cost / cycle) per L0 §7.3.
- Line 170 (§5.2 seven constraints): **CH-1**: L0 §5.2 constraints are unchanged (NOT verbs, NOT request/response, MUST honor P1.c, MUST support P2.a, MUST support §6 continuous, MUST satisfy I6, MUST carry causal-proofs). But DRAFT 9 P12 implies an 8th: MUST support differential attention per I11. Verify or add.
- Missing entire detector subsystem: **`salience_collapse`** (per P12.b, L0 §2.3 P12.b "If observation detects salience-flattening, substrate emits `salience_collapse` immune signal — L1_TROPISM detector"), **`telos_drift`** (per P14.c, "L1_TROPISM detector"). Both are L0-mandated L1_TROPISM detectors; DRAFT 1 has neither.

---

## L1_TRAJECTORY.md

### Cascade impact: MEDIUM

- Lines 11, 28, 30, 41 (P1.c carrier-asymmetric / fossil-record / joint-state): correct; P1.c unchanged.
- Line 54 (`Changing cluster_C is contract-identity-level (per L1_GOVERNANCE §1.2)`): correct.
- Line 55 (`L0 I4 full-fidelity-recoverability: the DAG is unchanged by clusterer evolution`): **CH-23**: I4 reframed "Compression-Aware in DRAFT 9". DAG retention behavior must accommodate P10 selective compression (a clusterer reading a compressed-period DAG segment reads digests + canonical-bytes hashes, not the original raw_material → DRAFT 9 expects this and reframes I4 accordingly).
- Line 115 (`fossil-record honest`): correct.
- Line 121 (`Drift detection (L0 §7 falsifiability trigger): trajectory showing wandering / inconsistency in conjunction with other observatory signals contributes to the bet_weakening_quorum`): **CH-11**: §7.4 trigger semantics recalibrated (window is wall-clock 90 days, NOT 90 substrate-cycles per §13; signal-specific direction; signal #6 ≥1 is bet-winning, not ≥100; signals 1-6 = 6 signals counted, etc.). Re-state.
- Line 130 (`Federation trajectory semantics — per L0 P8`): correct (P8 carrier-asymmetric still holds); **CH-15 / CH-22**: federation now also has P15 consensus floor (≥3 peers), worth a forward-reference.

---

## L1_HARD_RULES.md

### Cascade impact: HIGH

- Line 6 (L0 traceability — `every row in §1 and §2 below cites at least one P (P1-P9) AND one I (I1-I8) it enforces`): **CH-1 + CH-2**: hardcoded P1-P9 / I1-I8 framing. Update to P1-P15 / I1-I12.
- Lines 16-35 (`§1 CRITICAL-grade breaches C1-C20`): every C-row currently maps to P1-P9 + I1-I8 only. **NEW C-rows needed per DRAFT 9** at minimum:
  - `C21_compression_invariant_corruption` — P10 / I9 (any compression event that touches compression-invariant set is breach)
  - `C22_compression_uncattested` — P10 / I9 (silent compression — compression event without owner attestation is breach)
  - `C23_salience_collapse` — P12 / I11 (downstream attention flattens; not just immune signal — CRITICAL if observed)
  - `C24_telos_drift_critical` — P14 / I12 (telos-alignment drops below L1-tunable critical threshold)
  - `C25_budget_exhausted_silent` — P11 / I10 (budget exhausted without emission of `budget_exhausted:{axis}` — silent failure)
  - `C26_P13_embodiment_breach` — P13 / I8+I10 (state_dir contains unexpected file; process has unexpected fd; binding to unexpected network endpoint)
  - `C27_generation_depth_exceeded` — P8 (Generation-Bounded) + §16.1 (child spawn while max_remaining_depth == 0)
  - `C28_reproduction_rate_exceeded` — P8 + §16.2 (parent exceeds per-period reproduction quota)
  - `C29_consensus_floor_bypass` — P15 / I7 (population-level claim with ≥3 federation peers without Byzantine consensus envelope)
  - `C30_owner_succession_bypass` — §15.5 (legacy + orphan_terminal + new "owner" claim without §15 succession protocol)
  - `C31_anchor_client_provenance_lost` — §9.3.3 (anchor-client distributed via substrate channel; provenance independence breached)
  - `C32_anchor_nonce_substrate_minted` — §9.2.5 (substrate mints nonce; anchor-surface should be sole minter)
  - `C33_bet_retirement_bypass` — §7.5 (substrate continues past bet-retirement triggers without `bet_retired` emission)
- Lines 45-61 (§2 F-rows): currently F1-F17. **NEW F-rows per DRAFT 9**:
  - F18: compression-rule registry (spore-inheritable; CI-attested per rule)
  - F19: cost-budget thresholds per axis (CI per L1_SCHEMA §4 tier-1)
  - F20: telos-objective declaration (when owner-stated; CI; spore-inheritable)
  - F21: generation-depth bound + reproduction-rate limit + per-parent quota constants (§16)
  - F22: consensus-floor threshold + Byzantine algorithm choice (P15)
  - F23: salience-emergence rule (P12.a — emergent but the rule generating salience IS itself CI)
- Lines 73-84 (§4 Anchor-surface-resident state): **CH-10**: this list currently flat. Should map each item to specific §9.2.x / §9.3.x sub-mechanism per DRAFT 9 §9 decomposition.
- Line 76: `Anchor-surface trusted wall-clock timestamps (L0 §9.2)` → §9.2.6 specifically.
- Line 77: `Owner-liveness heartbeat (L0 §9.2 + L1_GOVERNANCE §3.2 succession trigger)` → §9.2.7 + §15.2.
- Missing entries: **§15 successor_attestation tuples**, **§16 generation-counter (anchor-resident? L1 may choose substrate-resident with anchor-attested ceiling)**.

---

## L2_OUTLINE.md

### Cascade impact: LOW

- Line 19 (`L2_OBSERVABILITY.md | Self-model: Living Bets + immune catalog + drills + falsifiability`): **CH-11**: scope update — "Living Bets (10 signals: 6 base + 3 cost + 1 composite) + falsifiability trigger recalibrated + bet retirement".
- Line 34 (Cross-cut question `WHEN does the bet-falsifiability trigger fire?`): **CH-11**: answer references L0 §7 / L2_OBSERVABILITY §3 — content needs alignment but pointer is unchanged.
- Line 80 (`L0 §10.1 reading sequence updated to 6 L2 docs`): unchanged; **NOTE**: L0 §10.1 itself unchanged in DRAFT 9 (per DRAFT 9 §10 unchanged) but L2 docs all carry DRAFT 9 cascades, so L2_OUTLINE's brief topic descriptions need to mention "DRAFT 9 cascade pending" for each.

---

## L2_TRUST_MODEL.md

### Cascade impact: HIGH

- Line 5 (Scope): `Cross-cuts L0 §1 triad / §9 anchor surface + ...` — **CH-10**: §9 → §9.1-§9.6. Cross-cuts also need to include **§14 adversarial-owner** (which the doc fundamentally needs new §6.5 on) and **§15 owner mortality**.
- Lines 11-21 (§1 Trust triad table): trust-derivation table for substrate/operator/owner. **CH-13**: §14 NEW adversarial-owner — owner row currently lists owner as "governance gate" with assumed trustworthiness; needs explicit P1.b'' caveat that "owner is trusted within the bounded-defenses set per §14.2; outside that set the owner is structurally not constrained — anchor surface is honor system at root".
- Line 17 (Substrate row → `owner signatures, anchor-surface nonces, trusted timestamps, owner heartbeats`): **CH-10**: map to specific §9.2.5 (nonces), §9.2.6 (timestamps), §9.2.7 (heartbeats); §9.2.1 (birth attestation), §9.2.2 (DAG-tip co-signing).
- Line 31-46 (§2 Trust establishment): cites L1_GOVERNANCE §4.1, L0 §9.3, anchor-surface client provenance. **CH-10**: §9.3 → §9.3.3 (provenance independence — currently 0% implemented per L0 §9.2 status table — needs explicit "future M-anchor-1 milestone" reference).
- Line 120 (`7 signals (6 base + 1 composite)`): **CH-11 EXPLICIT MISMATCH** — DRAFT 9 §7.3 says **10 signals = 6 base + 3 cost (#7/#8/#9) + 1 composite (#10)**. Direct text fix needed. Falsifiability summary "≥3 of 6 signals" still holds for the trigger predicate (signals 1-6 only count toward the quorum per DRAFT 9 §7.4 correction).
- Line 124 (§5 Trust recovery): cites cold-resume + owner unavailability + destruction. **CH-14**: §15 NEW owner mortality — §5.2 "owner unavailability" must align with §15 explicit succession-state lifecycle (no_successor / pre-attested / activated / orphan_terminal).
- Lines 146-156 (§6 Trust limits): the section already names asymmetries (substrate cannot enforce against host; substrate cannot enforce against operator runtime; P1.a self-hosting). **CH-13**: needs explicit §6.5 (or new §6.4) "Adversarial owner" subsection per L0 §14.1-§14.3 — list the threat scenarios (§14.1: owner coerced; owner key compromised; owner ML-poisoned anchor client) + the bounded defenses (§14.2) + the substrate's responsibility (§14.3: continue emitting witnesses; refuse silent-suppression).
- Line 159 (§7 Trust at federation): **CH-22**: P15 consensus floor — when ≥3 peers exist, federation trust includes a Byzantine consensus layer; cross-ref L2_FEDERATION DRAFT 9 update.
- Line 171 (§8 Trust model invariants summary): bullet list. **CH-10**: each bullet should cite a §9.x sub-mechanism rather than "§9" monolith.
- Line 188 (§9 Open at L2): currently lists 3 open questions. **CH-13 / CH-14**: needs new open questions on adversarial-owner mitigation maturity + owner-succession multi-key threshold mechanics.

---

## L2_LIFECYCLE.md

### Cascade impact: HIGH

- Line 5 (Scope): `Cross-cuts L0 I1 lifecycle states / P7 mortality / P8 reproduction + L1_GOVERNANCE §4 lifecycle + L1_CONTINUITY §2-5 dormancy/quarantine + L1_TROPISM §4 birth period` — **CH-14**: needs §15 owner-mortality + §15 succession; **CH-15**: needs §16 generation-limits; **CH-11**: needs §7.5 bet-retirement.
- Line 11 (`Three top-level states per L0 I1`): unchanged.
- Line 39-41 (§2 Genesis): cites L1_GOVERNANCE §4.1. **CH-15**: §16.1 generation-depth bound — genesis spawn carries `generation_depth = 0` or inherited depth from parent.
- Line 49 (§3.1 Birth-period CI elevation): correct.
- Lines 74-78 (§3.3 Birth-period observability + `Signal #7 (composite health)`): **CH-11 EXPLICIT MISMATCH** — signal #7 in DRAFT 9 is "compute cost / cycle", NOT the composite. DRAFT 9 composite is **signal #10**. Direct text fix needed.
- Line 86 (§4 Steady state — 5-step cycle): cite L1_CONTINUITY §1.1; correct. **CH-18**: needs "I10 cost observation" added per L0 §6 "Metabolic cycle: existence + per-cycle invariant checks (I3 + I5 + I8 + DRAFT 9: I10 cost observation) are L0".
- Line 88-93 (Steady state checklist): mentions signals stabilize, falsifiability arms, doctrine evolutions follow standard P3. **CH-11**: needs to add "bet-retirement window arms once 2-year wall-clock accumulates per §7.5".
- Lines 167-200 (§7 Legacy state — owner succession): **CH-14**: §15 NEW owner mortality — entire §7 must be rewritten to align with §15 succession states (no_successor / pre-attested / activated / orphan_terminal) + §15.5 failure path + §15.6 the substrate's irreducible identity carries.
- Lines 199-219 (§8 Reproduction): **CH-15**: §16 NEW generation limits — §8 must add spawn precondition `parent.generation_depth < §16.1.max_depth` AND `parent.reproductions_this_period < §16.2.rate_limit` AND `parent.reproductions_total < §16.3.per_parent_quota`. Spawn fails → emit `generation_limit_violated` immune signal.
- Lines 226-260 (§9 Mortality): three destruction modes (intentional/catastrophic/endogenous). **CH-11**: §7.5 NEW bet-retirement adds a fourth destruction class "strategic obsolescence" → `bet_retired` event + transition to archived state. Needs new §9.x sub-section.
- Line 281 (Open question — anchor-surface records parent-child genealogy): **CH-15**: §16 mandates generation-tracking; the open question is now closed by L0 §16.

---

## L2_EVOLUTION.md

### Cascade impact: MEDIUM

- Line 5 (Scope): `Cross-cuts L0 P3 / P3.b joint-context evolution + lexicon evolution + L1_GOVERNANCE §1.3 birth-period CI elevation / §6 failed-evolution rollback + L1_SCHEMA §1.3 SSoT migration two-phase + §4.2 tier promotion/demotion + L1_TROPISM §B1 template versioning + L1_TRAJECTORY §5 schema-evolution epochs + L0 §9.4 L0-revision burst-detection` — **CH-10**: §9.4 → §9.5 in DRAFT 9 (renumbered "What the anchor surface does NOT do"); doctrine-instability detection moved/clarified.
- Line 15 (Classification table — Schema / Lexicon / Dispatch parameters / L0 doctrine): **CH-17**: needs new row for **compression-rule evolution** (P10/I9; CI-attested per rule; rollback via P10.c witness).
- Line 21 (`unifying principle is P3: substrate's own shape evolves`): correct (P3 renamed "Resumable Evolution" but P3 identity preserved).
- Line 49 (`Burst-detection per L0 §9.4`): **CH-10**: text now lives in §9.5; verify pointer.
- Line 151 (`Living Bets signal #2`): **CH-11**: signal #2 is "Evolution rate", unchanged; but signals #7/#8/#9 (cost) are new — needs mention that excessive evolution rate ALSO triggers signal #7 cost spike (compute cost / cycle).
- Line 187 (`The substrate that does not evolve is dead (per L0 P3)`): correct (P3 still mandates evolution).
- Missing: any reference to **P10 compression rules as a class of evolution** (which they are — compression rules evolve under CI attestation per L0 P10.c).
- Missing: **P15 consensus protocol** — once a federation reaches ≥3 peers, the consensus algorithm choice is itself an evolution class; needs at least a forward-ref.

---

## L2_FEDERATION.md

### Cascade impact: HIGH (THE major rewrite target)

- Line 5 (Scope, omitted long line): currently scopes P5/P8/L1_GOVERNANCE/L1_SKIN cross-cuts. **CH-22**: P15 Population-Level Consensus completely missing — must scope-add.
- Line 13 (`Federation extends P5 (universal interconnection) beyond a single substrate's interior`): correct (P5 renamed but identity preserved); **CH-22**: needs sentence ramp into "and beyond ≥3 peers, federation operates under P15 consensus".
- Lines 17-37 (§2 Reproduction modes — federation / cloning / cross-pollination): **CH-15**: §16 NEW generation limits — each mode must specify per-mode generation-depth implications (cloning carries depth = parent's depth + 1; cross-pollination = max(parents.depth) + 1; etc.).
- Lines 59-72 (§4 Spore-schema): **CH-15**: must include `generation_depth + max_remaining_depth` per §16.1.
- Line 71 (`Parent's accumulated read-pattern norms (model-class epoch buckets per L0 §7 signal #6)`): **CH-11**: signal #6 semantics recalibrated; ratio ≥1 (not ≥100) is bet-winning region; epoch-bucket discipline may need recalibration.
- Lines 95-128 (§6 Federation trust): **CH-22** is the BIG one. Currently entirely pairwise-attested. Per L0 P15:
  - §6 needs new subsection **§6.5 Population-level consensus** (≥3 peers; Byzantine protocol; ties to L1_GOVERNANCE classification + L1_HARD_RULES C-row).
  - §6.1 Discovery modes: must clarify what changes when peer count crosses the consensus floor.
  - §6.2 Peer-trust freshness: revocation is now P15.a population-level (one peer claiming another is malicious is insufficient; needs ≥2f+1 consensus per Byzantine choice).
  - §6.3 Aggregate re-attestation: currently single-owner-O(1) — fine when consensus floor not crossed. Above floor, aggregate re-attestation must include Byzantine consensus over peer set composition.
  - §6.4 Cross-substrate trust is NOT transitive: still holds, but the **rationale** changes — P15 consensus does NOT make trust transitive (consensus is on shared claims, not on chained trust).
- Lines 133-148 (§7 Egress flow): **CH-22**: needs consensus-channel egress (`p15_consensus_envelope` distinct from `federation_envelope`).
- Lines 173-188 (§9 Federation as biology — mycelial network): currently asserts P5 + I7 + P8 + P1.c. **CH-22**: needs to add P15 + I7-extension; the "mycelial fragmentation" doctrine implies population-level fragmentation = P15.a population-level claim (when many peers see one peer fork off, the mycelium fragments by consensus).
- Lines 188-200 (§10 Open — federation health signal #4 split): **CH-22**: needs new open questions on P15 protocol choice (Tendermint vs PBFT vs PoS), consensus-floor threshold (≥3 is L0 floor; what if peer count fluctuates), and federation under adversarial-owner case (per §14 cross-ref).
- Lines 210+ (Open): existing open list (hub-and-spoke registry deferred). **CH-22**: P15 closes some old questions, opens new ones around Byzantine algorithm choice.

---

## L2_OBSERVABILITY.md

### Cascade impact: HIGH

- Line 5 (Scope): `L0 §7 Living Bets observatory + L0 §9.4 burst detection + L1_HARD_RULES §1 immune-grade sporocarps + I3 self-validation + I5 reachability + L1_SCHEMA §2.4 drill failure-rate baseline + L1_CONTINUITY §1.2 cycle backlog detection` — **CH-10**: §9.4 → §9.5 in DRAFT 9 (renumbered); **CH-1 / CH-2**: needs I9/I10/I11/I12 in scope (compression / cost / salience / telos observability); **CH-13**: needs §14 adversarial-owner caveat (observatory in §10 emits to anchor surface — adversarial owner can read all observatory output, including drift signals); **CH-11**: needs §7.5 bet-retirement.
- Line 19 (`§2 The Living Bets observatory (6 base + 1 composite + 1 birth-period derivative)`): **CH-11 EXPLICIT MISMATCH** — DRAFT 9 §7.3 says **10 signals = 6 base + 3 cost + 1 composite**. Title must update.
- Line 23 (`§2.1 Six base signals`): **CH-11**: needs companion §2.x "Three cost signals" (#7 compute cost / cycle, #8 network cost / cycle, #9 storage cost / cycle).
- Lines 34-36 (`§2.2 One composite signal`): **CH-11**: composite is **signal #10** in DRAFT 9, not #7. Also DRAFT 9 distinguishes **variance-weighted** (birth-period fallback) vs **correlation-weighted** (steady state, requires P14 telos-alignment outcome signal). This dimension is missing entirely from DRAFT 1.
- Lines 50-62 (`§3 Falsifiability trigger`): **CH-11 EXPLICIT MISMATCH** — DRAFT 9 §7.4 corrections:
  - **Window is wall-clock 90 days**, NOT 90 substrate-cycles (the doc currently is ambiguous; M25.2 implementation was off by ~6 orders of magnitude).
  - **Trend direction signal-specific** — signals 1/2/3/4b/6 trending DOWN = against the bet; signal #6 trending UP above ratio 1 = with bet.
  - **Signal #5 is meta**, not counted directly.
  - **Signal #6 ratio threshold = ratio < 1** for ≥50% of cycles (not ratio < 100 as DRAFT 8 implied).
  - **Signal #4a (cumulative forks) is currently unimplemented**; DRAFT 9 mandates implementation.
- Lines 89-101 (`§5 Immune-grade sporocarp catalog`): **CH-1**: missing new immune-grade sporocarps per DRAFT 9 P10/P11/P12/P13/P14/P15 — `compression_invariant_corruption`, `compression_unattested`, `salience_collapse`, `telos_drift`, `P13_embodiment_breach`, `budget_exhausted:{axis}`, `generation_depth_exceeded`, `consensus_floor_bypass`, `bet_retired`.
- Lines 102-117 (`§6 Drill failure-rate baseline`): **CH-16**: §11.1 NEW backup access doctrine — drills must also exercise backup-access discipline (who can read backup; backup integrity check).
- Line 122 (§7 Cycle-level diagnostics): **CH-12**: §13 time semantics — cycle-vs-wall-clock backlog detection should cite §13.4 substrate's own clock truth.
- Lines 132-138 (`§8 L0/L1 revision burst detection`): **CH-10**: §9.4 → §9.5 in DRAFT 9.
- Lines 140-148 (`§9 Federation-network observability`): **CH-22**: P15 population-level metrics are observability targets (consensus participation rate, Byzantine-witness lag, fork-resolution latency).
- Lines 151-163 (§10 Operator-side observability): **CH-13**: §14 adversarial-owner — operator-side observability is the agent's only defense against adversarial owner (since the agent doesn't get raw anchor-surface access).
- Lines 165-176 (§11 Owner-side observability — anchor surface): **CH-10**: enumerate §9.2.x / §9.3.x sub-mechanisms specifically; currently flat list.
- Lines 186-200 (§13 Falsifiability summary): **CH-11**: corrections cascade from §3.
- Line 203 (§14 Open): needs new open questions on telos-alignment as outcome signal (does substrate self-report align with agent-reported utility?), composite weighting transition (variance → correlation), bet-retirement triggers (3-strikes-2-year window).

---

## L2_TRAJECTORY.md

### Cascade impact: MEDIUM

- Line 5 (omitted long line): scope notes L0 §5.3 + L1_TRAJECTORY. **CH-21**: trajectory is the input for P14 telos-alignment computation (per L0 P14.a — "L1_TROPISM specifies telos-alignment computation; likely trajectory-cluster coherence per L1_TRAJECTORY + agent-feedback-trajectory"). Needs explicit telos-cross-cut.
- Line 9 (`§1. The negative commitment (L0 §5.3)`): correct.
- Line 25 (`Trajectory is a function of (DAG, cluster_C) jointly. The DAG is substrate state (I4); cluster_C is a substrate-resident object with its own identity`): **CH-23**: I4 reframed "Compression-Aware in DRAFT 9" — trajectory queries over compressed DAG segments operate on digests + canonical-bytes-hashes, not raw_material. cluster_C MUST handle compressed-region semantics.
- Line 41 (`Drift detection (per L2_OBSERVABILITY §3): trajectory showing wandering or inconsistency contributes to the Living Bets bet_weakening_quorum trigger`): **CH-11**: trigger semantics recalibrated per L0 §7.4.
- Line 110 (`Substrate-internal: immune system observes trajectory drift (echo-chamber detection; long-horizon convergence patterns); aggregates into observatory signal #3 (read-pattern diversity per L0 §7)`): correct; signal #3 unchanged.
- Line 113 (`Cross-cut to L2_OBSERVABILITY §10`): correct pointer (Operator-side observability is §10).
- Line 121 (`federation event content is canonical-bytes serialized (per L1_GOVERNANCE §5.3)`): **CH-10**: also references L0 §9.3.1 canonical-bytes sub-mechanism.
- Line 138 (Open: `Federation trajectory inheritance — likely NO; preserves P1.c carrier-asymmetry`): correct (P15 doesn't change this — P15 is about population-level claims, not identity transfer).

---

## L3_OUTLINE.md

### Cascade impact: MEDIUM

- Line 41 (`The 7 L1 mechanism docs each become one substrate code module ... One additional support module for shared cryptographic + canonical-bytes infrastructure. One module for the anchor-surface client`): **CH-22 / P15**: needs new module sketch for **`kernel/consensus`** (Byzantine consensus protocol; activated when ≥3 peers + population-level claim). Or formal acknowledgment that P15 is L2_FEDERATION-only and L3-deferred to first ≥3-peer instantiation.
- Lines 43-54 (§2.1 Substrate-side modules): **CH-17 / CH-18 / CH-19 / CH-20 / CH-21**: each new principle needs L3 module assignment:
  - P10 / I9 compression → `kernel/schema` (existing module gets new sub-feature) OR new `kernel/compression`
  - P11 / I10 cost observation → cross-cuts `kernel/continuity` (cost per cycle) + `kernel/skin` (network cost at egress) + `kernel/schema` (storage cost at DAG insert)
  - P12 / I11 salience → `kernel/tropism` (existing)
  - P13 embodiment → `kernel/skin` (existing — state_dir + process boundary detection)
  - P14 / I12 telos → `kernel/tropism` + `kernel/trajectory` (trajectory-cluster-coherence input + telos-objective config)
  - P15 → new module OR L2_FEDERATION-only deferred
- Line 83 (`If a cyclic dependency surfaces during L4 implementation, the L3 module boundary needs revision (CI-level revision per L0 §10.2 — L3 is L0-governed)`): correct.
- Line 117 (P1.a self-hosting recommendation): correct.
- Line 128 (§5.2 Anchor-client language considerations — `per L0 §9.3`): **CH-10**: §9.3.3 anchor-client provenance independence is currently 0% per L0 §9.2 status table. L3 must elevate provenance-independent distribution to a non-deferrable module boundary.
- Line 221 (Open: owner anchor-surface mechanism choice): correct; but **CH-13**: §14.2 adversarial-owner bounded-defenses set restricts the choice space.

---

## L3_PACKAGE_MAP.md

### Cascade impact: MEDIUM

- Lines 21-22 (Module table — `anchor_client (L0 §9 + multiple L1)` + `operator_bindings/<host>`): **CH-10**: anchor_client now needs §9.1-§9.6 sub-mechanism implementation. The L3 status table from L0 §9.2 shows §9.2.3 (owner-out-of-band key) and §9.3.3 (provenance independence) are at 0% — anchor_client module must own these.
- Lines 34-37 (§2.1 Responsibilities — `kernel/shared`): **CH-17**: canonical-bytes serializer spec carries compression-rule serialization too (P10.c witness emission needs canonical-bytes for compression events).
- Lines 60-69 (§3 `kernel/skin`): **CH-20 / P13**: needs explicit state_dir-content-watcher sub-module + process-fd-set-watcher + network-binding-watcher per L0 P13.d. Currently zero P13 implementation outlined.
- Lines 89-103 (§4 `kernel/schema`): **CH-17 / CH-25**: needs new sub-module for compression-event emission + compression-invariant set verification.
- Lines 115-129 (§5 `kernel/governance`): **CH-14 / CH-15**: needs new sub-modules for §15 owner-succession FSM + §16 generation-counter management + §16 rate-limit enforcement.
- Lines 145-163 (§6 `kernel/continuity`): **CH-12 / §13**: time-source authority hierarchy is `kernel/continuity` responsibility (cycle clock vs anchor-trusted timestamp).
- Lines 171-189 (§7 `kernel/tropism`): **CH-18 / CH-19 / CH-21**: needs new salience-emergence sub-module + telos-alignment-computer sub-module + cost-observation hook for embedding-service queries.
- Line 246-256 (§10 anchor_client responsibilities + L0 §9 cross-ref): **CH-10**: must enumerate §9.2.1-§9.2.7 + §9.3.1-§9.3.6 with implementation status.
- Line 253-254 (`Trusted wall-clock timestamps + Owner liveness heartbeat`): **CH-12 / CH-14**: §13 time semantics + §15 owner mortality — these features are now L0-doctrine-backed, not just L1-mechanism.

---

## Summary statistics

| Metric | Count |
|---|---|
| Total files audited | 17 |
| Files needing update | 17 (every L1/L2/L3 doc cascades from DRAFT 9) |
| **HIGH-impact updates** | **11**: L1_OUTLINE, L1_SKIN, L1_CONTINUITY, L1_GOVERNANCE, L1_SCHEMA, L1_TROPISM, L1_HARD_RULES, L2_TRUST_MODEL, L2_LIFECYCLE, L2_FEDERATION, L2_OBSERVABILITY |
| **MEDIUM-impact updates** | **5**: L1_TRAJECTORY, L2_EVOLUTION, L2_TRAJECTORY, L3_OUTLINE, L3_PACKAGE_MAP |
| **LOW-impact updates** | **1**: L2_OUTLINE (status pointer refresh only) |
| Sections flagged for update | **~140** (counted as discrete line-anchored items above; ~8.2 per doc avg) |
| New L1_HARD_RULES C-rows needed | **13** (C21-C33) |
| New L1_HARD_RULES F-rows needed | **6** (F18-F23) |
| New immune-grade sporocarps needed | **9** (compression_invariant_corruption, compression_unattested, salience_collapse, telos_drift, P13_embodiment_breach, budget_exhausted, generation_depth_exceeded, consensus_floor_bypass, bet_retired) |
| Estimated cascade work milestone | **M26-cascade**: ~17 file-edits + 1 L1_HARD_RULES major expansion = **~30-40 atomic file-changes** |

---

## Critical mismatches requiring text fixes (direct contradictions vs DRAFT 9)

| File:line | Current text | DRAFT 9 truth |
|---|---|---|
| L1_OUTLINE.md:18 | "eight invariants and nine principles" | twelve invariants and fifteen principles |
| L1_OUTLINE.md:27 | "operationalizing the 8 invariants" | operationalizing the 12 invariants |
| L1_HARD_RULES.md:6 | "P (P1-P9) AND one I (I1-I8)" | P (P1-P15) AND one I (I1-I12) |
| L2_TRUST_MODEL.md:120 | "7 signals (6 base + 1 composite)" | 10 signals (6 base + 3 cost + 1 composite); composite is #10 |
| L2_OBSERVABILITY.md:19 | "6 base + 1 composite + 1 birth-period derivative" | 6 base + 3 cost + 1 composite (DRAFT 9 §7.3); birth-period derivative is layered orthogonally |
| L2_OBSERVABILITY.md §3 trigger | "signal #6 stays < 1" (correct) but window unit ambiguous | window is wall-clock 90 days per L0 §7.4 + §13 |
| L2_LIFECYCLE.md:78 | "Signal #7 (composite health)" | composite is signal #10 in DRAFT 9; #7 is now compute-cost-per-cycle |
| L2_EVOLUTION.md:49 / L2_OBSERVABILITY.md:132+ | "L0 §9.4 burst-detection" | DRAFT 9 §9.4 is "Canonical-bytes doctrine"; burst-detection moved into §9.5 + §10 burst-rate |

---

## Recommended cascade work ordering

1. **First** — fix the 8 direct contradictions above (atomic edits; ~1 hour total). Highest-confidence, lowest-effort. Closes the "L1/L2 doc factually contradicts L0" failure mode.
2. **L1_HARD_RULES expansion** — add C21-C33 + F18-F23 + 9 new immune-grade sporocarps. This is the IMMUNE-CATALOG truth-table; everything downstream cites this. ~3-4 hours.
3. **L1_OUTLINE coverage matrix** — add rows for P10-P15 + I9-I12 + §13-§16. Once this is updated, every downstream L1 doc has an authoritative ownership pointer. ~1 hour.
4. **L1_GOVERNANCE** — codify §15 owner mortality, §16 generation limits, §14 adversarial-owner classifier rows. THE highest L1-internal cascade load. ~4-6 hours.
5. **L1_SCHEMA + L1_TROPISM + L1_SKIN + L1_CONTINUITY** — add compression discipline (P10/I9), cost signals (P11/I10), salience + telos detectors (P12/P14, I11/I12), embodiment-breach detector (P13). ~3-4 hours each; can parallelize.
6. **L2_TRUST_MODEL** — add §14 adversarial-owner subsection + §15 succession subsection + §9.x sub-mechanism citations + signal-count fix. ~3-4 hours.
7. **L2_LIFECYCLE** — owner-succession alignment with §15; generation-limit alignment with §16; bet-retirement state alignment with §7.5. ~3-4 hours.
8. **L2_OBSERVABILITY** — full Living Bets rewrite to 10 signals; new immune-grade sporocarps; falsifiability-trigger correction. ~3-4 hours.
9. **L2_FEDERATION** — P15 consensus floor; entire §6 rewrite. ~4-6 hours (largest single L2 cascade).
10. **L2_EVOLUTION + L2_TRAJECTORY + L2_OUTLINE** — alignment for compression-rule evolution + telos cross-cut + 9.x sub-mechanism citations + scope refresh. ~1-2 hours each.
11. **L3_PACKAGE_MAP + L3_OUTLINE** — module assignments for P10-P15 / I9-I12; new sub-modules for compression / cost / salience / telos / embodiment-breach detectors; optional `kernel/consensus` decision. ~2-3 hours.

**Total estimated cascade work**: **~40-55 hours of focused editing across 17 files** with 9 new sporocarps + 13 new C-rows + 6 new F-rows + 4 new L0 section bindings. Realistic milestone block: **M26-cascade (~30-40 atomic commits)**.

**Sequencing rationale**: contradictions first (cheap, high-credibility wins) → L1_HARD_RULES (the canonical surface; everything cites it) → L1_OUTLINE (the L1 ownership table) → L1 mechanism docs (concrete enforcement) → L2 cross-cut docs (high-altitude views of mechanism) → L3 module map (code organization implications). Pre-cascade test: every doc-pair (Lx ↔ Ly) cross-reference must resolve; post-cascade test: every L0 P/I/§ reference in L1/L2/L3 must point to extant DRAFT 9 line.

---

## Findings not in any individual doc (cross-cutting)

- **No L1/L2/L3 doc currently mentions P15 or Byzantine consensus**. Federation doctrine assumes pairwise-attested trust everywhere. This is the single largest doctrinal gap to close. L2_FEDERATION is the primary owner but L1_GOVERNANCE §5 and L1_HARD_RULES need C-rows too.
- **No L1/L2/L3 doc currently mentions compression or P10/I9**. The DRAFT 8 doctrine actively forbade pruning (L1_SCHEMA §2.5 DAG-pruning prohibition; L1_HARD_RULES F9 no lossy compression). DRAFT 9 inverts this carefully (compression invariant set is preserved; everything else compressible under CI). Major doctrinal shift; requires cross-doc alignment.
- **No L1/L2/L3 doc currently mentions adversarial owner**. L2_TRUST_MODEL §6 lists trust limits (P1.a self-hosting; substrate cannot enforce against host; substrate cannot enforce against operator runtime) but assumes owner is trusted. DRAFT 9 §14 explicitly addresses this; L2_TRUST_MODEL needs §6.4 / §6.5.
- **No L1/L2/L3 doc currently mentions §13 time semantics as L0 doctrine**. L1_GOVERNANCE §2.2 dual-clock + L1_CONTINUITY §1.2 wall-clock vs cycle-clock are implemented empirically; DRAFT 9 codifies the doctrine. Cite chain needs to be tightened.
- **No L1/L2/L3 doc currently mentions §15 / §16 explicitly as L0 sections** (succession + generation limits exist as L1 mechanisms; DRAFT 9 elevates to L0 doctrine, demanding L1 docs cite the L0 doctrine instead of owning the doctrine themselves).
- **Anchor surface §9.2.x / §9.3.x decomposition is universally missing** — all 17 docs cite "§9" or "§9.3" or "§9.4" as monolith; DRAFT 9 has 13 sub-mechanisms with explicit implementation-status tracking. Every anchor-surface citation in every doc needs to map to one of §9.2.1 through §9.3.6.

**End of cascade list.**

---

## §18. Post-owner-gate-decision addendum (2026-05-17 conversation)

After cascade list was written, owner G-9.b decision (Phase γ §17 gate) retracted P12/P13/P15 from L0 to L1/L2. This creates additional cascade work BEYOND the items above:

### P12 Differential Response → L1_TROPISM (cascade addition)
L1_TROPISM (currently doesn't have salience section) MUST add:
- New §X "Salience / Attention" specifying salience-emergence mechanism (P12.a)
- New §X+1 "Anti-uniformity guarantee" with birth-period exemption (P12.b)
- `salience_collapse` immune signal type + detector
- Bootstrap initialization (uniform until N=100 samples; then EWMA-correlation)

### P13 Embodiment → folded into P9 + I8 (cascade reconciliation)
L1_SKIN MUST extend I8 enforcement to:
- Spatial-locus checks: state_dir contents allowlist, process FD set, network bindings allowlist
- New `P9_spatial_locus_breach` immune signal (originally `P13_embodiment_breach` in DRAFT 9 v1)

### P15 Population-Level Consensus → L2_FEDERATION (cascade addition)
L2_FEDERATION MUST add:
- New section "Population-level consensus floor" specifying ≥3 peer threshold (per G-9.b/G-7.c)
- Byzantine-fault-tolerant consensus protocol choice (Tendermint-style PBFT recommended)
- Pairwise-trust below consensus floor (DRAFT 8 inheritance)

### §14 Adversarial Owner → L2_TRUST_MODEL (cascade addition)
L2_TRUST_MODEL MUST add:
- Threat scenario table (owner key compromise / coerced / impersonated / deceased / anchor-client tampered)
- Duress_attestation mechanism specification
- Owner_signature_velocity observability metric
- N-of-m multisig recommendation

### §15 Owner Mortality → L1_GOVERNANCE §3.2 (cascade addition)
L1_GOVERNANCE §3.2 (currently deferred per DRAFT 8) MUST be specified now:
- Successor_chain registry format
- Heartbeat staleness trigger semantics
- Legacy/orphaned sub-state FSM
- Terminal-state per owner G-8 (L1 owner decision: bet-retirement / self-euthanasia / indefinite-orphan)

### §16 Generation Limits → L1_GOVERNANCE (cascade addition)
L1_GOVERNANCE MUST add:
- reproduction_lineage_depth bounds (seed 10)
- reproduction_rate limit (seed 1 sprout per 24h)
- Per-substrate lifetime quota (seed 100)
- Override mechanism via anchor-attested CI mutation

### Cultivation vocabulary (G-11.a) → universal cascade
Every L1/L2/L3 doc that references "owner-substrate relationship" or "owner role" should mention Cultivation / Cultivator / Cultivar in glossary entries. Existing "owner" usage remains valid (matches §9 anchor surface vocabulary); new doc additions should prefer Cultivation terminology.

**Estimated additional cascade work**: ~10 additional commits (~10-15 hours) on top of the original cascade estimate (30-40 commits, 40-55 hours).

**Total M26-cascade work after G-9.b retraction**: ~40-50 commits, ~50-70 hours.

**End of post-owner-gate-decision addendum.**
