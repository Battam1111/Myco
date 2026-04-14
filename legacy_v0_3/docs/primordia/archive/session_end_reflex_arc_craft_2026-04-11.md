---
type: craft
status: ARCHIVED
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Craft — Session End Reflex Arc (Wave 14, contract v0.12.0 → v0.13.0)

> Sibling to `boot_reflex_arc_craft_2026-04-11.md`. Where Wave 13 closed the
> **start** of a session against W1/W3/§8.4 drift, Wave 14 closes the **end**
> of a session against W5 (persistent evolution) / Gear-2 reflection / Gear-4
> sweep drift. Both arcs are agent-autonomous per Wave 12 precedent.

## 0. Motivation — two holes in Section 4 of the agent protocol

`docs/agent_protocol.md §4 Session End Sequence` currently lists five prose
steps: reflect → log → hunger → lint → MYCO.md. There is **no detector** that
fires when these steps are skipped across sessions. Dogfood scan of Myco
kernel's own `log.md` confirms both holes are active:

**H5 — Gear 2 reflection drift (W5 / evolution engine)**
- Last `## [YYYY-MM-DD] meta |` entry in `log.md`: line 116, **2026-04-10**.
- Between that line and line 693 (Wave 13 milestone, 2026-04-11) there are
  **30+ milestone / friction / system / craft** entries with **zero** `meta`
  reflections. A full day of kernel work produced no Gear-2 system-about-
  itself signal.
- `myco_reflect` is an advisory MCP tool. Agent that forgets to call it at
  session end leaves no trace; next session's boot sequence has no way to
  know a reflection is missing. Drift is invisible.

**H6 — Gear 4 sweep drift (W5 / evolution engine)**
- `grep -c "g4-candidate" log.md` = **18**
- `grep -c "g4-pass" log.md` = **0**
- Oldest unresolved: **2026-04-07** (log.md:152). Four days old, never
  swept. `MYCO.md` §5 step 6 says "Gear 4 sweep: scan log.md for g4-candidate
  → write each into Myco docs or annotate g4-pass". The discipline is
  documented, the agent ignores it, and **no lint or hunger signal objects**.

Both are structurally identical to the Wave 13 problem: an instruction
lives in prose, the prose is obeyed sporadically at best, and no code-level
reflex fires when it's skipped. Wave 12 reflex arc rule applies: if the
principle is W-series and the surface touches kernel contract / evolution
engine, the mechanism has to be HIGH, not advisory, and must be emitted as
part of the normal hunger report.

Parent contradictions (unchanged from v0.12.0 arc):
- `docs/agent_protocol.md §4` prose steps vs. W1-style drift enforcement
- Wave 12 reflex arc autonomy precedent (agent writes craft in-session on
  missing obligations) applied asymmetrically — only to boot, not end
- `docs/evolution_engine.md` Gear 2 / Gear 4 rituals lack any drift sensor
- Real-world kernel dogfood: self-blind to own Gear 2/4 debt

---

## 1. Round 1 — attack the concept

### A1 — "just reuse myco_reflect, make it mandatory"

**Attack**: Upgrading `myco_reflect` to mandatory doesn't help — it still
requires the agent to invoke it. The failure mode is not "reflect returned
the wrong thing", it's "reflect was never called". Making a tool mandatory
in prose has the same failure surface as the prose step it replaces.

**Response**: Accept. The mechanism MUST be pull-style (surfaced by
`myco_status` / `myco hunger`) not push-style (agent must call). Wave 13
established this as the reflex pattern. Wave 14 inherits it.

### A2 — "g4-candidate is a log grep, not a knowledge-substrate signal"

**Attack**: Gear 4 sweep asks the agent to grep `log.md` for a string. A
pure text-search is not knowledge; it's a shell habit. Why does this need
a lint-class reflex rather than a `Makefile: sweep` rule?

**Response**: Partial accept. The sweep itself is cheap text work, but the
**obligation** is a W5 principle (continuous evolution) and the **drift
signal** (count of unresolved g4-candidates, age of oldest) is exactly the
kind of metabolic health indicator `myco hunger` is designed to surface.
A Makefile rule would again require the agent to remember to run it. The
hunger report already runs on every session boot. Folding this check there
is the minimum-invasive choice.

### A3 — "Gear 2 reflection is subjective; you can't detect absence of it"

**Attack**: Gear 2 is about the agent noticing something wrong with the
system. By definition, if nothing feels wrong, there is nothing to reflect
on. A "no meta entry in N days" alarm punishes healthy sessions.

