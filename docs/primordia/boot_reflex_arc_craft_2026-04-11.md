---
type: craft
status: ACTIVE
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.91
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Boot Reflex Arc — Making Session Boot Metabolically Mandatory

**Parent contradictions**:
- `docs/agent_protocol.md §3` prescribes a 4-step boot sequence (`myco_status → myco_hunger → myco_digest → task`) but only `agent_protocol.md §8.4` contract-version lock is similarly documented; neither is wired into code.
- `docs/primordia/craft_autonomy_craft_2026-04-11.md` (Wave 12) established the rule: "Substrate-level processes must not depend on external signal to fire." Session boot is as substrate-level as metabolism — but currently it is exactly as advisory as pre-Wave-12 craft was.
- **Realtime dogfood evidence**: `myco hunger` on the Myco kernel repo itself reports **27 raw notes** at the moment this craft is written. The kernel fails its own digestive reflex. A substrate that cannot metabolize its own notes cannot honestly claim to be one.
- `_canon.yaml::system.upstream_scan_last_run` is defined as a null field that no code path ever writes — a declared reflex with no nervous system.

**Scope**: this craft decides how the session-boot obligation moves from documented ritual into an autonomous reflex arc, in the same shape as Wave 12 craft reflex. It does *not* claim to solve metabolic inlet (open_problems §1–4); it only closes the gap between "kernel tells you to boot" and "boot actually happens or lint turns red".

---

## 0. Problem definition

Wave 12 established the invariant: if a reflex is reflexive in theory but
advisory in practice, some non-zero fraction of occurrences will silently
ship. The proof was Wave 10's README trilogy rewrite, which skipped craft
because craft was advisory.

The same pattern applies to three boot-class reflexes that are **still**
advisory today:

| Reflex | Documented in | Enforced by |
|---|---|---|
| contract version drift check | `agent_protocol.md §8.4` (Upstream Protocol v1.0) | nothing — no code compares `synced_contract_version` to kernel's `contract_version` |
| session boot hunger consumption | `agent_protocol.md §3` (4-step boot) | nothing — `myco_status` doesn't invoke hunger; raw_backlog is text advisory |
| raw_backlog metabolic obligation | `notes.py::compute_hunger_report` (emits signal string) | nothing — severity is implicit TEXT; craft_reflex (HIGH) is asymmetrically stricter |

Concretely, three failure modes are currently possible and undetectable:

1. **Version-locked drift**: Instance on v0.8 talks to kernel on v0.11.
   The instance follows pre-Wave-11 reflex rules, ships edits that would
   fire L15 today. No lint catches this because the instance's local
   lint was compiled from its own older `_canon.yaml`.

2. **Boot skip**: Agent opens a session, goes straight to task work,
   never runs hunger. raw_backlog grows silently. The session-end hunger
   pass is optional (end sequence §4). A full session can ship without
   touching the digestive substrate at all.

3. **Metabolic constipation (live right now)**: Myco itself. 27 raw
   notes. 0 actions taken per recent sessions to drain them. raw_backlog
   emits but agent treats it as informational. This is exactly the
   advisory-not-arc gap Wave 12 closed for craft.

Leaving any of these three at "LOW signal + hope the agent notices" is
a post-Wave-12 inconsistency. The substrate has a category of reflex
(`craft_reflex_missing`) where failure to act in-session is a W3
violation — but symmetrical digestive and version-lock reflexes are left
at advisory severity. That asymmetry is arbitrary and cannot be
justified from Myco's identity anchors.

---

## 1. Decision candidates

- **C1 (do nothing)**: Leave boot obligations as prose in
  `agent_protocol.md`. Rejected immediately — same posture as
  pre-Wave-11 craft; we know the failure rate is non-zero and the
  27-raw-note dogfood datum proves it.

