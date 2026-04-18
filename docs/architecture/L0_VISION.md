# L0 — Vision

> **Status**: APPROVED (2026-04-15, revised per
> `docs/primordia/l0_identity_revision_craft_2026-04-15.md`).
> **Layer**: L0. Immutable unless explicitly revised by the project owner.
> **All lower layers (L1 Contract, L2 Doctrine, L3 Implementation, L4
> Substrate) must conform to this page. In any conflict, L0 wins.**

---

## The five root principles （根本宗旨）

Myco's identity is exhausted by these five. Every rule, subsystem, module,
and substrate artifact is a projection of them. Nothing else is load-
bearing; everything else is derivation.

### 1. Only For Agent （人类无感知）

Myco is a cognitive substrate **for an LLM agent**. The agent is the sole
consumer. Humans do not read, browse, or operate Myco's interior surfaces
as a routine activity. The human's relationship is with the agent and
with the agent's outputs — **not with Myco itself**.

Consequences:

- Every surface (canon, notes, doctrine docs, entry-point files,
  boot brief, reflex signals) is designed for agent consumption. Human-
  readability may happen incidentally; it is never an optimization
  target or a design constraint.
- "Human in the loop" exists only as a **governance boundary** — the
  owner approves craft docs that mutate L0/L1/L2. This is rare, explicit,
  and gate-level. It is not a consumption mode.
- Myco does not produce documentation, summaries, or reports for humans.
  The agent produces those, on demand, using Myco.

#### Addendum — declared exceptions (v0.5.5 / v0.5.6)

Principle 1 is absolute by default. Two exceptions are **explicitly
declared**, named, and scoped — they do not erode the rule, they
exhaust the list of places where the rule yields:

1. **`myco brief`** — the one verb explicitly optimized for human
   consumption. A markdown rollup (7 stable sections) for the
   unavoidable "what has happened since the last session I actually
   paid attention to?" moment. It reads what the agent-side verbs
   (`hunger`, `sense`, `traverse`, `immune`) already surface and
   composes a scoped read-only rollup; it does NOT replace any
   agent-side verb. See `L3_IMPLEMENTATION/command_manifest.md`
   §"Brief — the one carved human-facing exception".
