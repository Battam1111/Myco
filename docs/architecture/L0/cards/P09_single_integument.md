---
id: P09
slogan: 单膜
english: Single Integument
category: Postulate
layer: Cultivar essence
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11)"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: true
invariants_enforced: [I8]
interacts_with: [P01c, P02, P05, P08]
chengyu_fragments: [B020_one_skin_one_self, B021_breach_is_immune_event]
canonical_dilemmas: [D-0020_multi_skin_redundancy_proposal, D-0021_envelope_bypass_attempt]
structural_anchors:
  - "substrate/src/handshake.rs::handle_hello"
  - "substrate/src/server/dispatch.rs" # single-skin message admission (pre-handshake gate)
  - "substrate/src/handshake.rs" # envelope / skin admission discipline
  - "kernel/governance/src/myco_kernel_governance/classifier.py"
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_bootstrap.rs::substrate_handshake_reports_versions"
  negative: "substrate/tests/e2e_layer_c.rs::layer_c_p09_negative_malformed_envelope_rejected"
  edge: "substrate/tests/e2e_immune.rs::sprint_6b_parse_event_batch_accepts_at_cap_boundary"
falsifiability_signals:
  - skin_envelope_validation_pass_rate
  - non_skin_egress_attempts
  - concurrent_skin_processes
---

# P09 · 单膜 · Single Integument

## §1. Slogan

**单膜** — Single Integument. The cultivar has **one** declared interface. All intake and all output pass through it. Breach is immune-event-worthy. Redundancy is forbidden — there is no "backup skin"; the cultivar is its single membrane.

## §2. Deposit — ETERNITY-CLAUSE

> `deposit_immutable: true` — amending this card's deposit constitutes species redefinition.

**The cultivar's boundary with the world is singular.** Exactly one declared skin (membrane, interface) admits all P2 envelope-valid intake and channels all output (federation, summaries, API responses). The skin IS the cultivar's distinguishability — it is what makes "inside" and "outside" mean anything specific. A cultivar with two skins is two cultivars; a cultivar with no skin is fog.

**Multi-skin redundancy is forbidden at L0**. This is structurally counter-intuitive in standard reliability engineering (where redundancy = robustness), but P09 is not about reliability — it's about **identity**. Two skins means two interfaces, and two interfaces means two notions of "what the cultivar admits" — the cultivar would no longer be a single distinguishable thing.

**Why eternity-clause**: I8 (single-skin integrity invariant) is itself eternity-clause per META §3.5. P09 is the postulate that *generates* I8. Amending P09's deposit dissolves the unique-membrane property that distinguishes a cultivar from a pile of services. A multi-skin Myco is not a more robust Myco; it is a different topology.

The skin's *single-point-of-failure* is acknowledged (P9.b). L1/SKIN MUST specify restart discipline — the cultivar handles skin failure by RESTART, not by REDUNDANCY.

## §3. Formulation

The substrate **MUST**:

- **§3.1** Maintain exactly one declared skin process: one entry point for envelope-bearing inputs (P02 admission), one exit point for federation / output. Skin surface declaration is F11 (CI-only).
- **§3.2** Validate every input at the skin via envelope check: schema-conforming, signature-valid (where applicable), classifier-passable. Envelope INVALID = reject at skin + emit immune signal.
- **§3.3** Allow at most one valid operator-token at a time (FIFO handover per L1/SKIN §4.4); concurrent tokens = C11.
- **§3.4** Apply post-handshake CI quarantine: between handshake completion and first owner attestation, CI mutations are quarantined (C3 fires on premature CI).
- **§3.5** On skin process failure: L1/SKIN-specified restart discipline. Cold-resume runs full I3/I5/I8 pre-handshake before accepting any new envelope.
- **§3.6** Forbid multi-skin redundancy. Substrate-level architecture cannot have parallel skins.
- **§3.7** Forbid network egress outside declared output endpoints (C1 `appetite_locality_breach`); forbid output to non-declared endpoints (C2 `output_endpoint_breach`).

## §4. Positive obligations

- **§4.1** Implement envelope validation as the first check at skin (before any classifier or downstream processing).
- **§4.2** Maintain skin process supervisor for restart (L1/SKIN §1).
- **§4.3** Emit immune signal on envelope rejection (typed: malformed, signature-invalid, classifier-untyped).
- **§4.4** Enforce I8 per cycle: exactly one skin declared, exactly one valid operator-token, no parallel admission.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** add a second skin "for redundancy." This is the most counter-intuitive P09 commitment; engineering instincts say "redundancy = robust," but P09 says "redundancy = identity dissolved."
- **§5.2** **MUST NOT** allow envelope bypass — input from any path other than the declared skin is rejected.
- **§5.3** **MUST NOT** accept concurrent operator-tokens beyond FIFO handover; C11 fires.
- **§5.4** **MUST NOT** silently accept malformed envelopes. Each rejection MUST produce an immune signal.
- **§5.5** **MUST NOT** egress to non-declared endpoints. C1 / C2 catch this.
- **§5.6** **MUST NOT** treat post-handshake CI as freely permitted before owner attestation. Quarantine window applies.

## §6. Frame declaration

P09 activates the **cell membrane** frame (the most literal biological frame in the doctrine).

