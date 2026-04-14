---
type: craft
status: ARCHIVED
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Craft — L13 Body Schema (Wave 15, contract v0.13.0 → v0.14.0)

> Closes (partially) `docs/craft_protocol.md §7 #3` — "Body structure is
> not linted". Keeps §7 #5 (attack-depth scoring) as open problem.
> Sibling to Wave 13/14 reflex arcs: same agent-autonomous pattern, same
> dogfood discipline, but targets L13's own measurement surface rather
> than adding a new hunger signal.

## 0. Motivation — declared rounds vs actual rounds

`docs/craft_protocol.md §7 #3` is explicit: "`rounds: N` is a declaration,
not a measurement. Authors can theoretically water rounds to pass L13
without meaningful attack". The current L13 implementation in
`src/myco/lint.py` enforces only two checks on the rounds field:

1. `rounds >= min_rounds` (integer comparison against declared value)
2. `decision_class` matches `confidence_targets_by_class`

That's the full extent of body-structure verification. A craft with
`rounds: 3` in frontmatter and zero `Round N` headings in the body passes
L13 green. A craft with 50 non-whitespace chars of body content passes
L13 green. Both are exactly the hollow-craft failure mode §7 #3 warns
about, and §7 #5 flags as the honor-system ceiling for Wave 12
agent-autonomous crafts.

**Dogfood measurement** (kernel's own `docs/primordia/*_craft_*.md`, 11
crafts with `craft_protocol_version: 1`):

| craft                                    | decl | body_rounds | body_chars |
|------------------------------------------|------|-------------|------------|
| biomimetic_restructure                   |  3   |      3      |    773     |
| boot_reflex_arc                          |  3   |      3      |   1159     |
| craft_autonomy                           |  3   |      3      |    767     |
| craft_reflex                             |  3   |      3      |  19892     |
| dead_knowledge_seed                      |  2   |      2      |    623     |
| forage_substrate                         |  2   |      2      |  17445     |
| lint_ssot                                |  2   |      2      |   5981     |
| **pre_release_rebaseline**               |  2   |    **0**    |  13957     |
| session_end_reflex_arc                   |  3   |      3      |   2132     |
| upstream_absorb                          |  2   |      2      |   2958     |
| usability_positioning                    |  4   |      4      |  24327     |

Observation: 10/11 crafts already carry `Round N` headings that match
their declared count. **One legitimate exception** —
`pre_release_rebaseline` uses the style `## Attacks → Defenses` and
`## Revised Claim` instead of explicit round headings. It is the only
real craft without a clean body_rounds count, and it has 13 957 chars of
dense body. Any L13 body check MUST NOT fail it without a grandfather or
structural-style override; a check that breaks a healthy committed craft
to catch hollow ones would itself be a regression.

The hole is real (checks are purely nominal) and the dogfood sample is
large enough to calibrate (11 samples, healthy minimum 623 body chars
for a 2-round craft).

## 1. Round 1 — attack the concept

### A1 — "This just moves the Goodhart target"

**Attack**: An attacker writing a hollow craft will now stub out
`## Round 1` and `## Round 2` headings with two sentences of boilerplate
and still pass. The enforcement surface shifts from "declare rounds" to
"write round headings", but the attacker adapts trivially. L13 body
schema is security theater against adversarial authors.

**Response**: Partial accept. The goal is not perfect adversarial
resistance — §7 #5 explicitly registers attack-depth scoring as future
work. The goal is to close the **pure nominal** hole: currently an
attacker (or a rushed agent) can write a 30-char craft and pass. After
Wave 15, they must produce **structurally recognisable round sections**
and at least N × 200 non-whitespace chars of body, which raises the
effort bar enough that **accidental** hollow crafts disappear. The
transparency countermeasure from §4 of the protocol handles deliberate
adversaries; L13 body schema handles **drift by neglect**, which is the
far more common failure mode observed in Phase ② friction data.

### A2 — "The regex will overfit on English 'Round N' headings"

**Attack**: Crafts can be in Chinese, Japanese, or use alternative
structural idioms (e.g. `## §2 第一轮攻击`). A hard-coded `Round\s+(\d+)`
regex creates language bias and will false-fire on legitimate non-English
crafts.

**Response**: Accept. Detection MUST accept multiple surface forms of
"round N":

1. `Round\s+(\d+)` — English canonical
2. `第\s*([一二三四五六七八九十\d]+)\s*轮` — Chinese
3. `ラウンド\s*(\d+)` — Japanese
4. `R(\d+)` as word boundary — abbreviation (common shorthand)

Unique-number set is taken across **all** matched forms per `##` line.
Canon declares the patterns in a list so downstream instances can
localise without code change.

