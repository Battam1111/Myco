# Agent Routing — Model Selection by Task Type

> Absorbed from claude-code-best-practice + gstack sub-agent routing patterns.

## When to Execute

When spawning subagents or choosing model effort level for a subtask.

## Routing Table

| Task Type | Model Class | Tools | Isolation | Why |
|-----------|------------|-------|-----------|-----|
| Codebase search | haiku (fast) | Read-only | none | Speed over depth |
| File content scan | haiku | Glob, Grep, Read | none | Pattern matching |
| Research synthesis | sonnet | All read + WebSearch | none | Balanced depth |
| Architecture decision | opus | All | none | Deep reasoning |
| Experimental code | sonnet | All | worktree | Isolation for safety |
| Compression synthesis | opus | All write | none | Quality-critical |
| Inlet evaluation | opus | WebSearch + Read | none | Judgment-critical |
| Routine digest | sonnet | Write | none | Summarization |
| Prune decision | sonnet | Read + Write | none | Pattern matching |

## Steps

1. Identify the task type (search / synthesis / decision / routine)
2. Look up the routing table above
3. Select the matching model class + tool set + isolation level
4. If spawning a subagent, set `maxTurns` limit (default 10)
5. Execute with the selected configuration

## Principles

1. **Match model to task scope** — don't use opus for grep
2. **Read-only first** — search agents should not write
3. **Isolate experiments** — use worktree for risky changes
4. **Budget maxTurns** — prevent runaway subagents (default: 10)
5. **PROACTIVELY describe** — subagent descriptions should trigger auto-invocation
