# L2 — Trust Model Doctrine

> **Status**: DRAFT 3 (2026-05-17, M27 R4 cleanup). M26-cascade A4 for L0 DRAFT 9 SEALED.
> **Scope**: cross-cut trust framing. Mechanism specs at L1 + L2_FEDERATION + L2_OBSERVABILITY.

---

## §1. The trust triad (per L0 §1)

Three trust-bearing parties; **carrier-asymmetric responsibilities** (L0 P1.c + §1.2 G-11.a):

| Party | Carries | Cannot author | Provides |
|---|---|---|---|
| **Substrate (Cultivar)** | substrate-ID, owner_key_history, DAG, SSoT | Cultivator signatures, anchor nonces, trusted timestamps, heartbeats, anchor client | Witnesses, enumerated DAG nodes, sealed `operator_token`, metabolism events |
| **Operator (agent)** | Per-handshake signing keypair (runtime memory only) | substrate_secret, substrate state, Cultivator signatures, anchor state | `operator_witness` signatures over canonical bytes |
| **Cultivator (owner)** | Anchor-surface, private signing key, optional `duress_keypair` (§10.A.2), liveness heartbeat | Substrate-internal state, operator-runtime state | All CI attestations, key rotations, successor pre-attestations, peer attestations, final-seal, duress attestations |

No party unilaterally fabricates trust; roles structurally non-substitutable (modulo P1.a + §10).

---

## §2-§5. Trust lifecycle (cross-refs)

- **§2 Establishment** — **L1_GOVERNANCE §4.1** (genesis + substrate-ID + optional `duress_keypair` per §10.A.2) + **L1_SKIN §4.1** (operator pins `(substrate-ID, anchor-pubkey, owner-pubkey)` out-of-band).
- **§3 Per-interaction** — **L1_SKIN §4.2** (handshake), **L1_SKIN §2** (delta `envelope_digest` HMAC), **L1_TROPISM §B6** (sporocarp), **L1_GOVERNANCE §2.2** (CI attestation; duress → §10.A.2).
- **§4 Maintenance** — **L1_GOVERNANCE §3.1** (key rotation cooldown+veto+active-prefix); **L1_SCHEMA §4.1 + L1_CONTINUITY §1.1** (tier-1/tier-2/I3+I4+I5+I8); **L2_OBSERVABILITY §2** (10 signals; falsifiability quorum fires C40 per L0 §10.2).
- **§5 Recovery** — **L1_CONTINUITY §3** (cold-resume witnesses; failure → quarantined → `quarantine_clearance`); **L1_GOVERNANCE §3.2** (heartbeat stale → `succession_required` → successor → `legacy`); **L1_GOVERNANCE §4.4** (destruction three modes; L2_LIFECYCLE §9).

---

## §6. Trust limits (declared)

- Substrate is identity carrier; operator-disconnect ends pair-instance, not identity.
- Cannot enforce against own host (L0 §6); Cultivator monitoring required.
- Cannot enforce against operator runtime (L1_SKIN §5.4); exfiltration is Cultivator concern.
- P1.a self-hosting: adversarial agent maintaining code can attack codebase; anchor raises bar.
- Cannot enforce against adversarial Cultivator (§10); L0 §14.2 commitments survive.

---

## §7-§8. Federation + invariants

§7 federation: see **L2_FEDERATION** (peer attestation §6.3, freshness §6.2, non-transitivity §6.4, Sybil §13.1, Eclipse §13.2, recursive injection §11).
§8 invariants: model rests on L0 §4 + L0 §9 + L1_GOVERNANCE §2.2/§3.1 + L1_SKIN §4.2; when these hold AND §11 collapse closed, model addresses L1_HARD_RULES §1 CRITICAL breaches; novel attack classes caught by observatory drift (L2_OBSERVABILITY §14).

---

## §10. Adversarial-Cultivator threat model (L0 §14 cascade)

L0 §14: Myco is not safe under adversarial Cultivator; defenses raise attack cost.

### §10.A Threat scenarios

