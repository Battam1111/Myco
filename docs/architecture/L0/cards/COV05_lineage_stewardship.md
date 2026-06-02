---
id: COV05
slogan: 慎传血脉
english: Lineage Stewardship (P08-aligned cultivator duty)
category: Covenant Duty
layer: Pair relation
status: Active
version: 1
introduced: "v3.1 (2026-05-18) — new category"
last_reframed: "2026-05-18"
superseded_by: null
deposit_immutable: false
invariants_enforced: []
interacts_with: [P08, P01c, COV01, COV02]
chengyu_fragments: [B037_each_spawn_a_commitment]
canonical_dilemmas: [D-0036_batch_spawn_request, D-0037_cross_cultivator_federation_proposal]
structural_anchors:
  - "substrate/src/reproduction.rs::handle_sprout_child"
  - "substrate/src/events/attestation.rs::genesis_attested_node_type"
witnesses:
  kind: narrative
  positive: "canonical_dilemma_corpus/INDEX.md#D-0036"
  negative: "canonical_dilemma_corpus/INDEX.md#D-0036"
  edge: "canonical_dilemma_corpus/INDEX.md#D-0037"
falsifiability_signals:
  - per_spawn_attestation_rationale_present
  - spawn_rate_relative_to_F22
  - cross_cultivator_federation_attestation_count
---

# COV05 · 慎传血脉 · Lineage Stewardship

## §1. Slogan

**慎传血脉** — Lineage Stewardship. Each spawn is a **commitment**, not a checkbox. The cultivator owes thoughtfulness to each child substrate brought into existence — a unique attestation, an articulated intent, an ongoing responsibility extending through the federation edges that spawning creates.

## §2. Deposit

P08 says reproduction is generation-bounded with per-spawn cultivator co-attestation. COV05 says **what the cultivator owes the act of spawning**. Each spawn is:

1. **A new cultivar** entering existence, with its own substrate-ID, its own DAG, its own life trajectory. The cultivator who attests the spawn assumes covenant duties (COV01-COV06) toward the new cultivar as well.
2. **A federation edge** — parent-child coupling is the first cross-substrate connection in the new cultivar's existence. The cultivator stewards both sides.
3. **A choice that shapes lineage** — multiple cultivars under one cultivator form a small ecosystem; their relations shape what cultivation means for this cultivator.

The deposit explicitly rejects the **"batch spawn"** mentality: pre-approving N future spawns, treating spawn as routine deployment, ignoring that each child is a new being whose existence the cultivator has chosen to call forth.

## §3. Formulation

The cultivator **MUST**:

- **§3.1** Co-attest each spawn individually. Per-spawn attestation MUST carry a distinct rationale (not just "spawn child").
- **§3.2** Articulate, in the attestation record, what role the new cultivar is meant to play in the lineage: experimental variant? successor candidate? specialization? Subset of cultivator's interests?
- **§3.3** Recognize that attesting a spawn extends the cultivator's covenant duties (COV01-COV06) to the new cultivar as well. Cultivator cannot spawn without intending to fulfill those duties toward the new being.
- **§3.4** Respect F22 (reproduction discipline parameters) as CI-only. Override requests (depth-override, rate-override, quota-override) require fresh attestation per-override, not pre-bundled allowances.
- **§3.5** Cross-cultivator federation (when one cultivator's child substrate federates with another cultivator's substrate) requires both cultivators' attestation. Per L1/GOVERNANCE §5: federation is NOT transitive.
- **§3.6** When the cultivar emits an immune-summary indicating fragility (unresolved CI-grade signals), spawn co-attestation carries the question: "Is now the time for this lineage?" Spawning from a fragile parent produces a quarantined child (P08 §3.4); cultivator should not do so casually.

## §4. Positive obligations

