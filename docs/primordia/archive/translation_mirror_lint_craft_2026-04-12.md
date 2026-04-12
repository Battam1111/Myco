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

# Wave 39 — L20 Translation Mirror Consistency

**Purpose**: Add a new lint dimension `L20 Translation Mirror Consistency`
that enforces structural skeleton parity across the three locale-mirror
README files (`README.md` / `README_zh.md` / `README_ja.md`). Closes Wave 37
D7 candidate #2, the second-highest-leverage Wave 39 candidate per Wave 26
D3 friction-driven ordering, and follows the same SSoT-violation-class shape
as L19 (which closed candidate #1 in Wave 38). The three READMEs are the
substrate's user-facing first impression in three languages; if their
structural skeletons drift apart (one section dropped from `README_zh.md`
but not from `README.md`), non-English users see a degraded substrate while
English readers see a healthy one. L20 makes that class of drift
structurally impossible by enforcing intra-locale skeleton parity.

## §0 — Problem definition

### 0.1 What fired this wave

Wave 37 D7 candidate ranking placed `translation-mirror lint` at #2:

1. **Lower historical leverage than L19** but **higher anticipated leverage**:
   the three READMEs already exist (`README.md`, `README_zh.md`, `README_ja.md`)
   and have already accumulated subtle structural drift. A manual diff at
   Wave 38 R0 found that all three currently mirror in skeleton (14 H2 + 5
   H3 capabilities), but there is no automated check enforcing this. The
   first time a wave adds a section to `README.md` and forgets the locale
   mirrors, the drift becomes silent.

2. **Same root pattern as L19**: SSoT violation. The "structural truth" of
   the README is its section skeleton (count + relative order of H2/H3
   headings + key tabular structures). The three locale files are
   downstream caches of that truth. L19 enforced numerical-claim parity
   across surfaces; L20 enforces structural-skeleton parity across locales.

3. **User-facing impact**: README is a first-impression surface. Drift here
   directly mistreats non-English users, who would see a substrate with
   missing sections and conclude the project is incomplete or abandoned in
   their language. Severity is HIGH.

4. **Hard for human to spot**: a maintainer who only reads English cannot
   notice that `README_zh.md` is missing a section unless they read all
   three. The cost of manual review scales with the number of locales. An
   automated check is the only sustainable defense.

### 0.2 The structural truth (SSoT for translation skeleton)

Wave 39 R0 enumerated the current skeleton of all three READMEs by counting
markdown structural elements:

| Element                          | README.md | README_zh.md | README_ja.md |
|----------------------------------|-----------|--------------|--------------|
| H1 sections (`^# `)              | 1         | 1            | 1            |
| H2 sections (`^## `, real)       | 14        | 14           | 14           |
| H3 sections (`^### `, real)      | 5+1=6     | 5+1=6        | 5+1=6        |
| Fenced code blocks (```)         | 4         | 4            | 4            |
| Verb table rows (`\| ... \|`)    | 22        | 22           | 22           |
| Lint badge (`Lint-N%2FN`)        | 1         | 1            | 1            |

(Note: H2/H3 counts exclude lines that appear inside fenced code blocks;
the parser must respect code-fence state.)

The "real" structural truth is therefore: `(14, 6, 4, 22, 1)`. Any drift
on any one of these counts in any one of the three READMEs is a translation
mirror violation.

### 0.3 What L20 must NOT do

- L20 must NOT compare actual heading text. Translation is precisely
  why these files exist; their text is supposed to differ.
- L20 must NOT compare paragraph content or word counts. Translation
  length naturally varies (Chinese is denser than English; Japanese is
  more verbose).
- L20 must NOT enforce specific line numbers. Translation length differences
  shift line numbers naturally.
- L20 must NOT scan files outside the 3 enrolled READMEs. Future
  multilingual surfaces (e.g. CONTRIBUTING_zh.md if it ever exists) must
  be enrolled explicitly via a Wave 40+ scope expansion.

## §1 — Round 1: design

### 1.1 What L20 enforces (positive specification)

L20 reads all three README files (HIGH severity for any failure) and
computes a 5-tuple of structural counts for each:

```
skeleton(file) = (
    h2_count,      # number of `^## ` headings outside fenced code blocks
    h3_count,      # number of `^### ` headings outside fenced code blocks
    code_count,    # number of fenced code block opens (``` ... ```)
    table_rows,    # number of `^|` table rows in the verb table section
    badge_count,   # number of `Lint-N%2FN` badge lines
)
```

The reference skeleton is `skeleton(README.md)`. L20 fails any locale file
whose skeleton tuple does not equal the reference. Each mismatched component
produces a separate issue line so the human reader can see exactly which
counts drifted.

### 1.2 Why README.md is the reference

The English README is the source of truth because:
1. It is updated first in practice (the workflow is "edit English, then
   translate"; this is observed across Waves 30-38).
2. Every contributor reads English; only some read CJK.
3. Picking *one* canonical reference is necessary for a 1-vs-N comparison
   model. Picking the English one is the least surprising default.

This is a documented design decision (D2 below) and can be revisited if
the project's contributor base shifts.

### 1.3 Five design questions to address in §2 attacks

- **Q1**: Should L20 also enforce verb table content parity (verb-by-verb)?
- **Q2**: Should the skeleton tuple be expanded to include paragraph counts?
- **Q3**: How does L20 handle fenced code blocks containing `##` lines?
- **Q4**: Where does L20 sit relative to L19? Same wave class? Same severity?
- **Q5**: What if a wave deliberately drops a section from one locale (e.g.
  Japanese README intentionally omits something)?

## §2 — Round 2: attack the design

### 2.1 Attack A — "Why not a single 'translation parity' check that covers
both structural skeleton AND verb table content?"

**Defense**: scope creep. The verb table is already in the structural count
(its row count is one of the 5 tuple components). Verb-by-verb content
comparison would require the verb names (the leftmost cell) to be locale-
neutral, which they ARE in the current codebase (`myco eat`, `myco lint`,
etc. — all Latin). But that's a separate invariant that deserves its own
dimension if drift is observed. Wave 38 craft Round 2 Attack A taught us:
"a structural lint that does too much produces too many false positives and
the team starts ignoring it." Skeleton parity is a focused, defensible
invariant. Verb-content parity can be Wave 41+ if friction surfaces.

### 2.2 Attack B — "Why isn't this just a unit test, Wave 38-style?"

**Defense**: a unit test would only catch drift in the test snapshots, not
in the README files themselves. The test file would itself be a downstream
cache (the snapshot would need to be updated when the README changes), and
that cache could rot the same way the dimension-count narrative caches did.
A lint dimension reads the live README files at every invocation, so it
cannot rot. Wave 38 D3 ("L19 as a permanent structural lint") applies
identically here: Wave 39 D3.

### 2.3 Attack C — "What about the H2 lines INSIDE fenced code blocks?
Lines 207, 210, 213 of README.md start with `# ` inside a bash code block."

**Defense**: this is exactly why the parser must track fenced-code state.
The implementation MUST count toggle on each ``` line and skip H2/H3/H1
headings inside fences. Wave 39 R0 verified all three READMEs use the
same code-fence convention (triple-backtick, no language-specific
exceptions). The parser is ~10 lines of state-machine code.

### 2.4 Attack D — "What if the user intentionally adds a section to
README.md that doesn't make sense in Chinese or Japanese?"

**Defense**: Wave 39 D5 escape hatch — the user can add a wave-specific
exception by passing a `# l20-skip` HTML comment marker on the line above
the section. The parser respects the marker and excludes that section
from the count. This is the same pattern Wave 38 R3 C7 used for the
quick-mode L0-L3 exemption: legitimate exceptions get an explicit opt-out,
not a silent drop. In practice this should be rare; the design assumption
is that all sections in the English README should mirror to the locale
files. If exceptions become common, the design is wrong and the dimension
should be revisited.

### 2.5 Attack E — "Why is HIGH the right severity? Translation is a
nice-to-have, not load-bearing."

**Defense**: this attack is wrong on two counts. First, the project
explicitly maintains three locale READMEs as a contributor commitment; if
that commitment were optional, the files wouldn't exist. Second, the
substrate-immutability doctrine treats user-facing first impressions as
HIGH severity (Wave 38 D4): a user who sees a half-translated README
forms a half-finished impression of the substrate, which is exactly the
"silent damage" L19's HIGH classification was designed to protect against.
HIGH stays.

### 2.6 Attack F — "What if README.md drops a section but README_zh.md
keeps it? Is that drift, or is README.md the regression?"

**Defense**: under D2 (README.md is the reference), this would be flagged
as `README_zh.md has 15 H2 sections, README.md has 14`. The user reading
the lint output decides whether the regression is in the English (in which
case they restore the section) or the Chinese (in which case they remove
it from Chinese). L20 surfaces the asymmetry; the human resolves it. This
is explicitly NOT a case where the lint should auto-fix; the *direction*
of the fix is a human-judgment call.

## §3 — Round 3: edge cases + decisions

### 3.1 Edge cases enumerated

- **C1**: README.md doesn't exist → L20 silently passes (nothing to compare).
  This happens in fresh `myco init` projects before the user writes a
  README. L20 only fires when at least 2 of the 3 locale files exist.

- **C2**: Only 2 of the 3 README files exist (e.g. only English + Chinese).
  L20 still fires but only compares the 2 present files. The "reference"
  is whichever file has higher line count (proxy for "more developed").

- **C3**: A README file is empty (0 bytes). Treated as "exists but has
  no skeleton". L20 reports the drift loudly (`README_zh.md has skeleton
  (0,0,0,0,0) vs reference (14,6,4,22,1)`).

- **C4**: A README file uses `=`/`-` underline-style headings instead of
  `#`/`##`. The Wave 39 implementation supports atx headings only (`^#`).
  Setext-style headings are out of scope; the project convention is
  atx everywhere. If a future contributor introduces setext, the parser
  will silently miss them — this is documented as L1 below.

- **C5**: A README file uses Windows line endings (CRLF). The parser must
  use `splitlines()` which handles all line ending styles. Verified.

- **C6**: A heading has trailing whitespace (`## Foo  \n`). The parser
  must `rstrip()` before checking the prefix, otherwise edge spacing
  produces false matches/misses. Implemented.

- **C7**: The verb table heading is the same line in all three READMEs?
  No — Wave 39 R0 verified the verb table is consistently the LAST H3
  section in all three READMEs (under "How You Work With Myco" or its
  translated equivalent). The parser counts table rows by scanning for
  `^|` lines after the last H3 in the file.

### 3.2 Decisions (D1-D8)

**D1 — SSoT principle for translation skeleton**: `skeleton(README.md)` is
the canonical structural truth. `README_zh.md` and `README_ja.md` are
downstream caches that MUST mirror it tuple-for-tuple. This is the same
SSoT principle as Wave 38 D1, applied to a different cache class
(structural skeleton vs numerical claim).

**D2 — README.md as the reference**: English README is reference for the
reasons in §1.2. Revisit if contributor base shifts.

**D3 — L20 as a permanent structural lint** (mirrors Wave 38 D3): no
one-time scripts, no test-snapshot caches, no manual review checklist.
L20 reads live files at every lint run.

**D4 — HIGH severity matrix**: all 3 READMEs are HIGH (per Wave 38 D4
"user-facing first impression" classification). Per-component issues each
emit a separate line so triage is granular.

**D5 — Skip-marker escape hatch**: a section preceded by `<!-- l20-skip -->`
on the previous non-blank line is excluded from all skeleton counts. This
allows wave-specific exceptions (e.g. an English-only "Open Problems"
section that doesn't translate) without weakening the lint.

**D6 — Code-fence-aware parser**: the H2/H3 counter MUST respect fenced
code blocks. The parser is a ~15-line state machine: track fence depth,
ignore heading-prefix lines while inside a fence.

**D7 — Contract bump v0.29.0 → v0.30.0**: L20 is a new lint dimension that
modifies the behavior of `myco lint`, increases `len(FULL_CHECKS)` from 20
to 21, and is therefore a kernel_contract change requiring contract bump.

**D8 — Four unit tests in `tests/unit/test_lint_translation_mirror.py`**:
test_l20_clean_substrate_passes (3 mirrored stub READMEs, 0 issues),
test_l20_section_drop_caught (one locale missing one H2 section),
test_l20_skip_marker_respected (l20-skip marker excludes a section
correctly), test_l20_code_fence_aware (`## ` line inside ``` is NOT
counted as a real H2 section).

### 3.3 Known limitations

- **L1**: Setext-style headings (`====` / `----` underlines) are not
  supported. The project convention is atx-only; setext would silently
  pass through the parser. If a future contributor introduces setext,
  the dimension will under-count. Acceptable trade-off given zero
  setext usage in current substrate.

- **L2**: L20 is enrolled to exactly 3 README files. New multilingual
  surfaces require an explicit code change to add to the enrolled list.
  This is identical to L19 D5's "explicit allowlist" pattern and the same
  trade-off applies: false positives on incidentally-numeric strings in
  unrelated docs would be unacceptable, so explicit allowlist wins.

- **L3**: The 5-tuple skeleton is a proxy for "structural parity", not
  full prose parity. L20 cannot catch a translation that has the right
  number of sections but wildly wrong content. Full prose parity is
  fundamentally unenforceable by an automated check (translation is
  not a function); manual review remains the only defense for prose
  drift. L20 only protects the skeleton.

- **L4**: L20 does not enforce that the locale READMEs are kept in
  sync *temporally* (one is updated and the other is not until later).
  The skeleton-parity check captures the steady state, not the velocity.
  A wave that is partway through a multi-locale update will trip L20
  until all three files are updated; this is the desired behavior
  ("the wave is incomplete until all three are mirror-aligned").

## §4 — Conclusion

### 4.1 Decisions (canonical reference, copy to log.md milestone)

**D1**: SSoT for translation skeleton = `skeleton(README.md)`.

**D2**: Reference README is `README.md` (English).

**D3**: L20 is a permanent structural lint, not a script or test snapshot.

**D4**: HIGH severity for all 3 READMEs.

**D5**: `<!-- l20-skip -->` marker respected on the line before a section.

**D6**: Code-fence-aware parser (skip headings inside ``` blocks).

**D7**: Contract bump v0.29.0 → v0.30.0.

**D8**: 4 unit tests covering D1, D5, D6, and section-drop drift.

**D9** (operational): the implementation MUST also bump all narrative
surfaces' "20-dimension / L0-L19 / 20/20" → "21-dimension / L0-L20 / 21/21",
which is L19's job. L19 will catch any forgotten surface at the next lint
run, dogfooding L19's protection during Wave 39's own landing.

### 4.2 Landing list (≤ 15 verifiable steps)

1. Add `lint_translation_mirror_consistency(canon, root)` function to
   `src/myco/lint.py` with full docstring tracing back to Wave 39 D1-D9.
2. Add `_L20_LOCALE_READMES = ("README.md", "README_zh.md", "README_ja.md")`
   constant near `_L19_HIGH_SURFACES`.
3. Implement `_count_skeleton(content)` helper that returns the 5-tuple
   `(h2, h3, code, table_rows, badge)` for a given file content, with
   code-fence state machine and l20-skip marker respect.
4. Add L20 entry to `FULL_CHECKS` tuple at the end of the dimension list.
5. Bump `_canon.yaml::system.contract_version` v0.29.0 → v0.30.0 +
   `synced_contract_version` mirror.
6. Bump `src/myco/templates/_canon.yaml::system.synced_contract_version`
   v0.29.0 → v0.30.0.
7. Append v0.30.0 entry to `docs/contract_changelog.md` with motivation,
   changes, verification, backward-compatibility, forward path.
8. Bump `src/myco/lint.py` module docstring header `20-Dimension` →
   `21-Dimension` and dimension table.
9. Bump `src/myco/immune.py` `20-dimension immune system` →
   `21-dimension immune system` + add L20 bullet to dimension list.
10. Bump `src/myco/mcp_server.py` lines 9, 90, 108, 189: `20-dimensional` →
    `21-dimensional`, add L20 to enumeration in tool description, mode
    label `full (L0-L19)` → `full (L0-L20)`.
11. Bump 12 other narrative surfaces — README badges (en/zh/ja)
    `Lint-20%2F20` → `Lint-21%2F21`, MYCO.md headlines, CONTRIBUTING.md,
    wiki/README.md, the migrate/init scripts, docs/reusable_system_design.md.
12. MYCO.md §指标面板: bump lint health value 0.70 → 0.72 with L20 mention,
    bump contract version line v0.29.0 → v0.30.0.
13. Add `tests/unit/test_lint_translation_mirror.py` with 4 tests (D8).
14. Eat decisions note via `myco eat` + `myco digest --to integrated`.
15. Run `myco lint` → expect 21/21 PASS. Run `pytest tests/ -q` → expect
    30/30 PASS (26 prior + 4 Wave 39). Append log.md Wave 39 milestone.
    Commit `[contract:minor] Wave 39 — L20 translation mirror lint (v0.30.0)`
    + push.

### 4.3 Known limitations (carried forward to landing record)

L1-L4 from §3.3 above are inherited as known limitations of the landing.
Specifically: setext headings unsupported, explicit allowlist required for
new multilingual surfaces, prose parity uncatchable, temporal velocity
not measured.

### 4.4 Wave 40+ disposition

Wave 39 closes Wave 37 D7 followup #2. Remaining followup from Wave 37 D7:

- **#3**: contract-version-inline lint (cli help strings, mcp tool
  annotations must mirror `_canon.yaml::contract_version`)

This becomes the natural Wave 40 candidate per Wave 26 D3 friction-driven
ordering, completing the 3-wave SSoT-enforcement sequence (Wave 38 numerical
claims, Wave 39 structural skeleton, Wave 40 inline version strings).

Wave 41+ candidates (deferred until friction surfaces):
- Verb-content parity across locale READMEs (Wave 39 §2.1 deferral)
- Cross-version migration assistance for contract bumps
- Whatever new friction `myco hunger` reports after Waves 38-40 land

### 4.5 Supersession pointer

This craft does not supersede any prior craft. It builds on:
- Wave 26 D3 (friction-driven ordering)
- Wave 37 D7 (followup ranking)
- Wave 38 D1-D9 (SSoT enforcement pattern)

Wave 38's Wave 39+ disposition explicitly anticipated "translation-mirror
lint" as the next followup; this craft executes that anticipation.

### 4.6 Confidence self-report

Target confidence: 0.90 (kernel_contract floor per craft_protocol §4).
Current confidence: 0.90 (single-author equality per craft_protocol §4
floor for kernel_contract). The 0.90 reflects:
- (+) Direct continuation of Wave 38's proven SSoT-enforcement pattern
- (+) Skeleton-parity is a well-defined, testable invariant
- (+) All 3 READMEs already mirror in skeleton at Wave 39 R0
- (-) The 5-tuple is a coarser-grained check than full prose parity (L3)
- (-) Setext heading support (L1) and temporal velocity (L4) are gaps
- (-) Cannot catch prose drift, only skeleton drift

Confidence is appropriate for a kernel_contract change that enforces a
new structural invariant on a HIGH-severity surface (the README badge is
literally the first thing a user sees on the GitHub project page).