**Response**: Reject. Gear 2 is a **ritual** in Myco's evolution engine,
not an oracle — `docs/evolution_engine.md` is explicit that the value comes
from the **practice of looking**, not from finding defects every time. A
session that produces ten milestones and zero `meta` entries is by default
suspect, not by default healthy. The check is not "did you find something",
it is "did you look". Counter-evidence: Wave 13's dogfood discovery of 27
unhandled pure-raw notes happened exactly because the agent ran hunger,
not because it felt something was wrong.

### A4 — "two detectors, one craft — are you over-bundling?"

**Attack**: H5 and H6 are about different principles (Gear 2 vs Gear 4).
Bundling them dilutes each. Wave 13 bundled three detectors (contract_drift
+ raw_backlog + include_hunger) but all three were same-principle
(session-boot W1/§8.4). This bundle crosses ritual boundaries.

**Response**: Partial reject. Both H5 and H6 share: (a) same lifecycle
stage (session end), (b) same emission channel (hunger signals), (c) same
root cause (prose instructions lack code-level reflex), (d) same parent
principle family (W5 evolution discipline). Splitting into two crafts
would create two contract bumps (v0.13 + v0.14) over the same weekend for
the same failure surface. The bundle stays, but each detector MUST be
independently toggleable via canon flags so future crafts can revise one
without touching the other.

---

## 2. Round 2 — attack the design

### B1 — "what counts as a 'session'?"

**Attack**: You need a session boundary to say "N sessions went without a
meta entry". Myco has no session model. `myco_status` is called per-agent-
invocation, not per-session; a single long session could correctly have
zero meta entries during the body of work.

**Response**: Accept — use **log-entry density** as the proxy, not
session count. Heuristic:

- Count `## [YYYY-MM-DD]` entries after the latest `## [YYYY-MM-DD] meta |`
  line in `log.md`.
- If the count exceeds `gear2_drift_threshold` (default **15**), emit
  `session_end_reflex_missing: gear2`.
- Rationale: 15 non-meta log entries roughly equals a full active day of
  kernel work. It fires on real drift (current kernel: 30+ entries since
  last meta) but tolerates a normal milestone-heavy push.

This is not perfect — a bursty session could trip it — but false positives
are cheap (the reflex asks for one-sentence reflection) and it does not
block task work, only nags at next boot.

### B2 — "g4-candidate age vs count — which is the real signal?"

**Attack**: You have 18 g4-candidates. Is the threshold on **count** (too
many unresolved) or **age** (oldest stale)? Both have pathological edges:
count penalizes active debate phases where candidates stack up naturally;
age penalizes legitimately long deliberations.

**Response**: Use **age**, not count. Rationale:

- A candidate created today and a candidate from 2026-04-07 are not
  symmetric — the old one has had four session boots to be resolved and
  none took it up. That is the drift signature.
- Concretely: detect the **oldest** `g4-candidate` line in `log.md` whose
  `## [YYYY-MM-DD]` date is older than `gear4_drift_threshold_days`
  (default **5**). If any exists and has no paired `g4-pass` or
  `craft_reference` in the same entry or after it, fire
  `session_end_reflex_missing: gear4`.
- 5 days matches the `stale_raw_days` intuition: anything untouched for
  five days is cold. Threshold lives in canon for future tuning.

### B3 — "g4-pass pairing — how do you match a candidate to a resolution?"

**Attack**: A candidate says "→ g4-candidate: X". A resolution could be
anywhere after: an inline `g4-pass` annotation, a new log entry
`g4-resolved: X`, or a craft file named after the topic. Pairing is fuzzy.
You could easily double-count.

**Response**: Accept — use **conservative pairing**. A `g4-candidate`
line is considered **resolved** iff **any** of these is true:

1. Same line contains `g4-pass:` (inline dismissal with reason)
2. A later line in `log.md` contains `g4-resolved` or `g4-landed` with
   enough lexical overlap (≥2 shared nouns) — stretch goal, not v1
3. The candidate line references a craft file
   (`docs/primordia/<name>_craft_YYYY-MM-DD.md`) that exists on disk
4. A `g4-pass` entry in MYCO.md's `### g4-candidates` dedicated section
   (future extension; v1 ignores this)

v1 implements **1 and 3 only** — conservative false-negative bias. A
candidate is drift-flagged iff none of 1/3 match and the line is older
than threshold. Over-flagging nags the agent to add explicit `g4-pass`
annotations, which is the desired behavior.

### B4 — "HIGH or LOW?"

**Attack**: Wave 13 made boot reflexes HIGH because W1 (auto-sediment) is
a named principle and skipping it violates the kernel contract. Is W5
(continuous evolution) equally sacrosanct? A missing Gear 2 reflection
doesn't corrupt data or leak PII; the substrate keeps working.

**Response**: LOW, not HIGH. Reasoning:

