# Changelog

All notable changes to Myco are recorded here. This changelog tracks the
**package version** (`src/myco/__init__.py::__version__`). Contract-layer
changes (L0/L1/L2 doctrine) are recorded separately in
`docs/contract_changelog.md` (created at Stage C).

The pre-rewrite changelog is preserved at `legacy_v0_3/CHANGELOG.md`.

Format: roughly [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## [Unreleased] — `0.4.0.dev`

Greenfield rewrite in progress. The pre-rewrite codebase (v0.3.4 lineage)
is quarantined in `legacy_v0_3/` and will be removed at the v0.4.0
release commit.

### Added

- **Stage A scaffold.** Fresh `pyproject.toml` (Hatchling dynamic version,
  SSoT at `src/myco/__init__.py`), `src/myco/` with eight packages
  (`core`, `genesis`, `ingestion`, `digestion`, `circulation`,
  `homeostasis`, `surface`, `symbionts`), mirror `tests/` layout, and a
  sanity test verifying every package imports and `myco.__version__`
  equals `"0.4.0.dev"`. See
  `docs/primordia/stage_a_scaffold_craft_2026-04-15.md`.

### Architecture

- **L0–L3 authoritative design** landed under `docs/architecture/`. Five
  root principles (Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
  万物互联), seven L1 hard rules, five biological subsystems, eight-package
  L3 map. Governing crafts:
  `docs/primordia/greenfield_rewrite_craft_2026-04-15.md` and
  `docs/primordia/l0_identity_revision_craft_2026-04-15.md`.

### Notes

- This entry will be split into proper `Added` / `Changed` / `Removed`
  sections as Stage B lands each subsystem.
- The `0.4.0.dev` suffix is dropped at Stage C when `_canon.yaml`,
  `MYCO.md`, and the ASCC migration script are authored and
  `legacy_v0_3/` is deleted.
