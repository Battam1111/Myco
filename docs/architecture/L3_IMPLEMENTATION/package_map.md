# L3 — Package Map

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; v0.6.0 amendment LANDED 2026-04-28 per `docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` §F2).
> **Layer**: L3. Subordinate to L0/L1/L2. Code MUST conform to this map;
> a divergence between code and map is resolved in favor of the map (per
> R7 + §9 execution constraints).

---

## v0.6.0 amendments

- `cycle/` is the canonical **6th subsystem** (since v0.6.0); doctrine
  page lands at `docs/architecture/L2_DOCTRINE/cycle.md`. Matches
  `L0_VISION.md:172-186` which already named Cycle as the 6th subsystem
  since v0.5.3.
- `boundary/` is the canonical **7th subsystem** (since v0.6.0 Round 4
  owner amendment §A1). It physically unifies the four legacy
  cross-cutting adapter packages: `boundary.surface` (CLI/MCP/manifest),
  `boundary.install` (host writers), `boundary.mcp` (MCP launcher),
  `boundary.host_integration` (14 per-host adapters, formerly
  `symbionts/`). L0 vocabulary clause narrowly extended in §A1 to
  admit `boundary` as a doctrine-level term.
- **Physical merger LANDED at Round 5** per owner directive
  ("不许有任何一丝一毫偷懒"): the legacy top-level packages
  `myco.surface` / `myco.install` / `myco.mcp` / `myco.symbionts` are
  **REMOVED**. 201 import-path rewrites across 60 files (src + tests +
  docs + configs) bring the codebase onto the canonical
  `myco.boundary.<sub>` form. pyproject entry-points updated:
    - `myco = "myco.boundary.surface.cli:main"`
    - `mcp-server-myco = "myco.boundary.mcp:main"`
    - `myco-install = "myco.boundary.install:main"`
- The 14 host_integration adapters all live under
  `boundary/host_integration/` (claude-code / cursor / cowork /
  vscode / continue-dev / cline / jetbrains / zed / goose / windsurf /
  codex-cli / gemini-cli / openclaw / claude-desktop).
- `homeostasis/dimensions/` reorganized into 4 category subdirectories:
  `mechanical/` (31), `shipped/` (2), `metabolic/` (6), `semantic/` (7).
  pyproject entry-points updated for all 46 dim paths.
- `tests/unit/verbs/<verb>/` reorganization landed: 13 verb-shape test
  files moved from subsystem-organized layout into 20 verb directories.
- Core invariants preserved: PA4 (mechanical, HIGH) guards `core/`
  against any subsystem import (including boundary); PA5 (mechanical,
  MEDIUM) guards subsystem→boundary import discipline.

---

## The `src/myco/` layout (v0.6.0)

