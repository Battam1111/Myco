---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
closes:
  - "Wave 27 D8 implementation brief: myco compress MVP + io_utils + L18 + compression_ripe"
  - "anchor #4 (压缩即认知) impl_coverage gap 0.35 → ~0.75"
---

# Wave 30 — `myco compress` MVP (v0.26.0)

> **Scope**: kernel_contract implementation craft. Lands the substrate's
> first forward-compression primitive per Wave 27 design (D1–D9). Bundles
> the io_utils atomic-write helper + L18 lint dimension + compression_ripe
> hunger signal + 5 new tests as one subsystem (per Wave 27 D8). Bumps
> contract v0.25.0 → v0.26.0.
>
> **Parents**:
> - Wave 27 `compression_primitive_craft_2026-04-12.md` (design specification)
> - Wave 26 `vision_reaudit_craft_2026-04-12.md` §3.3 (Wave 27+ scope lock)
> - Wave 29 `biomimetic_execution_craft_2026-04-12.md` (re-export pattern Wave 30 dogfoods)
>
> **Supersedes**: none. Pure new-feature implementation.

## 0. Problem definition

Wave 27 produced a complete design for `myco compress` (D1–D9) but no code.
Anchor #4 (`压缩即认知：存储无限，注意力有限`) remains the lowest-coverage
identity anchor at `implementation_coverage = 0.35` per Wave 26 Round 1's
audit. Wave 27 itself increased Wave 30's risk by elevating expectations:
the design is locked, the contract between design and implementation is
public, and now Wave 30 must validate the design against real
implementation pressure or admit Wave 27's confidence was inflated.

What Wave 30 must produce, end-to-end, in one wave:

1. `myco compress` verb that takes either `--tag <T>` or positional note
   ids, builds an output `extracted` note with full audit fields, and
   excretes the inputs with bidirectional back-references.
2. A reusable atomic-write primitive (`src/myco/io_utils.py::atomic_write_text`)
   so the compression's multi-file write is at least best-effort atomic
   via temp-file + `os.replace`. This is the first piece of hermes catalog
   C2 (atomic writes) the substrate absorbs.
3. L18 `lint_compression_integrity` enforcing bidirectional audit-chain
   integrity at lint time so a corrupted chain blocks pre-commit hook.
4. `compression_ripe` hunger signal (advisory, not blocking) per Wave 27
   D2 friction-driven trigger.
5. 5 new pytest tests in `tests/unit/test_compress.py` covering each of
   the load-bearing Wave 27 decisions (D3 audit shape / Attack G dry-run /
   §2.1 cascade rejection / §1.7 idempotence / L18 orphan detection).
6. Contract bump v0.25.0 → v0.26.0 with new optional_fields, new
   `valid_sources` enum value `compress`, and new `notes_schema.compression`
   sub-section.
7. All of the above as ONE subsystem per Wave 27 D8 — bundling is
   appropriate because every piece is structurally coupled to the verb's
   correctness. Splitting into 4 waves would leave 3 of them as half-built
   no-ops blocking the verb that justifies them.

## 1. Round 1 — bundling vs splitting

**R1.1 Attack**: Wave 27 D8 was a *recommendation* not a binding decision.
The Wave 25 doctrine "scope discipline = one subsystem per wave" should win.
Wave 30 should ship `myco compress` with the bare minimum needed to
exit 0 (no L18, no hunger signal, no atomic helper — direct file writes
like the rest of `notes.py`). L18 is Wave 31, hunger signal is Wave 32,
io_utils is Wave 33.

**R1.1 Defense**: Rejected. The "subsystem" boundary is not file count, it
is *can the user trust this verb at the moment Wave 30 lands?*. Without L18,
a partial-write torn state at `_execute_compression` mid-flight produces
exactly the shape that L18 catches: an input with `compressed_into` pointing
at a non-existent output. Without `lint_compression_integrity`, that shape
escapes the pre-commit hook and lands in git. Without `compression_ripe`,
the verb has no agent-adaptive trigger surface, which means anchor #4's
`agent-adaptive` clause stays unimplemented past Wave 30. Without
`atomic_write_text`, the multi-file write is *less safe than the existing*
`notes.write_note` because compress mutates 1+N files instead of 1 — the
torn-state surface is amplified, not held flat.

