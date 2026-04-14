# Stage A Scaffold — Implementation Craft

> **Status**: APPROVED for execution 2026-04-15 by Yanjun.
> **Depth**: one-round. Stage A has no real design tensions — all
> shape decisions were fixed in L0-L3 docs. This craft exists to
> record the concrete file inventory and the verification contract,
> not to argue structure.
> **Governing docs**:
> - `docs/architecture/L0_VISION.md` (five root principles)
> - `docs/architecture/L1_CONTRACT/versioning.md` (`0.4.0.dev`,
>   Hatchling dynamic version SSoT)
> - `docs/architecture/L3_IMPLEMENTATION/package_map.md`
>   (eight-package layout)
> - `docs/architecture/L3_IMPLEMENTATION/migration_strategy.md`
>   (single-path, no v4 marker)

---

## Intent

Establish the build surface so Stage B.1 onward can focus on logic,
not on scaffolding. Stage A is mechanical. It succeeds when:

1. `pip install -e .` works from the repo root.
2. `python -c "import myco; print(myco.__version__)"` prints
   `0.4.0.dev`.
3. `pytest --collect-only` finds the sanity test and no collection
   errors.
4. `pytest tests/test_scaffold.py` passes.

## File inventory

### Build config
- `pyproject.toml` — Hatchling dynamic version; console script
  `myco = myco.surface.cli:main`; pytest ini options; minimal deps
  (pyyaml for canon parsing in B.1/B.2; nothing else until needed).
- `.gitignore` — augmented with Python / pytest / packaging
  defaults. (Root `.gitignore` inherited from pre-quarantine era is
  preserved; augments are additive.)

### Meta
- `CHANGELOG.md` — fresh, records the `0.4.0.dev` start. Old
  CHANGELOG lives in `legacy_v0_3/`.

### Source tree (`src/myco/`)

Each `__init__.py` is a short docstring referencing the L2 doctrine
doc. No business logic.

```
src/myco/
├── __init__.py               __version__ = "0.4.0.dev"  (SSoT)
├── __main__.py               python -m myco entry; NotImplementedError
│                             placeholder until B.7
├── core/__init__.py          L1 primitives; no subsystem deps
├── genesis/__init__.py       → L2_DOCTRINE/genesis.md
├── genesis/templates/__init__.py
├── ingestion/__init__.py     → L2_DOCTRINE/ingestion.md
├── digestion/__init__.py     → L2_DOCTRINE/digestion.md
├── circulation/__init__.py   → L2_DOCTRINE/circulation.md
├── homeostasis/__init__.py   → L2_DOCTRINE/homeostasis.md
├── homeostasis/dimensions/__init__.py
├── surface/__init__.py       CLI + MCP adapters (per L3 command_manifest.md)
└── symbionts/__init__.py     downstream-project adapters
```

### Test tree (`tests/`)

```
tests/
├── __init__.py
├── conftest.py               shared fixtures (tmp project root)
├── test_scaffold.py          sanity: every package imports; __version__ is 0.4.0.dev
├── unit/
│   ├── __init__.py
│   ├── core/__init__.py
│   ├── genesis/__init__.py
│   ├── ingestion/__init__.py
│   ├── digestion/__init__.py
│   ├── circulation/__init__.py
│   ├── homeostasis/
│   │   ├── __init__.py
│   │   └── dimensions/__init__.py
│   └── surface/__init__.py
└── integration/
    └── __init__.py
```

## Decisions recorded here

- **pyproject.toml — Hatchling, not setuptools.** L1 versioning.md
  specifies Hatchling dynamic version as the SSoT mechanism.
- **`0.4.0.dev` suffix during Stage A–B.** Drops to `0.4.0` only at
  Stage C. L1 versioning.md "Starting points" calls this out.
- **Console script points at a not-yet-existing target.**
  `myco = myco.surface.cli:main` is installed now; invoking it
  before B.7 will `ImportError`. That is acceptable — it documents
  the target shape and forces B.7 to land before v0.4.0 can ship.
- **`src/myco/__main__.py` raises deliberate `NotImplementedError`.**
  `python -m myco` returns a clear error rather than a silent
  import failure.
- **Minimal runtime deps.** Only `pyyaml` is added as a runtime
  dep. Dev deps: `pytest`, `pytest-cov`. No `rich`, no `typer`, no
  `mcp` SDK yet — those land when B.7 needs them.
- **No hooks under `.claude/` yet.** SessionStart and PreCompact
  hooks wire to `myco hunger` / `myco session-end`, which don't
  exist until B.4 and B.7. Adding hooks now would break the very
  next session. Hooks land at Stage C as part of the substrate
  re-export.
- **No `_canon.yaml` at the root yet.** Same reasoning — canon is
  fresh-authored at Stage C. Tests use `tmp_path` fixture canons.

## What could go wrong (brief self-rebuttal)

- *pip install -e . fails because of Hatchling path resolution on
  WSL / mount.* → Pre-check with a dry `hatch version` if we have
  hatch installed; otherwise `pip install -e . -v` will surface the
  failure and we can fix the path spec in pyproject.
- *`tests/unit/homeostasis/dimensions/` will sit empty for a long
  time before B.8.* → That's fine; it documents the expected shape.
  An empty `__init__.py` is not a lint finding.
- *Augmenting the root `.gitignore` might conflict with Cowork's
  desktop-commander behavior.* → Augments are additive; existing
  ignores are preserved.

## Verification script (run at end of Stage A)

```bash
pip install -e .
python -c "import myco; assert myco.__version__ == '0.4.0.dev', myco.__version__"
python -m myco   # expect deliberate NotImplementedError with a clear message
pytest --collect-only
pytest tests/test_scaffold.py -v
```

All four must pass. If any fails, the Stage A commit is rolled back
and the craft's §"What could go wrong" is revisited.
