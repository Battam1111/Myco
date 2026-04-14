"""
Myco Symbionts — adapter layer for zero-touch session hooks across environments.

Wave 55 (vision_closure_craft_2026-04-14.md, Partition B G7):
Abstracts session lifecycle hooks for Cowork, Claude Code, Cursor, VS Code, Continue, Zed.

Design:
    - Each host has a detect() function and check_hooks() inspector.
    - Degradation ladder: native hooks → daemon → protocol.
    - All adapters are graceful (missing hooks return status, not errors).

Public surface:
    detect_active_symbiont() -> str | None
    effective_hook_level(root) -> Literal["native", "daemon", "protocol"]
    check_all_hooks(root) -> dict
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional


def detect_active_symbiont() -> Optional[str]:
    """Detect which symbiont environment is active.

    Checks in priority order:
    1. COWORK_SESSION env var
    2. Cowork directory structure
    3. Claude Code .claude/ directory
    4. Cursor .cursor/ directory
    5. VS Code .vscode/ directory
    6. Continue .continue/ directory
    7. Zed .zed/ directory
    8. Codex ~/.codex/ or CLI
    9. Cline global settings
    10. Windsurf ~/.codeium/windsurf/ or CLI

    Returns: "cowork" | "claude_code" | "cursor" | "vscode" | "continue" | "zed" |
             "codex" | "cline" | "windsurf" | None
    """
    from myco.symbionts import codex, cline, windsurf

    cwd = Path.cwd()

    # Check Cowork (highest priority)
    if os.getenv("COWORK_SESSION"):
        return "cowork"
    if str(cwd).startswith("/sessions/"):
        return "cowork"

    # Check Claude Code
    if (cwd / ".claude").exists():
        return "claude_code"

    # Check Cursor
    if os.getenv("CURSOR_SESSION"):
        return "cursor"
    if (cwd / ".cursor").exists():
        return "cursor"

    # Check VS Code
    if (cwd / ".vscode").exists():
        return "vscode"

    # Check Continue
    if (cwd / ".continue").exists():
        return "continue"

    # Check Zed
    if (cwd / ".zed").exists():
        return "zed"

    # Check Codex (global CLI)
    if codex.detect():
        return "codex"

    # Check Cline (global settings)
    if cline.detect():
        return "cline"

    # Check Windsurf (global CLI)
    if windsurf.detect():
        return "windsurf"

    return None


def effective_hook_level(root: Path) -> Literal["native", "daemon", "protocol"]:
    """Determine best available hook level for this host.

    Degradation ladder:
    1. native: true session hooks (plugin/host-native)
    2. daemon: background process monitoring
    3. protocol: text-protocol fallback (always available)

    For now, all adapters support at least protocol level.
    """
    host = detect_active_symbiont()

    # Cowork: native hooks via plugin
    if host == "cowork":
        return "native"

    # Claude Code: native hooks via .claude/settings.json
    if host == "claude_code":
        return "native"

    # Cursor: native hooks via .cursor/rules
    if host == "cursor":
        return "native"

    # VS Code: protocol only (no native hook support yet)
    if host == "vscode":
        return "protocol"

    # Continue: MCP-only bootstrap model
    if host == "continue":
        return "protocol"  # Note: continue uses MCP but no native hooks

    # Zed: MCP-only bootstrap model
    if host == "zed":
        return "protocol"  # Note: zed uses MCP but no native hooks

    # Codex: rules-based hooks on Unix, protocol on Windows
    if host == "codex":
        import sys
        return "native" if sys.platform != "win32" else "protocol"

    # Cline: global JSON config (MCP settings)
    if host == "cline":
        return "protocol"

    # Windsurf: rules files (.windsurf/rules/*.md)
    if host == "windsurf":
        return "native"

    # Unknown/local: protocol fallback
    return "protocol"


def check_all_hooks(root: Path) -> dict:
    """Run all host adapters' hook checks.

    Returns dict with per-adapter status and summary.
    """
    from myco.symbionts import cowork, claude_code, cursor, vscode, continue_, zed, codex, cline, windsurf

    results = {
        "detected_symbiont": detect_active_symbiont(),
        "effective_level": effective_hook_level(root),
        "adapters": {},
        "summary": {
            "all_ok": True,
            "issues": [],
        },
    }

    for adapter_name, adapter_module in [
        ("cowork", cowork),
        ("claude_code", claude_code),
        ("cursor", cursor),
        ("vscode", vscode),
        ("continue", continue_),
        ("zed", zed),
        ("codex", codex),
        ("cline", cline),
        ("windsurf", windsurf),
    ]:
        try:
            status = adapter_module.check_hooks(root)
            results["adapters"][adapter_name] = status
            if status.get("issues"):
                results["summary"]["all_ok"] = False
                results["summary"]["issues"].extend(
                    [f"{adapter_name}: {issue}" for issue in status["issues"]]
                )
        except Exception as exc:
            results["adapters"][adapter_name] = {"error": str(exc)}
            results["summary"]["all_ok"] = False

    return results
