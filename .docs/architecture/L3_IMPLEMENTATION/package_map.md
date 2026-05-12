# L3 — Package Map

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9; v0.6.0 amendment LANDED 2026-04-28 per `docs/primordia/_landed/v0_6_x/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md` §F2).
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
  owner amendment §A1). At v0.8.5 it physically unifies three
  cross-cutting adapter packages: `boundary.surface` (CLI/MCP/manifest),
  `boundary.install` (host writers — the data-driven JsonClientSpec
  table covers 10 MCP hosts), and `boundary.mcp` (MCP launcher).
  L0 vocabulary clause narrowly extended in §A1 to admit `boundary`
  as a doctrine-level term.
- **Physical merger LANDED at Round 5** per owner directive
  ("不许有任何一丝一毫偷懒"): the legacy top-level packages
  `myco.surface` / `myco.install` / `myco.mcp` / `myco.symbionts` are
  **REMOVED**. 201 import-path rewrites across 60 files bring the
  codebase onto the canonical `myco.boundary.<sub>` form. pyproject
  entry-points:
    - `myco = "myco.boundary.surface.cli:main"`
    - `mcp-server-myco = "myco.boundary.mcp:main"`
    - `myco-install = "myco.boundary.install:main"`
- **v0.8.5**: the `boundary/host_integration/` subpackage (14 per-host
  adapter modules at v0.6.0 — claude-code / claude-desktop / cline /
  codex-cli / continue-dev / cowork / cursor / gemini-cli / goose /
  jetbrains / openclaw / vscode / windsurf / zed) was **excreted**.
  The 8 pure-stub adapters returned empty `InstallReport`\\s; the 6
  functional rule-template writers were never invoked by the
  production `myco-install host <client>` path (which delegates to
  the data-driven `boundary/install/clients.py::JsonClientSpec`
  table). Re-introducing rule writers, if wanted in v0.9, should land
  as a new `RuleClientSpec` row inside `clients.py` rather than as a
  parallel module registry. The `MF3SymbiontArtifactIntegrity` dim
  (premise: signature header in installed adapter artifacts) was
  retired in the same commit.
- `homeostasis/dimensions/` organized into 4 category subdirectories:
  `mechanical/` (32 dims across 8 cluster files + 4 singletons),
  `shipped/` (2 dims in 1 cluster), `metabolic/` (6 dims in 1 cluster),
  `semantic/` (7 dims across 2 clusters + 1 singleton). v0.8.8
  consolidated 42 per-dim files into 12 ``<letter>_cluster.py``
  files (reverting v0.6.0 §R2 "one module per dim" L3 organization
  choice); 47 dims, 17 files total. pyproject entry-points updated
  for all live dim paths.
- `tests/unit/verbs/<verb>/` reorganization landed: 13 verb-shape test
  files moved from subsystem-organized layout into 20 verb directories.
- Core invariants preserved: PA4 (mechanical, HIGH) guards `core/`
  against any subsystem import (including boundary); PA5 (mechanical,
  MEDIUM) guards subsystem→boundary import discipline.

---

## The `src/myco/` layout (v0.8.5 — current)

