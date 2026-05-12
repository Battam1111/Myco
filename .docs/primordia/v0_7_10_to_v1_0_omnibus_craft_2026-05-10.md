# v0.7.10 — Roadmap-to-v1.0 Omnibus (the longest-march release)

> **Status**: LANDED (2026-05-10).
> **Predecessor**: v0.7.5 (P0-P6 omnibus), shipped 2026-05-10.
> **Trigger**: owner directive — ship every roadmap item that was queued for v0.7.6 / v0.8.x / v0.9-v1.0 in one breath. Version label = v0.7.10 (5-patch jump from v0.7.5; intermediate v0.7.6/.7/.8/.9 burned). Scope = all of it.

---

## Round 1 — Initial claim

v0.7.10 ships 13 substantive items in one atomic release:

| # | Item | Roadmap origin |
|---|---|---|
| A | Pytest `myco.mcp` → `myco.boundary.mcp` migration | v0.7.6 (closes MB8 sunset gate) |
| B | LB1 Living-Bets-overdue lint dimension | v0.7.6 |
| C | Federation 3-peer fixture network + propagate `list[Path]` | v0.8.x |
| D | SQLite ingestion adapter (8th) | v0.8.x |
| E | Email/mbox ingestion adapter (9th) | v0.8.x |
| F | Git-history ingestion adapter (10th) | v0.8.x |
| G | Streamable-HTTP + OAuth 2.1 verification suite | v0.9-v1.0 |
| H | Graph builder benchmark suite (10K-file synthetic substrates) | v0.9-v1.0 |
| I | Examples/ × 8 framework demos smoke tests | v0.9-v1.0 |
| J | `.myco/plugins/` reference plugin + graft integration test | v0.8.x |
| K | Self-eat v0.5.x + v0.6.x craft historical backlog | v0.8.x (P4 honesty) |
| L | New L2 doctrine `release_discipline.md` | v0.8.x (promotes v0.7.x distillation) |
| M | Living Bets Option A ratification + audit cadence dim | v0.7.6 (closes the v0.7.5 audit DRAFT) |

## Round 1.5 — Self-rebuttals (5-critic L0 P1-P5 fanout)

### T1 (chytrid / P1 Only-For-Agent)

> Stuffing 13 items into one release is a contract delivery, not an agent-first design. Where's the agent-experience improvement?

**Resolution**: each item closes an agent-experience gap surfaced by the v0.7.5 retrospective:
- A unblocks shim deletion (smaller substrate the agent can hold in context)
- B mechanizes a cadence the agent currently honors only by remembering
- C tests the federation pathway the agent's `propagate` verb has promised
- D/E/F expand "anything the agent can point at" by 3 modalities
- G verifies a transport claim the agent's deployment surface advertises
- H proves the graph (which the agent reads constantly) scales
- I confirms 8 framework adapters the agent might be invoked from
- J makes the per-substrate plugin path the agent dogfoods
- K runs the agent's own iteration loop on its own history
- L promotes hard-won lessons into doctrine the agent reads
- M closes a governance loop the agent's L0 mandates

This bundle isn't 13 features. It's 13 *closed loops*.

### T2 (rhizomorph / P2 Eternal-Devour)

> 3 adapters when 7 already exist? Why not 5+, given P2's "anything"?

**Resolution**: SQLite + email/mbox + git-history are all stdlib-only. Audio/video/OCR (whisper/tesseract) require heavy optional deps that risk breaking CI on platforms without them. v0.7.10 ships the stdlib-3 + documents `myco[multimedia]` as v0.8 future scope. Honest engineering: don't ship adapters whose CI hits 80% of users with `ImportError` at install time.

### T3 (mycoparasite / P3 Eternal-Evolve)

> 5-patch version jump (v0.7.5 → v0.7.10) burns four version slots. Is this PEP 440 / SemVer compliant?

**Resolution**: SemVer and PEP 440 both permit non-contiguous version sequences. v0.7.6/.7/.8/.9 simply never existed (no PyPI uploads under those names; no git tags). MCP Registry and PyPI both index v0.7.10 as the next-after-v0.7.5 entry; nothing about that is non-compliant. The version-strict check in release.yml only verifies tag matches files; it doesn't enforce contiguity.

### T4 (saprotroph / P4 Eternal-Iterate)

