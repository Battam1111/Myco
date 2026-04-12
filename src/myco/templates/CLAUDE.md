# {{PROJECT_NAME}} — Myco-Powered Project

> 最后更新：{{DATE}}
> **Boot ritual**: Call `myco_hunger(execute=true)` as your FIRST action every session.
> **Schema**: `_canon.yaml`

## What Is Myco

Myco is your non-parametric learning mechanism. You (the Agent) provide intelligence.
Myco provides memory, self-regulation, metabolism, self-model, and evolution.
Together you form a complete cognitive entity. Neither is whole alone.

## Session Flow

1. **Boot**: `myco_hunger(execute=true)` — checks substrate health, auto-executes repairs
2. **Work**: Do the human's task. Follow these ALWAYS rules:
   - `myco_eat` IMMEDIATELY when: user gives feedback, you make a decision, you learn something, you hit friction
   - `myco_search` BEFORE answering any factual question about the project
   - `myco_eat` user's natural language feedback THE MOMENT they say it — don't wait, don't treat it as casual conversation
3. **End**: `myco_reflect()` — session-end reflection (auto-captures execution learnings)

## Context Loading (hierarchical)

This project may have subdirectory CLAUDE.md files. Load only when working in that directory.
Priority (highest wins): session override > project CLAUDE.md > user ~/.claude > organization

## Skill Resolution

If a `skills/` directory exists, check for matching skills before starting a task.
If no skill matches (or no skills/ directory), proceed with agent judgment.

## Tool Triggers (21 MCP tools)

| Category | Tools | When to Call |
|----------|-------|-------------|
| **Boot** | `myco_hunger(execute=true)` | FIRST call every session |
| **Health** | `myco_lint`, `myco_status` | End of session, after modifying docs |
| **Capture** | `myco_eat` | After decisions, insights, friction |
| **Process** | `myco_digest`, `myco_compress`, `myco_prune` | When hunger signals recommend |
| **Search** | `myco_search`, `myco_session` | BEFORE answering factual questions |
| **Analyze** | `myco_graph`, `myco_cohort` | Before refactoring, compression |
| **External** | `myco_inlet`, `myco_forage`, `myco_upstream` | When gaps detected |
| **Log** | `myco_log`, `myco_reflect` | After completing tasks, session end |
| **View** | `myco_view` | When recalling past decisions |

## Reflex Arcs (auto-enforced)

- **[REFLEX HIGH] raw_backlog** — digest notes before any task work
- **[REFLEX HIGH] contract_drift** — sync contract version first
- **[REFLEX HIGH] craft_reflex_missing** — write craft before kernel changes

## Write Surface

Only write to paths listed in `_canon.yaml::system.write_surface.allowed`.
Anything outside = substrate pollution.
