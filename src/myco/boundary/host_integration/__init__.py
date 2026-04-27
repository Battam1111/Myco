"""``boundary.host_integration`` — per-host Agent-sugar adapters (v0.6.0 PHYSICAL).

**Definition (v0.5.5 protocol; v0.6.0 physical-mounted at boundary)**:
host_integration adapters wire Myco's manifest verbs into one specific
Agent-host environment's native extension surface (Claude Code skills
+ hooks, Cursor rule files, Continue rules, Zed slash commands, Goose
recipes, etc.) without requiring the host to know anything about Myco
internals.

**Not** per-substrate — that is `.myco/plugins/` (substrate-local).
A host_integration adapter is shared across every Myco substrate the
user creates on a given host.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/boundary.md``.

Governing craft:
``docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md``
§A1+§A3 owner amendments (Round 4): physical move from
``src/myco/symbionts/`` to ``src/myco/boundary/host_integration/``
landed at v0.6.0 (no re-export shim — owner instruction "全部一口气
做完").

Ships **all 14 host adapters** with the four-function protocol
(discover / install_basic / install_deep / uninstall):

- ``claude_code.py`` — Anthropic Claude Code (introspection +
  signature verification; the .claude-plugin/ bundle is the
  canonical writer)
- ``cursor.py`` — Cursor 2.0 (writes ~/.cursor/rules/myco.mdc)
- ``cowork.py`` — Anthropic Cowork (Claude Desktop local-agent-mode)
- ``vscode.py`` — Visual Studio Code (writes .vscode/tasks.json)
- ``continue_dev.py`` — Continue (writes ~/.continue/rules/myco.md)
- ``cline.py`` — Cline (writes .clinerules/myco.md)
- ``jetbrains.py`` — JetBrains AI Assistant + Junie 2025.2+
- ``zed.py`` — Zed (writes ~/.config/zed/commands/myco.toml)
- ``goose.py`` — Goose (writes ~/.config/goose/recipes/myco-bootstrap.yaml)
- ``windsurf.py`` — Windsurf (detection only)
- ``codex_cli.py`` — OpenAI Codex CLI (detection only)
- ``gemini_cli.py`` — Google Gemini CLI (detection only)
- ``openclaw.py`` — OpenClaw (detection only)
- ``claude_desktop.py`` — Claude Desktop standalone (detection only)
"""

from __future__ import annotations

from . import (
    claude_code,
    claude_desktop,
    cline,
    codex_cli,
    continue_dev,
    cowork,
    cursor,
    gemini_cli,
    goose,
    jetbrains,
    openclaw,
    vscode,
    windsurf,
    zed,
)

__all__ = [
    "claude_code",
    "claude_desktop",
    "cline",
    "codex_cli",
    "continue_dev",
    "cowork",
    "cursor",
    "gemini_cli",
    "goose",
    "jetbrains",
    "openclaw",
    "vscode",
    "windsurf",
    "zed",
]
