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

## [0.5.0] — 2026-04-17

Closes all five MAJOR gaps from the v0.4.1 post-release audit
(`docs/primordia/v0_4_1_audit_craft_2026-04-15.md`). The README's
"the substrate changes shape with the work" (L0 principle 3,
永恒进化) and "you never migrate again" promises are now mechanically
backed, not aspirational prose. The governing three-round craft is
`docs/primordia/v0_5_0_major_6_10_craft_2026-04-17.md`.

### Added

- **MAJOR 6 — Dimension registration via entry-points.**
  `pyproject.toml` now declares every built-in lint dimension under
  `[project.entry-points."myco.dimensions"]`. Third-party substrates
  register their own dimensions the same way — no fork of Myco, no
  source edit, just a single row in their own `pyproject.toml`.
  Discovery is driven by
  `importlib.metadata.entry_points(group="myco.dimensions")`; the
  hardcoded `_BUILT_IN` tuple (renamed from `ALL`) is a dev-checkout
  fallback that fires a `DeprecationWarning` when used. Broken
  third-party entry-points are skipped with a `UserWarning` rather
  than killing the kernel.
- **`myco immune --list`** enumerates every registered dimension
  (id / category / default_severity / one-line summary) without
  running any of them. Output is sorted by id; safe on any
  substrate.
- **`myco immune --explain <dim>`** prints the dimension's class
  docstring as prose. `--list` and `--explain` are mutually
  exclusive; passing both raises `UsageError`.
- **MAJOR 7 — `MF1` lint dimension.** Mechanical / HIGH: every
  `canon.subsystems.<name>.package` path must resolve to an
  existing directory under substrate root. Silent when a subsystem
  entry has no `package:` field (documentation-only subsystems stay
  valid). The first cross-check between the canon's `subsystems`
  block and the actual package layout.
- **MAJOR 8 — Forward-compatible canon reader.** An unknown
  `schema_version` in `_canon.yaml` now emits a `UserWarning` and
  proceeds best-effort instead of raising `CanonSchemaError`. A new
  module-level registry `myco.core.canon.schema_upgraders:
  dict[str, Callable]` is the seam for future v1→v2 in-code
  upgraders (chain-applied; cycle-detected). Empty at v0.5 — schema
  v1 is still the only shipped shape. This is the single code-level
  change that makes "you never migrate again" a load-bearing claim:
  an older kernel reading a newer canon warns rather than halting.
- **MAJOR 9 — Governance as verbs.** Three new agent-callable
  CLI/MCP verbs; previously all three were Markdown-social
  conventions:
  - **`myco craft --topic <phrase>`** scaffolds a dated primordia
    doc at `docs/primordia/<slug>_craft_<date>.md` from a three-round
    template (claim / self-rebuttal / revision / counter-rebuttal /
    reflection, with YAML frontmatter carrying `type`, `slug`,
    `kind`, `date`, `rounds`, `status`). Refuses to overwrite.
  - **`myco bump --contract <v>`** is the first code path in Myco
    that mutates a post-genesis `_canon.yaml`. Regex-patches the
    top-level `contract_version:` and `synced_contract_version:`
    fields, re-reads via `load_canon` to validate, then prepends a
    new section to `docs/contract_changelog.md`. Restores the
    original canon text on any post-write parse error. `--dry-run`
    previews without writing.
  - **`myco evolve --proposal <path>`** runs five shape gates on a
    craft or proposal doc (frontmatter `type`, title, body size
    bounds, round-marker count ≥ 2, per-round body ≥ 150 chars).
    Returns `exit 0` with `verdict: pass` on clean, `exit 1` with
    `violations: [{gate, message}]` on fail. Read-only; does not
    mutate.
- **MAJOR 10 — Handler auto-scaffolding.**
  **`myco scaffold --verb <name>`** generates a minimal handler
  stub at the filesystem path derived from the manifest's
  `handler:` string (not the `subsystem:` tag). The stub returns a
  well-formed `Result(exit_code=0, payload={"stub": True, "verb":
  <name>})` and emits a `DeprecationWarning` on every invocation,
  so unfinished verbs are neither silent successes nor crashes.
  Refuses to act on a verb the manifest does not declare (manifest
  stays SSoT); refuses to overwrite unless `--force` is passed.