### A3 — "body_rounds==0 with legitimate structure must be tolerated"

**Attack**: `pre_release_rebaseline_craft_2026-04-11.md` uses
`## Attacks → Defenses` (argument-based structure) instead of round
headings. It has 13 957 chars of body and was accepted as a healthy
craft. Any body-rounds check that fires HIGH on body_rounds==0 will
retroactively break this commit. Breaking healthy committed history to
tighten a new check is a credibility-destroying regression.

**Response**: Accept, hard. Design rules:

- `body_rounds == 0 && declared > 0` → **MEDIUM** advisory only. Not
  HIGH. Nudges authors toward explicit `Round N` headings for future
  crafts, does not break existing ones.
- A new `body_schema_exempt` list in canon lets explicit exemptions be
  declared per-file (for pre_release_rebaseline and any future alternate-
  structure craft).
- Hollow-craft detection (body_chars check) fires HIGH regardless of
  body_rounds count — even alternative-structure crafts must have real
  content. Threshold N × 200 chars keeps the real crafts comfortably
  above the floor (smallest at 623 chars for N=2 well above 400).

### A4 — "Is 200 chars per round the right floor?"

**Attack**: 200 × N is arbitrary. A craft with genuinely short rounds
(e.g. 2 rounds × 150 chars each = 300 chars, honest) would fail. A
verbose craft with long prose outside the rounds (e.g. 1500-char
Motivation section, 100 chars per round) would pass.

**Response**: Partial accept. 200 is a heuristic bootstrap value. The
real signal we want is "did the attacker actually defend a position", not
"is the craft a certain size". A two-part check is closer to honest:

- **Total body chars** ≥ `min_body_chars * declared_rounds` — catches the
  truly hollow case. Default `min_body_chars` = 200.
- **Per-round body chars** (heuristic) — for each detected `Round N`
  heading, measure content between it and the next top-level heading.
  If any is < `min_round_body_chars` (default 150), emit MEDIUM. Authors
  sometimes have one dense round and one short one; this is a nudge, not
  a block.

Both thresholds live in canon and are revisable after 2-3 sessions of
friction data. §7 #6 grandfather precedent applies: bootstrap values,
calibrated later.

---

## 2. Round 2 — attack the design

### B1 — "Performance — reading every craft body on every lint"

**Attack**: Lint already reads frontmatter. Now it will also read the
full body of every craft_protocol_version:1 file on every lint run. For
kernel with 11 crafts and ~5 MB total, fine. For an instance with 100+
crafts, lint gets 10× slower.

**Response**: Accept as scale concern, defer as premature optimisation.
Rationale:
- `read_file(path)` is already called for every craft in the current
  L13 loop — see `src/myco/lint.py:821`. Adding body scanning uses the
  string already in memory. Zero incremental IO cost.
- 100+ crafts is a signal to split the directory, not to skip lint.
- Cached `Path.stat()` is constant per file.

No change needed. Measurement is essentially free.

### B2 — "Per-round slicing depends on heading ordering"

**Attack**: Measuring content between `## Round 1` and `## Round 2`
assumes sequential presentation. A craft with a `## Sidebar` between
rounds, or with `## Round 1` far below `## Conclusion`, will produce
nonsense slices. This is why docs are hard to lint structurally.

**Response**: Accept. Simplify to: for each **unique round number** R,
count total chars in any `## Round R` section regardless of ordering,
and use the **sum** across all rounds for `total_body_chars`. Per-round
slice is just "content from this heading to the next `##`". Sidebar or
out-of-order rounds will produce slightly lower slice counts, but the
**total** is unaffected. Since total-body check is HIGH and per-round
check is MEDIUM, the ordering weakness only affects the soft nudge, not
the hard block.

### B3 — "Regex approach misses nested rounds in sub-headings"

**Attack**: Some crafts structure rounds as `### A.1 Round 1 Attack`
instead of `## Round 1`. Using `^##` only misses these.

**Response**: Tighten scope intentionally. Only top-level `^## ` headings
count as round anchors. Sub-headings are attack/defense **within** a
round, not rounds themselves. Authors who want L13 credit for N rounds
must elevate round boundaries to top-level. This enforces a consistent
outline shape across crafts and makes hollowness measurement possible at
all.

### B4 — "Severity asymmetry risks the Wave 14 asymmetry lesson"

**Attack**: Wave 14 was the first craft to introduce deliberate LOW
severity for W5 drift. Now Wave 15 is going to sprinkle HIGH (total body)
and MEDIUM (per-round, body_rounds==0) all over L13. That's **three
different severity tiers** in one lint dimension. The severity semantics
become muddled.

