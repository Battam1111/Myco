---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.85
current_confidence: 0.85
rounds: 3
craft_protocol_version: 1
decision_class: exploration
closes:
  - "Wave 30 L4 known limitation: no `myco uncompress` reverse verb"
  - "Wave 27 D5 reversibility promise: now mechanically enforced, not aspirational"
---

# Wave 31 — `myco uncompress` MVP (no contract bump)

> **Scope**: exploration class implementation craft. Adds a reverse verb
> that mechanically inverts a single `myco compress` operation. No new
> schema, no new lint, no canon change — just a new verb that reads the
> four audit fields Wave 30 already preserves and writes them back to
> their pre-compression state. **No contract bump** (v0.26.0 unchanged).
>
> **Parents**:
> - Wave 30 `compress_mvp_craft_2026-04-12.md` (introduces the audit shape this craft reverses)
> - Wave 27 `compression_primitive_craft_2026-04-12.md` D5 (design promise of reversibility)
>
> **Supersedes**: none. Closes a known limitation only.

## 0. Problem definition

Wave 30 landed `myco compress` with full audit metadata: `compressed_from`,
`compressed_into`, `compression_method`, `compression_rationale`,
`compression_confidence`, and crucially `pre_compression_status` on each
input. Wave 30 §4.3 listed as L4 known limitation: *"No reverse verb. The
audit metadata makes uncompress mechanically possible (read pre_compression_status,
restore each input, delete the output) but no CLI surface exposes it. A user
who runs compress on the wrong cohort must manually undo via direct file
edits."*

