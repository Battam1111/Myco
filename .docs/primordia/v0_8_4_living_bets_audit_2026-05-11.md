# v0.8-MAJOR Living Bets Re-Audit (post-amendment evaluation)

> **Status**: DRAFT — AWAITING_OWNER_RATIFICATION (2026-05-11).
> **L0 cadence trigger**: `docs/architecture/L0_VISION.md` § "Appendix — Living bets" mandates re-audit at every MAJOR release. v0.8.0 MAJOR shipped 2026-05-11 with the persistence-budget refinement (commit `783da78`). The v0.8 audit is now due per the LB1 dim's LOW finding ("Living Bets audit overdue: substrate at v0.8.4 but most-recent audit covers v0.7.5").
> **Predecessor audit**: `docs/primordia/_landed/v0_7_x/v0_7_5_living_bets_audit_2026-05-10.md` (RATIFIED via Option B at v0.8.0).
> **Distinct from v0.7 audit**: the v0.7 audit was retroactive (covered v0.7.0-v0.7.5 cycle). This v0.8 audit is **on-time** (substrate is at v0.8.4; LB1 fired at MAJOR-bump moment; audit lands within 4 patch versions of the trigger).

---

## Round 1 — The bet 7 minor versions later (now with v0.8.0's persistence-budget framing)

The L0 wager (post-v0.8.0) reads:

> "Coordination vocabulary survives model growth in proportion to the substrate's persistence budget."

**Two regimes named explicitly**:
- Bet wins: multi-session / multi-host / federated work where substrate persistence > any single Agent's read window.
- Bet loses: ephemeral single-session work where one Agent can hold the entire problem in context.

**State at v0.8.4** (verified 2026-05-11 via `myco brief`):

| Signal | Value | Implication |
|---|---|---|
| `metrics.session_count` proxy (shim_hits.json distinct session_id) | ~30 | Beyond bet-losing threshold (5); below bet-winning auto threshold (50) — **transitional** |
| `identity.federation_peers` length | **1** (CC) | Crosses bet-winning threshold (≥1 peer = federated regime) |
| LB2 dim verdict on Myco-self | **silent** (bet-winning regime via peer_count ≥ 1) | Substrate self-classifies as bet-winning |
| Verb invocation rate (per session) | ~10-30 verb calls/session typical | Verbs ARE actively used (not bypassed in favor of raw filesystem reads) |
| Cross-substrate propagation events (production) | **5** (myco-self → CC, 2026-05-11) | First-ever production federation activity; bet exercises its winning regime concretely |

## Round 1.5 — Self-rebuttals (5-critic L0 P1-P5 fanout)

### T1 (chytrid / P1 Only-For-Agent) — falsification probe

> Has any 2026-class agent demonstrated the 1M-file substrate-without-verbs Sutton-trigger condition?

**Honest answer**: still no. The substrate's growth (40 integrated + 5 distilled + 3 retrospectives wrote in v0.7.10's K item) was authored by agents WITH the verbs. We have no controlled experiment that rejects the bet.

**Verdict**: bet stands; trigger condition unmet.

### T2 (rhizomorph / P2 Eternal-Devour) — adoption-side probe

> If the bet has value, where's the production cross-substrate evidence?

**Update from v0.7 audit**: v0.8.0 P3 shipped CC as the first production federation peer. **5 distilled retrospectives propagated end-to-end** (verified 2026-05-11; `_canon.yaml::identity.federation_peers: ["C:/Users/10350/Desktop/CC"]`). The bet's cross-substrate component is now **half-validated** (myco-self → CC verified; CC → myco-self direction is enabled but unexercised pending CC's own integrated-content authoring).

**Verdict**: meaningful progress since v0.7.5 audit. Bet stands stronger.

### T3 (mycoparasite / P3 Eternal-Evolve) — wager-evolution probe

> The v0.8.0 amendment added the persistence-budget framing. Is the new wording holding up to the v0.8.x cycle's evidence?

