---
name: hunger
description: Check Myco substrate health at session boot. Returns the boot brief, active reflexes, and raw-notes backlog. Usually fired automatically by the SessionStart hook; invoke manually when that hook did not run or when substrate state may have drifted.
allowed-tools: Bash
---

# /myco:hunger

Myco's boot ritual, per L1 rule R1. Every session begins here.

## When to invoke

- The SessionStart hook did not run (e.g. the plugin is not installed
  in this project, or hooks are disabled).
- The current substrate state may have drifted (a long idle, an
  external edit, a branch switch).
- Before asserting any substrate fact — R3 says sense first, but if
  the session has not yet been booted, hunger comes before sense.

## Command

```bash
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" hunger
```

If `$CLAUDE_PROJECT_DIR` is not set (you are invoking outside Claude
Code), substitute the substrate root path, e.g. `"$PWD"`.

## Output shape

JSON with at least:

- `boot_brief` — path to the newly written brief under `.myco_state/`.
- `reflexes` — HIGH-severity signals that gate all other work until
  addressed. Read these first.
- `backlog` — raw-notes count, stale-reflection flags, MB1 / MB2
  indicators.

## How the agent should act on the output

1. Read `reflexes` first. Any HIGH item is addressed before the user's
   request.
2. Translate remaining signals into plain language for the user — do
   not dump the JSON verbatim.
3. Once the agent is satisfied nothing HIGH is outstanding, proceed
   with the user's task. Call `/myco:sense` (or `myco sense`) before
   any factual claim about the substrate.

## Related verbs

- `/myco:session-end`: the matched ritual at session close (the
  skill is kept under its legacy directory name; the canonical verb
  is `myco senesce`, with `--quick` for SessionEnd hooks).
- Full verb set (19 verbs at v0.5.24: 18 agent + 1 human-facing
  `brief`) is exposed as MCP tools when the plugin's MCP server is
  running.
