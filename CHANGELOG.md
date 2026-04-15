# Changelog

All notable changes to Myco are recorded here. This changelog tracks the
**package version** (`src/myco/__init__.py::__version__`). Contract-layer
changes (L0/L1/L2 doctrine) are recorded separately in
`docs/contract_changelog.md`.

The pre-rewrite changelog is preserved at `legacy_v0_3/CHANGELOG.md`.

Format: roughly [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## [Unreleased] — `0.4.1.dev`

First maintenance release after the greenfield rewrite. Scope is fixed
by the four explicit promises in the v0.4.0 release notes and the
README roadmap line. No other features are in scope for this release.

### Added

- **`[mcp]` optional-dependency target** (Stage D.1). `pyproject.toml`
  now declares `mcp = ["mcp>=1.2"]` so `pip install "myco[mcp]"` pulls
  the Model Context Protocol SDK alongside the package. Lower bound of
  1.2 covers `FastMCP.run()`, the synchronous stdio entry point that
  `python -m myco.mcp` relies on; the rest of the 1.x line is accepted
  because the low-level API has been stable across all 1.x releases.
- **`python -m myco.mcp` standalone launcher** (Stage D.2). New
  `src/myco/mcp/` subpackage with an `__init__.py` that re-exports
  `build_server` and a `main()` entry, plus a thin `__main__.py` that
  wires argparse to `FastMCP.run`. Three transports are selectable
  (`--transport {stdio, sse, streamable-http}`, default `stdio`). When
  the MCP SDK is not installed the launcher fails loud with a single
  sentence telling the user to `pip install 'myco[mcp]'` and a POSIX
  exit code of 2 — never a raw `ImportError` traceback. Library users
  who embed the server in their own process can import the shared
  `build_server` directly.

### Planned

- **Official `.plugin` bundle.** A Cowork / Claude-Code plugin packaging
  Myco's CLI, the manifest-driven MCP server, and the existing
  `.claude/hooks/` wiring. Drop-in install target.
- **`CONTRIBUTING.md`.** Repo root. Covers dev install, test runner,
  three-round craft convention, where architectural changes land, and
  commit-message style.

### Changed

- **Package description cleaned** (Stage D.1). `pyproject.toml` no
  longer self-describes as "v0.4.0 greenfield rewrite" in its PyPI
  summary; that phrasing was accurate at the v0.4.0 release and stale
  the moment v0.4.1 became the development head.

### Post-release hygiene from v0.4.0 (Stage C.7)

- **Scaffold version assertion is now version-agnostic.** The Stage A/B
  sanity test previously hard-coded `"0.4.0.dev"`; it now accepts any
  PEP 440 release or `.dev` marker via regex. Release bumps no longer
  force a test edit.
- **`myco --help` reports `__version__` dynamically** instead of a
  hard-coded `"v0.4.0"` literal. The description line is now derived
  from the SSoT at `src/myco/__init__.py`.
- **CHANGELOG.md header corrected.** The v0.4.0 release commit
  (Stage C.4, `198470f`) left the header as `[Unreleased] — 0.4.0.dev`;
  this is now promoted to a proper `[0.4.0] — 2026-04-15` section with
  a fresh `[Unreleased]` segment above.
- **v0.4.1 handoff brief landed** at
  `docs/primordia/agent_handoff_v0_4_1_2026-04-15.md` — onboarding doc
  for the session that executes the four promises above.

---

## [0.4.0] — 2026-04-15

Greenfield rewrite release. Backward-incompatible with v0.3.x. The
pre-rewrite codebase (v0.3.4 lineage) is preserved at tag
`v0.3.4-final`; consumers (e.g. ASCC) remain pinned there until they
migrate via the fresh re-export path.

### Added

- **Eight-package source layout** under `src/myco/`: `core`, `genesis`,
  `ingestion`, `digestion`, `circulation`, `homeostasis`, `surface`,
  `symbionts`. Each subsystem maps to a biological role per L0's
  authoritative metaphor table.
- **Twelve verbs, manifest-driven.** `genesis` · `hunger` · `eat` ·
  `sense` · `forage` · `reflect` · `digest` · `distill` · `perfuse` ·
  `propagate` · `immune` · `session-end`. The single source of truth is
  `src/myco/surface/manifest.yaml`; CLI and MCP surfaces are both
  derived from it. Adding a verb edits the manifest, not `cli.py` or
  `mcp.py`.
- **Eight lint dimensions** authored fresh (not ported from v0.3's
  30-dim table):
  - Mechanical: M1 (canon identity), M2 (entry-point exists),
    M3 (write-surface declared).
  - Shipped: SH1 (package-version ref resolves).
  - Metabolic: MB1 (raw-notes backlog), MB2 (no integrated yet).
  - Semantic: SE1 (dangling refs), SE2 (orphan integrated).
- **Seven L1 hard rules (R1–R7)** with explicit mechanical /
  disciplinary enforcement mapping. See
  `docs/architecture/L1_CONTRACT/protocol.md`.
- **`_canon.yaml`, `MYCO.md`, `.claude/hooks/`** materialized fresh at
  the repository root. The SessionStart hook fires `myco hunger`; the
  PreCompact hook fires `myco session-end`.
- **ASCC substrate migrator** at `scripts/migrate_ascc_substrate.py`
  (dry-run default, `--execute` opt-in). Maps v0.3 canon fields into
  the v0.4 schema per the "fresh re-export" discipline.
- **Trilingual READMEs** (`README.md`, `README_zh.md`, `README_ja.md`)
  ported to the new surface.
- **Assets** — `assets/_gen_logo.py` generator plus produced PNGs
  referenced by the READMEs (restored Stage C.6 after an overly broad
  Stage C.4 sweep).

### Architecture

- **L0–L3 top-down design** landed under `docs/architecture/`. Five
  root principles (Only For Agent / 永恒吞噬 / 永恒进化 / 永恒迭代 /
  万物互联), three derived invariants, seven L1 hard rules, five
  biological subsystems, eight-package L3 map. Governing crafts:
  `docs/primordia/greenfield_rewrite_craft_2026-04-15.md` and
  `docs/primordia/l0_identity_revision_craft_2026-04-15.md`.
- **Single-path rewrite discipline** — v0.4 code is written directly
  into `src/myco/`, not under a `src/myco_v4/` staging path. No v4
  marker appears anywhere in paths, package names, or commit subjects.
  Rationale in
  `docs/architecture/L3_IMPLEMENTATION/migration_strategy.md`.
- **Contract changelog separation.** `docs/contract_changelog.md` now
  tracks L0/L1/L2 doctrine changes separately from this package
  changelog. First entry records the v0.4.0 contract surface and the
  break from v0.3.x.

### Removed

- **Pre-rewrite quarantine (`legacy_v0_3/`) removed from the working
  tree.** Git history is preserved; tag `v0.3.4-final` is the sole
  anchor for the pre-rewrite lineage.
- **v0.3 30-dimension lint table** superseded by the fresh 8-dimension
  set above.

### Release mechanics

- Annotated tag `v0.4.0` (`git tag -a`, never lightweight).
- GitHub release published at `Myco-v0.4.0`.
- PyPI upload: wheel + sdist, `PYTHONIOENCODING=utf-8` plus
  `--disable-progress-bar` to survive the GBK Windows console.

---
