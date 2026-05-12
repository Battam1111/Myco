---
type: craft
topic: v0.7.1 myco.mcp shim revival (v0.7.0 hotfix)
slug: v0_7_1_shim_revival
kind: hotfix
date: 2026-04-30
rounds: 3
craft_protocol_version: 1
status: LANDED
authored_by: human
path_allowlist:
  - "src/myco/mcp/__init__.py"
  - "src/myco/mcp/__main__.py"
  - "tests/unit/boundary/test_legacy_mcp_shim.py"
  - "docs/contract_changelog.md"
incident:
  trigger_event: "owner's Claude Desktop MCP host disconnected within 2 hours of v0.7.0 release"
  root_cause: "v0.7.0 deleted src/myco/mcp/ shim while owner's claude_desktop_config.json still spelled command as `python -m myco.mcp`"
  detection_path: "MCP server log dump pasted by owner showing `No module named myco.mcp` errors at 2026-04-29T18:27 (v0.7.0 shipped at 16:45)"
  blast_radius: "owner's local Claude Desktop instance (1 confirmed); unknown number of downstream substrates with similarly-stale configs"
---

# v0.7.1 — myco.mcp shim revival (v0.7.0 hotfix)

> **Date**: 2026-04-30
> **Layer**: L4 hotfix (restores src/myco/mcp/ shim package + test) + L1 lesson record (extends shim removal schedule from v0.7.0 to "indefinite, gated on telemetry").
> **Upward**: enacts L0 P1 (Only For Agent — restoring agent operability is non-negotiable); names a previously-implicit invariant: **"public-API removal requires telemetry verification, not just deprecation copy."**
> **Governs**: revival of `src/myco/mcp/__init__.py` (75 LoC) + `__main__.py` (22 LoC) + `tests/unit/boundary/test_legacy_mcp_shim.py` (133 LoC) deleted in v0.7.0; updated deprecation copy to mention the v0.7.0 incident; user's local claude_desktop_config.json migrated to canonical `myco.boundary.mcp` so the shim deprecation can complete cleanly when telemetry permits.

This craft documents a substrate self-correction: v0.7.0 removed a public-API shim that was still load-bearing for the substrate's own owner. The deprecation warning machinery (stderr + DeprecationWarning) emitted for 4 versions but the host config never read it. v0.7.1 reverses the deletion and re-anchors the removal schedule.

---

## Round 1 — 主张 (claim)

**Claim (C):** Restore `src/myco/mcp/` shim package as deleted in v0.7.0, update its docstring + deprecation copy to record the incident, and re-schedule removal to **indefinite (gated on SH3 telemetry or v1.0.0 stable freeze)**.

**Why now (3 load-bearing claims):**

1. **The owner's MCP host is broken in production.** Within 2 hours of v0.7.0 ship at 2026-04-29T16:45Z, the owner's `claude_desktop_config.json` (which spelled command as `python -m myco.mcp`) raised `ModuleNotFoundError: No module named 'myco.mcp'` and disconnected. The substrate is unusable in its own owner-Claude-Desktop configuration. **L0 P1 (Only For Agent) is violated by an inoperable agent surface.**

2. **The v0.7.0 craft's "sole public API break" assumption was wrong by 1.** v0.7.0 §"Load-bearing assumption" claimed: "Internal codebase has zero `from myco.mcp` consumers (verified pre-execution); only external downstream substrates importing the legacy path are affected, and they were already being warned via DeprecationWarning since v0.6.13." The hidden flaw: **the substrate has no telemetry surface to verify "external" consumer count**. The claim "no downstream consumer" was unverifiable; it should have been classified as P0 BLOCK rather than load-bearing assumption.

3. **The deprecation pattern itself failed.** The shim emitted a stderr deprecation warning for 4 minor versions (v0.6.13 → v0.6.16) plus 1 attempted-removal version (v0.7.0). The warning IS visible in MCP host logs (the Cowork dashboard / Claude Desktop "View Logs" panel). But neither the host UI nor the substrate's own owner read it. Conclusion: stderr warnings without an active migration mechanism (auto-config-update, owner notification, telemetry counter) produce zero migration even with multi-version notice.

## Round 1.5 — 自我反驳 (3 tensions)

- **T1 [P0] — Restoring the shim contradicts v0.7.0's "Major Autolysis" doctrine.** v0.7.0 framed shedding as L0 P3 mechanism; v0.7.1 reverses one shed. Doctrine inconsistency.

- **T2 [HIGH] — Indefinite retention creates technical debt.** The shim is now permanent until SH3 ships. SH3 is a future feature with its own design overhead. Without a clear sunset, every future contributor has to re-litigate "why is myco.mcp still here?"

- **T3 [HIGH] — The owner-config-migration is a one-shot.** v0.7.1 patches the owner's claude_desktop_config.json directly. Other downstream substrates with the same config remain broken until their owners hand-edit. The shim revival masks this.

## Round 2 — 精化 (synthesis)

