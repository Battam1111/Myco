> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L2 — Trust Model Doctrine

> **Scope**: cross-cut trust framing. Mechanism specs at L1 + L2/FEDERATION + L2/OBSERVABILITY. All numeric thresholds L1-tunable unless specified.

---

## §1. The trust triad (keyless v3.1.5; per L0/META §1 + §7.8 + L0/cards/P01_agent_primary.md)

Three trust-bearing parties; **carrier-asymmetric responsibilities** (L0 P1.c + §1.2). *(Keyless v3.1.5: the owner Ed25519 key + the out-of-band anchor surface — nonces, trusted timestamps, heartbeats, anchor client, duress keypair — are retired. The trust root is the keyless triad of META §7.8: the live human-in-the-loop at the CI gate + the causal DAG + the BLAKE3-sealed bundle.)*

| Party | Carries | Cannot author | Provides |
|---|---|---|---|
| **Substrate (Cultivar)** | substrate-ID, DAG, SSoT, its own signing keypair (F24) | substrate's own CI-class fixed-points (self-authoring), the cultivator's at-gate approval | Witnesses (re-derivable inputs), enumerated DAG nodes, sealed `operator_token`, metabolism events, BLAKE3 at-rest seal of its own state |
| **Operator (agent)** | Per-handshake signing keypair (runtime memory only) | substrate_secret, substrate state, the cultivator's at-gate approval | `operator_witness` signatures over canonical bytes |
| **Cultivator** | Presence + judgment at the live human-in-the-loop CI gate | Substrate-internal state, operator-runtime state | All CI approvals (at the gate), successor approvals, peer approvals, whole-death approval — keyless: by reviewing + approving in the loop, not by an owner signing key |

No party unilaterally fabricates trust; roles structurally non-substitutable (modulo P1.a + §10). The integrity that the owner key formerly provided is now provided by the **causal DAG** (P06, tamper-evident) + the **BLAKE3-sealed bundle** (doctrine integrity), both re-derivable by the cultivator at the gate.

---

## §2-§5. Trust lifecycle (cross-refs)

- **§2 Establishment** — L1/GOVERNANCE §4.1 (genesis + keyless substrate-ID; v3.1.5: no owner-keypair / anchor endpoint / duress_keypair) + L1/SKIN §4.1 (operator pins out-of-band).
- **§3 Per-interaction** — L1/SKIN §4.2 (handshake), L1/SKIN §2 (delta `envelope_digest` HMAC), L1/TROPISM §B6 (sporocarp), L1/GOVERNANCE §2.2 (CI approval at the live human-in-the-loop gate; keyless — the prior duress → §10.A.2 path is retired).
- **§4 Maintenance** — *(keyless v3.1.5: owner key rotation retired)* L1/SCHEMA §4.1 + L1/CONTINUITY §1.1 (tier-1/tier-2/I3+I4+I5+I8); L2/OBSERVABILITY §2 (10 signals; falsifiability quorum fires C40).
- **§5 Recovery** — L1/CONTINUITY §3 (cold-resume witnesses; failure → quarantined → `quarantine_clearance`); L1/GOVERNANCE §3.2 (keyless: no heartbeat-stale auto-transition — §10.A.4 acknowledged-debt; succession → successor → `legacy` gated by the C46 catechumenate floor); L1/GOVERNANCE §4.4 (whole-death: the single live `self_euthanasia_proposal` channel + bet-retirement; v3.1.5 drill-auto-emit retired).

---

## §6-§8. Trust limits + federation + invariants

§6 limits: identity carrier substrate; cannot enforce against own host, operator runtime, P1.a adversarial maintainer, or adversarial Cultivator (§10); L0/cards/P07_mortality.md §4 (substrate irreducible commitments) commitments survive. §7 federation → **L2/FEDERATION** (§6.2-§6.4 + §11-§13 enumerate Sybil / Eclipse / recursive injection / non-transitivity). §8 invariants: model rests on L0/cards invariants_enforced + Layer C witnesses + §9 + L1/GOVERNANCE §2.2 (keyless CI approval; v3.1.5: §3.1 owner-key-rotation retired) + L1/SKIN §4.2; with the keyless trust root (META §7.8) in place of the retired anchor surface (§11 resolved-by-retirement), addresses L1/HARD_RULES §1 CRITICAL breaches; novel classes caught by observatory drift.

