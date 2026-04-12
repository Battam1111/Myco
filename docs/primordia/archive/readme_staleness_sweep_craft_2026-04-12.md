---
type: craft
status: ACTIVE
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.90
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
closes:
  - "Wave 36 §4.4 (a) — README staleness sweep candidate"
  - "Doctrinal drift in MYCO.md §任务 4 (declared 'inlet 不在 v1.2 实现' but Wave 35 v0.27.0 implemented inlet MVP in the v1.2-phase era)"
  - "CLI help-string drift (cli.py says '18-dimension', immune.py docstring says 'L0–L17', actual is 19 dimensions L0–L18 since Wave 22 added L18 Compression Integrity)"
---

# Wave 37 — README + doctrinal-surface staleness sweep

> **Scope**: kernel_contract class documentation-sync craft. Brings every
> consultable surface that describes the kernel's lint count, verb count,
> Self-Model D state, and Metabolic Inlet state into agreement with the
> code state as it exists after Waves 18, 22, 28, 29, 30, 31, 32, 33, 35,
> 36. Does NOT change any lint dimension count itself. Does NOT add new
> verbs. Does NOT change semantics. Pure documentation freshening across
> 12+ surfaces, plus one MYCO.md doctrinal-wording sync that brings the
> task queue into agreement with what shipped.
>
> **Parents**:
> - `docs/primordia/primordia_soft_limit_rebaseline_craft_2026-04-12.md`
>   (Wave 36 §4.4 explicitly listed README staleness sweep as the top
>   Wave 37 candidate)
> - `docs/primordia/inlet_mvp_craft_2026-04-12.md` (Wave 35 — the wave
>   that landed inlet MVP without updating MYCO.md §任务 4; the
>   doctrinal sync this craft applies *should have* been part of Wave 35
>   but was dropped on the floor)
> - `docs/primordia/metabolic_inlet_design_craft_2026-04-12.md` (Wave 34
>   — explicitly stated "No `MYCO.md` edit" §4.2)
> - `docs/primordia/dead_knowledge_seed_craft_2026-04-11.md` (Wave 18 D
>   layer seed) and the W30/W31/W33 chain (`compress` / `uncompress` /
>   `prune`) which the README also fails to mention
> - `docs/primordia/biomimetic_nomenclature_craft_2026-04-12.md` (Wave 28)
>   which is the source of `myco immune` and the L0 immune-system framing
>   in `immune.py` — that docstring lists L0–L17 because L18 didn't exist
>   at Wave 28; L18 landed in Wave 22 wait — actually L18 landed later,
>   Wave 22 was Compression Integrity (L18). Cross-check needed in §1.
>
> **Supersedes**: none structurally. The substantive supersession this
> craft applies — MYCO.md §任务 4 wording "不在 v1.2 实现代谢入口" → "已在
> Wave 35 / v0.27.0 落地 MVP scaffold; 冷启动 + 触发 + 持续压缩仍 open" —
> is already substantively superseded by the Wave 34 design craft + Wave
> 35 implementation craft. This craft just **applies** that supersession
> to the consultable surface that wasn't updated at land time.

---

## §0 Problem definition

### The friction in one paragraph

Multiple consultable surfaces describing the kernel's current state are
stale. Some are stale by 8+ waves (lint count "15-dimension" in
`scripts/myco_init.py` references contract v0.8.0 era). Some are stale
by 1 wave (MYCO.md §任务 4 still says inlet won't be implemented in v1.2,
but Wave 35 implemented it in v1.2). Some are stale across translation
mirrors (README.md, README_zh.md, README_ja.md all carry the same wrong
"15/15 lint" badge plus the same out-of-date verb table). The aggregate
effect is a substrate where an external reader cannot trust the surface
labels — every claim must be cross-checked against `myco --help` and
`myco lint` output to confirm which version of reality they're in.

### Why this is the right next wave (Wave 26 D3 friction-driven)