> Self-eat 20+ historical crafts in one release? That's a one-shot bulk operation, the opposite of "eternal" iteration.

**Resolution**: K closes a ONE-TIME debt (the v0.5.x and v0.6.x crafts that were never assimilated). Once K lands, the eternal-iteration cadence resumes — every future cycle's crafts will assimilate as they ship (the v0.7.x cycle did this in v0.7.5 P4). K is the historical catch-up, not the new pattern.

### T5 (mycorrhiza / P5 All-Things-Connected)

> 3-peer fixture network is still test code. P5 says federation across REAL substrates.

**Resolution**: full agreement. The 3-peer network is **not** production federation — it's the test infrastructure that proves `propagate()` handles N>1 destinations correctly without breaking when peers fail/diverge/collide. Production federation requires owner-decision: which sibling project (OPASSCC / ICML-Rebuttal / C3 / 3D-COT / etc.) becomes the first real peer. v0.7.10 ships the *infrastructure* so that decision becomes a 5-minute owner action when ready, not a v0.8 craft.

## Round 2 — Refinement

**Test count delta** (estimated):
- A: -10 to +5 (migration mostly delete-old-add-new-shaped)
- B: +12 (LB1 dim + edge cases)
- C: +12 (3-peer scenarios beyond the existing 5 single-peer tests)
- D/E/F: +30 (~10 each)
- G: +6 (HTTP smoke + OAuth flow)
- H: +8 (benchmark fixtures)
- I: +24 (8 demos × 3 happy-path tests)
- J: +6 (graft loader)

Total: ~+93. Going from 1601 → ~1694.

**Lint dim count**: 50 → **51** (LB1 added).

**Schema bump?**: NO. LB1 reads filesystem mtime + filename pattern from `docs/primordia/`; no canon mutation needed. Schema stays at v3.

**Files added/modified scope**: ~50 new + ~20 modified.

## Round 3 — Decision shape

**LANDED**.

Subagent dispatch (10 parallel opus, max-effort, ≥30-tool budget each per memory directive):
- 10 independent items run in parallel; aggregate wall-clock ≈ slowest single subagent.
- Owner-side work (K self-eat + L doctrine + M LB ratification) runs concurrently in main context.
- Single feat-omnibus commit + atomic bump commit + push + tag + CI + cloud verify.

**No rollback**: per the v0.7.x cycle's "Two-hour blast-radius rule" (now to be promoted to L2 doctrine via item L), every public-API change in this bundle is gate-(a) verified internally OR has telemetry hooks for gate-(b) verification post-ship. The propagate signature change in C is the largest API drift; mitigated by keeping the single-Path call shape as a thin wrapper over the new list-shape.

**Post-ship verification target**:
- PyPI 0.7.10, MCP Registry 0.7.10 isLatest=True, GH Release v0.7.10 with myco-0.7.10.zip
- substrate_pulse.contract_version = v0.7.10
- pytest 1690+ passed
- immune exit_code 0 (LB1 silent at v0.7.10 because Living Bets v0.7-MAJOR audit shipped 2026-05-10; MB8 silent because pytest no longer imports myco.mcp; SH2/MB8 transients normal during process restart)

## Cross-cutting risks acknowledged

1. **propagate API change**: the function currently takes `dst_root: Path`. Generalizing to `dst_roots: list[Path] | Path` is the kind of change that risks downstream breakage. Mitigation: preserve single-Path call site by wrapping; new tests exercise both shapes; no removal of single-shape support.

2. **Plugin loader integration**: `.myco/plugins/` machinery exists but has never been exercised. The reference plugin in J is the first real load. Risk: discovery code path may have bit-rot. Mitigation: subagent J reads the loader source first, writes the plugin to match exactly what the loader expects.

3. **OAuth mock provider**: the verification suite needs a Python-side OAuth 2.1 mock. Risk: mock differs from real provider behavior. Mitigation: subagent G uses the well-known `authlib` test patterns + documents the mock-vs-real gap.

4. **Historical self-eat batching**: 20+ docs through 3 stages = ~60 verb calls in serial. Risk: MCP server churn. Mitigation: batch eat as `path=docs/primordia/_landed/` (directory mode → 1 note per file, 1 verb call); single bulk assimilate; selective sporulation by version cluster.
