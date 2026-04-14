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
mutation must go through governance (craft + bump), not through drift.
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
myco immune [--fix] [--exit-on <spec>] [--json] [--only <dim>...]
myco immune --list          # enumerate dimensions, categories, severities
myco immune --explain <dim> # prose description from the dimension's own file
```

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
   named `l<N>_<slug>.py` with a dimension-local docstring that becomes
   the `--explain` output.
2. A category assignment in `_canon.yaml::lint.dimensions`.
3. A test under `tests/unit/homeostasis/` named `test_l<N>_*.py`.
4. A changelog entry in `docs/contract_changelog.md` (contract bump
   required if it changes category semantics; not required if it's a
   pure addition within an existing category).

## What changed from pre-rewrite

The v0.3 `immune.py` monofile (4400 LoC) is decomposed: each dimension
has its own file, the orchestration is a thin loop, and the 30-dim
inventory is reconsidered at L3 design time (some dimensions consolidate,
some split, the contract is not to preserve count). Total kernel code
budget for Homeostasis at v0.4.0: ≤ 1500 LoC excluding per-dimension
files.
