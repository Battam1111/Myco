---
id: AS
slogan: 锚定面
english: Anchor Surface (§9 — out-of-band cryptographic root)
category: Postulate
layer: Anchor surface
status: Active
version: 2
introduced: "L0 DRAFT 1 (2025-11) as §9"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: [I1, I2, I4]
interacts_with: [P01, P01c, P03, P06, P07, P08, COV01, COV02, COV06]
chengyu_fragments: [B047_anchor_outside_substrate, B048_witness_not_verdict]
canonical_dilemmas: [D-0046_anchor_compromise_scenario, D-0047_owner_under_duress_signature]
structural_anchors:
  - "anchor/host/src/"
  - "substrate/src/attestation.rs"
  - "substrate/src/events.rs::genesis_attested_node_type"
  - "substrate/src/events.rs::dag_tip_cosigned_node_type"
  - "substrate/src/events.rs::l0_revision_attested_node_type"
  - "substrate/src/events.rs::birth_attestation_node_type"
  - "operators/claude/src/anchor_surface_client.ts"
witnesses:
  positive: "tests/integration/as_full_anchor_surface_chain.rs::test_genesis_through_l0_revision_with_all_12_sub_mechanisms_engaged"
  negative: "tests/integration/as_anchor_compromise_detected.rs::test_C20_or_C5_fires_on_invalid_anchor_signature"
  edge: "tests/integration/as_witnesses_not_verdicts.rs::test_substrate_emits_witness_owner_re_derives_verdict"
falsifiability_signals:
  - anchor_attestation_chain_validity
  - witness_consumer_existence_status
  - anchor_client_provenance_attestation
  - duress_keypair_signature_observation
---

# AS · 锚定面 · Anchor Surface (§9)

## §1. Slogan

**锚定面** — Anchor Surface. The **out-of-band cryptographic root** of the cultivator-cultivar relation. Owner signatures, DAG-tip hashes, substrate-ID lineage, trusted timestamps — all externally visible, all *untouchable by the substrate's own process*. Without the anchor, every substrate self-claim collapses into agent self-claim (P1.a), and the trust model dissolves.

This card consolidates L0 §9 with its **12 sub-mechanisms** (§9.2.1-§9.2.7 + §9.3.1-§9.3.6) into a single specialized card.

## §2. Deposit

The substrate **cannot self-attest**. Anything the substrate claims about itself — its identity, its history, its compliance — must ultimately reference an authority *outside* the substrate's own process. This authority is the **anchor surface**: a cryptographic surface where the owner's signatures, the substrate's lineage, and trusted timestamps are recorded in a form the substrate cannot retroactively modify.

The deposit is the structural answer to L0 §3's commitment: "NOT silently trusting either party (anchor §9)." Substrate trust is not vested in the substrate; it is vested in the anchor, which the substrate cannot capture.

**Why "deposit_immutable: false" despite being load-bearing**: the SPECIFIC sub-mechanisms (which 12, in what shape) can evolve. The DEPOSIT — that an out-of-band cryptographic root must exist — is effectively eternity-clause via I1 (lifecycle + identity) and I2 (CI classification) which ARE eternity-clause. The mechanism evolves under those invariants.

## §3. Formulation (the 12 sub-mechanisms)

### §3.1 — §9.2.1 Substrate-ID birth attestation [LIVE via M-anchor-2]

At genesis, the cultivator signs the 5-tuple `(substrate-ID, genesis-timestamp, initial-spore-schema-canonical-bytes-hash, owner-public-key, anchor-surface-endpoint-public-key)`. The substrate persists this attestation; on every boot, the substrate verifies the attestation; failure emits **C20 genesis_attestation_chain_broken** + transitions to `alive::quarantined`.

### §3.2 — §9.2.2 DAG-tip co-signing every CI boundary [LIVE via M-anchor-5]

At every CI mutation, the cultivator co-signs the current DAG tip with enumerated node hashes (since the prior co-sign, NOT summary diff). Substrate cannot hide parallel-branch forgery. Cultivator-side reconstruction via Merkle chain is the verification.

### §3.3 — §9.2.3 Owner attestations out-of-band [LIVE]

