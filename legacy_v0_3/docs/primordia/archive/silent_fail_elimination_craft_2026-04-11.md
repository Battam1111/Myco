---
type: craft
status: ARCHIVED
created: 2026-04-11
target_confidence: 0.90
current_confidence: 0.92
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
---

# Silent-Fail Elimination — Grandfather Ceiling + Strict Project-Dir (Wave 20)

## 0. Problem definition

Panorama round 2 note `n_20260411T235030_f184` surfaced two holes
that share a single pathology — **"missing configuration triggers
silent pass instead of loud alarm"**:

- **NH-2 (CRITICAL)** — `detect_contract_drift` in `notes.py:705`
  gates *all* detection behind `boot_reflex.get("enabled", False)`.
  Instances whose canon predates Wave 13 (when boot_reflex was
  introduced) have **no `boot_reflex` block at all**. The default
  `False` means the detector returns `None` immediately. Live
  evidence: ASCC is pinned to `synced_contract_version: v0.8.0`
  while kernel is `v0.18.0` — ten minor versions of drift — and
  `myco hunger` on ASCC reports `healthy`. The Wave 13 reflex arc
  is invisible to the one instance that needs it most.

- **NH-1 (HIGH)** — `_project_root` in `notes_cmd.py:44` walks up
  for `_canon.yaml` and on failure falls through to
  `return Path(raw).resolve()`. `compute_hunger_report` then runs
  on a directory with no `notes/` subdir and silently reports
  `total notes: 0 · healthy-ish`. Live evidence: running
  `myco hunger --project-dir .` from `/tmp` returned a clean
  report with no warning that `/tmp` is not a Myco project.

Both failures produce **false confidence** — the worst possible
failure mode for a sensory system. A crash is recoverable because
the agent *knows* something is wrong. A silent zero is
indistinguishable from a truly-healthy signal.

## Round 1 — structural debate

**A1 (Proposal).** Two coordinated changes:

1. **Grandfather ceiling** for `detect_contract_drift`. Even when
   `boot_reflex` is absent or disabled, if `synced_contract_version`
   is present and differs from kernel `contract_version` by more
   than N minor versions (default 5), emit a
   `[REFLEX HIGH] grandfather_expired` signal that bypasses the
   enabled-gate. This gives grandfather compatibility a hard ceiling.

2. **Strict project-dir resolution**. `_project_root` stops
   fall-through on no-canon. Instead, it raises
   `MycoProjectNotFound` which the CLI layer catches and prints a
   single clear error: `myco hunger: not a Myco project
   (no _canon.yaml found above <path>) — did you forget to cd or
   pass --project-dir?`. Exit 2.

**A2 (Attack — ceiling arbitrariness).** "5 minor versions" is a
magic number. Why 5? Why not 3 or 10? And how is "minor version
gap" computed when one side is `v0.8.0` and the other is
`v0.18.0` — is that gap 10 or something else?

**A3 (Defense — principled choice + config-driven).**
- **5 is the default, not the law**. Put it in
  `canon.system.boot_reflex.grandfather_ceiling_minor_versions`
  so every instance can override. The number lives in canon, not
  code. Agents that want looser discipline can set 10; paranoid
  ones can set 1.
- **Gap computation**: parse `vMAJOR.MINOR.PATCH` into a tuple and
  compare lexicographically with emphasis on minor. For v0.8.0 vs
  v0.18.0 the minor gap is 10. Ignore patch drift (x.y.0 vs x.y.3
  is 0 minor gap). Major mismatch is *always* a REFLEX HIGH
  regardless of ceiling — majors are never grandfathered.
- **Fail-open for malformed versions**: if either side fails to
  parse as semver, emit a different signal
  `[REFLEX MEDIUM] version_parse_error` and return. Never silent
  pass.

**A4 (Attack — ASCC migration lock-in).** If I land this wave,
ASCC's next `myco hunger` will immediately fire REFLEX HIGH. That
blocks ASCC's Phase 2 experiment work until someone manually
imports the contract. The agent running ASCC has zero knowledge
of ten minor versions of contract changelog — they'd have to read
everything from v0.9.0 to v0.18.0 before making any "kernel-class
action". That's not zero cost.