- **C2 (add advisory signal only)**: Emit a `boot_incomplete` signal
  in `myco hunger` when drift is detected, ask the agent to notice.
  Rejected — this is exactly the advisory gradient Wave 12 identified
  as insufficient. Adding a fourth low-severity signal does not change
  the arc.

- **C3 (full reflex arc, in-session execution mandate)** ✅: Make these
  three reflexes symmetrical to craft reflex.
  - Implement `detect_contract_drift(root, canon)` that compares
    `system.synced_contract_version` to kernel's `contract_version`
    (read from `pyproject.toml` or a package constant) and emits a
    HIGH signal when they differ.
  - Upgrade `raw_backlog` signal phrasing to carry explicit reflex
    language (HIGH severity, in-session digest obligation, bypassing
    via inaction is a W1 violation).
  - Wire `myco_status` MCP tool to auto-invoke hunger when called
    without an explicit opt-out, and surface drift + raw_backlog in
    its response body (so that the documented `myco_status → work`
    short-circuit still sees the signals).
  - Add `boot_sequence_incomplete` signal that fires if
    `upstream_scan_last_run` is stale (> lookback_days) AND any
    trigger-surface file in `write_surface.allowed` was touched in the
    current git state — analogous to craft reflex's mtime probe.

- **C4 (new L16 lint)**: Add a dedicated lint dimension for boot
  drift. Rejected as over-instrumentation — the check is a cheap canon
  read, and hunger is the right surface (it is already consulted at
  every session boundary and is the reflex-arc surface by Wave 11
  precedent).

**Decision**: C3.

---

## Round 1 · Attack surface

**A1 (version comparison is brittle)**: What if `pyproject.toml` ships
a dev suffix like `0.11.0.dev1`? Contract version is separate from
package version. — **Response**: Read `system.contract_version` from
the *kernel's* `_canon.yaml` on disk, not from package metadata. The
kernel repo is detectable via git remote or fallback to `importlib.
resources` pointing at `src/myco/templates/_canon.yaml` which is the
version shipped to instances. When instance runs lint on itself, both
files coexist — but for a real instance, we compare local
`system.synced_contract_version` to the shipped template's
`system.synced_contract_version` (that template is updated every
release). This means **the shipped template is now a contract ledger**,
not just a bootstrap seed. Accept this as a new invariant.

**A2 (`myco_status` auto-hunger breaks read-only hint)**: `myco_status`
is annotated `readOnlyHint=True`. Calling hunger inside it would not
break read-only (hunger is read-only too), but wiring them couples
two MCP tools. — **Response**: Keep them decoupled at the API level.
Add an optional `include_hunger: bool = True` parameter to
`myco_status`. Default True makes boot check atomic; False preserves
the old behavior for agents that specifically want the lightweight
dashboard. Hunger is already readOnly so annotations remain honest.

**A3 (Wave 12 asymmetry critique cuts both ways)**: If every reflex
has to be HIGH, then hunger will fire five HIGH signals simultaneously
and nothing is distinguishable. Severity inflation. — **Response**:
HIGH is for arcs whose inaction violates a named protocol principle.
raw_backlog inaction violates **W1 autopilot** (auto-sedimentation)
the same way craft_reflex inaction violates **W3 craft**. Both are
named principles. The other signals (stale_raw, no_deep_digest, etc.)
remain advisory because they are *information* — how the substrate is
metabolizing — not *protocol violations*. Severity is not flat, it
reflects whether the underlying rule is a named principle or a soft
preference.