- **§10.A.1 Key compromise** — L1_GOVERNANCE §3.1: anchor-attested `rotation_request` from registered backup; 30-day cooldown with `rotation_veto`; active-prefix history. Optional n-of-m multisig (SHOULD; institutional Cultivars MUST); below threshold → `multisig_threshold_unmet`; quorum-emergency rotation bypasses cooldown. Limits: primary captured pre-backup → out-of-band court-attested only.
- **§10.A.2 Coerced Cultivator (duress)** — Cultivator pre-registers `duress_keypair` at genesis (separate Ed25519; private on separate medium). On duress-key verify: emit `coerced_owner_suspected` (CI-grade, F23); freeze destructive mutations (`destruction_attestation`, mass rotation/deletion, schema replacement, I2 `destructive_irreversible`); re-emit each CI until cleared; does NOT reject. Unfreeze: `out_of_band_safety_reattestation` (primary at anchor) OR `anchor_heartbeat_with_safety_confirmation`.
- **§10.A.3 Impersonated Cultivator** — `owner_signature_velocity` rolling-window; seed 30-day daily-cadence; after N=20 events compute `baseline_mean`+`baseline_stddev`; anomaly when rolling > `mean+3*stddev` OR `mean*100` → `owner_signature_velocity_anomaly` (daily; CI-elevated in birth-period). Routes to anchor dashboard (L2_OBSERVABILITY §12); §10.A.5 catches source.
- **§10.A.4 Deceased without succession** — L1_GOVERNANCE §3.2 + L0 §15: no successor → `legacy` → `orphaned`; terminal-state choice (retirement / euthanasia / indefinite) is genesis-Cultivator pre-attestation. Court-attested recovery only if substrate genesis-configured.
- **§10.A.5 Anchor-client tampering** — L0 §9.3.3 + L1_HARD_RULES F6: Cultivator signs `anchor_client_provenance_attestation` at genesis declaring install channel structurally independent of substrate (same-machine local-binary INSUFFICIENT). Two-tool verification before high-stakes CI. **v0.9: NOT provenance-independent (§11 collapse)**; M-anchor-1 closes.

### §10.B Irreducible commitments (L0 §14.2)

Enforced regardless of Cultivator honesty (via I9/I10/I12/I4): P6 causality (DAG cannot erase); truthful observability emission; truthful mortality signals (dual-channel L1_GOVERNANCE §4.4); P10.b compression-invariant preservation (I9 rejects pressure, emits CRITICAL).

---

## §11. Anchor-surface honor-system collapse window

v0.9 anchor surface honor-system; substrate documented-vulnerable, NOT production-ready until M-anchor-1..5 close.

### §11.1 Current state — operator IS anchor

v0.9 `e796451`: owner key at `~/.myco/operator_keys/identity.key` on same host as operator (same npm workspace); nonces substrate-minted; wall-clock from operator process; anchor client uses same-package code; witnesses are pass/fail not re-derivable Merkle. L0 §9.2: 9 of 11 sub-clauses 0-30% mechanical.

### §11.2 Attack surface

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

### §11.3 M-anchor closure

- **M-anchor-1**: key out of agent-spawnable process + anchor client from independent channel + owner-side rendering (§9.2.3/§9.3.2/§9.3.3).
- **M-anchor-2**: substrate-ID birth-attestation owner-signature (§9.2.1).
- **M-anchor-3**: anchor-issued nonces + anchor-clock independence + liveness heartbeat (§9.2.5/§9.2.6/§9.2.7).
- **M-anchor-4**: Merkle-witness emission + anchor-nonce-derived sampling (§9.3.4/§9.3.5).
- **M-anchor-5**: DAG-enumeration closure check + L0 revision diff workflow (§9.2.2/§9.2.4/§9.3.6).

### §11.4 Posture

Until closure: Cultivator must trust same host as substrate process; §10 + §13 defenses are LANDING TARGETS not deployed; substrate observatory + immune provide partial protection.

---

## §12. Time-semantics attacks (per L0 §13)

