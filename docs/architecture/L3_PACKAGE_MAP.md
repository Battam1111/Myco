# L3 — Package Map (module-by-module specification)

> **Status**: DRAFT 1 (2026-05-13).
> **Layer**: L3.
> **Scope**: complete module-by-module map of substrate code. Each module = one row in the table below; full detail in §§2-10.

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
| `kernel/hard_rules` | L1_HARD_RULES | Immune detection: 20 CRITICAL + F-row watchdog | All other kernel/* (citation; runtime observation) | 1500-2500 |
| `anchor_client` | (L0 §9 + multiple L1) | Owner-side rendering + signing + nonce + heartbeat | `kernel/shared` (serializer spec) | 2000-3000 |
| `operator_bindings/<host>` | L1_SKIN §4.1 | Per-LLM-host operator runtime; per-handshake keypair; HMAC envelope | `kernel/shared` (serializer spec) | 500-1000 per binding |

**Substrate-kernel total: ~12000-19000 lines** estimated. **Plus anchor_client + operator bindings: +3000-5000.** Total v0.9 first-birth implementation: **~15000-24000 lines**.

(Estimates are language-agnostic ranges; specific languages with stronger abstraction may end lower; verbose languages may end higher.)

---

## §2. `kernel/shared` — foundation module

### §2.1 Responsibilities

- **Canonical-bytes serializer** (per L1_SCHEMA §3.1 spore-schema + L0 §9.3 canonical-bytes doctrine). Pure-declarative format spec; deterministic encoding from typed values to canonical bytes; loadable by every party (substrate, operator-runtime, anchor-client) for independent derivation.
- **Cryptographic primitives**: Merkle hash (content-addressed; tree construction; closure verification); signature verification (substrate's `owner_key_history` active prefix; anchor-surface nonces); HMAC (envelope_digest for delta intake).
- **Sealed-derive wrapper**: OS-level sealing API for substrate_secret. Wrapper around L4-picked mechanism (TPM / kernel keyring / HSM / hardware-secure-element). Substrate code uses sealed-derive without ever seeing substrate_secret in plaintext.
- **Active-prefix + archived-tail data structure** (per L1_GOVERNANCE §3.1): generic primitive used by `kernel/governance` for `owner_key_history`, `kernel/tropism` for `template_version_registry`, `kernel/governance` for federation aggregate-reattestation chain.

### §2.2 Public API surface (illustrative; L4 picks)

```
serialize_canonical(value: TypedValue) → CanonicalBytes
verify_signature(public_key, signature, canonical_bytes) → bool
hmac_sign(key, canonical_bytes) → HmacTag
merkle_hash(parent_hashes, content_canonical_bytes) → NodeHash
merkle_path(node_hash, ancestor_hash) → MerklePath  # for DAG closure proofs
sealed_derive(handshake_nonce, current_cycle, kernel_random) → OperatorToken
active_prefix_get(active_prefix, key) → Value | None
archived_tail_query(archived_tail, key, deep_cycle_token) → Value | None
```

### §2.3 Test discipline

Tier 1: unit tests per primitive (Merkle hash, canonical serialization round-trip, HMAC determinism, signature verification edge cases). Tier 2: sealed-derive integration with chosen L4 sealing mechanism. **Critical**: canonical-bytes serializer must round-trip identically across all language bindings (substrate-kernel, operator-binding, anchor-client) — a single canonical-bytes test suite shared across language ecosystems.

---

## §3. `kernel/skin` — boundary surface

### §3.1 Responsibilities

Per L1_SKIN §1-§6:

- Skin surface declaration: single declared boundary; intake endpoints; output endpoints; forbidden surfaces.
- Envelope schema validation: integrity check; freshness check; size check; payload_shape recognition; envelope_digest HMAC verification.
- Operator handshake protocol: `operator_signing_key_public` reception; non-deterministic `operator_token` generation (via `sealed_derive`); `handshake_complete` emission with owner-birth-attestation; bidirectional validation.
- Single-operator enforcement: race-handling via OS-accept-queue FIFO order; `concurrent_connect_attempt` immune events.
- Network-egress enforcement: runtime-level (kernel netns / container filter / eBPF / userspace proxy — L4-picked).
- Federation egress freshness check at emission (per L1_SKIN §3.1 + cross-cut to `kernel/governance`).
- Breach detection: 10 breach categories per L1_SKIN §6 table.

### §3.2 Internal sub-modules

- `kernel/skin/envelope` — envelope schema + integrity check.
- `kernel/skin/handshake` — handshake protocol + operator-token generation.
- `kernel/skin/output_gate` — output endpoint routing + canonical-bytes discipline for anchor-surface output.
- `kernel/skin/egress_enforce` — runtime network-egress detection.

### §3.3 Test discipline

Tier 1: envelope schema validation; handshake state machine; canonical-bytes-roundtrip for output. Tier 2: full handshake including dependency on `kernel/shared` sealed-derive. Tier 3: end-to-end including operator runtime emitting envelopes (after `operator_bindings/<first-target>` built).

Tier 4 adversarial: envelope tamper attempts; replay attacks; concurrent-connect attempts; out-of-band-egress attempts (require platform setup).

---

## §4. `kernel/schema` — substrate state representation

### §4.1 Responsibilities

Per L1_SCHEMA §1-§4:

- SSoT representation + designation. SSoT format L4-chosen within {YAML, TOML, JSON+JSONL, SQLite, custom}; this module provides the abstraction.
- Merkle DAG storage: content-addressed nodes; parent-hash chain; tip-hash maintenance; enumerated-node export at CI co-sign moments.
- Spore-schema construction + validation (for genesis + reproduction).
- Validation tier dispatch (tier-1 per cycle; tier-2 deep-cycle; tier-3 owner-triggered or via L4 escalation path).
- Recovery drill scheduling + sampled cold-tier drills (per L1_SCHEMA §2.4) + drill failure-rate baseline.

### §4.2 Internal sub-modules

- `kernel/schema/ssot` — SSoT designation + tier classification + designation migration two-phase commit.
- `kernel/schema/dag` — Merkle DAG storage + tip maintenance + enumerated-node export for CI events.
- `kernel/schema/spore` — spore-schema construction + validation (for genesis + reproduction).
- `kernel/schema/validation` — tier-1/tier-2 dispatch.
- `kernel/schema/recovery` — backup mechanism + drill engine + baseline tracking.

### §4.3 Test discipline

Tier 1: SSoT round-trip; DAG node insertion + Merkle chain consistency; spore-schema validation. Tier 2: recovery drill against integration backup. Tier 3: substrate genesis through aging via simulated history.

---

## §5. `kernel/governance` — classifier + lifecycle

### §5.1 Responsibilities

Per L1_GOVERNANCE §1-§6:

- Classifier function: mechanical `classify(mutation_envelope) → {daily, contract_identity_level, untyped}` against dimension table (tier-1 SSoT field).
- Birth-period CI elevation (during birth, all parameter-tuning elevates to CI).
- Attestation envelope construction: canonical-bytes; operator_witness signature verification (against operator_signing_key_public); enumerated DAG nodes since last co-sign; anchor-surface nonce binding; dual-clock expiry.
- Lifecycle FSM: genesis protocol; dormancy state transitions (with `kernel/continuity` cooperation); reproduction closure verification (with `kernel/schema/spore`); mortality three modes.
- Owner key rotation FSM with cooldown window + veto.
- Owner succession protocol with anchor-surface liveness heartbeat.
- Federation discovery + peer attestation list + revocation list + aggregate reattestation.
- Failed P3 evolution rollback procedure.

### §5.2 Internal sub-modules

- `kernel/governance/classifier` — dimension table + classify function.
- `kernel/governance/attestation` — attestation envelope construction + verification.
- `kernel/governance/lifecycle` — genesis / dormancy / reproduction / mortality state transitions.
- `kernel/governance/owner_keys` — key rotation + succession + cooldown.
- `kernel/governance/federation` — discovery + peer list + freshness + aggregate reattestation.
- `kernel/governance/rollback` — failed-evolution rollback.

### §5.3 Test discipline

Tier 1: classifier truth-table; dimension-table mutation tests; attestation envelope construction (canonical-bytes round-trip with `kernel/shared` + `kernel/schema/spore`). Tier 2: full attestation flow with mock anchor-client. Tier 3: substrate genesis → birth → steady state → mortality cycle.

---

## §6. `kernel/continuity` — operating regime engine

### §6.1 Responsibilities

Per L1_CONTINUITY §1-§5:

- Metabolic cycle engine: 5-step cycle structure (tier-1 → gradient → delta-absorb → DAG-commit → skin-breach check); cadence dispatch; backlog detection.
- Dormancy state machine: alive ↔ dormant; throttled / paused modes; wake-on-attestation-arrival.
- Cold-resume protocol: pre-handshake invariant checks (I1/I3/I4/I5/I8); witness emission; quarantine entry on failure.
- Delta atomicity: WAL-based commit; crash-recovery procedure; partial-delta handling.
- Quarantine sub-state metabolism (intake-closed; federation-suspended).

### §6.2 Internal sub-modules

- `kernel/continuity/cycle` — metabolic cycle engine.
- `kernel/continuity/dormancy` — dormancy state machine.
- `kernel/continuity/cold_resume` — pre-handshake checks + witness emission.
- `kernel/continuity/wal` — WAL-based delta atomicity.
- `kernel/continuity/quarantine` — quarantine sub-state.

### §6.3 Test discipline

Tier 1: cycle ordering; dormancy state transitions; WAL atomicity (crash mid-write). Tier 2: cold-resume after simulated invariant failure. Tier 3: multi-cycle substrate lifecycle with simulated crashes.

---

## §7. `kernel/tropism` — dispatch mechanism (positive form)

### §7.1 Responsibilities

Per L1_TROPISM §1-§B10:

- Appetite-axis schema implementation; `update_rule` runtime for each axis; threshold-emergence-rule application (per axis, with mortality-signal axis CI-protected per L1_HARD_RULES F7).
- Gradient configuration state + per-cycle gradient advance.
- Sporocarp emission: fruiting-trigger evaluation; sporocarp type tree dispatch; causal_in_edges proof construction; template_version annotation.
- Delta absorption into appetite axes.
- Self-hosting bootstrap: kernel-evolution-tension appetite for the kernel-source repository.
- Birth-period vs steady-state mode switching (with `kernel/governance` cooperation for maturity attestation).

### §7.2 Internal sub-modules

- `kernel/tropism/appetite` — appetite-axis runtime + gradient state.
- `kernel/tropism/sporocarp` — sporocarp construction + causal-proof + emission.
- `kernel/tropism/template_registry` — template_version_registry (uses `kernel/shared` active-prefix + archived-tail primitive).
- `kernel/tropism/birth_period` — birth-period state + maturity attestation.

### §7.3 Test discipline

Tier 1: gradient advance per-cycle; fruiting-trigger evaluation; causal_in_edges proof construction. Tier 2: full delta absorption → gradient → sporocarp emission flow. Tier 3: birth-period progression through to steady-state.

---

## §8. `kernel/trajectory` — intent derivation

### §8.1 Responsibilities

Per L1_TRAJECTORY §1-§9 + L2_TRAJECTORY:

- Cluster_C runtime: substrate-resident; CI-protected; epoch-bounded queries.
- Trajectory query API: causal_ancestors_and_descendants(neighborhood(t)) + cluster_C(.).
- Cold-start handling: empty-DAG cases return `cold_start_marker`.
- Thread_id orthogonal grouping (optional per substrate canon).
- Echo-chamber detection (substrate-keyed, not operator-keyed): delta-novelty weighting + threshold detection.
- Schema-evolution epoch boundary tracking.

### §8.2 Internal sub-modules

- `kernel/trajectory/cluster` — cluster_C dispatch + algorithm runtime.
- `kernel/trajectory/query` — neighborhood + trajectory query API.
- `kernel/trajectory/epoch` — epoch-boundary tracking + within-epoch query.
- `kernel/trajectory/echo_chamber` — delta-novelty weighting + detection.

### §8.3 Test discipline

Tier 1: cluster_C produces deterministic output given same `(DAG, cluster_C)`; epoch boundary respected. Tier 2: trajectory query over multi-cycle DAG. Tier 3: echo-chamber attack scenarios (red-team via adversarial deltas).

---

## §9. `kernel/hard_rules` — immune detection layer

### §9.1 Responsibilities

Per L1_HARD_RULES §1-§5:

- **20 CRITICAL detectors** (C1-C20 from L1_HARD_RULES §1) — runtime observers reading from other modules' emission streams; emit CRITICAL immune sporocarps + trigger auto-quarantine via `kernel/continuity/quarantine`.
- **F-row watchdogs** (F1-F17 from L1_HARD_RULES §2) — observe CI fixed-point mutation attempts; emit `classifier_fixed_point_bypass` + similar.
- **Birth-period CI elevation enforcement** — verifies the birth-period flag is honored.
- **Anchor-surface-resident state non-authorability check** — verifies the substrate doesn't author the anchor-surface-resident fields enumerated in L1_HARD_RULES §4.

### §9.2 Internal sub-modules

- `kernel/hard_rules/critical_detectors` — 20 C-row detectors (each one a focused observer pattern).
- `kernel/hard_rules/fixed_point_watchdog` — 17 F-row watchdogs.
- `kernel/hard_rules/anchor_surface_check` — non-authorability verifier.

### §9.3 Test discipline

Tier 1: per-detector unit tests (synthetic breach inputs → expected immune emission). Tier 2: integration with other modules (real breach scenarios trigger correct detectors). Tier 3 + Tier 4 adversarial: full attack-scenario suite per L1_HARD_RULES C1-C20.

---

## §10. `anchor_client` — owner-side tool

### §10.1 Responsibilities

Per L0 §9 + L1_GOVERNANCE §2:

- Canonical-bytes rendering: deterministic render of canonical bytes for owner review (using the same `kernel/shared` serializer spec).
- Signature production: owner key in OS-sealed storage; signing happens at the anchor-client; substrate never sees the private key.
- Nonce generation + consumed-nonce log (anchor-surface owns; substrate cannot mint).
- Trusted wall-clock timestamps.
- Owner liveness heartbeat (periodic signing of `liveness_heartbeat` events).
- Aggregate-reattestation diff rendering (owner reviews diff, not full peer set).
- L0/L1 revision diff review (verbatim diff against prior commit hash).

### §10.2 Internal sub-modules

- `anchor_client/renderer` — canonical-bytes rendering.
- `anchor_client/sealed_key` — OS-sealed owner-key access.
- `anchor_client/nonce_log` — nonce generation + consumed-nonce tracking.
- `anchor_client/heartbeat` — periodic liveness signing.
- `anchor_client/ui` — owner-facing review UI (web / CLI / hardware-token UI — L4-picked).

### §10.3 Test discipline

Tier 1: canonical-bytes rendering is identical to substrate-side serialization. Tier 2: full attestation flow with mock substrate. Tier 3: substrate-anchor end-to-end across attestation, rotation, federation re-attestation, mortality seal.

---

## §11. `operator_bindings/<host>` — per-LLM-host runtime

### §11.1 Responsibilities

Per L1_SKIN §4.1:

- Per-handshake keypair generation (`operator_signing_key_public` / `_private`); private key in operator-runtime memory only.
- HMAC envelope_digest signing (using operator_token from handshake response).
- Independent canonical-bytes derivation from deltas (using shared serializer spec).
- Bootstrap-pinning: receives owner-provided `(substrate-ID, anchor-surface-endpoint-pubkey, owner-pubkey)` at first install.
- Anchor-surface query for current owner-pubkey-active-at-handshake (per L2_TRUST_MODEL §3.1 step 5).
- Trajectory query API consumer (operator reads substrate's trajectory view).

### §11.2 Per-binding sub-modules

Each `operator_bindings/<host>` is a thin wrapper. The first target is L4-picked; common candidates: claude_code (Node.js), mcp_typescript (MCP/TS), mcp_python (MCP/Python).

### §11.3 Test discipline

Tier 1: keypair generation + signature; HMAC envelope_digest construction. Tier 2: end-to-end handshake against `kernel/skin`. Tier 3: full substrate session including delta absorption + sporocarp observation.

---

## §12. Build dependency graph (visualized)

```
                                                        ┌──────────┐
                                                        │  shared  │
                                                        └────┬─────┘
                                                             │
                              ┌──────────────────────────────┼──────────────────────────────┐
                              │                              │                              │
                              ▼                              ▼                              ▼
                       ┌────────────┐                 ┌────────────┐                 ┌──────────────┐
                       │    skin    │                 │   schema   │                 │ anchor_client│
                       └─────┬──────┘                 └─────┬──────┘                 └──────────────┘
                             │                              │
                             ├──────────────┬───────────────┤
                             ▼              ▼               ▼
                      ┌─────────────┐ ┌────────────┐ ┌──────────────┐
                      │ governance  │ │ continuity │ │ operator_bd  │
                      └──────┬──────┘ └──────┬─────┘ └──────────────┘
                             │               │
                             │               ├─────────────────┐
                             │               ▼                 │
                             │        ┌─────────────┐          │
                             │        │   tropism   │          │
                             │        └──────┬──────┘          │
                             │               │                 │
                             │               ▼                 │
                             │        ┌─────────────┐          │
                             │        │ trajectory  │          │
                             │        └─────────────┘          │
                             │                                 │
                             └──────────────┬──────────────────┘
                                            ▼
                                    ┌────────────────┐
                                    │   hard_rules   │ (citation-only; observes all)
                                    └────────────────┘
```

---

## §13. L4 implementation entry point

For an L4 implementer beginning work, the recommended starting commit set:

1. Clone v0.9-genesis branch.
2. Read L0_VISION.md (full).
3. Read L1_OUTLINE.md + L1_HARD_RULES.md (cross-cuts index).
4. Read L3_OUTLINE.md + L3_PACKAGE_MAP.md (this file).
5. Choose L4 implementation language(s) for `kernel/shared` + `kernel/skin` + `kernel/schema`.
6. Begin Milestone 1: implement `kernel/shared` per §2 above.

Pass-1 critic on first L4 code: same 6-lens 100%-confidence loop methodology, applied to actual code. The doctrine layer's pass-1 → pass-2 → pass-3 → pass-4 convergence pattern applies to code as well — expect first code submissions to surface ~30-50 findings; iterate.
