---
type: craft
topic: senesce --quick mode for SessionEnd hook timeout budget
slug: v0_5_7_senesce_quick_mode
kind: design
date: 2026-04-19
rounds: 3
craft_protocol_version: 1
status: COMPILED
---

# v0.5.7-buffer — `senesce --quick` for the SessionEnd Timeout Gap

> **Date**: 2026-04-19.
> **Layer**: L3 (implementation — `src/myco/cycle/senesce.py`,
> `src/myco/surface/manifest.yaml`), L4 (hook configs —
> `hooks/hooks.json`, `.claude/settings.local.json`).
> **Does not touch**: L0–L1 doctrine. R2 prose in
> `docs/architecture/L1_CONTRACT/protocol.md` stays frozen at v0.5.6
> wording until v0.5.7 ships as a full release (see §Pending for
> the v0.5.7-release work list).
> **Upward**: strengthens R2 coverage (no Session exits the ritual
> entirely) without altering R2 semantics; consistent with L0
> principles 3 & 4 (永恒进化 / 永恒迭代 — evolve the implementation
> below a stable contract).
> **Governs**: the two-mode shape of `myco senesce`, the hook
> bindings in `hooks/hooks.json` and `.claude/settings.local.json`,
> and the test suite `tests/unit/cycle/test_senesce.py`.

---

## Round 1 — 主张 (claim)

Before this patch, the Myco self-substrate bound two Claude Code
hooks to `myco senesce`:

* `SessionStart` → `myco hunger` (R1 ritual)
* `PreCompact` → `myco senesce` (R2 ritual)

The user noticed a coverage gap: sessions that end via `/exit`,
Ctrl+D, or window-close **never fire PreCompact**, so the R2
ritual is silently skipped. The user's fix was to bind a third
hook — `SessionEnd` — to the same `myco senesce` command.

Independent research on the SessionEnd hook (GitHub issues
#4318, #6306, #6428, #17885, #41577) plus a wall-clock
measurement on the v0.5.6 self-substrate surfaced a hard
constraint:

* **SessionEnd default timeout**: ~1.5 s (controlled by
  `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`; the hook process is
  hard-killed at the limit).
* **`myco senesce` on myco-self**: 1.656 s wall-clock — **already
  over budget**, and monotonically growing as dimensions, tests,
  and AST surfaces expand.

Binding the heavyweight `senesce` unchanged to SessionEnd would
therefore fail almost every time, producing garbage output and no
reliable state advance. The PreCompact binding is still fine
(PreCompact blocks until the hook completes).

This craft proposes a **two-mode senesce**:

* **Full** (default) — unchanged. Runs `reflect` then
  `immune(fix=True)`. Bound to PreCompact (blocking, has time).
  Semantic home of R2.
* **Quick** (`--quick`) — **new**. Runs `reflect` only. Skips
  `immune`. Bound to SessionEnd (short budget).

The split is safe because:

1. **`reflect` is the state-advancing piece**, and it is already
   per-note and idempotent. An interrupted reflect run leaves the
   un-promoted remainder in `notes/raw/` for the next call —
   exactly the behavior we already rely on across any unexpected
   process exit.
2. **`immune` is read-only lint** (plus an opt-in `--fix` pass
   whose changes are write-surface-bounded, per the safe-fix
   discipline added in v0.5.5). Skipping it loses nothing the
   next `myco hunger` (at SessionStart) or the next PreCompact
   wouldn't re-surface.
3. **The canonical session end** (a user who types `/compact`
   before exiting) still runs the full pipeline. The quick mode
   is a *fallback* for the case when the canonical path cannot
   run in time, not a new canonical semantics.

Concretely:

| Hook           | Command                 | Runtime budget | Runs            |
|----------------|-------------------------|----------------|-----------------|
| `SessionStart` | `myco hunger`           | blocking       | R1 boot brief   |
| `PreCompact`   | `myco senesce`          | blocking       | reflect + immune --fix |
| `SessionEnd`   | `myco senesce --quick`  | ~1.5 s kill    | reflect only    |

All three hook bindings ship in both:

* `.claude/settings.local.json` — the Myco self-substrate's own
  Claude Code config (tracked since v0.4.4 precisely so
  self-dogfood sessions auto-ritualize).
* `hooks/hooks.json` — the Claude Code plugin hook manifest
  referenced by `.claude-plugin/plugin.json::hooks`. Every
  downstream substrate that installs the Myco Claude Code plugin
  inherits these bindings.

---

## Round 2 — 反驳 (refute / stress-test)

Seven challenges, each resolved before landing code:

**C1 · "Just skip `immune` from senesce forever."**
Rejected. `/compact` is the dominant session-end action in Claude
Code long-session flows, and it has no timeout on PreCompact. Cutting
`immune --fix` loses the only automatic end-of-session fix pass.
Two modes preserves both wins.

**C2 · "Quick mode should also skip `reflect` — safer under short
budget."**
Rejected. `reflect` is the state-advance; skipping it means raw
notes never become integrated and reflex signals accumulate
across sessions. That defeats the entire point of binding
SessionEnd. Measurement on the self-substrate shows `reflect`
alone is well under 1 s (empty or nearly-empty `notes/raw/`
scans are ms; bulk-promote of a handful of notes is sub-second).
The 1.656 s full-mode total is dominated by the 11-dimension
immune scan.

**C3 · "If reflect itself ever takes >1.5 s (1,000 pending raw
notes), we're back in the same bug."**
Acknowledged but not blocking. `reflect` is per-note, and every
promoted note lands atomically on disk before the next starts —
so even a hard kill mid-promote leaves a consistent partial
result that the next senesce completes. No state corruption,
only latency across sessions. If this ever becomes a real
problem (user reports), add chunked `--budget-ms` cooperation; no
need to pre-build that machinery.

