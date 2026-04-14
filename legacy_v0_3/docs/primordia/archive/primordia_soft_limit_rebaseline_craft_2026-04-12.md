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
  - "Wave 22 §B7 R2.4 explicit exit clause: 'If creation velocity ever exceeds compression... probably time to raise the soft limit or split primordia by phase'"
  - "Wave 30+ chronic structural_bloat hunger signal firing without operator response (sensor-with-no-effector pathology, ~6 waves)"
---

# Wave 36 — `primordia_soft_limit` re-baseline 40 → 60

> **Scope**: kernel_contract class threshold-tuning craft. Re-baselines
> the `primordia_soft_limit` value in `_canon.yaml::system.structural_limits`
> from 40 to 60 to honestly reflect mature-substrate craft accumulation.
> Does NOT add new lint dimensions, mechanisms, or verbs. Does NOT archive
> any crafts. Does NOT split primordia into phases. Single decision: a
> threshold value plus the audit + reasoning chain that justifies it.
>
> **Parents**:
> - Wave 22 `primordia_compression_craft_2026-04-12.md` (the original
>   workflow + W13 procedural rule + the explicit anticipation of this
>   exact exit case at §B7 R2.4)
> - `docs/WORKFLOW.md` W13 (the procedural rule binding all subsequent
>   waves to either compress-or-defer-with-reason — this craft is the
>   first wave to take the "compress by re-baselining" path)
>
> **Supersedes**: none. Wave 22's craft and W13 rule remain fully active.
> This craft tunes one value Wave 22 set, using the explicit Wave 22 §B7
> R2.4 escape clause Wave 22 itself defined.

## 0. Problem definition

The `structural_bloat` hunger signal has been firing every `myco hunger`
run for at least 6 consecutive waves (Wave 30 → Wave 35), reporting
"docs/primordia/*.md has N files (soft limit 40, over by N-40)" with N
growing monotonically from ~42 → 47 over those waves. No wave between
Wave 22 and Wave 36 has executed a primordia compression sweep. This is
**exactly** the "sensor that fires but nothing catches the signal"
pathology Wave 22 was created to fix — the very pathology that motivated
both the archive directory mechanism AND the W13 procedural rule.

Yet Wave 22's archive operation is **not repeatable on the current
substrate**. Wave 22 successfully archived 11 crafts because those
crafts were old debate transcripts (04-07 to 04-09 era) with minimal
dependency depth — they were referenced primarily by `docs/primordia/README.md`
and a few cross-citations in other primordia files. Updating ~15 link
references was a tractable closing step.