---

## §10. Adversarial-Cultivator threat model (L0/cards/P07_mortality.md (mortality protection) cascade)

L0/cards/P07_mortality.md (mortality protection): Myco not safe under adversarial Cultivator; defenses raise attack cost.

**§10.A.1 Key compromise — RETIRED v3.1.5**: there is no owner key to compromise. The prior defense (anchor-attested `rotation_request` from a registered backup, 30-day cooldown + `rotation_veto`, n-of-m multisig) is removed with the owner key. The keyless analog of "a captured credential" is a compromised CI-gate session; its mitigation is the after-the-fact auditability of the change (causal DAG + BLAKE3-sealed bundle), not a cryptographic rotation.

**§10.A.2 Coerced Cultivator (duress) — RETIRED v3.1.5 (residual named as acknowledged-debt)**: the pre-registered `duress_keypair` (F23) is removed with the anchor surface. But **the threat is real without it** (D-0047, reframed keyless): the keyless trust root *is* the live human at the CI gate, so a coerced live human is precisely the residual gap. There is **no cryptographic duress channel** to silently flag coercion; the only after-the-fact protections are the auditable causal DAG + BLAKE3-sealed bundle (the *change* is visible) + the cultivator's fiduciary covenant (COV01/COV02). This is honestly named acknowledged-debt — see §10.A.4 + L0 D-0047.

**§10.A.3 Impersonated Cultivator — RETIRED v3.1.5**: `owner_signature_velocity` anomaly detection is removed (there are no owner signatures to rate). The keyless analog — anomalous CI-gate activity — has no cryptographic velocity detector; it is acknowledged-debt alongside §10.A.2.

**§10.A.4 Deceased without succession (KEPT, keyless)** — L1/GOVERNANCE §3.2 + L0/cards/COV06_no_abandonment_succession.md: no successor → `legacy` → `orphaned`; the terminal-state choice is the genesis-cultivator's pre-decided `cultivation_orphaned_terminal_choice`. *(Keyless v3.1.5: there is no anchor liveness-heartbeat to auto-time the `legacy`/`orphaned` transition — that detection is acknowledged-debt per COV06 §8.5; `alive::orphaned` is established by a human-in-the-loop, e.g. a pre-named contact, and its un-suppressibility is enforced by C69. Succession activation is gated solely by the C46 catechumenate-session floor, keyless.)* This is also the home of the keyless residual coercion concern (D-0047): the live human-in-the-loop is both the trust root and its own residual risk.

**§10.A.5 Anchor-client tampering — RETIRED v3.1.5**: the anchor client (and F6 `anchor_client_provenance_attestation`) is removed with the anchor surface; there is no anchor-client to tamper. The cultivator's review tooling at the live CI gate is ordinary software whose integrity is a deployment concern, not a doctrinal fixed-point.

**§10.B Irreducible commitments (L0/cards/P07_mortality.md §4 (substrate irreducible commitments))**: Enforced via I9/I10/I12/I4: P6 causality; truthful observability + mortality signals; P10.b compression-invariant preservation.

---

## §11. Anchor-surface honor-system collapse window — RESOLVED-BY-RETIREMENT v3.1.5

The prior v0.9 "anchor honor-system collapse" gap — owner key on the same host as the operator, substrate-minted nonces, operator-process wall-clock, same-package anchor client, witnesses not re-derivable — described a *partially-collapsed* anchor surface that never reached full independence. **v3.1.5 resolves this by retiring the anchor surface entirely** rather than hardening it. The trust model no longer claims an out-of-band cryptographic root; it claims the keyless triad (META §7.8): the **live human-in-the-loop at the CI gate** (genuinely out-of-process — a present human), the **causal DAG** (tamper-evident, re-derivable), and the **BLAKE3-sealed bundle** (doctrine integrity). The honor-system framing is moot: there is no anchor to honor. The keyless residual risks (no trusted wall-clock; in-the-moment coercion at the gate) are named at §10.A.2/§10.A.4 + L0 D-0047. Irreducible commitments (§10.B) are unchanged.

