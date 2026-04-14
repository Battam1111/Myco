# Stage B.3 — Genesis (Bootstrap) Craft

> **Date**: 2026-04-15
> **Governs**: `src/myco/genesis/` + `tests/unit/genesis/`.
> **Upward**: L2 `genesis.md` + L1 `canon_schema.md`.
> **Scope**: one command — `myco genesis` — creates the first substrate
> state in a bare project directory. Runs **once** per project lifetime.

---

## Round 1 — 主张 (tentative design)

Genesis owns the birth of a substrate. Input: a project directory with
nothing Myco-specific in it. Output: a minimal, lint-clean skeleton.

Proposed surface:

```python
def bootstrap(
    *,
    project_dir: Path,
    substrate_id: str,
    tags: Sequence[str] = (),
    entry_point: str = "MYCO.md",
    contract_version: str = _DEFAULT_CONTRACT_VERSION,
    dry_run: bool = False,
) -> Result: ...
```

On execution:

1. Refuse if `project_dir/_canon.yaml` already exists
   (`ContractError` → exit 3).
2. Render `_canon.yaml` from `templates/canon.yaml.tmpl` via
   `string.Template.substitute`. Dollar-prefix placeholders avoid YAML
   `{}` flow-style collisions.
3. Create `notes/`, `docs/`, `.myco_state/` directories.
4. Write `.myco_state/autoseeded.txt` with a single-line provenance
   marker. Homeostasis reads this to enable skeleton-mode downgrade.
5. Render and write the entry-point file (`MYCO.md` or `CLAUDE.md`)
   from `templates/entry_point.md.tmpl`.
6. Return `Result(exit_code=0, payload={files_created: (...), dry_run,
   project_dir, substrate_id})`.

Templates live at `src/myco/genesis/templates/` and are packaged with
the wheel (Hatchling picks them up under `packages = ["src/myco"]`).

## Round 1.5 — 自我反驳 (attack)

T1. **Handler signature mismatch with command manifest.** The manifest
(L3 `command_manifest.md`) specifies
`run(args: dict, *, ctx: MycoContext) -> Result`. But genesis
*predates* the substrate — there is no `MycoContext` to hand it.
Accepting `ctx` forces callers to construct a fake substrate.

T2. **Template engine choice.** Picked `string.Template`. But canon is
YAML with list values (`tags: ["a", "b"]`). Rendering a Python list
requires a helper that emits YAML flow syntax. Is that a hidden
complexity?

T3. **Idempotency vs one-shot.** L2 doctrine says "re-running Genesis
on an established substrate is an error, not a convenience." But the
code already treats partial states (marker present, canon absent) —
what if `_canon.yaml` is missing but `.myco_state/` exists? Is that a
corruption case or a re-run case?

T4. **Substrate-id validation.** Proposal silently accepts any string.
The canon schema says "slug; globally unique". If we allow
`"My Substrate"` with spaces, the next `myco hunger` call may emit
weird diagnostics.

T5. **Contract-version drift.** Hardcoding `v0.4.0-alpha.1` inside
`genesis.py` duplicates the SSoT. Where should the default live?

T6. **Dry-run semantics.** Returning just the list of paths doesn't
let a caller preview the actual rendered content. A thoughtful
`--dry-run` shows what would be written.

T7. **Entry-point content.** The entry-point template is
project-agnostic. But the file mentions subsystems, architecture refs,
and root principles — all L0/L1 concepts. Will the generated file
trail its hardcoded references when L0/L1 shift?

## Round 2 — 修正 (revised design)

Resolutions in order:

R1 (→ T1). Genesis has a **non-manifest Python surface** (`bootstrap`)
and a **separate manifest handler wrapper** (Stage B.7) that
translates `args` into `bootstrap(**kwargs)` without needing a live
`ctx`. The manifest's handler signature is relaxed for genesis only:
`surface/cli.py` detects the `genesis` verb and calls `bootstrap`
directly, bypassing the `ctx` requirement. This keeps the kernel
invariant clean: every *other* command takes `ctx`, genesis is the
sole exception because it creates the substrate `ctx` wraps.

R2 (→ T2). Templates receive pre-rendered strings. `bootstrap` does
the YAML shaping in Python (`_yaml_flow_list(tags)`) before handing
the ready-to-substitute string to `string.Template`. That keeps
templates tool-independent and keeps us off Jinja2.

