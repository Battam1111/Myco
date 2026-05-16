# L2 — Trust Model Doctrine

> **Status**: DRAFT 3 (2026-05-17, M27 R5 cleanup). M26-cascade A4 for L0 DRAFT 9 SEALED.
> **Scope**: cross-cut trust framing. Mechanism specs at L1 + L2_FEDERATION + L2_OBSERVABILITY.

---

## §1. The trust triad (per L0 §1)

Three trust-bearing parties; **carrier-asymmetric responsibilities** (L0 P1.c + §1.2):

| Party | Carries | Cannot author | Provides |
|---|---|---|---|
| **Substrate (Cultivar)** | substrate-ID, owner_key_history, DAG, SSoT | Cultivator signatures, anchor nonces, trusted timestamps, heartbeats, anchor client | Witnesses, enumerated DAG nodes, sealed `operator_token`, metabolism events |
| **Operator (agent)** | Per-handshake signing keypair (runtime memory only) | substrate_secret, substrate state, Cultivator signatures, anchor state | `operator_witness` signatures over canonical bytes |
| **Cultivator (owner)** | Anchor-surface, private signing key, optional `duress_keypair` (§10.A.2), liveness heartbeat | Substrate-internal state, operator-runtime state | All CI attestations, key rotations, successor pre-attestations, peer attestations, final-seal, duress attestations |

No party unilaterally fabricates trust; roles structurally non-substitutable (modulo P1.a + §10).

---

## §2-§5. Trust lifecycle (cross-refs)

- **§2 Establishment** — L1_GOVERNANCE §4.1 (genesis + substrate-ID + optional `duress_keypair`) + L1_SKIN §4.1 (operator pins out-of-band).
- **§3 Per-interaction** — L1_SKIN §4.2 (handshake), L1_SKIN §2 (delta `envelope_digest` HMAC), L1_TROPISM §B6 (sporocarp), L1_GOVERNANCE §2.2 (CI attestation; duress → §10.A.2).
- **§4 Maintenance** — L1_GOVERNANCE §3.1 (key rotation cooldown+veto+active-prefix); L1_SCHEMA §4.1 + L1_CONTINUITY §1.1 (tier-1/tier-2/I3+I4+I5+I8); L2_OBSERVABILITY §2 (10 signals; falsifiability quorum fires C40).
- **§5 Recovery** — L1_CONTINUITY §3 (cold-resume witnesses; failure → quarantined → `quarantine_clearance`); L1_GOVERNANCE §3.2 (heartbeat stale → `succession_required` → successor → `legacy`); L1_GOVERNANCE §4.4 (destruction three modes).

---

## §6-§8. Trust limits + federation + invariants

§6 limits: identity carrier substrate; cannot enforce against own host (L0 §6) or operator runtime; P1.a adversarial-maintainer attacks codebase (anchor raises bar); cannot enforce against adversarial Cultivator (§10); L0 §14.2 commitments survive.

§7 federation: see **L2_FEDERATION** (§6.3 peer attestation, §6.2 freshness, §6.4 non-transitivity, §13.1 Sybil, §13.2 Eclipse, §11 recursive injection).

§8 invariants: model rests on L0 §4 + §9 + L1_GOVERNANCE §2.2/§3.1 + L1_SKIN §4.2; when these hold AND §11 collapse closed, model addresses L1_HARD_RULES §1 CRITICAL breaches; novel classes caught by observatory drift.

---

## §10. Adversarial-Cultivator threat model (L0 §14 cascade)

L0 §14: Myco not safe under adversarial Cultivator; defenses raise attack cost.

**§10.A.1 Key compromise** — L1_GOVERNANCE §3.1: anchor-attested `rotation_request` from registered backup; 30-day cooldown with `rotation_veto`; optional n-of-m multisig (SHOULD; institutional MUST); below → `multisig_threshold_unmet`; quorum-emergency bypasses cooldown. Limits: primary captured pre-backup → out-of-band court-attested only.

**§10.A.2 Coerced Cultivator (duress)** — Pre-registered `duress_keypair` at genesis (separate Ed25519; separate medium). On duress-key verify: emit `coerced_owner_suspected` (CI-grade, F23); freeze destructive mutations; re-emit each CI until cleared; does NOT reject. Unfreeze: `out_of_band_safety_reattestation` OR `anchor_heartbeat_with_safety_confirmation`.

**§10.A.3 Impersonated Cultivator** — `owner_signature_velocity` rolling-window; after N=20 events: anomaly when rolling > `mean+3*stddev` OR `mean*100` → `owner_signature_velocity_anomaly`.

**§10.A.4 Deceased without succession** — L1_GOVERNANCE §3.2 + L0 §15: no successor → `legacy` → `orphaned`; terminal-state choice is genesis-Cultivator pre-attestation.

