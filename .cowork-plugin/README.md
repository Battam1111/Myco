# Myco — Cowork plugin

This directory is the **Cowork-plugin** form of Myco: a bundle that
Claude Desktop's Cowork mode can load so the agent sees a correctly-
framed onboarding skill the moment the user opens a Myco substrate.

## Why this exists separately from `.claude-plugin/`

Myco already ships `.claude-plugin/` at the repo root for **Claude Code**
(install via `/plugin marketplace add Battam1111/Myco` + `/plugin install
myco@myco`). Cowork uses the same plugin file shape but is a different
product with a different install path (`%APPDATA%/Claude/local-agent-
mode-sessions/<owner>/<workspace>/rpm/plugin_<ULID>/`) and a different
registry (`rpm/manifest.json`).

This `.cowork-plugin/` directory is the **source-of-truth template**
Myco ships; `scripts/install_cowork_plugin.py` discovers the user's
Cowork plugin dirs, copies the template in, and registers it in the
per-workspace `rpm/manifest.json`.

## Why a skill, not a hook

Cowork does not implement session hooks the way Claude Code does.
Instead, agent behavior is guided by **Skills**: markdown files with
YAML frontmatter that Cowork matches against user intent and agent
context. The single skill shipped here — `myco-substrate` — triggers
whenever the user mentions Myco, opens a workspace containing
`_canon.yaml`, or a prior `substrate_pulse` response referenced the
substrate. The skill's body is the full onboarding brief (what Myco
is, the 18 verbs, R1-R7, pulse reading, multi-project pattern).

## What Cowork loads

After `scripts/install_cowork_plugin.py` runs:

1. `rpm/plugin_myco/.claude-plugin/plugin.json` — plugin metadata.
2. `rpm/plugin_myco/skills/myco-substrate/SKILL.md` — onboarding brief.
3. `rpm/plugin_myco/.mcp.json` — MCP server declaration (redundant
   with `claude_desktop_config.json::mcpServers.myco` but kept for
   self-contained installation).
4. Entry appended to `rpm/manifest.json::plugins`.

Restart Claude Desktop and the Cowork agent will see the Myco skill
on next session start.

## One-line install

```bash
python scripts/install_cowork_plugin.py
```

Run from the Myco repo root. Pass `--dry-run` to preview.

See the script's `--help` for options.
