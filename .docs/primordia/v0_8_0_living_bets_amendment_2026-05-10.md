# v0.8.0 — Living Bets Amendment (Option B: persistence-budget refinement)

> **Status**: LANDED (2026-05-10, v0.8.0 MAJOR opening act).
> **Layer**: L0-amending. Modifies `docs/architecture/L0_VISION.md` § "Appendix — Living bets". Per L0 § "Changes to this page" governance, requires (1) a craft doc, (2) explicit owner approval, (3) contract bump, (4) cascade review of every lower-layer doc. This document is (1); owner approval is recorded inline below; (3) and (4) are absorbed into the v0.8.0 MAJOR contract bump that this craft opens.
> **Source**: ratifies Option B from `docs/primordia/_landed/v0_7_x/v0_7_5_living_bets_audit_2026-05-10.md` (v0.7-MAJOR re-audit; Round 2 § "Decision shape").
> **Supersedes**: the deleted `v0_7_10_living_bets_ratification_2026-05-10.md` (which had pre-emptively chosen Option A while owner ratification was pending).
> **Owner approval**: explicit, 2026-05-10, "选择 B，那么拜托了！" — recorded as Round 2 conclusion below.

---

## Round 1 — What this craft does

**Adopts T3 of the v0.7.5 Living Bets re-audit** (mycoparasite / P3 Eternal-Evolve adversarial probe) as a binding L0 amendment. Specifically:

- Replaces the analogy-based wager wording ("verbs survive the way `cp`/`mv`/`grep` survive IDEs") with a **predictive wager**: verbs survive **in proportion to the substrate's persistence budget**.
- Introduces "**persistence budget**" as a new L0-level concept the substrate's reasoning may use to prioritize work (more on this below).
- Keeps the bet's core claim intact: `cp`/`mv`/`grep` analogy is preserved in the rationale, just demoted from being the entire bet to being one supporting example.
- Explicitly identifies the regime where the bet **wins** (multi-session / multi-host / federated substrates) and the regime where it **loses** (ephemeral single-session tasks).

This is the **first amendment to L0 since the v0.4.x identity revision** (2026-04-15). It deliberately ships at the opening of the v0.8.0 MAJOR window so that every subsequent v0.8.x decision can rest on the refined bet.

## Round 1.5 — Self-rebuttals (5-critic L0 P1-P5 fanout)

### T1 (chytrid / P1 Only-For-Agent) — refutation probe

> The persistence-budget refinement gives agents more decision criteria. Is this useful to the agent, or just metaphysical decoration?

**Resolution**: useful. The current bet wording ("verbs survive like grep") gives the agent zero machinery for deciding *whether to commit something to the substrate vs hold it in context*. The refined wording explicitly maps "this work has high persistence budget → put it in substrate" vs "this work is ephemeral → context is fine". Future agents reading L0 inherit a concrete heuristic, not a slogan.

### T2 (rhizomorph / P2 Eternal-Devour) — adversarial probe

> Does "persistence budget" as a concept survive without being defined? Won't future audits argue endlessly about what counts as "persistent"?

**Resolution**: definition is coverage-based, not threshold-based. The amendment names two **regimes** (single-session-ephemeral vs multi-session/multi-host/federated) and asserts the bet's prediction in each. Future audits don't need a numeric threshold — they classify the substrate's actual workload along the regime axis and check whether the bet's prediction matched observed behavior. Mechanizable later (e.g., a `LB2` dim that measures session-count + host-count + peer-count and reports the regime); deliberately not done in this amendment to keep the L0 change minimal.

### T3 (mycoparasite / P3 Eternal-Evolve) — recursion probe

> The amendment is itself adopted via the cycle "fruit → winnow → molt" governance the bet describes. Is this self-referential and therefore suspect?

**Resolution**: no — this is exactly what L0 P3 prescribes. Schema and bet evolve together; that's the substrate's design, not a smell. The recursion is well-founded because each amendment ships with explicit owner approval + contract bump, breaking any infinite-amendment loop at the governance gate.

### T4 (saprotroph / P4 Eternal-Iterate) — calibration probe

> What does "the bet is winning" look like under the new wording, observable at v0.9 / v1.0 audits?

**Resolution**: under the new wording, the bet's evidence ladder becomes:
1. Substrate's session count + host count + peer count grow over time.
2. Verb usage tracked in surface logs continues to be consistent across the growth.
3. Agent outputs that touch the substrate cite/reference past artifacts at a non-decreasing rate (i.e., the substrate is being read, not just appended to).