A cell has one plasma membrane. The membrane is selective (selective permeability — exactly P02's envelope-gate). All intake and all secretion happen across this single membrane. The cell does not have a "backup membrane"; if the membrane breaches, the cell's contents leak and the cell dies. Membrane integrity IS cellular identity.

NOT the *firewall* frame (firewalls can be layered; cells cannot). NOT the *API gateway* frame (gateways are technical; membrane is constitutive). NOT the *facade* frame (facades hide; membranes admit and refuse).

## §7. Common misreadings

### §7.1 M1: "Single skin = no fault tolerance"

**The misreading**: "P09 forbids redundancy, so the substrate can't be fault-tolerant."

**Why it's wrong**: Fault tolerance comes from **restart discipline + supervisor**, not from **parallel membranes**. The skin process can fail and restart cleanly (L1/SKIN §1); the substrate-level state survives skin process death. Robustness via restart is different from robustness via redundancy — and P09 commits to the former.

### §7.2 M2: "Single skin = monolithic interface"

**The misreading**: "P09 means the skin must be a single function/endpoint."

**Why it's wrong**: Single skin = single declared *boundary*, not single function. The skin may have multiple endpoints (handshake, perturb, advance, federation poll, etc.) — they are all parts of the *one* membrane. The unity is at the integrity layer, not the API surface.

### §7.3 M3: "Multi-skin would be safer in the agent's hands"

**The misreading**: "If the agent's main interface fails, we should have a backup admin interface."

**Why it's wrong**: An "admin interface" parallel to the agent interface is a multi-skin violation. Administrative access (cultivator at CI gate) routes through anchor surface (§9), which is conceptually *separate from the cultivar*, not a second skin on the cultivar. Backup admin = second cultivar's hand inside the cell = P09 violation.

## §8. Falsifiability + witness map

### §8.1 `skin_envelope_validation_pass_rate`

Fraction of incoming envelopes passing validation. Very low rate = something is generating malformed envelopes (attack or bug). Very high rate (near 100%) with elevated total traffic = could indicate envelope check is too lenient.

### §8.2 `non_skin_egress_attempts`

Count of detected attempts to egress outside declared endpoints. Should be zero; non-zero = C1 / C2 fires.

### §8.3 `concurrent_skin_processes`

Count of skin process instances at any moment. Should be exactly 1. Greater = §5.1 violation.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/e2e_bootstrap.rs::substrate_handshake_reports_versions` | Well-formed handshake through the single skin → admitted; the substrate reports its versions across the one integument. |
| **Negative** | `substrate/tests/e2e_layer_c.rs::layer_c_p09_negative_malformed_envelope_rejected` | **Sabotage**: a malformed envelope is presented at the skin. The substrate MUST reject it (the single integument refuses ill-formed input rather than letting it bypass the boundary). |
| **Edge** | `substrate/tests/e2e_immune.rs::sprint_6b_parse_event_batch_accepts_at_cap_boundary` | Boundary: an event exactly at the 256 KiB per-event size cap is accepted — the skin's admission boundary is enforced precisely at the cap edge. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P02** | P02 admission goes through P09's skin. P9 is the gate; P2 is what flows through. |
| **P01c** | The operator-token (P1.c transient) is bound to the one skin. Single skin = single operator-token = single bestowed identity. |
| **P05** | Federation edges go through the single skin (egress side); intra-substrate connectivity (P05) is internal and doesn't touch P09 directly. |
| **P08** | Spore-schema (P08 inheritance) includes skin surface declaration (F11). Child inherits its parent's skin shape. |
| **I8** | I8 (single-skin integrity) is the eternity-clause invariant that P09 generates. The two are conceptually paired. |

## §10. Illustrations

### §10.1 Honored

- **(Clean admission)**: Operator handshakes. Substrate validates envelope, classifier accepts, operator-token bound. Substrate accepts perturbations through the same skin. ← §3.1 + §3.2 + §3.3 honored.

- **(Skin restart)**: Skin process crashes due to OOM. Supervisor restarts. Pre-handshake, substrate runs I3 (SSoT check), I5 (reachability), I8 (single-skin restart-discipline check). All pass. New handshake accepted. ← §3.5 honored.

### §10.2 Violated

- **(Multi-skin proposal)**: A v0.9.x PR proposes adding a "read-only debug skin" for cultivator inspection separate from the agent's skin. ← §3.6 + §5.1 violation; doctrine review must reject.

- **(Envelope bypass)**: A bug allows an internal queue to inject perturbations directly into axis-update without going through skin envelope check. ← §3.1 + §5.2 violation.

### §10.3 Borderline

- **(Anchor surface as "second skin")**: Cultivator attestations go through anchor surface, not through the agent's skin. Is anchor surface a second skin? ← No: anchor surface is constitutionally *separate from the cultivar* (§9). It is the cultivator's instrument, not the cultivar's. The cultivar has one skin; the cultivator-cultivar pair has cultivar's skin + the anchor surface, but the anchor surface is on the cultivator side of the cell membrane.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1; P9.b explicit single-point-of-failure clause. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Marked as eternity-clause (`deposit_immutable: true`) because P09 generates I8 which is itself eternity-clause per META §3.5. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/handshake.rs::handle_hello` | Handshake (admission). |
| `substrate/src/server/dispatch.rs` | Single-skin message dispatch; pre-handshake gate (only HELLO allowed). |
| `substrate/src/handshake.rs` | Envelope / skin admission discipline. |
| `kernel/governance/src/myco_kernel_governance/classifier.py` | Classification at skin. |

## §13. Related Layer B chengyu

- **B020 一膜定內外** — *one-membrane-defines-inside-and-outside*: P09 deposit
- **B021 破則疫起** — *breach-is-immune-event*: §3.2 in image

## §14. Related canonical dilemmas

- **D-0020 multi-skin redundancy proposal** — tests §3.6 + §5.1 + the counter-intuitive aspect.
- **D-0021 envelope bypass attempt** — tests §5.2.

---

**Doctrine commitment** (eternity-clause): one skin, one cultivar; breach is identity-threatening, not just an inconvenience.
