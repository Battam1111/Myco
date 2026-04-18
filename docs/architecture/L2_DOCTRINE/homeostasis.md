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
the immune system has ten dimensions at v0.5.5 (was nine). MF2's
scope — substrate-local extension — is one axis of a two-axis
extension model; the per-host axis is `src/myco/symbionts/`. Both
axes are documented together in `extensibility.md` (in-progress;
see also `L3_IMPLEMENTATION/symbiont_protocol.md` for the per-host
seam's contract).

**v0.5.6**: `MP1` joins the inventory (mechanical/HIGH:
"Agent calls LLM; substrate does not"). MP1 forbids a `src/myco/**`
module from importing a known LLM provider SDK (`anthropic`,
`openai`, `google.generativeai`, the `litellm`-family wrappers,
…) unless `_canon.yaml::system.no_llm_in_substrate: false`. The
opt-out form requires populating `src/myco/providers/` (v0.5.6
reserves the package; empty at release) and a contract-bumping
molt. MP1 is the mechanical half of the L0-principle-1 addendum
"Agent calls the LLM; the substrate does not". Combined with MF1
and MF2, the immune system now has **eleven dimensions** at v0.5.6.

### Dimension enumeration (v0.5.6, all 11)

| ID | Category | Default severity | Fixable? | One-line summary |
|---|---|---|---|---|
| `M1` | mechanical | CRITICAL |  | Required canon fields present; top-level shape parses |
| `M2` | mechanical | HIGH | ✓ | Declared entry-point file exists (fix: create minimal skeleton) |
| `M3` | mechanical | CRITICAL |  | All writes stay inside `system.write_surface.allowed` |
| `MF1` | mechanical | HIGH |  | Declared subsystems resolve to real packages on disk |
| `MF2` | mechanical | HIGH |  | Substrate-local plugin shape + overlay YAML + registration all clean |
| `MP1` | mechanical | HIGH |  | No LLM-provider import from `src/myco/**` unless `no_llm_in_substrate: false` (v0.5.6) |
| `SH1` | shipped | CRITICAL |  | `__version__` is the single source; no static `version=` alongside `dynamic` |
| `MB1` | metabolic | MEDIUM | ✓ | Stale assimilation markers cleaned up (fix: prune stale markers) |
| `MB2` | metabolic | MEDIUM |  | Undigested-note backlog pressure — surfaces but never blocks |
| `SE1` | semantic | HIGH |  | Cross-references resolve (no orphans, no dangling refs) |
| `SE2` | semantic | HIGH |  | Canon-cited numbers and paths match observed reality |

Fixable dimensions (marked ✓) declare `Dimension.fixable = True`
and implement the `fix()` protocol (see "Homeostasis does" below).
At v0.5.6 two dimensions are fixable: `M2` and `MB1`. Every other
dimension is report-only; `myco immune --fix` calls `fix()` only
on fixables and leaves the rest to Agent discretion.

## Boundary

Homeostasis **does**:

- Run every dimension on demand (`myco immune`) or incrementally.
- Apply skeleton-mode downgrade (per L1 exit-codes doc).
- Apply gitignore-aware severity downgrade (dimensions may opt in).
- Compute the final exit code from category policy.
- Auto-fix findings when `--fix` is passed and the dimension declares
  itself fixable.

### Fixable-dimension protocol (v0.5.5)

A dimension declares itself fixable by setting
`Dimension.fixable: ClassVar[bool] = True` on the class and
implementing `fix(ctx, finding) -> dict[str, Any]`. The return
shape is:

```python
{
    "applied": bool,          # True if the fix was performed; False if a
                              # guard short-circuited (e.g. the file
                              # already exists with non-empty content).
    "detail": str,            # one-line description of what was done or
                              # why it was skipped — surfaced to the
                              # Agent via `immune --fix` output.
    # dimension-specific keys allowed: "path", "bytes_written", etc.
}
```

`myco immune --fix` iterates findings, calls `fix(ctx, finding)`
on each finding whose emitting dimension has `fixable=True`, and
aggregates the per-finding return dicts into the command-level
result. A dimension with `fixable=False` ignores `--fix` entirely;
a dimension with `fixable=True` must handle every finding it can
emit (partial coverage is a contract bug).

**M2** (missing entry-point file) and **MB1** (stale assimilation
markers) are the first concrete fixable dimensions, both landing
at v0.5.5. Future fixable additions land the same way: declare
`fixable=True`, implement `fix`, mark the row in the dimension
enumeration table above.

Homeostasis **does not**:

- Infer user intent from findings.
- Rewrite prose or code to "look healthier".
- Decide what's worth checking — that decision is made upstream in L2
  (this doc) and L3 (dimension inventory).

## Safe-fix discipline (v0.5.5)

A fixable dimension's `fix()` implementation must obey four rules.
These are doctrine, not style — the kernel guards them before
dispatch, and a dimension that breaks any of them is a contract
bug that MUST be rolled back on discovery.

1. **Idempotent.** Re-running a fix on the same substrate state is
   a no-op. The second call observes the first call's result and
   short-circuits; it does not re-write identical bytes, and it does
   not amplify. Formally: `fix` is applied *to* a finding; if the
   finding no longer exists on re-scan, `fix` returns
   `{"applied": False, "detail": "already resolved", ...}`.

2. **Narrow.** A single `fix` call creates or corrects **exactly one**
   named file or field. It never cascades — fixing M2 does not also
   create `notes/`, populate canon, or register a dimension. If a
   finding implies a chain of changes, that chain is N separate
   findings from N separate dimensions, each with its own narrow
   fix. Cascades are how drift-healing turns into drift-creating.

3. **Non-destructive.** A fix NEVER deletes. A fix NEVER overwrites
   non-empty content. If the fix would overwrite non-empty content,
   the fix short-circuits with `{"applied": False, "detail":
   "would-overwrite: <reason>"}` and emits an informational finding
   so the Agent sees the conflict. The Agent decides whether to
   proceed — the substrate does not guess.

4. **Bounded.** The fix target path MUST resolve under
   `canon.system.write_surface.allowed`. The kernel guards this
   before calling `fix()`; a `fix()` that targets outside the
   allowed surface is a contract violation and is blocked — the
   dimension sees a `PermissionError` and the finding stays
   unresolved. This ties safe-fix discipline back to R6 (write-
   surface) and prevents fixes from writing beyond the substrate's
   declared boundary.

The four rules compose: a safe fix is idempotent AND narrow AND
non-destructive AND bounded. A fix that is idempotent but
unbounded is not safe. A fix that is narrow but destructive is
not safe. "Safe" is the conjunction.

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