- **`myco.meta/` package.** What was a single-file
  `src/myco/meta.py` in v0.4 is now a package with five submodules
  (`session_end.py`, `craft.py`, `bump.py`, `evolve.py`,
  `scaffold.py`) plus a `templates/` subdirectory holding the
  craft-doc template. `meta/__init__.py` re-exports
  `session_end_run` so any out-of-tree caller that imported from
  the old module path keeps working unchanged.
- **Sixteen verbs.** v0.4 shipped twelve; v0.5 adds `craft`, `bump`,
  `evolve`, `scaffold`.
- **Nine lint dimensions.** v0.4 shipped eight; v0.5 adds `MF1`.

### Changed

- **`session-end` manifest handler path.** Moved from
  `myco.meta:session_end_run` to `myco.meta.session_end:run` as a
  consequence of the `meta.py → meta/` package migration. The
  backward-compat re-export in `meta/__init__.py` means imports
  like `from myco.meta import session_end_run` still work.
- **`test_scaffold.py::PACKAGES`** switched from a hardcoded
  14-entry list to `pkgutil.walk_packages(myco.__path__)`. Adding
  a new subsystem package no longer forces a test edit. The
  module's prose header also corrected — it previously claimed
  "eight-subsystem layout" against a 14-entry list.
- **Genesis canon template no longer claims `package:` paths.**
  A fresh substrate starts with `subsystems.<name>.doc` only;
  `package:` is opt-in for substrates whose subsystems correspond
  to code packages under the substrate root (e.g. Myco's own
  `_canon.yaml`). Prevents `MF1` from firing on every fresh-genesis
  fixture.
- **Doctrine updates bundled with the release.**
  - `docs/architecture/L1_CONTRACT/canon_schema.md` rule 4 — text
    moved from "refuses to read unknown `schema_version`" to
    "warns and preserves, with `schema_upgraders` as the forward-
    compat seam".
  - `docs/architecture/L2_DOCTRINE/homeostasis.md` — entry-points-
    driven registration, `MF1` in the inventory, `--list` /
    `--explain` surface documented, dimension-adding workflow
    updated.
  - `docs/architecture/L3_IMPLEMENTATION/command_manifest.md` —
    governance-verbs section added, 16-verb inventory table.
  - `docs/architecture/L3_IMPLEMENTATION/package_map.md` — `meta/`
    as a package, mapping matrix updated.

---

## [0.4.4] — 2026-04-16

Hotfix for hook-invocation failures when a stale `myco` exists on
PATH (Anaconda, older venvs, etc.) or when the console-script
Scripts dir is not on PATH at all.

### Fixed

- **`hooks/hooks.json` and `.claude/settings.local.json`** now
  invoke `python -m myco --json ...` instead of bare `myco --json
  ...`. The bare form assumes the currently-installed myco's
  Scripts dir is on PATH; in practice any pre-v0.4 myco on PATH
  (common with Anaconda or system Python) will shadow the target
  version and fail because v0.3 CLIs do not accept
  `--project-dir`. Using `python -m myco` dispatches through
  `sys.path`, which finds the correct package regardless of
  Scripts-dir PATH state.
- **Regression test** `test_hooks_use_python_m_myco` in
  `tests/integration/test_plugin_bundle.py` pins the new convention.

### User action required (if hit on <=0.4.3)

```bash
pip install --upgrade 'myco[mcp]'
# Re-install the plugin / re-run myco-install to pick up the new
# hook command form, or hand-edit your existing hook config files.
```

---

## [0.4.3] — 2026-04-16

Hotfix for the most common MCP install failure: `spawn ENOENT`.

### Fixed

