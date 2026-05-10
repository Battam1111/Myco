# v0.7-MAJOR Living Bets Re-Audit

> **Status**: DRAFT — AWAITING_OWNER_RATIFICATION (2026-05-10).
> **L0 cadence trigger**: `docs/architecture/L0_VISION.md` § "Appendix — Living bets" mandates re-audit at every MAJOR release (v0.6, v0.7, v1.0). v0.6.0 was audited inside the v0.6.0 unified-evolution craft. v0.7.0 (Major Autolysis, 2026-04-30) shipped without a Living-Bets audit. v0.7.5 retroactively performs the v0.7-MAJOR audit so the L0 cadence contract is honored.
> **Authority**: this document does NOT amend `L0_VISION.md`. It records a re-audit. Owner ratifies (no change required) or escalates to L0 amendment via a separate craft.
> **Predecessor audit**: implicit inside `docs/primordia/_landed/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` (v0.6.0).

---

## Round 1 — The bet, restated against 2026-05 reality

The L0 appendix as of 2026-04-15 says (paraphrased):

> Myco's coordination surface — 17 agent verbs + 1 human verb + canon SSoT + 11 lint dimensions — has value at every Agent intelligence tier. Whether a 2026-class Claude or a 10× successor, a standardized substrate vocabulary lets the Agent coordinate across sessions/hosts/substrates without re-deriving shape. Sutton's bitter-lesson counter-reading: a sufficiently capable Agent will hold substrate state in context and act coherently without explicit verbs.

**State 7 minor versions later (2026-05-10)**:

| Surface in the bet | v0.5.6 baseline | v0.7.5 reality | Direction |
|---|---|---|---|
| Verb count | 17 + 1 = 18 | 19 + 1 = 20 (added `intake`, `graft`, `ramify`) | grew |
| Lint dim count | 11 | 50 (4.5× growth) | grew |
| Subsystems | 6 fungal | 7 (added `boundary` v0.6.0) | grew |
| Substrate hosts | ~6 | 14 host adapters | grew |
| Schema versions | 1 | 2 (v0.6.0 schema-v2; v0.7.5 introduces v3) | grew |
| Adapters (ingestion) | 4 | 7 (chat-log added v0.7.5) | grew |

The vocabulary surface has **expanded ~3-4× since the bet was written**. The L0 statement of the bet has not been falsified — but it has also not been re-validated against the LARGER current surface.

## Round 1.5 — Self-rebuttals (5-critic L0 P1-P5 fanout)

### T1 (chytrid / P1 Only-For-Agent) — falsification probe

> Has any 2026-class agent demonstrated the ability to maintain a 1M-file Myco-shaped substrate purely from raw filesystem reads, without invoking the verbs?

**Honest answer**: not in any benchmark this audit can cite. The substrate's own development since v0.5.6 has proceeded *with* the verbs as the coordination surface. We have no controlled experiment that says "agent X with 1M-token context did just as well without verbs."

The bitter-lesson reading remains a *concern*, not a *demonstration of falsification*. The bet is unfalsified, not validated.

**Verdict**: bet stands; Living Bets §"concrete trigger for rewrite" still requires the demonstrated 1M-file-without-verbs capability before triggering rewrite. We do not have it. Bet continues.

### T2 (rhizomorph / P2 Eternal-Devour) — adoption-side probe

> If the bet has value, where's the evidence of cross-session/cross-substrate coordination that validates it in production?

**Honest answer**: Myco-self is the only substrate this audit can observe. No external substrate has propagated through `myco propagate` in production (P3 in v0.7.5 ships the FIRST end-to-end federation test, against a fixture peer; this is acknowledged in the v0.7.5 omnibus craft as "first federation E2E in 7 minor versions").

**Verdict**: the bet's *cross-substrate* component is currently unvalidated by production data. The bet is not falsified, but the validation evidence is thinner than a 7-month-old project should have. This is a P5 (mycorrhiza/All-Things-Connected) IOU more than a Living Bets falsification.

### T3 (mycoparasite / P3 Eternal-Evolve) — adversarial probe

> What change to the L0 appendix would *strengthen* the bet without amending its core claim?

**Proposed wording refinement** (non-binding; owner ratifies):

