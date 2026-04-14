# Changelog

All notable changes to this project are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## v1.1.2 — 2026-04-14

### Features
- feat: wave b/c/d — 9-symbiont auto-setup + hosts→symbionts + doctor/diagnose→pulse

## v0.6.1 — 2026-04-14

### Bug Fixes
- fix(ci): restore truncated Publish-to-PyPI step in auto-release.yml
- fix(ci): allow scoped conventional commits like fix(lint): to trigger auto-release
- fix(lint): skip .claude worktrees + update stale 26->29 / 19->25 numeric claims
- fix(release): inline PyPI publish + patch-only + CHANGELOG walkback

## v0.6.0 — 2026-04-14

### Features
- feat: Wave 57/58 zero-touch Agent reflex + self-loop

### Bug Fixes
- fix(release): push annotated tags so gh release create finds them. Root cause of v0.4.0 / v0.5.0 release failures: git tag creates lightweight tags by default, and git push --follow-tags only pushes annotated tags.

## v0.5.0 — 2026-04-14

### Features
- feat(zero-touch): Wave 56 W1 — first-contact auto-seed, claude_hint, session-end hook
- feat: vision-closure mechanisms G1–G9 — 9-subsystem substrate upgrade (foraging, truth immune, aggressive excretion, self-evolution, cross-project conduction, zero-touch hooks, protocol adherence, PyPI auto-release)
- feat: L25 Cross-Layer Interconnection Health + `compute_interconnection_map()`
- feat: universal interconnection — L2 auto-discovery + L19 full-project scan
- feat: absorption gates + perfusion + synaptogenesis
- feat: auto-register metabolic cycle scheduled task on first boot
- feat: `myco connect` creates full automation stack; global install via `MYCO_ROOT` env var

### Bug Fixes
- fix: complete dimension count update in all cited_in files
- fix: extract/integrate tests for absorption gate
- fix: metabolic cycle audit — dual-mode skills, step numbering, dedup settings
- fix: restore `_canon.yaml` + `log.md` + `MYCO.md` to git (required for CI + immune)

### Refactors
- refactor: substrate identity upgrade + Wave archival + terminology sweep
- rename: `myco-knowledge-system` plugin to `myco`

### Chores
- chore: gitignore internal operations data (`log.md`, `_canon.yaml`, `MYCO.md`, `marketing/`)
- chore: normalize line endings in `seed_cmd.py`

> Note: v0.4.0 was tagged on the same day during infrastructure bring-up; its
> commit set is a strict subset of v0.5.0 and is therefore not listed
> separately here. The auto-release tagging bug that produced the overlap
> was fixed in commit 1701758 (annotated tags + explicit push).

## v0.3.1 — 2026-04-13

### Bug Fixes
- fix: use absolute URL for logo in README (PyPI compatible)

## v0.3.0 — 2026-04-13

### Features
- biomimetic naming alignment across all documents
- Wave archival + terminology sweep

## v0.2.0 — 2026-04-12

Initial public pre-release.
