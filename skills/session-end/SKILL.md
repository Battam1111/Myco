---
name: session-end
description: Run the session-end ritual — reflect (promote raw notes to integrated) followed by immune --fix (auto-correct drift). Usually fired automatically by the PreCompact hook; invoke manually when compaction will not happen but you still want to externalize session state before it is lost.
allowed-tools: Bash
---

# /myco:session-end

Myco's close-of-session ritual, per L1 rule R2. Every session ends
here so nothing the agent learned is lost to compaction or eviction.

## When to invoke

- Closing a working session without a compact — wrap up explicitly.
- Before a long-running operation that will evict context.
- Any time reflect + immune --fix should run as a single atomic act.

## Command

```bash
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" session-end
```

## What it does

`session-end` is a meta-verb composing two calls:

1. `reflect` — promote raw notes to `integrated/` where they belong.
2. `immune --fix` — auto-correct the lint dimensions that support
   safe automatic repair.

Both run; the payload aggregates both results. The exit code is the
worse of the two — non-zero does not abort compaction but surfaces as
a signal at the next session's `hunger` call.

## How the agent should act on the output

1. Scan both sub-results. Anything that did NOT auto-fix is a flag for
   the next session — mention it to the user so they know state was
   externalized but not cleaned.
2. If `reflect` promoted notes, the agent should summarize what went
   into integrated tier in one sentence.
3. Do not retry on failure — the next `hunger` will see the residual
   state and surface it again.

## Related verbs

- `/myco:hunger` — the matched ritual at session start.
- `reflect`, `immune` — the underlying verbs, also available
  individually as MCP tools or CLI commands.