> The current language: *"We bet coordination vocabulary survives model growth the way `cp`/`mv`/`grep` survive IDEs."*

> Possible refinement: *"We bet coordination vocabulary survives model growth in proportion to the SUBSTRATE'S PERSISTENCE BUDGET. A short-lived, single-session task can be solved by raw context-holding; a multi-session, multi-host, federated substrate cannot, because no single Agent's context covers the full graph at once. The verbs survive because the substrate exceeds any single Agent's read window."*

This refinement adds a *predictive* component: the bet wins MORE strongly as substrate persistence + federation scope grows; LESS strongly for ephemeral single-session work. This makes the bet falsifiable in a sharper direction.

**Verdict**: refinement is RECOMMENDED but NOT REQUIRED. Owner can accept the refinement (small edit to `L0_VISION.md`), reject it (bet stays as-is), or defer (bet stays; refinement re-proposed next MAJOR).

### T4 (saprotroph / P4 Eternal-Iterate) — calibration probe

> What does the bet's review cadence ("every MAJOR release") look like in practice 7 minor versions in?

**Reality check**: v0.6.0 audit was bundled into the unified-evolution craft (no standalone Living Bets file). v0.7.0 audit was MISSED (this v0.7.5 craft retroactively performs it 5 minor versions after the trigger). The cadence as stated isn't being mechanically enforced — it depends on the authoring agent remembering, or on a craft to bundle it in.

**Recommendation**: introduce a lint dimension `LB1` (Living-Bets-overdue) that fires when:
- `_canon.yaml::contract_version` MAJOR has incremented (v0.6 → v0.7) since the most recent Living-Bets audit document timestamp under `docs/primordia/`, AND
- ≥2 minor versions have shipped since that MAJOR

This mechanizes the cadence. Without LB1, the cadence remains an honor-system contract that just got missed.

**Verdict**: recommend LB1 dim for v0.7.6 or v0.8 (out-of-scope for v0.7.5 — the omnibus craft is already 7 items). This audit doesn't propose adding LB1 *here*; it surfaces the IOU.

### T5 (mycorrhiza / P5 All-Things-Connected) — graph probe

> Has the verb surface's coordination value extended to the federation graph the L0 promises?

**Honest answer**: federation is shipped as code (propagate verb) since v0.5.x, but `_canon.yaml::identity.federation_peers: []` has remained empty across all 7 minor versions. v0.7.5's P3 ships the first integration test exercising the propagate code path filesystem-to-filesystem. The L0 P5 connection ("substrate is a connected graph, including across federated substrates") is half-realized: the SAME substrate's internal graph spans code → doctrine → notes → canon as promised, but the CROSS-substrate graph is one fixture peer in a test, not a real federated network.

**Verdict**: this is the largest gap surfaced by the audit. It's not a falsification of the Living Bet (the bet doesn't require federation to be in production); it's an unredeemed L0 P5 promise. v0.8 should consider whether to ship a real federation reference implementation (e.g., a sibling research substrate that propagates from this one) or to scope-down P5's federation language in L0.

## Round 2 — Decision shape

**Recommendation to owner** (any one is acceptable; this craft does not pre-judge):

**Option A — accept as-is**: bet stands, no L0 amendment, log this audit as the v0.7-MAJOR cadence event. v0.8 will perform the next audit.

**Option B — accept with T3 refinement**: amend L0 appendix to include the persistence-budget refinement (T3). Requires a separate L0-amending craft + contract bump.

**Option C — defer T3 + commit to T4 LB1 dim**: bet stands as-is; commit to mechanizing the cadence via LB1 dim by v0.8.0. Requires a v0.8-scope craft.

**Default if owner does not respond**: Option A (no L0 amendment; cadence honored; this craft files as the audit record).

## Round 3 — What this craft commits

This craft commits to **none of A/B/C**. It files the audit document as required by L0 §Appendix cadence and surfaces three distinct paths the owner can choose. Land status: **DRAFT — AWAITING_OWNER_RATIFICATION**.

The craft document is written to `docs/primordia/` and not moved to `_landed/` until owner ratification (which may take any of the three forms above). v0.7.5 ships with this craft visible as a draft. Subsequent audits at v0.8.0 / v0.9.0 / v1.0.0 inherit this trail.
