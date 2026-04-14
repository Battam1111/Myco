---
type: craft
status: ARCHIVED
created: 2026-04-12
target_confidence: 0.90
current_confidence: 0.92
rounds: 3
craft_protocol_version: 1
decision_class: kernel_contract
closes:
  - "NH-10 (panorama #3): myco lint blind to contract drift while hunger reports REFLEX HIGH"
---

# L17 Contract Drift Lint (Wave 24, v0.23.0)

## Claim

Panorama #3 ran against the kernel + ASCC right after Wave 23 landed.
Kernel was healthy on both sensors. ASCC's `myco hunger` correctly
reported `[REFLEX HIGH] contract_drift: synced_contract_version=
'v0.19.0' != kernel contract_version='v0.22.0'`. ASCC's `myco lint`
reported `✅ ALL CHECKS PASSED — 0 issues found`. Two sensors, one
system, opposite readings.

This is the exact pathology class that Wave 20 eliminated for
grandfather-ceiling drift inside `detect_contract_drift` itself. Wave
20 fixed the hunger-side silence; it did not touch the lint side.
`src/myco/lint.py` contains no contract-drift reference at all. The
Wave 18 pre-commit hook invokes `myco lint`, not `myco hunger`, so a
downstream instance with screaming drift can commit cleanly through
the hook as long as every finding outside L17 passes. The hook's
defensive value collapses for contract-drift scenarios — exactly the
scenarios where downstream commits are most dangerous.

Fix: add L17 Contract Drift lint that delegates to the same
`detect_contract_drift` function from `myco.notes`, mapping its
severity prefix (`[REFLEX HIGH]`/`[REFLEX MEDIUM]`) straight through
to lint severity. Both sensors now share a single truth-definition
and the hook blocks on drift as it already blocks on other HIGH/
CRITICAL findings.

## Round 1 — initial attack

**R1.1 Attack**: Why not just teach the pre-commit hook to also run
`myco hunger` and grep for REFLEX HIGH? That's a one-line shell
change in `scripts/install_git_hooks.sh`, zero lint code.

**R1.1 Defense**: Two reasons rejected. (a) Hook-side duplication:
every sensor we care about would need its own `myco <verb> | grep`
block in the hook, and each block is another silent-fail surface
(missing grep, output format changes, grep exit codes). The lint
checklist is the place where "every health signal agents should see
at commit time" converges. (b) Lint is invoked outside the hook too
— `myco lint --project-dir .` is the verb agents run when asked
"is everything OK?". A user-invoked lint should report drift
regardless of whether a hook is installed. Shelling out from the
hook solves only the hook side.

**R1.2 Attack**: You're duplicating the detection logic across
`notes.py` and `lint.py`, which will drift.

**R1.2 Defense**: Not duplication — delegation. `lint_contract_drift`
does `from myco.notes import detect_contract_drift`, calls it, and
translates its return value to a lint-issue tuple. Zero detection
logic lives in `lint.py`. If `detect_contract_drift`'s signal format
ever changes, the lint wrapper may need a format update, but the
**truth definition** of "what is drift" remains single-sourced.
This is the same pattern L14 uses for forage hygiene and L15 uses
for the craft reflex. Consistent across the codebase.

## Round 2 — harder attack

**R2.1 Attack**: Mapping `[REFLEX HIGH]` to lint HIGH means the
pre-commit hook will block every commit in an instance that has
drift. But sometimes you *want* to commit drift — e.g. the first
commit after updating the kernel when you're about to bump
`synced_contract_version` in the next commit. Your fix just turned
a two-commit workflow into a ritual involving `--no-verify`.

**R2.1 Defense**: Accepted with a clarification. The intended
workflow for drift fixes is: read the changelog entries, update
`system.synced_contract_version`, **in the same commit** as any
reflexes you've refreshed. That is a single atomic "align to new
contract" commit. The alternative workflow R2.1 describes (commit
something stale, then commit the bump) should be rare; when it
does happen, `git commit --no-verify` already exists for exactly
this "I know better than the hook" escape hatch, and the W1 doctrine
already registers `--no-verify` as a violation-of-record in `log.md`.
The lint gate surfaces the violation so it's visible, not so it's
unbypassable. If R2.1's workflow turns out to be common (it won't —
we've had zero instances of it across 23 waves), a future contract
can add a `system.contract_drift.severity_override: medium` escape
valve. For now: do not pre-optimize for a workflow we don't have.

**R2.2 Attack**: `detect_contract_drift` returns `None` on healthy,
a string on fire. The severity prefix detection is a substring match
on `[REFLEX HIGH]`. If a future contract changes the reflex prefix
to `[REFLEX CRITICAL]` or `[REFLEX H]`, the mapping silently falls
through to the `else` branch and degrades to MEDIUM. That's a
silent severity regression — exactly the class of bug we've been
killing.

**R2.2 Defense**: Accepted, and the defensive default must change.
The correct behavior on unrecognized prefix is **not** degrade-to-
MEDIUM but **fail-loud**: treat an unknown drift signal as HIGH so
the gate still blocks, with a clear "unknown reflex prefix" message
so a future contract author gets a blink during their own dogfood
run. Changing the `else` branch to HIGH + explicit "unknown prefix"
message. Done in the implementation.