These four pieces are **structurally coupled** to the verb's correctness in
a way that the Wave 25 D1 scope rule does not contemplate. Wave 25 D1
addressed "feature creep" (don't ship unrelated features in the same wave);
Wave 30 ships nothing unrelated. Every piece is one of: (a) the verb itself,
(b) a safety mechanism for the verb, (c) a trigger surface for the verb,
(d) tests for the verb. The bundling is necessary, not opportunistic.

**R1.2 Attack**: Five tests is too many for an MVP. The Wave 25 baseline
was 4 tests for the entire `tests/` tree. Adding 5 in one wave doubles the
test suite. That is a tooling-velocity hit on every future wave's CI cycle.

**R1.2 Defense**: Each of the 5 tests guards a Wave 27 design decision that
would silently regress without it. A 5-line decision in a craft is cheap to
write and 100× harder to discover regressed than to test once at land time.
The five tests run in <0.5 seconds total (measured: full suite went from
0.10s to 0.33s) — the velocity cost is one decimal point of CI time. The
velocity *gain* is that future waves modifying compress get a safety net at
the boundary that scared us most (cascade prevention, L18 integrity, dry-run
purity). The Wave 25 baseline of 4 was a *floor*, not a ceiling. Wave 30's
multiplier is justified by the verb's complexity (multi-file two-phase write
+ schema additions + new lint dimension): more surface, more tests.

## 2. Round 2 — atomicity model

