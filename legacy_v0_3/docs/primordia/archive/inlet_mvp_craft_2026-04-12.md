---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
closes:
  - "Wave 34 metabolic_inlet_design_craft_2026-04-12 §3.1 (10-item implementation brief)"
  - "Wave 26 vision_reaudit_craft_2026-04-12 §2.3 long-tail: 'Metabolic Inlet primitive — declared in anchor #3, never implemented' (scaffold piece only)"
  - "Anchor #3 七步代谢管道: closes the inlet declaration gap that has been open since Wave 10 vision recovery"
---

# Wave 35 — `myco inlet` MVP (Metabolic Inlet primitive scaffold)

> **Scope**: kernel_contract class implementation craft. Lands the
> Metabolic Inlet primitive declared in anchor #3 (七步代谢管道) and
> deferred since Wave 10. Operator-deferred for all 4 open_problems
> §1-4 sub-problems per Wave 34 §2.4 (cold start / trigger signals /
> alignment / continuous compression hook).
>
> **Parents**:
> - Wave 34 `metabolic_inlet_design_craft_2026-04-12.md` §3.1 (locked spec)
> - Wave 26 `vision_reaudit_craft_2026-04-12.md` §2.3 (long-tail priority)
> - Wave 10 `vision_recovery_craft_2026-04-10.md` (the original anchor #3
>   declaration that this wave finally implements)
>
> **Supersedes**: none. (Wave 34 design is augmented, not replaced — this
> craft validates the design under implementation pressure.)

## 0. Problem definition

Wave 34 produced a complete scaffold design (D1–D8) for the Metabolic Inlet
primitive, with the prescriptive 10-item implementation brief at §3.1. But
no code. Anchor #3 (`七步代谢管道：感受 → 评估 → 提取 → 整合 → 压缩 → 摄取 → 排泄`)
has carried an implementation gap since Wave 10's Vision Recovery. The first
step of the seven-step pipeline — the inlet — has been doctrinally declared
for 25 waves with no kernel-side implementation.

The Wave 26 audit (`docs/primordia/vision_reaudit_craft_2026-04-12.md` §2.3)
flagged this as the longest-standing implementation deferral in the substrate.
Wave 26 Round 1's per-anchor coverage assessment placed anchor #3 at 0.65
because: ① the digestion verbs (W32 evaluate/extract/integrate) were just
landed; ② the compression verb (W30) was just landed; but ③ no inlet existed.

Wave 34 designed the scaffold with deliberate scope discipline: the design
covers WHAT the primitive looks like and HOW provenance is captured, but
explicitly defers WHO decides what to inlet, WHEN to inlet, WHETHER to
filter relevance, and HOW to wire continuous compression. Those four
sub-problems are catalogued in `docs/open_problems.md` §1-4 and remain
operator-deferred per Wave 34 D2 + D5.

**The problem this craft solves**: Wave 34 §3.1 prescribed a 10-item brief
but did not validate it under implementation pressure. The brief might
underspecify ① how to handle non-UTF-8 input (binary files, unknown
encodings); ② the exact exit-code mapping for the 3 input-resolution
branches; ③ whether the body should preserve input bytes verbatim or be
allowed a header (which affects sha256 tamper detection); ④ whether the
default tag should be hardcoded or canon-driven; ⑤ the soft L10 lint check
severity (LOW vs MEDIUM). This craft answers each under implementation
pressure and locks the answers as decisions.

**The intended outcome**: a working `myco inlet` verb that ① ships under
the zero-non-stdlib-deps contract, ② passes all 19 lint dimensions, ③ has
5 seed tests covering the load-bearing paths, ④ is wired into cli.py with
the standard subparser pattern, ⑤ is contract-bumped to v0.27.0 with
template mirroring, ⑥ does NOT solve any of the 4 open_problems §1-4
sub-problems (those are explicitly out of scope per Wave 34 §2.4).

## 1. Round 1 — Implementation pressure validation

Wave 34's design was specified at §3.1 as a 10-item brief. Round 1 walks
each item, identifies what the design underspecified, and locks an answer.

