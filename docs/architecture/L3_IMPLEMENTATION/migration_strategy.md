# L3 — Implementation Migration Strategy (single-path)

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9 + Yanjun's
> 2026-04-15 single-path directive: "不用标记 v4，现在这个就作为涅槃重生的
> myco 本 myco").
> **Layer**: L3 procedural. Explains how the v0.4.0 rewrite is built
> into `src/myco/` directly, without any `src/myco_v4/` staging path.

> **Historical note (v0.5.3 rename)**: throughout this document,
> `genesis/` refers to the v0.4.0 package name. v0.5.3 renamed the
> package to `germination/`; the legacy import path is preserved
> through v1.0.0 as a shim (`from myco.genesis import ...` continues to
> resolve with a `DeprecationWarning`). Similarly, `meta/` → `cycle/`
> at v0.5.3 with the same shim treatment. This migration_strategy
> document describes the v0.4.0 greenfield plan and is retained as
> historical audit record; the body is NOT rewritten to the new names,
> so that the record of "what the v0.4.0 plan actually said" stays
> intact. For current package layout see `package_map.md`.

---

## Why single-path (supersedes earlier parallel-build sketch)

An earlier draft of this doc proposed a parallel-build strategy:
authoring v0.4 code under `src/myco_v4/` alongside `src/myco/` v0.3,
then an atomic swap at Stage C. That was the right answer while v0.3
code still lived at the repository root. It is the **wrong** answer
now.

After the 2026-04-15 quarantine, all v0.3 content is in
`legacy_v0_3/`. The repository root has no `src/`, no `tests/`, no
`pyproject.toml`. There is no collision to work around. Authoring
under `src/myco_v4/` would be ceremonial — and would silently encode
the idea that v0.4 is a "next version alongside v0.3", which
contradicts the directive "this IS the reborn myco itself".

Therefore the new code goes directly into `src/myco/` at the
repository root. There is no staging path, no atomic swap, and no
v4 marker in package names, test paths, or git history.

## The sequence

### Stage A — Scaffold

Single commit establishes the build surface:

- `src/myco/` with eight packages (per `package_map.md`): `core/`,
  `genesis/` (+ `templates/`), `ingestion/`, `digestion/`,
  `circulation/`, `homeostasis/` (+ `dimensions/`), `surface/`,
  `symbionts/`.
- Each `__init__.py` carries a short docstring pointing at the
  corresponding L2 doctrine file. No business logic yet.
- `src/myco/__init__.py::__version__ = "0.4.0.dev"` (per L1
  `versioning.md` "Starting points").
- `src/myco/__main__.py` as the `python -m myco` entry; during
  Stage A it raises a deliberate `NotImplementedError` until
  `surface/cli.py` lands in Stage B.7.
- `pyproject.toml` — Hatchling dynamic version, `myco` console script
  pointing at `myco.surface.cli:main`, pytest config, minimal
  runtime deps.
- `.gitignore` — fresh Python ignores; the root `.gitignore` carried
  over from v0.3 is preserved but augmented.
- `CHANGELOG.md` — fresh, records `0.4.0.dev` start.
- `tests/` — mirror layout (`unit/<subsystem>/`, `integration/`) with
  `__init__.py` shims; a single sanity test verifying every package
  imports.

Verification at end of Stage A:

- `pip install -e .` succeeds.
- `pytest --collect-only` finds the sanity test.
- `pytest tests/test_scaffold.py` passes.
- `python -c "import myco; print(myco.__version__)"` prints `0.4.0.dev`.

### Stage B — Subsystems (top-down, one per session)

Each B.x step lands one subsystem, in dependency order:

```
B.1 core              (no intra-myco deps)
B.2 homeostasis kernel + exit_policy + skeleton + dim registry
B.3 genesis           (depends on core + homeostasis kernel)
B.4 ingestion         (depends on core, homeostasis)
B.5 digestion         (depends on core, ingestion's note format)
B.6 circulation       (depends on core, digestion's integrated notes;
                       includes propagate per §9 E4 redefine-first)
B.7 surface           (depends on all subsystems; manifest + CLI + MCP)
B.8 homeostasis/dimensions/   (authored fresh against L1/L2 needs,
                               NOT ported from v0.3's 30-dim table)
```