Falsification looks like: (1) substrate growth flat (substrate isn't being persisted in production), AND (2) agents bypass verbs to read raw filesystem (vocabulary gone unused). Future audits can pull these signals from `.myco_state/`, surface logs, and the graph dim outputs.

### T5 (mycorrhiza / P5 All-Things-Connected) — graph probe

> Does the refinement affect federation language elsewhere in L0?

**Resolution**: no breaking changes to P5. The refinement uses "federated substrate" as **one example** of high-persistence-budget regime, not as a definition of federation. P5's existing "across federated substrates" language stands as written. The amendment is purely additive at the §Appendix level.

## Round 2 — Decision (owner-ratified)

**Owner directive (2026-05-10)**: "选择B，那么拜托了！" — translation: "Pick B, please proceed!"

The amendment is **APPROVED**. The five critics' verdicts (above) collectively raise no blocker. The contract bump that ships with v0.8.0 MAJOR carries this amendment. Subsequent v0.8.0 work (OAuth wire-up, federation production peer with CC, etc.) builds on the refined bet.

## Round 3 — The exact L0 diff

The amendment edits **one block** in `docs/architecture/L0_VISION.md` § "Appendix — Living bets" (around lines 197-222 at v0.7.10).

### Before (v0.5.6 wording, preserved through v0.7.10)

```markdown
**Myco's wager.** We bet coordination vocabulary survives model
growth the way `cp`/`mv`/`grep` survive IDEs. The verbs are not a
user interface for the human — they are a coordination grammar for
the Agent, and grammars persist as abstractions even when the
underlying actor gets smarter. A smarter `grep` user still runs
`grep`; a smarter Agent still runs `myco hunger` because the
substrate is a shared object the Agent coordinates *with*, not
just a memory it holds. But this bet is undetermined, not proven.
```

### After (v0.8.0 wording — Option B refinement)

```markdown
**Myco's wager.** We bet coordination vocabulary survives model
growth **in proportion to the substrate's persistence budget**. A
short-lived, single-session task can be solved by raw context-
holding; a multi-session, multi-host, federated substrate cannot,
because no single Agent's context covers the full graph at once.
The verbs survive because the substrate exceeds any single Agent's
read window. This is the same reason `cp`/`mv`/`grep` survive
IDEs — IDE memory is per-session, the file system is persistent —
but the analogy is supporting evidence, not the wager itself.

The verbs are not a user interface for the human — they are a
coordination grammar for the Agent, and grammars persist as
abstractions even when the underlying actor gets smarter. A smarter
`grep` user still runs `grep`; a smarter Agent still runs `myco
hunger` because the substrate is a shared object the Agent
coordinates *with*, not just a memory it holds. But this bet is
undetermined, not proven.

**The two regimes the bet names explicitly**:

- **Bet wins in**: multi-session / multi-host / federated work
  where the substrate's persistence budget exceeds any single
  Agent's read window. Verbs are the only common-knowledge
  protocol across the boundary.
- **Bet loses in**: ephemeral single-session work where one Agent
  can hold the entire problem in context. Raw context-holding wins;
  verb surface is overhead.

A future audit's job is to classify observed work along this regime
axis and check whether verb usage tracked the bet's prediction.
```

**Net effect**: ~25 lines added (one new sentence at the top + a new section "The two regimes the bet names explicitly"). No deletions. The original analogy ("`cp`/`mv`/`grep` survive IDEs") is preserved as supporting evidence rather than being the wager's full statement.

## Round 4 — Cascade review (lower-layer dependencies)

Per L0 § "Changes to this page" requirement (4): "A cascade review of every lower-layer doc for implicit dependencies."

| Layer | File(s) | Dependency on the old wording | Required edit |
|---|---|---|---|
| **L1** | `docs/architecture/L1_CONTRACT/protocol.md` | None (R1-R7 don't reference the bet) | None |
| **L1** | `docs/architecture/L1_CONTRACT/canon_schema.md` | None | None |
| **L1** | `docs/architecture/L1_CONTRACT/versioning.md` | None | None |
| **L2** | `docs/architecture/L2_DOCTRINE/*.md` × 8 | None of the 8 cite the wager directly | None |
| **L3** | `docs/architecture/L3_IMPLEMENTATION/*.md` | None | None |
| **L4** | `MYCO.md`, READMEs × 3 | None of these cite the wager | None |

Cascade scan finding: **zero downstream documents depend on the analogy-based wager wording**. The amendment is genuinely additive at L0; the cascade review is satisfied with no follow-on edits required.

## Round 5 — What ships in this commit (v0.8.0 MAJOR opening act)

This commit is **prepare-v0.8.0-MAJOR** — the L0 amendment lands first, separate from the rest of the v0.8.0 MAJOR work, so the audit trail is clean and the L0 change is reviewable in isolation.

Files touched in this commit:

- `docs/architecture/L0_VISION.md` — wager wording (Round 3 diff above)
- `docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md` — this craft (NEW)
- `docs/primordia/_landed/v0_7_x/v0_7_5_living_bets_audit_2026-05-10.md` — status changed from DRAFT → "**RATIFIED via Option B at v0.8.0**"

Files NOT touched in this commit (deferred to v0.8.0 MAJOR main commit):

- `_canon.yaml::contract_version` — bumps as part of the MAJOR's atomic bump commit, not separately
- All v0.8.0 MAJOR substantive items (OAuth wire-up, CC peer integration, schema v3 → v4 if any, etc.)

The version label remains v0.7.10 on disk after this commit. The actual `v0.8.0` tag is created when the v0.8.0 MAJOR main commit ships.

## Round 6 — Future audits inherit the new bet

The next Living Bets re-audit fires at v0.9.0 MAJOR (or earlier if forced by craft). It inherits:

- The persistence-budget regime axis as the primary judgment criterion.
- The falsification template defined in T4: substrate growth flat + verb-bypass observed = bet failing.
- The optional `LB2` dim hook (regime-classifying lint dim) as a v0.8.x or v0.9 IOU. Not commitment-binding here.

Once the bet has a persistence-budget shape, any future agent reading L0 understands **why** the substrate exists: not because verbs are aesthetically preferable, but because **substrate persistence > any single Agent's context window**. That's the operational kernel of P5 (Universal Interconnection) made explicit in the wager.