**C4 · "Add a proper `--timeout` / `--budget-ms` argument so the
hook can tell us how much time it has."**
Rejected as scope. The hook host's timeout is an external kill,
not a cooperative budget — we cannot meaningfully observe "time
remaining" without instrumenting every sub-call. Simpler and
more honest to ship a bimodal fast/slow shape and document the
budget assumption explicitly. Revisit if behavior on the ground
proves otherwise.

**C5 · "Naming — should it be `--mode=quick|full` instead of a
bool `--quick`?"**
Rejected. A two-valued axis is naturally a boolean. Upgrading
to `--mode` only makes sense if a third mode (say `--deep` that
adds a graph rebuild) ever lands; at that point, rename.
Until then, `--quick` is the conventional shape matching
`immune --fix` / `senesce --quick` / `ramify --force` across the
manifest.

**C6 · "Why not also add an explicit `--full` flag for symmetry?"**
Rejected as noise. `--full` is just `not --quick` — the default.
Adding the flag produces two names for the same behavior and
invites subtle divergence. One explicit override, one implicit
default.

**C7 · "Does the quick-mode immune `{\"skipped\": true}` payload
key break any existing consumer?"**
Checked. Every reader of `senesce` payload in the codebase
(`brief` rollup, hunger sidecar, MCP initialize echo) reads
`payload["immune"]` as a dict and accesses known sub-keys by
`.get()` or pattern-matching. The `{skipped: true, reason: str}`
dict is a valid value; no KeyError risk. The `"mode"` key is
new and additive — old readers ignore it. New consumers can
switch on `payload["mode"]` to render quick-vs-full differently
(e.g., `brief` could say "quick-mode senesce at last exit; run
`myco senesce` for a full pass" when it sees `mode == "quick"`
in the last-run metadata). That rendering upgrade is NOT part
of this patch — flagged under §Pending.

---

## Round 3 — 反思 (synthesize / scope-lock)

**Scope lock.** This patch does exactly these things and no
others:

