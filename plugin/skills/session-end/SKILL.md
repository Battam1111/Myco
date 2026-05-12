---
name: session-end
description: Run the session-end ritual — `myco senesce` composes `assimilate` (promote raw notes to integrated) with `immune --fix` (auto-correct drift). Two modes at v0.5.7+ — full (reflect + immune, PreCompact hook) and quick (reflect only, SessionEnd hook, ~1.5 s kill budget). Skill directory name kept as `session-end` for v0.5.x backward compatibility; the canonical verb is `senesce`.
allowed-tools: Bash
---

# /myco:session-end

Myco's close-of-session ritual, per L1 rule R2. Every session ends
here so nothing the agent learned is lost to compaction or eviction.

**Directory name note**: this skill lives under `skills/session-end/`
because the v0.5.2 → v0.5.3 rename kept `session-end` as a
backward-compatible CLI alias (and the skill directory name is what
shows up as the slash-command). The canonical verb is `myco senesce`;
invoking `/myco:session-end` calls `senesce` under the hood via the
alias resolver.

## When to invoke

- Closing a working session without a compact — wrap up explicitly.
- Before a long-running operation that will evict context.
- Any time `assimilate` + `immune --fix` should run as a single
  atomic act.

## Commands

```bash
# Full mode — assimilate + immune --fix. Bound to PreCompact.
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce

# Quick mode (v0.5.7+) — assimilate only. Bound to SessionEnd.
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce --quick
```

The v0.5.2 alias `session-end` still resolves — both
`python -m myco session-end` and `python -m myco senesce` invoke the
same handler.

## What it does

`senesce` is a meta-verb. In **full** mode it composes two calls:

1. `assimilate` (was `reflect` in v0.5.2) — promote raw notes to
   `integrated/` where they belong.
2. `immune --fix` — auto-correct the lint dimensions that support
   safe automatic repair.

Both run in full mode; the payload aggregates both results and
carries `mode: "full"`. The exit code is the worse of the two —
non-zero does not abort compaction but surfaces as a signal at the
next session's `hunger` call.

In **quick** mode (`--quick`) only step 1 runs; step 2 is reported
as `immune: {skipped: true, reason: <str>}` in the payload and
`mode: "quick"`. The SessionEnd hook uses quick mode because Claude
Code kills the hook at ~1.5 s; full mode's immune scan can exceed
that budget. The next SessionStart `hunger` or PreCompact `senesce`
picks up any findings quick mode would have surfaced.

## How the agent should act on the output

1. Scan `payload["mode"]`. If `"quick"`, note that `immune` did not
   run; mention it to the user so they know a deferred lint pass is
   pending at the next boot.
2. Scan both sub-results (`payload["reflect"]` always present;
   `payload["immune"]` is either the full lint payload or the
   `skipped: true` marker).
3. If `reflect` promoted notes, the agent should summarize what went
   into integrated tier in one sentence.
4. Anything that did NOT auto-fix (full mode) or was deferred
   (quick mode) is a flag for the next session — mention it to the
   user so they know state was externalized but not fully cleaned.
5. Do not retry on failure — the next `hunger` will see the residual
   state and surface it again.

## Related verbs

- `/myco:hunger` — the matched ritual at session start.
- `assimilate`, `immune` — the underlying verbs, also available
  individually as MCP tools or CLI commands.
