# L3 — Outline / Charter (implementation map)

> **Status**: OUTLINE DRAFT 1 (2026-05-13).
> **Layer**: L3 (code organization; bridges L2 doctrine → L4 substrate).
> **Authority**: navigation + boundary-discipline. The L3 docs are normative for L4 code organization (module boundaries; dependency direction; build order) but **language-agnostic** — language choice is L4.

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
| `kernel/hard_rules` | L1_HARD_RULES | Cross-cuts index → immune detection layer (the 20 CRITICAL detectors + F-row mutation watchdogs) |
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

**Cross-cut module `kernel/hard_rules`**: contains immune detectors. It cites every other module's CRITICAL surfaces (per L1_HARD_RULES §1 C1-C20) but does NOT import them at compile time — it's the runtime observation/enforcement layer that reads from the other modules' emission streams.

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

## §5. Language choice — L4 territory (with L3 recommendations)

L3 does NOT commit to specific languages. But L3 surfaces the **shape considerations** L4 must answer:

### §5.1 Substrate-kernel language considerations

- **Security-critical**: OS-sealed-key access (TPM / kernel keyring / HSM), cryptographic primitives, Merkle DAG integrity, network-egress enforcement.
- **Performance-relevant**: DAG operations scale with substrate age; trajectory clustering may be compute-intensive.
- **Agent-maintainability**: per P1.a self-hosting, the agent maintains substrate code; the language affects how easily an LLM agent can read + modify + extend it.

Trade-off space: **Rust/Go** (security + performance, harder agent maintenance) vs **Python/TypeScript** (easier agent maintenance, weaker system access, runtime overhead).

L4 recommendation: **multi-language is plausible** (substrate-kernel core in Rust/Go for `kernel/shared` + `kernel/skin` + `kernel/schema`; substrate-kernel doctrine modules in Python for `kernel/tropism` + `kernel/trajectory` + `kernel/hard_rules` where agent-readability matters more than performance). **Single-language is also plausible** (Rust throughout, with agent learning curve as a P1.c-symbiosis cost) (Python throughout, with system-access via careful FFI / privileged daemon companion).

L4 chooses.

### §5.2 Anchor-client language considerations

- **Owner-friendly**: owner is human; the anchor-client is the human interface.
- **Independent provenance**: per L0 §9.3, distributed via channel structurally independent of substrate.
- **Cryptographically robust**: signature verification, canonical-bytes rendering.

L4 recommendation: anchor-client can be a **separate language ecosystem** from substrate (recommended: Rust for cryptographic robustness + TypeScript/web for owner UI). Cross-ecosystem mitigates supply-chain risk (substrate-kernel compromise doesn't automatically compromise anchor-client).

### §5.3 Operator-runtime language considerations

- **LLM-host-language**: depends on which LLM tooling consumes substrate (Claude Code = Node.js; MCP server libs = TypeScript / Python; etc.)
- **Per-handshake keypair generation + signing**: standard crypto primitives needed.

L4 recommendation: operator-runtime is **multiple bindings** (one per LLM-host-language); each binding uses the same canonical-bytes serializer spec from `kernel/shared`.

---

## §6. Test discipline

Each module has three test tiers:

**Tier 1 (unit)**: per-module; pure tests; no inter-module dependencies; runs in CI on every commit. Tests boundaries, edge cases, invariants of the module.

**Tier 2 (integration)**: cross-module; runs after tier 1 passes. Tests dependency interactions (e.g., `kernel/skin` + `kernel/governance` integration for attestation envelope flow).

**Tier 3 (substrate-end-to-end)**: full substrate lifecycle from genesis through some metabolism cycles. Runs less frequently (per build, not per commit). Tests L0 invariants + L1_HARD_RULES C1-C20 breach detection.

**Tier 4 (adversarial)** — optional but recommended: red-team scenarios per L1_HARD_RULES C-rows. Run on a schedule (e.g., nightly), not per-commit.

L4 picks specific test frameworks per module language.

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

## §8. First-implementation priorities

When L4 begins coding, the recommended order:

1. **`kernel/shared`** — establish canonical-bytes serializer + crypto primitives. Validates the serializer spec is implementable. Unblocks every other module.
2. **`kernel/skin`** — establish envelope schema + handshake protocol. Validates the L1_SKIN spec. Unblocks substrate↔operator path.
3. **`kernel/schema`** — establish SSoT + Merkle DAG storage. Validates L1_SCHEMA spec.
4. **`anchor_client`** (parallel) — establish owner-side rendering + signing. Validates anchor-surface independence.
5. **`operator_bindings/<first-target>`** (parallel) — pick one LLM-host-language; build first binding; demonstrates end-to-end substrate↔operator.
6. **`kernel/governance`** — wire attestation flow end-to-end (substrate → anchor-client → owner-signature → substrate).
7. **`kernel/continuity`** — metabolic cycle engine.
8. **`kernel/tropism`** — gradient configuration + first appetite axis (e.g., `hunger`).
9. **`kernel/trajectory`** — first clusterer.
10. **`kernel/hard_rules`** — immune detection wired to all modules.

Milestone targets:
- **Milestone 1 (M1)**: `kernel/shared` + `kernel/skin` + `kernel/schema` running standalone; can perform a single handshake + store a single DAG node. ~3-4 weeks.
- **Milestone 2 (M2)**: + `anchor_client` + `kernel/governance`; can execute a single attestation flow end-to-end. ~3-4 weeks more.
- **Milestone 3 (M3)**: + `kernel/continuity` + minimal `kernel/tropism`; runs a metabolic cycle; absorbs deltas; emits sporocarps. ~4-6 weeks more.
- **Milestone 4 (M4)**: + `kernel/trajectory` + `kernel/hard_rules`; first end-to-end substrate "alive" with all 8 invariants enforced + 20 CRITICAL detectors wired. ~4-6 weeks more.

Total v0.9 first-birth target: **~16-20 weeks** of dedicated implementation work post-L3-sealing.

---

## §9. Open at L3 (deferred to L4)

- Language choice per module (see §5).
- Specific framework / library / build-tool selections.
- Repository layout (monorepo vs multi-repo).
- CI/CD platform.
- Owner anchor-surface mechanism specific choice (TPM / cloud HSM / etc., per L1_GOVERNANCE §2.1).
- Substrate_secret OS-sealing mechanism specific choice (per L1_SKIN §4.2).
- Network-egress enforcement specific mechanism (per L1_SKIN §5).

These are L4-implementation decisions where the doctrine commits to the shape; the choice is the implementer's.