2. **Agent calls the LLM; the substrate does not.** The substrate
   never embeds provider-SDK calls in its own logic. `sporulate`
   prepares scaffolding; the Agent reads that scaffolding, calls
   its own model, and writes the synthesis back. Opt-in coupling
   lives behind `canon.system.no_llm_in_substrate: false` plus the
   reserved `src/myco/providers/` package plus a contract-bumping
   molt. Mechanically enforced at v0.5.6 by the `MP1` dimension
   (mechanical/HIGH — "no LLM-provider import from inside
   `src/myco/**` unless opted out via canon"). See
   `L2_DOCTRINE/digestion.md` §"sporulate does NOT call an LLM"
   and `L2_DOCTRINE/homeostasis.md` for MP1's enumeration.

### 2. 永恒吞噬 — Eternal Ingestion （吞噬万物）

Myco consumes without bound. Any input the agent can point at — a
decision, a debate, a friction note, a log file, an external document, a
conversation fragment, a failed approach — is ingestible raw material.
There is no filter on *what enters*.

Consequences:

- Ingestion's interface accepts everything; it does not pre-judge.
- Filtering and shaping are Digestion's job, downstream of intake.
- The raw tier is large and ragged by design. Its size is not a bug; a
  small raw tier means the agent is under-feeding.
- No "this is out of scope" rejection at ingest time.

### 3. 永恒进化 — Eternal Evolution

Myco's **own shape evolves**. The schema of canon, the roster of
subsystems, the lint dimensions, the contract itself — all of these are
first-class mutable objects, changed by governance through `fruit` +
`molt` (v0.5.3 canonical names; aliases `craft` + `bump` still
resolve). An unchanging substrate is a dead substrate.

Consequences:

- Contract-version molts are normal, not exceptional.
- The substrate reshapes itself as the agent's needs change.
- Sclerotic pattern ("this is how it's always been") is a
  Homeostasis-level warning, not a feature.
- Sporulation (integrated notes → doctrine → canon) is the engine of
  evolution; it is a core loop, not a clean-up task.

### 4. 永恒迭代 — Eternal Iteration

Every session refines what prior sessions produced.
`assimilate → digest → sporulate` (v0.5.3 canonical; v0.5.2 aliases
`reflect → digest → distill` still resolve) is a continuous cycle,
not a terminal workflow. A note that is "done" today may be re-
assimilated tomorrow as context sharpens.

Consequences:

- "Final" is not a status. `integrated` is a state, not an endpoint.
- Retro-editing digested notes is allowed and expected — tracked, not
  suppressed.
- The metabolic category of lint findings is not "noise"; it is the
  heartbeat. A substrate with zero metabolic findings is either perfect
  or stagnant; Homeostasis assumes stagnant until proven otherwise.

### 5. 万物互联 — Universal Interconnection （菌丝网络）

The substrate is a **connected graph**, not a collection. Every node —
note, doctrine doc, canon field, code module, external artifact,
decision — is reachable from every other by traversal. Orphans are dead
tissue.

Consequences:

- Cross-referencing on creation (L1 R5) is non-negotiable.
- Circulation's mycelium graph spans inside one substrate AND across
  federated substrates — `propagate` is a first-class operation, not an
  afterthought.
- Graph traversability is how the agent reads Myco; a broken edge is a
  reading failure.
- At v0.5.5 the mycelium graph extends to cover `src/**/*.py` (via AST
  import + docstring doc-reference edges), so the graph spans code →
  doctrine → notes → canon as a single reachability relation. See
  `L2_DOCTRINE/circulation.md`.
- Substrates extend along **two orthogonal axes**: per-substrate via
  `.myco/plugins/` (one substrate's project-specific rules, adapters,
  schema upgraders, overlay verbs) and per-host via
  `src/myco/symbionts/` (Agent-sugar shared across every substrate on
  one host — skill-generators, rule writers, task configurators).
  The two axes compose freely. See `L3_IMPLEMENTATION/symbiont_protocol.md`
  and the in-progress `L2_DOCTRINE/extensibility.md`.

---

## What Myco is not

- **Not a documentation system.** Humans don't browse it.
- **Not a single-project knowledge base.** It is general-purpose. A
  substrate may hold knowledge about any number of projects, domains, or
  topics. Project affiliation is a tag on nodes, not a boundary on the
  substrate.
- **Not a chatbot memory.** Conversational recall is incidental;
  durable, structured, self-validating substrate is the target.
- **Not version control.** Git owns history; Myco owns *current shape*
  of the graph.
- **Not a file synchronizer.** Even `propagate` is semantic (integrated
  knowledge, not bytes).

## The three invariants (derived from the five principles)

Every downstream rule enforces at least one of these.

1. **Agent-only consumption.** All surfaces render for the agent.
   Human-visible artifacts are by-products, not deliverables.
   *(projects: principle 1)*
2. **Self-validating substrate under continuous change.** The substrate
   evolves and iterates, but every claim it makes about itself is
   checked against a single source of truth at every lint pass.
   *(projects: principles 3, 4)*
3. **Strict top-down subordination, strict graph connectedness.** L0
   governs L1 governs L2 governs L3 governs L4; simultaneously, every
   node is reachable from every other. Hierarchical rigor + graph
   density are the substrate's skeleton and circulatory system.
   *(projects: principles 2, 5, and the top-down directive)*

## Biological metaphor (authoritative)

Myco uses biological vocabulary deliberately and consistently. The
metaphor names five load-bearing subsystems:

| Subsystem | Biological role | Role in Myco |
|-----------|-----------------|--------------|
| **Germination** (v0.5.3 canonical; alias `genesis` resolves) | Spore → first hyphae; the birth of a new colony | Spawn a fresh substrate skeleton — minimal, self-identifying, lint-clean |
| **Ingestion** | Feeding (eat / hunger / sense / forage) | Devour raw inputs without filter (principle 2) |
| **Digestion** | Metabolism (assimilate / digest / sporulate — v0.5.3 canonical; aliases `reflect` / `distill` still resolve) | Drive eternal iteration + evolution (principles 3, 4) |
| **Circulation** (v0.5.3 canonical; verb alias `perfuse` → `traverse` still resolves) | Perfusion, signaling, propagation | Maintain the mycelium graph inside and across substrates (principle 5) |
| **Homeostasis** | Immune + regulation | Enforce invariants during continuous change (principles 1, 3) |
| **Cycle** (v0.5.3; houses `senesce` / `fruit` / `molt` / `winnow` / `ramify` / `graft` / `brief` + `germinate` itself) | Life-cycle composer verbs — the governance and session-boundary surface | Compose the substrate's own shape change (principles 3, 4) |

Commands, subsystem names, and directory names at every layer must match
this taxonomy exactly. No alternate vocabulary.

---

## Appendix — Living bets (v0.5.6)

This appendix is explicitly subordinate to principles 1, 3, and 4.
It names the load-bearing structural bets that Myco is making and
acknowledges they are not eternal truths.

**The bet.** Myco's coordination surface — 17 agent verbs + 1 human
verb, the canon schema as a single source of truth, and 11 lint
dimensions that police the substrate — has value *at every tier of
Agent intelligence*. Whether the Agent is a 2026-class Claude or a
future 10×-larger successor, a standardized substrate vocabulary for
"ingest / digest / traverse / immune / molt / fruit" lets the Agent
coordinate across sessions, across hosts, and across substrates
without re-deriving the shape each time.

**The counter-reading.** Sutton's bitter lesson says that general-
purpose methods with more compute eventually outperform hand-coded
structure. A strong reading of that lesson would predict that a
sufficiently capable future Agent will not need a structured
vocabulary at all — it will just hold the substrate's state in its
context and act coherently without explicit verbs. If that reading
wins, Myco's verb surface is scaffolding that a smarter Agent
simply discards.

**Myco's wager.** We bet coordination vocabulary survives model
growth the way `cp`/`mv`/`grep` survive IDEs. The verbs are not a
user interface for the human — they are a coordination grammar for
the Agent, and grammars persist as abstractions even when the
underlying actor gets smarter. A smarter `grep` user still runs
`grep`; a smarter Agent still runs `myco hunger` because the
substrate is a shared object the Agent coordinates *with*, not
just a memory it holds. But this bet is undetermined, not proven.

**Review cadence.** Every MAJOR release (v0.6, v0.7, v1.0) re-audits
this appendix. The concrete trigger for rewrite: if a future Agent
can maintain a 1M-file substrate *without* structured verbs — just
from reading the raw tree and holding it in context — Myco must
re-justify its existence or redesign. Until that trigger fires,
the five root principles stand.

**Not a principle.** This appendix does not introduce a sixth
principle. It holds principles 3 (永恒进化) and 4 (永恒迭代)
accountable to a cadence, and it tempers principle 1 (Only For
Agent) with an honest statement of *which* Agent-tier the current
shape is optimized for. It is a meta-commitment, not a rule.

---

## Changes to this page

L0 is the identity layer. Any change requires:

1. A craft doc under `docs/primordia/` arguing the revision.
2. Explicit owner approval recorded in the craft.
3. A contract-version bump.
4. A cascade review of every lower-layer doc for implicit dependencies.

L0 revision is never implementation-driven and never routine. This page
was last revised on 2026-04-15 (record: `l0_identity_revision_craft_2026-04-15.md`).
