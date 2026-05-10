# L2 — Release Discipline

> **Status**: APPROVED (2026-05-10, v0.7.10 omnibus item L).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/protocol.md`.
> **Maps to**: `scripts/bump_version.py`, `.github/workflows/release.yml`, `tests/integration/test_install_cowork_plugin.py`, the `stipe` subagent at `.claude/agents/stipe.md`.
> **Promoted from**: `notes/distilled/d_v0-7-x-release-cycle-retrospective.md` (v0.7.5 P4 self-eat output) per the v0.7.x cycle's accumulated lessons.

---

## What this doctrine codifies

Release discipline is the substrate's **mechanical contract for shipping changes** — the rules every cycle's release process honors regardless of who's authoring (owner, agent, subagent, or future automation).

Five rules promoted from the v0.7.x retrospective. Each was learned in production (often the hard way) across v0.5.20 through v0.7.4. They are now binding L2 doctrine; deviating requires an L2-amending craft.

## Rule 1 — The Two-Hour Blast-Radius Rule

> **Any release that deletes a public-API surface symbol — even one transitively referenced by an external consumer's config — has a measurable failure mode within hours, not days. External-consumer reachability assessment is necessary, not optional, before deletion.**

**Origin**: v0.7.0 (Major Autolysis) deleted `myco.mcp` shim within 2 hours of ship; the owner's local Claude Desktop MCP host crashed because *its* config still referenced `python -m myco.mcp`. v0.7.1 hotfix (same day) revived the shim with deprecation-warning telemetry.

**Mechanism (v0.7.3+)**: any deletion of a public-API symbol must satisfy ONE of:
- **Gate (a) — Internal-only verification**: 4-condition grep against the to-be-deleted symbol confirms zero external references.
- **Gate (b) — Telemetry verification**: live shim-hit counter (e.g., `.myco_state/shim_hits.json` for `myco.mcp`) shows ≥7 senesce cycles + ≥7 wall-clock days zero hits.

The discipline is recorded at `docs/architecture/L2_DOCTRINE/boundary.md` § "Public-API deletion discipline (v0.7.1-named, v0.7.3-canonized)" and is mechanized via the MB8 ratchet dim (v0.7.2). The pytest-shim migration in v0.7.10 item A unblocks the gate-(b) countdown for `myco.mcp` deletion.

## Rule 2 — Ratchet Dimensions Are Eternal Pruning

> **A category of lint dimension exists whose purpose is to fire LOUDER as substrate health DECLINES along its axis. These are not bug-detectors; they are entropy-counter-pressure mechanisms.**

**Origin**: v0.7.2 introduced 4 ratchet dims (MB8 / PA6 / MF5 / SE5) explicitly named "永恒删减 (eternal pruning)" — the structural mechanism for L0 P3-Eternal-Evolution acting against accumulated cruft.

**Categories of ratchet** (one per immune category):
- **Mechanical ratchet** (PA6 repo bloat, MF5 mirror drift): silent at health, MEDIUM at degradation.
- **Metabolic ratchet** (MB8 shim hits): louder as legacy code-paths accumulate hits.
- **Semantic ratchet** (SE5 version-anchor staleness): louder as documents lag behind monotone tag sequence.

v0.7.10 adds **LB1** (Living-Bets-overdue, semantic/LOW) as the first ratchet for governance cadence, mechanizing the L0 §"Appendix — Living bets" every-MAJOR re-audit requirement.

**Test of doctrine**: any future cycle that adds a new dim category MUST consider whether a ratchet variant in that category is warranted. Silent absence is acceptable; unmotivated absence is a craft IOU.

## Rule 3 — External-Bug Workaround Discipline

> **When a downstream consumer ships a bug we cannot fix (Anthropic, Cowork, third-party MCP host, etc.), the substrate's response is a 6-step workaround discipline. Workaround quality is graded against the steps.**

**Origin**: v0.7.4 (`.plugin` → `.zip` extension hotfix per Anthropic GitHub issue #40414) executed all 6 steps consciously and codified them.

**The 6 steps**:
1. **Don't blame**: even when the upstream is verifiably wrong, frame the substrate's response as a fix to OUR surface, not as critique of theirs.
2. **Reproduce minimally**: confirm the bug in an isolated test case before attempting workaround.
3. **Find the issue tracker entry**: search the upstream's bug tracker; cite the exact issue number in commit messages and L2 doctrine.
4. **Workaround in our own surface**: change Myco-side defaults / behaviors so users hit the workaround path without effort.
5. **Regression-test the workaround**: the workaround MUST be pinned by a test that fails if a future contributor undoes it. Locks the value (e.g., `BUNDLE_EXTENSION = ".zip"` regression test).
6. **Codify the constraint origin**: write an L2 doctrine entry naming the upstream issue + the workaround + an explicit "what would justify reverting" condition.

**Test of doctrine**: any v0.8.x+ workaround that omits any step is a craft-review reject.

## Rule 4 — Hotfix Cadence Honesty

> **Hotfix cadence within a MAJOR release is unrestricted. Hotfix release type is HONEST: hotfixes must explicitly self-identify in commit messages, contract changelogs, and craft titles.**

**Origin**: v0.7.x cycle shipped 5 versions in 10 days, 2 of which were hotfixes (v0.7.1, v0.7.4) responding to external/owner-environment failure modes. The discipline: hotfixes did NOT pretend to be feature releases; their crafts were named "hotfix" explicitly.

**Mechanical implication**: contract_changelog.md headlines must include one of {"feat", "hotfix", "molt", "audit", "omnibus"} as a prefix label. Conformance is currently honor-system; v0.8 may mechanize via a new dim if drift is observed.

## Rule 5 — L2 Doctrine Codification As The Seal

> **Whenever the substrate makes the same kind of decision 2+ times across versions, the THIRD instance is required to promote the pattern to L2 doctrine. Recurring ad-hoc decisions are forbidden as institutional-memory bypass.**

**Origin**: v0.7.x cycle promoted 3 patterns to L2 doctrine: "Legacy import shims (v0.7.3+)", "Public-API deletion discipline (v0.7.1-named, v0.7.3-canonized)", "Cowork plugin artifact extension (v0.7.4+)". Each was an ad-hoc response that, by the second occurrence, was clearly a recurring class.

**The 2+ trigger**: if the substrate's diff history shows two crafts addressing the same kind of issue under different names, the next craft authoring must include an L2 promotion as a sub-deliverable, OR explicitly justify why this kind doesn't deserve doctrine promotion.

**Mechanical aspiration**: a future dim DC6 (Doctrine Coverage) could lint craft documents for the `2+ rule` automatically. Out of scope at v0.7.10; tracked as IOU.

## What this doctrine does NOT cover

- **L1 contract amendments**: those go through `myco fruit` + owner approval + contract bump per `L1_CONTRACT/protocol.md` § governance. Release discipline is L2; contract is L1; conflicts resolve top-down per R7.
- **L0 amendments**: the 5 root principles are immutable except by explicit owner-authorized L0 craft (rare, recorded at the top of `L0_VISION.md`). Release discipline cannot override L0.
- **Per-host install-surface decisions**: those live in `boundary.md`, not here. Release discipline is the *temporal* axis; per-host install is the *per-target* axis.

## Test of completeness

A future contributor (or future agent) writing a v0.8.x craft can use this doctrine as a checklist: "have I considered the blast-radius? Is this a ratchet candidate? Is there an upstream bug? Am I labeling honestly? Am I noticing a recurring pattern that deserves L2 promotion?" Honoring the 5 rules is the substrate's way of saying *we have learned, and we won't re-derive*.
