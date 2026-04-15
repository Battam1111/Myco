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
- **Official Claude-Code / Cowork plugin bundle** (Stage D.3). The
  repo root now ships a full plugin manifest tree alongside the
  Python source: `.claude-plugin/plugin.json`, a one-plugin
  `marketplace.json`, a `.mcp.json` pointing at `python -m myco.mcp`,
  a `hooks/hooks.json` wrapping SessionStart → `hunger` and
  PreCompact → `session-end`, and two slash skills under `skills/`
  (`/myco:hunger`, `/myco:session-end`). Users install with:

        /plugin marketplace add Battam1111/Myco
        /plugin install myco@myco

  The plugin tree coexists with the project's own `.claude/` folder;
  the two do not conflict because `.claude/` is the dogfooding config
  for the Myco repo itself while `.claude-plugin/` + root-level files
  are the distribution artifact.
- **Plugin-bundle structural tests** (Stage D.3). A new
  `tests/integration/test_plugin_bundle.py` validates the manifest
  shape, version-alignment with `myco.__version__`, hooks wiring, and
  skill-frontmatter completeness so a malformed plugin cannot ship
  silently.
- **Write-surface extended** (Stage D.3). `_canon.yaml` now whitelists
  `.claude-plugin/**`, `.mcp.json`, `hooks/**`, and `skills/**` so
  future plugin-file edits stay within R6 without a doctrine bump.
- **Trilingual README install flow updated** (Stage D.3). The English,
  Chinese, and Japanese READMEs now document the plugin install path
  alongside the manual-copy fallback, and the "ships in v0.4.1"
  forward-looking paragraphs are replaced with current-state prose.
- **`CONTRIBUTING.md`** (Stage D.4). Root-level contributor guide,
  roughly 1100 words. Sections: welcome (dual human + agent
  audience), before-you-start, dev environment, daily loop, the
  top-down L0–L3 rule, the three-round craft convention, what agents
  should do differently, what not to touch without discussion, PR
  checklist, AI-assisted contributions, bug reports, internal commit
  style (optional for external contributors), governance, code of
  conduct. The READMEs' `*(v0.4.1)*` placeholder marker on the
  `CONTRIBUTING.md` link is removed now that the file exists.
- **`mcp-server-myco` console script** (Stage D.5). `pyproject.toml`
  now declares a second entry point alongside `myco`, following the
  community `mcp-server-<name>` convention. Every MCP host config
  (Cursor, Windsurf, Zed, Codex, Gemini, Continue, Claude Desktop,
  LangChain / CrewAI / DSPy) can now just point at
  `command: "mcp-server-myco"` without having to reason about
  `python` vs `python3` aliasing or which venv the host will spawn.
  Usable via `pipx install 'myco[mcp]'` or
  `uvx mcp-server-myco` for zero-venv install.
- **Cross-platform install matrix** (Stage D.5). Trilingual READMEs
  now carry an eight-row table covering every MCP-supporting host
  on the 2026-04 landscape — each row is the exact config path and
  the exact line to paste. Aider is flagged as awaiting upstream MCP
  support (aider-ai/aider #4506).
- **`substrate_pulse` sidecar + initialization instructions**
  (Stage D.5). `myco.surface.mcp.build_server` now attaches a
  `substrate_pulse` field to every MCP tool response (current
  `substrate_id`, `contract_version`, and a rule hint that escalates
  from R1 → R3 once `myco_hunger` has fired), and populates the
  FastMCP `instructions` block with a compact R1–R7 summary linking
  to `docs/architecture/L1_CONTRACT/protocol.md`. This is the
  cross-platform analogue of the Claude-Code SessionStart hook:
  every MCP client (Cursor, Windsurf, Zed, Codex, Gemini, Continue,
  Claude Desktop) sees it without any host-side configuration.
- **"Stable kernel, mutable substrate" positioning** (Stage D.5).
  Trilingual READMEs swap the stale "v0.4.0 — Greenfield Rewrite"
  banner for a positioning line that names the design split
  explicitly: `pip install` locks the kernel; substrate evolution
  runs via the twelve MCP verbs. Contributor editable-install path
  is promoted into Quick Start.
- **Release-ephemerals excluded from sdist** (Stage D.5).
  `pyproject.toml` gains explicit `[tool.hatch.build.targets.sdist]`
  include/exclude lists so `.release_notes_*.md`, `upload*.log`,
  `dist/`, `build/`, `legacy_v0_3/`, `.pytest_cache/`, and every
  `__pycache__/` stay out of the PyPI tarball even if they happen
  to sit in the working tree at build time. `.gitignore` gains the
  same patterns as belt-and-suspenders.
- **Hook commands prefer `myco` over `python -m myco`**
  (Stage D.5). Both `hooks/hooks.json` (plugin) and
  `.claude/settings.local.json` (dogfooding) now invoke the `myco`
  console script rather than `python -m myco`, closing the same
  `python` / `python3` / venv gap the MCP launcher just closed.

### Planned

*(empty — the four v0.4.1 promises are all landed; Stage E is the
release itself.)*

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
