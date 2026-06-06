---
id: AS
slogan: 锚定面（已废止）
english: Anchor Surface (§9 — Superseded v3.1.5; owner-key/anchor root retired)
category: Postulate
layer: Anchor surface
status: Superseded
version: 3
introduced: "L0 DRAFT 1 (2025-11) as §9"
last_reframed: "2026-06-06"
superseded_by: "META §7.8 (trust root = live human-in-the-loop + causal DAG + BLAKE3-sealed bundle)"
deposit_immutable: false
invariants_enforced: [I1, I2, I4]
interacts_with: [P01, P01c, P03, P06, P07, P08, COV01, COV02, COV06]
chengyu_fragments: [B047_anchor_outside_substrate, B048_witness_not_verdict]
canonical_dilemmas: [D-0047_owner_under_duress_signature]
structural_anchors:
  - "substrate/src/attestation.rs" # keyless: the owner-key/anchor-surface primitives were removed here (v3.1.5)
  - "substrate/src/events/attestation.rs::genesis_attested_node_type" # the kept keyless invariant-witness machinery (M-anchor-4 witnesses-not-verdicts, now consumed at the live CI gate)
witnesses:
  kind: executable
  positive: "substrate/tests/e2e_attestation.rs::m_anchor_4_invariant_witnesses_emitted_at_boot_for_each_tier_1_check"
  negative: "substrate/tests/e2e_attestation.rs::m_anchor_4_invariant_witness_inputs_decode_and_carry_substrate_id"
  edge: "substrate/tests/e2e_attestation.rs::m_anchor_4_witness_decode_helper_roundtrip"
falsifiability_signals:
  - invariant_witness_emission_status
---

# AS · 锚定面 · Anchor Surface (§9) — **Superseded v3.1.5**

> **Superseded v3.1.5** — the owner-key + out-of-band anchor-surface cryptographic root was **removed** from Myco (the owner Ed25519 key, the anchor-surface host process, anchor-issued nonces, anchor-stamped wall-clock, the owner-liveness heartbeat, DAG-tip co-signing, `l0_revision_attest`, the duress keypair, and the birth-attestation signature chain). The **trust root is now** the **live human-in-the-loop at the CI gate** (META §7.8) + the substrate's own **causal DAG** (P06) + the **BLAKE3-sealed doctrine bundle** (the keyless seal = the BLAKE3 hash of the L0 bundle, with no owner signature). This card is retained **in place** for provenance (the *isnad* chain): PROVENANCE §2 still maps prior-L0 §9 / §9.2.x / §9.3.x to this file, and the card count (28) is unchanged.

## §1. What was retired, what was kept

**Retired (gone from code + doctrine, v3.1.5):**

- The **owner Ed25519 key** and every owner-signature gate (birth attestation, CI co-attestation, succession signature, destruction signature).
- The **anchor surface** as an out-of-band process: anchor-issued nonces (§9.2.5), anchor-stamped trusted wall-clock (§9.2.6), the owner-liveness heartbeat (§9.2.7), DAG-tip co-signing (§9.2.2), the `l0_revision_attest` co-sign (§9.2.4), the anchor-client provenance surface (§9.3.3), and the REVEAL/duress keypair machinery.
- Detectors **C12, C17, C20, C44, C50, C70** (retired — their numbers are **reserved**, not renumbered; see L1/HARD_RULES).
- Fixed-points **F3** (owner_key_history), **F4** (anchor_surface_endpoint_public_key), **F6** (anchor_client_provenance), **F23** (duress_keypair).

**Kept (keyless), the load-bearing residue of the old §9:**

- The **witnesses-not-verdicts** discipline (old §9.3.4 / §3.11) survives in spirit and in code: the substrate still emits **invariant witnesses** (canonical-bytes inputs the verifier re-derives) rather than self-asserted verdicts — but the verdict is now re-derived by the **live human-in-the-loop at the CI gate**, not by an anchor-client holding an owner key. This is what the kept M-anchor-4 witness tests exercise (§3 witness map).
- **F24** — the substrate's **own** private signing keypair (it signs its own `snapshot.cb` + federation hello). This is NOT the owner key; it is kept.
- **F5** (at-rest seal) and **F2** (substrate-ID immutability) — kept.
- **F16** canonical-bytes serialization + the **C7** Merkle re-derivation that catches parallel-branch forgery (old §9.3.6 closure check) — kept; these never needed an owner key.

## §2. Where the deposit's concern now lives

The old deposit was "the substrate cannot self-attest; trust is vested outside the substrate's own process." That concern is **not abandoned** — it is **relocated**:

