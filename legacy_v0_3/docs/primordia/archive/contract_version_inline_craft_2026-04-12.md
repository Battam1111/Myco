---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
authors: [yanjun, claude-opus-4-6-1m]
supersedes: []
---

# Wave 40 — L21 Contract Version Inline Consistency

**Purpose**: Add a new lint dimension `L21 Contract Version Inline Consistency`
that enforces forward-looking "current contract version" claims in narrative
surfaces match `_canon.yaml::system.contract_version`. Closes Wave 37 D7
followup #3, the third (and final) Wave 39+ candidate per Wave 26 D3
friction-driven ordering. Sister to Wave 38 L19 (dimension count consistency)
and Wave 39 L20 (translation mirror consistency) — together the three
dimensions close the substrate's three highest-leverage silent-rot scar
classes in the user-facing first-impression layer.

## §0 — Problem definition

### 0.1 What fired this wave

While re-reading `MYCO.md` after the Wave 39 landing to verify L20 cleanliness,
the agent discovered that **MYCO.md lines 4 and 159 still claim
"kernel contract v0.28.0"** while `_canon.yaml::system.contract_version`
is `v0.30.0`. The drift accumulated silently across two consecutive
contract bumps:

- Wave 38 (v0.28.0 → v0.29.0): bumped lines 110 and 136 of MYCO.md, but
  missed lines 4 and 159 (the header bullet + Phase ② tracker tail).
- Wave 39 (v0.29.0 → v0.30.0): bumped lines 110 and 136 again, but again
  missed lines 4 and 159.

L17 (contract drift, Wave 24) caught the `synced_contract_version` →
`contract_version` mismatch, but ONLY between the two YAML keys — it has
no eyes on inline narrative claims. L19 (Wave 38) catches dimension count
drift but uses pattern matching on "N-dimension" / "L0-LN" / "N%2FN"
forms, NOT version strings. L20 (Wave 39) catches structural skeleton
drift between locale READMEs but is structure-blind to in-prose version
strings. **The version-inline scar class had zero immune coverage**, and
the proof is that the home repo's own MYCO.md was carrying stale version
claims after two consecutive waves of "narrative surface bump" sweeps.

This is exactly the friction Wave 37 D7 followup #3 was reserved for.
The Wave 26 D3 friction-driven ordering (post-friction-as-exception
clarification in Wave 37) places it as the third + final candidate from
the original Wave 37 batch. Waves 38 (L19) and 39 (L20) closed #1 and #2;
Wave 40 closes #3 and consumes the Wave 37 followup queue.

### 0.2 The scar class L21 catches

**Forward-looking current contract version claims** that drift away from
the canonical `_canon.yaml::system.contract_version` SSoT.

Examples (all CURRENTLY in the substrate, all CURRENTLY drifted):

```
MYCO.md:4    > **知识系统**：Myco v0.2.0（…；kernel contract v0.28.0）
MYCO.md:22   **当前阶段**：…，kernel contract v0.28.0）
MYCO.md:159           · 当前 contract                    v0.28.0 (Wave 36)
docs/adapters/README.md:14   In the current pre-release (… kernel contract v0.28.0), …
```

