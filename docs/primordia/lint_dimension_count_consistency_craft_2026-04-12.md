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

# Wave 38 — L19 Lint Dimension Count Consistency

**Purpose**: Add a new lint dimension `L19 Lint Dimension Count Consistency`
that scans living narrative surfaces for hardcoded `LINT_DIMENSION_COUNT`
claims and fails when they drift from the canonical truth `len(FULL_CHECKS)`
in `src/myco/lint.py`. Closes Wave 37 D7 candidate #1, the highest-leverage
Wave 38 candidate per Wave 26 D3 friction-driven ordering. The substrate
silently rotted for ~7 waves between Wave 30 (when L18 landed) and Wave 37
(when the manual sweep caught it). L19 makes that class of rot structurally
impossible: any future wave that adds a lint dimension and forgets to bump
downstream caches will trip L19 at the next lint run.

## §0 — Problem definition

### 0.1 What fired this wave

Wave 37 D7 candidate ranking placed `LINT_DIMENSION_COUNT-from-ground-truth
lint` at #1, ahead of translation-mirror lint (#2) and contract-version-
inline lint (#3), because:

1. **Highest historical leverage**: had it existed at Wave 30 (when L18
   landed), it would have made Wave 37's entire 15-surface manual sweep
   unnecessary. The 7-wave drift was a silent, expensive failure mode.
2. **Lowest implementation cost**: a single new lint function (~120 LOC)
   with a regex sweep over a known surface list. No new schema, no new
   verb, no new infrastructure.
3. **Self-reinforcing discipline**: L19 turns Wave 37 D1 ("SSoT is
   `len(checks)`, every other surface is a downstream cache") from a
   prose convention into a structural enforcement.
4. **Smallest blast radius**: pure narrative-surface check. False positives
   are fixable by either (a) bumping the surface or (b) adjusting L19's
   pattern set if the false positive is structural.

### 0.2 Friction quote (Wave 37 D1)

> **D1 — Single source of truth for LINT_DIMENSION_COUNT is `len(lint.py::checks)`**
> Whenever a new lint dimension lands, the contract bump craft MUST include
> a "label sync" landing item that scans these surfaces and bumps them all
> in the same wave. No exceptions. (Wave 38+ candidate: a
> LINT_DIMENSION_COUNT-from-ground-truth lint that auto-fails when these
> surfaces drift — see §4.4 of Wave 37 craft.)

Wave 38 turns the parenthetical into a binding lint.

### 0.3 What this craft commits to

- **Deliverable**: a new lint function `lint_dimension_count_consistency`
  added to `src/myco/lint.py`, registered in `FULL_CHECKS`, with severity
  HIGH for user-facing surfaces (README badges, MYCO.md headlines) and
  MEDIUM for maintainer-facing surfaces (source code docstrings, comments).
- **Decision class**: `kernel_contract` because adding a new lint
  dimension is a kernel surface mutation (touches lint.py + cli.py help
  + immune.py exports + mcp_server.py docstring + canon contract version).
- **Contract bump**: v0.28.0 → v0.29.0 (minor — adds new mandatory
  invariant to the kernel contract, no breaking changes).
- **Label sync (Wave 37 D1 in action)**: Wave 38 will bump every surface
  from "19-dimension / L0-L18 / 19/19" to "20-dimension / L0-L19 / 20/20"
  in the SAME wave / SAME commit, because L19 will fail otherwise. This is
  the first wave to honor Wave 37 D1's discipline.

### 0.4 What this craft does NOT do

- Does NOT add a translation-mirror lint (Wave 37 D7 #2 — deferred).
- Does NOT add a contract-version-inline lint (Wave 37 D7 #3 — deferred).
- Does NOT touch anchor coverage scores, vision.md, theory.md, or any
  doctrine surface beyond the dimension-count labels.
- Does NOT add MCP tool mirror for lint dimension count (consistent with
  W32 D4 / W33 L6 / W35 L7 — agent tool budget consideration).
- Does NOT scan pinned surfaces (log.md, contract_changelog.md,
  docs/primordia/*.md, notes/*.md, examples/ascc/*) per Hard Contract #2.

## §1 — Round 1: Per-question audit (8 design questions)

### 1.1 Q1 — How is the canonical count computed?

**Decision**: Compute from `len(FULL_CHECKS)` at module load time.

**Rationale**:
- Hardcoding a constant `LINT_DIMENSION_COUNT = 20` would re-introduce
  the exact rot that L19 is designed to prevent (the constant itself
  becomes a downstream cache). The whole point is "ground truth from
  the structure that defines it".
- `FULL_CHECKS` is currently inside `main()` as a local variable. Wave 38
  will refactor it to a module-level tuple `FULL_CHECKS` so L19 can
  reference `len(FULL_CHECKS)` without recomputing. This refactor is
  itself a tiny improvement to code organization.
- L19 itself is in `FULL_CHECKS`, so `len(FULL_CHECKS) == 20` post-Wave-38.
  The chicken-and-egg is resolved by the order-of-operations: implement
  L19 → add to FULL_CHECKS → run lint → see surfaces fail at "19" → bump
  surfaces to "20" → lint passes.

### 1.2 Q2 — What patterns does L19 scan for?

**Decision**: 5 regex patterns, each capturing a specific drift class.

| # | Pattern | What it catches | Source surface |
|---|---------|-----------------|----------------|
| 1 | `Lint-(\d+)%2F(\d+)\s+green` | README badge | README*.md |
| 2 | `\b(\d+)[- ]dimension(?:al)?\s+(?:lint\|immune\|consistency)` | English count claim | source + docs |
| 3 | `\b(\d+)\s*维\s*(?:lint\|L0)` | Chinese count claim | MYCO.md, README_zh.md |
| 4 | `L0[-–](?:L)?(\d+)\b` | English range claim | every surface |
| 5 | `(\d+)/(\d+)\s+(?:green\|绿\|PASS\|pass)` | "X/X green" claim | README badges + wiki |

**Why these 5 specifically**: each pattern matches a class observed in
the Wave 37 sweep. Wave 37 had to fix exactly these classes; L19 prevents
their recurrence. Patterns are deliberately conservative (require literal
keywords like "green" / "lint" / "L0") to minimize false positives on
unrelated numeric strings.

**Patterns explicitly NOT included** (rejected):
- `\d+ checks?` — too vague, would match "5 checks" in test descriptions
- `dimensions: \d+` — would only catch YAML literal which is rare
- `len\(checks\) == \d+` — meta-circular, would only catch test code which
  is the wrong place to flag

### 1.3 Q3 — Which surfaces does L19 scan?

**Decision**: Two tiers — HIGH and MEDIUM — with exact file lists hardcoded
in the lint function.

**HIGH severity (user-facing narrative)**:
- `README.md`
- `README_zh.md`
- `README_ja.md`
- `MYCO.md`

**MEDIUM severity (maintainer-facing source/docs)**:
- `CONTRIBUTING.md`
- `wiki/README.md`
- `src/myco/cli.py`
- `src/myco/immune.py`
- `src/myco/mcp_server.py`
- `src/myco/migrate.py`
- `src/myco/init_cmd.py`
- `scripts/myco_init.py`
- `scripts/myco_migrate.py`
- `docs/reusable_system_design.md`
- `docs/adapters/README.md`

**NOT scanned (pinned per Hard Contract #2)**:
- `log.md` (append-only, historical entries reference old counts)
- `docs/contract_changelog.md` (append-only, historical entries reference
  old counts)
- `docs/primordia/*.md` (pinned crafts, may reference any historical count)
- `notes/*.md` (pinned, may reference any historical count)
- `examples/ascc/*.md` (pinned snapshot)

**NOT scanned (would create false positives)**:
- `src/myco/lint.py` itself — comments reference specific dimensions like
  `# L18 (Wave 30)` which would all fail. lint.py IS the source of truth,
  it cannot lint itself for dimension counts.

### 1.4 Q4 — What severity is L19?

**Decision**: HIGH for user-facing surfaces (README badges, MYCO.md
headlines), MEDIUM for source code / maintainer-facing docs.

**Rationale**: A drifted README badge is the FIRST thing a new user sees on
GitHub — silent first-impression damage. A drifted source comment is
maintainer-friction but not user-friction. The two-tier severity matches
the blast radius asymmetry.

**Why not all HIGH**: false-positive recovery cost. If L19 fires on a
maintainer-facing surface during a refactor wave (e.g., Wave 38 itself),
we want lint to allow `(some HIGH issues, no CRITICAL)` to exit non-fatally
in pre-flight scenarios. Mixed severity preserves that escape hatch.

**Why not all MEDIUM**: silent first-impression damage on README badges
deserves the same severity as L17 contract drift (HIGH) — both are
"substrate is misrepresenting itself to external observers".

### 1.5 Q5 — How does L19 handle the lint.py self-reference problem?

**Decision**: L19 explicitly excludes `src/myco/lint.py` from its scan.

**Rationale**: lint.py contains comments and docstrings like "L18 (Wave 30)"
that reference specific dimensions, not the count. Treating these as
"dimension count claims" would generate false positives. The simplest
defense is exclusion: lint.py IS the canonical source, it cannot be
linted against itself.

**Counter-defense**: what if lint.py's docstring at the top says "this
module implements 20 lint dimensions"? That would still be a current
claim that should track ground truth. **Resolution**: as long as the
top-of-file docstring uses literal numbers, exclude with a `# L19-exempt`
inline comment OR rephrase to "this module implements N lint dimensions
where N is `len(FULL_CHECKS)`". Wave 38's lint.py top docstring will be
audited and either rephrased or marked exempt.

### 1.6 Q6 — How does L19 distinguish current from historical claims?

**Decision**: L19 ONLY scans non-pinned surfaces (per §1.3). Pinned
surfaces are excluded from scan, so historical claims in
`log.md`/`changelog`/`primordia`/`notes` are inherently safe.

**Edge case**: what if a non-pinned surface (e.g., MYCO.md) wants to
reference a historical state like "as of Wave 8 we had 15 dimensions"?
- **Convention**: such references should be in changelog or release notes,
  not in living narrative. If genuinely needed in MYCO.md, the pattern
  must be paraphrased to avoid the regex (e.g., "Wave 8 introduced fifteen
  dimensions" with the number spelled out).
- **Severity for false positives**: if a legitimate historical reference
  trips L19, the operator can either rephrase the source surface or file
  a Wave 39+ refinement of L19's regex. Wave 38 prefers strict-and-loud
  over loose-and-silent because the silent failure mode is what we are
  fixing.

### 1.7 Q7 — Does L19 modify FULL_CHECKS structure or just append?

**Decision**: Refactor `main()`'s local `checks` variable to a module-level
constant `FULL_CHECKS` (and `QUICK_CHECKS` for the L0-L3 quick mode subset).
L19 reads `len(FULL_CHECKS)`.

**Why refactor not append**: a module-level constant makes `len(FULL_CHECKS)`
referentiable from L19's body without invoking `main()` or duplicating
the list. The refactor is small (~10 lines), preserves all existing
behavior, and creates the SSoT that Wave 37 D1 says should exist.

**Diff shape**:
```python
# Before (in main, lines 1824-1847):
checks = [("L0 ...", lint_canon_schema), ...]
if not quick:
    checks.extend([...])

# After (module-level, before main):
QUICK_CHECKS = (("L0 ...", lint_canon_schema), ...)
FULL_CHECKS = QUICK_CHECKS + ((...), ..., ("L19 ...", lint_dimension_count_consistency))
LINT_DIMENSION_COUNT = len(FULL_CHECKS)  # for export

# In main:
checks = list(QUICK_CHECKS) if quick else list(FULL_CHECKS)
```

Tuples (immutable) at module level prevent accidental mutation; the
explicit `list()` cast inside `main()` preserves the existing pattern of
treating `checks` as locally-mutable.

### 1.8 Q8 — How are tests structured?

**Decision**: 4 unit tests in `tests/unit/test_lint_dimension_count.py` (NEW):

1. `test_dimension_count_consistency_passes_when_synced` — fabricate a
   tmpdir with a README.md badge matching `LINT_DIMENSION_COUNT`, run L19,
   assert zero issues.
2. `test_dimension_count_consistency_fails_on_drifted_badge` — fabricate
   a tmpdir with `Lint-15%2F15 green` (drift from current 20), assert L19
   produces 1 HIGH issue with the correct file path and message format.
3. `test_dimension_count_consistency_fails_on_drifted_l_range` — fabricate
   a MYCO.md fragment with `**18 维 lint (L0-L17)**`, assert L19 produces
   2 issues (1 for "18 维 lint" + 1 for "L0-L17") because both patterns
   match and both drift.
4. `test_dimension_count_consistency_severity_split` — fabricate drift in
   both README.md (HIGH-tier) and CONTRIBUTING.md (MEDIUM-tier), assert
   the issues have correct severities and the function returns both.

**Why 4 tests not more**: each test pins one boundary in the design space:
(1) the pass case (validator/writer agreement), (2) the badge regex, (3)
the multi-pattern co-match case (one line, two regexes fire), (4) the
severity split. Adding more tests at this granularity would be fixture
duplication, not new boundary coverage.

## §2 — Round 2: Attack defense

### Attack A — "Why a new lint dimension instead of a one-time script?"

**The attack**: Wave 37 already fixed the problem. Adding L19 as a permanent
lint adds maintenance burden (one more dimension to update across surfaces
on every future bump), and a one-time `scripts/check_dimension_drift.py`
that can be run on demand would be lighter.

**Defense**:
- **Permanence is the point**. The Wave 37 → Wave 38 pattern is the same
  as Wave 22 → Wave 30: a manual operation that became a structural
  invariant. The whole substrate philosophy (anchor #2 non-parametric
  evolution + W12 craft reflex arc) is "turn lessons into structural
  constraints, not into procedural folklore". A one-time script is folklore
  that decays the moment the maintainer who knew about it leaves.
- **Marginal maintenance cost is a feature**. Yes, adding L19 means future
  bumps must update one more dimension count. But that "one more" is
  exactly the discipline the substrate needs — it forces the bump to be
  visible at lint time, not hidden in a script that someone has to remember
  to run. Maintenance pressure IS the safety property.
- **Lint is the substrate's immune system**. Adding a lint is the
  substrate-native way to encode any consistency invariant. Not adding it
  would be saying "this invariant is too maintenance-heavy to enforce
  structurally", which is equivalent to "this invariant should be silently
  optional", which is equivalent to "we accept silent rot here". That's
  exactly the failure mode Wave 37 surfaced.

**Resolution**: ATTACK FAILS. L19 is the correct shape.

### Attack B — "5 regex patterns will produce false positives"

**The attack**: Regex pattern matching against natural language text is
fragile. Patterns like `\b(\d+)[- ]dimension` will fire on phrases like
"in the 5-dimension space of color..." (hypothetical) and produce false
positives.

**Defense**:
- **Contextual constraint**: pattern 2 requires `(?:lint|immune|consistency)`
  AFTER the dimension claim. This rejects "5-dimension space" because
  "space" is not in the keyword set. The pattern is anchored to lint-domain
  vocabulary.
- **Surface scope is narrow**: L19 only scans a hardcoded list of 15 files,
  none of which have natural-language paragraphs about color spaces or
  unrelated mathematical dimensions. The substrate's narrative surfaces
  are technical doctrine, not general prose.
- **Failure mode is operator-correctable**: if a future surface (e.g., a
  new doc explaining vector space embeddings) trips L19 falsely, the fix
  is either (a) rephrase the surface to avoid the keyword, or (b) Wave N+
  refinement adds an exclusion. Either is cheap. The opposite failure
  mode (false negative — drift not caught) is what just cost us 7 waves.
- **Manual audit before commit**: Wave 38 will run L19 against the current
  substrate and inspect every issue it produces. If false positives exist,
  the regex is tuned BEFORE landing, not after. The Wave 38 commit must
  show L19 PASSING against a freshly-bumped substrate (20/20).

**Resolution**: ATTACK PARTIALLY VALID — false-positive risk is real but
mitigated by narrow surface scope + keyword-anchored patterns + pre-commit
audit. The risk is bounded and asymmetric (false-positive is annoying;
false-negative is what just cost 7 waves of silent rot).

### Attack C — "Why not just use a Python constant `LINT_DIMENSION_COUNT = 20`?"

**The attack**: A module-level constant in lint.py is simpler than the
FULL_CHECKS refactor. Just set `LINT_DIMENSION_COUNT = 20`, scan surfaces
against it, done. The FULL_CHECKS refactor adds complexity for no value.

**Defense**:
- **A constant is itself a downstream cache**. The whole point of L19 is
  "ground truth from the structure that defines it". A literal constant
  `LINT_DIMENSION_COUNT = 20` is exactly the same kind of label that
  README badges and MYCO.md headlines are — it's a number that has to be
  manually bumped on every dimension addition. Wave 39 would add L20
  and forget to bump the constant, and L19 would silently believe
  the wrong count.
- **`len(FULL_CHECKS)` is structurally derivable**. Adding `("L20 ...",
  lint_X)` to FULL_CHECKS automatically updates `len(FULL_CHECKS)`. The
  ground truth is the actual checks list, not a label that claims to
  match it. L19 is meaningful only if its anchor point is structural,
  not labeled.
- **Refactor cost is tiny**. Moving `checks = [...]` from inside `main()`
  to a module-level `FULL_CHECKS = (...)` is ~10 lines of mechanical edit.
  It does not change behavior, does not change the public API, and makes
  L19 strictly more reliable.

**Resolution**: ATTACK FAILS. The refactor is required for L19 to be
structurally sound.

### Attack D — "L19 will fail Wave 38's own commit if not bumped first"

**The attack**: Wave 38 adds L19 to FULL_CHECKS, making `len(FULL_CHECKS)
== 20`. Every existing surface still says "19" / "L0-L18". L19 will
immediately fire on every one of those surfaces. The lint will be RED at
the moment of L19's introduction, until all 15 surfaces are bumped. This
violates the marathon discipline (only stop on lint red) and the commit
discipline (every commit lints green).

**Defense**:
- **Order of operations**: Wave 38 does NOT commit until ALL surfaces are
  bumped. The implementation order is:
  1. Refactor `main()` → module-level `FULL_CHECKS`.
  2. Implement `lint_dimension_count_consistency` function.
  3. Add it to `FULL_CHECKS`.
  4. Bump every surface 19→20 (predictable mechanical edit, ~17 surfaces).
  5. Bump immune.py exports + mcp_server.py L0-L19 enumeration.
  6. Bump _canon.yaml contract v0.28.0 → v0.29.0.
  7. Run lint, expect 20/20 PASS.
  8. Run pytest, expect (22 + new L19 tests) PASS.
  9. Commit.
- **Lint red is acceptable IN-WAVE if it's the wave's own intermediate
  state**. The marathon discipline says "stop on lint red" meaning "do not
  push a red commit", not "every line of every edit must keep lint green".
  Intermediate red state during a multi-step wave is normal — Wave 30 was
  red between steps 4 and 11, Wave 35 was red between steps 3 and 9. The
  discipline is about commit boundary, not edit boundary.
- **Pre-commit verification gate**: Wave 38 CANNOT commit until step 7
  passes. If it doesn't pass, the wave is debugged BEFORE the commit, not
  pushed-then-fixed. This is the same gate every kernel_contract wave has
  honored.

**Resolution**: ATTACK FAILS. The intermediate-red-state concern is real
but is the standard operating procedure for any wave that adds a new lint
dimension. The discipline is honored at commit time, not at every edit.

### Attack E — "Why exclude lint.py from its own scan? That's a loophole."

**The attack**: L19 scans every narrative surface except lint.py itself.
This means future stale claims IN lint.py docstrings will go unflagged.
The lint cannot self-correct. This is a structural blind spot.

**Defense**:
- **Self-referential scan creates a circular dependency**: L19 lives in
  lint.py. lint.py contains specific dimension references (`L18 (Wave 30)`,
  `# 19 immune dimensions`) that are NOT current count claims, they are
  identifiers for specific dimensions. Pattern 4 (L0-LX) would fire on
  every `# L0-L18` comment, generating dozens of false positives. The
  scan is structurally impossible to make clean against the very file
  that defines the lint.
- **Mitigation: comment-level exemption**: L19 can be extended later to
  scan lint.py with a `# L19-EXEMPT: ...` inline annotation marking lines
  that are intentionally count-bearing. This is deferred to Wave 39+ if
  friction emerges. For Wave 38, the simpler exclusion is sufficient
  because lint.py's count-bearing surfaces are primarily docstring
  headings, which have low drift rate (developers editing lint.py are by
  definition aware of the dimension count).
- **Consistency check via tests**: the test `test_dimension_count_count
  matches_full_checks` (a sanity test in test_lint_dimension_count.py)
  asserts `len(FULL_CHECKS) == 20` directly. This is the substitute
  for self-scanning lint.py — the test pinpoints the canonical count and
  fails loudly if a future refactor breaks it. **WAIT — this is exactly
  the kind of brittle test that needs maintenance per dimension addition.**
  Reject this sub-mitigation; the canonical count comes from the structure,
  not from a test assertion.
- **Honest limitation**: L19 has a known scope hole at lint.py self-scan.
  This is L19 honest limitation L1. Filed in §3.

**Resolution**: ATTACK PARTIALLY VALID. L19 has a known scope hole at
lint.py itself. The hole is documented as L1 known limitation. Future
Wave N may close it via comment-level exemption annotation. For Wave 38,
the simpler exclusion is the correct trade-off.

### Attack F — "20 lint dimensions is a lot. When does the substrate stop adding more?"

**The attack**: At Wave 38 the substrate has 20 lint dimensions. At Wave 50
it might have 30. Each new dimension adds maintenance burden, slows
`myco lint` by N%, and risks false positives. The substrate should consider
when to stop expanding the immune system rather than always adding more.

**Defense**:
- **The growth rate matches doctrine maturity, not drift**. Reviewing
  L0–L18 history:
  - L0–L8: born during Hermes/ASCC scar history (Wave 1–8)
  - L9–L14: Wave 8 pre-release re-baseline
  - L15: Wave 12 craft reflex arc
  - L16: Wave 21 boot brief freshness
  - L17: Wave 24 contract drift
  - L18: Wave 30 compression integrity
  - L19: Wave 38 dimension count consistency
  - Each addition closes a *real scar* — not a hypothetical defense, an
    actual past failure that the substrate experienced.
- **Substrate growth is bounded by failure modes**. New lint dimensions
  are added when a real failure mode is observed, not when a hypothetical
  defense seems clever. The substrate has had 5 lint additions in 30 waves
  (~1 per 6 waves), which is a sustainable rate.
- **Performance impact is negligible**. The current 19-dimension lint
  runs in ~1 second. L19 is a regex sweep over 15 small files — its
  marginal cost is <50ms. At 30 dimensions the lint will still run in
  under 2 seconds.
- **The "stop adding" question deserves a future craft, not a Wave 38
  block**. If Wave 50+ produces a "lint dimension proliferation" friction
  signal, that warrants a Wave N craft that audits which dimensions are
  still load-bearing and which can be retired. Wave 38 does not need to
  pre-answer that question. Wave 26 D3 says "service the friction that is
  firing now"; today's friction is "label drift", not "too many lints".

**Resolution**: ATTACK FAILS for Wave 38 scope. The "when to stop" question
is a legitimate future concern but not a blocker for Wave 38.

## §3 — Round 3: Edge cases + Decision lock

### 3.1 Edge cases

**C1 — Surface file does not exist (e.g., `wiki/README.md` deleted in some
project)**: L19 must `continue` silently, not raise. Implementation: `if
not path.exists(): continue`.

**C2 — Surface file is empty or unreadable**: same as C1, `continue` if
`read_file()` returns None.

**C3 — Pattern matches the same line twice (overlap)**: regex `finditer()`
yields non-overlapping matches by default. Two distinct patterns matching
the same line both fire — that's the desired behavior (test 3 above).

**C4 — Multi-line claims**: L19 scans line-by-line, so a claim split across
lines (e.g., `\n19-\ndimension lint`) would not match. This is acceptable
because no observed surface uses such formatting. Filed as L2 limitation.

**C5 — Surface uses comma-formatted numbers (`1,000 dimensions`)**: regex
`\b(\d+)\b` would match "000" not "1,000". This is a hypothetical edge
case with no current substrate occurrence. Filed as L3 limitation.

**C6 — Surface uses spelled-out numbers ("twenty dimensions")**: L19 does
not catch spelled-out numbers. This is an acceptable limitation because
no observed surface uses spelled-out numbers, and the convention is
to use digit form for technical claims. Filed as L4 limitation.

**C7 — README badge URL contains the count in a different format
(`shields.io/badge/Lint-19/19-green`)**: L19 pattern 1 specifically matches
the `%2F` URL-encoded slash form. If a surface uses literal `/`, the
pattern misses it. Currently all 3 README badges use `%2F`. Filed as L5
limitation if we ever add a surface with the literal-slash form.

### 3.2 Decision lock D1–D9

**D1**: L19 = `lint_dimension_count_consistency`, registered in
`FULL_CHECKS` after L18, severity HIGH for user-facing surfaces and MEDIUM
for source/maintainer surfaces. Closes Wave 37 D7 candidate #1 + Wave 37
D1 enforcement.

**D2**: Refactor `main()`'s local `checks = [...]` to module-level
`QUICK_CHECKS` + `FULL_CHECKS` tuples (immutable). `main()` reads them as
`list(QUICK_CHECKS)` or `list(FULL_CHECKS)` to preserve local mutability.
This is a tiny refactor that creates the SSoT for `LINT_DIMENSION_COUNT`.

**D3**: Canonical count = `len(FULL_CHECKS)` computed at module-load time.
NO Python constant `LINT_DIMENSION_COUNT = N` (that would be a downstream
cache, defeating the purpose). The expression `len(FULL_CHECKS)` IS the
SSoT.

**D4**: Surface list hardcoded in L19 body — 4 HIGH (READMEs + MYCO.md) +
11 MEDIUM (sources/docs/scripts). NOT in canon yaml because the list is
implementation detail, not contract surface. NOT extensible by user
configuration in v1 — operators who fork Myco can edit the list directly.

**D5**: Pinned surfaces NEVER scanned: `log.md`, `contract_changelog.md`,
`docs/primordia/*.md`, `notes/*.md`, `examples/ascc/*`. These are
append-only / pinned by Hard Contract #2. lint.py also excluded (own-file
self-reference loophole, filed as L1).

**D6**: 5 regex patterns (badge, X-dimension, X 维, L0-LX, X/X green/绿/PASS).
Conservative — require domain keywords. False-positive recovery cost is
acceptable; false-negative recovery cost is what we are eliminating.

**D7**: Contract bump v0.28.0 → v0.29.0 (minor — adds new mandatory
invariant). Update `_canon.yaml` + `src/myco/templates/_canon.yaml` mirror.
Append v0.29.0 entry to `docs/contract_changelog.md`.

**D8**: 4 unit tests in `tests/unit/test_lint_dimension_count.py` covering
(1) pass case, (2) badge drift, (3) multi-pattern co-match, (4) severity
split. Total test count: 22 → 26 (+4).

**D9**: Wave 38 lands the SAME wave as the surface bumps (19→20 across
all 15 surfaces). This is the first wave to honor Wave 37 D1's "label sync
in same wave as dimension addition" discipline. Future waves adding new
dimensions MUST follow the same pattern.

## §4 — Conclusion

### 4.1 Decisions captured

D1–D9 above. All decisions are binding and become canon for Wave 38+.

### 4.2 Landing list (15 verifiable steps)

1. Refactor `src/myco/lint.py::main` — extract `checks = [...]` to
   module-level `QUICK_CHECKS` + `FULL_CHECKS` tuples (D2). ~10 line diff.
2. Implement `lint_dimension_count_consistency(canon, root)` in
   `src/myco/lint.py` (~120 LOC) per §1.2 + §1.3 + §1.4 + D6.
3. Add `("L19 Lint Dimension Count Consistency",
   lint_dimension_count_consistency)` to `FULL_CHECKS` (D1, D3). This
   makes `len(FULL_CHECKS) == 20`.
4. Update `src/myco/lint.py` top-of-file docstring (if needed) to either
   rephrase any current count claim or mark exempt.
5. Bump `_canon.yaml::system.contract_version` v0.28.0 → v0.29.0 +
   `_canon.yaml::system.synced_contract_version` mirror (D7).
6. Bump `src/myco/templates/_canon.yaml` mirror (same change).
7. Append v0.29.0 entry to `docs/contract_changelog.md` documenting
   the new L19 dimension + label-sync mandate.
8. Bump `src/myco/immune.py` — re-export `lint_dimension_count_consistency`,
   docstring "19-dimension" → "20-dimension", "L0–L18" → "L0–L19",
   add L19 bullet, update `__all__`, update `# 19 immune dimensions`
   comment.
9. Bump `src/myco/cli.py` — 4 occurrences "19-dimension" → "20-dimension"
   in lint + immune parser blocks.
10. Bump `src/myco/mcp_server.py` — 3 occurrences (line 9 module docstring,
    line 108 tool description with full L0-L19 enumeration adding L19,
    line 189 mode label `full (L0-L18)` → `full (L0-L19)`).
11. Bump README.md, README_zh.md, README_ja.md (3 surfaces, badge
    `Lint-19%2F19` → `Lint-20%2F20`, plus body counts).
12. Bump MYCO.md (~3 occurrences: §身份锚点 invariant clause "19 维 lint
    L0-L18" → "20 维 lint L0-L19", §指标面板 rationale).
13. Bump CONTRIBUTING.md (line 140), wiki/README.md (line 35),
    docs/reusable_system_design.md (line 197).
14. Bump src/myco/migrate.py (line 169), src/myco/init_cmd.py (line 115),
    scripts/myco_init.py (line 104), scripts/myco_migrate.py (line 217)
    — 4 identical shim creation messages "19-dimension" → "20-dimension".
15. Add `tests/unit/test_lint_dimension_count.py` with 4 tests (D8).
    Verify `myco lint` 20/20 PASS + `pytest tests/ -q` 26/26 PASS.

### 4.3 Known limitations

**L1 — lint.py self-scan loophole**: L19 does not scan lint.py itself
to avoid false positives on dimension-identifier comments (`# L18 (Wave
30)` etc). A future Wave N+ may close this via comment-level
`# L19-EXEMPT: ...` annotation. For Wave 38, the exclusion is
documented and accepted.

**L2 — Multi-line claims not detected**: a claim split across lines is
not caught by line-by-line scan. No observed surface uses this; deferred
unless friction emerges.

**L3 — Comma-formatted numbers not detected**: hypothetical edge case.

**L4 — Spelled-out numbers not detected**: ("twenty dimensions") —
acceptable per substrate convention of digit form for technical claims.

**L5 — Literal-slash badge format not detected**: pattern 1 only matches
`%2F`. If a future surface uses `Lint-19/19-green` directly, the pattern
misses it. Mitigation: substrate currently uses `%2F` consistently;
defer fix until counter-example surfaces.

**L6 — Pinned surfaces not validated**: by design — pinning means
historical claims are correctly preserved, even if they reference old
counts. L19 trusts the pinning convention to prevent stale doctrine
from leaking into living surfaces.

**L7 — No MCP tool mirror for L19** — consistent with W32 D4 / W33 L6 /
W35 L7. Agent tool budget consideration; lint runs as a single tool
already.

### 4.4 Wave 39+ trajectory

Per Wave 26 D3 friction-driven ordering, NOT pre-scoped. Candidates from
Wave 37 D7 + Wave 36 §4.4 still on deck:
- Wave 37 D7 #2 — translation-mirror lint (would catch README mirror
  divergence between EN/zh/ja)
- Wave 37 D7 #3 — contract-version-inline lint (would flag inlined
  `contract v0.X.Y` strings in non-changelog surfaces)
- Wave 36 §4.4 (b) — inlet_ripe / compression_overdue advisory signal
- Wave 36 §4.4 (c) — cross-reference graph for inlet provenance
- Wave 36 §4.4 (d) — Wave 29b biomimetic file renames

Wave 39 opening assessment will pick the highest-leverage candidate based
on which surface produces the most friction next.

### 4.5 Supersession pointer

This craft does NOT supersede any prior craft. It executes the
parenthetical promise in Wave 37 craft §4.4 ("see §4.4") and Wave 37 D1's
"will be the SSoT enforcement" implication.