R3 (→ T3). `bootstrap` checks **two** signals:
- Canon already present → `ContractError("substrate already exists")`.
- `.myco_state/` present but canon absent → `ContractError(
  "partial genesis state; refusing to proceed — remove
  .myco_state/ or restore _canon.yaml")`.

R4 (→ T4). Validate `substrate_id` against `^[a-z][a-z0-9_-]{0,63}$`.
Reject with `UsageError` if it doesn't match. Tags are slug-like too
but tolerated as-is (they're free-form per L0).

R5 (→ T5). Contract version lives as a module constant
`myco.genesis.DEFAULT_CONTRACT_VERSION = "v0.4.0-alpha.1"`. Surface
layer (B.7) may override via CLI flag. A Stage B.8 lint dimension
will later verify the canon's contract_version matches a SSoT
declared somewhere in code — we don't try to solve that here.

R6 (→ T6). Dry-run returns a `Mapping[Path, str]` inside the payload
(`preview`) so callers can print or diff. The file-creation side-effect
is the only difference from a real run.

R7 (→ T7). The entry-point template deliberately references **only**
the canon and two stable top-level docs (`docs/architecture/` and the
canon-declared `subsystems`). If those shift, the entry-point file is
regenerated by migration, not patched in place.

## Round 2.5 — 再驳 (attack the revisions)

T8. R1 concedes an exception: genesis is "special" among verbs. Is
the special case a symptom of a deeper design mistake (the manifest
assumes every handler needs `ctx`)? Two options:
- (a) Make `ctx` Optional[MycoContext] in the handler signature.
- (b) Keep `ctx` mandatory but let genesis receive a **pre-substrate
  ctx** that only carries env + stdout/stderr, leaving `substrate`
  nullable.

T9. R3 draws a line between "canon present" and "marker present, canon
absent". But what if `notes/` already exists with files in it (user
created it manually)? Do we merge, refuse, or clobber?

T10. R4's regex bans uppercase. The user may want
`ASCC-research` — that's a real-world substrate name. Too strict?

## Round 3 — 反思 + 最终方案

Resolutions:

F8 (→ T8). Adopt option (a) **but defer implementation** to Stage B.7
surface. Right now genesis is importable as `bootstrap` with no `ctx`
argument. When the manifest loader lands, it will detect the
genesis-shaped handler by its declared signature and not construct a
ctx for it. Recording the decision here so B.7 doesn't reinvent it.

F9 (→ T9). `bootstrap` **refuses to clobber** any existing file it
would write. An existing `notes/` directory that is empty is fine
(we'd create it anyway). A non-empty `notes/` is not a genesis
violation; we just don't touch it. But `.myco_state/autoseeded.txt`
and the entry-point file must not pre-exist — if either does, raise
`ContractError`.

F10 (→ T10). Loosen the regex to
`^[A-Za-z][A-Za-z0-9_-]{0,63}$`. Reject whitespace and leading
digit/punct; allow mixed case. Matches ASCC-style names.

### What this craft revealed

- The manifest's `(args, ctx) -> Result` rule was authored before
  genesis's role was fully specified. The "genesis exception" is
  small enough to hold now, large enough to drive the B.7 design of
  the manifest loader. Flag noted.
- "Skeleton mode" is born at genesis and consumed at homeostasis —
  this stage is the producer half; B.2 already implemented the
  consumer half. The marker's path is canonical; hardcoding
  `.myco_state/autoseeded.txt` in both sides is deliberate (per L1
  canon schema § `lint.skeleton_downgrade.marker`).
- No L0/L1/L2 edits emerged. The craft stays inside L3.

## Deliverables

```
src/myco/genesis/
├── __init__.py              # re-exports bootstrap, DEFAULT_CONTRACT_VERSION
├── genesis.py               # bootstrap() implementation
└── templates/
    ├── __init__.py          # empty (so the dir is a package for importlib.resources)
    ├── canon.yaml.tmpl
    └── entry_point.md.tmpl

tests/unit/genesis/
├── __init__.py
└── test_genesis.py          # ~12 tests covering happy path + refusals
```

No L0/L1/L2 edits. No changes to existing core/ or homeostasis/ code.

## Acceptance

- `pytest tests/unit/genesis/` green.
- `pytest` (full) still green (109 prior + genesis additions).
- Running bootstrap on `tmp_path` produces a substrate that
  `Substrate.load` accepts.
- Running bootstrap on that substrate again raises `ContractError`.