Note that `MYCO.md:159` contains `(Wave 36)` — that looks like a historical
marker but is actually a forward-looking claim ("the current contract is the
one Wave 36 last bumped to"). The author used a wave-number tag for
provenance but did not bump the version when a later wave landed. So
"Wave N" alone is NOT a sufficient skip signal — the rule must be tighter.

### 0.3 Out of scope (deliberately)

- **Package version `__version__` / pyproject.toml**: independent SemVer line
  (Wave 8 re-baseline doctrine). The package version 0.2.0 is allowed to
  diverge from contract version v0.30.0 because they advance on different
  cadences. L21 does NOT check this.
- **Append-only history surfaces**: `log.md`, `docs/contract_changelog.md`,
  `docs/primordia/*.md`, `notes/*.md`, `examples/ascc/**`. These are
  immutable per Hard Contract #2 — version mentions in them are historical
  facts about past states, never current claims. L21 does NOT scan them.
- **Genuine historical mentions in active surfaces**: lines like
  `Phase 1 完成 (v1.0.0)` or `Wave 24 — L17 (v0.23.0)` describe a past
  landing event and must NOT be flagged. L21 uses a positive-pattern + skip-
  pattern combination to filter these out (see §1.2).
- **Semantic alignment check**: L21 only verifies the version *string*
  matches canon. It does NOT verify the surrounding prose accurately
  describes what the contract version contains (that is human review
  territory).

## §1 — Round 1: Design

### 1.1 SSoT

`_canon.yaml::system.contract_version` is the single source of truth.
After Wave 17 contract drift lint (L17), `_canon.yaml::system.contract_version`
== `_canon.yaml::system.synced_contract_version` is invariant for the
home-repo case (Myco's substrate is its own kernel). L21 reads
`contract_version` and compares against narrative surfaces.

### 1.2 Detection algorithm

**Step 1**: For each scanned file, walk lines.

**Step 2**: Match lines against the **forward-looking pattern**:
```
re.compile(r"(?i)(kernel contract|当前\s*contract|current contract)\s*[:：]?\s*(v?\d+\.\d+\.\d+)")
```
This catches "kernel contract v0.X.Y", "当前 contract v0.X.Y",
"current contract: v0.X.Y" with optional colon/whitespace tolerance.

**Step 3**: For each match, apply **historical-marker filters** to determine
whether the match is a current claim (check) or a historical reference (skip).
A line is treated as **historical** (skip) if ANY of these are true:

- The previous non-blank line contains the literal `<!-- l21-skip -->`
  (operator opt-out for ambiguous cases).
- The line contains a transition arrow: ` → ` between two version numbers
  (e.g. "v0.29.0 → v0.30.0" — describing a bump action).
- The line contains the word `landed`, `landing`, `落地`, `已完成` adjacent
  (within 30 chars) to the matched version (describing a past event).
- The line contains a date in parens like `(2026-04-12)` adjacent to the
  matched version (timestamping a past event).
- The line is inside a fenced code block (parser is fence-aware like L20).
- The line is a markdown table row (`^|`) AND the version is in a "value"
  cell (table tracking historical phases — see Phase ② tracker shape).
- The line contains `post-rebase` (Wave 8 historical mapping references).
- The line contains `supersedes` or `succeeded` (frontmatter / craft refs).

If ALL filters pass (no historical signal), treat as **current claim**.
Compare the matched version against canon. If different, emit issue.

**Step 4**: For each current-claim mismatch, emit one HIGH or MEDIUM issue
per the severity matrix (§1.4).

### 1.3 File allowlist

**HIGH severity** (user-facing first-impression surfaces):
- `MYCO.md`
- `README.md`
- `README_zh.md`
- `README_ja.md`

**MEDIUM severity** (developer/contributor surfaces):
- `docs/adapters/README.md`
- `CONTRIBUTING.md`
- `docs/architecture.md`
- `docs/vision.md`
- `docs/theory.md`

**Not scanned** (append-only or out of scope):
- `log.md`, `docs/contract_changelog.md` (append-only)
- `docs/primordia/**` (append-only)
- `notes/**` (append-only)
- `examples/ascc/**` (immutable example snapshot)
- `wiki/**` (no current-version claims expected)
- `src/**`, `tests/**`, `scripts/**` (Python sources — version drift here
  is package version `__version__`, not contract version, and is governed
  by pyproject.toml, not canon)
- `_canon.yaml`, `src/myco/templates/_canon.yaml` (the SSoT itself)

### 1.4 Severity matrix (D4 mirror)

| Surface class | File | Severity |
|---|---|---|
| Entry point | `MYCO.md` | HIGH |
| Locale READMEs | `README*.md` | HIGH |
| Adapters / contrib | `docs/adapters/README.md`, `CONTRIBUTING.md` | MEDIUM |
| Doctrinal | `docs/architecture.md`, `docs/vision.md`, `docs/theory.md` | MEDIUM |

### 1.5 Skip-marker semantics

`<!-- l21-skip -->` on the previous non-blank line excludes the immediately
following version mention from the check. Same shape as Wave 39 D5
`<!-- l20-skip -->`. Operators use this for:
- Ambiguous lines where the historical-marker auto-detection cannot decide
- Lines that intentionally reference an older version for documentation
  (e.g. "the v0.5.0 lint had only 5 dimensions")
- Test fixtures and examples that need a specific version for clarity

The marker is conservative — it only suppresses ONE following match, not
the rest of the line and not subsequent lines.

## §2 — Round 2: Attacks

### Attack A — "False positives on historical Phase tracker"

The MYCO.md Phase ② tracker (lines 153-159) contains many lines like:
```
· Upstream Protocol v1.0 (L12)    ✅ contract v0.2.0 (2026-04-11, post-rebase 映射)
```
These contain "contract v0.2.0" but are append-only historical landing
records. If L21 fires on them, the lint becomes useless noise.

**Defense**: The historical-marker filters explicitly handle this case:
- `(2026-04-11, post-rebase 映射)` matches the date-in-parens filter AND
  the `post-rebase` keyword filter. → skip.
- `✅` adjacent to the version is also a strong landed-marker (the white
  check mark is the substrate's "landed" UI convention).

The remaining tracker line `· 当前 contract v0.28.0 (Wave 36)` does NOT
have a date, does NOT have `post-rebase`, does NOT have ✅, and uses
"当前 contract" — exactly the forward-looking pattern. → CATCH (correct).

**Verdict**: filters survive. The Phase tracker is correctly partitioned
into "historical landing records" (skipped) and "current contract claim"
(caught).

### Attack B — "Skip-marker abuse"

An operator could spray `<!-- l21-skip -->` everywhere to silence the lint.
The lint then provides false confidence.

**Defense**: Skip markers require deliberate authoring and are visible in
git diffs. The marker exists for genuine ambiguity, not silence. We add a
SOFT countermeasure: if more than 5 skip markers exist in a single file,
the lint emits a LOW issue advising review. Hard limit not enforced;
operators retain agency.

### Attack C — "What about future inline patterns we haven't anticipated?"

The forward-looking pattern is `(kernel contract|当前 contract|current contract)`.
Future authors might write "this contract version" / "the contract is now"
/ "在 v0.30.0 的合约下" — patterns L21 doesn't catch.

**Defense**: L21 is intentionally scoped to the patterns that EXIST in the
substrate today (and have already shown drift). Adding future patterns is
a Wave 41+ extension, not a Wave 40 scope blocker. The substrate's existing
patterns are stable enough that catching them is high-leverage; speculative
pattern coverage is low-leverage. Wave 26 D3 friction-driven ordering says:
build for the friction you have, not the friction you might have.

### Attack D — "Why not require an explicit marker on every current claim?"

A purely opt-in approach (every current-claim line must have
`<!-- contract-current -->`) avoids all false positives.

**Defense**: Pure opt-in requires retroactive labeling of all existing
load-bearing surfaces, which is itself a manual sweep — exactly the kind of
manual labor Wave 38 / 39 / 40 aims to eliminate. The pattern-based approach
catches existing drift on day 1 with zero retroactive labeling. The skip-
marker is the opt-OUT escape hatch for the rare false positive case, which
is the cheaper end of the trade-off.

### Attack E — "Will the lint fire false positives on this very craft?"

This craft document is in `docs/primordia/` which is append-only and NOT
in the L21 scan allowlist. So no — L21 ignores this file by construction.

### Attack F — "What about `templates/_canon.yaml`?"

`templates/_canon.yaml` line 112 says
`# ── Craft Protocol v1 (W3, kernel contract v0.3.0) ─────`. This is a
historical landing reference inside a YAML comment, in a file that
participates in the contract bump cycle (synced_contract_version mirror).

**Defense**: `templates/_canon.yaml` is NOT in the scan allowlist. It is
the contract surface itself, governed by L17 (contract drift) for the
synced_contract_version field and by the Wave 38 SSoT for any hardcoded
LINT_DIMENSION_COUNT references. Line 112 is a comment inside the contract
file and is not a narrative-surface concern.

## §3 — Round 3: Edge cases + final shape

### 3.1 Edge cases

- **C1**: Multiple version claims on one line. The Phase tracker line
  `· 当前 contract v0.28.0 (Wave 36)` only has one. But hypothetically
  `kernel contract v0.30.0 (was v0.29.0 in Wave 38)` has two. The pattern
  matches only the FIRST occurrence per line because Python's `re.search`
  returns the first match. Sufficient — the rare two-version line is
  almost always a historical-comparison line and gets skipped via the
  `→` filter or the parenthetical phrasing.

- **C2**: Version with optional `v` prefix. `kernel contract 0.30.0` (no
  `v`) and `kernel contract v0.30.0` are both valid. The regex
  `v?\d+\.\d+\.\d+` handles both.

- **C3**: CJK punctuation. `kernel contract：v0.30.0` (full-width colon).
  The regex includes `[:：]?` to match both ASCII and full-width.

- **C4**: Allowlisted file does not exist. `docs/architecture.md` may not
  exist in greenfield projects. L21 silently skips missing files
  (no issue).

- **C5**: `_canon.yaml::system.contract_version` is missing. L21 cannot
  do its job without canon. Returns no issues (silent pass) — L0 already
  enforces canon presence, so this case is structurally impossible in a
  valid Myco project.

- **C6**: Code-fence-aware parsing. Same state machine as L20 — `## fake`
  inside a ` ```bash ` block doesn't count, neither does
  `kernel contract v0.5.0` inside a doc example. Reuses the L20 parser
  pattern conceptually but stays as a separate function (no premature
  abstraction).

- **C7**: Patterns used in the lint itself. The `lint_contract_version_inline`
  function in `src/myco/lint.py` references pattern strings as Python literals.
  `src/myco/**` is NOT in the scan allowlist, so this is harmless.

### 3.2 Final decisions

- **D1**: SSoT is `_canon.yaml::system.contract_version`. Forward-looking
  inline claims must match it. Detection: forward-looking pattern + 8-clause
  historical-marker filter (date, arrow, landed/落地, post-rebase, ✅,
  supersedes, code-fence, l21-skip marker).

- **D2**: File allowlist is explicit. 4 HIGH (entry point + 3 locale
  READMEs) + 5 MEDIUM (adapter/contrib/doctrinal). Not scanned: append-only
  history surfaces, source code, canon files themselves.

- **D3**: Permanent structural lint. Same role as L19 / L20 — runs on every
  `myco lint` invocation. Not a one-shot audit.

- **D4**: Severity = HIGH for entry-point + locale READMEs; MEDIUM for
  adapter/contrib/doctrinal surfaces. Same shape as Wave 38 D4 / Wave 39 D4.

- **D5**: Skip-marker `<!-- l21-skip -->` provides operator escape hatch
  for ambiguous cases. Same shape as Wave 39 D5 `<!-- l20-skip -->`.

- **D6**: Code-fence-aware parser. Inline `kernel contract v0.X.Y` mentions
  inside fenced blocks are NOT counted. Reuses the L20 conceptual approach
  but as a separate function (the L20 helper is shape-counting; L21 needs
  match-extracting).

- **D7**: Contract version bump v0.30.0 → v0.31.0 in `_canon.yaml`,
  `src/myco/templates/_canon.yaml`, and `docs/contract_changelog.md`.
  Minor bump (additive lint dimension).

- **D8**: 4 unit tests at `tests/unit/test_lint_contract_version_inline.py`,
  one per scar class:
  - `test_l21_clean_substrate_passes` (D1 base case)
  - `test_l21_stale_inline_caught_high` (D1+D4 principal scar)
  - `test_l21_historical_marker_skipped` (filter set base case)
  - `test_l21_skip_marker_respected` (D5 escape hatch)

- **D9**: Operational landing — fix the 3 currently-drifted MYCO.md lines
  (4, 22, 159) + the docs/adapters/README.md:14 line. These are exactly
  the scars that justify L21's existence; closing them in the same wave
  proves the lint is load-bearing.

## §4 — Conclusion

### 4.1 Decisions D1-D9

See §3.2.

### 4.2 Landing list (15 items)

1. Add `lint_contract_version_inline(canon, root)` function to
   `src/myco/lint.py` (~90 lines).
2. Add helper `_l21_is_historical_match(line, version, prev_nonblank_line)`
   that applies the 8-clause historical-marker filter set.
3. Add module-level constants `_L21_HIGH_FILES` and `_L21_MEDIUM_FILES`
   tuples encoding the file allowlist (D2).
4. Add module-level constant `_L21_SKIP_MARKER = "<!-- l21-skip -->"`.
5. Append `("L21 Contract Version Inline Consistency",
   lint_contract_version_inline)` to `FULL_CHECKS` tuple — auto-extends
   `len(FULL_CHECKS)` 21 → 22 (Wave 38 D2 SSoT discipline).
6. Bump `src/myco/lint.py` header docstring `21-Dimension` →
   `22-Dimension`, add L21 row to dimension table.
7. Bump `src/myco/immune.py` docstring 21→22, add L21 bullet, add
   `lint_contract_version_inline` to imports + `__all__`.
8. Bump `src/myco/mcp_server.py` 4 surfaces (header, title, full
   enumeration in tool docstring, mode label `full (L0-L20)` →
   `full (L0-L21)`).
9. Bump `src/myco/cli.py` `replace_all` `21-dimension` → `22-dimension`
   (immune scan help text + Wave 29 comment).
10. Bump `_canon.yaml` `contract_version: "v0.30.0"` → `"v0.31.0"` +
    `synced_contract_version` mirror.
11. Bump `src/myco/templates/_canon.yaml` `synced_contract_version` mirror.
12. Bump 15+ narrative surfaces 21-dim/L0-L20 → 22-dim/L0-L21
    (badge: 21%2F21 → 22%2F22, prose: 21 维 → 22 维, etc.). L19 dogfoods
    this transition — same anti-rot mechanism Wave 38 / 39 used.
13. **Fix the 4 currently-drifted contract version inline claims** (D9):
    - `MYCO.md:4` `kernel contract v0.28.0` → `v0.31.0`
    - `MYCO.md:22` `kernel contract v0.28.0` → `v0.31.0`
    - `MYCO.md:159` `当前 contract v0.28.0 (Wave 36)` →
      `v0.31.0 (Wave 40)`
    - `docs/adapters/README.md:14` `kernel contract v0.28.0` → `v0.31.0`
14. Add `tests/unit/test_lint_contract_version_inline.py` with 4 tests (D8).
    Suite count advances 30 → 34.
15. Append v0.31.0 entry to `docs/contract_changelog.md`. Append Wave 40
    milestone to `log.md` (5-point format mirroring Wave 39). Run
    `myco lint` → expect 22/22 PASS. Run `pytest tests/ -q` → expect 34/34
    PASS. Run `myco hunger` to refresh boot brief. Eat + integrate decisions
    note. Commit `[contract:minor] Wave 40 — L21 contract version inline
    lint (v0.31.0)` + push.

### 4.3 Known limitations (honest)

- **L1**: The pattern `(kernel contract|当前 contract|current contract)`
  is closed-set. Future authors might write the claim in a form L21 doesn't
  match (e.g. "the contract is at v0.X.Y"). Wave 41+ can extend the
  pattern; the substrate as it exists today uses only the patterns L21
  catches.

- **L2**: The 8-clause historical-marker filter is heuristic. A line that
  looks historical to a human but lacks every keyword in the filter will
  produce a false positive. The skip-marker D5 is the escape hatch.
  Conversely, a line that looks current but contains a historical keyword
  (e.g. someone writes "kernel contract v0.30.0 landed today") will be
  silently skipped. The filter is biased toward false negatives over
  false positives — operators see fewer noise issues but might miss edge
  cases. Acceptable trade-off.

- **L3**: L21 only enforces version-string equality. It does NOT verify
  that the surrounding prose accurately describes what's in that contract
  version. "kernel contract v0.31.0 (含 Z 个 lint 维度)" must match
  z = 22, but L21 doesn't check that — L19 does, via its own pattern set.
  L21 + L19 + L20 are complementary, not overlapping.

- **L4**: The file allowlist is hardcoded. Adding `docs/onboarding.md`
  requires a code change to `_L21_HIGH_FILES` or `_L21_MEDIUM_FILES`.
  Same trade-off as L20 D1 §C7 — explicit allowlist trades flexibility
  for predictability.

### 4.4 Wave 41+ disposition

After Wave 40 lands, the Wave 37 D7 followup queue is **empty**. The
substrate's three top staleness scar classes (dimension count, locale
skeleton, version string) are all regression-testable lint dimensions.

Wave 26 D3 friction-driven ordering then re-evaluates against fresh
friction signals from the post-Wave-40 state. The candidate ordering for
Wave 41+ depends on what friction has surfaced since Wave 37 — likely
candidates include:

- **Anchor #4 (压缩即认知) coverage**: still at 0.40 per MYCO.md
  `compression_discipline_maturity`. Real `myco compress` has shipped
  (Wave 30) but `myco evaluate/extract/integrate` workflows have not yet
  run a real compression cycle on a non-trivial corpus.
- **Metabolic Inlet cold-start**: Wave 35 shipped MVP scaffold; cold-start
  + autonomous trigger + continuous compression remain open per `MYCO.md`
  Phase ② tracker.
- **Open Problem H-2** (kernel/instance separation enforcement)
- **Open Problem C-layer structural** (consciousness layer instrumentation)

These are larger primitive-introduction waves, not lint dimension waves.
Wave 41+ scope decisions belong to a fresh re-audit, not Wave 40.

### 4.5 Why this matters (one paragraph)

Wave 38 made dimension counts a single source of truth and gave it
ground-truth lint coverage (L19). Wave 39 made locale README skeletons
mirror each other and gave that mirror ground-truth lint coverage (L20).
Wave 40 makes inline contract version claims match their canonical SSoT
and gives THAT mirror ground-truth lint coverage (L21). The three waves
together close the substrate's three highest-leverage silent-rot scar
classes: numerical drift (counts), structural drift (locale skeletons),
and version-string drift (inline claims). The proof that L21 is
load-bearing is that **MYCO.md was carrying stale "kernel contract v0.28.0"
claims after Wave 38 AND Wave 39 had already swept narrative surfaces
twice** — manual sweeps demonstrably missed it. After Wave 40, every future
contract bump will surface inline drift at the lint boundary instead of
silently rotting through wave transitions. This is the Wave 26 doctrine
("system grows organically from practice but with structural guarantees")
made operational across three consecutive sub-Wave landings.
