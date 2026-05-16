# L3 — Outline / Charter (implementation map)

> **Status**: OUTLINE DRAFT 2 (2026-05-17, M27 CA5 cleanup). Code organization layer (bridges L2 doctrine → L4 substrate). Normative for L4 module boundaries / dependency direction / build order; **language-agnostic**.

---

## §0. What L3 is

L3 is the **code organization** layer. It maps L1 mechanisms + L2 doctrine themes to code modules with explicit boundaries and dependency directions. L3 does NOT commit to specific code; L4 writes the code. L3 does NOT commit to a specific language; L4 chooses (potentially per-module).

**L3 commits to**:
- Module boundaries (which L1 mechanism becomes which substrate code module)
- Dependency direction (acyclic; which modules import which)
- Build order (which modules can be built independently; which require others first)
- Test discipline (what each module's test surface looks like)
- File layout shape (where files live in the repo)

**L3 does NOT commit to**:
- Specific language(s) — L4 chooses, potentially multi-language (substrate-kernel in security-language; agent-tooling in agent-friendly-language)
- Specific framework / library choices — L4 picks
- Specific build tooling — L4 picks
- Code naming conventions — L4 picks

---

## §1. The L3 document set

| File | Topic | Status |
|---|---|---|
| **`L3_OUTLINE.md`** (this file) | Charter + boundary discipline + decision points | DRAFT 1 ✓ |
| **`L3_PACKAGE_MAP.md`** | Module-by-module map: L1 mechanism → code package; dependency graph; build order | DRAFT 1 ✓ |

Just 2 docs. L3 is intentionally **smaller than L2** because the code organization is a finite catalog (~10 modules) rather than a cross-cut perspective space.

---

## §2. Module-boundary principles

The 7 L1 mechanism docs each become one substrate code module (or one tightly-coupled module cluster). One additional support module for shared cryptographic + canonical-bytes infrastructure. One module for the anchor-surface client (owner-side, NOT substrate-side, runs out-of-band).

### §2.1 Substrate-side modules (run inside substrate process)

| L3 module | L1 source | Responsibility |
|---|---|---|
| `kernel/skin` | L1_SKIN | Envelope schema + handshake protocol + single-operator + network-egress enforcement |
| `kernel/governance` | L1_GOVERNANCE | Classifier function + dimension table + attestation request envelope construction (canonical-bytes side) + lifecycle protocols (genesis/dormancy/reproduction/mortality state transitions) |
| `kernel/schema` | L1_SCHEMA | SSoT representation + Merkle DAG storage + canonical-bytes serializer (the SPEC; runtime is shared with anchor-client) + spore-schema + validation tier dispatch |
| `kernel/continuity` | L1_CONTINUITY | Metabolic cycle engine + dormancy state machine + cold-resume protocol + delta-atomicity WAL |
| `kernel/tropism` | L1_TROPISM | Appetite axes + gradient configuration + sporocarp emission + fruiting-trigger evaluation |
| `kernel/trajectory` | L1_TRAJECTORY | Cluster_C dispatcher + trajectory query API + thread_id support + echo-chamber detector |
| `kernel/hard_rules` | L1_HARD_RULES | Cross-cuts index → immune detection layer (CRITICAL detectors C1-C20 spec + C30-C49 substrate-private namespace; F-row watchdogs F1-F25 per current catalog) |
| `kernel/shared` | (cross-cut) | Cryptographic primitives + canonical-bytes serializer runtime + Merkle hash + sealed-derive wrapper |

### §2.2 Non-substrate modules

| L3 module | Role | Where it runs |
|---|---|---|
| `anchor_client` | Owner's anchor-surface tool (renders canonical bytes; verifies signatures; manages nonces + heartbeats; mediates between substrate and owner-signing-key) | Owner-controlled host, NOT substrate process |
| `operator_runtime` | Agent-side runtime: per-handshake keypair generation; HMAC envelope_digest; trajectory query API consumer | Operator host (e.g., Claude Code, MCP client, etc.); pinned with owner-supplied substrate-ID + anchor-endpoint-pubkey + owner-pubkey |

---

## §3. Dependency direction (acyclic DAG)

```
kernel/hard_rules    ← cross-cuts everything (citation only; no runtime dep from rules to mechanisms)
       ↓ (declarative)
kernel/skin   ← depends on kernel/shared
       ↓
kernel/governance ← depends on kernel/skin (for emitting attestation requests) + kernel/schema
       ↓
kernel/schema ← depends on kernel/shared
       ↓
kernel/continuity ← depends on kernel/schema + kernel/skin
       ↓
kernel/tropism ← depends on kernel/schema + kernel/continuity
       ↓
kernel/trajectory ← depends on kernel/schema + kernel/tropism (consumes sporocarps from tropism's DAG)
```

**Strict rule**: dependency direction is acyclic. A module higher in the graph cannot import a module lower. If a cyclic dependency surfaces during L4 implementation, the L3 module boundary needs revision (CI-level revision per L0 §10.2 — L3 is L0-governed).

**Cross-cut module `kernel/hard_rules`**: contains immune detectors. It cites every other module's CRITICAL surfaces (per L1_HARD_RULES §1 — C1-C20 spec + C30-C49 substrate-private) but does NOT import them at compile time — it's the runtime observation/enforcement layer that reads from the other modules' emission streams.

---

## §4. Build order (independent modules first)

Build order for L4 implementation (modules earlier have no dependencies on later):

1. **`kernel/shared`** — pure crypto + canonical-bytes serializer (no dependencies; standalone). Foundation.
2. **`kernel/skin`** — depends only on `kernel/shared`. Skin envelope + handshake. Tested in isolation.
3. **`kernel/schema`** — depends only on `kernel/shared`. SSoT + Merkle DAG. Tested in isolation.
4. **`kernel/governance`** — depends on `kernel/skin` + `kernel/schema`. Classifier + attestation envelope construction + lifecycle FSM.
5. **`kernel/continuity`** — depends on `kernel/skin` + `kernel/schema`. Metabolic cycle + dormancy + cold-resume.
6. **`kernel/tropism`** — depends on `kernel/schema` + `kernel/continuity`. Gradient configuration + sporocarp emission.
7. **`kernel/trajectory`** — depends on `kernel/schema` + `kernel/tropism`. Cluster_C + trajectory query.
8. **`kernel/hard_rules`** — depends on all of the above (citation-only; runtime observation). Drafts last.

In parallel with substrate-side build:

- **`anchor_client`** — owner-side. Depends on `kernel/shared` (canonical-bytes serializer spec) but runs out-of-band. Can be built independently of substrate-kernel once `kernel/shared` is stable.
- **`operator_runtime`** — operator-side. Depends on `kernel/shared` (canonical-bytes serializer spec for independent derivation per L2_TRUST_MODEL §2.5). Built independently of substrate-kernel.

---

## §5. Language choice — deferred to L4

L3 does NOT commit to specific languages. Per-module language selection (substrate-kernel multi-language plausible; anchor-client separate ecosystem mitigates supply-chain risk; operator-runtime is multiple bindings per LLM-host-language) is L4 territory. All bindings use the same canonical-bytes serializer spec from `kernel/shared`.

---

## §6. Test discipline

Four-tier discipline: **Tier 1 (unit)** per-module; **Tier 2 (integration)** cross-module; **Tier 3 (substrate-end-to-end)** full lifecycle, tests L0 invariants + L1_HARD_RULES C-row breach detection; **Tier 4 (adversarial)** red-team scenarios. Per-module test surface specifications in L3_PACKAGE_MAP §§2-11 (each module's §X.3 Test discipline subsection). L4 picks frameworks per module language.

---

## §7. File layout (shape, language-agnostic)

```
v0.9-substrate/
├── kernel/
│   ├── shared/        ← crypto primitives, canonical-bytes serializer
│   ├── skin/          ← L1_SKIN
│   ├── schema/        ← L1_SCHEMA
│   ├── governance/    ← L1_GOVERNANCE
│   ├── continuity/    ← L1_CONTINUITY
│   ├── tropism/       ← L1_TROPISM
│   ├── trajectory/    ← L1_TRAJECTORY
│   └── hard_rules/    ← L1_HARD_RULES (immune detectors)
├── anchor_client/     ← owner-side, independent ecosystem
├── operator_bindings/ ← per-LLM-host
│   ├── claude_code/
│   ├── mcp_typescript/
│   ├── mcp_python/
│   └── ...
├── tests/
│   ├── unit/          ← per-module
│   ├── integration/   ← cross-module
│   ├── e2e/           ← substrate lifecycle
│   └── adversarial/   ← L1_HARD_RULES C-row red-team
└── docs/
    └── architecture/  ← L0 / L1 / L2 / L3 doctrine (this directory)
```

Specific repository layout (monorepo vs multi-repo vs hybrid) is L4-decided. The shape above is the recommended starting structure.

---

## §8. Open at L3 (deferred to L4)

- Language choice per module (see §5).
- Specific framework / library / build-tool selections.
- Repository layout (monorepo vs multi-repo).
- CI/CD platform.
- Owner anchor-surface mechanism specific choice (TPM / cloud HSM / etc., per L1_GOVERNANCE §2.1).
- Substrate_secret OS-sealing mechanism specific choice (per L1_SKIN §4.2).
- Network-egress enforcement specific mechanism (per L1_SKIN §5).

These are L4-implementation decisions where the doctrine commits to the shape; the choice is the implementer's.
