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
  - "Wave 26 §2.3 long-tail priority: 'D-layer full completion — view audit log + cross-ref graph + adaptive threshold + auto-excretion' (auto-excretion piece only)"
  - "Wave 18 dead_knowledge_seed_craft_2026-04-11 §3.4 future work: 'wire dead-knowledge signal to an auto-excretion verb'"
---

# Wave 33 — `myco prune` (D-layer auto-excretion)

> **Scope**: exploration class implementation craft. Closes the
> dead_knowledge hunger-signal loop with one new verb. Lands ONLY the
> auto-excretion piece of Wave 26 §2.3's 4-item D-layer completion list.
> The other 3 pieces (view audit log, cross-ref graph, adaptive threshold
> auto-tuning) are filed as Wave 33 known limitations and deferred to
> future waves.
>
> **Parents**:
> - Wave 18 `dead_knowledge_seed_craft_2026-04-11.md` (introduces the
>   detection logic Wave 33 wires to a verb)
> - Wave 26 `vision_reaudit_craft_2026-04-12.md` §2.3 (priority ordering)
>
> **Supersedes**: none.

## 0. Problem definition

Wave 18 (v0.18.0) seeded the D-layer with `view_count` + `last_viewed_at`
fields and a `dead_knowledge` hunger signal that flags terminal-status
notes that have gone cold and unread. But the loop was never closed:
the signal told the user "you have 5 dead-knowledge candidates", and the
user had to manually run `myco digest <id> --excrete "..."` for each.
This is a Goodhart-class friction — the signal exists, the data is
correct, but the action it implies is too tedious to perform routinely.
Result: dead-knowledge accumulates, the signal becomes background noise,
and the substrate's "compression doctrine" (anchor #4) is observably
violated by the substrate's own state.

Wave 26 §2.3 listed D-layer completion as long-tail priority with 4
intended pieces:

1. View audit log (per-event log of view events, not just count + last)
2. Cross-ref graph (which notes reference which other notes)
3. Adaptive threshold (dead_knowledge_threshold_days adapts to substrate size/age)
4. Auto-excretion (close the loop — turn the signal into action)

In marathon mode, **auto-excretion is the highest-leverage piece** because:

- It is the smallest in implementation surface (~150 LOC including tests).
- It produces an observable substrate-health change on every invocation
  (dead notes become excreted; signal noise drops).
- The other 3 pieces are independently useful but do NOT change substrate
  state — they are sensors, not actuators.
- Wave 31's principle ("close known limitations before adding new ones")
  applies: the dead_knowledge signal IS a known limitation in service form
  (it's a dead-end signal — points at a problem, doesn't solve it).

What Wave 33 produces:

1. `find_dead_knowledge_notes(root)` in `src/myco/notes.py` — read-only
   scanner that mirrors `compute_hunger_report`'s 5 conditions and returns
   a list of `(path, meta, criteria_dict)` tuples.
2. `auto_excrete_dead_knowledge(root, dry_run=True)` — the mutation half
   that calls the scanner, builds a machine-parseable `excrete_reason`
   per candidate, and applies via `update_note`.
3. `myco prune` CLI verb that exposes this with `--dry-run` (default,
   safe) / `--apply` (opt-in mutation) / `--threshold-days` (override
   canon default) / `--json`.
4. 3 new tests in `tests/unit/test_notes.py` covering the load-bearing
   safety properties.

What Wave 33 does NOT produce (deferred):

- View audit log → Wave 34+ if it ever gets prioritized.
- Cross-ref graph → Wave 34+ (probably needs body-text parsing infrastructure).
- Adaptive threshold auto-tuning → Wave 34+ (requires friction data
  about what the right threshold is).
- No `myco unprune` reverse verb. The excrete_reason is machine-parseable
  so a future Wave 34+ could implement reversal mechanically, but Wave 33
  does not commit to reversal because: (a) excretion is a cheap mutation
  (status flip) and undoable manually; (b) Wave 31's uncompress proved
  the design pattern, so the future cost is low.

## 1. Round 1 — Design

### 1.1 Verb signature

```
myco prune [--apply] [--threshold-days N] [--json] [--project-dir <path>]
```

**D1**: defaults to `--dry-run` (no flag means dry-run). `--apply` is the
opt-in mutation flag. This is the **inverse asymmetry** from
`myco compress`, which defaults to apply and requires `--dry-run` to
preview. The asymmetry is intentional:

| Verb         | Default behavior | Opt-in flag |
|--------------|------------------|-------------|
| `compress`   | apply (mutates)  | `--dry-run` |
| `prune`      | dry-run (safe)   | `--apply`   |
| `uncompress` | apply (mutates)  | n/a         |