- **`myco-install` now writes the absolute Python interpreter path**
  (`sys.executable` plus `-m myco.mcp`) instead of the bare
  `mcp-server-myco` console script. GUI MCP hosts (Claude Desktop,
  Cursor, Windsurf) do not inherit the user's shell PATH, so the
  console script is invisible to them. The absolute-path form works
  regardless of PATH, venv, or `python`/`python3` aliasing.
- **`docs/INSTALL.md` adds a troubleshooting section** covering the
  three most common MCP failures: ENOENT, missing `[mcp]` extra,
  and "server disconnected" timeout. Manual-config users get the
  absolute-path form alongside the bare console-script form.

---

## [0.4.2] — 2026-04-16

Closes the five BLOCKER gaps surfaced by the v0.4.1 post-release
audit (docs/primordia/v0_4_1_audit_craft_2026-04-15.md). The README
promise "devours code repositories, framework documentation,
datasets, papers" is now mechanically honored by the code, not just
the prose.

### Added

- **Ingestion adapter protocol** (Stage F.1). New
  `src/myco/ingestion/adapters/` subpackage with an `Adapter` ABC,
  `IngestResult` dataclass, and a global registry. Built-in adapters
  auto-register at import time; external adapters call `register()`.
- **Six built-in adapters** (Stage F.1):
  - `text-file`: any UTF-8 file including `.py`, `.js`, `.ts`, `.go`,
    `.rs`, `.rb`, `.sh`, `.c`, `.cpp`, `.java`, `.kt`, `.swift`,
    `.lua`, `.r`, `.sql`, `.toml`, `.ini`, `.cfg`, `.xml`, `.css`,
    `.md`, `.yaml`, `.json`, `.log`, Makefiles, Dockerfiles, and
    60+ more extensions. Binary detection via null-byte heuristic.
  - `code-repo`: walks a directory, delegates per file to `text-file`,
    respects `.gitignore` if `pathspec` is installed. Capped at 500
    files. Provenance carries `<repo>/<relative-path>`.
  - `url`: HTTP GET via `httpx`, dispatches by Content-Type to
    `html`/`pdf`/`json`/plain-text. Requires `[adapters]` extras.
  - `pdf`: local `.pdf` via `pypdf`, one `IngestResult` per page
    with page numbers. Requires `[adapters]` extras.
  - `html`: local `.html` via `beautifulsoup4`, strips nav/footer/
    script/style. Requires `[adapters]` extras.
  - `tabular`: `.csv`, `.tsv`, `.json`, `.jsonl` via stdlib
    `csv`/`json`. Produces a summary (columns, row count, preview
    rows). No optional deps needed.
- **`eat --path` and `eat --url`** (Stage F.1). The `eat` verb now
  accepts `--path <file-or-dir>` or `--url <https://...>` in
  addition to `--content`. Each dispatches through the adapter
  registry and produces one note per `IngestResult`. Provenance is
  automatically set from the adapter rather than defaulting to
  `"agent"`.
- **`[adapters]` optional-dependency target** (Stage F.1).
  `pip install 'myco[adapters]'` pulls `httpx>=0.27`,
  `pypdf>=4.0`, `beautifulsoup4>=4.12`. Stdlib-only adapters
  (text-file, code-repo, tabular) work without this target.

### Changed

- **`forage` no longer silently drops files** (Stage F.1). The
  hardcoded 7-extension whitelist (`_INGESTIBLE_SUFFIXES`) is
  replaced by the adapter registry: a file is listed if any adapter
  claims it. Unreachable files are counted in a new `skipped` field
  in the payload so users know the listing is intentionally
  narrowed, not silently lossy. `forage --path ./src/myco` now
  returns 66 files (was 1 in v0.4.1).
- **`distill` derives a synthesis seed** (Stage F.1). The stub
  proposal now includes shared-tag theme analysis and first-line
  claim extraction from all source notes (was: filename listing
  only). Also fixes the empty-list CLI bug where `--sources` with
  no arguments was coerced to `()` instead of `None`, skipping the
  "use all integrated notes" path and raising `ContractError`.

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
