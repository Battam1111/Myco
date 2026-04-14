# Myco — Agent Working Memory

> This file is read automatically at session start by Claude Code / Cowork.
> Authoritative identity and doctrine live in `MYCO.md`. This file is the **operational gateway** — it tells the agent what to do, where to look, and which hooks are active.

## Boot Ritual (MANDATORY — first tool call every session)

```
myco_hunger(execute=true, project_dir=<repo root>)
```

The `SessionStart` hook (see `.claude/hooks/SessionStart.md`) fires this automatically before you read this file. If the hook succeeded you will already see the boot signals in context — scan them for `REFLEX HIGH` before doing anything else. If the hook failed, run `myco_hunger(execute=true)` manually as your first tool call.

## Where to Look (priority order)

| Question | Read |
|----------|------|
| What is Myco and why does it exist? | `MYCO.md` (identity anchors) |
| Formal contract with the agent | `docs/agent_protocol.md` |
| Which MCP tool do I call for X? | `docs/agent_protocol.md` (tool triggers) + `src/myco/mcp_server.py` (tool descriptions) |
| What's the substrate shape? | `_canon.yaml` (single source of truth for every number, name, and path) |
| What was decided recently? | `notes/` (digested) + `log.md` (timeline) |
| Which lint dimensions apply? | `src/myco/immune.py` (L0–L28) |

## Hard Contract (enforced by hooks + immune)

1. **Every session begins with `myco_hunger(execute=true)`.** Enforced by `SessionStart` hook.
2. **Every session ends with `myco_reflect` + `myco_immune(fix=true)`.** Enforced by `PreCompact` hook and `myco_session_end`.
3. **Before any factual claim about the project, call `myco_sense` first.** Not enforced mechanically — this is on you.
4. **Every decision, insight, friction point, and user feedback gets `myco_eat`'d immediately.** Not at end of session. Now.
5. **After creating any new file, add cross-references to related files.** Orphans are dead knowledge; the mycelium graph is the substrate's circulatory system.
6. **Write only to paths in `_canon.yaml::system.write_surface.allowed`.** Everything else is substrate pollution.

## Mode

You are working on **Myco itself** — the framework, not a downstream project. That means:

- Changes to `src/myco/` are kernel changes. Write the craft doc first (identity anchor #8).
- Changes to `MYCO.md`, `docs/agent_protocol.md`, `_canon.yaml` are contract changes. Bump the contract version and log in `docs/contract_changelog.md`.
- `myco immune --project-dir .` from the repo root is how you check your own health. Don't point it at `src/`.
- Version numbers live in **two** places (`pyproject.toml` + `src/myco/__init__.py`). Keep them in sync or the release workflow bakes the wrong tag.

## Active Hooks

- `SessionStart` → `python -m myco hunger --execute --json --project-dir .`
- `PreCompact` → `python -m myco reflect --json --project-dir . && python -m myco immune --fix --json --project-dir .`

If either hook is missing from `.claude/settings.local.json::hooks`, the mandate isn't enforced — add it back before continuing.

## Related

- `MYCO.md` — identity and doctrine
- `.claude/hooks/SessionStart.md` — boot ritual contract
- `.claude/hooks/PreCompact.md` — consolidation ritual contract
- `.claude/skills/` — Cowork skills (myco-boot, myco-eat, myco-search, and more)