**Why**: compress is **additive** (creates 1 new note from N inputs,
inputs are recoverable via uncompress), so dry-run is informative not
load-bearing. Prune is **destructive** (mutates terminal-status notes
to excreted, no built-in reversal in Wave 33), so dry-run is the only
safe default. A user who types `myco prune` and accidentally mutates 50
notes has a worse outcome than a user who types `myco compress --tag X`
and accidentally compresses cohort X (which they can uncompress).

The inverse defaults are NOT a UX inconsistency — they are a safety
hierarchy. Destructive defaults to safe; additive defaults to working.
This matches the broader CLI ecosystem (`rm` requires `-r` for recursive,
`mv` doesn't ask before clobber, `git rm` requires explicit args).

### 1.2 Algorithmic shape

Two functions, one verb:

**`find_dead_knowledge_notes(root, threshold_days=None, now=None)`**:
- Read-only, no mutation capability.
- Loads `_canon.yaml::system.notes_schema.dead_knowledge_threshold_days`
  for default.
- Mirrors `compute_hunger_report`'s 5-condition logic exactly:
  1. status ∈ terminal_statuses
  2. now - created ≥ threshold (grace period)
  3. now - last_touched ≥ threshold
  4. last_viewed_at is None OR now - last_viewed_at ≥ threshold
  5. view_count < 2
- Returns `List[(path, meta, criteria_dict)]` where criteria_dict
  carries the actual measured ages so the caller can build audit reasons.

**D2**: scanner is split from mutation. The split is what makes
`find_dead_knowledge_notes` reusable by future wave's `view audit log`
or `cross-ref graph` features without dragging in mutation responsibility.
It also makes the dry-run path mechanically certain not to mutate
(the function literally has no write capability).

**`auto_excrete_dead_knowledge(root, threshold_days, dry_run, now)`**:
- Calls `find_dead_knowledge_notes` to get candidates.
- For each candidate, builds an `excrete_reason` of the form:
  ```
  auto-prune: cold terminal note (created Nd ago, last_touched Nd ago,
  {never_viewed | last_viewed Nd ago}, view_count=K, threshold=Td)
  ```
- If `dry_run`: returns result list with `applied=False` per item.
- If `not dry_run`: calls `update_note(path, status='excreted', excrete_reason=reason)`
  per item, marks `applied=True` on success or `error=str(exc)` on failure.
- Per-note failures do NOT abort the loop — each excretion is independent
  (Wave 30 lesson: per-input atomicity is appropriate when there is no
  cross-note invariant).

**D3**: per-note independent excretion. No two-phase commit because there
is no cross-note invariant — each dead note is independently dead. This
is different from compress (where the inputs and output are linked by
audit chain) and uncompress (where the chain must be unwound atomically).

### 1.3 The audit reason as a machine-parseable record

Sample reason:
```
auto-prune: cold terminal note (created 35d ago, last_touched 35d ago, never_viewed, view_count=0, threshold=30d)
```

**D4**: the format is mechanical and parseable. A future `myco unprune`
(Wave 34+) could regex-extract the threshold and criteria values, restore
the note's prior status, and verify the original conditions still hold
before uncompromising. This is the same pattern Wave 30 used with
`pre_compression_status` — preserve enough information at mutation time
that the inverse is possible.

For Wave 33, the field is informational; for Wave 34+, it's actionable.

### 1.4 Default = dry-run rationale (deeper)

Why is `myco prune` dry-run by default but `myco compress` apply by default?

The answer comes from the **frequency of catastrophic mistake** for each verb:

- `myco compress` mistakes: a wrong cohort gets synthesized into one note.
  Recovery: `myco uncompress <output_id>` (Wave 31). Cost of mistake:
  one stale extracted note plus the cohort gets temporarily marked excreted
  during the wrong compress. Reversal time: seconds.
- `myco prune` mistakes: dead notes get excreted that the user didn't
  want excreted (e.g., a note the user planned to view "soon" but hadn't
  yet). Recovery: manually edit each excreted note's status back. Wave 33
  has no built-in reversal verb. Cost of mistake: N notes need manual
  status restoration. Reversal time: minutes per note.

The asymmetry in recovery cost justifies the asymmetry in default safety.

## 2. Round 2 — Attack

### Attack A: "Dead-knowledge detection has 5 conditions; auto-excretion respects all 5. But what if a condition is wrong?"

The 5 conditions were locked in Wave 18 (v0.18.0) as a seed. They could
be wrong in either direction:

- **Too strict** (false negatives): a note IS dead but doesn't get flagged.
  Result: signal noise underreports the problem. No mutation harm.
- **Too loose** (false positives): a note ISN'T really dead but gets flagged.
  Result: auto-prune would excrete a useful note.

**Defense**: the 5 conditions favor false negatives over false positives:
- Grace period (condition #2) means a fresh note must be aged before it
  can be flagged at all.
- View count threshold (#5: `< 2`) means a note must be viewed 0 OR 1
  times to be dead — 2 views is a clear "user noticed this" signal.
- Last-touched (#3) means any edit, digest, or even an `update_note`
  call resets the death clock.

For Wave 33 to false-positive, all 5 must align in the wrong direction
on a note the user actually values. If the user values the note enough
to keep it, they'll have viewed it ≥2 times OR touched it OR it'll be
fresher than 30 days. The condition stack is robust by construction.

**Honest edge**: the 30-day threshold is a fixed seed. It might be too
short for certain projects (e.g., a substrate where some notes are
referenced quarterly). The `--threshold-days` flag provides per-call
override, but no auto-tuning. Filed as Wave 33 L3.

### Attack B: "Why not give the user a confirmation prompt instead of dry-run/apply asymmetry?"

A `myco prune` could prompt the user "About to excrete N notes. Continue?
[y/N]" — same safety, less verbose UX (one command instead of two).

**Defense**: this craft is part of an autonomous cognitive substrate
designed to be invoked by both humans and agents. Agent invocation cannot
respond to interactive prompts. The dry-run/apply pattern is explicitly
agent-friendly: an agent runs `myco prune` to see what would happen, then
runs `myco prune --apply` if the dry-run output passes its own evaluation.
A confirmation prompt would force agents to either fake stdin or always
use `--no-confirm`-style flags, defeating the safety.

For human users, the dry-run pattern is also LESS friction-prone than
confirmation: a human running `myco prune` sees what's coming, can copy
the command into their shell history, edit the threshold if needed, then
run `myco prune --apply`. The two-command flow is auditable (both
invocations show up in shell history). A confirmation prompt is one
command but the decision is invisible to history.

### Attack C: "What if the canon dead_knowledge_threshold_days is misconfigured to 0 or 1?"

If the canon has `dead_knowledge_threshold_days: 0`, every terminal-status
note becomes immediately dead. `myco prune` would propose to excrete
every extracted/integrated note in the substrate. Catastrophe.

**Defense**: dry-run default. The user sees the catastrophic output
("found 60 candidates"), realizes the misconfiguration, fixes the canon,
re-runs prune. No mutation occurs.

**Honest edge**: there is no minimum sanity floor on `--threshold-days`
(e.g., refuse if threshold < 7). Should there be? Probably yes — a
threshold of 0 is almost never sensible. Filed as Wave 33 L4 (sanity
floor is a nice-to-have, not a Wave 33 blocker since dry-run already
prevents the catastrophe).

### Attack D: "Per-note error tolerance — but what if every note fails?"

The function logs per-note failures with `error=str(exc)` but does not
abort the loop. If 100 dead notes are detected and all 100 fail to
update (e.g., disk full), the result list has 100 failed entries and
the user has to scroll through them.

**Defense**: this is correct behavior. Aborting at the first failure
would be inconsistent — failure modes are usually permanent (disk full,
permission denied) so subsequent notes will also fail, but the user gets
the COMPLETE picture by running through all of them. The output clearly
shows N=100 failures, making the systemic problem obvious.

### Attack E: "Why scan twice (find then update)? Why not do it in one pass?"

The split between `find_dead_knowledge_notes` and `auto_excrete_dead_knowledge`
means each note is read twice in the apply path: once to check criteria,
once to update. For 1000 notes this is 2000 reads instead of 1000.

**Defense**: the split is the dry-run safety guarantee. If the functions
were merged, the dry-run path would have to take a "boolean dry_run flag"
and the function signature would need to make a runtime decision for
each note. The split makes dry-run mechanically incapable of writing —
the find function literally has no write capability. The 2x read cost
on a 1000-note substrate is microseconds; the safety guarantee is
permanent. Worth it.

### Attack F: "What about thread safety / concurrent prune calls?"

If two prune calls run concurrently, they could both find the same
candidate, both call update_note, and the second one might race with
the first.

**Defense**: notes are individual files; update_note uses path.write_text
which is atomic-ish at the OS level. The race is benign — both attempts
write the same content (same excrete_reason for the same note's same
state), the later one wins. If they write different reasons (e.g.,
different threshold values from different invocations), the later one
wins, which is correct: the most recent call's intent takes precedence.

For stronger guarantees, a future wave could add file locking. Wave 33
does not need to.

## 3. Round 3 — Conclusion lock

### 3.1 Decisions

- **D1**: dry-run is the default; `--apply` is opt-in. Inverse from
  compress because destructive verbs need safety defaults.
- **D2**: scanner (`find_dead_knowledge_notes`) is split from mutation
  (`auto_excrete_dead_knowledge`) so dry-run is mechanically write-incapable.
- **D3**: per-note independent excretion; no two-phase commit because
  there is no cross-note invariant.
- **D4**: excrete_reason is machine-parseable so a future `myco unprune`
  can regex-extract criteria and reverse mechanically.
- **D5**: no confirmation prompt; agent-friendly dry-run/apply pattern.
- **D6**: only auto-excretion piece of Wave 26 §2.3's 4-item D-layer
  completion lands in Wave 33. Other 3 pieces deferred.
- **D7**: exploration class. No kernel surface touched (notes.py and
  notes_cmd.py and cli.py are not in L15 trigger list). No contract bump.
  No new lint dimension.

### 3.2 Landing list

1. ✅ `find_dead_knowledge_notes(root)` in `src/myco/notes.py`
2. ✅ `auto_excrete_dead_knowledge(root, dry_run, threshold_days)` in `src/myco/notes.py`
3. ✅ `auto_excrete_dead_knowledge` re-exported via existing `from myco.notes import` block in `src/myco/notes_cmd.py`
4. ✅ `run_prune(args)` in `src/myco/notes_cmd.py`
5. ✅ `prune_parser` subparser in `src/myco/cli.py`
6. ✅ `args.command == "prune"` dispatch in `src/myco/cli.py`
7. ✅ 3 new tests in `tests/unit/test_notes.py`: dry-run-no-mutation /
   apply-excretes / grace-period-respected
8. ✅ `pytest tests/ -q` 17/17 green
9. ✅ `myco lint` 19/19 green
10. ✅ End-to-end dogfood: `myco prune` on live substrate returns
    "Substrate is clean" (no false positives on healthy substrate)
11. ⏳ Wave 33 craft eaten as raw note + decisions integrated note
12. ⏳ Wave 33 milestone in `log.md`
13. ⏳ commit as `[refactor] Wave 33 — myco prune (D-layer auto-excretion)`

### 3.3 Known limitations

- **L1**: no view audit log (per-event log of view events). Wave 26
  §2.3 listed this as part of D-layer completion. Wave 33 does not land
  it because the `view_count` + `last_viewed_at` fields are sufficient
  for prune's purposes; an audit log would be a separate feature.
- **L2**: no cross-ref graph (which notes reference which other notes).
  Wave 26 §2.3 listed this. Wave 33 does not land it because it would
  require body-text parsing infrastructure that no current verb depends on.
- **L3**: no auto-tuning of `dead_knowledge_threshold_days`. The
  threshold is canon-fixed (default 30) with per-call override via
  `--threshold-days`. Auto-tuning needs friction data about which
  threshold values produce too many false positives in real use.
- **L4**: no sanity floor on `--threshold-days` (e.g., refuse if `< 7`).
  Dry-run default already prevents the catastrophe of a 0-day threshold,
  but a sanity floor would be nice as defense-in-depth.
- **L5**: no `myco unprune` reverse verb. The excrete_reason is
  machine-parseable so reversal is mechanically possible (Wave 31 pattern),
  but Wave 33 does not commit to reversal. If an agent or user
  systematically over-prunes, manual restoration is the recourse.
- **L6**: per-note error tolerance produces verbose output on systemic
  failures. A user with 100 dead notes and disk full sees 100 failed
  entries. A future enhancement could detect "all failures share root
  cause" and collapse to one summary line.

### 3.4 Anchor coverage shifts

- Anchor #5 (四层自模型): `0.78 → 0.85`. The D-layer was the
  largest underserved layer in Wave 18's seed. Wave 33 closes the
  signal-to-action loop for the most common D-layer event (cold terminal
  note → excretion). The other 3 D-layer pieces remain unimplemented but
  are now clearly framed as "additional sensors" rather than "missing
  loop closure."
- Anchor #4 (压缩即认知): `0.78 → 0.79` (small bump). Auto-excretion
  is a form of compression — it removes notes that no longer earn their
  storage. The substrate's "attention finite" doctrine gains a self-acting
  enforcement mechanism, not just a hunger-signal advisory.
- Other anchors: unchanged.

### 3.5 Confidence

`current_confidence: 0.85 = target_confidence: 0.85`. Single-source
ceiling for an agent-only craft. The decisions are all internal-consistency
arguments grounded in Wave 18's existing detection logic + Wave 30/31's
established CLI safety patterns. No external research.

## 4. Conclusion

Wave 33 closes the dead_knowledge signal-to-action loop with one new verb,
2 new functions, 3 new tests, ~150 LOC + ~280 LOC craft. No risk to
existing functionality (all routes through battle-tested update_note).
The dead_knowledge hunger signal becomes actionable for the first time
since Wave 18 introduced it.

Marathon mode continues. Wave 34 is open. Most natural next move per
Wave 26 §2.3 long-tail: either (a) continue D-layer with view audit log,
OR (b) shift to anchor #6 selection-loop hardening, OR (c) tackle the
held-open Metabolic Inlet design problem. Wave 26's priority ranking
points at Metabolic Inlet as the long-deferred structural blind spot.
