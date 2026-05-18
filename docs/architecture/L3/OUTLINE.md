> **L0 doctrine reference (v3.1 transition note)**: this document was written against the prior monolithic L0 (DRAFT 9 SEALED, 2026-05-17). The canonical L0 doctrine is now `docs/architecture/L0/` (v3.1-stratigraphy, 2026-05-18). References in this document using the old `L0 §x.y` / `P2.a` / `I3` notation resolve to v3.1 cards via `docs/architecture/L0/PROVENANCE.md` §2 mapping table. Surgical update of these references to v3.1 citation form is deferred to a v0.9.x housekeeping pass (coupled with Layer C witness corpus implementation per META §5.4) — see `docs/architecture/OUTLINE.md` §3 for details.

---

# L3 — Outline / Charter (implementation map)

> Code organization L2 → L4. Normative for module boundaries / dependency direction / build order / test discipline; **language-agnostic**.

---

## §0-§1. Charter + document set

L3 maps L1 mechanisms + L2 themes to code modules. Commits: module boundaries + acyclic dependency direction + build order + test discipline + file layout. Does NOT commit: language(s) / framework / build tooling / naming — L4.

| File | Topic |
|---|---|
| `L3/OUTLINE.md` (this) | Charter + boundary discipline |
| `L3/PACKAGE_MAP.md` | L1 → code package; dependency graph; build order |

---

## §2. Module-boundary principles

7 L1 mechanism docs → 7 substrate code modules; +1 shared crypto/canonical-bytes module; +owner-side `anchor-client` + per-LLM-host `operator_runtime` (out-of-band). Module index + responsibilities + dependencies: **L3_PACKAGE_MAP §1**.

---

## §3-§4. Dependency + build

Acyclic DAG + parallel build groups: `diagrams/l3_dependency_graph.txt`. Higher cannot import lower; L4 cyclic dependency → L3 module-boundary revision (CI per L0 §10.2). `kernel/hard_rules` cites every module's CRITICAL surfaces but does NOT compile-time import. `anchor-client` + `operator_runtime` depend only on `kernel/shared` serializer spec; built independently once shared stable.

---

## §5-§6. Test + layout

§5 test discipline: T1 (unit) per-module; T2 (integration) cross-module; T3 (substrate e2e) full lifecycle + L0 invariants + L1/HARD_RULES C-row breach; T4 (adversarial) red-team. Per-module surfaces in L3_PACKAGE_MAP §§2-11; L4 picks frameworks per module language.

§6 file layout:

```
v0.9-substrate/
├── kernel/{shared, skin, schema, governance, continuity, tropism, trajectory, hard_rules}/
├── anchor/client/         (owner-side, independent ecosystem)
├── operators/     (per-LLM-host: claude_code, mcp_typescript, mcp_python, …)
├── tests/                 (unit / integration / e2e / adversarial)
└── docs/architecture/     (L0 / L1 / L2 / L3 doctrine)
```

Repository layout (monorepo / multi-repo / hybrid) is L4-decided.
