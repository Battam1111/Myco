# L3 — Package Map (module-by-module specification)

> **Status**: DRAFT 2 (2026-05-17, M27 CA5 cleanup). Line-estimate ranges are pre-Phase-γ M22-M25 sizing.

---

## §1. Module index

| Module | L1 source | Responsibility | Dependencies | Lines (est.) |
|---|---|---|---|---|
| `kernel/shared` | — | Crypto + canonical-bytes serializer + sealed-derive wrapper | (none — foundation) | 1000-1500 |
| `kernel/skin` | L1_SKIN | Envelope + handshake + single-operator + egress enforcement | `kernel/shared` | 1500-2500 |
| `kernel/schema` | L1_SCHEMA | SSoT + Merkle DAG + spore-schema + validation tiers | `kernel/shared` | 2000-3000 |
| `kernel/governance` | L1_GOVERNANCE | Classifier + attestation envelope + lifecycle FSM | `kernel/skin`, `kernel/schema` | 2500-3500 |
| `kernel/continuity` | L1_CONTINUITY | Metabolic cycle + dormancy + cold-resume + delta atomicity | `kernel/skin`, `kernel/schema` | 1500-2500 |
| `kernel/tropism` | L1_TROPISM | Appetite gradient + sporocarp emission + fruiting evaluator | `kernel/schema`, `kernel/continuity` | 2000-3000 |
| `kernel/trajectory` | L1_TRAJECTORY | Cluster_C + trajectory queries + thread_id + echo-chamber | `kernel/schema`, `kernel/tropism` | 1500-2500 |
| `kernel/hard_rules` | L1_HARD_RULES | Immune detection: C1-C20 + C30-C49 + F1-F25 | All other kernel/* (citation; runtime) | 1500-2500 |
| `anchor_client` | (L0 §9 + L1) | Owner-side render + sign + nonce + heartbeat | `kernel/shared` (serializer spec) | 2000-3000 |
| `operator_bindings/<host>` | L1_SKIN §4.1 | Per-LLM-host runtime; per-handshake keypair; HMAC envelope | `kernel/shared` (serializer spec) | 500-1000 per binding |

**Totals**: substrate-kernel ~12000-19000; +anchor_client + operator bindings: +3000-5000. v0.9 first-birth ~15000-24000 lines.

---

## §2. `kernel/shared`

**Responsibilities** (L1_SCHEMA §3.1 + L0 §9.3 + L1_GOVERNANCE §3.1):
- Canonical-bytes serializer: pure-declarative; deterministic typed-values → bytes; loadable by every party for independent derivation.
- Crypto primitives: Merkle hash (content-addressed; tree; closure verification); signature verify (`owner_key_history` active prefix; anchor-surface nonces); HMAC (envelope_digest).
- Sealed-derive wrapper: OS-level sealing API for substrate_secret over L4-picked mechanism (TPM/keyring/HSM/secure-element); substrate code never sees plaintext.
- Active-prefix + archived-tail primitive: used by `kernel/governance` (`owner_key_history`, federation aggregate-reattestation) + `kernel/tropism` (`template_version_registry`).

**Test discipline**: T1 per-primitive units (hash, canonical round-trip, HMAC determinism, signature edges). T2 sealed-derive vs L4 mechanism. **Critical**: serializer must round-trip identically across all language bindings — single shared test suite across ecosystems.

---

## §3. `kernel/skin` (L1_SKIN §1-§6)

**Responsibilities**:
- Skin surface declaration; intake/output endpoints; forbidden surfaces.
- Envelope schema validation (integrity, freshness, size, payload_shape, envelope_digest HMAC).
- Operator handshake: `operator_signing_key_public` reception; non-deterministic `operator_token` via `sealed_derive`; `handshake_complete` with owner-birth-attestation; bidirectional validation.
- Single-operator: OS-accept-queue FIFO; `concurrent_connect_attempt` immune events.
- Network-egress enforcement: runtime-level (kernel netns / container filter / eBPF / userspace proxy — L4-picked).
- Federation egress freshness at emission (§3.1 + cross-cut `kernel/governance`).
- Breach detection: 10 categories per §6.

**Sub-modules**: `envelope` / `handshake` / `output_gate` / `egress_enforce`.

**Test discipline**: T1 envelope schema + handshake FSM + canonical-bytes round-trip. T2 full handshake with `kernel/shared` sealed-derive. T3 e2e with operator runtime. T4 adversarial: envelope tamper, replay, concurrent-connect, out-of-band egress.

---

## §4. `kernel/schema` (L1_SCHEMA §1-§4)

**Responsibilities**:
- SSoT representation + designation (format L4-chosen ∈ {YAML, TOML, JSON+JSONL, SQLite, custom}; this module provides abstraction).
- Merkle DAG storage: content-addressed; parent-hash chain; tip maintenance; enumerated-node export at CI co-sign moments.
- Spore-schema construction + validation (genesis + reproduction).
- Validation tier dispatch: tier-1 per cycle; tier-2 deep-cycle; tier-3 owner-triggered or L4 escalation.
- Recovery drill scheduling + sampled cold-tier drills (§2.4) + drill failure-rate baseline.

**Sub-modules**: `ssot` / `dag` / `spore` / `validation` / `recovery`.

**Test discipline**: T1 SSoT round-trip; DAG insertion + Merkle chain; spore validation. T2 recovery drill vs integration backup. T3 genesis-through-aging via simulated history.

---

## §5. `kernel/governance` (L1_GOVERNANCE §1-§6)

**Responsibilities**:
- Classifier: mechanical `classify(mutation_envelope) → {daily, contract_identity_level, untyped}` against dimension table (tier-1 SSoT field).
- Birth-period CI elevation (all parameter-tuning → CI during birth).
- Attestation envelope: canonical-bytes; operator_witness signature verify; enumerated DAG nodes since last co-sign; anchor-surface nonce binding; dual-clock expiry.
- Lifecycle FSM: genesis; dormancy transitions (with `kernel/continuity`); reproduction closure (with `kernel/schema/spore`); mortality three modes.
- Owner key rotation FSM (cooldown + veto); owner succession with anchor-surface liveness heartbeat.
- Federation discovery + peer attestation list + revocation list + aggregate reattestation.
- Failed P3 evolution rollback.

**Sub-modules**: `classifier` / `attestation` / `lifecycle` / `owner_keys` / `federation` / `rollback`.

**Test discipline**: T1 classifier truth-table; dimension-table mutation; attestation envelope (canonical-bytes round-trip with `kernel/shared` + `kernel/schema/spore`). T2 full attestation flow with mock anchor-client. T3 genesis → birth → steady → mortality.

---

## §6. `kernel/continuity` (L1_CONTINUITY §1-§5)

**Responsibilities**:
- Metabolic cycle engine: 5-step (tier-1 → gradient → delta-absorb → DAG-commit → skin-breach check); cadence dispatch; backlog detection.
- Dormancy FSM: alive ↔ dormant; throttled/paused; wake-on-attestation-arrival.
- Cold-resume: pre-handshake invariant checks (I1/I3/I4/I5/I8); witness emission; quarantine entry on failure.
- Delta atomicity: WAL commit; crash-recovery; partial-delta handling.
- Quarantine sub-state metabolism (intake-closed; federation-suspended).

**Sub-modules**: `cycle` / `dormancy` / `cold_resume` / `wal` / `quarantine`.

**Test discipline**: T1 cycle ordering; dormancy transitions; WAL atomicity (crash mid-write). T2 cold-resume after simulated invariant failure. T3 multi-cycle lifecycle with simulated crashes.

---

## §7. `kernel/tropism` (L1_TROPISM §1-§B10)

**Responsibilities**:
- Appetite-axis schema; per-axis `update_rule` runtime; threshold-emergence-rule (mortality-signal axis CI-protected per L1_HARD_RULES F7).
- Gradient configuration state + per-cycle gradient advance.
- Sporocarp emission: fruiting-trigger evaluation; type-tree dispatch; `causal_in_edges` proof; `template_version` annotation.
- Delta absorption into appetite axes.
- Self-hosting bootstrap: kernel-evolution-tension appetite for kernel-source repo.
- Birth-period vs steady-state mode switching (with `kernel/governance` for maturity attestation).

**Sub-modules**: `appetite` / `sporocarp` / `template_registry` (active-prefix + archived-tail) / `birth_period`.

**Test discipline**: T1 gradient advance; fruiting-trigger; causal_in_edges proof. T2 delta absorb → gradient → emission. T3 birth-period through to steady-state.

---

## §8. `kernel/trajectory` (L1_TRAJECTORY §1-§9 + L2_TRAJECTORY)

**Responsibilities**:
- Cluster_C runtime: substrate-resident; CI-protected; epoch-bounded queries.
- Trajectory query API: `causal_ancestors_and_descendants(neighborhood(t)) + cluster_C(.)`.
- Cold-start handling: empty-DAG → `cold_start_marker`.
- Thread_id orthogonal grouping (optional per substrate canon).
- Echo-chamber detection (substrate-keyed): delta-novelty weighting + threshold.
- Schema-evolution epoch boundary tracking.

**Sub-modules**: `cluster` / `query` / `epoch` / `echo_chamber`.

**Test discipline**: T1 cluster_C deterministic given `(DAG, cluster_C)`; epoch boundary respected. T2 trajectory query over multi-cycle DAG. T3 echo-chamber red-team via adversarial deltas.

---

## §9. `kernel/hard_rules` (L1_HARD_RULES §1-§5)

**Responsibilities**:
- CRITICAL detectors (C1-C20 spec + C30-C49 substrate-private per current catalog) — runtime observers reading other modules' emission streams; emit CRITICAL immune sporocarps + trigger auto-quarantine via `kernel/continuity/quarantine`.
- F-row watchdogs (F1-F25 per current catalog, incl. F18-F25 cascade for P10/P11/P14/§14/§15/§16) — observe CI fixed-point mutation attempts; emit `classifier_fixed_point_bypass` + similar.
- Birth-period CI elevation enforcement.
- Anchor-surface-resident state non-authorability check (§4).

**Sub-modules**: `critical_detectors` / `fixed_point_watchdog` / `anchor_surface_check`.

**Test discipline**: T1 per-detector units (synthetic breach → expected emission). T2 integration with other modules (real breach scenarios trigger correct detectors). T3 + T4 adversarial: full attack-scenario suite per C-row + F-row catalog.

---

## §10. `anchor_client` (L0 §9 + L1_GOVERNANCE §2)

**Responsibilities**:
- Canonical-bytes rendering: deterministic render for owner review (same `kernel/shared` serializer spec).
- Signature production: owner key in OS-sealed storage; signing at anchor-client; substrate never sees private key.
- Nonce generation + consumed-nonce log (anchor-surface owns; substrate cannot mint).
- Trusted wall-clock timestamps.
- Owner liveness heartbeat (periodic `liveness_heartbeat` signing).
- Aggregate-reattestation diff rendering (owner reviews diff, not full peer set).
- L0/L1 revision diff review (verbatim against prior commit hash).

**Sub-modules**: `renderer` / `sealed_key` / `nonce_log` / `heartbeat` / `ui` (web / CLI / hardware-token — L4-picked).

**Test discipline**: T1 rendering identical to substrate-side. T2 full attestation with mock substrate. T3 substrate-anchor e2e across attestation, rotation, federation re-attestation, mortality seal.

---

## §11. `operator_bindings/<host>` (L1_SKIN §4.1)

**Responsibilities**:
- Per-handshake keypair (`operator_signing_key_public`/`_private`); private in operator-runtime memory only.
- HMAC envelope_digest signing (operator_token from handshake response).
- Independent canonical-bytes derivation from deltas (shared serializer spec).
- Bootstrap-pinning: receives owner-provided `(substrate-ID, anchor-pubkey, owner-pubkey)` at first install.
- Anchor-surface query for current owner-pubkey-active-at-handshake (L2_TRUST_MODEL §3.1 step 5).
- Trajectory query API consumer.

**Sub-modules**: Each binding is a thin wrapper. First target L4-picked; candidates: `claude_code` (Node.js), `mcp_typescript` (MCP/TS), `mcp_python` (MCP/Python).

**Test discipline**: T1 keypair + signature; HMAC envelope_digest construction. T2 e2e handshake vs `kernel/skin`. T3 full substrate session including delta absorption + sporocarp observation.