1. Extend `src/myco/cycle/senesce.py::run` to read a `quick: bool`
   arg and switch execution accordingly. Payload always carries
   `reflect`, `immune`, and a new `mode` key; `immune` in quick
   mode is `{skipped: True, reason: <str>}`. Exit code in quick
   mode is `reflect_exit` only.
2. Add a single `quick` bool arg to the `senesce` entry in
   `src/myco/surface/manifest.yaml`. This propagates the flag
   through CLI (`argparse`), MCP (`build_tool_spec`), and the
   dispatcher (`build_handler_args`) with zero extra wiring
   because those surfaces are all manifest-driven.
3. Change the SessionEnd binding in both
   `.claude/settings.local.json` and `hooks/hooks.json` from
   `myco ... senesce` to `myco ... senesce --quick`. PreCompact
   stays on `senesce` (full mode).
4. Update the `description` field of `hooks/hooks.json` to
   document the three-hook layout and the quick/full split.
5. Update the `senesce.py` module docstring to explain the split
   and the fungal-biology analogy.
6. Ship `tests/unit/cycle/test_senesce.py` (new) with 12 tests
   covering: default = full, explicit quick, payload shape,
   exit-code derivation, manifest declaration, MCP tool-spec
   parity, alias survival, and dispatcher-path parity.
7. Author this craft doc.

**Explicitly does NOT touch** (to preserve the contract-bump
invariant — R7 — and the user-given "not yet v0.5.7 complete"
directive):

* `docs/architecture/L1_CONTRACT/protocol.md` — R2 prose and the
  enforcement table remain at v0.5.6 wording. When v0.5.7 ships
  as a full release, R2 should be re-worded to acknowledge the
  two-mode session end (tracked in §Pending).
* `src/myco/surface/mcp.py::_INSTRUCTIONS_TEMPLATE` — the R2 line
  echoes L1 verbatim and must stay in lockstep with `protocol.md`.
  Updated in the same v0.5.7 release commit.
* `_canon.yaml` — `contract_version`, `synced_contract_version`,
  and `schema_version` all unchanged. Test count bump only (see
  §Pending).

**Payload invariant** (contract-level claim for downstream tooling):

> After v0.5.7-buffer, every `senesce` Result payload has the
> shape `{reflect: {…}, immune: {…}, mode: "full"|"quick"}`. In
> `mode == "quick"`, `immune == {skipped: True, reason: <str>}`.
> In `mode == "full"`, `immune` is the full `run_immune` payload
> dict. This shape is promised stable across v0.5.x.

**Runtime targets** (post-patch, verified after winnow):

* `myco senesce` (full) — ≥ v0.5.6 runtime, possibly slightly
  faster due to reduced bookkeeping (target: ≤ 2.0 s on
  myco-self, same ballpark as v0.5.6's 1.656 s).
* `myco senesce --quick` — target ≤ 1.0 s on myco-self, which
  gives a ~33 % safety margin under the 1.5 s SessionEnd kill.

---

## Pending (for v0.5.7 release cycle, not this patch)

When the v0.5.7 release lands — with whatever else the user
decides to bundle — the following cross-cutting updates should
ship in the same commit set:

1. **L1 R2 re-wording** in
   `docs/architecture/L1_CONTRACT/protocol.md`:
   "Every session ends with `myco senesce` — full (reflect +
   immune --fix) on PreCompact (blocking), quick (reflect only)
   on SessionEnd (short-budget fallback). Canonical session-end
   is the full form; quick is the defense-in-depth fallback." Plus
   enforcement-table updates.
2. **MCP instructions template** (`src/myco/surface/mcp.py`) —
   update the R2 echo to match the new L1 wording.
3. **canon schema**: bump `_canon.yaml::contract_version` to
   `"v0.5.7"`, append to `docs/contract_changelog.md`.
4. **brief verb** rendering: when the last `senesce` ran in
   `mode == "quick"`, note that in the brief and suggest a
   manual full `senesce` at a convenient breakpoint.