---

## §12. Time-semantics attacks (per L0/cards/P06.md + COV01 + COV02 + COV06 + P08)

- **§12.1 NTP poisoning** — *(Keyless v3.1.5: there is no anchor-stamped trusted wall-clock; the substrate's monotonic clock orders within-substrate events, and time-bearing security checks are acknowledged-debt — §10.A.4 / COV06 §8.5. NTP poisoning of the host clock therefore cannot subvert a security-bearing timeout, because there is no such keyless timeout to subvert; re-arming one requires a trusted-time source.)*
- **§12.2 Year 2038 (i32)** — L0/cards/P06_eternal_causality.md + L1/CONTINUITY (time semantics) mandates i64 nanoseconds; I3 catches drift.
- **§12.3 Year 2262 (i64)** — `time_horizon_2262_warning` daily within horizon (default 100y); negative pre-1970 → `negative_epoch_timestamp`.
- **§12.4 Wall-clock untrustworthiness** — DAG ordering → substrate-monotonic (kept). *(Keyless v3.1.5: the prior "→ anchor-clock for attestation expiry / cooldown / federation freshness" is retired — no anchor clock; CI approval is a live-human-in-the-loop act with no expiry timer, key rotation is gone, and federation freshness windows that needed a trusted clock are acknowledged-debt.)*

---

## §13. Federation + reproduction + skin attacks

Mechanisms at L2/FEDERATION + L1/SKIN; threat framing here:

- **§13.1 Sybil** — L1/GOVERNANCE §5: Cultivator-attested peer list; new peers CI-grade (F14); non-transitive (§6.4); requires §10 compromise.
- **§13.2 Eclipse** — defense: ≥3 peers from ≥3 independent organizational lineages; signals #4a/#4b. Cultivator does diverse selection + out-of-Myco cross-channel verification.
- **§13.3 Recursive injection** — L2/FEDERATION §9/§11 (wrapped-events + allowlist + recursive defense).
- **§13.4 Forkbomb** — L0/cards/P08_eternal_reproduction.md (generation limits) + L1/GOVERNANCE §16: depth + rate + quota + per-spawn birth gate; requires §10 compromise or I7 violation.
- **§13.5 substrate_id collision** — keyless `hash(spore-schema-canonical-bytes, genesis-timestamp)` *(v3.1.5: owner-pubkey + anchor-pubkey inputs dropped)*; primitive break → suite migration. *(Keyless: the prior "collision requires BOTH hash break AND key compromise" no longer holds — there is no key; collision-resistance rests on the hash primitive + the genesis-timestamp entropy alone. C45 `substrate_id_low_entropy_collision` is the relevant guard.)*
- **§13.6 Backup privacy** — L1/SKIN backup encryption: the cultivator holds the symmetric key (the substrate persists only a public status field; F5 at-rest seal `substrate/src/at_rest_seal.rs`). *(Keyless v3.1.5: the prior "backups predating rotation readable with old key" no longer applies — there is no owner-key rotation; the backup key is the cultivator's own, independent of the retired owner key.)*
- **§13.7 Single-skin failure (P9.b)** — L1/SKIN §13 skin-restart; transport-error → quarantined → `skin_failure` immune → Cultivator `skin_restart_attestation`; extended failure → `legacy` or mortality; multi-skin rejected (P9).

---

## §14. L1 cascade

*(Keyless v3.1.5: the multisig + duress + quorum-emergency + `owner_signature_velocity` items are retired with the owner key/anchor surface.)* L1/GOVERNANCE §3.2 (successor FSM, keyless — C46 catechumenate floor; no court-attested key recovery); §5 (peer diversity). L1/CONTINUITY (time semantics — no anchor clock). L1/SCHEMA (i64 + year-2262). L1/SKIN (backup encryption — F5 at-rest seal). L2/FEDERATION (allowlist + wrapped-events). L2/OBSERVABILITY (the `owner_signature_velocity` sub-signal is retired).
