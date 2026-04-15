# Changelog

All notable changes to Myco are recorded here. This changelog tracks the
**package version** (`src/myco/__init__.py::__version__`). Contract-layer
changes (L0/L1/L2 doctrine) are recorded separately in
`docs/contract_changelog.md`.

The pre-rewrite changelog is preserved at `legacy_v0_3/CHANGELOG.md`.

Format: roughly [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versioning: [SemVer](https://semver.org/).

---

## [Unreleased]

*(next development head, no entries yet)*

---

## [0.4.1] — 2026-04-15

First maintenance release after the v0.4.0 greenfield rewrite.
Ships the four public promises (`[mcp]` extras, `python -m myco.mcp`
launcher, official plugin bundle, `CONTRIBUTING.md`) plus two
cross-platform passes that turn "works in Claude Code" into "works
across every active MCP host on the 2026-04 landscape," plus a
narrative rewrite that positions Myco as the substrate that
ingests other frameworks rather than yet another framework that
gets replaced.

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
- **`myco-install` one-command installer for seven MCP hosts**
  (Stage D.6). New `src/myco/install/` subpackage; third console
  script `myco-install`. Writes the correct schema per host
  (handles the four dominant schema variants: `mcpServers` JSON,
  `context_servers` JSON, `servers` JSON with `"type": "stdio"`, and
  OpenClaw's CLI-mediated `mcp.servers` nesting). Preserves any
  sibling servers in existing config files; idempotent; supports
  `--dry-run`, `--global`, `--uninstall`. Covers Claude Code,
  Claude Desktop, Cursor, Windsurf, Zed, VS Code, OpenClaw. Remaining
  hosts documented with per-platform snippets in
  [`docs/INSTALL.md`](docs/INSTALL.md).
- **OpenClaw support** (Stage D.6). OpenClaw uses a nested
  `mcp.servers.<name>` schema mutated via its own `openclaw mcp set`
  CLI, not the standard `mcpServers` key at repo root. The
  `myco-install openclaw` path shells out with the correct payload;
  documentation surfaces both the one-line helper and the manual
  path. Addresses the long-tail platform story the mainline
  "one snippet everywhere" framing cannot cover.
- **`docs/INSTALL.md` — comprehensive per-host matrix** (Stage D.6).
  New top-level install guide listing every MCP host active on the
  2026-04 landscape with the exact config path and exact line for
  each: `mcpServers`-family (11 hosts), VS Code, Zed, OpenClaw,
  OpenHands (TOML), OpenCode / Kilo Code (`mcp` key), Codex CLI
  (TOML), Goose (YAML), Warp (`mcp_servers`), Continue (YAML block),
  JetBrains AI, Devin (UI form), Bolt.new (UI form), Claude Desktop
  (three OS paths). Plus Python-framework adapter snippets for
  LangChain / CrewAI / DSPy / Smolagents / Agno / PraisonAI /
  Microsoft Agent Framework / Claude Agent SDK. Hosts without
  native MCP (Aider CLI, SWE-agent, Void) are flagged explicitly so
  users do not waste time there.
- **Narrative README rewrite** (Stage D.6). The "What it is"
  opening, five-principles block, and three-roles framing are
  re-authored across all three language READMEs (English, Chinese,
  Japanese) to embody rather than merely mention L0's five root
  principles. Every principle gets a one-sentence practical
  phrasing plus a consequence. The three roles name concrete
  behaviors instead of abstract nouns ("Myco runs a metabolism ...
  `hunger`, `eat`, `reflect / digest / distill`, `immune`,
  `propagate`"). Structure stays identically lined (169 lines each).
- **"Substrate that ingests frameworks" positioning + em-dash
  cleanup** (Stage D.7). Second pass on the trilingual READMEs
  tightening the core claim that sets Myco apart from competitors:
    * **Devour everything** is broadened to include code repositories,
      framework documentation, datasets, and papers by name (not
      just "notes and decisions"). The tagline is hardened to "not
      a framework, a substrate that ingests frameworks."
    * **Self-evolving shape** promises that even a complete internal
      rewrite remains a `myco` version bump, not a new dependency.
      The underlying substrate is never thrown away; users never
      migrate again. This is the real differentiator from every
      "agent framework" or "memory layer" on the market.
    * The rewrite explicitly frames why it works now and could not
      work before: "Agents are finally intelligent enough to
      maintain the system themselves; earlier attempts died because
      humans could not keep up."
    * Zero em-dashes across all three language READMEs. Replaced
      with colons, commas, parentheses, or sentence splits. The
      reading cadence now relies on full stops and clear nouns,
      which survives translation to CJK densities better than
      em-dash-heavy English. Word counts: en 1353, zh 636, ja 632.

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
