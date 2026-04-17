# L2 — Homeostasis

> **Status**: APPROVED (2026-04-15, greenfield rewrite §9).
> **Layer**: L2. Subordinate to `L0_VISION.md` and `L1_CONTRACT/*`.
> **Upward mapping**: enforces L1 R6 (write-surface), R7 (top-down
> mapping integrity), R1/R2 reflexes, and all three L0 invariants.

---

## Responsibility

Homeostasis owns **identity defense**: the immune system that detects
drift between the substrate's stated contracts (L0/L1/L2 + canon) and its
observed reality (files on disk, tests, package state).

Where Circulation asks "is the graph well-formed?", Homeostasis asks
"does the substrate still match what it claims to be?"

Critically, Homeostasis operates **under continuous change**. L0
principle 3 (永恒进化) means the substrate's own shape is mutable — but
mutation must go through governance (`fruit` + `molt` — the v0.5.2
aliases `craft` + `bump` still resolve), not through drift.
Homeostasis is what distinguishes the two: sanctioned evolution passes
silently; unsanctioned drift is a finding. A "calm" substrate that never
changes is as suspect as a chaotic one — principle 3 expects evolution.

## Lint dimensions

A lint **dimension** is a single, named check. Each dimension:

1. Belongs to exactly one category (mechanical / shipped / metabolic /
   semantic — see L1 exit-codes doc).
2. Emits findings with severity (CRITICAL / HIGH / MEDIUM / LOW).
3. Has a stable identifier (`L0`, `L1`, …) that persists across versions.

The v0.4.0 dimension set is authored fresh in L3 (not carried forward
from v0.3's 30-dimension inventory). Each dimension lives in its own file
under `src/myco/homeostasis/dimensions/` — never bundled into a
megafile.

**v0.5+ (MAJOR 6 and 7)**: dimension registration is entry-points-
driven. Myco's built-ins register via
`[project.entry-points."myco.dimensions"]` in `pyproject.toml`;
third-party substrates register their own dimensions the same way
(no fork of Myco required). The hardcoded `_BUILT_IN` tuple in
`src/myco/homeostasis/dimensions/__init__.py` is now only a fallback
for dev checkouts without `pip install -e .`. The v0.5 inventory
adds `MF1` (mechanical/HIGH: declared subsystems exist on disk) —
the first cross-check between `_canon.yaml::subsystems` and the
actual package layout.

**v0.5.3**: `MF2` joins the inventory (mechanical/HIGH: substrate-
local plugin health). It fires on broken `.myco/plugins/` shape,
missing `__init__.py`, manifest-overlay YAML errors, import-time
registration failures, or duplicate verb names across the overlay
and the packaged manifest. Substrate-local plugins auto-import at
`Substrate.load()` — MF2 is what keeps that magic audible. The
`graft` verb (Cycle subsystem, new at v0.5.3) is the Agent's
introspection surface for MF2 findings: `graft --list` enumerates
every registered plugin, `graft --validate` re-runs the import-plus-
registration gate, and `graft --explain <name>` prints the source
file and class docstring for a single plugin. Combined with MF1,
the immune system now has ten dimensions (was nine).

## Boundary

Homeostasis **does**:

- Run every dimension on demand (`myco immune`) or incrementally.
- Apply skeleton-mode downgrade (per L1 exit-codes doc).
- Apply gitignore-aware severity downgrade (dimensions may opt in).
- Compute the final exit code from category policy.
- Auto-fix findings when `--fix` is passed and the dimension declares
  itself fixable.

Homeostasis **does not**:

- Infer user intent from findings.
- Rewrite prose or code to "look healthier".
- Decide what's worth checking — that decision is made upstream in L2
  (this doc) and L3 (dimension inventory).

## Interfaces

```
myco immune [--fix] [--exit-on <spec>] [--json] [--dimensions <dim>...]
myco immune --list           # enumerate dimensions, categories, severities
myco immune --explain <dim>  # prose description from the dimension's class docstring
```

At v0.5, `--list` returns `payload.dimensions = [{id, category,
default_severity, summary}, …]` (sorted by id; summary is the first
line of the dimension's class docstring). `--explain <dim>` returns
`payload.explain = <class __doc__>` — the full block, not just the
one-line summary. Both modes skip `run()` entirely so they are safe
on any substrate, including ones whose immune kernel would otherwise
emit findings. `--list` and `--explain` are mutually exclusive; the
CLI surface maps them to `run_list` and `run_explain` respectively.

## Cross-subsystem contract

- Reads canon (to know categories, skeleton marker, write-surface).
- Reads substrate files (notes, docs, source, package metadata).
- Emits findings consumed by:
  - Ingestion's boot-brief injector (surfaces HIGH reflexes to the agent).
  - The CI gate via exit code.
  - `myco hunger --json` callers (structured consumption).

## Adding a dimension

A new dimension requires:

1. A one-file implementation under `src/myco/homeostasis/dimensions/`
   named `<id_lowercase>_<slug>.py` with a dimension-local docstring
   (module level) and a class-level docstring (used by
   `myco immune --explain`).
2. A row in `pyproject.toml::[project.entry-points."myco.dimensions"]`
   of the shape `<id> = "module.path:ClassName"`. Built-ins additionally
   append to the `_BUILT_IN` tuple in
   `src/myco/homeostasis/dimensions/__init__.py` to keep dev-checkout
   imports working without `pip install -e .`.
3. A category assignment in `_canon.yaml::lint.dimensions`.
4. A test under `tests/unit/homeostasis/dimensions/` named
   `test_<id_lowercase>_*.py`.
5. A changelog entry in `docs/contract_changelog.md` (contract bump
   required if it changes category semantics; not required if it's a
   pure addition within an existing category).

Third-party substrates register dimensions by step 2 alone in their
own `pyproject.toml` — `default_registry()` picks them up
automatically on next import.

## What changed from pre-rewrite

The v0.3 `immune.py` monofile (4400 LoC) is decomposed: each dimension
has its own file, the orchestration is a thin loop, and the 30-dim
inventory is reconsidered at L3 design time (some dimensions consolidate,
some split, the contract is not to preserve count). Total kernel code
budget for Homeostasis at v0.4.0: ≤ 1500 LoC excluding per-dimension
files.
