# L1 — Outline / Charter (post-structural-rework)

> **Status**: OUTLINE — naming-cleaned, post-DRAFT-5-of-L0 split (2026-05-13).
> **Layer**: L1 (mechanism). Governed by L0.
> **Authority**: this outline has **no** binding authority. It is a charter — a navigation aid. The L1 documents listed below (some written, some pending) are the authoritative L1 layer.
> **Naming hygiene**: throughout this document and the L1 layer, *"v0.9"* refers to the Myco substrate version. *"DRAFT N"* (no `v` prefix) refers to a document revision counter. There is no "L1 v0.X" — documents either exist (and carry a DRAFT N status) or they don't.

---

## §0. What L1 is

L1 is the **mechanism enforcement layer** for L0's principles + invariants. Where L0 says "Myco's dispatch must be symmetric, not request/response, support continuous operation" (negative + constraint statements), L1 says "the positive form is tropism + sporocarp punctuation; here is its schema; here is how it operationalizes I2 governance" (positive + mechanism specifications).

### §0.1 What L1 is NOT (and what L0 is NOT)

This layer split was clarified during L0 DRAFT 5 structural rework. The boundary:

- **L0 commits to**: identity (what Myco IS), negative space (what Myco IS NOT), constraints (what L1+ must satisfy).
- **L1 commits to**: positive forms (the specific mechanism satisfying L0's constraints), specifications (schemas, protocols, classifier functions), operational details (lifecycle protocols, validation procedures).

A statement belongs in L1 if it answers "*how does the substrate actually do X?*" rather than "*what is X-ness?*". L0 was bloated with L1 content in DRAFTs 3-4 (~700+ lines of mechanism detail); DRAFT 5 corrected this by extracting `L1_TROPISM.md` and `L1_TRAJECTORY.md` and condensing L0 to identity commitments only.

### §0.2 What L1 does NOT inherit from v0.8

v0.8 L1 was 7 hard rules (R1-R7) + canon schema + exit codes. Per L0's C7.3 maximal v0.8-origin discrimination, v0.9 L1 is rebuilt from L0's eight invariants and nine principles. Specifically:

- **No boot/session-end ritual** (§6 — continuous online agent dissolves R1/R2).
- **Sense-before-assert** is subsumed into the dispatch's field-read primitive (the agent inhabits the gradient configuration; sensing IS dispatch).
- **Capture-now** survives as the `hunger` appetite axis in tropism.
- **Cross-reference** survives as I5 (universal reachability across full state space) + orphans as immune signals.
- **Write-surface** survives as I8 (single-skin integrity) + the appetite-locality rule from I6.
- **Top-down** survives as the L0-L1-L2-L3-L4 layering itself.

L1 v0.9 is **not** "R1-R7 rephrased". L1 is whatever specifications emerge from operationalizing the 8 invariants + the chosen positive dispatch form + the chosen positive intent-derivation form + remaining mechanism choices.

---

## §1. L1 document set — current state

L1 is delivered as a set of focused documents (recommended partitioning, per §J below; subject to revision as L1 drafting progresses).

| File | Topic | Status |
|---|---|---|
| **`L1_OUTLINE.md`** (this file) | L1 charter + table of contents | OUTLINE (revised post-DRAFT-5) |
| **`L1_TROPISM.md`** | Positive dispatch form — tropism + sporocarp punctuation | **DRAFT 1 (2026-05-13)** ✓ |
| **`L1_TRAJECTORY.md`** | Positive intent-derivation mechanism — trajectory query over causal DAG | **DRAFT 1 (2026-05-13)** ✓ |
| `L1_SCHEMA.md` | SSoT format (I3) + DAG storage (I4) + reachability tiers (I5) + spore-schema (I7) | NOT YET WRITTEN |
| `L1_GOVERNANCE.md` | I2 classifier + lifecycle operations (genesis, dormancy, reproduction closure, mortality) | NOT YET WRITTEN |
| `L1_SKIN.md` | I8 skin specification (intake envelope, output gating, single-operator enforcement, breach detection) | NOT YET WRITTEN |
| `L1_CONTINUITY.md` | Host-disconnect recovery, metabolic cycle cadence, dormancy throttle | NOT YET WRITTEN |
| `L1_HARD_RULES.md` | The G-rules catalog (v0.9 replacement for v0.8 R1-R7) | NOT YET WRITTEN |

---

## §2. Coverage of L0 design hooks across L1 docs

This table maps L0-DRAFT-5's "L1-specified" mentions to the L1 doc that owns the answer:

| L0 reference | L1 doc owning it |
|---|---|
| §5.2 positive dispatch form | `L1_TROPISM.md` ✓ |
| §5.3 positive intent-derivation mechanism | `L1_TRAJECTORY.md` ✓ |
| §6 metabolic cycle cadence | `L1_CONTINUITY.md` |
| §6 dormancy compute budget | `L1_CONTINUITY.md` |
| P3 failed-evolution rollback mechanism | `L1_GOVERNANCE.md` |
| P8 federation discovery | `L1_GOVERNANCE.md` |
| I1 operator-token format | `L1_SKIN.md` (token is a skin-handshake artifact) |
| I2 classifier function | `L1_GOVERNANCE.md` |
| I3 SSoT format + claim coverage | `L1_SCHEMA.md` |
| I4 DAG storage + retention policy | `L1_SCHEMA.md` |
| I5 storage tiers covered | `L1_SCHEMA.md` |
| I6 embedding-model carve-out details | `L1_TROPISM.md` ✓ (appetite-locality + B-section hooks) |
| I7 reproduction closure verification | `L1_GOVERNANCE.md` |
| I8 skin specification | `L1_SKIN.md` |
| §7 Living Bets observatory signal-#6 attestation cross-check | `L1_GOVERNANCE.md` (observatory is governance-adjacent) |
| Owner attestation cryptographic protocol | `L1_GOVERNANCE.md` |
| Recoverability budget definition | `L1_SCHEMA.md` (backup policy lives with SSoT/DAG retention) |

---

## §3. Outstanding L1 work — what's pending

The five not-yet-written L1 docs each cover a coherent slice. The recommended drafting order (chosen for dependency-minimization):

1. **`L1_SCHEMA.md`** — SSoT format + DAG storage. Many other docs depend on this (governance reads SSoT, skin enforces intake/output against schema, continuity reads from DAG). Drafting first reduces forward-references.
2. **`L1_GOVERNANCE.md`** — classifier function + lifecycle. Depends on schema (knows what fields are governance-classified). Mostly stand-alone otherwise.
3. **`L1_SKIN.md`** — intake/output specification. Depends on schema (knows valid envelopes).
4. **`L1_CONTINUITY.md`** — recovery + cadence. Depends on all three above (cycle invariant checks reference schema; recovery reads sealed sporocarps; dormancy interacts with governance).
5. **`L1_HARD_RULES.md`** — the G-rules catalog. Should be last because it operationalizes the others (G-rules cite specific schema sections, classifier rules, skin specs, etc.).

Each L1 doc target: ~300-500 lines, focused. NOT the bloated multi-topic L0 DRAFTs 3-4 anti-pattern.

---

## §4. L1 design questions (cross-document)

These cut across the L1 docs; resolution may live in one doc but affect others:

1. **Should there be one canonical L1 entry point, or is the OUTLINE the entry point?** Recommended: this OUTLINE is the entry. Each L1 doc has its own §1 "what this doc commits to". No master "L1.md" needed.
2. **Cross-doc invariant traceability** — each L1 doc must enumerate which L0 invariants and principles it projects (already established in L1_TROPISM and L1_TRAJECTORY).
3. **L1 mutation discipline** — a change to an L1 doc is contract-identity-level (per L0 I2). Owner-gated. Process: same craft-style proposal + owner approval that L0 uses, but for L1 these may be more frequent (L1 evolves as L2/L3 implementation surfaces refinement needs).
4. **Cross-L1 consistency check** — when one L1 doc says "X is governance-classified" and another says "X is daily-autonomous", the conflict must be detected automatically. Recommended: a small classifier-table dimension in `L1_GOVERNANCE.md` is the source of truth; other L1 docs cite it, not duplicate it.
5. **L0 revision back-pressure** — when L1 work reveals an L0 constraint is unworkable, the L1 doc records the finding and L0 revision is proposed (per L0 §9.2). The L1 doc is NOT silently weakened.

---

## §J. Document-set rationale (kept from earlier outline)

The 7-doc set was chosen because:

- 7 topics are coherent slices: dispatch / intent / schema / governance / skin / continuity / rules.
- Each doc is short enough to read in one sitting (~300-500 lines, vs L0 DRAFT 4's 1117 — which was the source of the structural-rework decision).
- Cross-doc dependencies are mostly one-directional (schema is foundational; rules is downstream-of-everything).
- Owner can review and approve incrementally — no need for a single massive L1 review.

Alternative considered + rejected:

- **One monolithic `L1.md` doc**: rejected because L1 is large enough to warrant partitioning (the v0.8 monolithic L1_CONTRACT/protocol.md was a maintenance pain point).
- **Per-invariant docs (8 docs, one per I1-I8)**: rejected because some invariants tightly couple (I3 + I4 + I5 all touch schema) and would force cross-references.
- **Per-principle docs (9 docs, one per P1-P9)**: rejected because principles are L0; L1 is mechanism, which doesn't cleanly partition by principle.

The topic-split (7 docs) is the chosen partition.