```
src/myco/
├── __init__.py              # __version__ ONLY (SSoT per L1 versioning)
├── __main__.py              # `python -m myco` entry → boundary.surface.cli:main
├── py.typed                 # PEP 561 marker
│
├── core/                    # shared primitives, nothing subsystem-specific
│   ├── __init__.py
│   ├── errors.py            # single MycoError hierarchy (one model)
│   ├── project.py           # project-root discovery (one path only)
│   ├── paths.py             # write-surface validation + SubstratePaths.local_plugins / manifest_overlay (v0.5.3)
│   ├── canon.py             # canon load/validate against L1 schema (merges _canon_lint.yaml)
│   ├── severity.py          # CRITICAL/HIGH/MEDIUM/LOW enum + ordering
│   ├── substrate.py         # Substrate.load() — auto-imports .myco/plugins/ (v0.5.3)
│   └── version.py           # __version__ accessor, SemVer parsing
│   # NOTE: `risk_classifier.py` (v0.6.0+ agent-self-winnow tier
│   # classifier) was excreted at v0.8.5 — the agent-side classifier
│   # never got plumbed into ramify/molt/winnow runtime, and the
│   # ratchet doctrine moved to the natural choke points instead.
│
├── germination/             # L2 Germination (renamed from genesis/ at v0.5.3; shim removed at v0.6.0)
│   ├── __init__.py
│   ├── templates/           # canon + entry-point skeleton files
│   └── germinate.py         # `myco germinate` implementation
│
├── ingestion/               # L2 Ingestion
│   ├── __init__.py
│   ├── eat.py
│   ├── hunger.py            # payload includes local_plugins shape (v0.5.4+)
│   ├── sense.py
│   ├── forage.py
│   ├── excrete.py           # v0.5.24 — safely delete a raw note + tombstone
│   ├── intake.py            # v0.6.0 — bulk forage + eat with strict-mode failure visibility
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
│   └── propagate.py         # per §9 E4 + L2 circulation.md
│
├── homeostasis/             # L2 Homeostasis
│   ├── __init__.py
│   ├── kernel.py            # orchestrator, ≤ 1500 LoC
│   ├── exit_policy.py       # parse_exit_on, _compute_exit_code
│   ├── skeleton.py          # skeleton-mode downgrade
│   ├── registry.py          # register_external_dimension(cls) public API (v0.5.3)
│   └── dimensions/          # 47 dims across 17 files at v0.8.8 (clustered;
│                            # history: v0.6.0 25→46 / v0.7.2 +SE5+MB8+PA6 /
│                            # v0.7.5 +LB1+CG1+CG2 / v0.8.0 +LB2 /
│                            # v0.8.5 −MB7 −MF3 / v0.8.6 −SE4 −RL2 −RL3 /
│                            # v0.8.8 cluster-merge reversing v0.6.0 §R2 L3)
│       ├── mechanical/      # 32 dims in 12 files: 8 clusters (m/mf/mp/dc/cg/di/pa/cl) + 4 singletons (ad1/cs1/fr1/sc1)
│       ├── shipped/         # 2 dims in 1 file (sh_cluster: SH1+SH2)
│       ├── metabolic/       # 6 dims in 1 file (mb_cluster: MB1-MB4+MB6+MB8)
│       └── semantic/        # 7 dims in 3 files (se_cluster: SE1-3+SE5; lb_cluster: LB1+LB2; rl1: singleton)
│
├── cycle/                   # L2 Cycle (canonical 6th subsystem since v0.6.0; meta/ shim removed)
│   ├── __init__.py
│   ├── senesce.py           # assimilate + immune --fix; bimodal (full / quick at v0.5.7+)
│   ├── fruit.py             # three-round primordia author
│   ├── molt.py              # contract-version shed (atomic 5-file bumper companion)
│   ├── winnow.py            # craft-shape validator + G7 path_allowlist gate (v0.6.15+)
│   ├── ramify.py            # scaffold new verb / dimension / adapter
│   ├── graft.py             # substrate-local plugin introspection
│   ├── brief.py             # v0.5.5 — human-facing markdown rollup (single L0 P1 carved exception)
│   └── templates/
│       └── fruit.md.tmpl    # three-round primordia skeleton
│
├── boundary/                # L2 Boundary (canonical 7th subsystem since v0.6.0)
│   ├── __init__.py          # unified outward-interface umbrella
│   ├── surface/             # CLI/MCP/manifest (was top-level src/myco/surface/ pre-v0.6.0)
│   │   ├── manifest.yaml    # the 20-verb table (SSoT for both CLI and MCP)
│   │   ├── manifest.py      # manifest loader; supports aliases + overlay
│   │   ├── cli.py           # argparse wrapper; generated from manifest
│   │   └── mcp.py           # MCP server; generated from manifest
│   ├── install/             # MCP host writers + fresh-substrate bootstrap (was top-level install/)
│   │   ├── clients.py       # data-driven JsonClientSpec table — 10 automated MCP hosts at v0.8.5
│   │   └── fresh.py         # `myco-install fresh`
│   └── mcp/                 # `python -m myco.boundary.mcp` launcher (was top-level mcp/)
│       └── __init__.py      # thin delegator to surface.mcp
│   # NOTE (v0.8.5): the boundary.host_integration subpackage was
│   # excreted. 8 pure-stub adapters + 6 functional rule-template
│   # writers that production code never invoked. The data-driven
│   # clients.py table is the sole installer surface now.
│
└── mcp/                     # v0.6.13 back-compat shim — re-exports myco.boundary.mcp
    └── __init__.py          # DeprecationWarning on `from myco.mcp import ...`; scheduled for removal at v1.0.0
```

