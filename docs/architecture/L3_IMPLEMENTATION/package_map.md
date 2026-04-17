# L3 — Package Map

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L3. Subordinate to L0/L1/L2. Code MUST conform to this map;
> a divergence between code and map is resolved in favor of the map (per
> R7 + §9 execution constraints).

---

## The `src/myco/` layout (v0.5.3)

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
│   ├── hunger.py            # payload gains local_plugins: {count, health} at v0.5.3
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
│   └── templates/
│       └── fruit.md.tmpl    # three-round primordia skeleton (was craft.md.tmpl)
│
├── meta/                    # shim package (v0.5.3) — re-exports myco.cycle.*
│   └── __init__.py          # preserves `from myco.meta import session_end_run`; DeprecationWarning
│
└── symbionts/               # downstream-project adapters (opt-in, isolated)
    ├── __init__.py
    └── claude_code.py       # Claude Code / Cowork specific surface sugar
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
| `src/myco/cycle/` (v0.5.3) | (life-cycle composer verbs: `germinate`, `senesce`, `fruit`, `molt`, `winnow`, `ramify`, `graft`) | `command_manifest.md` governance-verbs section |
| `src/myco/meta/` (v0.5.3 shim) | (backward-compat re-export of `cycle`; preserves `from myco.meta import session_end_run`) | — |
| `src/myco/symbionts/` | (external integrations) | per-symbiont doc under `docs/adapters/` |

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
├── genesis/
├── ingestion/
├── digestion/
├── circulation/
├── homeostasis/
│   └── dimensions/      # one test file per dimension
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
