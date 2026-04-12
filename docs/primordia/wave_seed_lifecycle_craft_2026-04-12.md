---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
authors: [yanjun, claude-opus-4-6-1m]
supersedes: []
---

# Wave 41 — L22 Wave-Seed Lifecycle Lint

**Purpose**: Add a new lint dimension `L22 Wave-Seed Lifecycle` that catches
raw notes tagged `wave{N}-seed` where wave N has already landed (its
milestone exists in `log.md`). The lint enforces a structural post-condition
of every wave's seven-step pipeline (anchor #3): a wave-seed evidence bundle
captured during a wave MUST advance out of `raw` status before that wave
is closed. Closes the next-priority silent-rot scar class per Wave 26 D3
friction-driven ordering, identified by the Wave 41 scout when 7 raw
wave-seed notes from Waves 25-32 surfaced as orphaned-yet-hunger-healthy.

## §0 — Problem definition

### 0.1 What fired this wave

The Wave 40 closing doctrine handed Wave 41 a clean slate: "the Wave 37 D7
followup queue is empty, the next-priority scar class is whatever surfaces
in the boot brief / hunger / pytest suite as the next reproducible silent-rot
pattern." The Wave 41 friction scout immediately surfaced one such pattern:

```
$ myco hunger
  total notes: 96
  by_status: raw 10, digesting 2, extracted 13, integrated 66, excreted 5
  Signals: healthy: notes/ is metabolizing normally.

$ myco view --status raw | grep wave
[raw] n_20260412T013044_5546  d=0  forage-digest,...,wave25-seed,...
[raw] n_20260412T024846_91da  d=0  forage-digest,wave26-seed,...
[raw] n_20260412T030350_cace  d=0  forage-digest,wave27-seed,...
[raw] n_20260412T035236_f396  d=0  forage-digest,wave28-seed,...
[raw] n_20260412T060604_94cf  d=0  wave30-seed,compress-mvp,forage-digest
[raw] n_20260412T062305_32c0  d=0  wave31-seed,uncompress-mvp,forage-digest
[raw] n_20260412T063021_49c3  d=0  wave32-seed,step-verbs,anchor3,forage-digest
```