Excreted at v0.6.0 (physical merger): top-level `surface/`, `install/`,
`mcp/`, `symbionts/` packages. The `genesis/` and `meta/` shim packages
(v0.5.3) were also removed; downstream substrates use the canonical
`germination/` and `cycle/` paths now. The `providers/` package
(reserved at v0.5.6 for opt-in LLM coupling) was excreted at v0.6.14
after seven minor releases without population.

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
| `src/myco/germination/` | Germination | `docs/architecture/L2_DOCTRINE/genesis.md` (filename preserved across the v0.5.3 rename) |
| `src/myco/ingestion/` | Ingestion | `docs/architecture/L2_DOCTRINE/ingestion.md` |
| `src/myco/digestion/` | Digestion | `docs/architecture/L2_DOCTRINE/digestion.md` |
| `src/myco/circulation/` | Circulation | `docs/architecture/L2_DOCTRINE/circulation.md` |
| `src/myco/homeostasis/` | Homeostasis | `docs/architecture/L2_DOCTRINE/homeostasis.md` |
| `src/myco/cycle/` (6th, v0.6.0) | Cycle | `docs/architecture/L2_DOCTRINE/cycle.md` |
| `src/myco/boundary/` (7th, v0.6.0) | Boundary | `docs/architecture/L2_DOCTRINE/boundary.md` |
| `src/myco/boundary/surface/` | (boundary subpackage — CLI/MCP/manifest) | `L1_CONTRACT/protocol.md` + `L3_IMPLEMENTATION/command_manifest.md` |
| `src/myco/boundary/install/` | (boundary subpackage — MCP host writers + fresh-substrate bootstrap; 10 automated hosts at v0.6.15) | `docs/INSTALL.md` |
| `src/myco/boundary/mcp/` | (boundary subpackage — MCP launcher: `python -m myco.boundary.mcp`) | `L1_CONTRACT/protocol.md` + `command_manifest.md` |
| `src/myco/mcp/` (v0.6.13 shim) | (back-compat re-export of `boundary.mcp`; DeprecationWarning) | — |

### Excreted packages (historical)

Seven top-level / boundary packages were excreted across the v0.6.0+ refactor sequence:

- **`src/myco/genesis/`** (v0.5.3 shim → v0.6.0 removed): replaced by `src/myco/germination/`. Downstream substrates updated their imports.
- **`src/myco/meta/`** (v0.5.3 shim → v0.6.0 removed): replaced by `src/myco/cycle/`.
- **`src/myco/surface/`** (pre-v0.6.0 → v0.6.0 unified): now `src/myco/boundary/surface/`.
- **`src/myco/install/`** (v0.5.5 → v0.6.0 unified): now `src/myco/boundary/install/`.
- **`src/myco/symbionts/`** (v0.5.5 reserved → v0.6.0 unified → v0.8.5 excreted): briefly lived as `src/myco/boundary/host_integration/`; the entire subpackage was excreted at v0.8.5 along with `MF3` (8 pure-stub adapters returned empty `InstallReport`s; 6 functional rule-template writers were never invoked by production code). The data-driven `boundary/install/clients.py::JsonClientSpec` table is the sole installer surface now.
- **`src/myco/providers/`** (v0.5.6 reserved → v0.6.14 excreted): never populated through 7 minor releases; future LLM-provider coupling, if ever needed, requires its own L0 P1 amendment craft + fresh contract-bumping molt rather than a pre-baked escape hatch.
- **`src/myco/core/risk_classifier.py`** (v0.6.0 → v0.8.5 excreted): agent-self-winnow tier classifier with `path_allowlist`+recursion-cutter. Never wired into the verb runtime; the ratchet doctrine moved to the natural choke points (immune gating + craft winnow) instead of a separate classifier module.

The `src/myco/mcp/` shim (v0.6.13) is the only legacy import path still
honored; it re-exports `myco.boundary.mcp` with a DeprecationWarning and
is scheduled for removal at v1.0.0.

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
