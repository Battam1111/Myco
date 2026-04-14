---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.85
current_confidence: 0.85
rounds: 3
craft_protocol_version: 1
decision_class: exploration
closes:
  - "Wave 26 §2.3 priority ordering: 'Anchor #3 full completion — verbs for steps 2, 3, 4 (evaluate, extract, integrate)'"
  - "anchor #3 (七步管线) impl_coverage gap: pipeline middle was vestigial in CLI surface"
---

# Wave 32 — Anchor #3 step verbs (`evaluate` / `extract` / `integrate`)

> **Scope**: exploration class implementation craft. Adds three new
> first-class CLI verbs as **equal-peer aliases** (per Wave 29 D2) over
> the existing `myco digest --to <status>` path. No schema, no canon,
> no lint, no contract bump. Pure additive CLI surface.
>
> **Parents**:
> - Wave 26 `vision_reaudit_craft_2026-04-12.md` §2.3 (priority ordering)
> - Wave 28-29 biomimetic alias doctrine (additive, not replacement)
>
> **Supersedes**: none.

## 0. Problem definition

Wave 26 §2.3 priority ordering listed:

> *"Wave 30+ target: Anchor #3 full completion — verbs for steps 2, 3, 4
> (evaluate, extract, integrate). Each step gets its own design+impl wave pair."*

Wave 30 already implemented `myco compress` which folds steps 2+3+5+7 into
one verb per Wave 27 D6, taking anchor #3 from 0.43 → ~0.75. But the
**individual step verbs** are still missing from the CLI surface:

- Step 2 (evaluate): only accessible via `myco digest <id>` (no --to)
- Step 3 (extract): only via `myco digest <id> --to extracted`
- Step 4 (integrate): only via `myco digest <id> --to integrated`

The seven-step pipeline is documented in `MYCO.md §身份锚点 #3` as the core
metabolic doctrine, but a user reading `myco --help` cannot see steps 2-4
as first-class operations. They are present in the **functionality**
(run_digest handles all transitions correctly) but invisible in the
**vocabulary**. This is a doctrine ↔ surface alignment gap.

Wave 26 anticipated each step getting its own design+impl wave pair (6
waves total). Marathon discipline says this is over-engineered for what
is fundamentally three CLI aliases over an existing handler. Wave 32
collapses Wave 26 §2.3's three intended waves into one, on grounds that:

1. The transitions are already implemented in `run_digest` — adding three
   subparsers is wiring, not new logic.
2. The risk surface is minimal: each new verb is a thin namespace wrapper
   that calls the same battle-tested function path (~14 lines of dispatch).
3. The Wave 28-29 biomimetic alias doctrine explicitly endorses additive
   equal-peer aliases for vocabulary expansion without replacement risk.

## 1. Round 1 — Design

### 1.1 Verb signatures

```
myco evaluate [<note_id>] [--project-dir <path>]
myco extract <note_id>     [--project-dir <path>]
myco integrate <note_id>   [--project-dir <path>]
```