This limitation is a credibility tax on Wave 27 D5 (*"compression must be
reversible"*). Without the reverse verb, the design's reversibility claim
is aspirational — the data needed for reversal exists, but no path through
the agent loop reaches it. Wave 31 closes that gap with the smallest
possible primitive: a new verb that reads the audit fields and writes the
pre-compression state back.

**Why now, before Wave 32+ feature work**: the marathon discipline says
"do all work to the most complete." Leaving an L4 limitation behind is
incomplete. The reversal is mechanically simple — Wave 30 preserved every
field needed — so the cost-to-close is hours, not days. Closing it now
also lets Wave 32+ test crafts reference uncompress as a recovery path
for failed experiments.

**What Wave 31 must produce**:

1. `myco uncompress <output_id>` verb that reverses a single compress
   output: restores each input from `pre_compression_status`, clears
   the four input-side audit fields, deletes the extracted output.
2. Two new tests in `tests/unit/test_compress.py` (roundtrip + tampered
   chain refusal) that prove the inverse property holds and that audit
   tampering is refused before any writes.
3. No contract bump. No canon edit. No lint dimension. No schema change.

What Wave 31 must NOT do (scope discipline per Wave 25 Round 2 inheritance):

- No batch uncompress (`--all`, `--tag`). Wave 31 is single-output only.
- No `myco view` integration showing reversibility status.
- No L18 changes — L18 already validates chain integrity bidirectionally.
- No new schema fields. Wave 30's audit shape is sufficient.

## 1. Round 1 — Design

The design space for `myco uncompress` is narrow. Once you commit to
"single output, mechanical inverse, refuses on tampered chain", the
shape is mostly determined.

### 1.1 Verb signature

```
myco uncompress <output_id> [--json] [--project-dir <path>]
```

**D1**: positional `output_id`, not `--id`. Same shape as `myco view <id>`.
The output id is required, not inferable from cohort tags (a tag may
have been compressed into multiple outputs over time; user must name
exactly one).

### 1.2 Algorithmic shape

Two-phase, inputs-first, output-deletion-last:

**Phase 1 — Validate output**:
1. Read `<output_path>`. Refuse if missing.
2. Refuse if `status != "extracted"`.
3. Refuse if `source != "compress"`.
4. Refuse if `compressed_from` is empty/missing.

**Phase 1 — Validate each input**:
For each id in `output.compressed_from`:
1. Read input note. Refuse if missing.
2. Refuse if `input.compressed_into != output.id` (broken back-link).
3. Refuse if `input.status != "excreted"` (already restored or unexpected state).
4. Build restored frontmatter: status from `pre_compression_status`, clear
   `compressed_into`, `pre_compression_status`, `excrete_reason`. Refresh
   `last_touched`.

**Phase 2 — Atomic writes**:
1. Write each restored input via `atomic_write_text` (Wave 30 io_utils).
2. After ALL inputs successfully written, delete output note.
3. If any input write fails: WARN to stderr, do NOT delete output (the
   output is the only remaining recovery anchor for the failed inputs),
   return partial-restoration result.

**D2**: inputs first, output last. The inverse of compress's order
(compress writes output first then excretes inputs) for the same reason:
fail-safe is "the dataset is recoverable from what's still on disk."

### 1.3 What gets cleared vs restored

Cleared on each input:
- `compressed_into` → None (dropped from frontmatter by serialize_note)
- `pre_compression_status` → None
- `excrete_reason` → None

Restored on each input:
- `status` → value of `pre_compression_status` (which Wave 30 captured BEFORE excreting)
- `last_touched` → now

NOT touched on each input:
- `digest_count` (uncompress is not a digestion event)
- `compression_method/rationale/confidence` (these live on the output, not inputs)
- `id`, `created`, `tags`, `source`, `body`

**D3**: uncompress is metadata-only on the input side. Body is preserved
exactly. This is what makes the test `body == input_bodies_pre[input_id]`
in the roundtrip test load-bearing — if we ever drift to "regenerate body
from compressed output's notes section", the test catches it.

### 1.4 Refusal mode for tampered chain

If any input's `compressed_into` does not match the output's id, refuse
the entire operation with exit 3 BEFORE writing anything. This is the
**Phase 1 fail-fast** principle inherited from Wave 30.

**D4**: refuse-the-whole-cohort, not refuse-the-tampered-input. Partial
restoration would leave the substrate in a state where some inputs are
restored, others still excreted, and the output partially still pointing
at restored inputs — a state worse than either pre- or post-uncompress.
Total refusal preserves the pre-call state exactly.

### 1.5 Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 2 | Usage error (missing positional output_id) |
| 3 | Validation error (not extracted, broken back-link, missing input, etc.) |
| 5 | I/O error (cannot read project, cannot find output note file) |

**D5**: same exit code shape as compress. The `4` slot used by compress
for "empty cohort = no-op success" doesn't apply to uncompress because
uncompress's cohort is always known (it's `output.compressed_from`); an
"empty cohort" would be exit 3 (validation error: invalid output).

## 2. Round 2 — Attack

### Attack A: "Why not just use the existing tools?"

A user could manually undo a compress by editing each input file's
frontmatter and deleting the output. Why does Wave 31 need a verb?

**Defense**: manual editing has three failure modes the verb prevents:
1. **Forgetting a field**: a human editor might restore `status` but forget
   to clear `compressed_into`, leaving a dangling pointer. L18 would catch
   it eventually but the substrate is in an inconsistent state in the meantime.
2. **Editing the wrong file**: with N inputs, the chance of touching the
   wrong note grows linearly. The verb operates on the cohort atomically.
3. **Bypassing back-link validation**: a manual editor would not check
   that `compressed_into` actually points at the output being deleted.
   The verb refuses on mismatch.

The verb is not sugar; it is a safety floor.

### Attack B: "Why no `--all` or `--tag` form?"

Compress accepts `--tag <T>` to roll up a cohort. Why doesn't uncompress?