- W5 is a **drive**, not a **constraint**. W1 is "if you see information,
  eat it" — a positive obligation with a data-loss failure mode. W5 is
  "the system should improve itself" — a process obligation with a slower
  ossification failure mode.
- Wave 13 `raw_backlog` HIGH has a crisp W1 violation signature (pure raw
  count exceeds threshold = auto-sediment bypassed). Wave 14 session-end
  detectors are about habit decay; they benefit from visibility but don't
  merit the `[REFLEX HIGH]` stop-the-world semantics.
- Concretely: emit the signals without the HIGH prefix. They appear in
  `hunger_signals.advisory` in the `myco_status` response and in
  `myco hunger` plain output. Agent can still skip them if genuinely busy,
  but drift is now visible in every boot report.

This is a **deliberate asymmetry** with Wave 13 and must be justified in
the canon comment.

---

## 3. Round 3 — attack the edges

### C1 — "log.md parsing is fragile"

**Attack**: You're text-searching `log.md` for `^## \[YYYY-MM-DD\] meta \|`
and `g4-candidate`. Log conventions drift. A reformat of the log header
style would silently break detection.

**Response**: Accept. Detectors use **tolerant regex** and fail-open:
- Header regex: `^##\s*\[(\d{4}-\d{2}-\d{2})\]\s+(\w+)` — captures date
  and type token; accepts optional leading space, flexible separator.
- `g4-candidate` regex: `g4-candidate` anywhere on the line — case-
  insensitive.
- On parse failure or missing file: detector returns None (grandfather).
- Thresholds in canon mean a downstream instance can disable either
  check without touching code.

### C2 — "what if log.md is huge?"

**Attack**: Reading the entire log.md on every hunger call. Myco kernel's
current log.md is ~700 lines; no problem. But ASCC's (or future instances')
could easily be thousands.

**Response**: Accept — bound scan to **last 5 MB** of file content on
read. Use `Path.stat().st_size` + seek for files above that cap. For
kernel-scale logs this is a no-op; for large instances it caps work at
constant. Hunger is already not a per-request-hot path (called once per
session boot typically).

### C3 — "interaction with existing stale_raw signal"

**Attack**: `compute_hunger_report` already surfaces `stale_raw`. Adding
two more signals at the session-end stage could cause the advisory block
to feel noisy and agents to learn to ignore it.

**Response**: Accept the noise risk; mitigate by **co-locating** Gear 2
and Gear 4 detectors into a single merged signal when both fire:

```
session_end_drift: gear2 (N log entries since last meta),
gear4 (M g4-candidates older than K days, oldest YYYY-MM-DD)
```

Single line, two facts. Kernel's own first emission will be exactly this
form, with numbers N≈30, M≈18, K=5, oldest 2026-04-07. The agent sees one
item on the advisory list, not two.

### C4 — "dogfood cleanup plan"

**Attack**: Wave 13 landed the feature and cleaned the kernel's dogfood
state (27 notes digested). Wave 14 detectors will immediately fire on
kernel's own log.md with high numbers. Either the feature ships broken
green (we suppress on first emission) or we must clean in the same session.

**Response**: Match Wave 13 discipline — **clean in-session**. Concretely:

1. Implement detectors
2. Write this craft (done)
3. Write a **single** `## [2026-04-11] meta |` entry into log.md that
   reflects on Wave 13+14 as a pair (resets gear2 drift counter)
4. Walk the 18 `g4-candidate` entries: for each, write either a
   `g4-pass:` annotation with a one-line rationale **or** mark it
   `g4-landed` if it already has a craft reference. This is laborious
   but fair: Wave 13 ate 27 notes, Wave 14 eats 18 candidates.
5. Re-run hunger → expect both signals cleared → commit

This keeps the ledger honest and gives Wave 14 the same "landed on a
healthy kernel" property Wave 13 delivered.

---

## 4. Decisions (D1–D8)

- **D1 — New hunger detector**: `detect_session_end_drift(root) -> Optional[str]`
  in `src/myco/notes.py`. Reads `log.md`, parses with tolerant regex,
  computes gear2 count + gear4 oldest-age, emits merged signal when either
  trigger fires. Fail-open on IO errors.

- **D2 — Signal tier**: LOW (advisory). Prefix: none / standard hunger
  signal format. Justified by B4: W5 habit decay, not W1 data loss.

- **D3 — Canon block**: new `system.session_end_reflex` block in both
  `_canon.yaml` and `src/myco/templates/_canon.yaml`:
  ```yaml
  session_end_reflex:
    enabled: true
    severity: LOW   # intentional asymmetry with boot_reflex HIGH
    gear2:
      enabled: true
      drift_threshold_entries: 15
      reflection_marker: "meta"
    gear4:
      enabled: true
      drift_threshold_days: 5
      resolution_markers: ["g4-pass", "g4-landed"]
    log_scan_cap_bytes: 5242880  # 5 MB
  ```
  Each sub-detector independently toggleable per A4 partial-reject.

