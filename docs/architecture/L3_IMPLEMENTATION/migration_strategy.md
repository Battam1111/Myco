# L3 — Implementation Migration Strategy

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L3 procedural. Explains how v0.3 → v0.4 code replacement
> actually happens, given that no legacy branch is retained and tests
> must stay meaningful throughout.

---

## The core question

If we're doing a greenfield rewrite and keeping only `v0.3.4-final` as a
tag anchor (not a branch), how does the code actually swap over without
leaving the substrate in a broken state for weeks?

## Chosen approach — "build parallel, swap atomic"

### Stage A — Parallel build

The new code is authored under a staging path **`src/myco_v4/`** on the
`main` branch. Both `src/myco/` (v0.3 kernel) and `src/myco_v4/` exist
simultaneously during the rewrite. The package name in
`src/myco_v4/__init__.py` is still `myco` (there is no `myco_v4`
distribution); the directory name is a build-time staging marker only.

During Stage A:
- `pyproject.toml` continues to package `src/myco/` (v0.3 kernel).
- v0.3 tests continue to pass against the v0.3 kernel (no regression).
- New code under `src/myco_v4/` is import-isolated: its tests live under
  `tests/v4/` and are run as a separate pytest selection.
- `src/myco_v4/` has its own `__init__.py` with `__version__ = "0.4.0.dev"`
  to keep it recognizable in error traces.

### Stage B — Subsystem cutover

Each subsystem lands in a single commit that:
1. Completes its package under `src/myco_v4/<subsystem>/` with tests.
2. Updates the command manifest to point that verb at the new handler.
3. Leaves the old `src/myco/` code paths intact but no longer invoked.

The cutover order matches dependency order:

```
core  →  homeostasis kernel  →  genesis  →  ingestion  →
digestion  →  circulation  →  surface (CLI + MCP)
```

### Stage C — Atomic swap

Once all subsystems are live under `src/myco_v4/`:
1. Single commit: `git mv src/myco src/myco_legacy_trash` +
   `git mv src/myco_v4 src/myco` + `git rm -r src/myco_legacy_trash`.
2. `pyproject.toml` stays pointing at `src/myco/` (path unchanged).
3. v0.3 tests are deleted; v4 tests move from `tests/v4/` to
   `tests/unit/` and `tests/integration/`.
4. Version bumps to `0.4.0` (dropping the `.dev` suffix).
5. L4 substrate re-export runs (fresh `_canon.yaml`, fresh `notes/`).
6. `git tag -a v0.4.0 -m "Greenfield rewrite release"` (locally; push
   requires separate owner approval per the standing directive).

## Why not a branch?

A `rewrite/v0.4` branch would work, but §9 mandated "no long-lived
legacy branch." Building on `main` with a `src/myco_v4/` staging path
keeps history linear and avoids the ritual of a long-lived branch while
still letting the v0.3 kernel remain functional during the transition.

## Why not rm -rf src/myco first?

Because during the multi-session rewrite:
- Downstream ASCC still invokes `myco hunger` / `myco reflect` via the
  installed v0.3 wheel. Until v0.4 ships, those calls must work.
- The dev environment's `pip install -e .` points at `src/myco/`. If
  that directory disappears, local `myco` commands fail until Stage C.

## Tests during the rewrite

- `tests/unit/` and `tests/integration/` continue to test v0.3 and
  continue to be the pre-commit target.
- `tests/v4/` is excluded from the default pytest run; opt in via
  `pytest tests/v4/`. This keeps `pytest` green at all times without
  requiring v4 to be feature-complete.
- A CI gate added at Stage A ensures `tests/v4/` is not regressed once
  subsystems start landing.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Import ambiguity (both `src/myco/` and `src/myco_v4/` import as `myco`) | Only one is registered in `pyproject.toml`; dev tooling uses a test runner that adds only the active path to `sys.path` |
| Stage C discovers late a missing subsystem piece | Each subsystem cutover commit is its own PR-level gate with checklist |
| Long in-flight rewrite fatigue | Each subsystem is one session; manifest lists eleven verbs total; concrete, finite scope |
| ASCC breaks mid-rewrite because something in v0.3 kernel shifted | v0.3 kernel is frozen — only bug fixes, no features, until Stage C |

## Directive compliance check

- §9 E2 "fresh re-export": L4 substrate is re-exported at Stage C. Code is
  authored fresh under `src/myco_v4/`, not in-place-patched.
- §9 E6 "no legacy branch": no long-lived branch is created; history
  stays on `main` with tag anchors.
- §9 execution constraint "strict top-down": every cutover commit
  references the L2 doctrine and L3 package_map it's implementing.
- §9 execution constraint "no reverse erosion": if a Stage B commit
  requires changing L0/L1/L2, it must stop and author a craft doc first.