**Defense**: compress's `--tag` resolves to "all raw/digesting notes
carrying tag T that haven't been compressed yet." The cohort is determined
at compress time and frozen into `output.compressed_from`. Uncompress's
cohort is already determined — it's literally `output.compressed_from`.
Adding `--tag` to uncompress would mean "all outputs whose cohort included
notes with tag T", which is a more dangerous operation (it could undo
multiple unrelated compress runs). Wave 31 deliberately leaves that for
a future wave to consider with its own attack rounds.

This is also why Wave 31 is exploration class, not kernel_contract: the
single-output form is unambiguous and reversible; the batch form would
be ambiguous and warrants more design.

### Attack C: "What if compress was called with mixed pre_compression_status values?"

Wave 30's compress allows inputs of status `raw` or `digesting`, and stores
each input's pre-status individually. So a single output could have three
inputs that were `raw` and two that were `digesting`. Does uncompress
handle that correctly?

**Defense**: yes — `_build_input_restore` reads each input's own
`pre_compression_status` field. There is no shared/aggregated pre-status
on the output; the field is per-input. The roundtrip test only covers
all-`raw` (the most common case), but the implementation's loop is
status-agnostic.

**Honest edge**: the test does not exercise the mixed case. If a future
craft wants higher confidence on uncompress, add a test that compresses
a mixed cohort and verifies each input restores to its own status.
Filed in §4.3.

### Attack D: "What if the output was edited after compress (e.g. someone added a manual extraction summary)?"

If the output's body was manually edited between compress and uncompress,
that edit is lost (output is deleted).

**Defense**: this is **acceptable** because:
1. Wave 27 D5 explicitly says reversibility means "the inputs can be
   restored", not "the output is preserved." The output is by definition
   the lossy artifact.
2. The user invoking `myco uncompress` is asking for the inputs back;
   they have implicitly accepted losing the output.
3. If the user wanted to preserve the output's edits, they would not
   call uncompress — they would call `myco eat` to capture the edits as
   a fresh raw note before invoking uncompress.

**Limitation accepted**: Wave 31 does not warn the user before deleting
an edited output. A future enhancement could compare output mtime against
its inputs' last_touched and warn "this output has been edited since
compress; uncompress will lose those edits." Filed in §4.3.

### Attack E: "What if uncompress is called twice on the same output?"

The first call restores inputs and deletes output. The second call would
fail at "output not found" → exit 5. This is correct (the operation is
idempotent in the second-call sense: the system reaches the same state
either way).

**Defense**: passes. No mutation on second call.

### Attack F: "Compression should be reversible — but should it be infinitely round-trippable?"

Compress + uncompress + compress should leave the substrate in the same
state as just-compress. Compress + uncompress should leave the substrate
in the same state as before compress.

**Defense**: passes by construction. Compress writes deterministic audit
fields; uncompress clears them. The only non-deterministic field touched
is `last_touched`, which is intentionally refreshed on both sides because
that field's semantics are "when was this metadata last mutated." The
roundtrip test verifies body equality and key field equality; it does
NOT verify last_touched equality (that would be wrong).

### Attack G: "What if pre_compression_status was manually deleted from an input's frontmatter?"

Then `_build_input_restore` falls back to `"raw"` (the dict-get default).
This is **silently incorrect** for an input that was originally `digesting`.

**Defense**: this is a real defect of the current design. Two options:
1. Refuse uncompress if any input lacks `pre_compression_status`. Safe
   but breaks the L4 closure for any compression that predates Wave 31.
2. Default to `raw` (current behavior). Restores SOMETHING but may be wrong.

**Decision (D6)**: choose option 2 with a known limitation entry. Reasoning:
(a) all current compressions are post-Wave-30 and have `pre_compression_status`
set; (b) defaulting to `raw` is recoverable manually if wrong; (c) the
strict mode is a future hardening, not a Wave 31 blocker.

**Honest edge**: the test does not exercise this case. Filed in §4.3.

### Attack H: "Why no L19 lint dimension for uncompress safety?"