### 1.1 Item 1 — Canon edits (kernel + template mirrored)

Wave 34 §3.1 said: "v0.26.0 → v0.27.0 (kernel + template mirrored), add
4 inlet_* optional_fields, add inlet to valid_sources, new inlet:
sub-section with default_tag: 'inlet'."

**Underspecified**: where in the schema layout does the new `inlet:`
sub-section go? After `compression:` (the most recent addition) or
elsewhere? Does it sit at `notes_schema.inlet` or `inlet:` at the top
level of `system:`?

**Decision (D1)**: The `inlet:` sub-section sits at `system.notes_schema.inlet`
(NOT `system.inlet`). Rationale: it controls a notes-domain default
(default tag for inlet notes), so it semantically belongs under
`notes_schema`. Alternative locations would require either a new top-level
key (which spreads the notes-domain config across two places) or burying
it inside `notes_schema.optional_fields` (which conflates "what fields
exist" with "what defaults apply"). The decision matches Wave 30's
placement of `compression:` under `notes_schema`.

### 1.2 Item 2 — `notes.py` `VALID_SOURCES` + `OPTIONAL_FIELDS` extension

Wave 34 §3.1 said: "Add `inlet` to VALID_SOURCES; extend OPTIONAL_FIELDS
with the 4 inlet_* fields."

**Underspecified**: should the 4 inlet_* fields be enforced as required
when source=='inlet', or kept fully optional?

**Decision (D2)**: Fully optional in `OPTIONAL_FIELDS` (no hard requirement).
The soft enforcement happens in L10 lint with severity LOW. Rationale:
treating them as required would break grandfathering — any pre-Wave-35
note retroactively retagged source=='inlet' would fail L10 hard. The Wave
20 silent-fail elimination doctrine requires sensors to fail loud, but
this is the inverse: we explicitly want a soft warning so the sensor
surfaces the gap without blocking.

### 1.3 Item 3 — `inlet_cmd.py` (~200 LOC, 3 functions)

Wave 34 §3.1 said: "`_resolve_inlet_input` / `_build_inlet_meta` /
`run_inlet`."

**Underspecified**: ① the exact exit-code mapping for the 3 input-resolution
branches (file/explicit/URL); ② whether `_resolve_inlet_input` should be
permissive or strict on edge inputs (path vs URL ambiguity, e.g.
`./https-config.md` is a file path that starts with `https`); ③ whether
URL form should error at `argparse` time or inside `_resolve_inlet_input`.

**Decision (D3)**: Exit codes locked to:
- `0` — success
- `2` — usage error (missing/conflicting args, URL form rejected, partial
  --content/--provenance pair)
- `3` — input validation error (file not found, file not regular, file
  not UTF-8)
- `5` — io error (cannot resolve project root, cannot write notes/)

This mirrors `compress_cmd.py` exit codes 0/2/3/5 (compress also uses 4
for "empty cohort", which has no inlet equivalent because inlet always
produces exactly one note).

**Decision (D4)**: URL detection is **prefix-based** (`startswith("http://", "https://")`)
and happens inside `_resolve_inlet_input`. Edge case `./https-config.md`
is correctly handled because the positional `source` is checked
`startswith("http://", "https://")` first; a relative path starting with
`./` does not match. (The path `https-config.md` without `./` would
falsely match — but this is acceptable because the operator can disambiguate
with `./https-config.md` per shell convention. Filed as L7 known limitation.)

**Decision (D5)**: `_resolve_inlet_input` is the single source of truth
for input resolution. argparse does NOT pre-reject any form. Rationale:
keeping the resolution logic in one place makes it testable in isolation
without spinning up a full argparse parser, and means the URL-form error
message (which must be informative — see D7) lives next to the rejection
logic.

### 1.4 Item 4 — `cli.py` `inlet_parser` subparser

Wave 34 §3.1 said: "`myco inlet [<source>] [--content STR] [--provenance STR]
[--tags T1,T2] [--project-dir DIR] [--json]`."

**Underspecified**: should the positional `source` be mutually exclusive
with `--content` at the argparse level (via `add_mutually_exclusive_group`),
or handled at runtime by `_resolve_inlet_input`?

**Decision (D6)**: Handled at runtime by `_resolve_inlet_input`. Rationale:
argparse mutually-exclusive groups produce error messages that are not
operator-friendly ("argument --content: not allowed with argument source");
runtime resolution can produce a curated error message that points
operators at the agent-fetch pipe pattern. Per the Wave 34 D2 zero-deps
doctrine, the error message is part of the operator-deferred contract:
the kernel must tell the operator where to go next, not just what they
did wrong.

### 1.5 Item 5 — L10 soft inlet check

Wave 34 §3.1 said: "extend L10 (notes schema) to softly enforce: when
source==inlet, the 4 inlet_* fields SHOULD be present (warn, not error)."

**Underspecified**: severity level.

**Decision (D7)**: Severity LOW. Rationale: ① MEDIUM would aggregate
into the lint summary count and trigger operator concern; ② LOW signals
"this is a hint, not a violation"; ③ existing L10 patterns use MEDIUM
for actual schema violations (invalid status, invalid source) — using
LOW preserves the distinction between "the schema is wrong" (MEDIUM)
and "the schema is right but provenance is missing" (LOW).

### 1.6 Item 6 — Test file

Wave 34 §3.1 said: "`tests/unit/test_inlet.py` (NEW, 4-5 tests)."

**Underspecified**: which 4-5 tests, exactly?

**Decision (D8)**: 5 tests, each guarding a load-bearing Wave 34 design
decision:
- `test_inlet_file_creates_raw_note_with_provenance` — file form D1 + D3
  + D4 + provenance contract D6
- `test_inlet_explicit_content_creates_raw_note` — D2 zero-deps URL pipe
  pattern + auto-detect agent-fetched URL provenance (URL provenance →
  method url-fetched-by-agent; non-URL → explicit-content)
- `test_inlet_url_form_rejected_with_clear_message` — D2 reject branch +
  error-message UX contract (must point at agent-fetch pipe pattern)
- `test_inlet_default_tag_applied_when_tags_missing` — D6 canon-driven
  default tag, both fallback and canon-extended paths
- `test_inlet_lints_clean_under_l10` — soft check produces zero issues
  on freshly-inletted notes (validator/writer agreement contract)

5 not 4 because the URL-rejection branch and the lint-clean check are
both load-bearing and orthogonal — collapsing either into another test
would weaken the regression sensor.

## 2. Round 2 — Attack surface

### 2.1 Attack A — "Why ship URL fetching as operator-deferred when most
operators will want it?"

**Counter**: Because the kernel has a hard zero-non-stdlib-deps contract.
Adding `requests` or `httpx` would break that. Using `urllib.request`
would work but introduce 100+ LOC of error handling for SSL, redirects,
timeouts, retries, content-type sniffing, encoding detection — each of
which has security implications. The **agent wrapper** pattern (Claude
WebFetch + `myco inlet --content STR --provenance URL`) inherits all of
that error handling from the agent's existing HTTP stack and keeps it
out of the kernel attack surface.

**Verdict**: Defended. URL form remains rejected with a clear instruction
pointing at the agent-fetch pipe pattern. The error message tells
operators *what to do next*, not just *what they did wrong*.

### 2.2 Attack B — "What if the operator pastes binary content via
`--content`? Or a file with non-UTF-8 encoding?"

**Counter**: Two cases:
1. **Binary file (positional source form)**: `_resolve_inlet_input`
   reads via `path.read_text(encoding="utf-8")`, which raises
   `UnicodeDecodeError`. Caught and re-raised as `ValueError` with a
   stderr-grade message: "the Metabolic Inlet kernel only handles text.
   Convert binary content externally before inlet." Exit code 3 (input
   validation error).
2. **Binary string via `--content`**: argparse already disallows
   non-string arguments (it'd fail at `argparse` level with a Python
   `TypeError` that bubbles up). In practice, operators pasting binary
   into a shell would hit shell-encoding issues first. Filed as L4
   known limitation.

**Verdict**: Defended for case 1. Case 2 is filed as a known limitation.
The kernel is text-only by design — binary preprocessing (OCR for PDFs,
transcripts for audio, captions for video) happens in agent wrappers
before content reaches `myco inlet`.

### 2.3 Attack C — "The 5-test suite is too small for a kernel_contract
landing. Wave 30 had 7 tests, Wave 33 had 3. Why 5?"

**Counter**: Test count is not the right metric. The right metric is
**load-bearing path coverage**. Wave 35 has exactly 5 load-bearing paths:
file form, explicit form, URL rejection, default tag fallback, lint
agreement. Adding more tests would either ① test paths that aren't load-
bearing (e.g. exit code 5 when notes/ is unwritable — that's an io_utils
contract test, not an inlet test); or ② duplicate coverage of existing
paths.

Wave 30's 7 tests covered: compress with audit, dry-run no-write, cascade
rejection, idempotent empty cohort, L18 lint orphan, uncompress roundtrip,
uncompress broken backlink. Each of those is a distinct decision boundary.
Wave 35's 5 tests follow the same per-decision rule — there are 5 such
boundaries in Wave 34 §3.1's brief, so 5 tests.

**Verdict**: Defended. Test count is calibrated to load-bearing paths,
not to any external benchmark.

### 2.4 Attack D — "Why is `_build_inlet_body` allowed to add a header?
Doesn't that break sha256 tamper detection?"

**Counter**: The sha256 hash is computed over `content` (the input bytes),
NOT over the rendered note body. The header is metadata for human
readability via `myco view`, not part of the cryptographic chain. A
verifier checking tamper would extract `inlet_origin` + `inlet_method` +
`inlet_content_hash` from frontmatter, re-fetch the original via the
agent, sha256 it, and compare. The body's header doesn't enter that
calculation.

If a future operator demands "the body must be byte-identical to the
input", that's a separate doctrine question and would supersede D9 below.
Filed as L5 limitation.

**Decision (D9)**: Body MAY include a header. sha256 is over input bytes,
not body bytes. Verifiers MUST re-derive sha256 from the original source,
not from the note body.

**Verdict**: Defended. The cryptographic chain is intact; the body
rendering is presentation, not provenance.

### 2.5 Attack E — "Why does `_resolve_default_tag` read canon at call
time instead of import time?"

**Counter**: Test fixtures need to swap canon between tests. Reading
canon at import time would freeze the value at the first call and break
parameterized tests. The performance cost is negligible (one YAML parse
per inlet invocation, on a single-file canon < 10 KB).

**Verdict**: Defended. Call-time canon reads are the standard pattern in
`compress_cmd._project_root` and `notes_cmd._project_root`. Wave 35
follows the same pattern.

### 2.6 Attack F — "The L10 soft check at severity LOW will be invisible
in lint output by default. What's the point of having it if no one sees it?"

**Counter**: LOW issues are visible in `myco lint` output (they're listed
under the LOW section). The Wave 33 dogfood pattern showed that LOW
signals get noticed during routine substrate hygiene runs. Operators who
care about provenance integrity will see them; operators who don't will
ignore them. That's the intended balance.

If retroactive provenance becomes a real concern (e.g. an audit demands
all inlet notes have full provenance), the severity can be bumped to
MEDIUM in a future wave. Wave 35 ships at LOW because there are zero
pre-existing source=='inlet' notes (the source was added in this same
wave), so the soft check has nothing to fire on.

**Verdict**: Defended. LOW is the correct opening severity for a check
that has nothing to fire on yet.

## 3. Round 3 — Lock decisions and verify the landing

### 3.1 Decision lock summary

D1 — `system.notes_schema.inlet` (NOT `system.inlet`)
D2 — `OPTIONAL_FIELDS` not `REQUIRED_FIELDS` (soft enforcement only)
D3 — Exit codes 0/2/3/5
D4 — URL detection prefix-based, edge-case operator-disambiguated via `./`
D5 — `_resolve_inlet_input` is single source of truth for input resolution
D6 — Mutual exclusion handled at runtime, not argparse
D7 — L10 severity LOW
D8 — 5 tests, one per load-bearing path
D9 — Body MAY include header; sha256 over input bytes only

### 3.2 Landing verification

Pre-commit verification matrix (must all be GREEN before commit):

1. **`PYTHONPATH=src python -m pytest tests/ -q`** — expect 22 tests (17
   pre-Wave-35 + 5 new inlet tests). All must pass.
2. **`PYTHONPATH=src python -m myco.cli lint`** — expect 19/19 dimensions
   green. L16 boot brief may be temporarily stale due to canon edits;
   regenerate via `myco hunger` and re-lint to clear.
3. **`PYTHONPATH=src python -m myco.cli hunger`** — expect Wave 35 inlet
   notes to be visible in the inventory. No new dead_knowledge signals.
4. **`git diff _canon.yaml | grep contract_version`** — expect
   `v0.26.0 → v0.27.0`.
5. **`git diff src/myco/templates/_canon.yaml | grep synced_contract_version`**
   — expect `v0.26.0 → v0.27.0` (template mirror).

### 3.3 Empirical validation (Round 3 dogfood)

The Wave 35 craft itself validates D1–D9 by being landed via the same
verb chain it implements:
- The decisions note for this craft is created via `myco eat` (not via
  `myco inlet` — inlet is for *external* content; the decisions are
  internal substrate state).
- The evidence note for this craft documents the 10-item brief
  walkthrough above.
- The substrate is dogfooded in the post-landing run of `myco lint` +
  `myco hunger` + `myco view <new-inlet-id>` to confirm the verb produces
  notes that the rest of the substrate can read, lint, and surface.

A separate one-shot `myco inlet docs/primordia/inlet_mvp_craft_2026-04-12.md`
**will** be run post-landing to dogfood the file form against a real
file in the substrate. The output will be excreted via `myco prune` (or
manually) so it doesn't pollute the knowledge graph. (The dogfood is for
the verb, not for the content.)

## 4. Conclusions

### 4.1 Decisions (canonical)

**D1** — Canon section placement: `system.notes_schema.inlet`, NOT
`system.inlet`. Rationale: notes-domain default belongs under notes_schema.

**D2** — Provenance fields are in `OPTIONAL_FIELDS`, not `REQUIRED_FIELDS`.
Soft L10 check enforces presence at severity LOW.

**D3** — Exit code mapping: 0 success / 2 usage / 3 input validation /
5 io. (No exit 4 because inlet has no "empty cohort" analog.)

**D4** — URL detection is prefix-based on positional `source` only.
Operators disambiguate file paths starting with `https-` via `./` prefix.

**D5** — `_resolve_inlet_input` is single source of truth for input
resolution. argparse does no pre-rejection.

**D6** — Mutual exclusion is runtime, not argparse, so error messages
can guide the operator at the agent-fetch pipe pattern.

**D7** — L10 soft check severity is LOW.

**D8** — Test count is calibrated to load-bearing paths (5).

**D9** — Body MAY include a header. sha256 is computed over input bytes.
Future verifiers re-derive from original source.

### 4.2 Landing list (verifiable steps)

1. `_canon.yaml`: contract_version v0.26.0 → v0.27.0, synced_contract_version
   v0.26.0 → v0.27.0, add 4 inlet_* `optional_fields`, add `inlet` to
   `valid_sources`, add new `notes_schema.inlet:` sub-section with
   `default_tag: "inlet"`.
2. `src/myco/templates/_canon.yaml`: mirror all 4 above.
3. `src/myco/notes.py`: `VALID_SOURCES` += `inlet`, `OPTIONAL_FIELDS` +=
   4 inlet_* fields.
4. `src/myco/inlet_cmd.py`: NEW file (~290 LOC), 6 functions.
5. `src/myco/cli.py`: add `inlet_parser` subparser + dispatch case.
6. `src/myco/lint.py`: extend `lint_notes_schema` with soft inlet check
   at LOW.
7. `tests/unit/test_inlet.py`: NEW file, 5 tests covering Wave 34 §3.1
   load-bearing paths.
8. `docs/contract_changelog.md`: prepend v0.27.0 entry.
9. `docs/primordia/inlet_mvp_craft_2026-04-12.md`: this craft.
10. `notes/n_*.md`: evidence note + decisions note (eaten via `myco eat`).
11. `log.md`: append Wave 35 milestone entry.
12. `docs/open_problems.md`: §1-4 status update from "fully blocked" to
    "scaffolded; deferred sub-problems remain".
13. Commit + push.

### 4.3 Known limitations

**L1** — URL fetching is operator-deferred to agent wrappers. The kernel
itself never makes HTTP requests. Acceptable per the zero-non-stdlib-deps
doctrine, but creates an integration burden on agent wrappers.

**L2** — Binary file handling is rejected at the UTF-8 decode boundary
with no preprocessing hooks. PDFs, images, and audio must be converted
externally before inlet. A future wave could add a `--encoding` argument
or a binary-to-text preprocessing pipeline, but Wave 35 keeps the
contract minimal.

**L3** — The 4 open_problems §1-4 sub-problems (cold start, trigger
signals, alignment, continuous compression) are explicitly NOT solved.
Each becomes an operator-deferred concern. Wave 36+ may revisit any of
them as friction-driven hot-fix waves.

**L4** — `--content` form does not validate that the content string is
non-empty or non-whitespace. Operators can inlet a one-character note
"x" with provenance "test"; the substrate accepts it. This is a feature
(useful for testing) and a footgun (useful for noise). Filed but not
fixed.

**L5** — Body rendering decision D9 means the note body is NOT byte-
identical to the input. Future tamper verifiers must re-derive sha256
from the original source, NOT from the note body. If a future doctrine
demands byte-identical bodies, D9 supersedes.

**L6** — Filename conflict resolution (`while id_to_filename(nid).exists():`)
is single-threaded and only handles same-second collisions. Bulk inlet
runs (e.g. 1000 files in one second) could in principle exhaust the
4-hex collision space; in practice the timestamp resolution + random
suffix gives ample margin.

**L7** — File-path edge case: a file named `https-config.md` (no `./`
prefix) would be falsely detected as a URL. Operators must use `./https-config.md`
to disambiguate. Filed as a documentation issue, not a code fix, because
the alternative (regex-based URL detection) introduces parsing overhead
for a near-zero-frequency edge case.

### 4.4 Doctrine map shift

Anchor #3 (七步代谢管道) Wave 26 coverage: 0.65 (digestion verbs landed,
compression landed, but inlet declared with no implementation).

Wave 35 raises this to ~0.80. The primitive exists, the provenance
contract is enforced, the compression chain integration is automatic via
default tag, and the 4 deferred sub-problems are documented in
open_problems.md as candidates for friction-driven follow-up.

The remaining 0.20 gap is the 4 open_problems §1-4 sub-problems. Closing
each would raise coverage by ~0.05; closing all four would put anchor #3
at ~1.00.

### 4.5 Wave 36+ trajectory

Per Wave 26 D3 (friction-driven ordering after doctrine alignment), Wave
36 is NOT pre-scoped. The next wave is determined by what surfaces as
real friction in operator dogfooding. Three candidates from Wave 34 §3.3:

1. **`hunger inlet_ripe` advisory signal** — when the inlet pile reaches
   N notes with shared default tag, hunger emits a `inlet_ripe`
   suggestion to run `myco compress --tag inlet`. Closes
   open_problems §4.

2. **Cross-reference graph for inlet provenance** — `inlet_origin` plus
   `inlet_content_hash` enables a duplicate-detection lint that catches
   the same source being inletted twice. Closes part of open_problems §3.

3. **Continuous compression hook** — operator-as-daemon pattern where
   `myco hunger` advises and `myco compress --tag inlet` executes on a
   schedule (cron, agent loop). Closes open_problems §4 fully.

Wave 36 picks one based on which surface produces friction first.
