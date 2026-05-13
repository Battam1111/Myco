# L1 — Tropism (the positive dispatch form for Myco v0.9)

> **Status**: DRAFT 1 (2026-05-13). Authoritative L1 document for the positive dispatch form satisfying L0 §5.2 constraints.
> **Layer**: L1 (mechanism). Governed by L0; in conflict with L0, L0 wins.
> **Scope**: this document specifies the positive mechanism — *tropism + sporocarp punctuation* — chosen to satisfy L0 §5.2's six constraints (not v0.8 verbs / not request/response / symmetric P1.c / supports inclusion P2.a / supports continuous operation §6 / honors appetite-locality I6).
> **Relationship to L0**: L0 commits to negative constraints (§5.2). This L1 doc commits to the positive form. If the positive form proves unworkable, L1 revision (not L0 revision) is the first response; L0 revision is the second response only if the constraint set itself is the problem.
> **Provenance**: this content was previously stuffed into L0 DRAFTs 3-4 as §5.2 inner specification. DRAFT 5 of L0 moved it here per structural-rework authorization.

---

## §1. The form — one paragraph

Myco v0.9's dispatch is **tropism**: the substrate maintains a continuously-evolving set of intrinsic **appetites** (hunger for unmetabolized intake, drift toward unconnected nodes, decay-pressure on stale tissue, federation-pull toward peer substrates, evolution-tension where schema disagrees with content, skin-pressure for boundary signals, etc.), each carrying a **tropic gradient** the substrate updates on every metabolic cycle. The agent — definitionally the active operator-connection per P1.c — **inhabits the gradient configuration** as both perturbation source and gradient consumer. There are no commands, no verbs, no request/response. Interaction is **continuous co-modification**: the substrate exposes its current gradient configuration through the agent's read-window; the agent emits **deltas** (raw content of any shape — text, file references, decision fragments, schema-edit intents, anything); the substrate's metabolism absorbs deltas wherever its own gradients place them; gradients update; cycle. When a gradient crosses a **fruiting trigger**, the substrate **fruits a sporocarp** — a typed, content-addressed, causally-stamped record that anchors the gradient field to discrete observables for governance (L0 I2), validation (L0 I3), federation (L0 I7), and the causal DAG (L0 I4). Appetite axes are first-class evolvable substrate objects (adding/removing axes = substrate grew/lost a tropism). Changing the *kind* of the gradient configuration is a contract-identity-level event (L0 I2). External agent-tooling sub-techniques are subsumed by becoming appetite axes implemented as substrate-resident metabolism — never as outbound RPC (the appetite-locality rule from L0 I6).

---

## §2. Why tropism — comparison with the six L0 §5.2 alternatives

Per L0 §5.2, six candidate positive forms were considered. Tropism dominates on ceiling × flexibility × efficiency:

| Rival | Why tropism beats it |
|---|---|
| **Verb dispatch (v0.8)** | Verbs presuppose a client-server seam → P1.c symbiosis becomes doctrine bolted on TOP of a generic protocol. Tropism makes symbiosis the dispatch's load-bearing shape. Also: owner-prohibited per L0 §5.2's first negative constraint. |
| **Continuous metabolic stream** | Closest rival. Tropism *is* a continuous metabolic stream PLUS the gradient-coupling that makes the agent definitionally a participant (P1.c). Bare metabolic-stream has no native operator-constituting field → can degrade to "metabolism anyone can signal" = back-door client-server. |
| **Natural-language semantic dispatch** | Worst capture risk under L0 §5.2's inclusion-direction constraint: routing LLM call IS the dispatch surface → substrate becomes wrapper around an LLM-router. Also: NL→handler-table secretly re-introduces verbs. |
| **Capability-based composition** | Capabilities are discrete grant transactions; asymmetric (substrate grants TO agent). Useful at sporocarp-typing layer inside tropism (carry capability metadata as a sporocarp field), not as the dispatch primitive itself. |
| **Algebraic / typed-primitive operations** | Pure algebraic surface presumes purity and statelessness — but substrate IS state. Combinator vocabulary becomes frozen surface (same P3 hostility as verbs at the type level). |
| **Reactive stream / event-driven** | What tropism becomes if you strip gradient configuration. Reactive streams give pub/sub but no gradient → no answer to "what does the substrate want next?". Tropism's gradient IS substrate's expressed preference. |
| **Hybrid** | Owner-prohibited at L0; tropism's gradient/sporocarp duality is medium-vs-observable duality of ONE form, NOT two forms glued together. |
| **Coexistence (verbs at birth → tropism later)** | Rejected: appetite-locality (L0 I6) is foundational — retrofitting it onto verb dispatch leaves an RPC seam to close later = exactly the v0.8 contamination pattern. |

