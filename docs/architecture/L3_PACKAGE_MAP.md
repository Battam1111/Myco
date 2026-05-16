# L3 — Package Map (module-by-module specification)

> **Status**: DRAFT 3 (2026-05-17, M27 R4 cleanup). Sizing pre-Phase-γ M22-M25.

---

## §1. Module index

| Module | L1 source | Responsibility | Dependencies |
|---|---|---|---|
| `kernel/shared` | — | Crypto + canonical-bytes serializer + sealed-derive | (none) |
| `kernel/skin` | L1_SKIN | Envelope + handshake + single-operator + egress | `kernel/shared` |
| `kernel/schema` | L1_SCHEMA | SSoT + Merkle DAG + spore-schema + validation tiers | `kernel/shared` |
| `kernel/governance` | L1_GOVERNANCE | Classifier + attestation envelope + lifecycle FSM | `kernel/skin`, `kernel/schema` |
| `kernel/continuity` | L1_CONTINUITY | Metabolic cycle + dormancy + cold-resume + WAL | `kernel/skin`, `kernel/schema` |
| `kernel/tropism` | L1_TROPISM | Appetite gradient + sporocarp emission + fruiting | `kernel/schema`, `kernel/continuity` |
| `kernel/trajectory` | L1_TRAJECTORY | Cluster_C + trajectory queries + thread_id + echo-chamber | `kernel/schema`, `kernel/tropism` |
| `kernel/hard_rules` | L1_HARD_RULES | Immune detection: C1-C20 + C30-C49 + F1-F25 | All kernel/* (citation) |
| `anchor_client` | L0 §9 + L1 | Owner-side render + sign + nonce + heartbeat | `kernel/shared` (spec) |
| `operator_bindings/<host>` | L1_SKIN §4.1 | Per-LLM-host runtime; per-handshake keypair; HMAC | `kernel/shared` (spec) |

Line-estimate ranges + total sizing: `diagrams/build_dependency.txt`. Build dependency graph (parallel groups): same file.

---

## §2. `kernel/shared`

L1_SCHEMA §3.1 + L0 §9.3 + L1_GOVERNANCE §3.1. Canonical-bytes serializer (deterministic; loadable by every party); crypto (Merkle hash content-addressed; signature verify against active-prefix + anchor nonces; HMAC `envelope_digest`); sealed-derive wrapper (substrate_secret over L4 TPM/keyring/HSM/secure-element); active-prefix + archived-tail primitive. **T1** per-primitive; **T2** sealed-derive vs L4. Critical: serializer round-trips identically across language bindings (single shared test suite).

---

## §3. `kernel/skin` (L1_SKIN §1-§6)

Skin surface + intake/output + forbidden surfaces; envelope validation (integrity/freshness/size/payload_shape/HMAC); operator handshake (`operator_signing_key_public`; non-deterministic `operator_token` via `sealed_derive`; bidirectional); single-operator (OS-accept-queue FIFO; `concurrent_connect_attempt`); network-egress enforcement (kernel netns / container / eBPF / userspace proxy — L4-picked); federation egress freshness; §6 ten breach categories. Sub-modules: `envelope` / `handshake` / `output_gate` / `egress_enforce`. **T1** envelope+handshake FSM; **T2** sealed-derive; **T3** e2e operator; **T4** adversarial (tamper, replay, concurrent, out-of-band egress).

---

## §4. `kernel/schema` (L1_SCHEMA §1-§4)

SSoT representation + designation (L4 format ∈ {YAML, TOML, JSON+JSONL, SQLite, custom}); Merkle DAG (content-addressed; parent-hash chain; tip; enumerated-node export at CI co-sign); spore-schema construction + validation; validation tier dispatch (tier-1 per cycle; tier-2 deep-cycle; tier-3 owner-triggered); recovery drill + sampled cold-tier + failure-rate baseline (§2.4). Sub-modules: `ssot` / `dag` / `spore` / `validation` / `recovery`. **T1** SSoT+DAG+Merkle+spore; **T2** drill vs backup; **T3** genesis-through-aging.

---

## §5. `kernel/governance` (L1_GOVERNANCE §1-§6)

Classifier (`classify(mutation_envelope) → {daily, CI, untyped}` against dimension-table tier-1 SSoT); birth-period CI elevation; attestation envelope (canonical-bytes; operator_witness verify; enumerated DAG nodes since last co-sign; anchor nonce; dual-clock expiry); lifecycle FSM (genesis; dormancy w/ continuity; reproduction w/ schema/spore; mortality three modes); owner key rotation FSM (cooldown + veto) + succession w/ liveness heartbeat; federation discovery + peer attestation + revocation + aggregate reattestation; failed P3 rollback. Sub-modules: `classifier` / `attestation` / `lifecycle` / `owner_keys` / `federation` / `rollback`. **T1** truth-table+dimension+round-trip; **T2** attestation w/ mock anchor; **T3** genesis → birth → steady → mortality.

---

## §6. `kernel/continuity` (L1_CONTINUITY §1-§5)

Metabolic cycle (5-step: tier-1 → gradient → delta-absorb → DAG-commit → skin-breach; cadence; backlog); dormancy FSM (alive ↔ dormant; throttled/paused; wake-on-attestation); cold-resume (pre-handshake invariants; witnesses; quarantine on failure); delta atomicity (WAL; crash-recovery; partial-delta); quarantine sub-state metabolism. Sub-modules: `cycle` / `dormancy` / `cold_resume` / `wal` / `quarantine`. **T1** cycle ordering+dormancy+WAL atomicity; **T2** cold-resume after simulated failure; **T3** multi-cycle w/ simulated crashes.

---

## §7. `kernel/tropism` (L1_TROPISM §1-§B10)

Appetite-axis schema + per-axis `update_rule` + threshold-emergence-rule (mortality-signal CI-protected per F7); gradient configuration + per-cycle advance; sporocarp emission (fruiting; type-tree; `causal_in_edges`; `template_version`); delta absorption; self-hosting bootstrap (kernel-evolution-tension appetite); birth-period vs steady-state switching. Sub-modules: `appetite` / `sporocarp` / `template_registry` (active-prefix + archived-tail) / `birth_period`. **T1** gradient+fruiting+causal_in_edges; **T2** delta → gradient → emission; **T3** birth → steady.

---

## §8. `kernel/trajectory` (L1_TRAJECTORY §1-§9 + L2_TRAJECTORY)

Cluster_C runtime (substrate-resident; CI-protected; epoch-bounded); query API (`causal_ancestors_and_descendants(neighborhood(t)) + cluster_C(.)`); cold-start (empty-DAG → `cold_start_marker`); thread_id grouping; echo-chamber detection (substrate-keyed delta-novelty + threshold); schema-evolution epoch boundary. Sub-modules: `cluster` / `query` / `epoch` / `echo_chamber`. **T1** cluster_C deterministic + epoch respected; **T2** trajectory over multi-cycle DAG; **T3** echo-chamber red-team.

---

## §9. `kernel/hard_rules` (L1_HARD_RULES §1-§5)

CRITICAL detectors (C1-C20 + C30-C49 substrate-private) — runtime observers reading other modules' emission streams; emit CRITICAL immune + auto-quarantine via `kernel/continuity/quarantine`; F-row watchdogs (F1-F25 incl. F18-F25 cascade) — observe CI fixed-point mutation; emit `classifier_fixed_point_bypass` etc.; birth-period CI elevation enforcement; anchor-surface-resident state non-authorability check. Sub-modules: `critical_detectors` / `fixed_point_watchdog` / `anchor_surface_check`. **T1** per-detector synthetic breach; **T2** integration real-breach; **T3+T4** adversarial — full per-C-row + per-F-row attack suite.

---

## §10. `anchor_client` (L0 §9 + L1_GOVERNANCE §2)

Canonical-bytes rendering (same `kernel/shared` serializer spec); signature production (owner key in OS-sealed storage; substrate never sees private key); nonce generation + consumed-nonce log; trusted wall-clock; owner liveness heartbeat (periodic `liveness_heartbeat`); aggregate-reattestation diff rendering (owner reviews diff); L0/L1 revision diff review (verbatim against prior commit hash). Sub-modules: `renderer` / `sealed_key` / `nonce_log` / `heartbeat` / `ui` (web / CLI / hardware-token — L4-picked). **T1** rendering identical to substrate; **T2** attestation w/ mock substrate; **T3** substrate-anchor e2e across attestation, rotation, federation re-attestation, mortality seal.

---

## §11. `operator_bindings/<host>` (L1_SKIN §4.1)

Per-handshake `operator_signing_key_public/_private` (private in operator-runtime memory only); HMAC envelope_digest signing (operator_token from handshake); independent canonical-bytes derivation; bootstrap-pinning (owner-provided `(substrate-ID, anchor-pubkey, owner-pubkey)` at first install); anchor query for current owner-pubkey-active-at-handshake (L2_TRUST_MODEL §3); trajectory query API consumer. Sub-modules: thin wrapper per binding; candidates: `claude_code` (Node.js), `mcp_typescript` (MCP/TS), `mcp_python` (MCP/Python). **T1** keypair+signature+HMAC; **T2** e2e handshake vs `kernel/skin`; **T3** full session including delta absorption + sporocarp observation.