**Seven raw notes** tagged `wave{25,26,27,28,30,31,32}-seed`, all at
`digest_count=0`, all created during their respective waves' execution,
all left untouched ever since. Wave 25 landed on 2026-04-12 (8 hours
before Wave 41's scout). Waves 26-32 followed in the same calendar day.
Each wave eated its seed bundle at the start, used it as evidence input
to the wave's craft, committed the wave, and never returned to advance
the seed through the seven-step pipeline. The crafts exist; the decisions
notes exist; the seed bundles are the **dead matter left behind** by an
incomplete metabolic step.

Yet `myco hunger` reports "healthy: notes/ is metabolizing normally."
Why? Because:

- `raw_backlog` signal threshold = `>10` raw notes (we have exactly 10).
- `stale_raw` signal requires `last_touched` ≥ 7 days ago (the oldest
  is from 2026-04-11, less than 24 hours old at scout time).
- No signal exists for "raw note tagged with a closed wave that should
  have advanced before the wave committed."

This is the exact silent-fail pattern the Wave 20 doctrine ("a sensor
that returns ok when it isn't is worse than a crash") was built to
eliminate. Hunger says healthy. The substrate is leaking 7 raw notes
per the operator's own seven-step convention. Anchor #3 is being
violated by ad-hoc operator practice without any structural enforcement.

### 0.2 The scar class L22 catches

**Wave-seed orphans**: notes whose frontmatter has `status: raw` AND
`tags` contains a string matching `wave\d+-seed`, AND the wave number
parsed out of that tag has a corresponding `**Wave N landed**` milestone
entry in `log.md`. These three conditions identify a note that was
captured *during* a wave, was never advanced past `raw`, and remains
sediment after the wave's closing milestone is committed.

The lint does **not** enforce:
- That every wave MUST create a seed bundle (Waves 38, 39, 40 did not,
  and that is a legitimate efficient practice — see §2 attack F)
- That wave-seed bundles must reach a specific terminal state (extracted
  vs integrated vs excreted are all valid; the lint only requires
  *escape from `raw`*)
- That non-seed raw notes must advance (general raw_backlog is a
  separate signal with its own threshold; L22 narrows to the wave-seed
  scar class)
- That historical (pre-L22) wave-seed orphans must be excreted (the
  Wave 41 healing pass advances the existing 7 to `extracted`, after
  which the lint passes; future waves are subject to the lint
  prospectively)

### 0.3 Why the existing immune system missed it

| Layer | What it catches | Why it missed wave-seed orphans |
|---|---|---|
| L10 Notes Schema | Frontmatter shape, required fields, status enum | Doesn't cross-reference notes against log.md milestones |
| L14 Forage Hygiene | `forage/_index.yaml` integrity | Operates only on `forage/`, not `notes/` |
| Hunger `raw_backlog` | Pure-raw count vs threshold (>10) | Coarse global threshold; misses the wave-tagged subset |
| Hunger `stale_raw` | Raw notes untouched for ≥7 days | Time-window based; new wave-seeds slip under the window |
| Hunger `dead_knowledge` | Terminal notes cold + unviewed | Catches the OPPOSITE end of the pipeline (extracted/integrated, not raw) |
| L13/L15 Craft Reflex | Craft document presence on trigger touches | Catches missing craft, not orphaned raw evidence |

**The gap is precise**: we have *content* sensors (L10 schema, L14
forage) and *quantity* sensors (raw_backlog count, stale_raw age) but
no *referential* sensor that asks "is this raw note from a closed wave
that should have advanced by now?" L22 fills that gap with a
log.md-grounded, tag-grounded check.

### 0.4 What L22 is NOT a substitute for

- **`raw_backlog`** still fires when total raw count exceeds threshold,
  catching general pipeline constipation. L22 is narrower.
- **`stale_raw`** still fires on ANY raw note untouched ≥7 days,
  including non-wave-tagged ones. L22 fires earlier (as soon as the
  wave is logged) for the wave-seed subset.
- **L10 notes schema** still enforces frontmatter shape. L22 assumes
  that schema is already valid and reads tags without re-validating.
- **Manual operator review** still owns the decision of *which*
  terminal state (extracted/integrated/excreted) the seed should advance
  to. L22 only enforces "advance, period."

## §1 — Round 1: First-pass design

### D1 — Identification rule

A note is a **wave-seed orphan** iff ALL of:

1. `note.status == "raw"`
2. `any(re.match(r"wave(\d+)-seed", tag) for tag in note.tags)` is True
3. The captured wave number `N` has a milestone in `log.md` matching
   `(?i)\*\*Wave\s+N\s+landed\*\*` (loose enough to tolerate trailing
   parenthetical context)

When all three hold, L22 emits one HIGH issue per orphan note, naming
the note id, the wave number, and the canonical advancement command
(`myco digest --to extracted <id>`).

### D2 — Detection algorithm

```python
# Pseudocode
1. Read log.md, scan for `**Wave (\d+) landed**`, build set closed_waves.
2. Walk notes/*.md (not subdirectories — Myco notes are flat).
3. For each note, parse frontmatter via the existing read_note() helper.
4. If status != "raw": skip.
5. For each tag matching `wave(\d+)-seed`, extract N as int.
6. If N in closed_waves: emit issue.
7. (Multiple matching tags on one note → emit one issue per orphan note,
   not per tag — first match wins to keep noise bounded.)
```

The algorithm is **read-only**, **idempotent**, and **content-blind**:
it never opens the note body, only the frontmatter. This keeps the
lint fast (~7 file reads on the current substrate) and immune to body-
prose drift.

### D3 — log.md milestone format

The `(?i)\*\*Wave\s+(\d+)\s+landed\*\*` regex matches the canonical
form used by every wave from W1 forward in `log.md`:

```
## [2026-04-12] milestone | **Wave 40 landed (kernel_contract, contract bump v0.30.0 → v0.31.0)** — L21 ...
```

The bold is doctrinal (every milestone uses it) and the "landed"
keyword distinguishes a milestone from references like "Wave 40
followup" or "Wave 40 lessons." Loose alternatives ("Wave N completed",
"Wave N closed") are not in canonical use and are NOT recognized.
A future format change to log.md milestones would need to update this
regex — but L19 / L17 / L13 all share that fragility, and the format
has been stable for 40+ waves.

### D4 — Severity

**HIGH** for every orphan. Rationale:

- The substrate's seven-step pipeline (anchor #3) is being violated
  ad-hoc by operator practice.
- The violation is invisible to hunger's existing signals.
- The fix is single-command (`myco digest --to extracted <id>`) and
  cheap.
- HIGH causes `myco lint` to exit non-zero, blocking commits via the
  existing W23 pre-commit hook (when enabled). This is the right
  pressure level: don't merge if seven-step compliance is broken.

There is no MEDIUM tier for L22 — every orphan is functionally
equivalent in scar shape, and a tier system would over-engineer for
zero benefit.

### D5 — Healing pass for the existing 7 orphans

Wave 41's commit cannot pass `myco lint` until the 7 existing orphans
are advanced. Each must be moved out of `raw`. The default advancement
target is `extracted` because:

- The seed served as input to its wave's craft
- The craft is the *integrated* artifact; the seed is now historical
- `extracted` matches the W32 step verbs' "extracted = wisdom drained,
  source preserved as historical reference"
- `excreted` would be wrong because the seed was actually used (it
  informed the craft); `integrated` would be wrong because the
  *seed itself* is not in active substrate use, only the craft is

The healing path for each orphan:

```
PYTHONPATH=src python -m myco.cli digest --to extracted <id>
```

This single command advances the note from `raw` directly to
`extracted` (skipping `digesting`), increments `digest_count` from 0
to 1, and updates `last_touched`. The wave-seed is then no longer an
orphan (status != raw), the lint passes, and the substrate's
referential count of "extracted" notes goes from 13 to 20. This is
**append-only-equivalent** mutation: the note's body is untouched,
only metadata advances per the standard pipeline contract.

### D6 — Tag pattern strictness

L22 matches `wave\d+-seed` exactly. Variations like `w40-seed`,
`wave40_seed`, `wave-40-seed` are NOT recognized. This is intentional:
the Myco operator convention has used `wave{N}-seed` consistently
across waves 25-37 (per direct grep of the existing notes), and
loosening the pattern would invite stragglers. If a future operator
adopts a different convention, they should either (a) follow
`wave{N}-seed` for L22 compatibility, or (b) propose a craft to
extend L22's pattern set with a new format.

## §2 — Round 2: Attacks

### Attack A — "What if the operator deliberately wants a raw wave-seed?"

**Claim**: Some wave-seeds might be intentionally kept raw as
permanent archived evidence — the operator's choice, not a bug.

**Defense**: The seven-step pipeline (anchor #3) defines `raw` as
*pre-pipeline*. A note in `raw` is by definition "not yet metabolized."
A note that is *deliberately archival* belongs in `extracted` (drained
of active wisdom, kept for reference) or `excreted` (excluded from the
substrate's working set with a documented reason). Neither maps to
`raw`. If the operator wants to assert "this stays raw forever," they
are asserting that the seven-step pipeline has a permanent stuck-state,
which contradicts the doctrine. The right fix is to move the note to
the correct terminal state, not to weaken the lint.

If after Wave 41 a real case emerges where `raw` permanence is
genuinely necessary (which would surprise the author), the future
craft would propose either (a) a new status `archived` distinct from
`extracted`, or (b) a `<!-- l22-skip -->` frontmatter field. Both
would require their own kernel_contract craft. L22 v1 does not
preempt that future.

### Attack B — "What about non-wave-tagged raw notes?"

**Claim**: Why narrow to wave-seeds? The pipeline is being violated
just as much by raw notes that aren't wave-tagged.

**Defense**: Three reasons L22 narrows to wave-tagged orphans:

1. **Scar class is real and bounded**: 7 known orphans, all wave-tagged.
   General raw notes have legitimate use cases (capture queue, in-flight
   evidence, drafts). Wave-seeds have a *specific* failure mode: they
   were captured for a specific landed wave and should have been
   advanced as part of that wave's closing.
2. **Detection is reliable**: Wave-seed → wave milestone is a
   deterministic two-key match. General raw note pressure requires
   thresholds, and thresholds are features, not signals (per Open
   Problems §2).
3. **`raw_backlog` already covers the general case**: hunger's
   existing >10 threshold catches systemic constipation. L22 catches
   a *specific structural pattern* hunger can't see.

A more general "stale raw note" lint is a natural follow-up but
requires additional design (threshold semantics, escape hatches, false-
positive bounds). Wave 41 takes the high-leverage narrow win first.

### Attack C — "log.md regex is fragile"

**Claim**: Hard-coding `**Wave N landed**` couples L22 to a specific
log.md format. If the format changes, L22 silently misses or
silently over-fires.

**Defense**: Three layers of mitigation:

1. **Format has been stable for 40+ waves** (W1-W40). The bold +
   "landed" pattern is doctrinal, not incidental.
2. **L19 catches the inverse failure**: if a wave-seed N has no
   milestone, L22 silently passes — but if the wave actually landed
   and the format changed, L19 wouldn't catch that. The risk is a
   format-change wave that introduces L22 false negatives. The
   cost is one missed orphan, caught at the next manual sweep.
3. **L5 log.md format check** already enforces the milestone shape
   (it checks `## [date] type | text` structure). A breaking format
   change would surface in L5 first, drawing operator attention.

The fragility is real but bounded. If we wanted to eliminate it
entirely, we'd need a structured `log.yaml` companion file, which
would itself become a new SSoT to maintain. Wave 41 is not that wave.

### Attack D — "What if a note is tagged for a wave that hasn't landed yet?"

**Claim**: The agent might pre-tag a note for a wave that's still in
planning. L22 would silently pass (correct), but if the wave is later
abandoned, the orphan stays raw forever and L22 never fires.

**Defense**: Correct — and this is the **intended** behavior. The
post-condition L22 enforces is "if the wave landed, the seed must be
advanced." If the wave never lands, there's no post-condition to
enforce. The orphan can sit for as long as the operator finds useful;
when the wave eventually lands (or is explicitly abandoned via a craft
that excludes it), the next lint pass catches the orphan.

For the "wave abandoned" case, the operator's correct action is to
either (a) re-tag the note with `wave{newN}-seed` if the work
continues under a new wave number, or (b) excrete it via
`myco digest --excrete "abandoned planning artifact"`. Neither requires
L22 changes.

### Attack E — "Healing 7 notes is mass mutation. Append-only?"

**Claim**: The Myco hard contract says notes are append-only. Bulk
advancing 7 notes via `myco digest` mutates each one's frontmatter.
Is this a contract violation?

**Defense**: No — the append-only contract (Hard Contract #2) covers
**body content** of `log.md`, `docs/contract_changelog.md`,
`docs/primordia/*.md`, `notes/*.md`, and `examples/ascc/*`. Frontmatter
fields like `status`, `digest_count`, `last_touched` are explicitly
designed to advance via the lifecycle verbs (`evaluate`, `extract`,
`integrate`, `digest --to`). Each mutation is a recorded transition
in the seven-step pipeline. The body of each note is untouched. This
is the same advancement that operators perform single-shot every day
via `myco extract`; we're doing 7 in a row, not changing the contract.

The Wave 41 commit message will explicitly cite each healed note id
in the body so the audit trail is git-grepable.

### Attack F — "Waves 38-40 didn't make seed bundles. Are they violating L22?"

**Claim**: If L22 enforces wave-seed promotion, what about waves that
don't create a seed bundle at all?

**Defense**: L22 enforces a **conditional** post-condition: *IF* a
wave creates a seed bundle, *THEN* the bundle must advance before the
wave closes. It does NOT enforce that every wave must create a seed
bundle. Waves 38, 39, 40 went directly from scout → craft → decisions
note (integrated) without a separate raw evidence bundle, and that is
a legitimate efficiency. L22 has nothing to say about them — no raw
wave-seed exists, so the trigger condition is empty, so no issue is
emitted.

This is the right doctrinal shape. The choice of "do I need a separate
seed bundle for this wave" is a per-wave operator judgment call (deep
research warrants a seed; fast iteration may not). L22 only governs
the case where the operator has *already chosen* to create a seed and
must follow through.

## §3 — Round 3: Edge cases and final shape

### C1 — Multiple wave tags on one note

A note tagged with both `wave25-seed` and `wave26-seed` (e.g., a
forage bundle that spanned two waves) is checked against both wave
numbers. If either wave is closed, the note is an orphan. The issue
is emitted once per orphan (not once per tag) to keep noise bounded.
The issue message names the *first* matching closed wave.

### C2 — Note with `wave-seed` (no number)

The regex requires `wave\d+-seed` — at least one digit. A note tagged
just `wave-seed` is not matched and is silently ignored. This is
intentional: ambiguous tags don't imply a specific wave to check
against. If operators want such tags to be lint-active, they should
use the standard `wave{N}-seed` form.

### C3 — Note with non-integer wave tag

A note tagged `waveX-seed` or `wave-pre-seed` is not matched (regex
fails). Silent skip. Same rationale as C2.

### C4 — Wave milestone with trailing context

The log.md milestones look like `**Wave 40 landed (kernel_contract,
contract bump v0.30.0 → v0.31.0)**`. The regex `**Wave\s+(\d+)\s+landed\*\*`
matches the prefix but the full milestone includes parenthetical
context after `landed`. We need the regex to allow either `landed**` or
`landed ...**`, so the actual implementation uses
`\*\*Wave\s+(\d+)\s+landed[^*]*\*\*`. Tested against the existing 40
milestones in log.md.

### C5 — Notes outside notes/

L22 only walks `notes/*.md` (top-level glob, no recursion). The Myco
substrate keeps notes flat. If a future wave introduces nested notes
(e.g., `notes/archived/`), L22 would need to be extended. Out of scope
for v1.

### C6 — `_isolate_myco_project` tests

The conftest fixture provides an empty `notes/` and an empty `log.md`.
Tests must populate both before exercising L22. The L22 unit tests
(D8) all do exactly this.

### C7 — Performance

7 notes today, 96 total in the substrate. L22 reads each note's
frontmatter once + reads log.md once. O(N) on note count + O(M) on
log.md size. Both are tiny. No caching needed.

### C8 — Empty log.md

If `log.md` is missing or empty (greenfield project), `closed_waves`
is empty, no orphans are emitted, lint passes. This is the correct
behavior — a project with no waves has no seven-step violations to
catch.

## §4 — Conclusion

### §4.1 Decisions D1-D9

- **D1 Identification rule** — A wave-seed orphan is a `notes/*.md`
  with `status == "raw"` AND a tag matching `wave(\d+)-seed` AND
  the parsed wave number has a `**Wave N landed**` milestone in
  `log.md`. All three conditions required.
- **D2 Detection algorithm** — Walk `notes/*.md`, parse frontmatter,
  filter by status + tag regex, cross-check log.md `closed_waves`
  set. Read-only, idempotent, ~10 ms on current substrate.
- **D3 log.md milestone format** — Regex
  `(?i)\*\*Wave\s+(\d+)\s+landed[^*]*\*\*` (case-insensitive, allows
  trailing parenthetical context before the closing `**`). Stable
  across 40+ waves.
- **D4 Severity** — HIGH for every orphan. No tier system. Blocks
  `myco lint` exit code.
- **D5 Healing pass** — Each existing orphan advances to `extracted`
  via `myco digest --to extracted <id>`. The default terminal target
  is `extracted` (drained-of-wisdom historical reference); operator
  may override per-note via `--to integrated` or `--excrete <reason>`.
- **D6 Tag pattern strictness** — Exact regex `wave\d+-seed`. No
  loose variations.
- **D7 Trigger surface scope** — `notes/*.md` (top-level glob, no
  recursion). Consistent with current substrate flatness.
- **D8 Test coverage** — 4 unit tests in
  `tests/unit/test_lint_wave_seed_orphan.py`: clean substrate,
  orphan caught HIGH, current-wave-not-yet-landed silent pass, no-tag
  raw note silent pass. Suite count 34 → 38.
- **D9 Doctrine reference** — L22 enforces a structural post-condition
  of MYCO.md §身份锚点 #3 (代谢七步流水线). The lint citation is
  Wave 41's craft (this document); the doctrine citation is anchor #3
  itself. No new MYCO.md edit is required because L22 enforces an
  existing anchor, not a new one.

### §4.2 Landing list (15 items)

1. Add `lint_wave_seed_orphan` + `_L22_*` constants + `_l22_parse_closed_waves`
   helper in `src/myco/lint.py` (~120 lines total)
2. `lint.py` header `22-Dimension` → `23-Dimension` + dimension table row
   L22 added + FULL_CHECKS comment `L0-L21` → `L0-L22`
3. `src/myco/immune.py` docstring 22→23 + L0-L21→L0-L22 + L22 bullet +
   add `lint_wave_seed_orphan` to imports + `__all__`
4. `_canon.yaml` `contract_version` v0.31.0 → v0.32.0 + `synced_contract_version`
   mirror
5. `src/myco/templates/_canon.yaml` `synced_contract_version` v0.31.0 → v0.32.0
6. 15+ narrative surfaces bumped 22→23 (README ×3, MYCO.md ×4 lines,
   CONTRIBUTING, wiki/README, docs/reusable_system_design, src/myco/cli,
   init_cmd, migrate, mcp_server ×4, scripts/myco_init, myco_migrate)
7. 4 stale inline contract version claims updated to v0.32.0 (MYCO.md ×3,
   adapters/README ×1) — these are the same surfaces L21 enforces, so
   the bump is mechanical via Wave 40's L21 dogfood
8. **Heal pass**: 7 existing wave-seed orphans advanced via
   `myco digest --to extracted <id>`:
   - n_20260412T013044_5546 (wave25-seed)
   - n_20260412T024846_91da (wave26-seed)
   - n_20260412T030350_cace (wave27-seed)
   - n_20260412T035236_f396 (wave28-seed)
   - n_20260412T060604_94cf (wave30-seed)
   - n_20260412T062305_32c0 (wave31-seed)
   - n_20260412T063021_49c3 (wave32-seed)
9. `tests/unit/test_lint_wave_seed_orphan.py` 4 tests added (suite 34 → 38)
10. `docs/contract_changelog.md` v0.32.0 entry (~200 lines, 9 numbered changes)
11. `docs/primordia/wave_seed_lifecycle_craft_2026-04-12.md` (this document)
12. `log.md` Wave 41 milestone single-paragraph 5-point format
13. `myco lint` 23/23 PASS
14. `pytest tests/ -q` 38/38 PASS
15. `myco hunger` healthy (raw 10 → 3, extracted 13 → 20 after heal)

### §4.3 Limitations (honest)

- **L1**: Tag pattern is exact `wave\d+-seed`. Variations not caught.
  Future tag-format drift requires craft.
- **L2**: log.md milestone format is regex-coupled. Format change
  silently breaks L22 detection. Mitigated by L5's coverage of log.md
  format.
- **L3**: Only catches the *raw* end of the orphan pattern. A
  wave-seed stuck in `digesting` (advanced once, then forgotten) is
  not caught — L22 trusts that `digesting` already implies operator
  intent to continue. Future "digesting orphan" lint would be a
  separate dimension.
- **L4**: The healing target (`extracted`) is operator-chosen by
  doctrine. If the operator decides individually that a specific seed
  belongs in `integrated` or `excreted`, they must override
  per-note. The Wave 41 healing pass uses `extracted` for all 7
  uniformly because that is the doctrinally-correct default for
  seed-bundle-after-craft-landing.

### §4.4 Wave 42+ disposition

Wave 41 closes the wave-seed orphan scar class. The next priority per
Wave 26 D3 friction-driven ordering is whatever surfaces in the next
boot brief / hunger / pytest sweep. Candidate watchlist seeded by the
Wave 41 scout:

- **Open Problem #2** Metabolic Inlet trigger signals — `inlet_ripe`
  hunger advisory remains undesigned
- **Open Problem #4** Continuous compression — `myco compress` exists
  but no automatic trigger
- **Open Problem #5** Self-Model C structural decay metric — no proxy
  metric defined
- **Open Problem #6** Self-Model D layer view audit log — Wave 18 seed
  exists, full implementation pending
- **Process gap** Waves 38-40 skipped seed bundle creation entirely.
  L22 doesn't enforce seed creation, so this is a *practice drift*
  not a *lint scar*. Whether to formalize "every wave must seed" is
  itself a future craft target.

Wave 42 will rescout against the post-Wave-41 substrate.

### §4.5 Supersession pointer

This craft does NOT supersede prior crafts. It extends the lint
dimension lineage:
- Wave 24 (L17 contract drift)
- Wave 38 (L19 dimension count)
- Wave 39 (L20 translation mirror)
- Wave 40 (L21 contract version inline)
- **Wave 41 (L22 wave-seed lifecycle)** ← this craft

Each is orthogonal: L17/L21 cover version-related drift, L19 covers
count drift, L20 covers locale skeleton drift, L22 covers seven-step
pipeline post-condition drift. Together they form a 5-dimension
silent-rot fence around the substrate's most fragile referential
surfaces.
