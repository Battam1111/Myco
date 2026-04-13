# {{PROJECT_NAME}} — Myco-Powered Project

> 最后更新：{{DATE}}
> **Boot ritual**: Call `myco_hunger(execute=true)` as your FIRST action every session.
> **Schema**: `_canon.yaml`

## What Is Myco

Myco is your non-parametric learning mechanism. You (the Agent) provide intelligence.
Myco provides memory, self-regulation, metabolism, self-model, and evolution.
Together you form a complete cognitive entity. Neither is whole alone.

## First-Boot Setup (run ONCE per project, skip if already done)

Check if the Myco metabolic cycle scheduled task exists by calling `list_scheduled_tasks`.
If no task named `myco-metabolic-cycle` is found, register it:

1. Read `.claude/scheduled-tasks/myco-metabolic-cycle/SKILL.md` for the full prompt content
2. Call `create_scheduled_task(taskId="myco-metabolic-cycle", description="Daily Myco metabolic cycle — hunger + auto-heal + immune + verify", cronExpression="0 9 * * *", prompt=<SKILL.md content>)`

If `.claude/scheduled-tasks/myco-metabolic-cycle/SKILL.md` does not exist, construct the prompt:
"Run myco_hunger(execute=true), then myco_immune(fix=true), then propagate via Bash: python -m myco propagate, then diagnose via Bash: python -m myco diagnose. Pass project_dir to all MCP calls. Report any issues."

This ensures the metabolic cycle runs daily even when no human starts a session.
If `list_scheduled_tasks` or `create_scheduled_task` tools are not available, skip — the boot ritual below still runs every session.

## Session Flow

1. **Boot**: `myco_hunger(execute=true)` — checks substrate health, auto-executes repairs
2. **Work**: Do the human's task. Follow these ALWAYS rules:
   - `myco_eat` IMMEDIATELY when: user gives feedback, you make a decision, you learn something, you hit friction
   - `myco_sense` BEFORE answering any factual question about the project
   - `myco_eat` user's natural language feedback THE MOMENT they say it — don't wait, don't treat it as casual conversation
   - **Mycelium maintenance**: after creating ANY new file (note, doc, wiki, skill), add cross-references to related files. Never leave orphans. This is not optional — disconnected knowledge is dead knowledge.
3. **End**: `myco_reflect()` + check `myco_mycelium(action='orphans')` — fix any orphans before closing

## Context Loading (hierarchical)

This project may have subdirectory CLAUDE.md files. Load only when working in that directory.
Priority (highest wins): session override > project CLAUDE.md > user ~/.claude > organization

## Skill Resolution

If a `skills/` directory exists, check for matching skills before starting a task.
If no skill matches (or no skills/ directory), proceed with agent judgment.

## Tool Triggers (19 MCP tools)

| Category | Tools | When to Call |
|----------|-------|-------------|
| **Boot** | `myco_hunger(execute=true)` | FIRST call every session |
| **Health** | `myco_immune`, `myco_pulse` | End of session, after modifying docs |
| **Capture** | `myco_eat` | After decisions, insights, friction |
| **Process** | `myco_digest`, `myco_condense`, `myco_prune` | When hunger signals recommend |
| **Search** | `myco_sense`, `myco_memory` | BEFORE answering factual questions |
| **Analyze** | `myco_mycelium`, `myco_colony` | Before refactoring, compression |
| **External** | `myco_absorb`, `myco_forage` | When gaps detected |
| **Log** | `myco_trace`, `myco_reflect` | After completing tasks, session end |
| **View** | `myco_observe` | When recalling past decisions |
| **Evolve** | `myco_evolve`, `myco_evolve_list` | When skill_degradation hunger signal fires |
| **Undo** | `myco_expand` | When a compression was incorrect |

## Reflex Arcs (auto-enforced)

- **[REFLEX HIGH] raw_backlog** — digest notes before any task work
- **[REFLEX HIGH] contract_drift** — sync contract version first
- **[REFLEX HIGH] craft_reflex_missing** — write craft before kernel changes

## CLI Fallback (for platforms without MCP)

If MCP tools are not available (e.g., Cowork, terminal-only agents), use CLI equivalents via Bash:

| MCP Tool | CLI Equivalent |
|----------|---------------|
| `myco_hunger(execute=true)` | `myco hunger --execute` |
| `myco_immune(fix=true)` | `myco immune --fix` |
| `myco_eat(content=..., tags=...)` | `myco eat --content "..." --tags "t1,t2"` |
| `myco_digest(note_id=...)` | `myco digest <note_id>` |
| `myco_condense(tag=...)` | `myco condense --tag "..."` |
| `myco_expand(output_id=...)` | `myco expand <output_id>` |
| `myco_prune()` | `myco prune [--apply]` |
| `myco_sense(query=...)` | `myco memory sense "..."` |
| `myco_memory()` | `myco memory index` |
| `myco_mycelium(action=...)` | `myco mycelium orphans\|backlinks\|clusters\|stats` |
| `myco_colony(action=...)` | `myco colony suggest\|matrix\|gaps` |
| `myco_observe(note_id=...)` | `myco observe [<note_id>]` |
| `myco_absorb(source=...)` | `myco absorb <source>` |
| `myco_forage(...)` | `myco forage add\|list\|digest` |

MCP-only tools (no CLI equivalent): `myco_pulse`, `myco_trace`, `myco_reflect`, `myco_evolve`, `myco_evolve_list`.
All CLI commands support `--json` for machine-readable output. Run `myco <command> --help` for full options.

## Write Surface

Only write to paths listed in `_canon.yaml::system.write_surface.allowed`.
Anything outside = substrate pollution.
