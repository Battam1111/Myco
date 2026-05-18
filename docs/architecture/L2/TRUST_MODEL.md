> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L2 — Trust Model Doctrine

> **Scope**: cross-cut trust framing. Mechanism specs at L1 + L2/FEDERATION + L2/OBSERVABILITY. All numeric thresholds L1-tunable unless specified.

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

- **§2 Establishment** — L1/GOVERNANCE §4.1 (genesis + substrate-ID + optional `duress_keypair`) + L1/SKIN §4.1 (operator pins out-of-band).
- **§3 Per-interaction** — L1/SKIN §4.2 (handshake), L1/SKIN §2 (delta `envelope_digest` HMAC), L1/TROPISM §B6 (sporocarp), L1/GOVERNANCE §2.2 (CI attestation; duress → §10.A.2).
- **§4 Maintenance** — L1/GOVERNANCE §3.1 (key rotation cooldown+veto+active-prefix); L1/SCHEMA §4.1 + L1/CONTINUITY §1.1 (tier-1/tier-2/I3+I4+I5+I8); L2/OBSERVABILITY §2 (10 signals; falsifiability quorum fires C40).
- **§5 Recovery** — L1/CONTINUITY §3 (cold-resume witnesses; failure → quarantined → `quarantine_clearance`); L1/GOVERNANCE §3.2 (heartbeat stale → `succession_required` → successor → `legacy`); L1/GOVERNANCE §4.4 (destruction three modes).

---

## §6-§8. Trust limits + federation + invariants

§6 limits: identity carrier substrate; cannot enforce against own host, operator runtime, P1.a adversarial maintainer, or adversarial Cultivator (§10); L0 §14.2 commitments survive. §7 federation → **L2/FEDERATION** (§6.2-§6.4 + §11-§13 enumerate Sybil / Eclipse / recursive injection / non-transitivity). §8 invariants: model rests on L0 §4 + §9 + L1/GOVERNANCE §2.2/§3.1 + L1/SKIN §4.2; when these hold AND §11 collapse closed, addresses L1/HARD_RULES §1 CRITICAL breaches; novel classes caught by observatory drift.

---

## §10. Adversarial-Cultivator threat model (L0 §14 cascade)

L0 §14: Myco not safe under adversarial Cultivator; defenses raise attack cost.

**§10.A.1 Key compromise** — L1/GOVERNANCE §3.1: anchor-attested `rotation_request` from registered backup; 30-day cooldown with `rotation_veto`; optional n-of-m multisig (SHOULD; institutional MUST); below → `multisig_threshold_unmet`; quorum-emergency bypasses cooldown. Limits: primary captured pre-backup → out-of-band court-attested only.

**§10.A.2 Coerced Cultivator (duress)** — Pre-registered `duress_keypair` at genesis (separate Ed25519; separate medium). On duress-key verify: emit `coerced_owner_suspected` (CI-grade, F23); freeze destructive mutations; re-emit each CI until cleared; does NOT reject. Unfreeze: `out_of_band_safety_reattestation` OR `anchor_heartbeat_with_safety_confirmation`.

**§10.A.3 Impersonated Cultivator** — `owner_signature_velocity` rolling-window; after N=20 events: anomaly when rolling > `mean+3*stddev` OR `mean*100` → `owner_signature_velocity_anomaly`.

**§10.A.4 Deceased without succession** — L1/GOVERNANCE §3.2 + L0 §15: no successor → `legacy` → `orphaned`; terminal-state choice is genesis-Cultivator pre-attestation.

**§10.A.5 Anchor-client tampering** — L0 §9.3.3 + F6: Cultivator signs `anchor_client_provenance_attestation` at genesis declaring install channel structurally independent. Under §11 collapse: not provenance-independent.

**§10.B Irreducible commitments (L0 §14.2)**: Enforced via I9/I10/I12/I4: P6 causality; truthful observability + mortality signals; P10.b compression-invariant preservation.

---

## §11. Anchor-surface honor-system collapse window

Anchor surface honor-system: owner key on same host as operator; nonces substrate-minted; wall-clock from operator process; anchor client uses same-package code; witnesses pass/fail not re-derivable. Under collapse: Cultivator must trust same host as substrate process; §10 + §13 defenses are landing targets; observatory + immune provide partial protection. Attack-surface inventory + closure milestones: README §Status + L3/PACKAGE_MAP.md. Irreducible commitments (§10.B) survive collapse.

---

## §12. Time-semantics attacks (per L0 §13)

- **§12.1 NTP poisoning** — anchor wall-clock authoritative; L1/CONTINUITY NTP discipline; closure under §11.
- **§12.2 Year 2038 (i32)** — L0 §13.1 mandates i64 nanoseconds; I3 catches drift.
- **§12.3 Year 2262 (i64)** — `time_horizon_2262_warning` daily within horizon (default 100y); negative pre-1970 → `negative_epoch_timestamp`.
- **§12.4 Wall-clock untrustworthiness** — attestation expiry / cooldown / federation freshness → anchor-clock; DAG ordering → substrate-monotonic.

---

## §13. Federation + reproduction + skin attacks

Mechanisms at L2/FEDERATION + L1/SKIN; threat framing here:

- **§13.1 Sybil** — L1/GOVERNANCE §5: Cultivator-attested peer list; new peers CI-grade (F14); non-transitive (§6.4); requires §10 compromise.
- **§13.2 Eclipse** — defense: ≥3 peers from ≥3 independent organizational lineages; signals #4a/#4b. Cultivator does diverse selection + out-of-Myco cross-channel verification.
- **§13.3 Recursive injection** — L2/FEDERATION §9/§11 (wrapped-events + allowlist + recursive defense).
- **§13.4 Forkbomb** — L0 §16 + L1/GOVERNANCE §16: depth + rate + quota + per-spawn birth gate; requires §10 compromise or I7 violation.
- **§13.5 substrate_id collision** — hash of `(spore-schema-canonical-bytes, owner-pubkey, anchor-pubkey, genesis-timestamp)`; primitive break → suite migration; collision requires BOTH hash break AND key compromise.
- **§13.6 Backup privacy** — L1/SKIN backup encryption: operator-controlled symmetric; Cultivator out-of-band escrow; backups predating rotation readable with old key.
- **§13.7 Single-skin failure (P9.b)** — L1/SKIN §13 skin-restart; transport-error → quarantined → `skin_failure` immune → Cultivator `skin_restart_attestation`; extended failure → `legacy` or mortality; multi-skin rejected (P9).

---

## §14. L1 cascade

L1/GOVERNANCE §3.1 (multisig + duress + quorum-emergency); §3.2 (successor FSM + court-attested recovery); §5 (peer diversity). L1/CONTINUITY (NTP). L1/SCHEMA (i64 + year-2262). L1/SKIN (backup encryption). L2/FEDERATION (allowlist + wrapped-events). L2/OBSERVABILITY (`owner_signature_velocity` sub-signal).