**Response**: Accept, with clarification. Severity semantics per L13
body sub-check:

- **HIGH** — body_chars < floor (truly hollow, zero-content craft)
- **HIGH** — body_rounds > 0 but < declared (frontmatter lies about
  round count when body has detectable rounds)
- **MEDIUM** — body_rounds == 0 with declared > 0 (nudge toward explicit
  headings, does not break)
- **MEDIUM** — per-round body < floor when per-round slicing succeeds
- **LOW** — (future) attack-depth heuristic scores

Table goes into craft_protocol.md §7 revision alongside Wave 15 landing
so the classification is explicit, not implicit.

---

## 3. Round 3 — attack the edges

### C1 — "What about the craft that introduces this check itself?"

**Attack**: This very craft file (`l13_body_schema_craft_2026-04-11.md`)
will be subject to its own new checks when L13 v2 runs. If the check
logic is wrong, the craft that defines the check won't pass its own
check. Recursive bootstrap problem — classic §8.7 pattern.

**Response**: Accept. This craft is intentionally written in canonical
`## 1. Round 1 — attack the concept` / `## 2. Round 2 — ...` form with
heavy body content (>5 000 chars). It must pass its own new v2 check
to be credible. Post-landing verification includes running L13 v2
against this file and confirming pass. If any of B1-B3 fire on this
file, the implementation is wrong and must be fixed before commit.
Bootstrap exemption is NOT used for this file — the whole point is to
eat our own dog food.

### C2 — "What if the check produces zero findings across all existing
kernel crafts?"

**Attack**: Dogfood audit shows 10/11 existing crafts already pass
body_rounds == declared. The one exception (`pre_release_rebaseline`)
will be handled by MEDIUM nudge and/or explicit exemption. So the new
check will produce zero HIGH findings on landing. A check that never
fires is hard to distinguish from a check that doesn't work.

**Response**: Accept as verification discipline. Landing plan MUST
include an inline test — a synthetic hollow craft written to a temp
file that triggers HIGH, then torn down. This is done in the dogfood
harness, not committed. Proves the check works without polluting
history.

### C3 — "Grandfather list maintenance burden"

**Attack**: `body_schema_exempt: [pre_release_rebaseline_craft_2026-04-11.md]`
in canon now requires maintenance. Future alt-structure crafts add
entries. This creates a small permanent tax.

**Response**: Accept the tax. Alternative is silently grandfathering any
craft with body_rounds==0, which removes the nudge signal. Tax is small
(one list entry per exception, one line per) and explicit is better than
implicit. Instance-side exemption lists are per-project, not
contaminating kernel canon.

### C4 — "Contract version bump vs patch"

**Attack**: Is this minor (new canon fields + new checks) or patch (L13
behavior change)? The protocol is clear on MAJOR/MINOR/PATCH but not on
"add sub-checks under an existing lint ID".

