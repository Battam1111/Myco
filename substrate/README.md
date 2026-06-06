# `substrate/`, the Myco runtime daemon (L4 M6)

`myco-substrate` is the **runtime daemon** that brings a Myco organism to life: the
binary an operator runtime (e.g. [`operators/claude`](../operators/claude/)) spawns,
which then **orchestrates `operators` ↔ `kernel`**. It is simultaneously a *server*
for the operator (reads request frames from stdin, writes response frames to stdout)
and a *client* of the Python kernel worker, **spawning `python -m myco_kernel_bridge`
via the M5 bridge** (length-prefixed canonical-bytes + HMAC over stdio). It depends
at compile time on the Rust kernel crates `kernel/{shared, bridge/rust, continuity,
schema}`. Myco is **keyless**: there is no owner key and no anchor surface (both
were removed in v0.9). The substrate-ID is self-derived (P01c); the trust root is
the live human at the CI gate (the git/PR review on the doctrine repo, enforced by
the BLAKE3 drift-gate in CI), the substrate's own tamper-evident causal DAG (P06),
and the BLAKE3-sealed doctrine bundle. The substrate's OWN Ed25519 keypair (F24:
`snapshot.cb` + federation `FED_HELLO`) is kept, that is the substrate's own
crypto, not an owner key.

> **Doctrine anchors:** [`L3/PACKAGE_MAP.md`](../docs/architecture/L3/PACKAGE_MAP.md)
> §11 (operators/host, the substrate side bindings talk to) · [`L1/SKIN`](../docs/architecture/L1/SKIN.md)
> §4.1 (handshake + envelope) · [`L1/CONTINUITY`](../docs/architecture/L1/CONTINUITY.md)
> §1.1 (`advance` triggers the metabolic cycle).

---

## Module map (`src/`, grouped by domain)

`src/` is a flat module list with four submodule directories (`server/`,
`persistence/`, `events/`, `federation/`). Crate root and CLI entry are
[`lib.rs`](src/lib.rs) and [`main.rs`](src/main.rs).

| Domain | Modules | Role | L1 ref |
|---|---|---|---|
| **SERVER** | `server/` (`dispatch`, `autonomous`), `handshake` | Request loop + dispatch; operator handshake (M6 = M5 session_secret + HMAC). | SKIN §4.1 |
| **PERSISTENCE** | `persistence/` (`dag_io`, `manifest`, `snapshot`, `signing_key`), `persistence_health`, `persistence_runtime`, `at_rest_seal`, `backup`, `dpapi` *(win)*, `sealing` *(placeholder)* | On-disk DAG/state; at-rest sealing of the substrate's own (F24) secret; backup. (v0.9 keyless: the `nonce_log` + `operator_identity` modules were removed.) | SCHEMA · SKIN §4.2 |
| **METABOLISM / LIFECYCLE** | `lifecycle`, `cultivation`, `reproduction`, `ingest` | Genesis → steady → dormancy → mortality FSM; cultivation sessions; reproduction (spore); delta ingestion. | CONTINUITY · GOVERNANCE |
| **DAG / STATE** | `dag_query`, `derived_state`, `prune` | Query the Merkle DAG; recompute derived state from the live DAG; prune/compact. | SCHEMA |
| **GOVERNANCE-RUNTIME** | `attestation`, `integrity`, `consensus` | Runtime handlers for attestation envelopes, integrity checks, and consensus floor. | GOVERNANCE · L2/FEDERATION |
| **FEDERATION** | `federation/` (`protocol`, `transport`, `handlers`) | Peer discovery + wrapped-event exchange + mutual auth. | L2/FEDERATION |
| **EVENTS** | `events/` (`core`, `attestation`, `cultivation`, `federation`, `consensus`, `backup_encryption`, `compression`, `schema_migration`, `telos`, `char07`, `duress`, `internal_mortality`) | Typed event records the metabolic cycle and handlers emit. | CONTINUITY · GOVERNANCE |
| **OBSERVABILITY** | `observatory`, `python_call_health`, `persistence_health` | Self-perception surfaces + health of the Python bridge / persistence layer. | L2/OBSERVABILITY |
| **TIME** | `wall_clock` | Trusted wall-clock source for dual-clock attestation expiry. | GOVERNANCE |

Full module-by-module spec + dependency graph: [`L3/PACKAGE_MAP.md`](../docs/architecture/L3/PACKAGE_MAP.md).

---

## Boundary notes (why it's shaped this way)

- **Runtime handlers vs. mechanisms.** `attestation`, `integrity`, `lifecycle` (and
  peers) are *runtime handlers*, coupled to `ServerState` by design. The reusable
  **crypto mechanisms** they call live in [`kernel/shared`](../kernel/shared/) (hashing,
  canonical-bytes serializer, signature verify, HMAC, sealed-derive), not here.
- **Crate dependencies.** Compile-time deps are exactly `myco-kernel-{shared, bridge/rust,
  continuity, schema}` (see [`Cargo.toml`](Cargo.toml)). The Python kernel workers
  (`governance` / `tropism` / `trajectory` / `hard_rules`) are reached at **runtime over
  the M5 bridge**, not linked.
- **`unsafe` is fenced to OS-sealing FFI.** The crate is `#![deny(unsafe_code)]`; the only
  override is the Windows-gated `dpapi` adapter (`CryptProtectData`), kept isolated so
  `kernel/shared` stays zero-`unsafe`. Audit the whole `unsafe` surface with
  `git grep "allow(unsafe_code)"` in this crate. `sealing` is a doc-placeholder for the
  cross-platform sealing backends (Linux keyring / macOS Secure Enclave) scheduled to
  follow.

---

## Where the cycle lives

An `advance` request from the operator triggers a full
`CycleEngine` cycle (`myco_kernel_continuity::cycle`): the gradient-advance step is
forwarded to the Python `kernel/tropism` worker over the M5 bridge; the other steps run
Rust-native (M6 minimum). Pass-through operations (`register_axis` / `perturb` /
`snapshot`) reuse the M5 message types verbatim and forward straight to the worker.