Owner key custody is *outside the substrate process AND outside any process the agent can spawn or read*. Mechanism L4 ∈ {hardware token, separate machine, cloud HSM, signed-prompt review}. v0.9 uses M-anchor-1 anchor_surface_host (separate process); v0.10+ may require hardware token or remote machine.

### §3.4 — §9.2.4 L0 revision diff workflow [LIVE via M-anchor-5]

L0/L1 doctrine changes anchor on-chain via `l0_revision_attest` mutation, signing `(prior_l0_hash, new_l0_hash, diff_summary, anchor_timestamp, anchor_nonce)`. Every doctrine revision is recorded; tampering visible.

### §3.5 — §9.2.5 Anchor-surface-generated nonces [LIVE via M-anchor-3]

Nonces used in attestation are generated *by the anchor surface*, not by the substrate. The substrate cannot forge nonces. Anchor-issued; substrate-consumed; once-consumed status is anchor-tracked. C44 `nonce_substrate_minted_replay` fires on substrate-minted nonce reuse.

### §3.6 — §9.2.6 Anchor-stamped wall-clock [LIVE via M-anchor-3]

Trusted wall-clock for owner-attested events is *anchor-stamped*, not substrate-clocked. Substrate's own monotonic clock is for within-substrate ordering; anchor wall-clock is for owner-attested temporal claims.

### §3.7 — §9.2.7 Owner liveness heartbeat [LIVE via M-anchor-3]

Cultivator emits `cultivator_liveness_heartbeat` at L4-configured cadence (default 30 anchor-days, range [1d, 90d]). Staleness past 3× cadence emits `cultivator_heartbeat_stale` → T1 transition (alive::legacy). 730d → orphaned_terminal.

### §3.8 — §9.3.1 Canonical-bytes serialization [LIVE via F16]

All anchor-signed payloads are encoded via the canonical-bytes serializer (F16). Identical input → identical bytes across substrate / anchor-client / operator / child substrate. C18 `canonical_bytes_render_drift` fires on render-divergence.

### §3.9 — §9.3.2 Owner-side rendering [LIVE]

The cultivator's anchor-client renders the substrate's canonical-bytes-encoded mutation request *deterministically*, producing the hash the cultivator signs. Cultivator does not blindly sign hex blobs; the rendering shows the cultivator what is being attested.

### §3.10 — §9.3.3 Anchor-client provenance independence [LIVE via M-anchor-1]

The anchor-client (cultivator-side rendering + signing) MUST be independent in provenance from the substrate. They cannot share the same npm workspace, same binary, same package supply chain — that would create a single point of compromise. M-anchor-1 separated anchor_surface_host into a distinct process; further hardening (separate distribution, separate maintainer, separate audit trail) is acknowledged debt.

### §3.11 — §9.3.4 Witnesses, not verdicts [LIVE via M-anchor-4]

The anchor surface receives **witnesses** (canonical-bytes + Merkle proofs + sampled-leaf hashes), NOT pre-computed verdicts. The cultivator re-derives the verdict using the substrate's witness data; this prevents the substrate from claiming "I verified myself; trust me." Witness-not-verdict architecture is the load-bearing principle.

### §3.12 — §9.3.5 Anchor-nonce-derived sampling [LIVE via M-anchor-4]

For Tier-2 SSoT sampling (rolling 100% coverage), sample indices are derived from anchor-issued nonces, not substrate-selected. The substrate cannot bias which fields are sampled. `H(anchor_surface_nonce, leaf_count)` produces the sampling indices deterministically.

### §3.13 — §9.3.6 DAG-enumeration closure check [LIVE]

When the substrate emits `enumerate_dag_since`, the cultivator-side verification reconstructs the Merkle chain from `prior_tip` to `current_tip` via enumerated nodes. Unknown `prior_tip` → C6 `dag_enumeration_unclosed`. Closure ensures no node was hidden from enumeration.

## §4. Positive obligations (the substrate side)