- **D4 — Wire into `compute_hunger_report`**: detector called after
  craft_reflex, before forage_backlog. On fire, adds one line to
  `signals` list. Try/except grandfathers missing canon block.

- **D5 — Contract version**: bump kernel `contract_version` v0.12.0 →
  **v0.13.0** (minor: new advisory detector, backward-compatible). Both
  canon files and template `synced_contract_version` updated. This will
  trigger the **Wave 13 contract_drift reflex** on next boot of any
  downstream instance — working as designed.

- **D6 — Agent protocol §4 rewrite**: replace current 5-step prose with
  2-step arc mirroring §3:
  ```
  1. myco_hunger (or myco_status with include_hunger)
  2. 处理 session_end_drift 信号 → reflect / sweep / update log / commit
  ```
  Cross-reference this craft file.

- **D7 — Dogfood cleanup in same session**: per C4. Write one `meta`
  entry for Wave 13+14, add `g4-pass:` or `g4-landed:` annotations to
  all 18 existing `g4-candidate` lines, verify hunger green, commit.

- **D8 — Template sync**: `src/myco/templates/MYCO.md` hot-zone boot
  clause adds a bullet for `session_end_drift` so new instances
  inherit the advisory visibility.

- **D9 — Changelog entry**: new `v0.13.0 — 2026-04-11 (minor · session
  end reflex arc, Wave 14 — W5 drift visibility)` block in
  `docs/contract_changelog.md` above v0.12.0 entry. Include migration
  note: "downstream instances will see a new advisory signal; no code
  change required, optional canon override available."

---

## 5. Known limitations

- **L-1 — Pairing is conservative**: g4-candidate resolution via craft
  reference requires the craft file to exist on disk. Candidates resolved
  by inline reasoning without a craft file will over-fire. Mitigation:
  explicit `g4-pass:` annotation path (D1 option 1). Acceptable v1
  tradeoff — nudges agents toward explicit ledger entries.

- **L-2 — Reflection quality is unmeasured**: D2 LOW tier means the
  reflex only checks that *a* `meta` entry was written, not that it was
  substantive. A one-word meta entry satisfies the detector. Deliberate —
  Gear 2 quality is a Self-Model-C-layer problem (open problem §5) and
  out of scope for Wave 14.

- **L-3 — Threshold calibration deferred**: 15 entries / 5 days are
  kernel-tuned defaults. Downstream instances may need different values.
  Both are in canon for override. Post-Wave 14 dogfood over 2-3 sessions
  will confirm or adjust.

- **L-4 — Single log file assumption**: detector reads `log.md` at repo
  root. Multi-log or sharded layouts unsupported. Mirrors other hunger
  detectors; consistent with current schema.

- **L-5 — No sweep automation**: This craft surfaces the drift; it does
  NOT auto-resolve g4-candidates. Sweep remains manual. Gear 4 automation
  would be a separate craft (likely v0.14+).

---

## 6. Confidence

- Target: 0.90 (decision_class: kernel_contract)
- Arrived: **0.91**
- Rationale: direct structural parallel to Wave 13 boot reflex arc, same
  agent-autonomous pattern, same dogfood discipline, explicit asymmetry
  (LOW vs HIGH) justified. Primary residual risk is L-3 (threshold
  calibration) — a knob question, not a structural question. Craft clears
  target.

---

## 7. Landing checklist (Wave 14)

- [ ] Add `system.session_end_reflex` block to both canon files
- [ ] Bump `contract_version` + `synced_contract_version` → v0.13.0 (both)
- [ ] Implement `detect_session_end_drift` in `src/myco/notes.py`
- [ ] Wire into `compute_hunger_report`
- [ ] Rewrite `docs/agent_protocol.md §4` as 2-step arc + cross-ref
- [ ] Add v0.13.0 entry to `docs/contract_changelog.md`
- [ ] Sync `src/myco/templates/MYCO.md` hot-zone bullet
- [ ] Clean kernel dogfood: write one Wave 13+14 `meta` entry
- [ ] Clean kernel dogfood: annotate all 18 `g4-candidate` lines with
      `g4-pass:` / `g4-landed:` / craft reference
- [ ] `myco hunger` → verify session_end_drift cleared
- [ ] `myco lint --project-dir .` → 16/16 green (no new dim; reuses existing)
- [ ] `myco eat` — conclusion note, tags wave14/w5-enforcement
- [ ] Append Wave 14 milestone entry to `log.md`
- [ ] Commit + push via host-side desktop-commander