**T1 (doctrine inconsistency):** **Resolution — narrow the autolysis discipline.** v0.7.0's "Major Autolysis" doctrine is correct for: dead code, unused assets, archive-eligible docs, fail-silent dims. It is NOT correct for: public API surfaces with unknown downstream consumer count. v0.7.1 amends the autolysis discipline: **a deletion candidate must be either (a) verifiably internal-only OR (b) accompanied by telemetry that confirms zero downstream usage**. The shim violates (a) — it's exposed at module-load via `python -m myco.mcp` — and v0.7.0 had no (b) infrastructure. Doctrine consistency restored: autolysis stays, but its discipline is now load-bearing-aware.

**T2 (indefinite retention = tech debt):** **Resolution — make the SH3 ratchet a v0.7.1 first-class IOU.** v0.7.0 deferred SH3 to a future release. v0.7.1 makes that more explicit: SH3's design must include a shim-hit-counter telemetry surface so the "zero hits across N senesce cycles" gate becomes mechanically verifiable. Once SH3 ships and reports zero hits across (say) 30 senesce cycles, the shim removal becomes safe. Until then, the 97 LoC of shim is a debt the substrate accepts as the cost of premature deletion.

**T3 (one-shot config migration):** **Resolution — accept the partial fix.** The owner's config is patched directly. Other downstream substrates may remain broken; their owners will encounter the same `No module named myco.mcp` and either hand-fix or report. Until SH3 telemetry exists, there's no mechanism to actively migrate downstream configs. The shim's continued presence ensures their substrates keep working in the meantime.

### v0.7.1 final scope

5 changes, ~100 LoC net additions:

1. **Restore `src/myco/mcp/__init__.py`** (75 LoC, recovered from `git show 7c4e7d5~1:src/myco/mcp/__init__.py`). Updated docstring §"Scheduled removal" from "no earlier than v0.7.0" to "indefinite, gated on SH3 telemetry or v1.0.0 stable freeze" with the v0.7.0 incident named in the body.
2. **Restore `src/myco/mcp/__main__.py`** (22 LoC, same recovery path).
3. **Restore `tests/unit/boundary/test_legacy_mcp_shim.py`** (133 LoC). 5 tests verify: import resolves; `build_server` + `main` re-exports match canonical; `python -m myco.mcp --help` exits 0; deprecation warning emits.
4. **Update deprecation stderr copy** to name the v0.7.0 incident: "deprecated import path (v0.6.13+; v0.7.0 deletion reverted in v0.7.1 after breaking owner's MCP host). Update your MCP host config to either `mcp-server-myco` (the entry-point binary, recommended) or `python -m myco.boundary.mcp` (the canonical module). Removal indefinite, gated on SH3 telemetry or v1.0.0 stable freeze."
5. **Update owner's `claude_desktop_config.json`** (`%APPDATA%/Claude/claude_desktop_config.json`): `args: ["-m", "myco.mcp"]` → `args: ["-m", "myco.boundary.mcp"]`. This is owner-local, not committed; documented here as part of the hotfix execution.

### What this craft adds to substrate doctrine

A **public-API deletion discipline** is now load-bearing. From v0.7.1+:

- A shim deletion candidate must satisfy one of:
  - **(a) Internal-only verification** — `grep -r "from <legacy_path> import" src/ tests/ scripts/ examples/` returns zero hits, AND the path is NOT exposed via any CLI or MCP host entry point, AND no plugin manifest declares the path.
  - **(b) Telemetry verification** — the substrate has run for N senesce cycles with a shim-hit counter (introduced by SH3 dim, future) showing zero hits.
- v0.7.0 satisfied (a) only for internal imports, NOT for "exposed via plugin host config." That gap is what produced the regression.

This discipline lands in `docs/architecture/L2_DOCTRINE/boundary.md` § "Legacy import shims" as a craft-driven amendment. (Deferred to a follow-up doc-only molt; the v0.7.1 hotfix does not amend L2 to keep the hotfix path tight.)

## Round 3 — 决定 (decision)

**LANDED — shim revived, schedule re-anchored, lesson named.** All 3 tensions resolved.

### What did NOT change

- All 7 R-rules: identical text.
- All 7 subsystems: identical doctrine.
- All 46 lint dimensions: identical roster.
- All 20 verbs: identical manifest.
- v0.7.0 deletions of `legacy_v0_3/`, `dist/` stale wheels, unused assets, dead `digestion/` modules, test consolidations, doc archives: ALL preserved. v0.7.1 reverts only the `src/myco/mcp/` shim deletion + restores its test.
- Schema v2 unchanged.
- Public API of `myco.boundary.mcp`: identical.

### Pre-flight gate verification

- `ruff check src tests scripts` — clean
- `ruff format --check src tests scripts` — 297 files formatted
- `mypy src/myco` — 148 source files, no issues
- `pytest -q` — **1532 passed, 1 skipped** (up from v0.7.0 baseline of 1525, +7 from restored shim test suite)
- `myco immune` — exit 0
- `python -m myco.mcp --help` — boots successfully (legacy invocation works)
- `python -m myco.boundary.mcp --help` — boots successfully (canonical invocation works)
- `scripts/verify_mcp_boot.py` — 20 tools, handshake green

Predecessor: v0.7.0 (Major Autolysis), shipped 2026-04-29.