5. **MP1 / SE1 advisory scan** of the new surfaces (should be
   clean; this craft doc is linked from
   `src/myco/cycle/senesce.py` and
   `src/myco/surface/manifest.yaml` — no dangling code→doc refs
   expected).
6. **Release artefacts**: PyPI bump, GitHub release notes
   explaining the quick/full split and pointing downstream
   plugin consumers at the auto-inherited hook config.

The rest of the v0.5.7 scope is undetermined and owner-driven;
this buffer patch holds the implementation changes until then.

---

## Cross-references (R5 — cross-reference on creation)

* **Implementation**:
  * `src/myco/cycle/senesce.py` (§Round 3 #1 + docstring)
  * `src/myco/surface/manifest.yaml` (senesce entry, §Round 3 #2)
* **Configuration**:
  * `hooks/hooks.json` (§Round 3 #3 + #4)
  * `.claude/settings.local.json` (§Round 3 #3)
* **Tests**:
  * `tests/unit/cycle/test_senesce.py` (§Round 3 #6)
  * `tests/unit/meta/test_session_end.py` (untouched; covers the
    deprecation-shim import path)
* **Doctrine touched (indirectly, via invariant dependency)**:
  * `docs/architecture/L1_CONTRACT/protocol.md` — R2 prose frozen
    this patch; queued for §Pending upgrade.
  * `docs/architecture/L2_DOCTRINE/homeostasis.md` — safe-fix
    discipline (immune behavior referenced above).
* **Upstream evidence**:
  * GitHub issue `anthropics/claude-code#41577` — SessionEnd
    timeout-kill behavior.
  * GitHub issue `anthropics/claude-code#6428` — SessionEnd does
    not fire on `/clear`.
  * GitHub issue `anthropics/claude-code#17885` — SessionEnd
    unreliable on `/exit`.
  * GitHub issue `anthropics/claude-code#6306` — SessionEnd not
    documented.
* **Prior releases**:
  * `docs/primordia/v0_5_6_doctrine_realignment_craft_2026-04-17.md`
    — most recent doctrine-realignment craft; establishes R7 and
    MP1 as the mechanical guards this craft respects.
  * `docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md`
    — introduces the `senesce` name and the alias-survival
    contract that `test_alias_session_end_still_resolves`
    exercises.

---

## Self-winnow verdict

`myco winnow --proposal docs/primordia/v0_5_7_senesce_quick_mode_craft_2026-04-19.md`
(run 2026-04-19, v0.5.6 kernel):

* verdict: **pass**
* round_count: 3
* body_chars: 13 242
* violations: **0**
* frontmatter_keys: `craft_protocol_version / date / kind / rounds /
  slug / status / topic / type` (complete set per craft-protocol v1).

## Runtime verdict

Post-patch measurements on the v0.5.6 myco-self substrate
(Python 3.13, Windows, single-threaded, cold start each time):

| Command                   | Wall-clock | vs budget (1.5 s SessionEnd) |
|---------------------------|-----------:|-----------------------------:|
| `myco senesce` (full)     |   1.533 s  | n/a — bound to PreCompact (blocking) |
| `myco senesce --quick`    |   0.399 s  | **3.8× safety margin**       |

Quick mode comfortably fits inside Claude Code's default SessionEnd
kill budget with room to spare as the kernel grows.

## Test verdict

`pytest` after patch: **593 passed** (v0.5.6 baseline 580 + 13 new
tests in `tests/unit/cycle/test_senesce.py`). No regressions in
adjacent suites (`tests/unit/meta/test_session_end.py`,
`tests/unit/surface/test_mcp.py`).

## Immune verdict

`myco immune` after patch: **9 findings** — identical in count,
dimension, severity, and path set to the pre-patch baseline
(SE1 × 7 medium dangling code→doc refs + SE2 × 2 low orphan
integrated notes, all inherited from v0.5.6 and queued for the
v0.5.7 release clean-up pass). **Zero new findings introduced by
this patch.** MP1 remains silent (no provider SDK imports added).