- **§12.1 NTP poisoning** — anchor wall-clock authoritative (L0 §13.1 + §9.2.6); L1_CONTINUITY NTP discipline; §11 → M-anchor-3.
- **§12.2 Year 2038 (i32)** — L0 §13.1 mandates i64 nanoseconds; L1_SCHEMA cascade; I3 catches drift.
- **§12.3 Year 2262 (i64)** — L0 §13.2: `time_horizon_2262_warning` daily within L1-tunable horizon (default 100 years); negative pre-1970 → `negative_epoch_timestamp` daily.
- **§12.4 Wall-clock untrustworthiness** — L0 §13.1: attestation expiry / key rotation cooldown / federation freshness → anchor-clock; mortality drill timing → anchor-clock record + substrate-monotonic scheduling; DAG ordering → substrate-monotonic authoritative.

---

## §13. Federation + reproduction + skin attacks

Mechanisms at L2_FEDERATION + L1_SKIN; threat framing here:

- **§13.1 Sybil** — L1_GOVERNANCE §5: Cultivator-attested peer list; new peers CI-grade (F14); aggregate re-attestation O(1)/O(N); non-transitive (L2_FEDERATION §6.4); requires §10 compromise. Limits: bounded by Cultivator diligence.
- **§13.2 Eclipse** — defense: ≥3 peers from ≥3 independent organizational lineages (substrate cannot mechanically enforce diversity); signals #4a/#4b. Limits: Cultivator does diverse selection + out-of-Myco cross-channel verification.
- **§13.3 Recursive injection** — L2_FEDERATION §9/§11 (wrapped-events + allowlist + recursive defense); identity I1-protected TIER-1; federation cannot mutate identity. Shipped M24/M25.
- **§13.4 Forkbomb** — P8 + L0 §16 + L1_GOVERNANCE §16: depth + rate min-interval + lifetime quota + per-spawn birth gate; requires §10 compromise or I7 violation. Limits: loose defaults still cumulatively exhaust.
- **§13.5 substrate_id collision** — `hash(canonical-bytes(initial-spore-schema), owner-pubkey, anchor-endpoint-pubkey, genesis-timestamp)` (SHA-256+); primitive break → suite migration (L1_GOVERNANCE §3.1); birth-attestation anchors ID; collision requires BOTH hash break AND key compromise.
- **§13.6 Backup privacy** — L1_SKIN backup encryption (L0 §11.1): operator-controlled symmetric; Cultivator out-of-band escrow; rotation aligned with owner-key. Limits: backups predating rotation readable with old key.
- **§13.7 Single-skin failure (P9.b)** — L1_SKIN §13 skin-restart: transport-error detection → quarantined → `skin_failure` immune → Cultivator `skin_restart_attestation`; metabolism continues; skin declaration tier-1 CI-grade (F11). Limits: extended failure → `legacy` or mortality; multi-skin rejected (P9).

---

## §14-§15. Glossary + cascade obligations

§14 glossary — see **L0 §12** for Cultivator/Cultivar/Cultivation. Trust-specific: `duress_keypair` (§10.A.2); `owner_signature_velocity` (§10.A.3); `coerced_owner_suspected` (§10.A.2 F23); anchor-client provenance independence (§10.A.5, M-anchor-1); n-of-m multisig (§10.A.1); honor-system collapse window (§11; M-anchor-1..5); Sybil/Eclipse/Recursive injection/Forkbomb (§13.1-§13.4).

§15 L1 cascade — L1_HARD_RULES: F23 shipped; `owner_signature_velocity_anomaly` deferred. L1_GOVERNANCE §3.1: multisig + duress + quorum-emergency. L1_GOVERNANCE §3.2: successor FSM + court-attested recovery. L1_GOVERNANCE §5: peer diversity + audit hooks. L1_CONTINUITY: NTP discipline (§12.1). L1_SCHEMA: i64 + year-2262 + negative-pre-1970 (§12.3). L1_SKIN: backup encryption + escrow + rotation alignment (§13.6). L2_FEDERATION: allowlist + wrapped-events (§13.3). L2_OBSERVABILITY: `owner_signature_velocity` as §12 sub-signal.