**§10.A.5 Anchor-client tampering** — L0 §9.3.3 + F6: Cultivator signs `anchor_client_provenance_attestation` at genesis declaring install channel structurally independent. v0.9: NOT provenance-independent (§11); M-anchor-1 closes.

**§10.B Irreducible commitments (L0 §14.2)**: Enforced via I9/I10/I12/I4: P6 causality; truthful observability + mortality signals; P10.b compression-invariant preservation.

---

## §11. Anchor-surface honor-system collapse window

v0.9 anchor surface honor-system; substrate documented-vulnerable until M-anchor-1..5.

**§11.1 Current state**: v0.9 `e796451`: owner key on same host as operator; nonces substrate-minted; wall-clock from operator process; anchor client uses same-package code; witnesses pass/fail not re-derivable. L0 §9.2: 9/11 sub-clauses 0-30% mechanical.

**§11.2 Attack surface**:

| Attack | Closed by |
|---|---|
| Cultivator-key disk extraction | M-anchor-1 |
| Substrate-minted nonce replay | M-anchor-3 |
| Process clock spoofing | M-anchor-3 |
| Anchor-client tampering (same npm) | M-anchor-1 |
| Witness omission (pass/fail) | M-anchor-4 |
| DAG-enumeration closure not Cultivator-side | M-anchor-5 |
| Owner-liveness-heartbeat library no callers | M-anchor-3 |
| L0 revision workflow absent | M-anchor-5 |

**§11.3 M-anchor closure**: M1 = key out of agent-spawnable process + anchor client independent channel + owner-side rendering. M2 = substrate-ID birth-attestation. M3 = anchor-issued nonces + anchor-clock + heartbeat. M4 = Merkle-witness emission + anchor-nonce-derived sampling. M5 = DAG-enumeration closure + L0 revision diff workflow.

**§11.4 Posture**: Until closure: Cultivator must trust same host as substrate process; §10 + §13 defenses are LANDING TARGETS; observatory + immune provide partial protection.

---

## §12. Time-semantics attacks (per L0 §13)

- **§12.1 NTP poisoning** — anchor wall-clock authoritative; L1_CONTINUITY NTP discipline; §11 → M-anchor-3.
- **§12.2 Year 2038 (i32)** — L0 §13.1 mandates i64 nanoseconds; I3 catches drift.
- **§12.3 Year 2262 (i64)** — `time_horizon_2262_warning` daily within L1-tunable horizon (default 100y); negative pre-1970 → `negative_epoch_timestamp`.
- **§12.4 Wall-clock untrustworthiness** — attestation expiry / cooldown / federation freshness → anchor-clock; DAG ordering → substrate-monotonic.

---

## §13. Federation + reproduction + skin attacks

Mechanisms at L2_FEDERATION + L1_SKIN; threat framing here:

- **§13.1 Sybil** — L1_GOVERNANCE §5: Cultivator-attested peer list; new peers CI-grade (F14); non-transitive (§6.4); requires §10 compromise.
- **§13.2 Eclipse** — defense: ≥3 peers from ≥3 independent organizational lineages; signals #4a/#4b. Cultivator does diverse selection + out-of-Myco cross-channel verification.
- **§13.3 Recursive injection** — L2_FEDERATION §9/§11 (wrapped-events + allowlist + recursive defense). Shipped M24/M25.
- **§13.4 Forkbomb** — L0 §16 + L1_GOVERNANCE §16: depth + rate + quota + per-spawn birth gate; requires §10 compromise or I7 violation.
- **§13.5 substrate_id collision** — hash of `(spore-schema-canonical-bytes, owner-pubkey, anchor-pubkey, genesis-timestamp)`; primitive break → suite migration; collision requires BOTH hash break AND key compromise.
- **§13.6 Backup privacy** — L1_SKIN backup encryption: operator-controlled symmetric; Cultivator out-of-band escrow; backups predating rotation readable with old key.
- **§13.7 Single-skin failure (P9.b)** — L1_SKIN §13 skin-restart; transport-error → quarantined → `skin_failure` immune → Cultivator `skin_restart_attestation`; extended failure → `legacy` or mortality; multi-skin rejected (P9).

---

## §14-§15. Glossary + cascade

§14 — base terms at L0 §12; trust-specific defined inline at §10/§11/§13.

§15 L1 cascade — F23 shipped; `owner_signature_velocity_anomaly` deferred. L1_GOVERNANCE §3.1 (multisig + duress + quorum-emergency); §3.2 (successor FSM + court-attested recovery); §5 (peer diversity). L1_CONTINUITY (NTP). L1_SCHEMA (i64 + year-2262). L1_SKIN (backup encryption). L2_FEDERATION (allowlist + wrapped-events). L2_OBSERVABILITY (`owner_signature_velocity` sub-signal).