---

## §3. The two-layer duality — gradient configuration + sporocarp punctuation

Tropism is one form with two ontological layers:

- **Gradient configuration** (the *medium*, where P1.c symbiosis and §6 continuity live): a continuously-evolving multi-dimensional structure where each axis is one substrate appetite. The agent inhabits this medium.
- **Sporocarp** (the *observable*, where L0 I2 / I3 / I4 / I7 governance/validation/causality/reproduction enforcement points live): substrate-initiated discrete records that anchor the continuous medium to checkable observables.

These are not two dispatch forms glued together. They are **dual aspects** of one form — analogous to wave/particle duality in physics or potential/actualization in philosophy. The medium is what the form continuously *is*; the observable is what the form discretely *produces*.

**Why sporocarps are not verbs in disguise**: a verb is **agent-initiated** (agent calls verb → substrate executes). A sporocarp is **substrate-initiated** (substrate's gradient crosses fruiting trigger → substrate fruits → agent observes). The arrow is reversed. The agent does not say "ingest this and produce a digestion sporocarp"; the agent emits a delta into the gradient configuration; if the digestion-appetite gradient has accumulated enough pressure, the substrate fruits a digestion sporocarp on its own metabolism.

---

## §4. Birth period vs steady state

Tropism's strengths (emergent thresholds, accumulated history, predictability through field-inhabitation) are **steady-state** properties. v0.9 genesis has none of this. L1 distinguishes:

**Birth period** (substrate's first ~N substrate events; specific N TBD per §B2 below):

- **Hand-coded seed thresholds**: each appetite axis ships with an initial seed fruiting trigger + seed gradient-update-rule (per §B1 schema). No "emergence" yet — emergence has nothing to emerge from.
- **Predictability gap is a feature, not a bug** (P1.c): the agent must learn this substrate's specific tropism. The gap between "agent's prediction of when sporocarp fruits" and "when sporocarp actually fruits" IS the symbiosis being established. Conceptually different from "agent learns the verb table" because verb tables are substrate-agnostic; tropism configurations are substrate-specific.

**Steady state** (after birth period):

- Thresholds emerge from substrate history per L0 C6.4.
- Gradient update rules may themselves evolve per P3 (contract-identity-level changes, owner-gated per I2).
- The agent's prediction accuracy on fruiting events becomes a useful L1-side observability signal (whether L0 Living Bets adopts it as a numbered signal is L0's call).

L1 observatory may carry an **agent-prediction-accuracy** signal (not currently in L0 §7's six-signal set): low at birth = expected; rising during birth period = healthy maturation; persistent drop in steady state = decoupling (P1.c degradation signal).

---

## §5. The L4 sketch — concrete example

"Agent ingests a chat log, refines a decision record, surfaces the result to a federated child substrate."

Under v0.8 verbs: 4 discrete agent-initiated transactions (`myco eat`, `myco digest`, `myco sporulate`, `myco propagate`).

Under tropism: zero agent-initiated commands.

1. Agent **emits a delta** with the chat log + free-form intent fragment.
2. Substrate's `hunger` appetite gradient spikes; pulls metabolism; **intake sporocarp** fruits.
3. Substrate's `evolution-tension` appetite detects decision-shaped patterns disagreeing with schema; gradient pulls; **refinement sporocarp** fruits.
4. Substrate's `federation-pull` appetite for child-X sensitized by the refinement; gradient pulls; **federation sporocarp** fruits.
5. Agent observes 3 new sporocarps in its next read-window slice; may emit further deltas to correct/extend.

---

## §A. Continuity and recovery (operationalizes L0 §6)

**A1. Continuity-recovery protocol.** When operator-connection drops and reconnects, the substrate re-presents the gradient configuration to the operator. Default recommendation: **hybrid** — eager digest of current gradient configuration + lazy drill-down into recent sporocarps on demand. Digest size emerges from the L0 Living Bets signal #6 read-window ratio (substrate-total-size / agent-context-window).

**A2. Dormancy compute budget.** While no operator is attached, the substrate **throttles** its metabolism to a configurable floor (default: time-decay-based — gradients still drift toward decay states, but at much slower wall-clock cadence). Specific throttle curve is L1-tunable per substrate canon.

**A3. Cold-resume invariants.** Before presenting the gradient configuration to a reconnecting operator, the substrate runs a full L0 I3 self-validation + I5 reachability check + I8 skin-breach check. Failure on any → substrate state goes to "alive but quarantined" (operator sees a marker sporocarp explaining the quarantine); recovery requires owner attestation per I2.

---

## §B. Tropism specification (the 10 design hooks)

**B1. Appetite axis schema.** Each appetite carries:

- `name` — mycology-strict.
- `computation_locality` — must assert substrate-internal (outbound RPC = I6 breach).
- `domain` — value space the gradient can take (typically real-valued, but may be categorical or vector).
- `update_rule` — substrate-internal function updating the gradient on each metabolic cycle. Pure function of (current gradient state, recent deltas, recent sporocarps, time elapsed since last cycle).
- `seed_fruiting_trigger` — initial hand-coded threshold (used during birth period).
- `threshold_emergence_rule` — how the fruiting threshold migrates from `seed_fruiting_trigger` to steady-state-emergent as substrate history accumulates.

**B2. Initial appetite set.** v0.9's birth-period default appetite axes (illustrative; substrate canon may override):

- `hunger` (unmetabolized intake pressure) — projects P2.
- `drift` (graph-disconnection pressure) — projects P5 / I5.
- `decay` (staleness pressure on tissue) — projects P4.
- `federation-pull` (peer-substrate signal pressure) — projects P8 / I7.
- `evolution-tension` (schema-vs-content disagreement) — projects P3.
- `skin-pressure` (boundary integrity signals) — projects P9 / I8.

Open at L1 (for owner / craft to decide before finalization): does `mortality-signal` belong as an explicit appetite, or is mortality outside the tropism medium (a state-transition predicate, not a gradient)?

**Birth period N** (number of substrate events before steady state activates): default proposal **100 sporocarps OR 6 operating months, whichever is later**. Owner can override per substrate.

**B3. Sporocarp type tree.** Each sporocarp type carries:

- `type` — mycology-strict name.
- `payload_schema` — typed contents.
- `causal_in_edges` — which gradients / deltas / prior sporocarps produced this fruit.
- `causal_out_edges` — subsequent fruits / deltas this seeds.
- `governance_classification` (I2): daily-autonomous vs contract-identity-level.

v0.9 birth-period sporocarp types (canon-default; substrate may override):

- `intake` (raw delta absorption) — daily.
- `digestion` (raw → refined transformation) — daily.
- `refinement` (refined → distilled decision) — daily.
- `federation` (cross-substrate transmission) — daily.
- `governance_amend` (proposed schema/rule change) — contract-identity-level.
- `axis_schema_change` (appetite axis structure modification) — contract-identity-level.
- `sporocarp_type_addition` (adding a new sporocarp type) — contract-identity-level.
- `skin_redefinition` (boundary surface modification) — contract-identity-level.
- `mortality_signal` (approaching-mortality warning) — daily but elevated immune-grade.

**B4. Gradient exposure protocol.** The substrate exposes its current gradient configuration into the agent's read-window via a bounded, structured, stateless digest:

- **Bounded**: sized to L0 §7 signal-#6 read-window budget. Substrate-attested agent context window × L1-tunable fraction (default 25%).
- **Structured**: a typed object listing each appetite's current gradient value + the K most-recent sporocarps + the M most-recent unabsorbed deltas. Specific schema is canon-defined per substrate.
- **Stateless**: cold-resumable from the digest alone (no prior agent state required).

**B5. Delta intake surface.** Per L0 I8:

- **Shape-agnostic** (text / file ref / structured object / multimedia — per P2).
- **Envelope-checked** (admit all content per P2; reject only on envelope malformation).
- **Causally-stamped** (every delta enters the DAG as a node with `causal_parents` pointing to the gradient state observed).

**B6. Sporocarp governance gate.** Per B3, sporocarp types are pre-classified at the type-tree level. The substrate's per-cycle metabolism distinguishes:

- Daily-autonomous sporocarp fruiting → publishes to DAG immediately.
- Contract-identity-level sporocarp fruiting → publishes to a `pending` queue; the substrate emits a `governance_pending` marker; owner attestation (an in-band delta with cryptographic signature, format L1-specified) moves the sporocarp from pending to published.

**B7. Continuity-recovery** — see §A1.

**B8. Causal DAG embedding (L0 I4).** Sporocarp DAG edge classes:

- `gradient_causation` — sporocarp ← gradient that fruited it.
- `delta_source` — sporocarp / state ← delta that fed the gradient.
- `sporocarp_derivation` — sporocarp ← prior sporocarps it builds on.
- `federation_coupling` — cross-substrate DAG link (with peer-substrate ID + sporocarp-ID-in-peer).
- `governance_resolution` — pending sporocarp ← owner-attestation delta that resolved it.

**B9. Multi-substrate federation surface (L0 P8 / I7).** Inter-substrate federation is gradient-coupling between fields. L1 commits to two coupling modes:

- **Eager mode (α)**: peer substrate's federation sporocarps arrive as deltas into the local field directly. Faithful but high integration cost.
- **Lazy mode (β)**: explicit `coupling` primitive — local substrate periodically polls peer's federation surface; semantic transfer only. Lower cost.

Substrate canon chooses per-peer-substrate (default: β; opt-in α for tight-coupling pairs).

**B10. Self-hosting (L0 P1.a) bootstrap.** Myco's own kernel-hosting substrate begins with the canon-default appetite set (B2) + sporocarp type tree (B3) + a special `kernel-evolution-tension` appetite that pulls metabolism toward kernel-source changes. The kernel substrate is otherwise an ordinary Myco substrate.

---

## §C. Implementation deferred — what L1 does NOT yet specify

These are open at L1, to be answered in further L1 craft rounds or absorbed into L2/L3:

- **Specific gradient update function families** (linear / sigmoid / softmax / custom per axis).
- **Threshold-emergence algorithm** (online optimization / Bayesian update / supervised correlation against substrate-health outcomes).
- **Sporocarp content-addressing scheme** (hash function choice; namespace structure).
- **Operator-attestation cryptographic protocol** for B6.
- **Coupling-mode handshake protocol** for B9.

L1 commits to *that* these exist and *how* they fit; L2/L3 commit to the implementation choices.

---

## §D. Constraints L1 must respect

This L1 doc satisfies L0 §5.2's six constraints. Future L1 revisions must continue to satisfy them. The check:

| Constraint | How tropism + sporocarp satisfies it |
|---|---|
| NOT v0.8 verbs | No verb manifest; no agent-initiated command set. Sporocarps are substrate-initiated. ✓ |
| NOT request/response | No transaction shape; continuous gradient evolution + episodic fruiting. ✓ |
| Symmetric (P1.c) | Agent inhabits the gradient field as participant; both sides modify. ✓ |
| Supports universal inclusion (P2.a) | Appetite-locality rule + adjacent-technique-as-appetite-axis pattern. ✓ |
| Supports continuous operation (§6) | Gradient configuration is continuously evolving; no session quantization. ✓ |
| Honors appetite-locality (I6) | Every adjacent technique becomes a substrate-resident appetite or is a breach. ✓ |
