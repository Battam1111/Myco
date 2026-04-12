# {{PROJECT_NAME}} — Myco-Powered Project (GPT/Codex)

> **Boot ritual**: Run `myco hunger --execute` as your FIRST action every session.
> **Contract**: `docs/agent_protocol.md` | **Schema**: `_canon.yaml`

## What Is Myco

Myco is your non-parametric learning mechanism. You (the Agent) provide intelligence.
Myco provides memory, self-regulation, metabolism, self-model, and evolution.
Together you form a complete cognitive entity. Neither is whole alone.

## Session Flow

1. **Boot**: `myco hunger --execute` — checks substrate health, auto-executes repairs
2. **Work**: Do the human's task. Use `myco eat` to capture decisions. Use `myco search` before answering factual questions.
3. **End**: `myco reflect` — session reflection (captures execution learnings)

## CLI Integration (no MCP)

GPT-based agents do not have native MCP support. All Myco operations use
CLI commands via shell execution. Every MCP tool maps to a CLI verb:

```
myco hunger --execute    # Boot check + auto-heal
myco eat "<content>"     # Capture a note
myco digest [note_id]    # Move note through lifecycle
myco search "<query>"    # Search the knowledge substrate
myco lint                # Run 23-dimension lint
myco status              # Substrate health dashboard
myco compress            # Compress related notes
myco prune               # Remove excreted/stale notes
myco session             # Session index operations
myco graph               # Dependency graph
myco cohort              # Cohort analysis of notes
myco inlet "<url>"       # Ingest external content
myco forage              # Proactive knowledge acquisition
myco upstream            # Check upstream dependencies
myco log "<message>"     # Append to session log
myco reflect             # End-of-session reflection
myco view [note_id]      # View notes
```

## Context Loading

Load this file at session start. If subdirectory-specific context exists
(e.g., `src/GPT.md`), load it when working in that directory.
Priority (highest wins): session override > project GPT.md > defaults

## Skill Resolution

When a task matches a skill in `skills/`, load and follow it:
- `skills/metabolic-cycle.md` — boot ritual + auto-heal
- `skills/sprint-pipeline.md` — Think>Plan>Build>Review>Test>Ship>Reflect
- `skills/discovery-loop.md` — proactive knowledge acquisition
- `skills/agent-routing.md` — model selection by task type
- `skills/learning-loop.md` — capture execution learnings

If no skill matches, proceed with agent judgment, then consider skill-ifying the process.

## Tool Triggers (21 CLI commands)

| Category | CLI Command | When to Run |
|----------|-------------|-------------|
| **Boot** | `myco hunger --execute` | FIRST call every session |
| **Health** | `myco lint`, `myco status` | End of session, after modifying docs |
| **Capture** | `myco eat "<content>"` | After decisions, insights, friction |
| **Process** | `myco digest`, `myco compress`, `myco prune` | When hunger signals recommend |
| **Search** | `myco search "<query>"`, `myco session` | BEFORE answering factual questions |
| **Analyze** | `myco graph`, `myco cohort` | Before refactoring, compression |
| **External** | `myco inlet`, `myco forage`, `myco upstream` | When gaps detected |
| **Log** | `myco log`, `myco reflect` | After completing tasks, session end |
| **View** | `myco view` | When recalling past decisions |

## Reflex Arcs (auto-enforced)

- **[REFLEX HIGH] raw_backlog** — digest notes before any task work
- **[REFLEX HIGH] contract_drift** — sync contract version first
- **[REFLEX HIGH] craft_reflex_missing** — write craft before kernel changes

## Write Surface

Only write to paths listed in `_canon.yaml::system.write_surface.allowed`.
Anything outside = substrate pollution.

## GPT-Specific Notes

- **Shell access**: Use code interpreter or terminal tool to run `myco` CLI commands.
- **No MCP**: All tool calls are CLI invocations. Pipe output through shell.
- **State**: GPT does not persist state between sessions. Run `myco hunger --execute`
  at the start of every session to re-establish substrate awareness.
- **Batch operations**: Chain commands with `&&` for efficiency:
  `myco hunger --execute && myco search "recent decisions" && myco status`