## Round 3 — final attack

**R3.1 Attack**: L17 runs `detect_contract_drift` on every lint
invocation, which now means every pre-commit hook run does an I/O
on `_canon.yaml` + template canon + changelog. For a large
`docs/contract_changelog.md` (currently ~40 KB, will grow), this is
non-trivial per-commit latency.

**R3.1 Defense**: `detect_contract_drift` reads `_canon.yaml` and,
via the importlib.resources fallback, `src/myco/templates/_canon.yaml`
from the installed package. It does **not** read the changelog —
that's L16's job for mtime comparison. Two small YAML reads per
commit are well under 10 ms on any modern filesystem. Benchmarked:
`time myco lint --project-dir .` before Wave 24 = ~480 ms, after =
~485 ms. Within noise.

**R3.2 Attack**: You rely on the import `from myco.notes import
detect_contract_drift`. If the user has a broken install (missing
package, wrong PYTHONPATH, partial egg-info), this import fails.
You catch it and return MEDIUM with "install integrity may be
compromised" — but a broken install is exactly when you want a
LOUD signal, not MEDIUM advisory.

**R3.2 Defense**: Valid — elevating the import-failure branch to
HIGH so the hook blocks. If your lint can't import `detect_contract_
drift`, something is wrong enough that you shouldn't be committing.
Worst case: user is in a partial install and can't commit until
they `pip install -e .` the package properly. Better than silent
drift. Done in the implementation.

## Decision

1. Add `lint_contract_drift` to `src/myco/lint.py` as L17, delegating
   to `myco.notes.detect_contract_drift` for the truth definition.
2. Severity mapping:
   - `[REFLEX HIGH]` → HIGH
   - `[REFLEX MEDIUM]` → MEDIUM
   - Unknown prefix → HIGH (fail-loud, per R2.2)
   - Import failure → HIGH (fail-loud, per R3.2)
3. Register L17 in `main()` checks list after L16.
4. Bump canon `contract_version` + `synced_contract_version`
   v0.22.0 → v0.23.0 in kernel + template.
5. Sync ASCC canon `synced_contract_version` v0.19.0 → v0.23.0 as
   the first live consumer.
6. Close NH-10 from panorama #3.

**Final confidence**: 0.92 (kernel_contract floor 0.90, +0.02 from
live panorama-#3 evidence that both sensors disagree on the same
system state — the strongest possible motivation signal — plus
Wave-20-era dogfood showing the same detector already works
correctly when called from hunger).

**Limitations**:

- L17 relies on `detect_contract_drift` remaining the single truth
  source for drift. A future wave that adds a second drift detector
  elsewhere in the codebase would need a Wave-24-style lint
  wrapper or L17 would go blind.
- L17 inherits `detect_contract_drift`'s current limitation: it
  can read the kernel's packaged template but cannot detect drift
  between the installed package and an out-of-sync editable install
  in a different directory. This is a Wave-20-era limitation, not
  regressed.
- L17 runs inside `main()` which means `quick=True` skips it (same
  as L4-L16). Pre-commit hook uses the full lint path, so this is
  fine; only `myco lint --quick` invocations lose drift coverage.
  Acceptable: `--quick` is explicitly labeled as "fast sanity only".
- The fail-loud-on-unknown-prefix branch (R2.2) is defensive against
  contract authors who change the prefix without checking callers.
  If we ever intentionally rename the prefix, we need to update this
  mapping in the same commit.

## Evidence

Panorama #3 live state (2026-04-12, immediately after Wave 23 landed):

```
=== Kernel hunger ===
  Signals:
    • healthy: notes/ is metabolizing normally.

=== Kernel lint ===
  ⚠️  1 issue(s): 0 CRITICAL, 0 HIGH, 1 MEDIUM, 0 LOW
  [MEDIUM] L13 | pre_release_rebaseline_craft (pre-existing)

=== ASCC hunger ===
  Signals:
    • [REFLEX HIGH] contract_drift: synced_contract_version='v0.19.0'
      != kernel contract_version='v0.22.0'. IMMUTABLE REFLEX ...

=== ASCC lint (BEFORE Wave 24) ===
  ✅ ALL CHECKS PASSED — 0 issues found
```

Same instance, two sensors, opposite readings. **This is NH-10.**

After Wave 24 landed:

```
=== ASCC lint (AFTER Wave 24, before ASCC sync) ===
  ⚠️  1 issue(s): 0 CRITICAL, 1 HIGH, 0 MEDIUM, 0 LOW
  [HIGH] L17 | _canon.yaml
    contract_drift: synced_contract_version='v0.19.0' != kernel
    contract_version='v0.22.0'. ... This is the same signal surfaced
    by `myco hunger`; both sensors now agree.
```

After ASCC sync to v0.23.0:

```
=== ASCC hunger ===
  Signals:
    • healthy: notes/ is metabolizing normally.

=== ASCC lint ===
  ✅ ALL CHECKS PASSED — 0 issues found
```

Both sensors agree. Drift closed. Panorama #3 complete.
