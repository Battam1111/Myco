# L3 — Outline / Charter (implementation map)

> **Status**: OUTLINE DRAFT 3 (2026-05-17, M27 R5 cleanup). Code organization L2 → L4. Normative for module boundaries / dependency direction / build order / test discipline; **language-agnostic**.

---

## §0-§1. Charter + document set

L3 maps L1 mechanisms + L2 themes to code modules. Commits: module boundaries + acyclic dependency direction + build order + test discipline + file layout. Does NOT commit: language(s) / framework / build tooling / naming — L4.

| File | Topic |
|---|---|
| `L3_OUTLINE.md` (this) | Charter + boundary discipline |
| `L3_PACKAGE_MAP.md` | L1 → code package; dependency graph; build order |

---

## §2. Module-boundary principles

7 L1 mechanism docs → 7 substrate code modules; +1 shared crypto/canonical-bytes module; +owner-side `anchor_client` + per-LLM-host `operator_runtime` (out-of-band).

**§2.1 Substrate-side**:

| L3 module | L1 source | Responsibility |
|---|---|---|
| `kernel/skin` | L1_SKIN | Envelope + handshake + single-operator + egress |
| `kernel/governance` | L1_GOVERNANCE | Classifier + dimension table + attestation + lifecycle |
| `kernel/schema` | L1_SCHEMA | SSoT + Merkle DAG + canonical-bytes + spore + validation dispatch |
| `kernel/continuity` | L1_CONTINUITY | Metabolic cycle + dormancy FSM + cold-resume + WAL |
| `kernel/tropism` | L1_TROPISM | Appetite axes + gradient + sporocarp emission + fruiting |
| `kernel/trajectory` | L1_TRAJECTORY | Cluster_C + trajectory query + thread_id + echo-chamber |
| `kernel/hard_rules` | L1_HARD_RULES | Immune detection (C1-C20 + C30-C49 + F1-F25) |
| `kernel/shared` | (cross-cut) | Crypto + canonical-bytes runtime + Merkle + sealed-derive |

**§2.2 Non-substrate**:

| L3 module | Role | Where |
|---|---|---|
| `anchor_client` | Owner anchor tool (render + sign + nonces + heartbeats) | Owner-controlled host |
| `operator_runtime` | Per-handshake keypair; HMAC envelope_digest; trajectory consumer | Operator host; pinned with (substrate-ID, anchor-pubkey, owner-pubkey) |

---

## §3-§4. Dependency + build

Acyclic DAG + parallel build groups: `diagrams/l3_dependency_graph.txt`. Higher cannot import lower; L4 cyclic dependency → L3 module-boundary revision (CI per L0 §10.2). `kernel/hard_rules` cites every module's CRITICAL surfaces but does NOT compile-time import. `anchor_client` + `operator_runtime` depend only on `kernel/shared` serializer spec; built independently once shared stable.

---

## §5-§6. Test + layout

§5 test discipline: T1 (unit) per-module; T2 (integration) cross-module; T3 (substrate e2e) full lifecycle + L0 invariants + L1_HARD_RULES C-row breach; T4 (adversarial) red-team. Per-module surfaces in L3_PACKAGE_MAP §§2-11; L4 picks frameworks per module language.

§6 file layout:

```
v0.9-substrate/
├── kernel/{shared, skin, schema, governance, continuity, tropism, trajectory, hard_rules}/
├── anchor_client/         (owner-side, independent ecosystem)
├── operator_bindings/     (per-LLM-host: claude_code, mcp_typescript, mcp_python, …)
├── tests/                 (unit / integration / e2e / adversarial)
└── docs/architecture/     (L0 / L1 / L2 / L3 doctrine)
```

Repository layout (monorepo / multi-repo / hybrid) is L4-decided.