**A4 (27 raw notes is not a bug, it's pre-compaction context)**: What
if the 27 raw notes in the kernel repo represent intentional backlog
that Phase ② will consume wholesale? — **Response**: Partially accepted.
Inspect the 27 before writing the dogfood patch. If they are all
friction-phase2 notes intentionally waiting for Phase ② ignition, they
should be marked `digesting` with `digest_count=1` to indicate
"reviewed, held for batch processing", and raw_backlog should then only
count notes that are truly raw (digest_count=0 AND never touched).
Decision: add `raw_backlog` refinement — only pure-raw notes count,
digesting-held notes do not.

**A5 (boot_sequence_incomplete signal will overlap with
craft_reflex_missing)**: Touching a trigger-surface file already fires
craft_reflex. Adding boot_sequence_incomplete on the same surface
creates duplicate HIGH signals on the same edit. — **Response**: They
are different reflexes. Craft reflex asks "did you write a decision
record?", boot reflex asks "did you boot the session properly?". The
Venn intersection (edited kernel file without writing craft AND
without running hunger) fires both; agent fixes both. No duplication —
the two signals have distinct remedies. Keep separate.

**A6 (27 raw notes dogfood — who digests them?)**: This craft is
writing itself. The agent landing it must also drain the 27 notes
in-session. Is the context budget sufficient? — **Response**: The
dogfood cleanup is part of the landing list. If budget runs out,
partial cleanup is acceptable provided raw_backlog drops below 10
(the signal threshold). Batch 2 can finish any remainder. Record in
the landing list the exact count achieved.

**A7 (changing `upstream_scan_last_run` to be written by code is a
contract change, not a reflex)**: This isn't a reflex arc question,
it's a missing feature. — **Accept partially**. Split: the
`detect_contract_drift` part IS reflex-arc work (it fires a signal).
The `upstream_scan_last_run` write-path work is a separate fix
belonging in Batch 4. Remove from this craft and re-scope Batch 1 to
contract drift + raw_backlog HIGH + boot hunger wiring + dogfood only.
Batch 4 will handle the scan-timestamp write path.

---

## Round 2 · Second attack after R1 revisions

**B1 (HIGH severity for raw_backlog is Wave 12 cargo-cult)**: Just
because craft reflex is HIGH doesn't mean every metabolic signal must
be HIGH. This is reflex hypertrophy. — **Response**: The argument is
not "Wave 12 therefore HIGH". The argument is "W1 is a named kernel
principle, violating it without consequence falsifies the principle".
Wave 12 proved the general shape: advisory-tier reflex for a named
principle is indistinguishable from no reflex at all. W1 is at least
as foundational as W3. Either raise W1 enforcement to match, or admit
W1 is aspirational and downgrade it in `_canon.yaml`. The latter is
not acceptable — W1 is auto-sedimentation, the foundational premise
of the entire digestive substrate. Therefore raise enforcement.

**B2 (contract drift = W1? No, W? not specified)**: Which principle
does contract drift map to? — **Response**: Upstream Protocol v1.0,
which is not a W-principle, is a contract-level invariant documented
in `docs/agent_protocol.md §8`. Drift violates §8.4 ("instance must
compare synced_contract_version against kernel contract_version at
boot and refresh local reflexes if drift is detected"). This is a
**§8 contract-level invariant violation**, higher weight than any
single W-principle. HIGH is correct.

**B3 (auto-hunger in myco_status will produce noisy output)**: Agents
that call `myco_status` once per task will see hunger output every
time. — **Response**: hunger is O(notes) and notes are bounded (30 in
a healthy substrate, 100 in a stressed one). The signal block is
~10 lines max. Adding 10 lines to status output is cheap. Agents that
want the lean version pass `include_hunger=False`. Default to True
because the entire point is to make boot atomic.

**B4 (Myco's 27 notes may include notes I wrote in this session)**:
Self-reference: this craft file will become the 28th untouched
doc-primordia entry, and the notes I eat during landing will push
raw count up further. — **Response**: Correct. Eat ordering matters:
(a) write craft, (b) implement code, (c) dogfood-digest the existing
27 raw notes first, (d) eat the Wave 13 conclusion note last. The
conclusion note is then the only raw note left, and it will be
digested immediately to `integrated` as part of landing. Net delta:
raw_count: 27 → 0.

---

## Round 3 · Final sweep

**C1 (the raw_backlog signal message format is not defined)**: HIGH
severity needs consistent prefix across reflex signals. — **Response**:
Standardize prefix `[REFLEX HIGH]` at the start of any reflex-class
signal string. Update craft_reflex signal (already exists) to use the
same prefix. This is a UX fix that makes reflex signals visually
distinct from advisory signals in hunger output.

**C2 (contract_drift signal when kernel version unreadable)**: What
if the local instance is *the kernel itself* and there's no "other"
template to compare to? Self-reference loop. — **Response**:
`detect_contract_drift` reads `system.synced_contract_version` and
`system.contract_version` from the **same** `_canon.yaml` when running
on a kernel repo. For instances, `synced_contract_version` is in the
local `_canon.yaml` and `contract_version` lives in the kernel
template shipped in `src/myco/templates/_canon.yaml`. The detector
chooses: if a local repo's `_canon.yaml::system.contract_version`
exists (kernel self-check), compare it to synced. Otherwise look up
the package-local template. For the kernel itself running on itself,
both values exist in the same file and must be equal — drift is
caught at the same pass. Fail-closed: unreadable template = fire LOW
signal (don't block, but complain).

**C3 (README.md boot reflex docs)**: Documentation update for the
README / MYCO.md template / agent_protocol.md §3 — where does the
new enforced boot sequence get written? — **Response**:
`docs/agent_protocol.md §3` already prescribes the sequence; add a
sentence noting the enforcement is now code + hunger arc, not just
prose. Update the `src/myco/templates/MYCO.md` hot zone to reference
the new reflex. Do NOT rewrite README.md — this is an enforcement
change, not a public-surface claim change.

**C4 (what stops the agent from disabling `include_hunger` in every
`myco_status` call?)**: Reflex bypass loophole. — **Response**: Same
defense as Wave 12 `--no-verify` clause: setting `include_hunger=False`
while raw_backlog is > 10 is itself a W1 violation and should be
tracked. Lower priority than Wave 12's concern because there's no
auditable flag (`include_hunger` is a parameter, not a CLI flag).
Mitigation: `myco_status`'s tool docstring explicitly names
`include_hunger=False` as "bypass requires justification; creates W1
violation if raw_backlog is non-empty". Documentation over mechanism
here — Wave 12 arc already covers the underlying invariant, this is
just a specific case.

---

## 2. Final decisions

- **D1**: Implement `detect_contract_drift(root, canon) -> Optional[str]`
  in `src/myco/notes.py` (parallel to `detect_structural_bloat` /
  `detect_craft_reflex_missing`). Fires `[REFLEX HIGH] contract_drift`
  when local `synced_contract_version` ≠ kernel `contract_version`.
  Wired into `compute_hunger_report`.

- **D2**: Add `[REFLEX HIGH]` prefix to `raw_backlog` and
  `craft_reflex_missing` signal strings. Add explicit W1/W3 invariant
  language to raw_backlog message. raw_backlog counts only
  `digest_count == 0` AND `source != "bootstrap"` notes — the
  "bootstrap" exemption prevents fresh `myco init` repos from firing
  on seed data.

- **D3**: Refine `raw_backlog` threshold logic: `digesting`-state notes
  with `digest_count ≥ 1` no longer count toward raw_backlog (per A4).
  This is a single-line change in `compute_hunger_report`.

- **D4**: Add `include_hunger: bool = True` parameter to `myco_status`
  MCP tool. When True (default), invoke `compute_hunger_report` and
  attach its signals to the status response under a `hunger_signals`
  key. Tool docstring explicitly warns that `include_hunger=False`
  while raw_backlog > threshold is a W1 violation.

- **D5**: Update `_canon.yaml::system` to carry a new block:
  ```yaml
  boot_reflex:
    enabled: true
    severity: HIGH
    raw_backlog_threshold: 10   # existing implicit value → explicit
    reflex_prefix: "[REFLEX HIGH]"
  ```
  Under `craft_protocol.reflex` keep existing block. New `boot_reflex`
  is sibling, not nested, so `_canon.yaml` stays shallow.

- **D6**: Upstream Protocol v1.0 `contract_version` field — audit the
  canon: currently only `synced_contract_version` is declared on the
  instance side. Add a kernel-side `contract_version: "v0.12.0"` to
  `_canon.yaml` explicitly. (Wave 13 bumps kernel version to v0.12.0.)

- **D7**: Dogfood cleanup: inspect the 27 raw notes currently in the
  Myco kernel repo, digest each to `extracted` or `integrated` based
  on content, or `excreted` with reason if stale. Target post-landing
  state: raw_count ≤ 1 (this craft's conclusion note pre-digest).

- **D8**: Contract version bump v0.11.0 → v0.12.0. Update
  `contract_changelog.md` with Wave 13 entry referencing this craft.

- **D9**: Templates sync: propagate `boot_reflex` block and
  `synced_contract_version: v0.12.0` to
  `src/myco/templates/_canon.yaml`.

---

## 3. Known limitations (carried forward as future work)

- **L-1**: `detect_contract_drift` currently only compares the version
  string. It does not verify that the instance's reflex *implementations*
  match kernel's. A pinned v0.12.0 instance that also patches
  `lint_craft_reflex` locally is structurally indistinguishable from
  a clean v0.12.0 instance. This is the same honor-system ceiling
  Wave 12 acknowledged.

- **L-2**: `include_hunger=False` bypass is documentation-only.
  No code enforces it. A malicious/exhausted agent can silently skip
  boot hunger. Same mitigation strategy as `--no-verify` — trust plus
  async audit.

- **L-3**: The `raw_backlog_threshold: 10` value is bootstrap, not
  empirically calibrated. If Phase ② friction data reveals agents
  consistently hit 10 raw notes mid-session for legitimate reasons
  (e.g., a burst of forage absorb), we will raise it. For now 10 is
  conservative-enough that even the kernel repo triggered at 27.

- **L-4**: Contract version comparison happens at `myco hunger` time,
  which is at most once per session boot. A session that drifts into
  a kernel bump *mid-session* (someone runs `git pull` in parallel)
  will not refire the signal until next boot. Acceptable — sessions
  are the atomic unit per Wave 11 reasoning.

---

## 4. Landing list

1. ✅ L1 — This craft file (`boot_reflex_arc_craft_2026-04-11.md`)
2. Update `_canon.yaml::system.contract_version` → `"v0.12.0"`
3. Add `_canon.yaml::system.boot_reflex` block per D5
4. Implement `detect_contract_drift` in `src/myco/notes.py`
5. Refine `raw_backlog` counting logic per D3 + reflex prefix per D2
6. Add `[REFLEX HIGH]` prefix to existing `craft_reflex_missing` signal
7. Wire `include_hunger: bool = True` into `myco_status` MCP tool
8. Update `docs/agent_protocol.md §3` + §8.4 enforcement note
9. Update `src/myco/templates/_canon.yaml` (sync boot_reflex + v0.12.0)
10. Update `src/myco/templates/MYCO.md` hot-zone boot obligation text
11. Update `docs/contract_changelog.md` with Wave 13 entry
12. Dogfood: digest the 27 raw notes in Myco repo — target raw_count ≤ 1
13. Dual-path `myco lint --project-dir .` green (16/16)
14. `myco hunger` shows no `[REFLEX HIGH]` signals
15. `myco eat` conclusion note (friction-phase2, w1-enforcement tag)
16. `log.md` Wave 13 milestone + craft_reference
17. Git commit + push

**Craft reference ID**: boot_reflex_arc_craft_2026-04-11

**Confidence**: 0.91. Raised from 0.85 bootstrap after Round 1 A4
split, Round 2 B1 W1-principle mapping, Round 3 C1 prefix
standardization. Not higher because L-1 (honor-system ceiling)
and L-3 (threshold calibration) remain unaddressed until Phase ②
data arrives.
