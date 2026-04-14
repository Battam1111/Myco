# SessionStart Hook — Myco Boot Ritual

**Contract**: every new Claude Code / Cowork session in this substrate
begins with `myco hunger`. The hook removes agent discretion — hunger
fires every session, without exception.

## What fires

The command in `.claude/settings.local.json::hooks.SessionStart[0]` runs
**before the agent responds to the first user message**:

```
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" hunger
```

The JSON payload — boot brief, active reflexes, metabolic signals — is
fed into the agent's context. The agent then processes the user's first
message with substrate state already in hand.

## Why it exists

Without this hook, the boot ritual depends on the agent *remembering*
to call `hunger` after reading `MYCO.md`. Agents forget. The hook
removes the discretion.

## What the agent does with the output

`hunger` returns a structured payload covering:

- `boot_brief` — the brief written to `.myco_state/boot_brief.md`.
- `reflexes` — HIGH signals that gate all other work until addressed.
- `backlog` — raw-note counts and stale-reflection flags.

The agent should:

1. Scan `reflexes` first. Any HIGH reflex is addressed before the user
   request.
2. Surface the key remaining signals to the user in plain language —
   never a JSON dump.
3. Proceed with the user's task, calling `sense` before any factual
   claim about the substrate.