```
src/myco/
├── __init__.py              # __version__ ONLY (SSoT per L1 versioning)
├── __main__.py              # `python -m myco` entry → surface.cli:main
│
├── core/                    # shared primitives, nothing subsystem-specific
│   ├── __init__.py
│   ├── errors.py            # single MycoError hierarchy (one model)
│   ├── project.py           # project-root discovery (one path only)
│   ├── paths.py             # write-surface validation + SubstratePaths.local_plugins / manifest_overlay (v0.5.3)
│   ├── canon.py             # canon load/validate against L1 schema
│   ├── severity.py          # CRITICAL/HIGH/MEDIUM/LOW enum + ordering
│   ├── substrate.py         # Substrate.load() — auto-imports .myco/plugins/ (v0.5.3)
│   └── version.py           # __version__ accessor, SemVer parsing
│
├── germination/             # L2 Germination (renamed from genesis/ at v0.5.3)
│   ├── __init__.py
│   ├── templates/           # canon + entry-point skeleton files
│   └── germinate.py         # `myco germinate` implementation
│
├── genesis/                 # shim package (v0.5.3) — re-exports myco.germination.*
│   └── __init__.py          # DeprecationWarning on import; preserves `from myco.genesis import ...`
│
├── ingestion/               # L2 Ingestion
│   ├── __init__.py
│   ├── eat.py
│   ├── hunger.py            # payload includes local_plugins: {loaded, count_by_kind: {dimension, adapter, schema_upgrader, overlay_verb}, errors, module} (v0.5.4+)
│   ├── sense.py
│   ├── forage.py
│   ├── adapters/            # ingestion adapter protocol (registry; v0.4.2)
│   └── boot_brief.py        # entry-point signals block injector
│
├── digestion/               # L2 Digestion
│   ├── __init__.py
│   ├── assimilate.py        # was reflect.py at v0.5.2
│   ├── digest.py
│   ├── sporulate.py         # was distill.py at v0.5.2
│   └── pipeline.py          # raw→assimilating→integrated→sporulated state machine
│
├── circulation/             # L2 Circulation
│   ├── __init__.py
│   ├── graph.py             # cross-reference index
│   ├── traverse.py          # was perfuse.py at v0.5.2
│   └── propagate.py         # redefined per §9 E4 + L2 circulation.md
│
├── homeostasis/             # L2 Homeostasis
│   ├── __init__.py
│   ├── kernel.py            # orchestrator, ≤ 1500 LoC
│   ├── exit_policy.py       # parse_exit_on, _compute_exit_code
│   ├── skeleton.py          # skeleton-mode downgrade
│   ├── registry.py          # register_external_dimension(cls) public API (v0.5.3)
│   └── dimensions/          # one file per lint dimension
│       ├── __init__.py      # dimension registry
│       ├── l0_*.py
│       ├── l1_*.py
│       ├── mf1_*.py
│       ├── mf2_substrate_local_plugin_health.py  # v0.5.3
│       └── …
│
├── surface/                 # how the outside world talks to Myco
│   ├── __init__.py
│   ├── manifest.py          # command manifest loader (SSoT for surfaces); supports aliases + overlay
│   ├── manifest.yaml        # the 17-verb table (v0.5.3; 16 + graft)
│   ├── cli.py               # argparse wrapper; generated from manifest
│   └── mcp.py               # MCP server; generated from manifest
│
├── cycle/                   # life-cycle composer verbs (v0.5.3, was meta/ at v0.5.1–v0.5.2)
│   ├── __init__.py
│   ├── senesce.py           # was meta/session_end.py — assimilate + immune --fix
│   ├── fruit.py             # was meta/craft.py — three-round primordia author
│   ├── molt.py              # was meta/bump.py — contract-version shed
│   ├── winnow.py            # was meta/evolve.py — proposal shape validator
│   ├── ramify.py            # was meta/scaffold.py — extended with --dimension/--adapter/--substrate-local
│   ├── graft.py             # v0.5.3 new — substrate-local plugin introspection
│   ├── brief.py             # v0.5.5 new — human-facing markdown rollup (L0 p.1 carved exception)
│   └── templates/
│       └── fruit.md.tmpl    # three-round primordia skeleton (was craft.md.tmpl)
│
├── meta/                    # shim package (v0.5.3) — re-exports myco.cycle.*
│   └── __init__.py          # preserves `from myco.meta import session_end_run`; DeprecationWarning
│
├── install/                 # v0.5.5 — host MCP writers + fresh-substrate bootstrap
│   ├── __init__.py
│   ├── clients/             # one module per automated host: claude_code, claude_desktop, cursor, windsurf, zed, vscode, openclaw, gemini_cli, codex_cli (TOML), goose (YAML)
│   └── fresh.py             # `myco-install fresh` — germinate + wire hooks in one step
│
├── mcp/                     # v0.5.5 — `python -m myco.boundary.mcp` MCP launcher
│   └── __init__.py          # thin delegator to surface.mcp so the MCP server has a stable module path
│
├── providers/               # v0.5.6 NEW — reserved opt-in for LLM-provider coupling
│   └── __init__.py          # empty; populating this package requires
│                            # `canon.system.no_llm_in_substrate: false` + a
│                            # contract-bumping molt. MP1 guards the rest of
│                            # `src/myco/**` against provider-SDK imports.
│
└── symbionts/               # v0.5.5 — per-host Agent-sugar seam (defined-but-empty at v0.5.7)
    └── __init__.py          # points at `symbiont_protocol.md`; no concrete symbionts yet
```

### Substrate-local extension paths (v0.5.3)

```
<substrate_root>/.myco/
├── plugins/
│   ├── __init__.py          # auto-imported on Substrate.load(); runs registration side effects
│   ├── dimensions/          # optional; local Dimension subclasses
│   ├── adapters/            # optional; local ingestion Adapter subclasses
│   ├── schema_upgraders/    # optional; local canon upgraders
│   └── verbs/               # optional; local verb handlers (paired with overlay entries)
└── manifest_overlay.yaml    # merged into runtime manifest at build_context() time
```

Myco's own repo has **no** `.myco/plugins/` tree (it IS the kernel);
this path is for downstream substrates only. The `MF2` lint
dimension validates shape and surfaces any import / registration
errors as mechanical/HIGH findings.

## Invariants

1. **Nothing outside `src/myco/` contains package logic.** Tests, docs,
   and scripts may reference but not replicate.
2. **`core/` has no subsystem dependencies.** Subsystems depend on `core/`,
   not the reverse.
3. **Each subsystem is `import`-safe in isolation.** Importing
   `myco.digestion` does not require `myco.homeostasis` to be loadable.
4. **Surface layer is pure adaptation.** `surface/cli.py` and
   `surface/mcp.py` contain no business logic; they translate manifest
   entries into argparse parsers and MCP tool definitions respectively.
5. **No megafile.** Any module file > 800 LoC is a code smell and
   requires a split before merge. The pre-rewrite `immune.py` (4400 LoC),
   `mcp_server.py` (3385 LoC), and `notes.py` (2931 LoC) are abolished
   by construction.
6. **Biological naming is authoritative.** Package and module names must
   match L2 Doctrine vocabulary exactly.

## Mapping matrix (L3 → L2)

| L3 package | L2 subsystem | Upward doc |
|------------|--------------|------------|
| `src/myco/core/` | (cross-cutting primitives, not a subsystem) | L1 |
| `src/myco/germination/` (v0.5.3) | Germination | `docs/architecture/L2_DOCTRINE/genesis.md` (filename preserved) |
| `src/myco/genesis/` (v0.5.3 shim) | (backward-compat re-export of `germination`) | — |
| `src/myco/ingestion/` | Ingestion | `docs/architecture/L2_DOCTRINE/ingestion.md` |
| `src/myco/digestion/` | Digestion | `docs/architecture/L2_DOCTRINE/digestion.md` |
| `src/myco/circulation/` | Circulation | `docs/architecture/L2_DOCTRINE/circulation.md` |
| `src/myco/homeostasis/` | Homeostasis | `docs/architecture/L2_DOCTRINE/homeostasis.md` |
| `src/myco/surface/` | (cross-cutting — adapters for CLI and MCP) | L1 protocol + command manifest |
| `src/myco/cycle/` (v0.5.3) | (life-cycle composer verbs: `germinate`, `senesce`, `fruit`, `molt`, `winnow`, `ramify`, `graft`, `brief`) | `command_manifest.md` governance-verbs section |
| `src/myco/meta/` (v0.5.3 shim) | (backward-compat re-export of `cycle`; preserves `from myco.meta import session_end_run`) | — |
| `src/myco/install/` (v0.5.5) | (MCP host writers + fresh-substrate bootstrap; 10 automated hosts at v0.5.7) | `docs/INSTALL.md` |
| `src/myco/mcp/` (v0.5.5) | (MCP launcher surface: `python -m myco.boundary.mcp`) | `L1_CONTRACT/protocol.md` + `command_manifest.md` |
| `src/myco/providers/` (v0.5.6 NEW) | (reserved opt-in for LLM provider coupling; empty at v0.5.7; requires `canon.system.no_llm_in_substrate: false` + contract bump to populate) | `L2_DOCTRINE/digestion.md` §"sporulate does NOT call an LLM" + `providers/README.md` |
| `src/myco/symbionts/` | per-host Agent-sugar adapters (Claude Code skill-generators, Cursor rule writers, VS Code task configurators, etc.) | `L3_IMPLEMENTATION/symbiont_protocol.md`; package defined-but-empty at v0.5.7 |

### Shim packages (v0.5.3)

The `genesis/` → `germination/` and `meta/` → `cycle/` renames are
non-breaking: the old paths still exist as shim packages whose
`__init__.py` re-exports every name from the new location and
emits a `DeprecationWarning` on import. Examples:

- `from myco.meta import session_end_run` still works.
- `from myco.genesis import run_cli` still works.
- Both paths are scheduled for removal at v1.0.0.

## Test layout mirror

`tests/` mirrors `src/myco/` package-for-package:

```
tests/unit/
├── core/
├── germination/         # v0.5.3+ (was `genesis/` at v0.4.0–v0.5.2)
├── ingestion/
├── digestion/
├── circulation/
├── homeostasis/
│   └── dimensions/      # one test file per dimension
├── cycle/               # v0.5.3+ (was `meta/` at v0.5.1–v0.5.2)
├── install/             # v0.5.5+ — MCP host writers + `fresh` bootstrap
├── mcp/                 # v0.5.5+ — `python -m myco.boundary.mcp` entry
└── surface/
```

Integration tests live under `tests/integration/`, keyed by scenario not
by subsystem.

## What does NOT survive

- `src/myco/autoseed.py` (subsumed by `genesis/`).
- `src/myco/immune.py` (decomposed into `homeostasis/`).
- `src/myco/mcp_server.py` (replaced by manifest-driven `surface/mcp.py`).
- `src/myco/notes.py` (split into ingestion + digestion).
- `src/myco/evolve.py`, `redact.py`, `propagate_cmd.py` (dead; rewritten
  fresh if/when needed — see §9 E4 for propagate).
- The pre-rewrite 30-dimension inventory (reconsidered, see
  `homeostasis.md`).
