# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## v0.4.0 — 2026-04-14

### Features
- feat: L25 Cross-Layer Interconnection Health + compute_interconnection_map()
- feat: universal interconnection - L2 auto-discovery + L19 full-project scan
- feat: absorption gates + perfusion + synaptogenesis
- feat: auto-register metabolic cycle scheduled task on first boot
- feat: myco connect now creates full automation stack
- feat: global Myco install — myco connect + MYCO_ROOT env var

### Bug Fixes
- fix: complete dimension count 23 to 25 update in all cited_in files
- fix: update lint dimension count 23 to 25 for L23/L24
- fix: update extract/integrate tests for absorption gate
- fix: metabolic cycle audit — dual-mode skills, step numbering, dedup settings
- fix: restore _canon.yaml + log.md + MYCO.md to git (required for CI + immune)

### Refactors
- refactor: substrate identity upgrade + Wave archival + terminology sweep

### Chores
- chore: remove temp files
- chore: normalize line endings in seed_cmd.py
- chore: gitignore log.md + _canon.yaml (internal operations data)
- chore: gitignore MYCO.md (internal operations dashboard, not for public)
- chore: gitignore marketing/

### Other
- ﻿feat: vision-closure mechanisms G1-G9 鈥?9-subsystem substrate upgrade Implements the 9-mechanism vision-closure roadmap from docs/primordia/vision_closure_craft_2026-04-14.md to convert Myco's README promises from vision into operational reality. Partition A (notes metabolism pipeline): - G3 Truth Immune: freshness/last_verified/quarantine fields, myco verify   command, L26 Freshness Debt lint dimension - G4 Aggressive Excretion: multi-path prune detection (orphan + superseded   + low-value-raw + quarantine-stale), supersedes field, prune --auto - G5 Engine Self-Evolution: metabolism.jsonl logging, myco introspect   trend detector - G6 Cross-Project Conduction: auto project tagging, colony --global   clustering, cross_project wiki promotion, private-visibility support Partition B (intelligence + host layer): - G1 Autonomous Foraging: .myco_state/feeds.yaml subscriptions, arxiv/RSS   pulling via stdlib, immune filter (Jaccard dedup + interests + license),   myco_scent MCP tool for opportunistic Agent-triggered forage - G2 Semantic Gap Prediction: replaced word-frequency noise with three-   source topic extraction (user-turns + misses + orphan raws) scored   against wiki coverage - G7 Zero-touch Hooks: src/myco/hosts/ adapters (cowork/claude_code/   cursor/vscode), degradation ladder, myco doctor command with --fix - G8 Protocol Adherence: L27 lint dimension scanning session patterns   for eat/digest imbalance, miss recovery, boot hunger trigger Infrastructure: - G9 PyPI Release Automation: .github/workflows/auto-release.yml (conv-   commit semver driver), scripts/bump_version.py, scripts/generate_   changelog.py, L28 PyPI Sync lint dimension Canon updates: lint_dimensions 26->29 (L26/L27/L28 added), mcp_tool_count 19->20 (myco_scent), test_count 282->372. All 372 tests pass (90 new across 8 test files). Zero external runtime deps added; all new code uses stdlib only. Authoritative design: docs/primordia/vision_closure_craft_2026-04-14.md Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
- rename: myco-knowledge-system plugin to myco + sync READMEs
- Update README.md