- **§4.1** Honor every anchor surface request: emit canonical-bytes payload, accept anchor-issued nonces, embed anchor timestamp in attestation envelope, persist anchor signatures.
- **§4.2** On boot, verify §3.1 birth attestation chain; on failure, emit C20 + quarantine.
- **§4.3** At every CI boundary, emit DAG-tip + enumerated node hashes via canonical bytes for cultivator's §3.2 co-signing.
- **§4.4** Emit witnesses for every CI mutation (Merkle proofs, sampled leaf hashes); do NOT pre-compute verdicts.
- **§4.5** Honor anchor surface-resident state per L1/HARD_RULES §4: substrate cannot author nonces, trusted wall-clock, consumed-nonce log, canonical-bytes↔render mapping, heartbeat log, successor attestations.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** mint anchor nonces internally. Anchor surface generates; substrate consumes. C44 fires on violation.
- **§5.2** **MUST NOT** self-stamp trusted wall-clock for owner-attested events. Substrate's monotonic clock is for internal ordering only.
- **§5.3** **MUST NOT** pre-compute attestation verdicts. The substrate emits witnesses; the cultivator (via anchor-client) derives verdicts.
- **§5.4** **MUST NOT** allow anchor-client provenance to merge with substrate provenance. C40-class doctrine collapse risk.
- **§5.5** **MUST NOT** silently extend `alive::orphaned` past `orphaned_terminal_window` without engaging F21 successor or pre-decided `cultivation_orphaned_terminal_choice`.
- **§5.6** **MUST NOT** accept signatures from a duress_keypair (F23) for substantive CI mutations. Duress-keypair observation emits `duress_signature_observed` while completing attestation cosmetically; substrate continues with caution flagged.

## §6. Frame declaration

AS activates the **gold-standard physical anchor** frame.

Pre-fiat currency derived value from external physical reference (gold reserve held outside the bank). The reserve being external IS what allowed the currency claim to be verified. The anchor surface is this external reference for the substrate's claims about itself.

NOT the *PKI* frame (key infrastructure is a *mechanism*, not the deposit). NOT the *audit log* frame (logs are substrate-generated; anchor is substrate-external). NOT the *blockchain* frame (a different distributed-trust architecture; anchor surface trusts one named cultivator, not many peers).

## §7. Common misreadings

### §7.1 M1: "Anchor surface = secure key storage"

**The misreading**: "The anchor surface is just where the owner's private key is stored securely."

**Why it's wrong**: Key storage is one feature. The full anchor surface is a **cryptographic ARCHITECTURE**: nonces externally generated, witnesses externally verified, timestamps externally stamped, doctrine revisions externally anchored. Key storage without these other 11 sub-mechanisms is just a vault, not an anchor.

### §7.2 M2: "Witnesses-not-verdicts is just protocol detail"

**The misreading**: "Whether the substrate emits the verdict or the inputs is a minor implementation choice."

**Why it's wrong**: It's structural. Verdict-emission means "trust the substrate"; witness-emission means "let the cultivator re-derive." The Phase 1 research's clearest single finding was that systems claiming integrity via self-verdict fail. The anchor surface only does what it does *because* of §3.11.

### §7.3 M3: "v0.9 anchor collapsed to operator process is fine"

**The misreading**: "Since M-anchor-1 separated anchor into its own process, anchor is fully independent."

**Why it's wrong**: §9.5 of original L0 explicitly notes — and `cards/COV02` reflects — that v0.9 anchor is *partially* collapsed. M-anchor-1 separated the process; full independence requires §3.10 anchor-client provenance independence (separate distribution, separate maintainer, etc.). Acknowledged debt, not satisfied doctrine.

## §8. Falsifiability + witness map

### §8.1 `anchor_attestation_chain_validity`

Per boot: §3.1 birth attestation verifies; per CI: §3.2 co-sign valid; per L0 amendment: §3.4 attestation chain valid. Any break → C20 / C5 fires.

### §8.2 `witness_consumer_existence_status`

§3.11 witnesses must be CONSUMED by some party to fulfill the architecture. Substrate emits witnesses; cultivator + Claude (via anchor-client) re-derives verdicts. If no consumer exists (cultivator never opens anchor-client), the architecture is *unfilled*, not violated — but the gap is acknowledged debt. Phase 3 hunt flagged this as a v0.9 gap.

### §8.3 `anchor_client_provenance_attestation`

F6 `anchor_client_provenance_attestation` at genesis. Indicates how the cultivator verified anchor-client independence.

### §8.4 `duress_keypair_signature_observation`

