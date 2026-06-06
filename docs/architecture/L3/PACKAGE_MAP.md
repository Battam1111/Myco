> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4), see `docs/architecture/OUTLINE.md` §3 for details.

---

# L3: Package Map (module-by-module specification)

---

## §1. Module index

The map below is the **complete** module territory, grouped by layer in build-order
sense (foundation first; each layer may depend only on layers above it). The
kernel-mechanism layer (a) is 1:1 with the 7 L1 docs (+1 `shared` foundation); the
remaining layers (b)-(e) are the runtime, binding, and test apparatus that
make the mechanisms a *living* substrate. *(Keyless v3.1.5: the prior anchor-custody
layer (`anchor/host` + `anchor/client`) is removed; both the Rust
`anchor-surface-host` crate and the TS `@myco/anchor-client` package were deleted with
the owner-key surface.)* Language is L4-chosen per module
(`Rust` / `Python` / `TypeScript`); see `Cargo.toml` workspace header for the
realized split.

**(a) Kernel-mechanism layer**: doctrine mechanisms, 1:1 with the 7 L1 docs + shared foundation.

| Module | Layer / lang | Responsibility | Dependencies |
|---|---|---|---|
| `kernel/shared` | mechanism / Rust | **Foundation.** Canonical-bytes serializer + crypto (Merkle/HMAC/sig) + **safe** sealed-derive wrapper + sealing-* feature flags + active-prefix primitive. `#![forbid(unsafe_code)]` (pure-safe). | (none) |
| `kernel/skin` | mechanism / Rust | L1/SKIN: envelope + handshake + single-operator + egress + breach categories. | `kernel/shared` |
| `kernel/schema` | mechanism / Rust | L1/SCHEMA: SSoT + Merkle DAG + spore-schema + validation tiers + recovery. | `kernel/shared` |
| `kernel/continuity` | mechanism / Rust | L1/CONTINUITY: metabolic cycle + dormancy + cold-resume + WAL + quarantine. | `kernel/shared` |
| `kernel/governance` | mechanism / Python | L1/GOVERNANCE: classifier + CI-approval envelope + lifecycle FSM + cultivation succession + federation (keyless v3.1.5; owner-key rotation retired). | `kernel/bridge/python` |
| `kernel/tropism` | mechanism / Python | L1/TROPISM: appetite gradient + sporocarp emission + fruiting + birth-period. | `kernel/bridge/python` |
| `kernel/trajectory` | mechanism / Python | L1/TRAJECTORY: cluster_C + trajectory queries + thread_id + echo-chamber + epoch. | `kernel/bridge/python` |
| `kernel/hard_rules` | mechanism / Python | L1/HARD_RULES: immune detection C1-C20 + C30-C56 + F1-F26 watchdogs. | `kernel/bridge/python` |

**(b) Cross-language bridge**: the M5 IPC seam that lets the Rust runtime drive Python workers.

| Module | Layer / lang | Responsibility | Dependencies |
|---|---|---|---|
| `kernel/bridge/rust` | bridge / Rust | M5 client + framing + protocol + tropism_bridge: length-prefixed canonical-bytes + HMAC over stdio; spawns + drives a Python worker. | `kernel/shared`, `kernel/continuity` |
| `kernel/bridge/python` | bridge / Python | M5 server half: daemon + dispatcher + framing + protocol + canonical-bytes decode; the worker entrypoint the Python mechanisms run behind. | `kernel/shared` (serializer spec) |

**(c) Runtime-orchestration**: the substrate process itself.

| Module | Layer / lang | Responsibility | Dependencies |
|---|---|---|---|
| `substrate` | runtime / Rust | **The M6 orchestrator daemon binary.** Server for the operator; client of the Python kernel worker via the M5 bridge; owns ServerState + persistence + events + federation + lifecycle/integrity/attestation request handlers + OS-sealing FFI. See §12. | `kernel/shared`, `kernel/bridge/rust`, `kernel/continuity`, `kernel/schema` |

**(d) Operator-binding**: the agent-facing MCP interface (out-of-band per host).

| Module | Layer / lang | Responsibility | Dependencies |
|---|---|---|---|
| `operators/<host>` | binding / TypeScript | Per-LLM-host runtime the agent drives. `operators/claude` = `@myco/operators-claude`: MCP server + substrate-client + per-handshake operator keypair + HMAC operator-session auth (keyless v3.1.5; the prior `anchor-surface-client` sub-module is removed with the anchor surface). | `kernel/shared` serializer spec (re-derived in TS); spawns `substrate` |