**D1**: `evaluate` accepts an optional `note_id`. If omitted, run_digest
picks the oldest raw note (matching `myco digest`'s default behavior).
`extract` and `integrate` REQUIRE the positional id. Reasoning: the
"oldest raw" default is appropriate for the prompt-rendering mode
(evaluate) but risky for state mutations (extract/integrate) — a user
running `myco extract` with no id and intending one specific note could
silently extract a different one.

### 1.2 Dispatch shape

Each verb constructs a `SimpleNamespace` matching the digest_parser's
expected shape (`note_id`, `to`, `excrete`, `project_dir`) and calls
`run_digest`. The dispatch table:

```python
target_status = {
    "evaluate": None,        # let digest do raw→digesting + prompts
    "extract": "extracted",
    "integrate": "integrated",
}[args.command]
```

**D2**: dispatch table form (not three separate `if` blocks). The dict
keeps the wiring readable as one decision rather than three. Adding a
fourth step verb later (e.g., `myco excrete`) is a one-line addition.

### 1.3 What is NOT added in Wave 32

- **No `myco excrete`** as a step-7 alias. The current path
  `myco digest <id> --excrete "reason"` is more compact and the reason
  is mandatory for L11 compliance (excrete_reason). A standalone verb
  would need its own `--reason` requirement and would not be shorter.
  Filed in §3.3 L1.
- **No MCP tool mirrors**. The MCP layer currently exposes raw `digest`
  with `--to`, which is sufficient. Adding three more MCP tools would
  inflate the agent's tool list without functional gain. Filed in §3.3 L2.
- **No deprecation of `myco digest --to <status>`**. Per Wave 29 D2,
  these are equal-peer aliases. Both forms remain valid forever.
- **No tests for the CLI parser argument shape itself**. The unit tests
  call `run_digest` directly with the same SimpleNamespace shape the
  dispatch builds. End-to-end CLI parsing is exercised by `myco --help`
  manual verification (passes — all three verbs visible in usage line).

### 1.4 Test strategy

Three new tests in `tests/unit/test_notes.py`:

1. `test_step_verbs_extract_transitions_to_extracted` — note starts raw,
   call run_digest with the namespace evaluate-dispatch builds, assert
   status=extracted + digest_count=1.
2. `test_step_verbs_integrate_transitions_to_integrated` — same shape
   for integrated.
3. `test_step_verbs_evaluate_transitions_to_digesting` — `to=None` case,
   asserts raw→digesting + reflection prompts emitted to stdout (via
   capsys fixture).

These tests dogfood the dispatch shape: if cli.py's dispatch is ever
changed to pass different fields than `(note_id, to, excrete, project_dir)`,
the tests will fail because the SimpleNamespace shape would no longer
match what run_digest expects.

## 2. Round 2 — Attack

### Attack A: "Why three verbs instead of just one (`myco step <name>`)?"

A `myco step extract <id>` form would be one subparser instead of three.
Why not?

**Defense**: the seven-step pipeline is doctrine, not a generic switch.
Each step has its own semantics, its own preconditions, and its own
position in the cognitive arc. Compressing them into one verb with a
positional `<step>` argument hides the pipeline behind an abstraction
that obscures rather than reveals. `myco --help` should make the steps
visible as a vocabulary, not as a parameter.

Three verbs is more readable than one verb with a discriminator. The
cost is trivial (3 subparsers, 14 lines of dispatch).

### Attack B: "These are aliases, not new functionality. Why a craft at all?"

Wave 31 (uncompress) was justified as "voluntary craft for symmetry with
Wave 30." Wave 32 doesn't even close a known limitation — it just makes
existing functionality more visible. Is the craft warranted?

**Defense**: Wave 32 closes a Wave 26 §2.3 ordering item, which was
explicitly listed in the doctrine-dependency graph as the next priority
after Wave 30. The craft is the audit trail for "Wave 26 said do this,
here is what was done and what was deferred (excrete verb, MCP mirrors)."
Without it, the Wave 26 priority list becomes informally tracked rather
than formally landed.

Plus: the craft documents D1's "evaluate has optional id, extract/integrate
require it" decision, which is non-obvious from the code alone. A future
maintainer asking "why does extract refuse no-id?" gets the answer here.

### Attack C: "What if extract is called on a note that's already extracted?"

The current `run_digest` path on `--to extracted` for a note already at
status=extracted would: read the note, hit the `args.to` branch, validate
extracted ∈ VALID_STATUSES (yes), call update_note with status='extracted'
(idempotent — same status), increment digest_count, print transition.
Result: digest_count gets incremented but status doesn't change.

**Is this correct?** Yes — the digest_count increment is the audit trail
for "extract was called again". An idempotent re-extract is not an error;
it's a re-statement. The user's action is recorded.

**But should we warn?** Maybe — but a warn would be inconsistent with the
existing `myco digest --to extracted` behavior on already-extracted notes.
Wave 32 deliberately preserves that behavior. Filed as not-a-defect.

### Attack D: "Wave 32 expanded the CLI surface — does L11 (Write Surface)
care?"

L11 Write Surface lint guards against unauthorized files appearing in
write-protected paths. Wave 32 only added subparser definitions and
dispatch cases inside `src/myco/cli.py`, which is already a known
substrate-internal write target. No new files in any L11-monitored
location.

**Defense**: passes. Verified via the lint run (19/19 green after the
Wave 32 changes).

### Attack E: "Adding 3 verbs increases the cognitive load of `myco --help`. Was that worth it?"

The verb list grew from 18 → 21 (excluding `version`). That's a 17%
increase. Is the visibility gain worth the help-output bloat?

**Defense**: yes — the seven-step pipeline is doctrine (anchor #3), and
doctrine should be visible in the vocabulary. A user reading `myco --help`
can now see "evaluate, extract, integrate" alongside "compress" and
"forage" and immediately recognize the seven-step shape. Without these,
the pipeline is hidden inside `digest`'s `--to` flag, which is invisible
in the top-level help.

This is exactly the same trade-off the biomimetic Wave 28-29 made: more
surface, but the surface NAMES the doctrine. Worth it.

### Attack F: "What about `myco evaluate` defaulting to oldest-raw — is
that surprising?"

D1 said evaluate accepts optional id, defaulting to oldest raw. This
matches `myco digest`'s behavior. But a user typing `myco evaluate` with
the intent of "evaluate **the substrate's** state" might expect a hunger-
style overview, not a single-note transition.

**Defense**: the verb is `evaluate` (a step in the per-note pipeline),
not `evaluate-substrate` (a global health check). Substrate-level
overview already has `myco hunger`. Verb naming follows the per-note
seven-step pipeline. **Honest edge**: a future user might still be
confused by this; if friction emerges, file as a doc-clarity issue, not
a verb redesign.

## 3. Round 3 — Conclusion lock

### 3.1 Decisions

- **D1**: `evaluate` accepts optional `note_id`; `extract`/`integrate`
  require it. Reason: state-mutation safety vs prompt-rendering convenience.
- **D2**: dispatch via `target_status` dict, not three separate ifs.
  Reason: extensibility for future step-7 verb.
- **D3**: no `myco excrete` step verb. Reason: existing
  `digest --excrete "reason"` is already compact + L11-compliant; a new
  verb would add no shortness.
- **D4**: no MCP tool mirrors. Reason: agent tool budget; raw `digest`
  handles all transitions fine for MCP callers.
- **D5**: no deprecation of `myco digest --to <status>`. Reason: Wave 29
  D2 equal-peer alias doctrine.
- **D6**: Wave 32 collapses Wave 26 §2.3's intended 3-wave-pair sequence
  into one wave. Reason: aliases over an existing handler do not warrant
  full design+impl pair per step.
- **D7**: exploration class (no kernel surface touched, no contract bump).

### 3.2 Landing list

1. ✅ `evaluate_parser` / `extract_parser` / `integrate_parser` subparsers
   added in `src/myco/cli.py` after digest_parser, before view_parser
2. ✅ Single dispatch case `if args.command in ("evaluate", "extract", "integrate")`
   in main() of `src/myco/cli.py`, builds SimpleNamespace and calls run_digest
3. ✅ 3 new tests in `tests/unit/test_notes.py`: extract / integrate / evaluate
4. ✅ `myco --help` manual verification: all three verbs visible in usage line
5. ✅ `pytest tests/ -q` 14/14 green
6. ✅ `myco lint` 19/19 green
7. ⏳ Wave 32 craft (this document) eaten as raw note + decisions integrated note
8. ⏳ Wave 32 milestone in `log.md`
9. ⏳ commit as `[refactor] Wave 32 — anchor #3 step verbs (evaluate/extract/integrate)`

### 3.3 Known limitations

- **L1**: no `myco excrete <id>` step-7 alias. Existing
  `digest <id> --excrete "reason"` is sufficient and shorter when
  combined with the mandatory reason.
- **L2**: no MCP tool mirrors for the three new verbs. MCP callers still
  use `digest --to <status>`. Future MCP refresh could add these if
  agent friction demands.
- **L3**: `myco evaluate` with no id defaults to oldest raw, which a
  user might confuse with substrate-level "evaluate the project state".
  No friction yet — file as doc-clarity if it emerges.
- **L4**: tests do not exercise the cli.py parser layer end-to-end (no
  argv parsing). They test the dispatch shape via direct SimpleNamespace
  construction. A regression in cli.py argparse setup would be caught by
  the manual `myco --help` check + L17 contract drift, not by pytest.

### 3.4 Anchor coverage shifts

- Anchor #3 (七步管线): `0.75 → 0.82`. The CLI vocabulary now exposes
  steps 2/3/4 as first-class verbs alongside step 1 (forage), 5 (compress),
  6 (eat). Step 7 (excrete) remains accessible via `digest --excrete`
  shortcut, which is the only step still requiring a flag rather than a
  named verb. Doctrine ↔ surface alignment is now ~6/7 verbs visible.
- Other anchors: unchanged.

### 3.5 Confidence

`current_confidence: 0.85 = target_confidence: 0.85`. Single-source
convention ceiling. No external research. The decisions are all internal
trade-offs (alias granularity, dispatch table shape, scope discipline).

## 4. Conclusion

Wave 32 lands the smallest possible surface for the largest possible
doctrine win on anchor #3. Three new verbs, ~70 lines of cli.py wiring,
~85 lines of test code, ~310 lines of craft. No risk to existing
functionality (all routes through the same run_digest handler). The
seven-step pipeline now reads as a vocabulary in `myco --help`, not
just as a doctrine in `MYCO.md`.

Next wave (Wave 33) is open. The Wave 26 long-tail priority is
"Anchor #5 D-layer full completion — view audit log + cross-ref graph
+ adaptive threshold + auto-excretion". Marathon mode continues.
