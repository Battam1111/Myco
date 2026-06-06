> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4), see `docs/architecture/OUTLINE.md` §3 for details.

---

# L3: Outline / Charter (implementation map)

> Code organization L2 → L4. Normative for module boundaries / dependency direction / build order / test discipline; **language-agnostic**.

---

## §0-§1. Charter + document set

L3 maps L1 mechanisms + L2 themes to code modules. Commits: module boundaries + acyclic dependency direction + build order + test discipline + file layout. Does NOT commit: language(s) / framework / build tooling / naming; L4.

| File | Topic |
|---|---|
| `L3/OUTLINE.md` (this) | Charter + boundary discipline |
| `L3/PACKAGE_MAP.md` | L1 → code package; dependency graph; build order |

---

## §2. Module-boundary principles

7 L1 mechanism docs → 7 kernel-mechanism modules; +1 `kernel/shared` crypto/canonical-bytes foundation. Around those mechanisms the realized substrate adds: the **M5 `kernel/bridge`** cross-language IPC seam; the **`substrate`** runtime-orchestrator daemon (M6); the per-LLM-host **`operators/<host>`** binding (out-of-band); and the **`test_vectors/`** cross-language parity suite. *(Keyless v3.1.5: the prior `anchor/host` + `anchor/client` owner-key custody boundary is removed; both were deleted with the owner-key surface. CI approval is now exercised by the cultivator at the live human-in-the-loop CI gate, GOVERNANCE §2.)* Complete module index + layer grouping + responsibilities + dependencies: **L3/PACKAGE_MAP §1**.

Boundary note (kernel ↔ substrate): `kernel/*` holds **mechanisms + safe wrappers** (`kernel/shared` is `#![forbid(unsafe_code)]`); `substrate` holds **runtime request handlers** (coupled to `substrate::server::ServerState`) **+ the isolated unsafe OS-sealing FFI** (`#![deny(unsafe_code)]` + a single gated `dpapi` allow). Handlers therefore stay substrate-resident; relocating one into a kernel crate would create a forbidden kernel → substrate cycle (see PACKAGE_MAP §12).

---

## §3-§4. Dependency + build

Acyclic DAG + parallel build groups: `diagrams/l3_dependency_graph.txt`. Higher cannot import lower; L4 cyclic dependency → L3 module-boundary revision (CI per L0/META §7.5 (model-diversity)). `kernel/hard_rules` cites every module's CRITICAL surfaces but does NOT compile-time import. `kernel/bridge` (rust + python) is built once `kernel/shared` is stable; the runtime `substrate` then imports only `kernel/{shared, bridge/rust, continuity, schema}` (kernel-inward, acyclic, no kernel crate imports substrate). The out-of-band party `operators/<host>` depends only on the `kernel/shared` serializer spec (re-derived in TypeScript), built independently once shared is stable. *(Keyless v3.1.5: the prior out-of-band `anchor/host` + `anchor/client` parties are removed with the owner-key surface.)*

---

## §5-§6. Test + layout

§5 test discipline: T1 (unit) per-module; T2 (integration) cross-module; T3 (substrate e2e) full lifecycle + L0 invariants + L1/HARD_RULES C-row breach; T4 (adversarial) red-team. Per-module surfaces in L3/PACKAGE_MAP §§2-15; L4 picks frameworks per module language. Tests are **per-crate / per-package** (`<module>/tests/`), not a single top-level `tests/`; the one shared corpus is the **cross-language canonical-bytes parity suite** in `test_vectors/` (PACKAGE_MAP §15), the seam guaranteeing the serializer round-trips identical bytes in Rust, Python, and TypeScript.

§6 file layout (the realized tree, complete module territory; cf. PACKAGE_MAP §1):

```
Myco/
├── Cargo.toml              (Rust workspace: kernel/{shared,skin,schema,continuity,bridge/rust}, substrate, test_vectors/rs)  [keyless v3.1.5: anchor/host removed]
├── kernel/                 (a) mechanism layer, 1:1 with the 7 L1 docs + shared foundation
│   ├── shared/             Rust: canonical-bytes + crypto + safe sealed-derive + sealing-* flags  [#![forbid(unsafe_code)]]
│   ├── skin/  schema/  continuity/        Rust mechanisms
│   ├── governance/  tropism/  trajectory/  hard_rules/   Python mechanisms (pyproject.toml each)
│   └── bridge/             (b) M5 cross-language IPC seam
│       ├── rust/           myco-kernel-bridge   (client + framing + protocol)
│       └── python/         myco_kernel_bridge   (daemon + dispatcher + framing)
├── substrate/              (c) runtime orchestrator, Rust daemon binary  [#![deny(unsafe_code)] + gated dpapi FFI]
│   └── src/{server, persistence, events, federation}/ + lifecycle/integrity/attestation/cultivation/reproduction
│       + sealing/dpapi/at_rest_seal + observatory + handshake/ingest/dag_query/...
│                           (keyless v3.1.5: no anchor/ directory; the owner-key custody boundary was deleted)
├── operators/              (d) per-LLM-host agent binding (out-of-band)
│   └── claude/             TypeScript: @myco/operators-claude (MCP server + substrate-client + ceremonies; keyless, no anchor client)
├── test_vectors/           (e) cross-language canonical-bytes parity contracts
│   ├── canonical_bytes_v1.json  crypto_v1.json   (language-neutral vectors)
│   └── rs/                 myco-test-vectors-rs (Cargo member; parity harness)
└── docs/architecture/      (L0 / L1 / L2 / L3 doctrine)

# T1 unit tests live per-module under <module>/tests/ (each crate + each package);
# cross-language parity lives in test_vectors/: there is no single top-level tests/.
```

Repository layout (monorepo / multi-repo / hybrid) is L4-decided.