**(e) Test suite**: cross-language canonical-bytes parity (the seam-correctness guarantee).

| Module | Layer / lang | Responsibility | Dependencies |
|---|---|---|---|
| `test_vectors/` | test / Rust + JSON | `*.json` contracts (`canonical_bytes_v1.json`, `crypto_v1.json`) + `rs/` (`myco-test-vectors-rs`) parity harness. Every language's serializer + crypto must round-trip these identical bytes. | `kernel/shared` (Rust side); contracts consumed by Python + TS sides |

Per-crate / per-package T1 unit tests live **with each module** (`<module>/tests/`),
not in a single top-level `tests/`; cross-language parity lives in `test_vectors/`
(see OUTLINE §6). Line-estimate ranges + total sizing + build dependency graph:
`diagrams/build_dependency.txt`.

---

## §2. `kernel/shared`

L1/SCHEMA §3.1 + L0/cards/AS_anchor_surface.md §3 (the AS card survives in the sealed L0 as doctrine history) + L1/GOVERNANCE §3.1. Canonical-bytes serializer (deterministic; loadable by every party); crypto (Merkle hash content-addressed; Ed25519 signature verify against the substrate's OWN F24 active-prefix pubkey for snapshot.cb + FED_HELLO; HMAC `envelope_digest`; keyless v3.1.5: no anchor nonces); sealed-derive wrapper (substrate_secret over L4 TPM/keyring/HSM/secure-element); active-prefix + archived-tail primitive. **T1** per-primitive; **T2** sealed-derive vs L4. Critical: serializer round-trips identically across language bindings.

---

## §3. `kernel/skin` (L1/SKIN §1-§6)

Skin surface + intake/output + forbidden surfaces; envelope validation (integrity/freshness/size/payload_shape/HMAC); operator handshake (`operator_signing_key_public`; non-deterministic `operator_token` via `sealed_derive`; bidirectional); single-operator (OS-accept-queue FIFO; `concurrent_connect_attempt`); network-egress enforcement (kernel netns / container / eBPF / userspace proxy; L4); federation egress freshness; §6 ten breach categories. Sub-modules: `envelope` / `handshake` / `output_gate` / `egress_enforce`. **T1** envelope+handshake FSM; **T2** sealed-derive; **T3** e2e operator; **T4** adversarial.

---

## §4. `kernel/schema` (L1/SCHEMA §1-§4)

SSoT representation + designation (L4 ∈ {YAML, TOML, JSON+JSONL, SQLite, custom}); Merkle DAG (content-addressed; parent-hash chain; tip; enumerated-node export at CI approval at the live gate; keyless v3.1.5, was "CI co-sign"); spore-schema construction + validation; validation tier dispatch (tier-1 per cycle; tier-2 deep-cycle; tier-3 cultivator-triggered at the live CI gate; keyless v3.1.5); recovery drill + sampled cold-tier + failure-rate baseline. Sub-modules: `ssot` / `dag` / `spore` / `validation` / `recovery`. **T1** SSoT+DAG+Merkle+spore; **T2** drill vs backup; **T3** genesis-through-aging.

---

## §5. `kernel/governance` (L1/GOVERNANCE §1-§6)

Classifier (`classify(mutation_envelope) → {daily, CI, untyped}` against dimension-table tier-1 SSoT); birth-period CI elevation; CI-approval envelope (canonical-bytes; operator_witness verify; enumerated DAG nodes since last approval; substrate-clock expiry; keyless v3.1.5, no nonce, no owner signature, no anchor wall-clock); lifecycle FSM (genesis; dormancy w/ continuity; reproduction w/ schema/spore; mortality three modes); cultivation succession w/ C46 catechumenate floor (keyless v3.1.5: owner-key rotation FSM + the anchor liveness-heartbeat are retired, GOVERNANCE §3); federation discovery + peer attestation + revocation + aggregate reattestation; failed P3 rollback. Sub-modules: `classifier` / `attestation` / `lifecycle` / `succession` / `federation` / `rollback`. **T1** truth-table+round-trip; **T2** CI-approval re-derivation at the gate; **T3** genesis → birth → steady → mortality.

---

## §6. `kernel/continuity` (L1/CONTINUITY §1-§5)

Metabolic cycle (5-step: tier-1 → gradient → delta-absorb → DAG-commit → skin-breach; cadence; backlog); dormancy FSM (alive ↔ dormant; throttled/paused; wake-on-attestation); cold-resume (pre-handshake invariants; witnesses; quarantine on failure); delta atomicity (WAL; crash-recovery; partial-delta); quarantine sub-state metabolism. Sub-modules: `cycle` / `dormancy` / `cold_resume` / `wal` / `quarantine`. **T1** cycle ordering+dormancy+WAL atomicity; **T2** cold-resume after simulated failure; **T3** multi-cycle w/ simulated crashes.

---

## §7. `kernel/tropism` (L1/TROPISM §1-§B10)

Appetite-axis schema + per-axis `update_rule` + threshold-emergence-rule (mortality-signal CI-protected per F7); gradient configuration + per-cycle advance; sporocarp emission (fruiting; type-tree; `causal_in_edges`; `template_version`); delta absorption; self-hosting bootstrap (kernel-evolution-tension appetite); birth-period vs steady-state switching. Sub-modules: `appetite` / `sporocarp` / `template_registry` / `birth_period`. **T1** gradient+fruiting+causal_in_edges; **T2** delta → gradient → emission; **T3** birth → steady.

---

## §8. `kernel/trajectory` (L1/TRAJECTORY §1-§9)

Cluster_C runtime (substrate-resident; CI-protected; epoch-bounded); query API (`causal_ancestors_and_descendants(neighborhood(t)) + cluster_C(.)`); cold-start (empty-DAG → `cold_start_marker`); thread_id grouping; echo-chamber detection (substrate-keyed delta-novelty + threshold); schema-evolution epoch boundary. Sub-modules: `cluster` / `query` / `epoch` / `echo_chamber`. **T1** cluster_C deterministic + epoch respected; **T2** trajectory over multi-cycle DAG; **T3** echo-chamber red-team.

---

## §9. `kernel/hard_rules` (L1/HARD_RULES §1-§5)

CRITICAL detectors (C1-C20 + C30-C56 substrate-private; keyless v3.1.5: C50/C70 + the duress-keypair detectors F23/C50 retired with the anchor surface, see HARD_RULES §2-§4): runtime observers reading other modules' emission streams; emit CRITICAL immune + auto-quarantine via `kernel/continuity/quarantine`; F-row watchdogs (F1-F26 incl. F18-F26 cascade) that observe CI fixed-point mutation; emit `classifier_fixed_point_bypass` etc.; birth-period CI elevation enforcement; substrate-self-authorship refusal check (a substrate-side forge of a CI-class fixed-point MUST be `untyped`/C14 + rejected at the live CI gate; keyless v3.1.5, was the anchor-surface non-authorability check; HARD_RULES §4). Sub-modules: `critical_detectors` / `fixed_point_watchdog` / `ci_gate_authorship`. **T1** per-detector synthetic breach; **T2** integration real-breach; **T3+T4** adversarial.

---

## §10. `anchor-client`: RETIRED v3.1.5 (section number reserved)

**DELETED with the owner-key surface (v3.1.5 keyless teardown).** The `@myco/anchor-client`
TypeScript package no longer exists. It formerly held the owner-side render + owner-signature
production (owner key in OS-sealed storage) + nonce generation + consumed-nonce log + trusted
wall-clock + owner liveness heartbeat + aggregate-reattestation diff rendering + L0/L1 revision
diff review. **None of these exist in keyless mode.** What replaces the trust function, keyless:
the cultivator re-derives the canonical-bytes and approves at the live human-in-the-loop CI gate
(GOVERNANCE §2.2); doctrine-revision integrity is the BLAKE3-sealed bundle (PROVENANCE §6); there
is no owner key, no nonce, no trusted wall-clock (the substrate uses its own clock, acknowledged-debt
per GOVERNANCE §3.2.B). The section number is reserved so §§11-15 + external cross-refs stay stable.

---

## §11. `operators/<host>` (L1/SKIN §4.1)

Per-handshake `operator_signing_key_public/_private` (private in operator-runtime memory only); HMAC envelope_digest signing (operator_token from handshake); independent canonical-bytes derivation; bootstrap-pinning of `substrate-ID` at first install (keyless v3.1.5: the prior owner-provided `(anchor-pubkey, owner-pubkey)` pins + the anchor query for the active owner-pubkey are removed with the owner-key surface); trajectory query API consumer. The bonded pilot-agent is the runtime authority via the operator-session HMAC (by design; runtime has no human daemon-gate). Realized binding: `operators/claude` (`@myco/operators-claude`, TypeScript), sub-modules `mcp_server` / `substrate_client` / `canonical/` (canonical-bytes + crypto + renderer) / `protocol/` / `cli` + `ceremonies/` (the prior `anchor_surface_client` sub-module is deleted). Other host bindings are additive (MCP/TS, MCP/Python) reusing the same serializer spec. **T1** keypair+signature+HMAC; **T2** e2e handshake vs `kernel/skin`; **T3** full session.

---

## §12. `substrate` (runtime orchestrator: Rust daemon binary)

**The M6 orchestrator** and the largest single module. Build-order: depends on the
kernel-mechanism + bridge layers; sits *below* `operators/<host>` (the operator
spawns it). *(Keyless v3.1.5: there is no `anchor/host` to sit beside and no
owner-signature dataflow; CI-class mutations are emitted as canonical-bytes +
Merkle witnesses for the cultivator to re-derive and approve at the live CI gate,
GOVERNANCE §2.2.)* The dataflow is:

```
operators/claude (TS) --[M5 stdio]--> substrate (THIS, Rust) --[M5 stdio]--> python kernel worker
```

The TS→Rust direction reuses the M5 `kernel/bridge` message types verbatim; the
Rust→Python direction spawns + drives the Python `kernel/tropism` worker through
`myco_kernel_bridge::client::BridgeClient`.

**Kernel dependencies** (acyclic, kernel-inward; the *only* crates substrate imports):
`myco-kernel-shared`, `myco-kernel-bridge` (rust), `myco-kernel-continuity`,
`myco-kernel-schema`. No kernel crate depends on substrate.

**Module domains** (`substrate/src/`):

- **`server/`**: request dispatch + autonomous (self-driven) cycle loop; owns `ServerState`, the live in-memory runtime state every request handler operates on.
- **`persistence/`**: durable state: `dag_io` (DAG read/write) / `manifest` / `snapshot` / `nonce_log` / `signing_key` (the substrate's OWN F24 keypair, OS-sealed; keyless v3.1.5, NOT an owner key); plus top-level `persistence_runtime` / `persistence_health` / `prune` / `backup`.
- **`events/`**: the event-sourcing log: `core` + per-domain event kinds (`attestation` / `consensus` / `cultivation` / `federation` / `telos` / `char07` / `internal_mortality` / `schema_migration` / `backup_encryption` / `compression`). *(Keyless v3.1.5: the duress-event kind is retired with the duress keypair, GOVERNANCE §15 F23.)*
- **`federation/`**: peer attestation seam: `handlers` / `protocol` / `transport`.
- **lifecycle handlers**: `lifecycle.rs` / `integrity.rs` / `cultivation.rs` / `reproduction.rs` / `consensus.rs`: the genesis → steady → dormancy → reproduction → mortality FSM as **runtime request handlers**.
- **OS-sealing**: `sealing.rs` (sealing dispatch) / `dpapi.rs` (Windows DPAPI FFI backend) / `at_rest_seal.rs`: seal `substrate_signing_key` at rest (L1/SKIN §4.2 + C4).
- **observatory**: `observatory.rs`: self-perception / introspection surface.
- **attestation + runtime support**: `attestation.rs` (keyless CI-approval handler: re-derives the mutation hash + verifies the change matches what was approved at the live CI gate; keyless v3.1.5, no owner-signature verification) + `handshake` / `ingest` / `dag_query` / `derived_state` / `wall_clock` (the substrate's own clock; keyless, acknowledged-debt) / `python_call_health`.

**Boundary fact (the subtle part; do not "helpfully" relocate these).**
`substrate`'s `attestation.rs` / `integrity.rs` / `lifecycle.rs` are **runtime request
handlers**, not kernel libraries: each takes `&ServerState` / `&mut ServerState` and
imports from `crate::server` (e.g. `save_dag_state`, `emit_immune_sporocarp`). They
are *correctly substrate-resident*; the crypto **mechanisms** they invoke already
live in `kernel/shared`; what lives here is the request-handling *glue* coupled to
live runtime state. Moving a handler into a kernel crate would force that crate to
import `substrate::server::ServerState`, creating a **kernel → substrate dependency
cycle** (forbidden; L4 cyclic dependency ⇒ L3 module-boundary revision, OUTLINE §3).

Symmetrically, the **unsafe FFI** is deliberately isolated *here*: `substrate` runs
`#![deny(unsafe_code)]` with a single audited `#[allow(unsafe_code)]` on the `dpapi`
module (Windows `CryptProtectData`/`CryptUnprotectData`, gated `cfg(windows)`). This
keeps `kernel/shared` at `#![forbid(unsafe_code)]`: a **pure-safe foundation**.
`kernel/shared` holds only the *safe* `sealed_derive` wrapper + the `sealing-{tpm,
keyring,hsm,secure-enclave}` feature flags for future OS-sealing backends; the unsafe
backend implementation lives in substrate. **Net boundary: kernel = mechanisms + safe
wrappers; substrate = runtime handlers + isolated unsafe FFI.**

**T1** per-handler synthetic state; **T2** persistence + events + bridge integration; **T3** substrate e2e (genesis → steady → mortality, L0 invariants, C-row breach); **T4** adversarial.

---

## §13. `kernel/bridge` (M5 cross-language IPC: Rust + Python halves)

The **M5 protocol seam** that makes the multi-language split possible: a
length-prefixed canonical-bytes framing with an HMAC integrity tag, spoken over stdio
between a Rust parent and a Python worker (same wire format the operator uses to reach
substrate; see §12). Two halves, built independently once `kernel/shared` is stable:

- **`kernel/bridge/rust`** (`myco-kernel-bridge`): `client` (spawn + request/response) / `framing` (length-prefix + HMAC) / `protocol` (message types) / `tropism_bridge` (typed gradient operations). Depends on `kernel/shared` (serializer + HMAC) + `kernel/continuity`.
- **`kernel/bridge/python`** (`myco_kernel_bridge`): `daemon` (worker entrypoint) / `dispatcher` / `framing` / `protocol` / canonical-bytes decode. The server half the Python mechanism modules (`governance` / `tropism` / `trajectory` / `hard_rules`) run behind; depends on the `kernel/shared` serializer spec re-implemented in Python.

The contract is byte-identical canonical-bytes on both sides, enforced by §15
(`test_vectors/`). **T1** framing round-trip + HMAC reject + protocol encode/decode (each half); **T2** daemon smoke + dispatcher + migration (Python) against a Rust client; **T3** exercised via substrate e2e.

---

## §14. `anchor/host`: RETIRED v3.1.5 (section number reserved)

**DELETED with the owner-key surface (v3.1.5 keyless teardown).** The
`anchor-surface-host` Rust binary (Cargo workspace member) is removed from the
workspace; the `anchor/` directory no longer exists. It formerly held the owner
Ed25519 signing key outside both the operator and substrate processes (the realized
server-side counterpart of the spec-level `anchor-client`, §10), producing owner
signatures neither process ever saw the private key for. **None of this exists in
keyless mode**: there is no owner key to custody. CI approval is now exercised by the
cultivator at the live human-in-the-loop CI gate (GOVERNANCE §2); the only Ed25519 key
that survives is the substrate's OWN keypair (F24), used for `snapshot.cb` + the
federation FED_HELLO handshake (L2/FEDERATION §10), held in `substrate`'s
`persistence/signing_key`, not a custody daemon. The section number is reserved so §15
+ external cross-refs stay stable.

---

## §15. `test_vectors/` (cross-language canonical-bytes parity suite)

The **seam-correctness guarantee**: the canonical-bytes serializer + crypto primitives
must produce *byte-identical* output across all three language ecosystems (Rust
substrate/kernel, Python workers, TypeScript operator). Lives at repo top level
(not inside any one module) because it is a *contract shared by all*:

- **`canonical_bytes_v1.json` + `crypto_v1.json`**: language-neutral vector contracts: input → expected canonical bytes / digest.
- **`test_vectors/rs`** (`myco-test-vectors-rs`, Cargo member): `canonical_bytes_parity` + `crypto_parity` harness asserting the Rust serializer matches the JSON contracts; the Python + TS sides load the same `*.json` and assert the same bytes.

Adding an input type to the serializer ⇒ add a vector here ⇒ all three languages must
match or CI fails. This is what lets §13's "byte-identical on both sides" claim be a
*tested* invariant rather than an aspiration. **T1/T2** parity assertions per language; CI co-runs all three.