**A5 (Defense — that's the feature, not the bug).** The entire
point of NH-2 is that ASCC has been operating under a stale
contract the whole time. "It's annoying for the agent to catch up"
is a cost, but the alternative is "the agent silently violates
invariants we already changed". This wave makes the drift visible;
the catch-up is the actual Phase 2 rhizome behavior the project
designs for. The craft lands, then I manually update ASCC canon
in the same session as part of landing, so Phase 2 work is never
blocked past this wave. ASCC gets a one-time migration debt; the
kernel gets a permanent defense.

**A6 (Attack — project-dir strict mode breaks `cd /tmp &&
myco hunger`).** Some users might actually run `myco hunger` from
outside a project to sanity-check their install. Strict mode kills
that use case.

**A7 (Defense — `--no-check` escape hatch).** Add
`--no-check` / allow an env var `MYCO_ALLOW_NO_PROJECT=1` to skip
the check. Default = strict, explicit opt-out for users who
genuinely want the no-project behavior. This is the inverse of
the current default: opt-in silent-pass instead of opt-in loud-fail.

## Round 2 — implementation details

**B1 (grandfather ceiling logic).** New helper
`_parse_version_tuple(s)` that accepts `v0.8.0` / `v0.8` / `0.8.0`
and returns `(major, minor, patch)` tuple, or `None` on parse
failure. In `detect_contract_drift`:

```python
# After reading `synced` and `kernel_version` but BEFORE
# the boot_reflex.enabled gate:
ceiling = int(boot_cfg.get("grandfather_ceiling_minor_versions", 5))

if synced is not None and kernel_version is not None:
    synced_tup = _parse_version_tuple(synced)
    kernel_tup = _parse_version_tuple(kernel_version)
    if synced_tup is None or kernel_tup is None:
        return (f"{prefix} version_parse_error: "
                f"could not parse synced={synced!r} or "
                f"kernel={kernel_version!r} as semver. "
                f"Fix the field(s) in _canon.yaml.")
    if synced_tup[0] != kernel_tup[0]:
        return (f"{prefix} grandfather_expired: major version "
                f"mismatch {synced!r} → {kernel!r} — majors are "
                f"NEVER grandfathered. Import contract NOW.")
    minor_gap = kernel_tup[1] - synced_tup[1]
    if minor_gap > ceiling:
        return (f"{prefix} grandfather_expired: "
                f"{minor_gap} minor versions of drift "
                f"({synced!r} → {kernel_version!r}) exceeds ceiling "
                f"{ceiling}. Grandfather exemption lapsed. "
                f"Read docs/contract_changelog.md entries between "
                f"{synced} and {kernel_version} and update "
                f"_canon.yaml::system.synced_contract_version "
                f"(plus any missing canon blocks) before any "
                f"kernel-class action.")

# Only THEN proceed to the enabled gate — but note that at this
# point, if we got here, the gap is within ceiling AND boot_reflex
# is disabled, which is a legitimate grandfather case.
if not boot_cfg or not boot_cfg.get("enabled", False):
    return None
```

Key semantic change: the enabled-gate moves from "first thing"
to "last thing". A disabled `boot_reflex` means "don't fire the
normal drift signal", but it can no longer mean "don't even
*check* version parity". The ceiling runs unconditionally.

**B2 (canon block extension).** Add to existing
`system.boot_reflex` in both kernel and template canon:

```yaml
boot_reflex:
  enabled: true
  severity: HIGH
  raw_backlog_threshold: 10
  reflex_prefix: "[REFLEX HIGH]"
  # Wave 20 (v0.19.0): grandfather exemption lapses after this
  # many minor versions of drift. Set to a large number to
  # disable the ceiling; set to 0 for strict lockstep mode.
  grandfather_ceiling_minor_versions: 5
```

**B3 (_project_root strict mode).** New exception in notes.py:

```python
class MycoProjectNotFound(Exception):
    pass
```

`_project_root` in notes_cmd.py becomes:

```python
def _project_root(args) -> Path:
    raw = getattr(args, "project_dir", None) or "."
    root = Path(raw).resolve()
    for candidate in [root] + list(root.parents):
        if (candidate / "_canon.yaml").exists():
            return candidate
    # Wave 20: strict mode — no canon found in walk-up.
    import os
    if os.environ.get("MYCO_ALLOW_NO_PROJECT") == "1":
        return root
    raise MycoProjectNotFound(
        f"not a Myco project: no _canon.yaml found at or above "
        f"{root}. Did you forget to cd or pass --project-dir? "
        f"Set MYCO_ALLOW_NO_PROJECT=1 to override (not recommended)."
    )
```

Every CLI verb that calls `_project_root` catches
`MycoProjectNotFound` and prints the message to stderr + exits 2.
Wrap the catch in a tiny helper so the same code runs in
`run_eat`, `run_digest`, `run_view`, `run_hunger`,
`run_correct`. Use the existing top-of-function try/except
pattern — minimal footprint.

**B4 (MCP server impact).** `myco.mcp_server` tools also call
`_project_root`. They should return a structured error
(`{"error": "project_not_found", ...}`) rather than crashing the
MCP tool call. Wrap at MCP wrapper level — not in
`_project_root` itself — keep the core semantic strict.

**B5 (ASCC migration, same-session).** After the kernel wave
commits, immediately update `/sessions/.../mnt/OPASCC/_canon.yaml`:
- Bump `synced_contract_version` from `v0.8.0` to `v0.19.0` (the
  new kernel version this wave ships).
- Insert a minimal `boot_reflex` block matching the kernel template.
- Append to ASCC log.md a decision entry documenting the import.
- Run `myco hunger --project-dir .../OPASCC` → expect
  `healthy`-range (no drift because synced == kernel now).

This is "the migration debt costs exactly what it should cost"
in action — a one-time catch-up, not a recurring tax.

## Round 3 — edge cases and doctrine

**C1 (What if the kernel itself doesn't have synced_contract_version?).**
Kernel self-reference: both `synced` and `kernel_version` come
from the same file, both bumped together. Already handled by
existing code. Ceiling logic is additive — it kicks in *after*
both are read, not before, so the kernel case continues to work.

**C2 (pre-Wave-20 instances with stale canon that lack
grandfather_ceiling_minor_versions).** The `get("...", 5)` default
means instances without the field get the default 5. No migration
required for downstream instances that already have a boot_reflex
block but no ceiling field.

**C3 (What if version parsing fails on both sides simultaneously —
e.g. hand-edited canon with "v0.x.0" placeholders?).**
`_parse_version_tuple` returns None → version_parse_error signal.
The instance's agent sees a clear message asking to fix the
malformed field. Not silent.

**C4 (Does strict project-dir break boot_brief writers?).**
`write_boot_brief` and `render_entry_point_signals_block` take
`root` directly — they are called *from inside* `run_hunger`
after `_project_root` has already succeeded. If `_project_root`
raises, they never execute. Clean.

**C5 (Does strict mode break `myco init` in a fresh empty dir?).**
`myco init` runs in a dir that explicitly does NOT yet have
`_canon.yaml` — the whole point is to create one. `run_init` does
not call `_project_root` (it takes its target dir directly from
args) so it's unaffected. Verified by grep: `init_cmd.py` has no
`_project_root` import.

**C6 (What about a hypothetical future agent that runs
`myco hunger` as a health check on an unrelated directory tree to
monitor multiple projects from one cron?).** That use case is
fringe, but the `MYCO_ALLOW_NO_PROJECT=1` env var covers it with
explicit intent. Default behavior is loud.

**C7 (Does the grandfather ceiling interact with the
contract_drift signal's existing "silent LOW" branch when synced
or kernel is unreadable?).** No — the unreadable branch runs only
when *both* fields are None (or the file can't be read), which is
mutually exclusive with "gap exceeds ceiling" (gap requires both
values readable and parseable). The two branches live side by
side without overlap.

**C8 (Severity asymmetry).** `grandfather_expired` is HIGH because
it represents operating under an invalidated contract — a W1
(autopilot) violation just like the normal drift signal. Not LOW;
the whole point of this wave is to remove the silent path. Major
mismatch is also HIGH (same severity; different reason). Parse
error is MEDIUM because malformed canon is an agent bug, not a
contract violation — worth surfacing but not a reflex arc.

## Decisions

1. **D1 — Grandfather ceiling** added to `detect_contract_drift`.
   Runs *before* the enabled-gate. Default 5, canon-configurable
   via `system.boot_reflex.grandfather_ceiling_minor_versions`.
   Major mismatch is unconditional HIGH. (NH-2 closed.)
2. **D2 — Version parse helper** `_parse_version_tuple` accepts
   `vMAJOR.MINOR[.PATCH]` semver-ish formats. Parse failure →
   `version_parse_error` MEDIUM, not silent.
3. **D3 — `_project_root` strict mode**. Raises
   `MycoProjectNotFound` on walk-up failure. CLI catches and exits 2
   with a clear error. `MYCO_ALLOW_NO_PROJECT=1` env var is the
   explicit escape hatch. (NH-1 closed.)
4. **D4 — Contract bump** `v0.18.0 → v0.19.0`, minor. Changelog
   entry in `docs/contract_changelog.md`.
5. **D5 — ASCC migration happens in the same landing session**.
   Bump ASCC `synced_contract_version` to `v0.19.0` and add a
   minimal `boot_reflex` block. Document the import in ASCC's
   log.md.
6. **D6 — MCP wrapper catches `MycoProjectNotFound`** and returns
   a structured error, not crash. Out of scope for this wave if
   mcp_server.py refactor is required — document as follow-up.
7. **D7 — Self-test plan**: kernel drift self-test (tamper
   synced to v0.10.0, verify fire), project-dir strict test
   (cd /tmp, verify exit 2), env-var override test
   (MYCO_ALLOW_NO_PROJECT=1, verify pass), ASCC migration
   (bump + hunger → healthy).
8. **D8 — Hole closure**: NH-1 full, NH-2 full. The ASCC side
   also gets a one-time migration as evidence the mechanism works.

## 5. Landing checklist

- [x] Write craft (3 rounds, kernel_contract class, confidence ≥0.90)
- [ ] Add `MycoProjectNotFound` exception + `_parse_version_tuple`
      helper + grandfather ceiling logic in `src/myco/notes.py`
- [ ] Update `_project_root` in `src/myco/notes_cmd.py` to raise
      on no-canon with env-var escape hatch
- [ ] Wrap CLI verb entry points to catch `MycoProjectNotFound`
      and exit 2 with stderr message
- [ ] Add `grandfather_ceiling_minor_versions` to
      `_canon.yaml` and `src/myco/templates/_canon.yaml`
- [ ] Bump `contract_version` v0.18.0 → v0.19.0 in both canons
- [ ] Self-test: drift fire (tamper synced → revert), strict mode
      exit 2, env-var override, ASCC migration
- [ ] Add `v0.19.0` entry to `docs/contract_changelog.md`
- [ ] Update ASCC `_canon.yaml` (synced + boot_reflex block)
- [ ] Append to ASCC log.md: import decision entry
- [ ] `myco eat`/`correct` Wave 20 conclusion, digest to integrated
- [ ] Append kernel log.md milestone
- [ ] Commit + push via desktop-commander

## 6. Known limitations

- **L-1** Version parser is semver-like, not strict semver
  (accepts `v0.8` without patch). Acceptable because Myco's own
  version scheme is MAJOR.MINOR.PATCH with PATCH often omitted.
- **L-2** `grandfather_ceiling_minor_versions` is a fixed integer;
  no adaptive threshold based on substrate age or wave velocity.
  Future work if ceiling tuning becomes a real problem.
- **L-3** MCP server wrapper refactor for `MycoProjectNotFound`
  deferred to a follow-up; direct `myco` CLI is the audited
  surface this wave.
- **L-4** The ASCC migration only catches _this_ instance; any
  other downstream projects that might exist (there are none
  tracked right now, but there could be) will also fire on their
  next hunger until they're manually imported. That's the feature.