**R2.1 Attack**: `atomic_write_text` uses `tempfile.mkstemp` + `os.replace`
in the same directory. On Windows (the user's primary OS), `os.replace` is
atomic at the filesystem level, but a process crash *between* the output
note write and the input updates leaves a torn state where the new
extracted note exists with `compressed_from: [a, b, c]` but a/b/c are still
status `raw`. L18 catches this on the *next* lint run, but if the next
operation is "myco eat" or "myco hunger" before "myco lint", the torn state
is invisible to the agent. Wave 30 ships a verb whose torn-state window is
larger than `notes.write_note`'s.

**R2.1 Defense**: Accepted as a known limitation, mitigated three ways:

1. **Phase ordering**: write the output FIRST. If output write fails, none
   of the inputs are touched (zero torn state). If any input write fails
   AFTER output succeeds, the output exists pointing at unflipped inputs —
   a torn state, but one where the *audit trail itself* is the recovery
   instructions: `compressed_from: [a, b, c]` lists exactly which inputs
   need their status flipped to `excreted`. Manual recovery is mechanical.
2. **Best-effort warning**: `_execute_compression` catches per-input write
   failures, accumulates them, and emits a `[WARN] myco compress: N input(s)
   failed to update after output was written. Substrate is in a torn state...`
   to stderr with explicit recovery instructions citing the output id.
3. **L18 backstop**: the next lint run catches both directions of the torn
   state — either an output with no compressed_from members (pre-W30 verb
   regression) or an input with `compressed_into` pointing at an output
   that exists but does not back-reference it (the torn shape).

A *true* transactional multi-file write would require either filesystem-
level transaction support (not portable), an external journal (heavy
infrastructure), or a copy-on-write directory rename (changes the project
layout). All three are out of Wave 30 scope per Wave 27 D7 ("atomicity:
best-effort via two-phase commit"). The honest framing is: Wave 30's
torn-state window is *bounded by L18 detection*, which is the substrate's
chosen integrity model — same model as L1 reference integrity, L2 number
consistency, L8 .original sync, etc. Trust the lint, run the lint.

**R2.2 Attack**: `_resolve_cohort_by_tag` defaults to `{"raw", "digesting"}`.
But Wave 27 D1's wording is `"raw notes"` plural — the user might expect
that calling `myco compress --tag T` only operates on `raw` and *not*
`digesting`. Defaulting to both is a silent assumption beyond the design.

**R2.2 Defense**: Accepted with reframing. Wave 27 §1.1 actually says "all
raw notes matching a given frontmatter tag" in the option (a) text, but
§4.1 D1 just says "tag-scoped (primary)". Neither phrasing forbids
`digesting`. The reason to include `digesting` by default is that the
metabolic pipeline `raw → digesting → integrated → compressed` (or ` →
extracted` for compress's output) means a note that has been viewed once
(state `digesting` per Wave 18 D-layer seed) should still be eligible —
otherwise the user's act of *reading* a note pre-commit excludes it from
the next compression. That's a worse silent failure than the one R2.2
warns against. The fix: keep both as eligible default, but expose
`--status raw` as a one-flag override for the user who wants the strict
shape. The status flag is already implemented in `run_compress` and the
test `test_compress_idempotent_empty_cohort` exercises the default path.

**R2.3 Attack** (discovered during Round 2 test run): The first pytest
run revealed a real bug in `_resolve_cohort_by_tag` that this defense
process surfaced. The output note inherits the aggregated input tags via
`_build_output_meta`'s `aggregated_tags` loop. After the first compress on
tag `idempotent`, the output extracted note carries tag `idempotent` AND has
status `extracted` AND has `compressed_from` set. The original resolver
filtered only on `excreted`, so the output got re-resolved on the second
run, hit the cascade-prevention validator, and exited 3 instead of 4. The
test `test_compress_idempotent_empty_cohort` caught this immediately —
exit 4 expected, exit 3 observed. Wave 27 §1.7 idempotence guarantee was
silently violated by an incomplete resolver filter.

**R2.3 Defense**: Fixed in resolver (commit-pending diff): default
eligible-status filter is `{"raw", "digesting"}`, AND the resolver
explicitly skips notes that already have `compressed_from` set as a
belt-and-suspenders defense even if a future status enum addition leaves
the status filter loose. This is the exact case Wave 27 Attack F warned
about (audit-at-scale escape) — the test caught it before commit, which
is the entire point of Wave 25's tests infrastructure investment. **The
test caught a real bug in the implementation craft on its first run.**
This is the strongest possible motivation for Wave 25's existence and
is recorded as a confidence-amplifying signal in §4.4.

## 3. Round 3 — schema + naming

**R3.1 Attack**: `source: compress` is a new enum value in
`_canon.yaml::notes_schema.valid_sources`. Wave 27 L3 explicitly flagged
this as unresolved — "If Wave 28's Round 2 finds reason to reuse an existing
value (e.g. `promote`), D3's output shape still holds but the source value
changes." Wave 30 must commit one way and defend it.

**R3.1 Defense**: Adding `compress` (not reusing `promote`). Reasons:

1. **Semantic distinction**: `promote` is the existing source for a note
   that was elevated through digest gates without losing its source data
   (1-input → 1-output renaming). `compress` is N-input → 1-output with
   bidirectional audit AND structural data loss (the synthesis discards
   detail by definition). Reusing `promote` would conflate two operations
   with different reversibility contracts (`promote` is reversible by
   un-renaming, compress is reversible only via the audit chain).
2. **Lint surface**: L18 keys off `source: compress` to know which notes
   to validate. If we reuse `promote`, L18 must inspect every promoted
   note to see if it has `compressed_from` set, vs. just iterating notes
   where `source == "compress"`. Adds work + couples L18 to L10's source
   enum drift.
3. **Discoverability**: agents reading `myco view --tag X` see the source
   field; `compress` is self-documenting in a way that `promote`-with-
   audit-fields is not.

The added enum value lands in both `_canon.yaml` and the template canon.
ASCC and any downstream consumer must add `compress` to their own
`valid_sources` on next sync. This is a contract bump (v0.25.0 → v0.26.0).

**R3.2 Attack**: `compression_method: "manual" | "hunger-signal"` is a 2-value
enum that Wave 27 D4 left as free-form. `_canon.yaml` has no enum constraint
on `compression_method`. A future agent could write `compression_method:
"vibes"` and L10 would not catch it. Wave 30 ships a soft constraint.

**R3.2 Defense**: Accepted as a known limitation, *not* fixed in Wave 30.
Reasons: (a) the field is in `optional_fields` not `required_fields`, so
L10 already does not enforce values; (b) constraining it to a closed enum
now would lock in two strings before the substrate has friction-validated
either of them — a future hunger trigger may want a more granular method
(`hunger-signal:compression_ripe` vs `hunger-signal:dead_knowledge`); (c)
the rationale field is the source of truth for what happened during
compression, the method field is metadata; (d) a future Wave can elevate
to enum in a single-line `_canon.yaml` edit + a 5-line L18 check, with
zero regression risk because the absence of the field today is already
permitted. Documented as Wave 30 L2 limitation.

**R3.3 Attack**: The new module `src/myco/io_utils.py` is named generically
when the rest of the substrate is now using biomimetic names per Wave 28/29.
"io_utils" reads as software-generic; the biomimetic name should be
something like "membrane.py" (matches L11 "membrane permeability" framing).
Adding a software-generic module in Wave 30 is a step backwards from
Wave 28's nomenclature work.

**R3.3 Defense**: Accepted-with-deferral. The function `atomic_write_text`
is genuinely a low-level I/O primitive — both `notes.py` (metabolism) and
`compress_cmd.py` (compression) call it, and a future hunger sensor could
call it for `boot_brief.md` writes. Naming it `membrane.py` would commit
to a metaphor that may not extend cleanly to non-metabolic callers. The
correct fix is: in Wave 29b or later, evaluate whether the biomimetic name
should be `membrane.py` (if all callers turn out to be metabolic) or some
other name (if not). For Wave 30, ship the implementation under
`io_utils.py` with a comment in the module docstring explicitly flagging
that the name is provisional pending Wave 29b. This is the same "additive
first, rename later" pattern Wave 29 used for `metabolism.py` aliases.

## 4. Decision

### 4.1 D1 — Bundle the full subsystem in Wave 30

Ship `compress_cmd.py` + `io_utils.py` + L18 + `compression_ripe` + 5 tests
+ contract bump as ONE wave per Wave 27 D8. Splitting would create no-op
intermediates per R1.1 defense. Bundling is necessary, not opportunistic.

### 4.2 D2 — Two-phase commit with output-first ordering + L18 backstop

Phase 1: build all content in memory (output text + per-input new texts).
Phase 2: write output via `atomic_write_text`, then iterate inputs writing
each via `atomic_write_text`. On any input write failure: collect, warn
loudly to stderr with output id + recovery instructions. L18 catches any
torn state on the next lint run. This is the "best-effort + lint backstop"
model per R2.1.

### 4.3 D3 — Cohort resolver default = {raw, digesting}, with explicit
cascade skip

`_resolve_cohort_by_tag` defaults to eligible status `{raw, digesting}`
AND skips any note with `compressed_from` set, even if it would otherwise
match the status filter. The dual filter is the belt-and-suspenders
defense against Wave 27 Attack F (audit-at-scale fabrication) and against
the R2.3 silent-idempotence-violation that the first test run caught.

### 4.4 D4 — `source: compress` is a new enum value, not reused

Add `compress` to `valid_sources` in both kernel and template canons.
ASCC and any downstream consumer adds it on next sync. Resolves Wave 27
L3 in the additive direction.

### 4.5 D5 — `compression_method` stays free-form for Wave 30

L10 will not constrain values. Documented as L2 limitation. Future wave
can elevate to enum via single-line canon edit + 5-line L10/L18 check.

### 4.6 D6 — `io_utils.py` name is provisional pending Wave 29b biomimetic
sweep

Ships under `io_utils.py` for Wave 30. Wave 29b evaluates whether to rename
to `membrane.py` or another biomimetic name based on actual call-site
distribution. Module docstring flags the provisional status.

### 4.7 D7 — L18 lint dimension count 18 → 19, contract v0.25.0 → v0.26.0

`lint_compression_integrity` registered in `main()` after L17. Lint
count reported in dogfood + brief refreshed. Contract bumped in kernel
canon + template canon. ASCC syncs on next consumer pass.

### 4.8 D8 — `compression_ripe` is non-blocking advisory

Hunger signal returns `compression_ripe: tag '<T>' has N raw notes (oldest
M days old)` without `[REFLEX HIGH]` prefix. Per Wave 27 D2, the trigger
is friction-driven, not blocking. Anchor #6 (mutation + selection +
transparency) requires the agent to retain selection authority — a hunger
signal that auto-fires REFLEX HIGH would violate the selection loop.

### 4.9 Landing list (≤ 15 items, all verifiable)

1. Create `src/myco/io_utils.py` with `atomic_write_text` + `atomic_write_yaml`
2. Create `src/myco/compress_cmd.py` with `_resolve_cohort_by_tag` /
   `_resolve_cohort_by_ids` / `_validate_cohort` / `_build_output_body` /
   `_build_output_meta` / `_build_input_update` / `_execute_compression` /
   `run_compress`
3. Add `compress` subparser to `src/myco/cli.py` with all 7 args
4. Add dispatch case `if args.command == "compress": ...` in CLI main
5. Add 6 optional_fields + `compress` to valid_sources + `notes_schema.
   compression` section to `_canon.yaml`; bump `contract_version` and
   `synced_contract_version` v0.25.0 → v0.26.0
6. Mirror all #5 changes to `src/myco/templates/_canon.yaml`
7. Add `forage` and `compress` to `notes.VALID_SOURCES` (notes.py was
   missing `forage` from a prior wave — fix while here); add 6 optional
   field constants to `OPTIONAL_FIELDS`
8. Add `detect_compression_ripe` to `notes.py` and wire into
   `compute_hunger_report` signal list
9. Re-export `detect_compression_ripe` from `metabolism.py` and add to
   its `__all__`
10. Add `lint_compression_integrity` (~130 lines, 3 checks: output
    integrity / input back-link / cascade prevention + orphan detection)
    to `lint.py`; register as L18 in `main()`; update lint module docstring
    "18-Dimension" → "19-Dimension"
11. Re-export `lint_compression_integrity` from `immune.py` and add to
    its `__all__`
12. Create `tests/unit/test_compress.py` with 5 tests (consumptive_with_audit
    / dry_run_no_writes / cascade_rejected / idempotent_empty_cohort /
    lint_compression_integrity_catches_orphan)
13. Append v0.26.0 entry to `docs/contract_changelog.md`
14. `myco hunger` to regenerate `.myco_state/boot_brief.md` (clears the
    L16 MEDIUM that fires after canon edit)
15. `myco eat` Wave 30 evidence + decisions notes; `myco lint` 19/19 PASS
    + `pytest tests/ -q` 9/9 PASS verification before commit; append
    Wave 30 milestone to `log.md`; commit + push as
    `[contract:minor] Wave 30 — myco compress MVP (v0.26.0)`

### 4.10 Known limitations

**L1 — Two-phase commit is best-effort, not transactional**: per R2.1
defense. Torn-state window exists between output write and last input
write. Mitigated by L18 lint, L18 lint pre-commit hook, and `_execute_
compression`'s loud stderr warning on per-input failure with explicit
recovery instructions.

**L2 — `compression_method` is free-form**: per R3.2. A future agent
could write any string. Acceptable because the rationale field is the
truth source; method is metadata. Future wave can elevate to enum
trivially.

**L3 — `io_utils.py` name is provisional**: per R3.3 + D6. Wave 29b
biomimetic sweep evaluates rename.

**L4 — `myco uncompress` verb is still vapor**: Wave 27 D5 deferred to
Wave 29+. Wave 30 preserves the data (`pre_compression_status` field is
written), but no uncompress verb exists. Manual recovery is mechanical
because the data is on disk and the audit chain is intact (and L18-
enforced).

**L5 — Hallucination risk is bounded, not eliminated**: inherited from
Wave 27 L1. Wave 30 ships the bounding mechanisms (L18, cascade rejection,
audit fields, ripe-threshold floor for hunger signal) but cannot eliminate
the residual that an individual compression fabricates. This is the
honest framing of the cognitive primitive.

**L6 — `compression_ripe` is single-tag**: scans `notes/` once and reports
the first tag whose cohort meets the threshold. A repo with multiple
ripe tags surfaces only one signal per hunger run. Acceptable for the
MVP; future wave can multi-signal.

**L7 — Multi-tag input notes have order-dependent aggregation**: when
inputs share some but not all tags, `_build_output_meta`'s aggregated_tags
preserves first-seen order, which means the output's tag list depends
on the cohort's sort order (which is by note id, which is timestamp-then-
random). Deterministic but not semantic. Acceptable.

### 4.11 Provenance + next step

- **Craft authored**: 2026-04-12 by kernel-agent autonomous run
- **Trigger**: Wave 27 D8 + Wave 26 doctrine-dependency-graph ordering
- **Decision class**: kernel_contract
- **Target confidence**: 0.90 (kernel_contract floor)
- **Current confidence**: 0.91 (target met +0.01 from R2.3 — the test
  suite caught a real silent-failure bug in the implementation craft on
  its first run, which is the exact validation Wave 25 was built to
  enable; this is empirical evidence that the bundling decision in D1
  was correct rather than aspirational)
- **Rounds executed**: 3 (per §1, §2, §3) + R2.3 mid-round bug-found
  defense
- **External evidence base**: Wave 27 design craft (parent), Wave 25
  tests infrastructure (validates Wave 30 via pytest), hermes catalog
  C2 (atomic write reference pattern), live first-run pytest output
  (caught R2.3)
- **L13 schema**: compliant
- **L15 reflex arc**: satisfied (kernel_contract surface = `_canon.yaml`
  + lint dimensions list; this craft materializes within the same session
  as those edits; `docs/primordia/` is the canonical home)
- **Next step**: regenerate boot brief, eat evidence + decisions notes,
  append log milestone, commit + push as v0.26.0. Wave 31+ proceed per
  Wave 26 doctrine-dependency-graph ordering.