Each B.x step:

1. Opens a short implementation craft under `docs/primordia/` —
   depth calibrated to conflict density (one round if the doctrine
   already fixed the shape; three rounds if real tensions emerge).
2. Implements under `src/myco/<subsystem>/` with per-module tests
   under `tests/unit/<subsystem>/`.
3. Ends with: subsystem's tests green, `myco immune` clean within its
   scope, commit, todo list update.

### Stage C — v0.4.0 release

At the end of Stage B.8 the code is complete. Stage C materializes
the substrate:

1. **Fresh `_canon.yaml`** at the repository root, authored from the
   L1 `canon_schema.md` template. ≤ 300 non-comment lines.
2. **Fresh `MYCO.md`** at the repository root, the agent entry page,
   strictly following L0's five root principles. Not a port of the
   old `legacy_v0_3/MYCO.md`.
3. **Fresh `.claude/hooks/`** — SessionStart + PreCompact hooks
   wired to the new `myco hunger` / `myco senesce` (alias
   `session-end`) surface.
4. **ASCC migration script** under `scripts/migrate_ascc_substrate.py`
   (dry-run default, `--execute` opt-in). Maps ASCC's v0.3 canon
   fields into the new schema per §9 E2 "fresh re-export" discipline.
5. **Full immune pass** — mechanical + shipped + metabolic + semantic
   all clean on the new substrate.
6. **Full test suite** — `pytest` green including integration.
7. **Version bump** — `src/myco/__init__.py::__version__ = "0.4.0"`
   (drop the `.dev`).
8. **Delete `legacy_v0_3/`** — `git rm -r legacy_v0_3/` in a single
   commit.
9. **Tag** — `git tag -a v0.4.0 -m "Greenfield rewrite release."`
10. **Hold for push approval** — no `git push` until Yanjun
    separately approves.

## Invariants throughout

- No v4 marker appears anywhere: not in paths, not in package names,
  not in test IDs, not in git commit subjects. The code is **myco**,
  not myco-v4.
- No file under `legacy_v0_3/` is imported, tested, or referenced by
  any live file. That is the quarantine contract.
- Each B.x commit keeps `pytest` green and `myco immune` clean
  within the scope that exists at that point. A red test or immune
  finding blocks the next stage.
- L0/L1/L2 docs are not edited as a consequence of B.x implementation
  work. If implementation reveals a genuine gap in doctrine, work
  stops and a craft doc is authored to propose the upper-layer
  change — per the top-down invariant.

## Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Importing from `legacy_v0_3/` by accident | No `sys.path` entry for it; a homeostasis dimension (B.8) will lint any `import myco_legacy` or similar |
| Subsystem build takes more than one session | Each B.x is small enough to land in one session (300–800 LoC per subsystem typical); if it overruns, the craft splits it |
| `_canon.yaml` is absent during Stage A/B | All subsystem tests use fixture canons in `tmp_path`; no code path requires root canon until Stage C |
| ASCC breaks mid-rewrite | Pre-rewrite Myco v0.3.4 is pinned at `v0.3.4-final`; ASCC continues to use that until v0.4.0 is published and ASCC is manually migrated |
| Deleting `legacy_v0_3/` loses useful history | Git history is preserved; tag `v0.3.4-final` remains as the sole anchor |
| Missing piece discovered mid-Stage B | Per user-global rule 4: stop, update the plan, then continue — never patch reactively |

## Directive compliance check

- §9 E2 "fresh re-export": L4 substrate authored fresh at Stage C, not
  in-place migrated.
- §9 E6 "no legacy branch": only `v0.3.4-final` tag retained;
  `legacy_v0_3/` is a disk-level read-only snapshot, scheduled for
  deletion at Stage C.
- §9 execution constraint "strict top-down": each B.x commit
  references the L2 doctrine + L3 package_map entry it implements.
- §9 execution constraint "no reverse erosion": if a B.x discovers a
  need that requires editing L0/L1/L2, work stops, craft is authored,
  change is approved, then implementation resumes.
- 2026-04-15 "no v4 marker": this doc is the authoritative record of
  that decision; all subsequent scaffolding conforms.