**Empirical check**: v0.7.x → v0.8.x cycle made 5 minor releases + 4 hotfixes; through all of it, the substrate's session_count + peer_count grew monotonically. The persistence-budget framing predicts: substrates that persist + federate win the bet harder. Myco-self is doing both (4-week persistence + 1-peer federation). Subjectively (the agent author's report card): the persistence-budget framing has been a **useful decision aid** during v0.8.0 work — when item B (OAuth) was scoped, the question "does this raise the persistence budget?" pointed unambiguously at "yes, OAuth makes streamable-http production-deployable, which means the substrate can be hosted across machines, which extends the persistence-budget envelope." Without the framing, the OAuth IOU might have stayed deferred indefinitely.

**Verdict**: persistence-budget framing earns its place. **No further refinement needed at v0.8**.

### T4 (saprotroph / P4 Eternal-Iterate) — calibration probe

> What does the bet's review cadence look like one MAJOR after the LB1 dim was added?

**Update**: LB1 dim shipped v0.7.10. v0.8.0 was the first MAJOR-cadence trigger. LB1 fired LOW within 0 minor versions of the v0.8 bump (correctly), prompting this audit.

**The cadence is now mechanically enforced**. The v0.7.0 cadence miss (which v0.7.5 retroactively backfilled) is structurally prevented going forward.

**Verdict**: T4 from v0.7 audit (LB1 dim) is fully delivered. No further mechanization needed.

### T5 (mycorrhiza / P5 All-Things-Connected) — graph probe

> Has the federation graph component progressed beyond the v0.7.5 audit's "fixture-peer-only" state?

**Update**: yes. v0.8.0 ships:
- 1 production peer (CC) with real disk presence
- 5 propagation events (myco-self → CC) with proper source-stamping + propagated_at frontmatter
- propagate API generalized to `dst_roots: list[Path]` (v0.7.10) handles N-peer fan-out

**Still missing at v0.8.4**:
- CC has no integrated content yet → reverse direction (CC → myco-self) is enabled but unexercised
- Cross-machine federation (filesystem-only at v0.8.4)
- A 3-peer real network (only 1 production peer; 3-peer is fixture-only)

**Verdict**: significant progress; the largest remaining gap is **CC's own integrated-content authoring**, which is owner-organic activity.

## Round 2 — Decision shape

**Recommendation to owner** (this audit does not pre-judge):

**Option A — accept as-is**: bet stands with v0.8.0's persistence-budget refinement. No further L0 amendment. Next audit at v0.9.0 MAJOR.

**Option B — minor refinement**: consider adding a sub-clause to the wager that **explicitly names cross-machine federation** as a v1.0 ambition (the L0 currently uses "multi-host" but doesn't differentiate filesystem-host from network-host). This sharpens the falsification target — once cross-machine federation works, the bet has ANOTHER concrete test condition.

**Option C — no change**: confirm Option A explicitly.

**Default if owner does not respond**: Option A (substrate moves forward unchanged). v0.9.0 audit will revisit.

## Round 3 — What this craft commits

This craft commits to **none of A/B/C** by itself. It records the v0.8-MAJOR cadence event and surfaces the three ratification paths.

**Net status update from v0.7 audit**:

| Item | v0.7.5 audit verdict | v0.8.4 audit verdict |
|---|---|---|
| Bet validity | unfalsified, not validated | unfalsified; **partially validated** by CC peer + 5 propagations |
| Cross-substrate evidence | thin (no production peer) | **moderate** (1 production peer + 5 events) |
| Wager wording | analogy-only ("cp/grep") | persistence-budget refinement (T3 from v0.7) — **holding up well** |
| Cadence enforcement | LB1 dim proposed | LB1 dim shipped + fired correctly at v0.8 trigger |
| Graph connectivity (P5) | fixture-only federation | production-1-peer federation |

The bet is **healthier at v0.8.4** than at any prior audit. The persistence-budget framing is earning its place. Cross-substrate evidence is accumulating.

The audit document is written to `docs/primordia/v0_8_4_living_bets_audit_2026-05-11.md` and stays DRAFT until owner ratification (which may take any of A/B/C). The substrate continues to operate under the v0.8.0 amendment's wording; this audit is purely an evaluation event, not a contract change.
