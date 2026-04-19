# PreCompact Hook — Myco Session-End Ritual (Full Mode)

**Contract**: every context compaction in this substrate is preceded
by `myco senesce` in **full mode** (assimilate + immune --fix). No
raw note survives a compaction without assimilation; no immune-fixable
drift survives a compaction without the fix. The companion **SessionEnd**
hook runs `myco senesce --quick` (assimilate only) for non-compact
session exits — see [`SessionEnd.md`](SessionEnd.md).

## What fires

The command in `.claude/settings.local.json::hooks.PreCompact[0]` runs
**before Claude Code compacts the conversation** and **blocks until
done** (no timeout kill):

```
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce
```

`senesce` is the meta-verb that composes `assimilate` (promote raw
notes to integrated, was `reflect` pre-v0.5.3) with `immune --fix`
(auto-correct drift findings). Both run in one call; the payload
includes both results plus `mode: "full"`. PreCompact blocks until the
hook completes, so the full pipeline (assimilate ~ms, immune ~seconds)
always runs to completion.

## Why it exists

Compaction evicts in-context working state. Anything the agent learned
this session must be **externalized** before the evict, or it is lost.
Senesce (full) is that externalization ritual when the user invokes
`/compact`. For abrupt exits without `/compact` (user types `/exit`,
hits Ctrl+D, closes the window), the SessionEnd hook runs
`senesce --quick` (assimilate-only) inside Claude Code's ~1.5 s
SessionEnd kill budget; the `immune --fix` pass then runs at the next
PreCompact or SessionStart-hunger signal.

## Exit code handling

`senesce` returns the worse (higher) of the `assimilate` and `immune`
exit codes in full mode; just the assimilate exit in quick mode. A
non-zero exit does not block compaction; it surfaces as a signal the
agent notices at the next session boot (hunger surfaces the resulting
state).

## Alias note

The verb `senesce` was renamed from `session-end` at v0.5.3 (fungal
vocabulary migration). The v0.5.2 alias `session-end` still resolves
through v1.0.0 — hook configs in older substrates continue to work
without edits. New writes use `senesce`.
