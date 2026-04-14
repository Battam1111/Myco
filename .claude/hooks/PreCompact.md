# PreCompact Hook — Myco Session-End Ritual

**Contract**: every context compaction in this substrate is preceded
by `myco session-end`. No raw note survives a compaction without
reflection; no immune-fixable drift survives a compaction without the
fix.

## What fires

The command in `.claude/settings.local.json::hooks.PreCompact[0]` runs
**before Claude Code compacts the conversation**:

```
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" session-end
```

`session-end` is the meta-verb that composes `reflect` (promote raw
notes to integrated) with `immune --fix` (auto-correct drift
findings). Both run in one call; the payload includes both results.

## Why it exists

Compaction evicts in-context working state. Anything the agent learned
this session must be **externalized** before the evict, or it is lost.
Session-end is that externalization ritual.

## Exit code handling

`session-end` returns the worse of the `reflect` and `immune` exit
codes. A non-zero exit does not block compaction; it surfaces as a
signal the agent notices at the next session boot (hunger surfaces
the resulting state).
