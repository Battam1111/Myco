# L2 — Trust Model Doctrine

> **Status**: DRAFT 2 (2026-05-17). M26-cascade A4 for L0 DRAFT 9 SEALED.
> **Scope**: cross-cut trust framing. Mechanism specs at L1 (governance/skin/schema/continuity) + L2_FEDERATION + L2_OBSERVABILITY.

---

## §1. The trust triad (per L0 §1)

Three trust-bearing parties with **carrier-asymmetric responsibilities** (per L0 P1.c + §1.2 G-11.a; "owner" remains valid for the governance role):

| Party | Carries | Cannot author | Provides |
|---|---|---|---|
| **Substrate (Cultivar)** | substrate-ID, owner_key_history, DAG, SSoT | Cultivator signatures, anchor nonces, trusted timestamps, heartbeats, anchor client | Witnesses, enumerated DAG nodes, sealed `operator_token`, metabolism events |
| **Operator (agent)** | Per-handshake signing keypair (runtime memory only) | substrate_secret, substrate state, Cultivator signatures, anchor state | `operator_witness` signatures over canonical bytes |
| **Cultivator (owner)** | Anchor-surface ownership, private signing key, optional `duress_keypair` (§10.A), liveness heartbeat | Substrate-internal state, operator-runtime state | All CI attestations, key rotation co-signs, successor pre-attestations, peer attestations/revocations, final-seal, duress attestations |

No party can unilaterally fabricate trust; each role is structurally non-substitutable (modulo P1.a self-hosting + §10 adversarial-Cultivator caveats).

---

## §2. Trust establishment (genesis)

Per **L1_GOVERNANCE §4.1**: Cultivator generates owner-keypair + selects anchor endpoint + verifies anchor-client provenance per L0 §9.3 (optionally registers `duress_keypair` per §10.A); runs `genesis`; substrate computes `substrate-ID = hash(canonical-bytes(initial-spore-schema), owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp)`; Cultivator signs birth attestation; substrate persists identity record. Birth attestation is the root of subsequent trust derivations.

**Operator bootstrap** (L1_SKIN §4.1): at first install, Cultivator provides `(substrate-ID, anchor-endpoint-pubkey, owner-pubkey)` out-of-band; operator pins these. Substrate is NEVER source of these values.

---

## §3. Trust at every interaction (steady state)

- **Operator handshake** (L1_SKIN §4.2): bidirectional; substrate emits `owner_birth_attestation_signature` + `owner_public_key_active_at_handshake`; operator cross-checks anchor surface; mismatch → reject.
- **Delta absorption** (L1_SKIN §2): envelope with `envelope_digest = HMAC(operator_token, ...)` + `causal_parent_ref`. Content unfiltered (P2).
- **Sporocarp emission with `causal_in_edges`** (L1_TROPISM §B6): I3 re-derives fruiting condition.
- **CI-level mutation attestation** (L1_GOVERNANCE §2.2): substrate requests anchor nonce → attestation envelope → Cultivator verifies (provenance-independent client; DAG-enumeration closure; nonce/TTL match) → signs `(substrate_id, dag_tip_hash, proposed_mutation_hash, operator_witness_signature, operator_signing_key_public, anchor_surface_nonce, anchor_surface_timestamp)`. Duress-keypair signature routes to §10.A.

---

## §4. Trust maintenance

