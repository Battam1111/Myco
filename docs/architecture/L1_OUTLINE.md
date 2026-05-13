# L1 — Contract (v0.9 OUTLINE / sketch, pre-L0-seal)

> **Status**: OUTLINE v0.1 (skeleton — not yet authoritative, 2026-05-13).
> Produced alongside L0 v0.3 to surface L1's structural shape so the
> owner can sanity-check that L0 v0.3 is "L1-shaped" (L0 commits the
> right things; L1 territory begins where L0 stops).
> **Layer**: L1 (the contract). Below L0. Above L2 / L3 / L4.
> **Authority**: this outline carries **no** authority — it cannot
> bind L1 design. Formal L1 begins only after owner approves L0 v0.3
> as sealed.
> **Replaces**: v0.8 L1 was 7 hard rules (R1-R7) + canon schema +
> exit codes. v0.9 L1 is rebuilt from α (no R1-R7 inheritance per
> C7.3 maximal v0.8-origin discrimination).

---

## §0. What L1 is, and how it differs from v0.8 L1

L1 is the **mechanical enforcement layer** for L0's principles +
invariants. Where L0 says "agent-only consumption is the rule",
L1 says "this is the surface that's checked; this is the predicate
that runs; this is the exit code on failure". L1 is the layer the
immune system reads to know what to enforce.

**v0.8 L1 shape (rejected per C7.3):**
- R1-R7 hard rules (boot ritual, session-end, sense-before-assert,
  capture-now, cross-reference, write-surface, top-down).
- `_canon.yaml`-rooted SSoT + JSON-schema versioned migration chain.
- 20-verb manifest dispatch SSoT.
- Numeric exit codes.

**v0.9 L1 shape (rebuilt from α):**

- **No boot ritual / session-end ritual** (§6 — continuous online
  agent dissolves R1/R2).
- **No sense-before-assert as named rule** (subsumed into tropism's
  field-read primitive — the agent inhabits the field; sensing IS
  the dispatch surface).
- **Capture-now** survives in spirit as the tropism's `hunger`
  appetite axis (substrate's gradient pulls metabolism toward
  unmetabolized deltas).
- **Cross-reference** survives as I5 (universal reachability across
  the full state space) + the immune-detectable nature of orphans.
- **Write-surface** survives as I9 (single-skin integrity) + the
  appetite-locality rule (substrate-internal computation, never
  outbound RPC for adjacent techniques).
- **Top-down** survives as the L0-L1-L2-L3-L4 layering itself
  (§9 — L0 revision protocol).

So L1 v0.9 is **not** "R1-R7 rephrased". L1 is whatever specification
emerges from operationalizing the 9 invariants + the tropism
dispatch + the trajectory intent model.

---

## §A. Continuity model details (operationalizes L0 §6)

**Required specifications:**