Wave 36 §4.4 (a) explicitly listed "README staleness sweep" as the
top-priority Wave 37 candidate "if reading-friction surfaces". Reading
friction surfaced *immediately* in Wave 37's friction scan: `myco
--help` reports "Run 18-dimension substrate immune scan" while `myco
lint` actually runs 19 dimensions (L0–L18 inclusive). README badge says
15/15. CONTRIBUTING.md says "L0-L14, contract v0.8.0". These aren't
hypothetical staleness — they're claims that an honest agent reading
the substrate would have to second-guess on first contact.

Wave 26 D3 friction-driven ordering doesn't mean "service the loudest
signal" (Wave 36 meta entry). It means "service the signal whose action
repays the cost". Wave 37's action — mechanical sync of stale numbers
and doctrinal wording — is low cost (text edits, no behavior change, no
contract bump). The repayment is high (every external reader, including
the future-Claude-self that boots into this repo, gets accurate first
contact).

### Why one wave for 12+ surfaces (scope discipline pre-defense)

Wave 25 R2 inheritance: one subsystem per wave. Wave 37 touches:

1. README.md, README_zh.md, README_ja.md (3 translation mirrors of the
   same surface — "user-facing project pitch")
2. MYCO.md (kernel SSoT, §任务 4 + indicator panel rationale)
3. CONTRIBUTING.md (contributor-facing project structure)
4. wiki/README.md is **out of scope** — re-checked, the only "15/15"
   reference in wiki/README.md is line 35 "myco lint 应 15/15 绿" which
   is a procedural rule statement, not a count claim. Hmm — that IS
   stale (should say 19/19). Adding to scope.
5. src/myco/cli.py (4 occurrences of "18-dimension")
6. src/myco/immune.py (docstring "18 dimensions L0–L17")
7. src/myco/mcp_server.py (2 occurrences of "15-dimensional")
8. src/myco/migrate.py (1 occurrence)
9. src/myco/init_cmd.py (1 occurrence)
10. scripts/myco_init.py (1 occurrence)
11. scripts/myco_migrate.py (1 occurrence)

**These are all the same subsystem** at the right level of abstraction:
**"surfaces that describe kernel state to agents and humans on first
contact"**. They share a single root cause (kernel grew, surfaces
didn't sync) and a single fix vocabulary (current numbers, current
verbs, current Self-Model D state, current Metabolic Inlet state).
Splitting into 4–5 waves would just multiply ceremony for the same
mechanical edit. Wave 22 §B7 R2 already established that a coherent
edit across surface mirrors is one wave, not N waves.

---

## §1 Round 1 — Audit (per-surface staleness inventory)

### 1.1 README.md (English canonical)

| Line | Claim | Actual | Severity |
|---|---|---|---|
| 14 | Badge: `Lint-15/15 green` | 19 dimensions (L0–L18) | HIGH (badge is the first thing an external reader sees) |
| 168 | ASCC stat table: "15/15 lint dimensions green" | Historically pinned (ASCC validated when Myco had 15 dims) | LEAVE — historical, not stale |
| 196 | v0.x today: "15-dimension lint green" | 19-dimension | HIGH |
| 196 | v0.x today: "metabolic inlet is a declared primitive" | Wave 35 shipped MVP scaffold (v0.27.0) | HIGH |
| 196 | v0.x today: "Self-Model D layer is declared, not wired" | Wave 18 seed + Wave 33 `myco prune` excretion | HIGH |
| 187 | Open Problems #6: "D is declared, not yet implemented. Minimum viable seed is on the roadmap." | Seed shipped (Wave 18); auto-excretion via prune (Wave 33); full D layer (audit log + cross-ref + adaptive thresholds) still open | MEDIUM (sync to open_problems.md §6 wording) |
| 196 | "MCP server exposes 9 tools" | 9 tools confirmed (mcp_server.py grep: 9 `@mcp.tool` decorators) | LEAVE — accurate |
| 236-244 | Verb table: 7 entries (eat, digest, view, lint, forage, hunger, absorb) | Missing 8 metabolic verbs: correct/molt (Wave 19), evaluate/extract/integrate (Wave 32), compress (Wave 30), uncompress (Wave 31), prune (Wave 33), inlet (Wave 35) | HIGH |
| 46 | "the tools (`eat` / `digest` / `view` / `hunger`) are named from it on purpose" | The seven-step pipeline now has explicit verbs for evaluate/extract/integrate/compress/prune | MEDIUM |

**ASCC stat table decision (line 168)**: leave at "15/15". ASCC was
validated against the lint count at the time of capture. ASCC has no
`_canon.yaml`, cannot be re-linted as a Myco instance. Updating to
"19/19" without re-validation would be a fabrication. Updating to "all
green" loses precision. Cleanest move: leave as historical pin.

### 1.2 README_zh.md / README_ja.md

**Mirror staleness**. Each contains the same set of lines as README.md
in their respective languages:

- Line 14 badge: `Lint-15/15 全绿 / 全緑` → `Lint-19/19 全绿 / 全緑`
- ASCC stat table (zh:167, ja:169): leave as historical pin
- v0.x today row (zh:195, ja:197): same five fixes as English line 196
- Open Problems #6 (zh:185, ja:187): same fix as English line 187
- Verb table (zh:236-244, ja:237-245): add the same 8 missing verbs
- "the tools (`eat` / `digest` / `view` / `hunger`)" line (zh:46, ja:46):
  same fix

**Translation discipline**: edits to the mirrors must preserve voice.
Where English uses "shipped (Wave 35)", Chinese uses "已在 Wave 35
落地 MVP scaffold", Japanese uses "Wave 35 で MVP scaffold が出荷済み".
Don't translate from a literal English template — match each language's
existing register.

### 1.3 MYCO.md (kernel SSoT, doctrinal sync)

This is the most consequential surface in the sweep. Two distinct
classes of edit:

**Class A — factual freshening (numbers only):**
- Line 81: "**18 维 lint (L0-L17)**" → "**19 维 lint (L0-L18)**"
- Line 108: indicator rationale "**18 维 L0-L17 全绿**" → "**19 维
  L0-L18 全绿**"

These are number bumps in rationale strings, not value changes. The
indicator value (0.68) does not move.

**Class B — doctrinal sync (§任务 4 wording):**
- Line 69: Task 4 status `📐 v2.0` + progress `▱▱▱` → `🔄` (in progress,
  scaffold landed) + new progress bar reflecting Wave 35 landing
- Line 75: "现在不声明，外部贡献者会把 Myco 建成'更好的 CLAUDE.md'；
  声明后但不提前实现" — the second clause "声明后但不提前实现" is now
  factually false (Wave 35 implemented MVP). Update to: "声明后逐步落地：
  Wave 34 设计 craft + Wave 35 MVP scaffold (v0.27.0) → 冷启动 / 触发
  信号 / 持续压缩仍 open（见 docs/open_problems.md §1-§4）"
- Line 77: "**形状**（草图，v2.0 设计辩论时再细化）" → "**形状**（Wave 34
  设计 craft locked, Wave 35 MVP scaffold 落地）"
- Line 81: invariant clause keeps the same content but updates the
  number to 19/L0-L18 (already in Class A above)
- Line 91: "**不会做**: 在 v1.2 实现代谢入口（违反第一性原理立场）" —
  this is the load-bearing line that Wave 35 implicitly overturned
  without explicit doctrinal record. Update to: "**已部分实现，不会做**:
  Wave 35 落地 inlet MVP scaffold（参 inlet_mvp_craft）；'完全自主源
  发现 + 冷启动 bootstrap' 仍属 v2.0+，不会在 v1.2 实现"
  - This is the most delicate edit. The supersession is real (the code
    shipped), the wording must be honest about what was kept of the
    original "不会做" rule (the autonomous discovery part) and what was
    relaxed (the verb existence + manual file/URL ingestion).

**Why Class B is in Wave 37 scope, not deferred**: README.md line 196
will say "metabolic inlet MVP shipped" after Wave 37. If MYCO.md still
says "不在 v1.2 实现", README and MYCO.md will disagree. README is
downstream of MYCO.md doctrinally (MYCO.md is the kernel SSoT). Fixing
README without fixing MYCO.md leaves the upstream source still wrong
and creates a new lint-style integrity violation (claim drift between
SSoT and translation). The two surfaces must move together.

### 1.4 CONTRIBUTING.md (contributor-facing)

- Line 35 (the grep miss earlier — actually line 140): in the project
  structure ascii tree:
  `│   ├── lint.py            # 15-dimension consistency checker (L0-L14, contract v0.8.0)`
  → bump number AND contract version reference (v0.8.0 → no version
  reference, since the comment will go stale again on every contract
  bump; or → v0.28.0 with a footnote that contract drifts; cleanest:
  drop the parenthetical contract version, leave just `19-dimension
  consistency checker (L0-L18)`)

