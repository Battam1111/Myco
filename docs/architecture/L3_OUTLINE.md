# L3 — Outline / Charter (implementation map)

> **Status**: OUTLINE DRAFT 2 (2026-05-17, M27 CA5 cleanup). Code organization (L2 doctrine → L4 substrate). Normative for module boundaries / dependency direction / build order; **language-agnostic**.

---

## §0. Charter

L3 maps L1 mechanisms + L2 themes to code modules. **Commits**: module boundaries, acyclic dependency direction, build order, test discipline, file layout shape. **Does NOT commit**: language(s), framework/library, build tooling, naming conventions — all L4.

---

## §1. Document set

| File | Topic |
|---|---|
| **`L3_OUTLINE.md`** (this file) | Charter + boundary discipline |
| **`L3_PACKAGE_MAP.md`** | L1 → code package; dependency graph; build order |

---

## §2. Module-boundary principles

7 L1 mechanism docs → 7 substrate code modules; plus 1 shared crypto/canonical-bytes module; plus owner-side `anchor_client` and per-LLM-host `operator_runtime` (out-of-band).

### §2.1 Substrate-side

| L3 module | L1 source | Responsibility |
|---|---|---|
| `kernel/skin` | L1_SKIN | Envelope + handshake + single-operator + network-egress enforcement |
| `kernel/governance` | L1_GOVERNANCE | Classifier + dimension table + attestation envelope + lifecycle protocols |
| `kernel/schema` | L1_SCHEMA | SSoT + Merkle DAG + canonical-bytes serializer (spec; runtime shared) + spore-schema + validation tier dispatch |
| `kernel/continuity` | L1_CONTINUITY | Metabolic cycle + dormancy FSM + cold-resume + delta-atomicity WAL |
| `kernel/tropism` | L1_TROPISM | Appetite axes + gradient + sporocarp emission + fruiting evaluation |
| `kernel/trajectory` | L1_TRAJECTORY | Cluster_C + trajectory query API + thread_id + echo-chamber detector |
| `kernel/hard_rules` | L1_HARD_RULES | Immune detection (C1-C20 + C30-C49 substrate-private + F1-F25 watchdogs) |
| `kernel/shared` | (cross-cut) | Crypto + canonical-bytes serializer runtime + Merkle hash + sealed-derive wrapper |

### §2.2 Non-substrate

| L3 module | Role | Where it runs |
|---|---|---|
| `anchor_client` | Owner's anchor-surface tool (render canonical bytes; sign; nonces; heartbeats; mediates substrate vs owner-signing-key) | Owner-controlled host |
| `operator_runtime` | Per-handshake keypair; HMAC envelope_digest; trajectory query consumer | Operator host; pinned with (substrate-ID, anchor-pubkey, owner-pubkey) |

---

## §3. Dependency direction (acyclic DAG)

```
kernel/hard_rules    ← cross-cuts everything (citation only; no runtime dep from rules to mechanisms)
       ↓ (declarative)
kernel/skin   ← depends on kernel/shared
       ↓
kernel/governance ← depends on kernel/skin (attestation requests) + kernel/schema
       ↓
kernel/schema ← depends on kernel/shared
       ↓
kernel/continuity ← depends on kernel/schema + kernel/skin
       ↓
kernel/tropism ← depends on kernel/schema + kernel/continuity
       ↓
kernel/trajectory ← depends on kernel/schema + kernel/tropism (consumes sporocarps from tropism's DAG)
```

Acyclic. Higher cannot import lower. Cyclic dependency in L4 → L3 module-boundary revision (CI-level per L0 §10.2). `kernel/hard_rules` cites every module's CRITICAL surfaces but does NOT compile-time import — runtime observation reading other modules' emission streams.

---

## §4. Build order

`shared` → `skin` + `schema` (parallel) → `governance` (skin+schema) + `continuity` (skin+schema) → `tropism` (schema+continuity) → `trajectory` (schema+tropism) → `hard_rules` (citation-only over all, drafts last).

Parallel tracks: `anchor_client` and `operator_runtime` both depend only on `kernel/shared` serializer spec; built independently of substrate-kernel once shared is stable.

---

## §5. Test discipline

- **Tier 1 (unit)** — per-module.
- **Tier 2 (integration)** — cross-module.
- **Tier 3 (substrate e2e)** — full lifecycle; L0 invariants + L1_HARD_RULES C-row breach detection.
- **Tier 4 (adversarial)** — red-team.

Per-module test surfaces in L3_PACKAGE_MAP §§2-11 (each §X.3). L4 picks frameworks per module language.

---

## §6. File layout (language-agnostic shape)

```
v0.9-substrate/
├── kernel/
│   ├── shared/        ← crypto, canonical-bytes serializer
│   ├── skin/          ← L1_SKIN
│   ├── schema/        ← L1_SCHEMA
│   ├── governance/    ← L1_GOVERNANCE
│   ├── continuity/    ← L1_CONTINUITY
│   ├── tropism/       ← L1_TROPISM
│   ├── trajectory/    ← L1_TRAJECTORY
│   └── hard_rules/    ← L1_HARD_RULES (immune detectors)
├── anchor_client/     ← owner-side, independent ecosystem
├── operator_bindings/ ← per-LLM-host (claude_code, mcp_typescript, mcp_python, …)
├── tests/             ← unit / integration / e2e / adversarial
└── docs/architecture/ ← L0 / L1 / L2 / L3 doctrine
```

Repository layout (monorepo vs multi-repo vs hybrid) is L4-decided.