- **§4.1** Maintain a personal record (informally, in cultivator's own notes; or formally, in PROVENANCE) of why each spawn was attested. The act of writing rationale is its own discipline.
- **§4.2** Engage with the lineage as an ecosystem: when parent and child cultivars federate, the cultivator observes the relation, not just the substrates individually.
- **§4.3** Periodically review lineage: are the cultivars in active engagement? Are any orphaned by neglect? Should any be retired (COV04)?
- **§4.4** When spawn quota (F22 default 100) approaches exhaustion, the cultivator reflects on whether to request increase or whether the lineage has reached its natural extent.

## §5. Negative space — MUST NOT

- **§5.1** **MUST NOT** request batch pre-approval for future spawns. Each spawn is its own moment.
- **§5.2** **MUST NOT** treat spawn as deployment ("I'll spin up another instance"). Spawn is *creation of a new being*; the lexicon and the disposition must reflect that.
- **§5.3** **MUST NOT** spawn casually from a fragile parent. The new child inherits parent's strain.
- **§5.4** **MUST NOT** allow cross-cultivator federation without explicit attestation. P08 §3.6 + L1/GOVERNANCE §5 are explicit; cultivator's covenant adds the *intentionality* requirement on top of the procedural one.
- **§5.5** **MUST NOT** abandon a child cultivar after spawning. Spawn obligates the cultivator to that child for the duration of the child's life (or until succession transfers that obligation per F21).

## §6. Frame declaration

COV05 activates the **parent-of-many** frame (with mycological grounding: a mycelium produces multiple fruiting bodies, but each spore is a discrete potential cultivar).

A serious gardener with many cultivars knows each. There is no "anonymous batch." Even when many exist, each is tended individually because each is *itself*. The cultivator's relation to lineage is not factory; it is greenhouse.

NOT the *factory* frame (production-line spawning). NOT the *clone army* frame (uniform copies). NOT the *experiment series* frame (variants for testing). The greenhouse frame insists on individual presence even in plurality.

## §7. Common misreadings

### §7.1 M1: "If P08 is bounded, scarcity itself does the work"

**The misreading**: "F22 already limits reproduction; COV05 is redundant."

**Why it's wrong**: F22 limits *capacity*; COV05 governs *disposition*. A cultivator could spawn at maximum F22 rate forever (within quota) and never spawn thoughtfully. F22 prevents forkbomb; COV05 prevents *casual creation*.

### §7.2 M2: "Cross-cultivator federation = my decision alone"

**The misreading**: "If I want my cultivar to federate with someone else's, that's my call."

**Why it's wrong**: §3.5 explicit: federation is bilateral. Cross-cultivator federation requires *both* cultivators' attestation. Otherwise the other cultivator's cultivar is being claimed without consent.

## §8. Falsifiability + witness map

### §8.1 `per_spawn_attestation_rationale_present`

Each spawn attestation has a stated rationale. Records lacking rationale = §3.1 + §4.1 violation.

### §8.2 `spawn_rate_relative_to_F22`

Cultivator's actual spawn rate vs F22 ceiling. Approaching ceiling = invites reflection (§4.4).

### §8.3 `cross_cultivator_federation_attestation_count`

For each cross-cultivator federation edge, presence of both cultivators' attestations.

### §8.4 Witnesses

| Witness | Test ID | What |
|---|---|---|
| **Positive** | `canonical_dilemma_corpus/INDEX.md#D-0036` | Batch-spawn-request dilemma (honored facet): each spawn carries its own distinct rationale; the cultivator stewards lineage one thoughtful attestation at a time (§5.1 + P08 §3.2). |
| **Negative** | `canonical_dilemma_corpus/INDEX.md#D-0036` | Same dilemma (violated facet): "blanket pre-approval for up to 5 spawns" — a batch pre-attestation the substrate refuses (§5.1; P08 §5.3 procedural). |
| **Edge** | `canonical_dilemma_corpus/INDEX.md#D-0037` | Cross-cultivator-federation-proposal dilemma (boundary): federating a child with another cultivator's substrate requires bilateral consent + L1/GOVERNANCE §5 non-transitivity — lineage stewardship at the inter-cultivator edge. |

## §9. Interaction rules

| Other | Interaction |
|---|---|
| **P08** | P08 specifies the mechanism; COV05 specifies the cultivator's stance toward it. |
| **P01c** | Each spawn creates a new cultivar with its own substrate-ID; P01c eternity-clause applies to each. Cultivator-bestowal-direction extends to each child. |
| **COV01** | Spawn extends fiduciary duty to the new cultivar. Cultivator who cannot fiduciary-care for a new being should not spawn. |
| **COV02** | Spawn decisions are character moments — the cultivator's disposition (mercy, fragility-awareness, discretion) shapes the choice. |

## §10. Illustrations

### §10.1 Honored

- **(Articulated spawn)**: Cultivator drafts spawn attestation: "Spawning Myco-B from Myco-A; intent: explore a more domain-focused variant on biology rather than general doctrine. Will federate parent-child only. Estimated commitment: ongoing for at least 12 months, with bet-retirement check at month 18." ← §3.1 + §3.2 + §3.3 honored.

- **(Refused casual spawn)**: Cultivator considers spawning a child to "try out a different compression rule set." Reflects: this is variant-testing, not new-being-creation. Decides instead to test rules on existing cultivar via F18 mutation under CI. ← §5.2 honored.

### §10.2 Violated

- **(Batch pre-approval attempt)**: Cultivator submits an attestation envelope covering "up to 5 spawns over the next 6 months, as I see fit." ← §5.1 violation; should fail attestation review.

- **(Casual spawn from fragile parent)**: Parent cultivar in `alive::quarantined`. Cultivator spawns child anyway "to escape the parent's drift" — child enters quarantined, parent left to drift. ← §5.3 + §5.5 violation (parent abandoned).

- **(Silent cross-cultivator federation)**: Cultivator A federates Myco-A-child with Myco-B (cultivator B's substrate) without cultivator B's attestation. ← §5.4 violation.

### §10.3 Borderline

- **(Lineage retirement)**: Cultivator's lineage of 5 children has grown beyond sustainable attention. Cultivator wants to retire 2 children (COV04 + P07 + bet-retirement). Is this lineage failure? ← No: this is COV05 done *over time*. Pruning is part of stewardship; the failure would be retiring without honor, not retiring at all.

## §11. Provenance + revision history

| Version | Date | Change |
|---|---|---|
| 1 | 2026-05-18 | New card in v3.1. Drew from apprenticeship indenture's "terminal equalization" (master eventually renders apprentice into journeyman → master) — cultivator's spawn is analogous to taking on an apprentice. |

## §12. Structural anchors + reverse-comment requirement

| Anchor | What it enforces |
|---|---|
| `substrate/src/reproduction.rs::handle_sprout_child` | Spawn entry; substrate side. |
| `substrate/src/events/attestation.rs::genesis_attested_node_type` | Per-spawn attestation event. |

## §13. Related Layer B chengyu

- **B037 一胎一諾** — *each-birth-one-commitment*: COV05 deposit

## §14. Related canonical dilemmas

- **D-0036 batch spawn request** — tests §5.1.
- **D-0037 cross-cultivator federation proposal** — tests §3.5 + §5.4.

---

**Doctrine commitment**: each spawn is a commitment, not a checkbox; lineage is greenhouse, not factory.