### 1.5 wiki/README.md

- Line 35: "5. `myco lint` 应 15/15 绿" → "5. `myco lint` 应 19/19 绿"

This line is part of a numbered "promote checklist" (the conditions for
the first wiki promote). It's a procedural rule containing a count.
Number bump only.

### 1.6 src/myco/cli.py — 4 stale "18-dimension" claims

| Line | Context | Fix |
|---|---|---|
| 104 | Comment in `myco lint` parser block | "18-dimension" → "19-dimension" |
| 109 | Help string for `myco lint` | "Run 18-dimension substrate immune scan" → "Run 19-dimension" |
| 126 | Comment in `myco immune` parser block | "18-dimension" → "19-dimension" |
| 132 | Help string for `myco immune` | "Run 18-dimension substrate immune scan" → "Run 19-dimension" |

These are the strings users see when they run `myco --help` and
`myco lint --help`. First-contact text. Sync immediately.

### 1.7 src/myco/immune.py — module docstring drift

Two issues in `src/myco/immune.py`:

- Line 4: "the substrate's 18-dimension immune system" → "19-dimension"
- Line 8: "the 18 dimensions L0–L17 perform immune-system functions" →
  "the 19 dimensions L0–L18 perform immune-system functions"
- Lines 10–27: the docstring enumerates L0 through L17 (one bullet per
  dimension). L18 (`Compression Integrity`) is missing. Add line 28:
  `- **L18** compression integrity (.original / extracted note hash audit)`