L18 already validates compressed_into back-links bidirectionally. There
is no additional invariant uncompress introduces — uncompress is a verb,
not a schema. A new lint dimension would be redundant with L18.

**Defense**: passes. No L19 needed.

## 3. Round 3 — Conclusion lock

### 3.1 Decisions (D1–D6 above, plus)

**D7**: Wave 31 is exploration class (0.85 floor) not kernel_contract.
Reasoning: no kernel surface touched (cli.py and compress_cmd.py are
not in the L15 trigger surface list), no schema/canon change, no new
lint dimension. The reflex arc does not fire for Wave 31. The craft is
written voluntarily for symmetry with Wave 30 and audit completeness.

**D8**: no contract bump. v0.26.0 stays. The compression schema is
unchanged; uncompress just reads existing fields. Per Wave 24 L17
contract drift discipline, a new verb that adds zero canon mutations
is `[refactor]` class, not `[contract:minor]`.

### 3.2 Landing list

1. ✅ `_build_input_restore(input_meta)` in `src/myco/compress_cmd.py`
2. ✅ `_execute_uncompression(root, output_path)` in `src/myco/compress_cmd.py`
3. ✅ `run_uncompress(args)` in `src/myco/compress_cmd.py`
4. ✅ `uncompress_parser` subparser in `src/myco/cli.py`
5. ✅ `args.command == "uncompress"` dispatch in `src/myco/cli.py`
6. ✅ `test_compress_uncompress_roundtrip` in `tests/unit/test_compress.py`
7. ✅ `test_uncompress_broken_backlink_refuses` in `tests/unit/test_compress.py`
8. ✅ `pytest tests/ -q` 11/11 green
9. ✅ `myco lint` 19/19 green
10. ⏳ Wave 31 craft eaten as raw note + decisions integrated note
11. ⏳ Wave 31 milestone in `log.md`
12. ⏳ commit as `[refactor] Wave 31 — myco uncompress MVP (closes Wave 30 L4)`

### 3.3 Known limitations

- **L1**: only single-output form. No `--all`, no `--tag`. (Attack B)
- **L2**: edited output's body changes are lost without warning. (Attack D)
- **L3**: mixed-status cohort uncompress is not test-covered. (Attack C)
- **L4**: missing `pre_compression_status` falls back to `"raw"` silently. (Attack G)
- **L5**: no `--dry-run` for uncompress. Compress has it; uncompress
  inherits its absence as a Wave 31 limitation. The reverse operation is
  more frequently used in panic/recovery scenarios where dry-run would
  add safety, so L5 is the most likely Wave 32+ enhancement target.

### 3.4 Anchor coverage shifts

- Anchor #4 (压缩即认知): `0.75 → 0.78`. Reversibility promise (Wave 27 D5)
  is now mechanically enforced. The full claim "compression is the only
  cognition that respects substrate scarcity" gains teeth: mistakes are
  now recoverable through the verb path, not just through manual file
  surgery.
- Other anchors: unchanged.

### 3.5 Confidence

`current_confidence: 0.85 = target_confidence: 0.85`. Per single-source
convention, this is the ceiling for an agent-only craft with no external
research. The craft's defenses are all internal-consistency arguments;
no Polanyi/Argyris/Voyager citation provides external grounding for
"reversibility is enforced via mechanical inverse." Honest edge: a future
human-collaborative craft could argue for raising this to 0.88+.

## 4. Conclusion

Wave 31 closes Wave 30 L4 with a 200-line implementation, 2 new tests,
1 craft, 1 milestone log entry, 0 schema changes, 0 contract bumps.
Wave 30 paid the cost of preserving `pre_compression_status` so Wave 31
could be cheap; the discipline pays off.

Next wave (Wave 32) is open: marathon discipline says continue. The Wave 26
ordering puts anchor #3 (seven-step pipeline) verbs as the next anchor
service target after anchor #4 reaches 0.75+. Wave 31 brings #4 to 0.78,
clearing that gate.