A1. **Continuity-recovery protocol.** When operator-connection
    drops and reconnects, how is field state re-presented to the
    operator? Options:
    - Eager full-field snapshot at reconnect (high cost, deterministic).
    - Lazy gradient-only digest (low cost, agent re-builds context
      from sporocarps as needed).
    - Hybrid (digest by default + drill-down on demand).
    Recommended position: hybrid, with the digest size emerging from
    Living Bets read-window ratio (§7 base signal #6).

A2. **Dormant-substrate metabolism budget.** While no operator is
    attached, does the substrate continue running its full
    metabolism? Or does it idle on most appetite axes? The choice
    affects energy / compute cost.

A3. **Cold-resume invariants.** What must be true of the field at
    reconnect-time for the operator to validly resume? (I3
    self-validation + I5 reachability checks must pass before the
    operator is presented the field.)

---

## §B. Tropism specification (operationalizes L0 §5.2 — 10 hooks)

These are the 10 L1 design hooks the C5.3 craft surfaced.

B1. **Appetite axis schema.** Each appetite is structured as:
    - `name` (mycology-strict).
    - `computation_locality` (must assert substrate-internal; outbound
      RPC = appetite-locality-rule violation = I6 breach).
    - `domain` (the value space the gradient can take).
    - `update_rule` (the substrate-internal function that updates the
      gradient on each metabolic tick).
    - `threshold_emergence_rule` (how the fruiting threshold emerges
      from substrate history).

B2. **Initial appetite set.** Candidates (illustrative; L1 chooses):
    - `hunger` (unmetabolized intake pressure) — P2.
    - `drift` (graph-disconnection pressure) — P5 / I5.
    - `decay` (staleness pressure) — P4.
    - `federation-pull` (peer-substrate signal pressure) — P8 / I8.
    - `evolution-tension` (schema-vs-content disagreement) — P3.
    - `skin-pressure` (boundary integrity signals) — P9 / I9.
    Open: does L1 include `mortality-signal` as an explicit appetite,
    or is mortality a state-transition outside the field?

B3. **Sporocarp type tree.** Each sporocarp type carries:
    - `type` (mycology-strict name).
    - `payload_schema` (typed contents).
    - `causal_in_edges` (which gradients / deltas produced this fruit).
    - `causal_out_edges` (subsequent fruits / deltas this seeds).
    - `governance_classification` (per I2: daily vs contract-identity-level).
    Candidate types: `intake`, `digestion`, `refinement`, `federation`,
    `mortality_signal`, `governance_amend`, `schema_evolve`, etc.

B4. **Field exposure protocol.** How is the gradient configuration
    rendered into the agent's read-window? Required properties:
    - **Bounded** (sized to read-window budget per §7 base #6).
    - **Structured** (the agent must parse appetite levels +
      recent sporocarps efficiently).
    - **Stateless** (cold-resumable; no prior agent state required to
      read the field at time t).

B5. **Delta intake surface.** Deltas are agent emissions into the
    field. Required properties:
    - **Shape-agnostic** (text / file ref / structured / etc. —
      per P2).
    - **Envelope-checked** (I9 — admit all content, reject only on
      envelope integrity).
    - **Causally-stamped** (every delta enters the DAG as a node
      with `causal_parents` pointing to the field state it
      observed).

B6. **Sporocarp governance gate.** Which sporocarp types are
    contract-identity-level (owner-gated, per I2)? Likely:
    - `axis_schema_change` (changing appetite-axis structure) →
      contract-identity.
    - `skin_redefinition` → contract-identity.
    - `sporocarp_type_addition` → contract-identity.
    - All other (daily metabolism, federation, intake, digest) →
      daily / agent-autonomous.

B7. **Continuity-recovery (cross-ref §A1).**

B8. **Causal DAG embedding.** Edge classes:
    - `gradient_causation` (sporocarp ← gradient that fruited it).
    - `delta_source` (sporocarp / state ← delta that fed it).
    - `sporocarp_derivation` (sporocarp ← prior sporocarps it builds on).
    - `federation_coupling` (cross-substrate DAG link).

B9. **Multi-substrate federation surface.** Inter-substrate federation
    is gradient-coupling between fields:
    - Option α: peer substrate's sporocarps become deltas into local
      field (high integration cost, faithful).
    - Option β: explicit `coupling` primitive (low cost, semantic
      transfer only).
    L1 chooses (likely β with α as opt-in for tight-coupling pairs).

B10. **Self-hosting (P1.a) bootstrap.** What initial appetite set does
     the kernel's own substrate carry at genesis? (The "spore-schema"
     for the kernel-self-hosting case is L1-defined.)

---

## §C. Schema specification (SSoT — I3 enforcer)

C1. **SSoT format.** v0.8 used `_canon.yaml`. v0.9 chooses fresh
    per C7.3. Candidates:
    - YAML (legibility, current default; what v0.8 used).
    - TOML (more rigorous typing).
    - SQLite (native query / index).
    - Custom binary + WAL (highest performance, lowest legibility).
    - JSON + JSONL append log (deterministic append, easy diff).
    Per C7.3 v0.8-discrimination, YAML must justify independently
    (legibility for agent-side cold-read is a defensible reason).

C2. **DAG storage discipline (I4).** Where is the causal DAG stored?
    Same file as SSoT? Separate file? Separate medium (SQLite)?
    The choice affects I4 retention enforcement.

C3. **Retention policy.** Full-fidelity DAG is unbounded.
    Contract-identity-level retention rule must specify:
    - Maximum DAG age (none = full eternal record; cap = chosen lossy
      compression — VIOLATES I4 unless the cap operation produces
      a P1.b''-gated sporocarp).
    - Compaction predicate (when does the DAG decide to summarize? —
      only at contract-identity bumps; never silently).

C4. **Spore-schema (I8).** What does a child substrate inherit
    from parent at reproduction time?
    - Minimum: appetite-axis schemas + sporocarp-type tree + SSoT
      designation.
    - Maximum: full parent DAG snapshot (close to cloning).
    - Recommended: appetite + sporocarp-type + SSoT-designation
      only (true fresh-symbiosis-from-scratch per P8).

C5. **Reachability tiers (I5).** Which storage tiers are part of
    the reachability graph? Notes, doctrine, canon, DAG, observatory.
    Tier-exemption is contract-identity-level.

---

## §D. Governance classification (I2 enforcer)

D1. **Classifier function signature.** `classify(touched: Set[Field/File]) -> {daily, contract-identity-level}`.

D2. **Field-touch table.** Which fields, when mutated, trigger
    contract-identity classification?
    - L0 file → always contract-identity.
    - L1 file (protocol / canon schema) → always contract-identity.
    - Appetite-axis-schema field → contract-identity.
    - Sporocarp-type-tree → contract-identity.
    - SSoT-designation → contract-identity.
    - Skin-surface declaration → contract-identity.
    - All other → daily.

D3. **Owner-gate mechanism.** How does the substrate actually wait
    for owner approval on a contract-identity-level change?
    - Pending sporocarp queue with `status=awaiting_owner` field.
    - Out-of-band owner attestation (signed approval delta) feeds
      back into the field; pending sporocarp resolves.

D4. **Untyped mutation immune-detection.** Mutations that don't
    classify (the classifier returns Unknown) are immune-flagged
    immediately. Specifies the dim grade.

---

## §E. Skin specification (I9 enforcer)

E1. **Skin surface declaration.** A single file or canon-section
    enumerating:
    - Intake endpoints (the surfaces deltas can enter through).
    - Output endpoints (the surfaces results can exit through).
    - Forbidden surfaces (everything else is breach).

E2. **Intake envelope check.** What does the substrate validate
    on a delta arriving at intake?
    - Encoding integrity (the byte stream is well-formed).
    - Size (delta is below absolute-max — not content filtering).
    - Origin attestation (delta comes through declared intake surface,
      not smuggled).
    Content filtering is **forbidden** (P2 / I9 — admit all content).

E3. **Output gating.** What goes through output surface? Federation
    sporocarps to peer substrates, human-facing summaries (per P2.a /
    I6 same-pipeline rule), API responses. NOT internal metabolism
    events.

E4. **Single-operator enforcement.** L1 specifies how concurrent
    connections are detected and refused at the skin (per P1.c +
    I9 single-active-operator semantics).

E5. **Breach detection mechanism.** What dim grade does each breach
    category receive?

---

## §F. Lifecycle operations (I1 state-space + I7 + I8 enforcers)

F1. **Genesis protocol.** The only human moment in the substrate's
    lifecycle. Specifies:
    - Initial appetite set (per B2 + B10).
    - Initial sporocarp-type tree (per B3).
    - Initial SSoT skeleton (per C1).
    - Initial skin surface (per E1).
    - Owner attestation as the first sporocarp.

F2. **Dormancy semantics.** What metabolism continues when no
    operator is attached? (Cross-ref A2.) When does dormancy
    auto-transition to mortality? — never (per I7; only intentional
    or catastrophic).

F3. **Reproduction closure (I8).** When `spawn-child` fires:
    - Child runs first metabolic cycle as part of spawn (not after).
    - All I1-I9 checks must pass in the child before spawn returns success.
    - Parent-child link enters parent's DAG as a federation_coupling edge.

F4. **Mortality detection.** When is "destroyed" actually true?
    - Intentional: owner-attested destruction sporocarp.
    - Catastrophic: substrate storage corruption beyond recovery
      budget (which is L1-specified — backup policy lives here).
    Approaches to mortality (graph fracture, repeated I5 failures)
    are immune-grade signals, not death itself.

---

## §G. Hard rules (the v0.9 replacement for v0.8 R1-R7)

The 9 invariants in L0 §4 are the load-bearing rules. L1 may name
additional rules that operationalize them. Likely:

- **G1**: Every delta enters via skin (I9). Direct write to internal
  storage = breach.
- **G2**: Every appetite axis is substrate-internal (I6 / appetite-
  locality rule). Outbound RPC dispatching = breach.
- **G3**: Every state mutation classifies under I2 before persisting.
- **G4**: Every state has a recoverable derivation via DAG (I4).
  Silent state change = breach.
- **G5**: Every sporocarp is content-addressed, causally-stamped,
  type-conformant (I4 + B3).
- **G6**: Every claim about substrate state is checkable against SSoT
  (I3).
- **G7**: Every node reachable from every other (I5).

These are **not "v0.8 R1-R7 renamed"**. They're a fresh derivation
from the invariants. Cross-trace verifies independence from v0.8
shape (per C7.3).

---

## §H. Intent / trajectory (operationalizes L0 §5.3)

H1. **Trajectory window default.** Possible defaults:
    - Time-bounded (last 24h).
    - Operation-count-bounded (last N).
    - Graph-distance-bounded (k-hop from current frontier).
    Recommended: all three exposed as parameters; defaults emerge
    from substrate observatory.

H2. **Vector retrieval at trajectory layer (P2.a).** When DAG edges
    are sparse (agent jumped context), should trajectory use vector
    similarity over operation embeddings? Recommended: yes —
    P2.a native vector retrieval lands here.

H3. **Multi-trajectory composition.** If pair has multiple parallel
    directions, does trajectory return one composite or a set?
    Recommended: a set; clustering algorithm itself is L1 design.

H4. **Federation semantics for trajectory (P8 / I8).** Does child
    substrate inherit parent's trajectory at spawn? Per §C4 spore-
    schema = appetite + sporocarp-type + SSoT only → trajectory
    does NOT transfer; child begins its own.

H5. **Immune-system coupling.** Trajectory showing wandering (no
    convergent direction) is a homeostatic signal — what dim grade?
    Threshold from substrate observatory (per C6.4).

H6. **Schema-evolution trajectory invalidation.** When L1 mutates
    (vocabulary refactor, dispatch-form change), historical DAG ops
    may have predicates no longer in the type tree. Recommended:
    each L1 mutation creates a new **trajectory epoch**; queries
    can span or stay within an epoch.

---

## §I. L1 design questions catalog (cross-section roll-up)

Total: 38 specific L1 design questions surfaced by L0 v0.3.
Categorized:

- **Continuity (§A)**: A1-A3 (3 questions)
- **Tropism (§B)**: B1-B10 (10 questions)
- **Schema (§C)**: C1-C5 (5 questions)
- **Governance (§D)**: D1-D4 (4 questions)
- **Skin (§E)**: E1-E5 (5 questions)
- **Lifecycle (§F)**: F1-F4 (4 questions)
- **Hard rules (§G)**: G1-G7 (7 questions / proposed rules)
- **Trajectory (§H)**: H1-H6 (6 questions)

= 44 leaf design hooks (some overlap; net distinct ≈ 38).

L1 drafting proceeds section by section. Each section's outputs
become an L1 sub-document. The aggregate is L1 v0.1.

---

## §J. Open: should L1 be one document or many?

v0.8 L1 was 4 files (`protocol.md`, `canon_schema.md`, `exit_codes.md`,
plus 1 cross-cut). v0.9 has 8 substantive areas (§A-§H) plus the rule
catalog (§G). The right count is L1 drafting's first decision.

Recommended (open):
- One `L1_VISION.md` (this outline's sealed successor — the L1
  charter, what L1 does and does not commit to).
- One `L1_TROPISM.md` (§B — the bulk of the operational design).
- One `L1_SCHEMA.md` (§C + §E — SSoT + skin).
- One `L1_GOVERNANCE.md` (§D + §F — classifier + lifecycle).
- One `L1_TRAJECTORY.md` (§H — derived view spec).
- One `L1_HARD_RULES.md` (§G — the rule catalog).
- One `L1_CONTINUITY.md` (§A — the resume + dormancy spec).

= 7 L1 docs total. Cross-referenced. Owner can review each section
separately.