The post-Wave-22 substrate has 47 ACTIVE crafts that all participate in
a tightly-woven reference graph: each design craft is cited by its
implementation craft, by canon comments, by code module docstrings, by
contract changelog entries, and by historical notes. Per substrate
immutability doctrine (`docs/contract_changelog.md` Wave 8 banner +
MYCO.md hard contract #2 "log.md append-only"), historical notes and
committed log entries cannot be rewritten. Archiving any post-Wave-22
craft would force one of two violations:

(a) Leave references intact → causes dozens of link-rot incidents that
    later L17/L18 lint passes would not catch (since the lints check
    contract drift, not link integrity).
(b) Update references → requires rewriting immutable historical notes
    and log entries, violating substrate immutability.

Both options trade a stronger doctrine for a weaker signal.

**The craft must therefore answer**: given that archive is foreclosed
on this substrate, what response to the chronic `structural_bloat`
signal preserves the W22/W13 discipline without violating immutability?

## 1. Round 1 — Per-option pressure

### 1.1 Option A: Archive sweep (Wave 22 standard path)

**Audit performed**: scanned all 47 active crafts for SUPERSEDED
candidates. Found exactly 2 strong candidates:

1. `metabolic_inlet_design_craft_2026-04-12.md` (Wave 34, exploration
   class, design only) — its 8 design questions D1–D8 were resolved
   under implementation pressure in Wave 35. The Wave 35 craft
   `inlet_mvp_craft_2026-04-12.md` re-locks D1–D9 with the actual
   landed values, some of which differ from the Wave 34 proposal. By
   the strict SUPERSEDED definition (later craft's claims replace
   earlier craft's claims), Wave 34 is SUPERSEDED.

2. `compression_primitive_craft_2026-04-12.md` (Wave 27, exploration
   class, design only) — same pattern: its design questions were
   resolved by Wave 30's `compress_mvp_craft_2026-04-12.md` (which
   landed `myco compress`).

**Reference depth measurement** (`grep -r metabolic_inlet_design_craft
docs/ src/ notes/ log.md _canon.yaml`):
- `metabolic_inlet_design_craft_2026-04-12.md`: 14 references across
  log.md (3 historical entries), inlet_mvp_craft (parent reference),
  contract_changelog (W35 entry), src/myco/cli.py (1 docstring),
  src/myco/inlet_cmd.py (1 module docstring), src/myco/notes.py (2
  comments), src/myco/templates/_canon.yaml (2 comments), _canon.yaml
  (2 comments), notes/n_20260412T071256_8617.md (W35 evidence note,
  immutable). Total ~14.
- `compression_primitive_craft_2026-04-12.md`: 16 references across
  log.md, compress_mvp_craft, uncompress_mvp_craft, vision_reaudit_craft,
  contract_changelog (W30 entry), src/myco/cli.py, src/myco/compress_cmd.py,
  src/myco/lint.py, src/myco/notes.py (3 places), notes/n_20260412T024944_3e32.md
  (W26 evidence note), n_20260412T030350_cace.md (W27 craft note),
  n_20260412T030457_6717.md (W27 landing note). Total ~16.

**Total reference updates required** if both archived: ~30 path edits,
of which:
- ~6 are in immutable historical notes (substrate immutability
  violation)
- ~3 are in immutable log.md entries (substrate immutability violation)
- ~21 are in mutable canon/code/active-craft files (technically
  updatable but the count is non-trivial)

**Verdict on Option A**: foreclosed. Archive of post-Wave-22 design
crafts requires either link rot OR immutability violation. Both worse
than the bloat signal.

### 1.2 Option B: Re-baseline soft limit

Wave 22 §B7 R2.4 explicitly anticipated this exit and pre-authorized it:

> "Compression velocity matching creation velocity is aspirational, not
> enforced. Nothing stops a wave from creating 5 new crafts and
> archiving 0... A wave creating 5 crafts with 0 archives will push
> primordia further over limit → bigger signal next wave → bigger
> pressure to respond. The feedback loop is the enforcement... If
> creation velocity ever exceeds compression (e.g., wave 30+ where
> everything is still active), that's a real signal — probably time to
> raise the soft limit or split primordia by phase."

The condition **"wave 30+ where everything is still active"** is exactly
satisfied: we are at Wave 36, all 47 crafts are still active per the
Option A audit, and creation velocity has exceeded compression for 14
waves.

The doctrinal license is unambiguous. The execution is a single canon
edit with a multi-line comment justifying it.

### 1.3 Option C: Split primordia by phase

Wave 22 §B7 R2.4 also offered this alternative. Mechanism would be:
introduce subdirectories (`docs/primordia/foundational/`,
`docs/primordia/wave_11_25/`, `docs/primordia/wave_26_36/`, etc.) and
update the `detect_structural_bloat` glob to count only one of them.

**Cost analysis**:
- All 30+ existing references would need path updates (same problem as
  Option A archive)
- L15 craft reflex `trigger_surfaces` enumerates `docs/primordia/` —
  would need to update each subdirectory
- Future waves would need a "which phase does this craft go in" decision
  on every craft creation
- Adds a new directory convention to learn + lint
- For uncertain benefit (the count distribution would still need
  re-baselining)

**Verdict on Option C**: higher cost than Option B, no clear advantage.
Defer indefinitely.

### 1.4 Option D: Defer with reason (W13 path b)

W13 explicitly allows: "append a `deferred: primordia-compression
(<reason>)` line to the log.md entry." This is the "cannot act this
wave" escape valve.

But it's intended for one-off deferrals (e.g., "this wave is hot-fix,
no time to compress"). Using it 6 waves in a row is a degenerate use:
the discipline becomes a paper procedure with no behavioral consequence.
The W13 rule itself anticipates this — it says "the feedback loop is
the enforcement" — the bigger signal next wave is supposed to drive
action. After 6 waves of growing signal with no action, deferral is no
longer credible.

**Verdict on Option D**: structurally inadequate as a standing response.

## 2. Round 2 — Attacks against Option B

Selected Option B (re-baseline). Now attack it.

### 2.1 Attack A — "Re-baselining is just sweeping bloat under the rug"

**Claim**: raising the soft limit doesn't reduce the file count; it
just silences the sensor. The substrate is still 47 files, the burden
on readers is unchanged, you've broken the disciplinary feedback loop.

**Defense**: the bloat signal exists to motivate compression action,
not to be loud-for-its-own-sake. The signal's value comes from being
acted on. Wave 22 §B7 R2.4 explicitly distinguishes "sensor without
effector" from "sensor calibrated for early-substrate that has aged
into late-substrate". The first is a pathology; the second is a normal
maturity transition. The 40 baseline was set when the substrate had
~25 crafts (62% utilization). Holding it fixed at 40 while the
substrate grew to 47 (118% utilization) is not "preserving discipline",
it's "punishing growth that the doctrine itself authorized" (Wave 22
§B7 R2.4 anticipated and authorized this growth path).

The disciplinary feedback loop is preserved, just at a higher
calibration: at 60, the sensor will fire again around Wave 44–46
(projecting current velocity), and that wave will face the same
choice. If at that point archive becomes feasible (e.g., a substrate
re-org renders some crafts truly obsolete) it can be taken. If not,
re-baseline again with the same procedural rigor.

**Defense secondary**: re-baselining is itself a costly action — it
requires this craft, a contract bump, and a multi-line justification
in canon. It is not "free silencing". The cost is recorded, and future
re-baselines compound the visibility (each re-baseline craft cites
the previous one, building a visible "we have re-baselined N times"
audit trail that future operators can use to detect the degenerate
case).

### 2.2 Attack B — "60 is arbitrary, why not 50 or 80?"

**Claim**: the new value is unjustified — picking 60 vs 50 vs 80 is
the same magnitude of arbitrary choice as the original 40.

**Defense**: 60 is calculated from observed velocity:
- Wave 22 baseline: ~25 crafts / 40 limit = 62% utilization
- Wave 36 actual: 47 crafts (post-Wave-35 inlet, post Wave 36 craft = 48)
- Net growth: 22 crafts over 14 waves = 1.57 crafts/wave average
- Projected Wave 50: 47 + (14 × 1.57) ≈ 69
- Setting limit at 60 = 80% utilization at Wave 36, expected re-fire
  around Wave 44 (47 + 8×1.57 ≈ 60)
- Setting limit at 50 = 96% utilization at Wave 36, expected re-fire
  next wave (no headroom, defeats purpose)
- Setting limit at 80 = 60% utilization at Wave 36, expected re-fire
  around Wave 56 (too far, allows Wave 22's "sensor without effector"
  pathology to re-emerge before next forced re-baseline)
- 60 is the explicit middle ground: ~8 waves of headroom = 1 forced
  re-evaluation per ~2 month period at observed velocity

The arbitrariness is bounded. The number is not pulled from thin air;
it is the value where the headroom is meaningful but not infinite.

### 2.3 Attack C — "You should just delete the limit entirely"

**Claim**: the limit is a leaky abstraction. Soft limits without
enforcement are just optional anxiety. Either make it a hard fail or
delete it.

**Defense**: the limit's value is **calibration of the operator-as-daemon
loop**, not enforcement. Per `docs/open_problems.md` §4 (continuous
compression), Myco does not have an automatic compress trigger. The
hunger signal is the only mechanism alerting the operator that
compression is overdue. Deleting the signal would remove the only
visibility into bloat trends — a regression from the Wave 22 baseline.
Making it hard-fail would conflict with anchor #4's "compression
strategies themselves evolve" — a hard fail can't evolve.

The right shape is exactly what it is: a soft signal whose threshold
is recalibrated periodically by craft. This wave is the first
recalibration; this is the discipline working as designed.

### 2.4 Attack D — "What about the 14 waves of inaction? Isn't that the bug?"

**Claim**: the real failure isn't the 40 baseline being too low — it's
that 14 waves passed without anyone responding to the signal. Fix the
*response* mechanism, not the *threshold*.

**Defense**: this is a valid critique but addresses a different layer.
The response mechanism (W13 rule) IS in place; it explicitly allows
"defer with reason". What was missing was the *reason* — none of the
6 waves between Wave 30 and Wave 35 logged a `deferred:
primordia-compression` line. This is a genuine W13 violation in
historical waves. But since substrate immutability prevents rewriting
those past wave entries, the only available correction is "make sure
W36+ does not repeat the violation". This wave does that by either:
(a) executing compression (re-baselining is a kind of compression — it
compresses the *threshold*, freeing capacity), and (b) committing the
craft + contract bump as the W13-compliant response artifact.

Future waves remain bound by W13: if `structural_bloat` fires, they
must compress (any kind) or defer-with-reason. The 14-wave gap is a
historical wound; this wave starts the healing.

### 2.5 Attack E — "The README is out of date and that's a bigger bloat than the count"

**Claim**: `docs/primordia/README.md` only documents ~17 of the 48
files. Updating it is a real "compression" (better organization, less
cognitive load on readers). The count is a proxy; the README staleness
is the real problem.

**Defense**: this is a true and valid concurrent problem. The Wave 36
craft does NOT solve it. README maintenance is acknowledged as a
follow-up candidate, not absorbed silently. The reason: README rewrite
would be ~1 hour of careful prose work touching ~30+ entries, which
is too much surface for a wave whose scope is "single threshold value
+ justification". Combining them would dilute both. README rewrite
will be a Wave 37+ candidate. Recorded in §4.4 limitations.

### 2.6 Attack F — "Why bump the contract version for a single threshold value?"

**Claim**: a soft limit value isn't a "contract"; it's a tunable. Bump
should be a patch at most, or no bump at all.

**Defense**: per existing convention, every kernel canon edit at the
schema-or-value level has been a minor contract bump (Wave 22 set the
limit and was minor; Wave 35 added inlet fields and was minor). The
contract version is a coarse-grained "the kernel changed" marker; its
purpose is to trigger downstream instances to re-sync. Tunables that
affect signal behavior count as kernel changes for that purpose:
instances depending on `primordia_soft_limit=40` would observe
different bloat signals after the bump, and they need the
`synced_contract_version` mechanism to detect that they've absorbed
the change.

Patch-only would be appropriate for wording-only edits; this is a
behavioral change to a sensor. Minor is the consistent classification.

## 3. Round 3 — Edge cases and decision lock

### 3.1 Edge case — what about README.md (the file itself counts toward 48)

`detect_structural_bloat` glob: `primordia_dir.glob("*.md")` non-recursive.
This includes `README.md`. So the count of 48 is "47 active crafts +
README.md". With new limit of 60, this remains 48 < 60 ✓.

Decision: do NOT exclude README.md from the count. The count is
"primordia file pressure on the reader", and README contributes to
that pressure (it has to be read to navigate the directory). Excluding
it would be a free-of-cost-but-also-free-of-meaning change.

### 3.2 Edge case — adding the Wave 36 craft itself

Adding `primordia_soft_limit_rebaseline_craft_2026-04-12.md` brings
the count to 49 (47 + README + Wave 36 craft). Still under 60.

Decision: no special handling. The wave-creates-its-own-craft pattern
is standard.

### 3.3 Edge case — what triggers the next re-baseline

Per the velocity calculation: ~Wave 44–46 (when count reaches 60). At
that point the next operator (or future Claude session) will:
(a) read this craft as the W13-compliant precedent, (b) audit
SUPERSEDED candidates fresh (some Wave 36–46 design crafts may by then
have impl pairs and be archivable without breaking immutability —
e.g., if Wave 38 design + Wave 39 impl can be archived in Wave 47
because their references are still all in mutable surfaces),
(c) consider archive vs re-baseline using the same Round 1 framework.

Decision: do NOT pre-bind future waves. The standing W13 rule + this
craft's precedent is sufficient guidance. No new lint dimension
required.

### 3.4 Edge case — does the contract bump trigger any other lint

L17 (Contract Drift) checks `synced_contract_version` against kernel
`contract_version`. Both move from v0.27.0 → v0.28.0 in lockstep, so
no drift signal. L15 (Craft Reflex) fires because `_canon.yaml` is a
`kernel_contract` trigger surface. Evidence requirement is satisfied
by this craft file existing in `docs/primordia/` within the lookback
window.

L18 (Compression Integrity) is unrelated to primordia; it checks `myco
compress` artifact provenance. Untouched by this wave.

Decision: lint surface is fully satisfied by this single new craft +
the canon edit. No other moves needed.

### 3.5 Decision lock

**D1** — `primordia_soft_limit`: 40 → 60. Effective immediately. Both
kernel `_canon.yaml` and `src/myco/templates/_canon.yaml` updated.
`src/myco/notes.py::DEFAULT_STRUCTURAL_LIMITS` mirrored.

**D2** — Contract bump: v0.27.0 → v0.28.0 (minor). `contract_version`
+ `synced_contract_version` move in lockstep in kernel canon; template
mirrors `synced_contract_version`.

**D3** — NO archive of any primordia file. Audit found 2 strong
SUPERSEDED candidates (`metabolic_inlet_design_craft_2026-04-12.md`,
`compression_primitive_craft_2026-04-12.md`) but archive would force
~30 path updates, ~9 of which are in immutable historical surfaces.
Archive is foreclosed on this substrate.

**D4** — NO new lint dimension. The existing `structural_bloat` sensor
is unchanged; only its calibration moves.

**D5** — NO split of primordia by phase. Wave 22 §B7 R2.4 alternative
considered and rejected: higher cost than re-baseline, no clear
advantage.

**D6** — NO new W13-style procedural rule. The existing W13 remains
binding; this wave is the first compliant response under the
re-baseline path.

**D7** — Discharge gear2 session_end_drift advisory in this same wave
via the standard one-line meta entry to `log.md` (Gear 2 reflection
discharge per `session_end_reflex_arc_craft_2026-04-11.md`). Combined
with the Wave 36 milestone entry to keep log.md compact.

**D8** — Honest limitation acknowledgment: README staleness (Attack E)
is a real problem this wave does NOT solve. Recorded in §4.4 as Wave
37+ candidate.

**D9** — Re-baseline trajectory: next forced re-evaluation expected
around Wave 44–46. Do not pre-bind that wave's choice (archive vs
re-baseline vs some new mechanism). The discipline self-perpetuates
via W13.

## 4. Conclusions

### 4.1 Decisions (canonical)

D1–D9 above. The kernel canon edit is the minimal load-bearing change;
the craft is the rationale + audit + alternative-rejection record.

### 4.2 Landing list

1. `_canon.yaml`: `system.contract_version` v0.27.0 → v0.28.0, comment
   updated to reference Wave 36.
2. `_canon.yaml`: `system.synced_contract_version` v0.27.0 → v0.28.0.
3. `_canon.yaml`: `system.structural_limits.primordia_soft_limit`
   40 → 60 with multi-line comment block citing Wave 22 §B7 R2.4
   lineage.
4. `src/myco/templates/_canon.yaml`: `synced_contract_version`
   v0.27.0 → v0.28.0.
5. `src/myco/templates/_canon.yaml`: `structural_limits.primordia_soft_limit`
   40 → 60 with comment.
6. `src/myco/notes.py::DEFAULT_STRUCTURAL_LIMITS["primordia_soft_limit"]`
   40 → 60 with inline comment.
7. `docs/contract_changelog.md`: prepend v0.28.0 entry above v0.27.0
   (full motivation, scope, changes, self-tests, hard-contracts,
   doctrine coverage, see-also).
8. `docs/primordia/primordia_soft_limit_rebaseline_craft_2026-04-12.md`
   (this file): kernel_contract craft, status ACTIVE, rounds 3,
   target 0.90 / current 0.90.
9. `notes/n_<W36-evidence>.md`: evidence bundle (audit findings,
   reference depth measurements, alternatives considered) via `myco
   eat` + `myco extract`.
10. `notes/n_<W36-decisions>.md`: D1–D9 + landing record + limitations
    via `myco eat` + `myco integrate`.
11. `log.md`: append Wave 36 milestone entry (5-point format) WITH
    embedded gear2 meta discharge line per D7.
12. `myco lint` 19/19 PASS verification (post-edit).
13. `myco hunger` post-edit verification: `structural_bloat` should
    either go silent or report under the new threshold.
14. `pytest tests/` 22/22 PASS unchanged.
15. Commit `[contract:minor] Wave 36 — primordia_soft_limit re-baseline
    40 → 60 (v0.28.0)` + push.

### 4.3 Known limitations

- **L1**: Does NOT update `docs/primordia/README.md` to reflect the
  ~30 post-Wave-22 crafts that are missing from its index. Real
  problem (Attack E), deferred to Wave 37+ as a separate exploration
  craft. README rewrite needs care: each entry must point to the
  correct topic section, and several existing sections have stale
  status markers. Doing this hastily would create a bigger mess.
- **L2**: Does NOT solve the underlying "operator-as-daemon" gap
  (`docs/open_problems.md` §4 continuous compression). Re-baselining
  is a one-shot tuning, not a continuous mechanism. The tendency to
  go 14 waves without responding to a signal will recur unless the
  hunger advisory loop becomes more proactive (one of the Wave 34
  §3.3 candidates: `inlet_ripe` advisory signal, which can be
  generalized to a `compression_overdue` advisory signal).
- **L3**: Does NOT pre-bind the next re-baseline wave's choice. If
  Wave ~44 finds the substrate has matured to where some 04-12 era
  crafts ARE archivable, that wave can take the archive path
  (Option A from Round 1) rather than re-baselining again. The
  decision framework is preserved in this craft as a re-usable
  template.
- **L4**: The two SUPERSEDED candidates identified in Round 1.1
  remain in their original locations with their status frontmatter
  unchanged ("ACTIVE"). They are SUPERSEDED-in-fact but
  ACTIVE-in-record. This is honest about the constraint: marking
  them SUPERSEDED in frontmatter would mislead readers (the linked
  impl crafts cite them as authoritative design records). The
  resolution requires either substrate-immutability relaxation (a
  major doctrine change) or accepting the in-fact / in-record gap
  (chosen).
- **L5**: 60 may turn out to be too low (creation velocity rises) or
  too high (some compression mechanism lands and frees capacity).
  Re-baselines are cheap relative to the substrate; this is an
  acceptable risk.
- **L6**: Does NOT discharge other accumulated maintenance debt:
  Wave 29b biomimetic file renames (notes.py→metabolism.py etc),
  D-layer view audit log, cross-reference graph for inlet provenance.
  Each is a separate wave's scope per the "one subsystem per wave"
  discipline (Wave 25 Round 2 inheritance).
- **L7**: Does NOT introduce a `compression_overdue` automatic-pressure
  mechanism. The Wave 22 W13 rule + the standing `structural_bloat`
  sensor + the precedent set by this craft are the available
  mechanisms; nothing forces future waves to act except the growing
  signal magnitude.

### 4.4 Trajectory

Wave 37+ candidates, in friction-priority order based on what fires
post-Wave-36:

1. **README staleness sweep** (Wave 37 candidate if reading-friction
   surfaces) — exploration class, audit + rewrite of
   `docs/primordia/README.md` to reflect all 48 files in their proper
   topic sections, with [ACTIVE]/[ARCHIVED]/[SUPERSEDED-in-fact]
   markers as Wave 36 D4 establishes.
2. **`inlet_ripe` / `compression_overdue` advisory signal** (Wave 38
   candidate from Wave 34 §3.3 + this craft's L2) — extend `myco
   hunger` to emit forward-looking advisory signals (not just
   threshold-cross signals) so the operator-as-daemon loop has more
   actionable input.
3. **Cross-reference graph for inlet provenance** (Wave 34 §3.3 #2)
   — uses `inlet_origin` + `inlet_content_hash` to build a duplicate
   detector and a citation network across notes.
4. **Wave 29b biomimetic file renames** (long-deferred) — physical
   renames `notes.py → metabolism.py` etc, requires careful
   orchestration of imports + tests + lint dimensions.

The friction-driven Wave 26 D3 ordering remains in effect: the next
wave's pick is determined by which surface produces friction first
in post-Wave-36 substrate use.

### 4.5 Cross-reference

- **Wave 22**: `docs/primordia/primordia_compression_craft_2026-04-12.md`
  — original workflow + W13 procedural rule + §B7 R2.4 explicit
  authorization for this exit
- **Wave 26**: `docs/primordia/vision_reaudit_craft_2026-04-12.md` D3
  — friction-driven ordering doctrine that justifies picking
  primordia over the speculative Wave 34 §3.3 candidates
- **Wave 35**: `docs/primordia/inlet_mvp_craft_2026-04-12.md` — last
  contract minor bump, immediately preceding wave
- **`docs/WORKFLOW.md` W13** — primordia compression checkpoint rule,
  still binding, this craft is the first re-baseline-path-compliant
  response
- **`docs/open_problems.md` §4** — continuous compression open
  problem; this craft is a partial mitigation (raises threshold
  for ~8 waves) not a solution
