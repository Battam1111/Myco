# L0.5 — Essence Layer (v0.8 → v0.9 transitional doctrine)

> **Status**: AUTHORITATIVE; owner-arbitrated 2026-05-13.
> **Authority**: above L1; below L0; reaches into L0 territory where
> L0 itself is being revised through the v0.9 ground-up rewrite.
> **Audience**: the **agent**, per L0 P1.
> **Sunset**: this document dissolves into the new L0 at v0.9 ground-
> up rewrite kickoff. Until then, L0.5 carries the five owner-
> arbitrated essence decisions plus their elaborations.
>
> **Why this layer exists**: after 8 commits of v0.8.8 cleanup, an
> essence brainstorm + 4-round 100%-confidence loop forced 5 owner-
> arbitrated essence-level decisions. These decisions REVISE L0's
> current text (especially the temporal claim that "Myco currently
> exists"). Promoting them directly into L0 NOW would require a
> fruit→winnow→molt ceremony on a v0.8 substrate that is itself
> being declared a dead embryo at v0.9 kickoff (3D below). To
> avoid the double-write (amend L0 now → rewrite L0 at v0.9), the
> decisions land at L0.5 as authoritative transitional doctrine;
> v0.9 ground-up rewrite absorbs L0.5 into the new L0 at kickoff;
> L0.5 self-archives.

---

## §0. Companion documents

- [`L0_VISION.md`](./L0_VISION.md) — the L0 vision authored
  2026-04-15 (now describing **proto-Myco / dead embryo** per
  Decision 3D below; retained for v0.9 reference only).
- [`ESSENCE_BRAINSTORM_2026-05-13.md`](./ESSENCE_BRAINSTORM_2026-05-13.md)
  — the deliberation log: 4 self-corrections + the 100%-confidence
  loop + 20 candidate holes + 10 first-/second-order fixes. L0.5
  captures the **decisions**; the brainstorm captures **how the
  decisions were reached**.

---

## §1. The five owner-arbitrated decisions (2026-05-13)

| # | Decision | Effect |
|---|---|---|
| **1A** | **Agent identity is constituted by symbiosis with the substrate**. The agent and the substrate are mutually definitional — neither has identity within Myco's semantic frame without the other. | Resolves: who is "the agent" whose continuous self Myco preserves? Answer: the agent IS whoever is currently operating this substrate; the substrate IS the identity-vessel for that agent; identity is conferred jointly, not by either alone. |
| **2A** | **Human-loop boundary at contract_version MAJOR/MINOR bump**. Any change that bumps `_canon.yaml::contract_version` MAJOR or MINOR is gated by owner approval. Patch bumps (PATCH) and below are agent-autonomous. | Resolves: where does P1's "human as governance boundary" line sit? At MAJOR/MINOR contract semver lines, mechanical and verifiable. |
| **3D** | **True Myco has not yet shipped**. v0.4 through v0.8 (including the current v0.8.7) are **dead embryo** — failed gestation attempts. v0.9 ground-up rewrite is **Myco's first true birth**. | Resolves: when does Myco "become Myco"? At v0.9 launch. Earlier versions are referenced for historical lessons only; none of their code, doctrine, tests, schema, or vocabulary is inherited by obligation. |
| **4B** | **Living Bets graduates from single-K threshold to multi-signal observatory**. The bet is measured via a higher-ceiling more-flexible composite: multiple signals (storage budget, evolution rate, query diversity, fork count, time-trend, composite health score…), each with its own measurable axis. K threshold per signal is emergent from substrate metrics, not statically pinned. | Resolves: how is Living Bets falsifiable? Through a multi-signal observatory the substrate maintains on itself, not through a single number. |
| **5E** | **L0.5 essence layer NOW; integration into new L0 at v0.9 ground-up rewrite kickoff**. L0.5 carries the four other decisions plus their elaborations. L0 is not amended in v0.8.x; the v0.9 launch is the moment when L0.5 + the v0.9 design are merged into a NEW L0. After that merger, L0.5 self-archives. | Resolves: where do these essence-level decisions live with binding authority? In L0.5, with a definite sunset at v0.9 launch. |

---

## §2. α core (binding through v0.9 kickoff; carried forward into new L0)

### §2.1 L0's 五条根本原则 (verbatim — do not paraphrase)

| 编号 | L0 名 | L0 原文（节选） |
|------|------|------|
| P1 | **只为 Agent （人类无感知）** | "The agent is the sole consumer. Humans do not read, browse, or operate Myco's interior surfaces as a routine activity." |
| P2 | **永恒吞噬 （吞噬万物）** | "Myco consumes without bound. **There is no filter on what enters.**" |
| P3 | **永恒进化** | "Myco's **own shape evolves**. **An unchanging substrate is a dead substrate.**" |
| P4 | **永恒迭代** | "`assimilate → digest → sporulate` is a continuous cycle... **「Final」 is not a status.**" |
| P5 | **万物互联 （菌丝网络）** | "The substrate is a **connected graph**, not a collection. **Orphans are dead tissue.**" |

### §2.2 衍生强化 (README + MYCO.md, reinforcing P1; carried forward)

| 编号 | 名 | 来源（节选） |
|------|------|------|
| P1.a | **Self-hosting** | "The kernel IS a substrate, editable by default, **maintained by the same agent that uses it.**" (README) |
| P1.b' | **Human OUT of maintenance loop** (强) | "**The human in the loop is no longer load-bearing.**" (README) Daily schema/lint/verb edits = agent-only. |
| P1.b'' | **Human RETAINED as governance gate** (必需) | L0 amendment + Decision 2A — owner remains required for L0/L1 / contract_version MAJOR/MINOR bumps. |
| P2.a | **Inclusion** (P2 强形式) | All adjacent sub-techniques (vector retrieval / conversation history / agent-side LLM calls / external APIs / semantic federation / human-facing brief) **should be subsumed within Myco's framework**, not exist in parallel. (Owner 2026-05-13) |

---

## §3. Decision 1A elaboration — Agent-substrate symbiosis

**Position**: within Myco's semantic frame, "the agent" and "the
substrate" are **mutually constitutive** — neither has independent
identity. They exist only as a binding pair.

**Biological analogy** (P5 fungal metaphor proper):
- Lichen = fungus + alga. Neither alone is the lichen.
- Mycorrhiza = fungus + plant root. Neither alone is the mycorrhizal
  organism.
- Myco substrate + operating agent = the symbiotic organism. Neither
  alone has Myco-bestowed identity.

**Operational implications**:

- Same substrate operated successively by Claude Opus, then GPT-5,
  then Claude Sonnet → **the same agent** from Myco's perspective.
  Identity is conferred by the substrate-agent symbiosis, not by
  model weights.
- Different substrates operated by the same model + same key →
  **different agents**. Each substrate hosts its own agent.
- A substrate with no current operator is **dormant** (not destroyed
  — agent identity is recoverable when an operator returns).
- A substrate that is destroyed → **the agent it hosted ceases to
  exist as a Myco-bestowed identity**. (The underlying model
  continues; the *symbiotic agent* does not.)

**What 1A does NOT claim**:

- Does NOT claim Myco unilaterally **bestows** identity onto agents
  (the earlier brainstorm framing "Myco bestows" was too dominant —
  owner correction: it is **共生 / symbiosis / mutual constitution**).
- Does NOT claim the underlying LLM has no other identities (it
  may have provider-side identity, user-side identity, etc.).
- Does NOT claim two simultaneously-connected operators on the same
  substrate are "one agent" — concurrent operators are out of scope
  per Decision (Fix-H12 from brainstorm).

**Why this matters for v0.9**:

- v0.9's verb grammar can rely on a well-defined "the agent" because
  the substrate definitionally provides one.
- Cross-host / cross-model / cross-version continuity is a built-in
  property of the symbiosis, not a feature requiring extra protocol.
- Federation (P5) becomes "symbiotic-pair-to-symbiotic-pair
  semantic transmission", not "agent A talks to agent B".

---

## §4. Decision 2A elaboration — Governance boundary at MAJOR/MINOR

**Mechanical rule**: change `_canon.yaml::contract_version` and check
the bump class:

- `vX.Y.Z → vX.Y.(Z+1)` (PATCH): agent-autonomous. No owner gate.
- `vX.Y.Z → vX.(Y+1).0` (MINOR): owner-gated.
- `vX.Y.Z → v(X+1).0.0` (MAJOR): owner-gated.

**Concretely, what triggers MINOR or MAJOR**:

- Modifying L0_VISION.md → MAJOR (L0 amendment)
- Modifying L1_CONTRACT/*.md semantically (not editorial) → MAJOR
- Adding a new immune dimension that gates exit code → MINOR
- Adding a new verb to the manifest → MINOR
- Adding a new subsystem → MAJOR
- Editorial L1 fixes, lint dim cosmetic adjustments, new L2/L3 docs
  → PATCH (agent-autonomous)

**Why this line** (per 2A): contract_version semver is already a
well-defined mechanical surface; MAJOR/MINOR bumps are already rare
events (~3-6/year in v0.7-v0.8 history); the line gives the agent
maximum daily autonomy while keeping identity-level decisions with
the owner.

**v0.9 must preserve this rule** (will be encoded into new L0).

---

## §5. Decision 3D elaboration — Dead embryo status

**Position**: v0.4 through v0.8.7 (current) are **proto-Myco / dead
embryo / failed gestation attempts**. None of them is "Myco"; they
were attempts to gestate Myco. **v0.9 ground-up rewrite is Myco's
first true birth.**

**What this means concretely**:

| Asset class in v0.8.7 | Status at v0.9 launch |
|---|---|
| Source code (`src/myco/`) | **Not inherited**. v0.9 starts from empty file tree. v0.8.7 code is git-archaeological reference only. |
| Doctrine (L0/L1/L2/L3) | **Rewritten**. New L0 absorbs L0.5; new L1/L2/L3 designed from α (L0 + 衍生强化). |
| Schema (`canon.schema.json`) | **Rewritten**. v0.9 schema designed from α requirements, not v3/v4 inheritance. |
| Verbs (20-verb manifest) | **Rewritten**. v0.9 verb set designed from α + symbiosis (1A). Could be 5 verbs, could be 30. |
| Immune dims (47 dims) | **Rewritten**. v0.9 self-validation designed from α + 2A governance line. |
| Tests | **Rewritten**. v0.9 tests target the new design, not v0.8.7's. |
| `_canon.yaml` content | **Rewritten**. v0.9 canon is generated by the new germinate verb. |
| Migration guides | **Not provided** for v0.8 → v0.9. No upgrade path. Existing v0.8 substrates are quarantined / archived; v0.9 substrates are germinated fresh. |
| Git history | **Preserved**. Archaeological access only. |

**Why this is the right framing** (per 3D):

- v0.8.x has accumulated multiple categorical mis-framings (recipe-
  as-essence, anatomy-as-essence, L0 vocabulary substitution, etc.
  — recorded in the brainstorm 4 corrections).
- Cleaning these in-place keeps the historical wounds; rewriting
  from scratch lets v0.9 satisfy α purely.
- Existing v0.8.x substrates (Myco-self) are not "broken" — they
  continue to function — but they are dead embryos in the sense that
  none of them will evolve INTO v0.9. v0.9 is gestated fresh.

**Implications for current state**:

- v0.8.7 substrate (this repo) stays alive as a "reference embryo"
  for archaeological inspection during v0.9 design.
- No more cleanup commits to v0.8.7's β/γ (the 11 commits to date
  already established the post-mortem cleanup baseline).
- All forward work targets v0.9 ground-up rewrite, beginning with
  v0.9 L0 drafting (which absorbs L0.5).

---

## §6. Decision 4B elaboration — Living Bets observatory

**Position**: Living Bets is not a single-K threshold (`persistence_budget > K × read_window`). It is a **multi-signal
observatory** — the substrate measures multiple independent signals
about its own state and trajectory, and the "bet" is evaluated by
the multi-signal posture, not by any single number.

**Candidate signals** (illustrative, not exhaustive — v0.9 chooses
the actual signal set):

| Signal | What it measures | Bet posture |
|---|---|---|
| **storage budget** | Total tokens in substrate (canon + notes + doctrine + plugins) | High = bet wins (substrate exceeds read window) |
| **evolution rate** | Schema / doctrine / lint mutation frequency over time | High = P3 alive |
| **query diversity** | Distinct `sense` / `traverse` patterns per session | High = substrate is being navigated, not just held in context |
| **fork count** | Federated substrates spawned from this one | High = mycelium spreading (P5) |
| **time trend** | Per-signal trajectory (up / flat / down) | Up trends on most signals = healthy |
| **composite health score** | Weighted aggregation of all above | Single dashboard view |
| **read-window relative position** | substrate_total_tokens / agent_context_window ratio | > 100 = strongly in bet-wins region |

**Operational form**:

- v0.9 substrate ships a `living_bets_observatory.yaml` (or whatever
  v0.9 names it) tracking these signals over time.
- One or more dims monitor the signals; surface concerning trends
  (e.g. "storage budget shrinking 3 sessions in a row" = bet-
  weakening trajectory).
- Owner-set thresholds are NOT static; they emerge from the
  substrate's own historical metrics (4B: emergent).
- Living Bets MAJOR audit (per L0 cadence) reviews the observatory
  trajectory across the audit window.

**Why this** (per 4B): the substrate's bet-status is multi-
dimensional reality; collapsing to one number throws away signal.
A higher-ceiling more-flexible measurement keeps Myco honest about
*which* dimension of the bet is winning or losing.

**v0.9 must include the observatory** as a first-class subsystem or
dimension of homeostasis (whatever v0.9 calls it).

---

## §7. Decision 5E elaboration — L0.5 lifecycle and sunset

**Current state** (v0.8.7 + 11 cleanup commits + this L0.5):

- L0.5 is the binding doctrine for the v0.8 → v0.9 transition.
- L0 is unchanged but understood as describing dead embryo
  (per 3D).
- L0.5 > L1 in authority (per owner clarification A).

**Sunset trigger**: v0.9 ground-up rewrite kickoff.

At kickoff:

1. Draft new L0 (the v0.9 vision document) that absorbs L0.5's
   content.
2. The new L0 is the first artifact in the v0.9 substrate (created
   by `germinate` or equivalent, whatever v0.9 calls it).
3. L0.5 is archived to
   `_archive/L0_5_essence_v0_8_to_v0_9_transition_2026-05-13.md`
   in the v0.9 substrate (for posterity).
4. The v0.8.7 substrate (this one) retains L0.5 as its essence
   layer until end-of-life; v0.8.7 substrate is in "dead embryo
   reference" mode and receives no further changes.

**Health-of-transition signal**: if L0.5 exists past v0.9 kickoff
deadline (TBD by owner), the transition is stuck. Hygiene dim
should surface this.

---

## §8. What L0.5 carries forward (the v0.9 design input)

The new v0.9 L0 (drafted at v0.9 kickoff) must absorb:

- L0's 五条根本原则 verbatim (§2.1).
- L0's biological metaphor + "No alternate vocabulary" rule.
- L0's Living Bets appendix (revised per 4B observatory).
- All four §3-§6 elaborations (1A symbiosis, 2A MAJOR/MINOR gate,
  3D dead-embryo framing as v0.9-genesis story, 4B observatory).
- The brainstorm's 10 fix-Hs (H6/H3/H8/H11/H12 first-order +
  H21-H25 second-order, recorded in
  `ESSENCE_BRAINSTORM_2026-05-13.md`).

What it MUST NOT carry forward (per 3D dead-embryo):

- Specific verb names (20 in v0.8.7 — v0.9 designs its own)
- Specific dim names (47 in v0.8.7 — v0.9 designs its own)
- Specific subsystem partition (7 in v0.8.7 — v0.9 designs its
  own; could merge cycle into governance, could split, could
  abandon the 7-axis partition entirely)
- Specific schema version chain (v0.8.7 ships schema v4; v0.9
  resets to v1 of its own schema)
- The specific Python kernel architecture (cluster files, module
  layout, dependency graph — all redesigned)
- `_canon.yaml`'s specific field tree
- `manifest.yaml` as dispatch SSoT (v0.9 may not use a manifest
  file at all)
- biological-vocabulary specific mappings (the *metaphor* is
  preserved per L0; the *specific verb name choices* are not)

---

## §9. Confidence and remaining uncertainty

After owner arbitration of all 5 items + 4 clarifications, the
essence layer's confidence reaches **~98%**. The remaining ~2% is
the Living Bets push-back itself (a future Agent might hold a 1M-
file substrate without protocol mediation; in that scenario v0.9 is
again a dead embryo) — and this is L0-acknowledged open uncertainty,
not a defect of L0.5.

L0.5 is therefore considered **owner-sealed for the v0.8 → v0.9
transition window**. Any change before sunset requires owner
arbitration following the same 100%-confidence-loop discipline
recorded in the brainstorm.

---

## §10. Cross-references (R5 satisfied for L0.5)

- L0: [`L0_VISION.md`](./L0_VISION.md)
- L1 Contract: [`L1_CONTRACT/protocol.md`](./L1_CONTRACT/protocol.md)
- Brainstorm (deliberation log):
  [`ESSENCE_BRAINSTORM_2026-05-13.md`](./ESSENCE_BRAINSTORM_2026-05-13.md)
- Architecture overview: [`README.md`](./README.md)