- **Cultivator key rotation** (L1_GOVERNANCE §3.1): cooldown window with `rotation_veto` from any pre-registered key; active-prefix + archived-tail keeps tier-1 validation O(1).
- **Substrate self-validation** (L1_SCHEMA §4.1 + L1_CONTINUITY §1.1): tier-1 fields per metabolic cycle; tier-2 per deep cycle; I3 + I4 + I5 + I8 per 5-step cycle.
- **Living Bets observatory** (L2_OBSERVABILITY §2): 10 signals (6 base + 3 cost + 1 composite). Falsifiability: 90-day wall-clock rolling window quorum (≥3 of 6 signals trending against bet + signal #6 ratio <1 for ≥50% of samples) → `bet_weakening_quorum` (C40) requires Cultivator re-justification per L0 §10.2.

---

## §5. Trust recovery

- **Cold-resume** (L1_CONTINUITY §3): pre-handshake invariant checks (I1, I3, I4, I5, I8) emit **witnesses, not verdicts** sampled by anchor-nonce-derived indices; failure → `quarantined`; Cultivator-attested `quarantine_clearance` required.
- **Cultivator unavailability** (L1_GOVERNANCE §3.2): stale liveness heartbeat → `succession_required`; pre-attested successor activates; no successor → `legacy` sub-state.
- **Substrate destruction** (L1_GOVERNANCE §4.4): intentional-owner (signed `destruction_attestation` + final seal), catastrophic-environment (drill failures + medium-failure-beyond-budget), endogenous-pair (substrate `self_euthanasia_proposal` + Cultivator co-attestation).

---

## §6. Trust limits

Declared, not concealed:

- **Substrate is identity carrier**: bestowal flows substrate → operator at handshake; operator-disconnect ends a pair-instance, not substrate identity.
- **Cannot enforce against own host** (L0 §6): Cultivator-side monitoring required.
- **Cannot enforce against operator runtime** (L1_SKIN §5.4): exfiltration is Cultivator concern.
- **P1.a self-hosting**: adversarial agent maintaining code can attack codebase; anchor surface raises bar from "edit a file" to "compromise separate system".
- **Cannot enforce against adversarial Cultivator** (§10): substrate observes/emits, cannot reject legitimate signatures. L0 §14.2 irreducible commitments survive.

---

## §7. Trust at federation

See **`L2_FEDERATION.md`** for full doctrine: peer attestation + aggregate re-attestation (§6.3), peer-trust freshness (§6.2), egress per L1_SKIN §3.1, non-transitivity (§6.4), population-level adversary defenses (Sybil §13.1, eclipse §13.2, recursive injection §11). Threat-model framing in §13 below.

---

## §8. Trust model invariants summary

Trust model rests on L0 §4 invariants — see L0 §4 + L0 §9 + L1_GOVERNANCE §2.2/§3.1 + L1_SKIN §4.2 for individual mechanisms. When these hold AND §11 collapse window closed, model addresses L1_HARD_RULES §1 CRITICAL breaches. Novel attack classes caught by observatory drift signals (L2_OBSERVABILITY §14).

---

## §10. Adversarial-Cultivator threat model (L0 §14 cascade)

L0 §14: **Myco is not safe under adversarial Cultivator.** If governance gate is compromised/coerced/impersonated/absent-without-succession, no in-substrate defense fully substitutes. Defenses raise attack cost; not guaranteed safety.

### §10.A Threat scenarios

#### §10.A.1 Cultivator key compromise

**Threat**: attacker obtains primary Ed25519 key; CI co-signs verify as legitimate.

**Defenses**: anchor-attested key rotation (L1_GOVERNANCE §3.1) `rotation_request` from registered backup; cooldown window (default 30 anchor-trusted-timestamp days) during which ANY pre-registered key may `rotation_veto` (closes dual-sign attack); active-prefix key history keeps historical co-signs verifiable. **Limits**: primary captured before backup registered → out-of-band recovery only (L1_GOVERNANCE §3.2 court-attested).

**Recommendation — n-of-m multisig**: L1_GOVERNANCE §3.1 SHOULD specify optional m-of-n on structurally independent media. Below threshold → `multisig_threshold_unmet`. Multisig keys participate equally in rotation veto. Quorum-emergency rotation (≥m bypass cooldown) requires `quorum_emergency_attestation`; substrate emits `emergency_rotation_invoked`. L4-tunable; institutional Cultivars MUST use multisig.

#### §10.A.2 Coerced Cultivator (duress)

**Threat**: Cultivator signs CI under coercion; signatures verify legitimately.

**Defense — duress attestation**: Cultivator pre-registers `duress_keypair` (separate Ed25519) at genesis; public in birth attestation + identity record + anchor surface; private on separate medium. Under coercion, sign with duress_keypair. On duress-keypair verify, substrate (a) emits `coerced_owner_suspected` (CI-grade per F23); (b) freezes destructive mutations (`destruction_attestation`, mass key rotation, mass deletion, wholesale schema replacement, anything I2-classified `destructive_irreversible`); non-destructive continues; (c) re-emits at every CI boundary until cleared; (d) does NOT reject the signature outright (defeats purpose). Unfreeze: `out_of_band_safety_reattestation` signed by primary key at anchor, OR `anchor_heartbeat_with_safety_confirmation`. Channel L4-codified.

**Limits**: attacker capturing both keys; Cultivar without duress keypair registered; mistaken issuance (recoverable).

#### §10.A.3 Impersonated Cultivator

**Threat**: anchor-client compromised; attacker's signatures verify under legitimate owner-public-key.

**Defense — owner_signature_velocity**: rolling-window count of Cultivator-signed CI events per L1-tunable cadence (seed: 30-day window, daily cadence). After N=20 post-genesis events, compute `baseline_mean` + `baseline_stddev`; recompute after birth-period termination. Anomaly: rolling velocity > `mean + 3*stddev` OR `mean * 100` (L1-tunable) → emit `owner_signature_velocity_anomaly` (daily; CI-elevation during birth-period). Substrate does NOT reject signatures (verify → valid → rejecting breaks trust); signal goes to Cultivator via anchor dashboard (L2_OBSERVABILITY §12). Velocity catches BEHAVIORAL pattern; §10.A.5 anchor-client provenance catches SOURCE.

#### §10.A.4 Deceased Cultivator without succession

**Threat**: Cultivator permanently unavailable, no successor registered.

**Framing**: substrate MUST NOT manufacture trust, make destructive decisions alone, or silently terminate.

**Mechanism** (L1_GOVERNANCE §3.2 + L0 §15): no succession → `legacy` (alive, CI-frozen, daily ops continue); long-running `legacy` → `orphaned`; terminal-state choice (bet-retirement / endogenous self-euthanasia / indefinite-orphan) is genesis Cultivator-choice. **Court-attested key recovery**: legal authority issues `external_authority_succession`; honored only if substrate configured at genesis to recognize external authorities. Hardpoint where mechanical defense exhausts.

#### §10.A.5 Anchor-client tampering

**Threat**: anchor-surface client (L0 §9.3) modified to display different content than what is signed.

**Defense — anchor-client provenance independence** (L0 §9.3.3, L1_HARD_RULES F6): Cultivator signs `anchor_client_provenance_attestation` at genesis declaring install channel. Channel must be structurally independent of substrate-distribution (same-machine local-binary INSUFFICIENT; valid: HSM-vendor bundle vs. npm; separate Cultivator-controlled fork; institutional-CA-signed). Two-tool verification: render canonical bytes on a second independently-provenanced tool before signing high-stakes CI events. **Limits**: defends single-tool compromise, not coordinated multi-channel. Layer with §10.A.2 + §10.A.3.

**v0.9 status**: anchor client NOT currently provenance-independent (§11 collapse window). M-anchor-1 closes.

### §10.B Substrate's irreducible commitments (per L0 §14.2)

Four commitments enforced regardless of Cultivator honesty (via I9/I10/I12/I4): (1) P6 causality (DAG accumulates; cannot erase history); (2) truthful observability emission (substrate-mechanism, Cultivator cannot suppress); (3) truthful mortality signals (L1_GOVERNANCE §4.4 dual-channel; Cultivator can refuse co-attestation, cannot fake FALSE signals); (4) compression-invariant set preservation (L0 P10.b; I9 rejects pressure to compress; emits CRITICAL).

---

## §11. Anchor-surface honor-system collapse window

v0.9 anchor surface is honor-system. Until M-anchor-1 through M-anchor-5 close, substrate is documented-vulnerable, NOT production-ready.

### §11.1 Current state — operator IS anchor

At v0.9 commit `e796451`: owner Ed25519 key at `~/.myco/operator_keys/identity.key` on same host as operator runtime (same npm workspace); anchor nonces substrate-minted; wall-clock from operator process; anchor client uses same-package code; witnesses are pass/fail verdicts not re-derivable Merkle. Per L0 §9.2: 9 of 11 sub-clauses 0-30% mechanical; §9.3.1 (~95%) + §9.3.2 (~30%) partial.

### §11.2 Attack surface during collapse

| Attack | Closed by |
|---|---|
| Cultivator-key disk extraction | M-anchor-1 |
| Substrate-minted nonce replay | M-anchor-3 |
| Process clock spoofing | M-anchor-3 |
| Anchor-client tampering (same npm) | M-anchor-1 |
| Witness omission (pass/fail, not re-derivable) | M-anchor-4 |
| DAG-enumeration closure not Cultivator-side | M-anchor-5 |
| Owner-liveness-heartbeat library has no callers | M-anchor-3 |
| L0 revision workflow absent | M-anchor-5 |

### §11.3 M-anchor closure timeline

- **M-anchor-1**: Key out of agent-spawnable process + anchor client from independent channel + owner-side rendering live. Closes §9.2.3, §9.3.2, §9.3.3.
- **M-anchor-2**: Substrate-ID birth attestation owner-signature. Closes §9.2.1.
- **M-anchor-3**: Anchor-issued nonces + anchor-clock independence + owner liveness heartbeat. Closes §9.2.5, §9.2.6, §9.2.7.
- **M-anchor-4**: Merkle-witness emission + anchor-nonce-derived sampling. Closes §9.3.4, §9.3.5.
- **M-anchor-5**: DAG-enumeration closure check + L0 revision diff workflow. Closes §9.2.2, §9.2.4, §9.3.6.

### §11.4 Production-readiness posture

Until closure: Cultivator must trust same host as substrate process (no out-of-band escape); §10 + §13 defenses are LANDING TARGETS not deployed; substrate observatory + immune signals provide partial protection.

---

## §12. Time-semantics attacks (per L0 §13)

### §12.1 NTP poisoning

**Threat**: attacker controls substrate-process wall-clock → defeats dual-clock expiry by moving clock.

**Mitigation**: anchor-surface trusted wall-clock is authoritative (L0 §13.1 + §9.2.6); dual-clock attestation (both substrate-cycle + anchor-timestamp expiry required); L1_CONTINUITY NTP discipline policy per L0 §13.2 (source diversity, trusted sources NTS/signed-NTP, clock-drift monitoring). During §11 collapse, anchor-clock = operator-process; M-anchor-3 closes.

### §12.2 Year 2038 (i32) horizon

**Threat**: i32 timestamps overflow 2038-01-19 → silent corruption.

L0 §13.1: substrate MUST NOT use i32; i64 nanoseconds-since-epoch is canonical. L1_SCHEMA cascade enforces; I3 catches drift.

### §12.3 Year 2262 (i64) horizon-warning

**Threat**: i64 nanoseconds overflows ~2262-04-11.

L0 §13.2 cascade: L1_SCHEMA emits `time_horizon_2262_warning` daily as substrate approaches 2262 within L1-tunable horizon (default 100 years). Negative-pre-1970 forbidden → `negative_epoch_timestamp` daily.

### §12.4 Wall-clock untrustworthiness

Per L0 §13.1, substrate-cycle counters + process wall-clock NOT authoritative for: attestation expiry, owner-key rotation cooldown, federation peer-trust freshness (→ anchor-clock); mortality drill timing (→ anchor-clock for record, substrate-monotonic for scheduling); DAG event ordering (→ substrate-monotonic authoritative). During §11 collapse, all degrade to substrate-host-clock; M-anchor-3 closes.

---

## §13. Federation + reproduction + skin attacks

Threat-model framing; mechanisms at L2_FEDERATION + L1_SKIN.

### §13.1 Sybil

**Threat**: attacker creates many peers; population-consensus dominated.

**Defense — Cultivator-attested peer list** (L1_GOVERNANCE §5.1 default): owner curates approved IDs; new peers require attestation (CI-grade, L1_HARD_RULES F14). Aggregate re-attestation (L1_GOVERNANCE §5.2) gives O(1) workload; diffs are reviewed. Cultivator is bottleneck; Sybil requires §10 compromise; cross-substrate trust non-transitive (L2_FEDERATION §6.4). **Limits**: bounded by Cultivator due diligence.

### §13.2 Eclipse

**Threat**: attacker controls ALL peers a substrate connects to; coordinated false view despite individual attestation.

**Defense — diverse Cultivator-attested peers**: ≥3 peers from ≥3 independent organizational lineages. Substrate cannot enforce diversity mechanically. **Observability** (L2_FEDERATION §13 + L2_OBSERVABILITY §10): signals #4a/#4b. Eclipse presents partial signal (peers respond, content attacker-controlled). **Limits**: substrate cannot distinguish coordinated from honest; Cultivator does diverse peer-selection + out-of-Myco cross-channel verification.

### §13.3 Recursive injection

**Threat**: malicious peer crafts events causing receiver to emit posing-as-first-party events (`operator_pinned`, `cycle_advanced`, `genesis_event`).

**Spec**: L2_FEDERATION §9 (wrapped-events) + §9.4 (allowlist) + §11 (recursive defense). Identity-record fields are I1-protected TIER-1 SSoT; federation events cannot mutate identity. Shipped M24/M25.

### §13.4 Forkbomb

**Threat**: unbounded reproduction loop exhausts resources.

**Defense via P8** (L0 §16 + L1_GOVERNANCE §16): depth bound + rate min-interval + lifetime quota + per-spawn Cultivator-attested birth gate. Forkbomb requires §10 compromise or I7 violation. **Limits**: loose defaults still cumulatively exhaust; tight defaults preferred.

### §13.5 substrate_id collision

**Threat**: preimage attack on substrate-ID hash → impersonation.

**Defense**: substrate-ID = `hash(canonical-bytes(initial-spore-schema), owner-public-key, anchor-surface-endpoint-public-key, genesis-timestamp)` per L1_SCHEMA (SHA-256+). Primitive break → cryptographic suite migration (L1_GOVERNANCE §3.1). Birth-attestation signature anchors ID to Cultivator's key; collision substrate without Cultivator-attested birth fails handshake. Collision requires BOTH hash break AND key compromise.

### §13.6 Backup attack (privacy)

**Threat**: attacker reads backup media → full substrate state without compromising process.

**Defense via L1_SKIN backup encryption** (L0 §11.1 cascade): operator-controlled symmetric key (L1_SKIN DRAFT 2); not mandated at L0 (operational) but absence is acknowledged privacy surface. Key escrow: held by Cultivator out-of-band. Rotation aligned with owner-key rotation. **Limits**: backups predating rotation readable with old key; privacy-only attack; Cultivator backup-storage discipline load-bearing.

### §13.7 Single-skin failure (L1_SKIN P9.b)

**Threat**: skin endpoint failure (outage/crash/cert-expiry/DDoS) → cannot intake/emit. Availability attack.

**Defense via L1_SKIN §13 skin-restart discipline**: detect transport-level errors → `quarantined` on persistent failure → emit `skin_failure` immune → await Cultivator-attested `skin_restart_attestation`. Metabolism continues during quarantine. Skin declaration is CI-grade tier-1 (L1_HARD_RULES F11); attacker cannot reconfigure without attestation. **Limits**: extended skin-failure ages substrate; sustained → `legacy` or mortality. Multi-skin rejected: P9 single-boundary doctrinally preferred; L4 may reconsider.

---

## §14. Glossary

| Term | Definition |
|---|---|
| Cultivator / Cultivar / Cultivation | See L0 §12. |
| Duress attestation / keypair | Separate Ed25519 pre-registered (§10.A.2); private on separate medium; signs under coercion. |
| owner_signature_velocity | Rolling Cultivator-signed CI events count; anomaly → daily signal (§10.A.3). |
| coerced_owner_suspected | CI-grade signal on duress-keypair verify; freezes destructive mutations (§10.A.2). |
| Anchor-client provenance independence | Install channel structurally independent of substrate (L0 §9.3.3, §10.A.5; M-anchor-1). |
| n-of-m multisig | Optional m-of-n owner-key config (§10.A.1). |
| Honor-system collapse window | v0.9 collapsed operator+anchor (§11); closes via M-anchor-1 through M-anchor-5. |
| M-anchor-N | Milestone closing L0 §9.2/§9.3 sub-clauses (§11.3). |
| Sybil / Eclipse / Recursive injection / Forkbomb | §13.1 / §13.2 / §13.3 / §13.4. |

---

## §15. Cross-reference + L1 cascade obligations

- **L1_HARD_RULES**: `coerced_owner_suspected` shipped F23; `owner_signature_velocity_anomaly` deferred.
- **L1_GOVERNANCE §3.1**: n-of-m multisig + duress-keypair registration (F23) + quorum-emergency-rotation.
- **L1_GOVERNANCE §3.2**: successor FSM (L0 §15.2) + court-attested key recovery + deceased-without-succession terminal states.
- **L1_GOVERNANCE §5**: peer diversity (§13.2) + per-peer attestation audit hooks.
- **L1_CONTINUITY** (L0 §13.2): NTP discipline (§12.1).
- **L1_SCHEMA** (L0 §13.2): i64-nanoseconds + year-2262 horizon-warning + negative-pre-1970 (§12.3).
- **L1_SKIN** (L0 §11.1): backup encryption + key escrow + rotation alignment (§13.6).
- **L2_FEDERATION**: allowlist + wrapped-events (§13.3).
- **L2_OBSERVABILITY**: `owner_signature_velocity` as §12 sub-signal (§10.A.3).