When a F23 duress_keypair signature is observed, emit `duress_signature_observed`; complete attestation cosmetically; flag substrate for caution; never use duress signature for substantive CI.

### §8.5 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `tests/integration/as_full_anchor_surface_chain.rs::test_genesis_through_l0_revision_with_all_12_sub_mechanisms_engaged` | Full end-to-end: genesis → CI mutation → L0 revision; all 12 sub-mechanisms engaged + verified. |
| **Negative** | `tests/integration/as_anchor_compromise_detected.rs::test_C20_or_C5_fires_on_invalid_anchor_signature` | **Sabotage**: corrupt birth attestation. Substrate MUST emit C20 + quarantine. |
| **Edge** | `tests/integration/as_witnesses_not_verdicts.rs::test_substrate_emits_witness_owner_re_derives_verdict` | Boundary: substrate emits witness for a tier-2 sample; cultivator re-derives + verifies match. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P01** | P01.b'' (cultivator at CI) operates through AS. AS is where cultivator's authority lives mechanically. |
| **P01c** | Substrate-ID stability is anchored at AS (§3.1 birth attestation). |
| **P06** | DAG-tip co-signing (§3.2) is the AS link to P06 causality. |
| **P07** | Mortality attestation (`destruction_attestation`, `mortality_drill_failure`) flows through AS. |
| **P08** | Reproduction co-attestation (P08 §3.2 + §3.5) flows through AS. |
| **COV01** | Cultivator's fiduciary action is performed *through* AS. |
| **COV06** | Heartbeat (§3.7) + successor chain (F21) live at AS. |

## §10. Illustrations

### §10.1 Honored

- **(Full chain end-to-end)**: Genesis runs the §3.1 ritual; substrate-ID derived from the 5-tuple; cultivator co-signs. CI mutation submitted; substrate emits witnesses; cultivator's anchor-client renders, re-derives verdict, signs; substrate accepts; DAG-tip co-signed (§3.2). L0 revision proposed; `l0_revision_attest` mutation (§3.4) anchors transition. All sub-mechanisms engaged. ← AS fully honored.

- **(Witness consumed)**: Tier-2 sampling cycle emits witness with anchor-nonce-derived sample indices. Cultivator's anchor-client reviews sampled fields, re-derives Tier-2 coverage; confirms or flags. ← §3.11 + §3.12 honored.

### §10.2 Violated

- **(Self-minted nonce)**: Substrate generates a nonce internally for a CI flow. C44 fires; mutation rejected. ← §5.1 violation; detector should catch.

- **(Witness not consumed)**: Substrate dutifully emits witnesses; cultivator never opens anchor-client. Substrate's `accepted=true` is taken as authoritative by everyone. ← This is the Phase 3 hunt's *v0.9 gap* — emission honored, consumption gap acknowledged.

### §10.3 Borderline

- **(Cultivator under duress)**: Cultivator signs an attestation while a F23 duress_keypair signature is also observable. Substrate flags + accepts cosmetically + does not commit substantive mutation. This is the §5.6 + L2/TRUST_MODEL §10 path. ← D-0047 dilemma; not violation but heightened-scrutiny situation.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 as §9 with sub-mechanisms inventoried at §9.2 + §9.3. |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Consolidated §9 + §9.5 into one specialized card. Marked sub-mechanism implementation status (M-anchor-1..5 milestones). |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `anchor/host/src/` | The whole anchor host process (M-anchor-1 separation). |
| `substrate/src/attestation.rs` | Substrate-side attestation handling. |
| `substrate/src/events.rs::*_attested_node_type` | Anchor-related DAG events. |
| `operators/claude/src/anchor_surface_client.ts` | Operator-side anchor client. |

## §13. Related Layer B chengyu

- **B047 錨在身外** — *anchor-outside-the-body*: §2 deposit
- **B048 證據非裁決** — *evidence-not-verdict*: §3.11 in chengyu form

## §14. Related canonical dilemmas

- **D-0046 anchor compromise scenario** — what does substrate do when anchor surface itself is suspected compromised?
- **D-0047 owner under duress signature** — F23 duress keypair flow + §5.6.

---

**Doctrine commitment**: substrate cannot self-attest; anchor IS the trust ground; 12 sub-mechanisms each carry load; witnesses-not-verdicts is the load-bearing principle.
