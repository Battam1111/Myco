---
proposed_doctrine: v-0-7-x-release-cycle-retrospective
sources:
- notes/integrated/n_20260510T081112Z.md
- notes/integrated/n_20260510T081114Z.md
- notes/integrated/n_20260510T081116Z.md
- notes/integrated/n_20260510T081117Z.md
- notes/integrated/n_20260510T081119Z_v0-7-4-zip-extension-hotfix-drag-drop-va.md
distilled_at: '2026-05-10T08:11:43Z'
stage: distilled
ingest_state: distilled
synthesis_authored_at: '2026-05-10T08:15:00Z'
---

# Distillation: v0.7.x release-cycle retrospective

> Synthesizes 5 craft proposals (v0.7.0/v0.7.1/v0.7.2/v0.7.3/v0.7.4) shipped between 2026-04-30 and 2026-05-09. The 5 crafts span: structural autolysis, hotfix-on-broken-shim, eternal-pruning ratchets, lint-zero pre-distribution polish, and external-bug workaround. Together they describe how the v0.7.x cycle exercised every phase of Myco's evolution model.

## The cycle in one paragraph

v0.7.0 (Major Autolysis, 2026-04-30) deleted aggressive structure: the legacy `myco.mcp` shim, several deprecated paths, redundant exports — net ~8 KLOC removed. Two hours later, the owner's local Claude Desktop MCP host crashed because *its* config still referenced `python -m myco.mcp`; v0.7.1 (same day) revived the shim as a deprecation-warning back-compat layer with telemetry. v0.7.2 (also same day) generalized the lesson — added 4 ratchet dimensions (MB8 / PA6 / MF5 / SE5) that mechanically detect public-API deletion debt + repo bloat + mirror drift + version-anchor staleness. v0.7.3 (next day) executed a 6-cluster IOU closure run that took 171 lint findings → 1, codified the v0.7.1-named "public-API deletion discipline" as L2 doctrine, and prepared the substrate for fresh Cowork distribution. v0.7.4 (24h later) corrected an external Anthropic bug: the `.plugin` artifact extension shipped since v0.5.20 was rejected by Cowork's upload validator (per Anthropic GitHub issue #40414); switched to `.zip`, locked the constant in a regression test, and codified the discovery as L2 doctrine.

## Five doctrinal observations promoted from this cycle

### 1. **Two-hour blast-radius rule** (from v0.7.0 → v0.7.1)

A "structural compaction" release that deletes ANY public-API surface symbol — even one transitively referenced by external consumers' configs — has a measurable failure mode within hours, not days. v0.7.0's autolysis broke the owner's host within 2 hours. The lesson: external-consumer reachability assessment is necessary, not optional, before deletion. v0.7.1 codified this as the *named-named* "public-API deletion discipline" and v0.7.3 promoted it to L2 doctrine with two formal gates: (a) internal-only verification (4-condition grep against the to-be-deleted symbol), or (b) telemetry verification (live shim-hit counter must show N senesce cycles + D wall-clock days zero-hit). v0.7.5 backfills the missing tooling: bump_version.py auto-refreshes metrics so this telemetry never goes stale.

### 2. **Ratchet dimensions are eternal pruning** (from v0.7.2)

Dim categories — mechanical / shipped / metabolic / semantic — each have an "eternal pruning" complement that fires LOUDER as substrate health DECLINES along that axis. MB8 (shim hits) is a metabolic ratchet: it gets noisier the more legacy code runs. PA6 (repo bloat) is mechanical: louder as `du` exceeds threshold. MF5 (mirror drift) is mechanical: silent when bytes are identical, MEDIUM when divergent. SE5 (version-anchor staleness) is semantic: louder as version anchors in docs lag tag-monotone. Combined: ratchet dims are how a substrate refuses to accumulate cruft mechanically. v0.7.5's introduction of `metrics.lint_dim_count` (auto-refreshed) extends this pattern into metric self-consistency.

### 3. **External-bug workaround discipline** (from v0.7.4)

When a downstream consumer (Anthropic, in this case) ships a bug we cannot fix, the discipline is: (a) don't blame; (b) reproduce minimally; (c) find the issue tracker entry; (d) workaround in our own surface; (e) regression-test the workaround to lock it; (f) codify the constraint origin as L2 doctrine so a future contributor doesn't undo the workaround thinking it's superfluous. v0.7.4 executed all 6 steps. The "regression test pinning a constant against external constraint" pattern is generalizable.

### 4. **Hotfix cadence is honest** (across v0.7.0/.1/.2/.3/.4)

5 versions shipped in 10 days. Two were hotfixes (v0.7.1, v0.7.4) responding to external/owner-environment failure modes. Three were planned (v0.7.0, v0.7.2, v0.7.3). The hotfix lag-time was ~2 hours (v0.7.0→.1) and ~24 hours (v0.7.3→.4). This is the *correct* cadence for a substrate that values "ship + measure + iterate" over "ship + plan + ship-again". The Living-Bets appendix predicts coordination grammar survives model growth; this cycle is evidence that *hotfix grammar* survives grammar bloat — adding 4 ratchet dims didn't slow hotfix cadence.

### 5. **L2 doctrine codification is the seal** (across v0.7.1/v0.7.3/v0.7.4)

Each substantive cycle item produced a 1-3 paragraph L2 boundary doctrine addition: "Legacy import shims (v0.7.3+)", "Public-API deletion discipline", "Cowork plugin artifact extension (v0.7.4+)". The pattern: when an ad-hoc decision has been made on the same topic 2+ times across versions, it gets promoted to doctrine so the substrate's own future agents inherit it. **Doctrine is the substrate's institutional memory; without it, every cycle re-derives the same lessons.**

## Synthesis: what the v0.7.x cycle teaches

The L0 P3 promise (Eternal Evolution) and P4 promise (Eternal Iteration) are honored when:
- *Evolution* is mechanically gated (ratchet dims + bump_version auto-refresh + L2 doctrine codification).
- *Iteration* is permissive of hotfix cadence within MAJOR (v0.7.x: 5 versions, 10 days, 2 hotfixes) but strict on contract preservation (every hotfix stayed within MAJOR, no L0 amendment).

The five crafts together demonstrate the "ship and immediately codify the lesson" loop is the engine. v0.7.5's omnibus is the closure: it does the polish work the cycle deferred (metric auto-refresh, README dim count, contract changelog backfill) AND ships the missing-since-v0.5.x integration tests (federation E2E, schema upgrader exercise, chat-log adapter), AND honors the L0-mandated v0.7-MAJOR Living-Bets re-audit.

## Possible promotion to L2 doctrine

The "Two-hour blast-radius rule" + "External-bug workaround discipline" + "L2 doctrine codification is the seal" observations are candidates for promotion to a new L2 section: `docs/architecture/L2_DOCTRINE/release_discipline.md` (or appended to `boundary.md`). The v0.7.5 omnibus craft does NOT promote them — it surfaces the candidacy. Owner reviews this distillation; if accepted, a follow-up craft (probably v0.8.x scope) authors the L2 promotion.

## Source notes (graph back-references)

This distillation was synthesized from the following integrated notes (linked here so the SE2 graph dimension recognizes the inbound edge — the L0 P5 mycelium graph requires reachability, not just frontmatter listing):

- [v0.7.0 Major Autolysis](../integrated/n_20260510T081112Z.md)
- [v0.7.1 Shim Revival](../integrated/n_20260510T081114Z.md)
- [v0.7.2 Eternal Pruning Ratchets](../integrated/n_20260510T081116Z.md)
- [v0.7.3 Lint-Zero Pass](../integrated/n_20260510T081117Z.md)
- [v0.7.4 ZIP Extension Hotfix](../integrated/n_20260510T081119Z_v0-7-4-zip-extension-hotfix-drag-drop-va.md)
