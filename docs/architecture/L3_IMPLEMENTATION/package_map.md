# L3 — Package Map

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L3. Subordinate to L0/L1/L2. Code MUST conform to this map;
> a divergence between code and map is resolved in favor of the map (per
> R7 + §9 execution constraints).

---

## The new `src/myco/` layout

```
src/myco/
├── __init__.py              # __version__ ONLY (SSoT per L1 versioning)
├── __main__.py              # `python -m myco` entry → surface.cli:main
│
├── core/                    # shared primitives, nothing subsystem-specific
│   ├── __init__.py
│   ├── errors.py            # single MycoError hierarchy (one model)
│   ├── project.py           # project-root discovery (one path only)
│   ├── paths.py             # write-surface validation
│   ├── canon.py             # canon load/validate against L1 schema
│   ├── severity.py          # CRITICAL/HIGH/MEDIUM/LOW enum + ordering
│   └── version.py           # __version__ accessor, SemVer parsing
│
├── genesis/                 # L2 Genesis
│   ├── __init__.py
│   ├── templates/           # canon + entry-point skeleton files
│   └── genesis.py           # `myco genesis` implementation
│
├── ingestion/               # L2 Ingestion
│   ├── __init__.py
│   ├── eat.py
│   ├── hunger.py
│   ├── sense.py
│   ├── forage.py
│   └── boot_brief.py        # entry-point signals block injector
│
├── digestion/               # L2 Digestion
│   ├── __init__.py
│   ├── reflect.py
│   ├── digest.py
│   ├── distill.py
│   └── pipeline.py          # raw→digesting→integrated→distilled state machine
│
├── circulation/             # L2 Circulation
│   ├── __init__.py
│   ├── graph.py             # cross-reference index
│   ├── perfuse.py
│   └── propagate.py         # redefined per §9 E4 + L2 circulation.md
│
├── homeostasis/             # L2 Homeostasis
│   ├── __init__.py
│   ├── kernel.py            # orchestrator, ≤ 1500 LoC
│   ├── exit_policy.py       # parse_exit_on, _compute_exit_code
│   ├── skeleton.py          # skeleton-mode downgrade
│   └── dimensions/          # one file per lint dimension
│       ├── __init__.py      # dimension registry
│       ├── l0_*.py
│       ├── l1_*.py
│       └── …
│
├── surface/                 # how the outside world talks to Myco
│   ├── __init__.py
│   ├── manifest.py          # command manifest loader (SSoT for surfaces)
│   ├── manifest.yaml        # the 16-verb table (v0.5+)
│   ├── cli.py               # argparse wrapper; generated from manifest
│   └── mcp.py               # MCP server; generated from manifest
│
├── meta/                    # cross-cutting verbs (v0.5+, was meta.py in v0.4)
│   ├── __init__.py          # re-exports session_end_run for backward-compat
│   ├── session_end.py       # reflect + immune(fix=True) composer
│   ├── craft.py             # `myco craft <topic>` (MAJOR 9)
│   ├── bump.py              # `myco bump --contract <v>` (MAJOR 9)
│   ├── evolve.py            # `myco evolve --proposal <path>` (MAJOR 9)
│   ├── scaffold.py          # `myco scaffold --verb <name>` (MAJOR 10)
│   └── templates/
│       └── craft.md.tmpl    # three-round primordia skeleton
│
└── symbionts/               # downstream-project adapters (opt-in, isolated)
    ├── __init__.py
    └── claude_code.py       # Claude Code / Cowork specific surface sugar
```

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
| `src/myco/genesis/` | Genesis | `docs/architecture/L2_DOCTRINE/genesis.md` |
| `src/myco/ingestion/` | Ingestion | `docs/architecture/L2_DOCTRINE/ingestion.md` |
| `src/myco/digestion/` | Digestion | `docs/architecture/L2_DOCTRINE/digestion.md` |
| `src/myco/circulation/` | Circulation | `docs/architecture/L2_DOCTRINE/circulation.md` |
| `src/myco/homeostasis/` | Homeostasis | `docs/architecture/L2_DOCTRINE/homeostasis.md` |
| `src/myco/surface/` | (cross-cutting — adapters for CLI and MCP) | L1 protocol + command manifest |
| `src/myco/meta/` (v0.5+) | (cross-cutting — multi-subsystem verb composer; houses `session-end`, `craft`, `bump`, `evolve`, `scaffold`) | `command_manifest.md` governance-verbs section |
| `src/myco/symbionts/` | (external integrations) | per-symbiont doc under `docs/adapters/` |

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