**Response**: MINOR. Reasoning: the check adds new canon schema
(`body_schema` subkey under `craft_protocol`), new required behavior
(body measurement), and a potential new HIGH finding (hollow crafts).
Downstream instances may see new findings after upgrading. This matches
the MINOR semantics ("backward compat + new behavior that may surface
new findings"). Bump v0.13.0 → v0.14.0. Downstream will fire Wave 13
`contract_drift` HIGH on next boot (the designed propagation path).

---

## 4. Decisions (D1–D9)

- **D1 — New canon sub-block** `system.craft_protocol.body_schema` in
  both `_canon.yaml` and template:
  ```yaml
  body_schema:
    enabled: true
    min_body_chars_per_round: 200
    min_round_body_chars: 150   # per-round slice heuristic
    round_markers:
      - 'Round\s+(\d+)'
      - 'R(\d+)\b'
      - '第\s*([一二三四五六七八九十\d]+)\s*轮'
      - 'ラウンド\s*(\d+)'
    exempt_files: []   # instance-side list of file basenames to skip
  ```

- **D2 — New helper** `_l13_body_metrics(content)` in `src/myco/lint.py`
  returning `(body_chars, unique_round_numbers, per_round_chars)`.
  Parses only `^## ` headings, applies the regex list from canon.

- **D3 — Wire into `lint_craft_protocol`** after existing frontmatter
  checks:
  - HIGH: `body_chars < declared * min_body_chars_per_round`
  - HIGH: `0 < body_rounds < declared` (when body_rounds detectable)
  - MEDIUM: `body_rounds == 0 and declared > 0` (nudge)
  - MEDIUM: per-round slice < `min_round_body_chars` for any detected
    round
  - LOW: `exempt_files` contains the basename → skip all body checks
    but still run frontmatter checks

- **D4 — Grandfather list bootstrap**: kernel's `exempt_files` initial
  value is **empty**. `pre_release_rebaseline_craft_2026-04-11.md`
  will get a **MEDIUM** nudge, not an exemption. Rationale: MEDIUM
  does not fail lint (exit code 0), and the nudge is valuable — it
  will eventually motivate a structural retrofit. If the nudge becomes
  noisy after 2-3 sessions, the file can be exempted then.

- **D5 — Update `docs/craft_protocol.md §7 #3`**: replace "Body
  structure is not linted" with "Body structure is partially linted
  (Wave 15, v0.14.0): round heading count and body chars verified
  against frontmatter declaration; attack-depth scoring remains open
  (§7 #5 unchanged)". Record Wave 15 severity table explicitly.

- **D6 — Contract version bump** v0.13.0 → **v0.14.0** (minor).
  Kernel `contract_version` + kernel `synced_contract_version` both
  update. Downstream fires Wave 13 contract_drift HIGH on next boot.

- **D7 — Changelog entry** `v0.14.0 — 2026-04-11 (minor · L13 body
  schema, Wave 15 — partial closure of §7 #3)`.

- **D8 — Dogfood verification plan**:
  1. Implement check
  2. Run kernel lint → expect 0 HIGH (all existing crafts have body
     chars ≥ 400 and most have body_rounds == declared)
  3. Expect 1 MEDIUM on `pre_release_rebaseline` (body_rounds==0 nudge)
  4. Write synthetic hollow craft → expect HIGH → delete → lint green
  5. Run this craft file through lint → expect 0 findings
     (self-test)
  6. Commit + push

- **D9 — Template MYCO.md hot-zone** does NOT need a new bullet —
  L13 is a lint dimension, not a reflex. Existing boot/end reflex
  bullets already tell agents "lint must pass". Wave 15 tightens the
  pass criterion, not the workflow.

---

## 5. Known limitations

- **L-1 Attack-depth scoring still open** (§7 #5). Wave 15 closes the
  "declared but empty body" hole. Adversarial attackers who write N
  round headings with two-sentence body each can still pass. Attack
  quality is genuinely hard to measure (requires semantic analysis).
  Remains as open_problems.md entry.

- **L-2 Round-marker regex is bootstrap list**. Four patterns cover
  English / Chinese / Japanese / abbreviation. Other languages are
  silent failures (MEDIUM nudge, not HIGH block). Adding patterns is
  a canon-only change.

- **L-3 Per-round slicing is ordering-sensitive**. See B2 response —
  total body char check is ordering-insensitive, so the hard block
  works regardless of heading order. Slicing only affects the MEDIUM
  nudge.

- **L-4 Grandfather-via-MEDIUM is not permanent**. An attacker can
  write `body_rounds==0` forever and stay at MEDIUM. This is the
  deliberate looseness for alt-structure tolerance. If Phase ②
  friction data shows abuse, promote `body_rounds==0` to HIGH in a
  future minor.

---

## 6. Confidence

- Target: 0.90 (decision_class: kernel_contract)
- Arrived: **0.90**
- Rationale: structural parallel to Wave 13/14 reflex arcs but targets
  L13's own measurement surface. Every decision is backed by dogfood
  data on 11 real crafts. Severity table (B4) is explicit and grounded.
  Grandfather-via-MEDIUM (D4) handles the one problem file cleanly
  without special-casing. Self-test (C1) closes recursive bootstrap
  risk. Primary residual risk is L-1 (adversarial attack-depth),
  which is explicitly out of scope per protocol §7 #5. Craft clears
  target.

---

## 7. Landing checklist (Wave 15)

- [ ] Add `body_schema` sub-block to `_canon.yaml` under
      `craft_protocol`
- [ ] Sync template `_canon.yaml`
- [ ] Implement `_l13_body_metrics()` + new checks in
      `src/myco/lint.py::lint_craft_protocol`
- [ ] Bump `contract_version` v0.13.0 → v0.14.0 (both kernel +
      synced_contract_version)
- [ ] Revise `docs/craft_protocol.md §7 #3` with partial-closure note
      and severity table
- [ ] Add v0.14.0 entry to `docs/contract_changelog.md`
- [ ] `myco lint --project-dir .` → expect 16/16 green, 0 HIGH, ≤1
      MEDIUM on `pre_release_rebaseline`
- [ ] Synthetic hollow-craft smoke test (write / lint → HIGH / remove
      / lint → green)
- [ ] Self-test this craft file against new L13 (expect 0 findings)
- [ ] `myco eat` — Wave 15 conclusion note, tags wave15/l13-body-schema
- [ ] Append Wave 15 milestone entry to `log.md`
- [ ] Commit + push via host-side desktop-commander