| Old anchor mechanism | Keyless successor (v3.1.5) |
|---|---|
| Owner signature at CI | **Live human-in-the-loop approval** at the CI gate (META §7.8; L2/TRUST_MODEL) |
| Out-of-band cryptographic root | The **BLAKE3-sealed doctrine bundle** (tamper-evident; the seal is the bundle hash) + the substrate's **causal DAG** (P06) |
| Witnesses-not-verdicts (anchor re-derives) | Witnesses-not-verdicts (the **human + CI re-derive**; substrate still emits inputs, not verdicts) |
| Anchor-stamped wall-clock | (no trusted wall-clock) — acknowledged debt; time-bearing detections (e.g., COV06 heartbeat-staleness) are deferred until a trusted-time source returns |

The substrate still **cannot** vest trust in its own self-claims; what changed is that the external authority is a **present human at the gate + a sealed bundle + an append-only causal chain**, rather than a cryptographic owner key.

## §3. Witness map (keyless — kept M-anchor-4 invariant-witness machinery)

The three witnesses point at the **kept** invariant-witness tests — the part of old §9 that survived (witnesses-not-verdicts), now re-derived at the live CI gate rather than by an owner-keyed anchor-client:

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `substrate/tests/e2e_attestation.rs::m_anchor_4_invariant_witnesses_emitted_at_boot_for_each_tier_1_check` | The substrate emits an invariant **witness** (re-derivable evidence) for each Tier-1 check at boot — it surfaces inputs for a verifier, it does not assert a verdict. |
| **Negative** | `substrate/tests/e2e_attestation.rs::m_anchor_4_invariant_witness_inputs_decode_and_carry_substrate_id` | The witness inputs decode and carry the substrate-ID — a tampered/empty witness fails to decode, so a substrate cannot pass off a self-asserted verdict in place of re-derivable evidence. |
| **Edge** | `substrate/tests/e2e_attestation.rs::m_anchor_4_witness_decode_helper_roundtrip` | Boundary: an invariant witness round-trips through its decode helper — evidence the verifier can re-derive, the keyless heart of witnesses-not-verdicts. |

## §4. Frame (retained, reframed)

The old **gold-standard physical anchor** frame is retired with the cryptographic anchor. The keyless frame is **"a witness deposed before a present judge"**: the substrate gives testimony (re-derivable evidence) and a present human-in-the-loop weighs it at the CI gate. The deposit's anti-self-attestation spirit is preserved; the external reference is the human + the sealed bundle + the DAG, not a vault holding an owner key.

## §5. Related Layer B chengyu

- **B047 錨在身外** — *anchor-outside-the-body*: now **[DORMANT]** (the cryptographic anchor it imaged is retired). Retained, not deleted, per META §4.3.
- **B048 證據非裁決** — *evidence-not-verdict*: still live, **re-derived from P06** (the substrate emits causal evidence; the live human-in-the-loop renders the verdict at the CI gate).

## §6. Related canonical dilemmas

- **D-0047 owner-under-duress** — **reframed keyless**: the threat (a cultivator coerced while approving at the live human-in-the-loop CI gate) is **real without** a duress keypair. See canonical_dilemma_corpus/INDEX.md#D-0047.
- *(D-0046 anchor-compromise is **retired** — the anchor it concerned no longer exists.)*

## §7. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2025-11 | Introduced in L0 DRAFT 1 as §9 with 12 sub-mechanisms (§9.2.x + §9.3.x). |
| 1.1 | 2026-05-17 (M27) | Compression refactor. |
| 2 | 2026-05-18 | v3.1 schema. Consolidated §9 + §9.5 into one specialized card. |
| **3** | **2026-06-06** | **Superseded v3.1.5 (keyless-anchor retirement). The owner-key + anchor-surface cryptographic root removed from substrate Rust + Python kernel + the deleted anchor crate + the keyless operators. Trust root relocated to META §7.8 (live human-in-the-loop + causal DAG + BLAKE3-sealed bundle). Detectors C12/C17/C20/C44/C50/C70 retired (numbers reserved); fixed-points F3/F4/F6/F23 deleted; F24/F5/F2/F16 + C7 kept. Card retained in place (status: Superseded) so PROVENANCE §2 isnad mapping resolves + the 28-card / 36-file counts are unchanged. Witnesses re-grounded to the kept M-anchor-4 invariant-witness tests (witnesses-not-verdicts survives keyless).** |

---

**Doctrine commitment (superseded)**: the substrate cannot self-attest. The owner key and anchor surface that once carried this are retired; the trust root is now the live human-in-the-loop at the CI gate + the substrate's causal DAG + the BLAKE3-sealed doctrine bundle. Retained for provenance.
