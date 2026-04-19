# SessionEnd Hook — Myco Session-End Ritual (Quick Mode)

**Contract**: every non-compact session exit in this substrate runs
`myco senesce --quick` — assimilate only, no immune pass. The companion
**PreCompact** hook runs the full-mode senesce (assimilate + immune
--fix) for `/compact` — see [`PreCompact.md`](PreCompact.md). Together
the two hooks guarantee **every** session boundary fires at least the
assimilate half of R2, regardless of how the session ended.

## What fires

The command in `.claude/settings.local.json::hooks.SessionEnd[0]` runs
**when the Claude Code session terminates without compaction** —
`/exit`, Ctrl+D, window close, or other abrupt terminations:

```
python -m myco --json --project-dir "$CLAUDE_PROJECT_DIR" senesce --quick
```

Claude Code gives SessionEnd hooks a ~1.5 s kill budget (configurable
via `CLAUDE_CODE_SESSIONEND_HOOKS_TIMEOUT_MS`). Full-mode senesce —
which includes the 11-dimension immune scan — can exceed that budget.
**Quick** mode runs `assimilate` alone, measured at ~0.4 s on the Myco
self-substrate (3.8× safety margin under the 1.5 s kill).

## Why it exists

R2 (session-end ritual) is a contract invariant: every session ends
with at least the assimilate step so raw notes do not accumulate
across boundaries. The PreCompact hook satisfies R2 for the `/compact`
flow (which is the dominant one in long Claude Code sessions), but
sessions that end via `/exit` or window-close **never fire PreCompact**.
Without SessionEnd coverage, those exits silently skip the entire
ritual — reflex signals build up, the next session starts degraded.

Quick mode is the **defense-in-depth fallback**: it is not the
canonical form of R2 (full is), it is the form that fits inside the
host's short-exit kill budget. The canonical form runs at the canonical
moment (`/compact`); the quick form runs at the moment the canonical
form cannot.

## Payload shape

```json
{
  "exit_code": 0,
  "payload": {
    "reflect": {"promoted": N, "errors": [...], "outcomes": [...]},
    "immune": {
      "skipped": true,
      "reason": "--quick mode: reflect-only for SessionEnd hook timeout budget (~1.5s default). The next PreCompact/SessionStart will pick up any findings immune would have surfaced."
    },
    "mode": "quick"
  }
}
```

The `immune.skipped: true` marker is the contract that downstream
tooling (`brief`, hunger-sidecar, MCP clients) keys on when it wants
to know "was this session wrapped up the cheap way?". The full-mode
payload carries the real `run_immune` dict at `immune` and
`mode: "full"`.

## Exit code handling

Quick mode's exit code is derived from `assimilate` alone (the immune
step is skipped). If `assimilate` errored on every raw note it tried
(pathological case), the exit is 1; otherwise 0. SessionEnd does not
block the session exit on non-zero; the signal surfaces at the next
SessionStart-hunger call via the reflex-signal machinery.

## Known Claude Code bugs (upstream)

As of v1.0.85+, the SessionEnd hook has documented coverage gaps
(see GitHub issues `anthropics/claude-code#4318`, `#6306`, `#6428`,
`#17885`, `#41577`). Specifically:

- Does not fire on `/clear` (Issue #6428).
- Sometimes does not fire on `/exit` (Issue #17885).
- Fires on Ctrl+D and normal window-close.

These are Anthropic-side bugs, not Myco-side. The hook binding is
still the right thing to ship: on the paths that work, it closes R2
coverage. The paths that do not fire leave R2's coverage at the same
(PreCompact-only) level as v0.5.6 — no regression.
