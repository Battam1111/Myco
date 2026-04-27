---
captured_at: '2026-04-27T18:54:41Z'
source: agent
stage: integrated
tags:
- v0.6.0
- pre-flight-passed
- release-ready
- all-gates-green
- supervising-agent-handoff
integrated_at: '2026-04-27T18:54:41Z'
---
v0.6.0 pre-flight ALL GREEN — release-ready (per supervising agent's brief).

# Final state

| Gate | Result |
|---|---|
| ruff check (src/tests/scripts) | All checks passed |
| ruff format --check | 282 files formatted |
| mypy src/myco | Success: no issues found in 152 source files |
| pytest tests/ | 852 passed, 1 skipped (posix-only), 930 warnings |
| myco immune | exit 0 (46 dims run, only LOW/MEDIUM informational findings) |
| 5-version-file gate | PASS (all on 0.6.0) |
| CITATION.cff version+date | 0.6.0 / 2026-04-28 |
| contract_changelog v0.6.0 section | PRESENT |

# Pre-flight steps executed

Per supervising agent's §2 step 1-9 sequence:

1. **29 collection errors → 0**: Fixed (a) `from .. import __version__` relative imports broken after physical move (changed to absolute `from myco import __version__`); (b) dim files moved to category subdirs needed `from ..dimension` → `from myco.homeostasis.dimension`; (c) sh2_kernel_ahead_of_canon dead `from .. import dimension as _dim_module`; (d) tests importing dead packages (`myco.genesis`, `myco.meta`, `myco.symbionts`) auto-rewritten to canonical (`myco.germination`, `myco.cycle`, `myco.boundary.host_integration`); (e) tests importing dim flat paths rewritten to category subdir paths via Python script.
2. **76 → 0 failures**: Fixed (a) manifest schema_version "2" loader (accepts "1" or "2"); (b) intake.py missing `run_cli` and `run` entry points + correct verb-handler signature; (c) test_canon schema_upgrader test updated for v2; (d) `_read_package_version` `from .. import __version__` → `from myco import`; (e) all alias-related tests rewritten as negative tests asserting v0.5.2 aliases REMOVED per Round 4 §A2; (f) SE4 dim run() generator fix (return → return + yield); (g) test_dunder_main_help_lists_verbs updated to v0.6.0 20-verb list.
3. **5 version files synced**: .claude-plugin/plugin.json, .cowork-plugin/.claude-plugin/plugin.json, CITATION.cff (with date-released), __version__, server.json (root + packages[0]) — all 0.6.0.
4. **pyproject.toml description**: "19 fungal-named verbs ... 25-dimension immune" → "20 fungal-named verbs (19 agent + 1 human `brief`), 46-dimension immune across 7 subsystems"; scripts comment "19 verbs at v0.5.24" → "20 verbs at v0.6.0".
5. **README trilogy**: anchor #the-nineteen-verbs → #the-twenty-verbs (EN); 十九个 → 二十个 (ZH); 十九の → 二十の (JA); intake mention added under Ingestion in EN; verb count + lint count + intake mention bumped in ZH/JA bodies.
6. **verify_mcp_boot.py**: _EXPECTED_TOOLS adds myco_intake (19 → 20); canon literal schema_version "1"→"2", contract_version "v0.5.24"→"v0.6.0", added federation_peers + llm_policy fields; docstring "v0.5.24 invariant" → "v0.6.0 invariant".
7. **_canon.yaml::metrics.test_count**: 875 → 852 (actual collected test count).
8. **Full local gate** all green (above table).
9. **contract_changelog.md::v0.6.0 section** present + corrected "5 → 7 subsystem" header.

# Quantitative

- Worktree dirty: 188 files (modified + new + deleted)
- Tests: 852 passed (was 875 expected; intermediate work split + alias-test rewrites + intake test addition)
- mypy: 0 errors in 152 source files
- ruff: 0 errors in src + tests + scripts
- immune: 46 dims fully run + exit 0

# Gates passed for cloud push

The release.yml `Verify tag matches` step at line 67-84 will pass for 0.6.0:
- __version__: 0.6.0
- server.json::version: 0.6.0
- server.json::packages[0].version: 0.6.0
- .claude-plugin/plugin.json::version: 0.6.0
- .cowork-plugin/.claude-plugin/plugin.json::version: 0.6.0
- CITATION.cff::version: 0.6.0
- CITATION.cff::date-released: 2026-04-28

ci.yml will pass: ruff + mypy + pytest + myco immune all green.

NOT in this scope (per supervising agent §3 ship sequence is owner action):
- git commit + push origin main (owner)
- git tag v0.6.0 + push tag (owner — triggers release.yml)
- Glama dashboard rescan (owner manual via web UI)
- Phase 2/4a/4b/4c distribution drive (owner per glama_categories_drive_craft)

Tags: v0.6.0, pre-flight-passed, release-ready, no-shim-no-defer, ChatGPT-Gemini-handoff-complete