This is the most "deep" docstring fix because it's a per-dimension
enumeration. Cross-check with `lint.py:1825` (the actual checks list)
to confirm the L18 description matches what `lint_compression_integrity`
does.

### 1.8 src/myco/mcp_server.py — 2 stale "15-dimensional" claims

| Line | Context | Fix |
|---|---|---|
| 9 | Module docstring tool overview: "myco_lint  — Run 15-dimensional consistency checks (L0-L14)" | "Run 19-dimensional consistency checks (L0-L18)" |
| 108 | Tool description for `myco_lint`: "This is the 15-dimensional immune system of the knowledge substrate. It..." | "19-dimensional" |

Both are agent-facing strings (MCP tool descriptions are read by every
agent that loads the MCP server). First-contact text. Sync immediately.
**This file is in `kernel_contract` trigger surfaces — touching it
mandates this craft to exist.**

### 1.9 src/myco/migrate.py — stale ascii-tree comment

- Line 140: `# 15-dimension consistency checker (L0-L14, contract v0.8.0)` →
  `# 19-dimension consistency checker (L0-L18)`

Same fix logic as CONTRIBUTING.md: drop the parenthetical contract
version reference (it'll just go stale again on the next bump), leave
the dimension count + range.

### 1.10 src/myco/init_cmd.py + scripts/myco_init.py + scripts/myco_migrate.py

Three sites print the same ascii line at project init time:

`scripts/lint_knowledge.py (15-dimension Lint shim → myco.lint)`

This refers to a **shim file** that gets created at instance init, not
to `myco.lint` itself. Wait — let me re-check before editing. The shim
exists for backwards compatibility with pre-Myco-package projects.
Bumping the shim's description from "15-dimension" to "19-dimension" is
correct as long as the shim still delegates to `myco.lint` (which it
does — the comment says `→ myco.lint`).

Three identical edits, same fix on all three lines.

### 1.11 Out-of-scope (substrate immutability)

These files matched the grep but MUST NOT be touched (per Hard Contract
#2 — substrate immutability + historical pin):

- `log.md` — every milestone entry is append-only and historically pinned
- `docs/contract_changelog.md` — every contract version entry is pinned
  to that contract's truth at the time of bump
- `docs/primordia/*.md` — every craft document is a historical record
- `notes/n_*.md` — every note is a historical record
- `examples/ascc/*` — frozen ASCC artifact

**Procedural rule**: if a future grep shows these files match a stale
pattern, that's not staleness — that's historical truth. The fix is to
*update the live surfaces* (which Wave 37 does), not to rewrite history.

---

## §2 Round 2 — Scope discipline + ASCC table defense

### Attack A — "Two subsystems disguised as one"

**Attack**: Wave 25 R2 says one subsystem per wave. Wave 37 touches
README files (one subsystem) AND MYCO.md doctrinal lines (a different
subsystem) AND CLI source code (yet another). At minimum that's three.

**Defense**: The level of abstraction defining "subsystem" matters.
Wave 25 R2 was a reaction to a failed wave that mixed *unrelated*
subsystems (e.g., metabolism + lint engine + upstream protocol). Wave
37's surfaces are all answers to the same question: "what does the
kernel currently do, and where is that documented?". They share:

- Same root cause (kernel grew, surfaces didn't sync)
- Same fix vocabulary (current lint count, current verb count, current
  Self-Model D state, current Metabolic Inlet state)
- Same correctness check (`myco --help` + `myco lint` output as ground
  truth)
- Same risk profile (text edits, no behavior change, no contract bump)
- Same audience (external readers + future-self agents on first contact)

A wave that fixed only README without fixing MYCO.md would be **less**
coherent than Wave 37's bundled approach: it would leave the upstream
SSoT (MYCO.md) saying X while the downstream summary (README.md) says
not-X. That's the failure mode Wave 25 R2 was warning against, in
disguise.

**Verdict**: defensible as one subsystem at the right granularity.

### Attack B — "Why bundle CLI source edits with documentation edits"

**Attack**: README.md is documentation. cli.py is code. Code should be
in a separate wave from documentation.

**Defense**: The cli.py edits in scope are help-string edits, not
behavior changes. Help strings ARE documentation — they're the
documentation users see when they run `--help`. Splitting them off
into a separate wave would mean:
- A user who reads README post-Wave-37 but pre-Wave-38 sees "19
  dimensions" while their CLI says "18 dimensions". Local incoherence.
- The mcp_server.py edit (also a docstring) would have to wait for the
  same later wave. mcp_server.py is in `kernel_contract` trigger
  surfaces, so its edit MUST be paired with a craft. We'd have two
  crafts saying the same thing.

The minimal-coherence boundary cuts at "all surfaces describing kernel
capability", not at "code vs docs".

### Attack C — "ASCC table 15/15 should also bump to 19/19"

**Attack**: Leaving the ASCC stat table at 15/15 while bumping the
badge to 19/19 creates internal inconsistency in the README. A reader
will see two different numbers in the same file.

**Defense**: The badge claim is about *current Myco kernel state*. The
ASCC table claim is about *what ASCC achieved at the time of validation*.
These are different referents. ASCC has no `_canon.yaml`, can't be
re-linted as a Myco instance — verified earlier in this craft's
research:

```
$ PYTHONPATH=src python -m myco.cli lint --project-dir examples/ascc
FATAL: _canon.yaml not found at project root!
```

So the choice is:
1. Leave at "15/15" — historically accurate, internally inconsistent
   with badge
2. Bump to "19/19" — currently aspirational but unverifiable
3. Rephrase to "all lint dimensions green" — accurate but loses precision

Option 1 is the most honest. The internal inconsistency is real but
interpretable: badge = now, ASCC table = then. A reader confused by
this is a reader who needs the precision more, not less.

**Mitigation**: add a small footnote / parenthetical to the ASCC table
clarifying it's a snapshot. Wave 37 chooses *minimum mitigation*: leave
the table unchanged (no footnote), accept that a careful reader can
work out the discrepancy from context (the surrounding paragraph
mentions "An 8-day, 80+ file reinforcement-learning research project"
— clearly historical). Adding a footnote would be over-engineering for
a corner-case confusion.

**Verdict**: leave ASCC table at 15/15. Document this decision in §4.1
D2 for future audit.

### Attack D — "Why update MYCO.md §任务 4 doctrine wording at all — leave it stale and let Wave 38 handle"

**Attack**: MYCO.md §任务 4 line 91 ("不会做: 在 v1.2 实现代谢入口")
is a doctrinal statement, not a number. Updating doctrinal statements
needs its own craft. Wave 37 should be number-bump-only and defer the
§任务 4 supersession to a separate wave.

**Defense**: The supersession ALREADY HAPPENED in Wave 35. Wave 35
landed inlet MVP. The fact that MYCO.md wasn't updated at land time is
a *bug*, not a deferred decision. Wave 37 is *applying* the existing
supersession to the surface that wasn't updated, not *making* a new
supersession.

This is the same pattern as Wave 36 (which applied a Wave 22 §B7 R2.4
exit clause that had been "anticipated but not used"). Wave 37 applies
a Wave 35 supersession that "happened in code but didn't reach
docs". Both waves are *recovery from a previously incomplete landing*,
not new doctrinal moves.

**Procedural soundness check**: per craft_protocol.md §3 trigger #4,
"public_claim" surface touches need craft evidence. MYCO.md is a
public_claim surface. Wave 37's craft IS the evidence. The chain is:
Wave 35 craft (substantive decision) → Wave 37 craft (surface
application). Both crafts cite each other.

**Verdict**: in scope. Documenting as D3 in §4.1.

### Attack E — "What if Wave 35 deliberately left §任务 4 stale because the wording is still half-true"

**Attack**: Maybe Wave 35 chose not to touch §任务 4 because the line
"完全自主源发现 still v2.0+" remains true. The stale parts and the
fresh parts are intermixed, and pulling them apart is dangerous.

**Defense**: Read Wave 34 craft §4.2 (Landing list, Wave 34 only):
"No `MYCO.md` edit. No new test." Wave 34 is the design craft. It
explicitly excluded MYCO.md edit from its landing list — but for Wave
34's reasons (Wave 34 was design-only, no impl, so no surface change
should land). Wave 35 was the impl craft. Wave 35 landed code but did
not retroactively check whether Wave 34's "no MYCO.md edit" decision
should be lifted now that impl is real.

So the omission is best read as a *carry-over from Wave 34's deferral*,
not as a *deliberate Wave 35 decision*. Wave 37 closes the loop.

The wording in Wave 37's update preserves what's still true: the
"完全自主" branch stays open as v2.0+. Only the "声明后但不提前实现"
clause and the "不在 v1.2 实现" clause get superseded — and even these
are softened to "已部分实现" rather than "已完全实现". The §任务 4
edit is a delicate honest update, not a wholesale rewrite.

**Verdict**: in scope. Edit text in §1.3 above is the binding form.

### Attack F — "L17 contract drift will fire because cli.py is not in trigger surfaces but bumping its strings is a kernel-facing edit"

**Attack**: L17 contract drift checks `synced_contract_version` lag. If
I touch any surface that L17 watches, it might fire. Specifically, if
the immune.py docstring change is interpreted as a contract surface
change, the synced_contract_version in `src/myco/templates/_canon.yaml`
might need to bump in lockstep.

**Defense**: L17 watches `_canon.yaml::contract_version` vs
`src/myco/templates/_canon.yaml::synced_contract_version`. Wave 37
touches NEITHER. cli.py, immune.py, mcp_server.py docstring changes
don't affect either YAML file. L17 will remain silent.

Verification: pre-flight `myco lint` confirmed L17 PASS at the start
of Wave 37. Nothing this craft does will move the canon side. Post-
flight lint will confirm.

**Verdict**: not a concern. L17 stays silent.

---

## §3 Round 3 — Edge cases + decision lock

### Edge case C1 — What if `myco lint` itself has a different dimension count internally vs externally?

Lint output is generated from `lint.py:1824` `checks = [...]` list.
Verified earlier: 19 entries (L0 through L18). The "18-dimension"
strings in cli.py are independent constants — they don't read from
the actual list. They were hand-typed at the time of writing and never
re-checked when L18 landed.

**Implication**: there's no SSoT for the dimension count. cli.py says
18, lint.py implements 19, the docstring in immune.py says 18 and
enumerates L0–L17. After Wave 37 these will all say 19. But there's
nothing PREVENTING the same drift from happening again on a future
L19 addition.

**Should Wave 37 introduce a single source for this number?** It would
be a small change: introduce `LINT_DIMENSION_COUNT = len(checks)` as a
module-level constant in lint.py and have cli.py / immune.py /
mcp_server.py reference it.

**Decision**: NO. That's scope creep. Wave 37 is a sync sweep, not a
re-architecture. The "single source of truth for the dimension count"
is a Wave 38+ candidate (low priority — the next L19 addition will
re-trigger the sync friction at which point the SSoT becomes worth
adding). Document as L1 limitation in §4.3.

### Edge case C2 — Translation drift in README mirrors

Wave 37 edits README.md, README_zh.md, README_ja.md in lockstep.
Future-Wave-38+ might edit only one and leave the others stale. Same
problem as C1 — no enforcement that mirrors stay in sync.

**Decision**: NO new lint dimension for translation sync. That's a
plausible Wave 38+ candidate but out of scope here. Document as L2.

### Edge case C3 — What if some agent reads the immune.py docstring directly (not via help) and uses the L0–L17 enumeration as a checklist?

The immune.py docstring lists each Lx with a one-line description.
Updating to L0–L18 means adding one new line for L18. The format must
match the existing format exactly so any pattern-matching reader
(IDE, doc generator, agent that ingests the docstring as training
context) doesn't break.

**Check**: existing format is `- **L<n>** <category> (<short description>)`
on each line. New line for L18: `- **L18** compression integrity
(.original / extracted note hash audit)`. Matches format.

Verified format match. No regression risk.

### Edge case C4 — README.md verb table grows by 8 rows. Will any markdown rendering break?

Markdown table parsers handle arbitrary row counts. The existing 7-row
table grows to 15 rows. No syntactic concern. Visual concern: a 15-row
table is dense but still readable in GitHub's rendered view. Three
mirror tables grow identically.

**Decision**: accept the density. Alternative (split into two tables
"core verbs" + "metabolic verbs") is over-engineering for the actual
information density.

### Edge case C5 — `synced_contract_version` value in mcp_server.py docstring or templates?

mcp_server.py docstring at line 9 mentions tools, not version. The
edit (15-dimensional → 19-dimensional) is purely about lint count.
Does NOT touch synced_contract_version anywhere. Same for cli.py.

Verified: no surface in the Wave 37 edit set touches a contract version
string. v0.28.0 stays.

### Decision lock D1–D8

**D1** — Wave 37 sweeps every consultable surface that describes
kernel state into agreement with the actual kernel state as of the
moment of this craft. The "ground truth" for each claim is:
  - Lint count: `len(lint.py::checks)` = 19
  - Lint range: L0–L18 inclusive
  - Verb count (CLI): 22 verbs from `myco --help` (20 unique semantic,
    after collapsing the lint=immune and correct=molt aliases)
  - MCP tool count: 9 (verified from `@mcp.tool` decorator grep on
    mcp_server.py)
  - Self-Model D state: seed shipped Wave 18 (`view_count` +
    `last_viewed_at` frontmatter); auto-excretion via `myco prune`
    Wave 33; full D layer (audit log + cross-ref + adaptive thresholds)
    open
  - Metabolic Inlet state: MVP scaffold shipped Wave 35 (v0.27.0);
    cold-start, trigger signals, continuous compression remain open

**D2** — README ASCC stat table at 15/15 stays unchanged. It's a
historical claim about ASCC's state at validation time, not a current
kernel claim. Documented as historical pin in §2 Attack C.

**D3** — MYCO.md §任务 4 wording is updated to reflect Wave 35
landing. The substantive supersession was completed by Wave 35 craft;
Wave 37 just APPLIES it to the consultable surface. Edit text from
§1.3 is binding. Wave 37 is NOT making a new doctrinal decision.

**D4** — All three README mirrors (en/zh/ja) move in lockstep.
Translation edits preserve each language's existing register; do not
literally translate the English template across.

**D5** — wiki/README.md line 35 ("应 15/15 绿") gets the number bump
only. No structural change.

**D6** — CLI source files (cli.py, immune.py, mcp_server.py,
migrate.py, init_cmd.py, scripts/myco_init.py, scripts/myco_migrate.py)
get string-level edits only. No behavior change. No new constants. No
re-architecture. The "single SSoT for dimension count" is deferred to
a future wave (L1 limitation).

**D7** — CONTRIBUTING.md project-structure tree comment drops the
parenthetical contract version reference (was "v0.8.0", would just go
stale again). Leaves the dimension count + range.

**D8** — No contract version bump. Wave 37 is a refactor in spirit
(documentation sync) classified as kernel_contract because it touches
mcp_server.py docstring (a kernel_contract trigger surface). Confidence
target 0.90. v0.28.0 stays.

---

## §4 Conclusion

### 4.1 Decisions canonical

Reproducing D1–D8 from §3 as the citable canon record. See above.

### 4.2 Landing list (15 verifiable steps)

1. ✅ `docs/primordia/readme_staleness_sweep_craft_2026-04-12.md` (this file)
2. ⏳ Evidence note via `myco eat` capturing audit findings, surface
   list, ground-truth values, decision rationale
3. ⏳ Edit `README.md`: badge + verb table (8 new rows) + today/coming
   row + open problems §6 + line 46 seven-step pipeline tools mention
4. ⏳ Edit `README_zh.md`: same set, Chinese register
5. ⏳ Edit `README_ja.md`: same set, Japanese register
6. ⏳ Edit `MYCO.md`: §任务 4 line 69 status + line 75 wording + line
   77 草图 → 落地 + line 81 number bump + line 91 不会做 supersession +
   line 108 indicator rationale number bump
7. ⏳ Edit `CONTRIBUTING.md` line 140: drop contract version, bump
   dimension count
8. ⏳ Edit `wiki/README.md` line 35: 15/15 → 19/19
9. ⏳ Edit `src/myco/cli.py`: 4 occurrences of "18-dimension" → "19-dimension"
10. ⏳ Edit `src/myco/immune.py`: docstring "18 dimensions" + "L0–L17"
    + add L18 enumeration line
11. ⏳ Edit `src/myco/mcp_server.py`: 2 occurrences of "15-dimensional"
12. ⏳ Edit `src/myco/migrate.py` + `init_cmd.py` + `scripts/myco_init.py`
    + `scripts/myco_migrate.py`: 4 stale shim/tree comments
13. ⏳ Decisions note via `myco eat` + `myco integrate` capturing D1–D8
14. ⏳ `log.md` Wave 37 milestone entry (single paragraph, 5–10 numbered
    sub-points, anchor on Wave 36 milestone)
15. ⏳ Verify: `myco hunger` (regen brief), `myco lint` (expect 19/19
    PASS), `pytest tests/ -q` (expect 22/22 unchanged), commit + push

### 4.3 Known limitations

**L1 — No SSoT for dimension count**: cli.py, immune.py, mcp_server.py
each carry the literal number "19" after Wave 37. The next L19
addition will re-trigger the same staleness friction. Wave 38+
candidate: introduce `LINT_DIMENSION_COUNT = len(checks)` and have
help strings reference it. Deferred for scope discipline.

**L2 — No translation-mirror lint**: README_zh.md and README_ja.md can
silently drift from README.md again. Wave 38+ candidate: lint dimension
that checks README mirrors against the canonical English. Deferred.

**L3 — ASCC stat table is historical and unverifiable**: leaving the
"15/15 lint dimensions green" claim at its captured value. Future
readers must rely on context to interpret. Adding a footnote was
considered and rejected as over-engineering.

**L4 — MYCO.md §任务 4 supersession is single-author**: Wave 37 is
applying a Wave 35 decision to a stale surface. The single author is
the same Claude session. Per craft_protocol.md §4 single-source
convention, current_confidence should equal target_confidence (not
strictly less). Wave 37 reports 0.90 = 0.90, which is correct because
the substantive evidence (Wave 34 design + Wave 35 implementation
landed code) is external to this craft's reasoning chain.

**L5 — `wiki/README.md` line 35 bump is a procedural rule update**:
the rule "myco lint 应 19/19 绿" assumes the count won't grow again.
On the next L19 addition, this line will go stale. Same root cause as
L1.

**L6 — Wave 37 does not touch open_problems.md §6 wording**: README's
Open Problems #6 entry will be updated, but the canonical
`docs/open_problems.md` §6 already has the up-to-date wording (verified
in §1 audit). No edit needed there. If a future drift surfaces, that's
its own wave.

**L7 — Verb table grows from 7 to 15 rows**: visual density increase.
Considered splitting into two tables (core / metabolism). Rejected as
over-engineering. The verb table is a reference, not a tutorial; 15
rows is fine for a reference table.

### 4.4 Wave 38+ trajectory (conditional, not committed)

Per Wave 26 D3 friction-driven: Wave 38 derives from post-Wave-37
hunger signals, NOT from this craft's predictions. With that caveat,
plausible candidates:

- **A** — Single SSoT for `LINT_DIMENSION_COUNT` (closes L1 + L5)
- **B** — Translation-mirror lint dimension (closes L2)
- **C** — Continued continuation of Wave 36 §4.4 candidates: inlet_ripe
  / compression_overdue advisory signal generalized from W34 §3.3 #1
- **D** — Cross-reference graph for inlet provenance (W34 §3.3 #2)
- **E** — Wave 29b biomimetic file renames (long-deferred maintenance)

The actual Wave 38 pick depends on what fires after Wave 37 lands.

### 4.5 Cross-references

- Parent: `docs/primordia/primordia_soft_limit_rebaseline_craft_2026-04-12.md` §4.4
- Doctrinal precedent (the supersession this wave applies):
  `docs/primordia/inlet_mvp_craft_2026-04-12.md` (Wave 35) +
  `docs/primordia/metabolic_inlet_design_craft_2026-04-12.md` §4.2
  (Wave 34 — explicit "no MYCO.md edit" deferral)
- Sibling sync waves: none (Wave 37 is the first explicit cross-surface
  sync sweep)
- Hard contract honoured: #2 substrate immutability (no log.md /
  contract_changelog.md / primordia history / notes / examples touched)
- Lint covered: L9 vision anchor (MYCO.md §任务 4 wording stays
  consistent with §身份锚点 — no identity drift), L13 craft schema
  (this craft itself), L15 craft reflex (this craft satisfies the
  reflex for the public_claim + kernel_contract surface touches), L16
  boot brief freshness (will be regenerated post-edit by hunger), L17
  contract drift (silent — no canon touched)
