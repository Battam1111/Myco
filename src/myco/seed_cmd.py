#!/usr/bin/env python3
"""
Myco Project Initializer — creates a new Myco-powered project scaffold.
"""

import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path

from myco.templates import get_templates_dir, get_template, fill_template


def _metabolic_skill_content(project_dir: str) -> str:
    """
    Return the SKILL.md content for the scheduled metabolic cycle task.

    Single source of truth -- used by both ``--agent claude`` and
    ``--auto-detect`` code paths.  The ``allowed-tools`` frontmatter
    pre-approves every Myco MCP tool so the task runs without manual
    approval on first execution.

    NOTE: This file is written to .claude/scheduled-tasks/ as a **template**.
    The Agent must register it with Claude Code's scheduler via
    ``create_scheduled_task`` MCP tool on first boot (see CLAUDE.md
    First-Boot Setup section).  The file alone does NOT auto-schedule.
    """
    return (
        "---\n"
        "name: myco-metabolic-cycle\n"
        "description: Daily Myco metabolic cycle — hunger check + auto-heal + lint verification + self-verify\n"
        "allowed-tools:\n"
        "  - mcp__myco__myco_hunger\n"
        "  - mcp__myco__myco_immune\n"
        "  - mcp__myco__myco_trace\n"
        "  - mcp__myco__myco_memory\n"
        "  - mcp__myco__myco_digest\n"
        "  - mcp__myco__myco_condense\n"
        "  - mcp__myco__myco_prune\n"
        "  - mcp__myco__myco_pulse\n"
        "  - mcp__myco__myco_observe\n"
        "  - mcp__myco__myco_eat\n"
        "  - mcp__myco__myco_sense\n"
        "  - mcp__myco__myco_colony\n"
        "  - mcp__myco__myco_mycelium\n"
        "  - mcp__myco__myco_reflect\n"
        "  - mcp__myco__myco_evolve\n"
        "  - mcp__myco__myco_evolve_list\n"
        "  - mcp__myco__myco_absorb\n"
        "  - mcp__myco__myco_forage\n"
        "  - mcp__myco__myco_expand\n"
        "---\n"
        "\n"
        f"Run the Myco metabolic cycle. The project root is {project_dir}.\n"
        f"Pass project_dir=\"{project_dir}\" to EVERY myco MCP tool call.\n"
        "\n"
        "Steps:\n"
        f"1. Call myco_hunger(execute=true, project_dir=\"{project_dir}\") to auto-heal the substrate\n"
        "2. If any signal is REFLEX HIGH, address it immediately using the appropriate tool (always pass project_dir)\n"
        f"3. If session_index_missing signal appears, call myco_memory(action='index', project_dir=\"{project_dir}\")\n"
        f"4. Call myco_immune(project_dir=\"{project_dir}\", fix=true) to auto-repair mechanical issues, then verify 0 remaining\n"
        f"5. Run SSoT propagation via Bash: `cd \"{project_dir}\" && python -m myco propagate --project-dir \"{project_dir}\"`\n"
        f"6. Call myco_trace(entry_type='system', message='Metabolic cycle complete. Status: [healthy/N issues]', project_dir=\"{project_dir}\")\n"
        f"7. Self-verify: Run deployment health check via Bash: `cd \"{project_dir}\" && python -m myco diagnose --project-dir \"{project_dir}\"`\n"
        f"8. If verify finds issues (non-zero exit code), call myco_trace(entry_type='system', message='CRITICAL: Deployment verification failed: [list issues from verify output]', project_dir=\"{project_dir}\")\n"
        "9. If any check in the cycle failed (hunger REFLEX HIGH, lint issues, or verify issues), report: \"METABOLIC CYCLE FOUND DEPLOYMENT ISSUES: [list all issues]\"\n"
        "10. Report completion\n"
        "\n"
        "## Fallback: CLI commands (auto-approved via settings.json)\n"
        "\n"
        "If MCP tools are unavailable, use these Bash commands instead:\n"
        "```bash\n"
        f"cd \"{project_dir}\" && python -m myco hunger --execute\n"
        f"cd \"{project_dir}\" && python -m myco immune --fix\n"
        f"cd \"{project_dir}\" && python -m myco propagate\n"
        f"cd \"{project_dir}\" && python -m myco diagnose\n"
        "```\n"
        "These match the allowed Bash patterns in settings.json and run without approval.\n"
    )


def get_date():
    return datetime.now().strftime("%Y-%m-%d")


###############################################################################
# Auto-detect: detect_tools + per-tool MCP config generators
###############################################################################

# Canonical Myco MCP server definition — single source of truth.
_MYCO_SERVER_STDIO = {
    "command": "python",
    "args": ["-m", "myco.mcp_server"],
    "env": {"PYTHONUNBUFFERED": "1"},
}

# Bash patterns auto-allowed in .claude/settings.json — single source of truth.
_MYCO_BASH_PATTERNS: list[str] = [
    "mcp__myco__*",
    "Bash(python -m myco*)",
    "Bash(python3 -m myco*)",
    "Bash(python -c *myco*)",
    "Bash(myco *)",
]


def detect_tools(project_dir: Path) -> dict[str, bool]:
    """
    Detect which AI tools / editors are available.

    Returns a dict mapping tool name -> detected (bool).
    Detection heuristics per tool:
      Claude Code : ``claude`` on PATH  OR  ``CLAUDE_CODE`` env var  OR
                    ``.mcp.json`` in project dir  OR  parent process name
                    contains "claude" (covers running FROM Claude Code)
      Cursor      : ``.cursor/`` in project dir  OR  ``cursor`` on PATH
      VS Code     : ``.vscode/`` in project dir  OR  ``code`` on PATH
      Codex       : ``~/.codex/`` exists          OR  ``codex`` on PATH
      Cline       : global ``cline_mcp_settings.json`` exists (OS-specific)
      Continue    : ``.continue/`` in project dir
      Windsurf    : ``windsurf`` on PATH  OR  ``~/.codeium/windsurf/`` exists
      Zed         : ``zed`` on PATH
    """
    home = Path.home()

    # Claude Code: multi-signal detection (CLI may not be on PATH when
    # running FROM Claude Code itself).
    def _detect_claude_code() -> bool:
        if shutil.which("claude") is not None:
            return True
        if os.environ.get("CLAUDE_CODE"):
            return True
        if (project_dir / ".mcp.json").is_file():
            return True
        # Best-effort: check parent process name
        try:
            import psutil
            parent = psutil.Process(os.getpid()).parent()
            if parent and "claude" in (parent.name() or "").lower():
                return True
        except Exception:
            pass
        return False

    return {
        "Claude Code": _detect_claude_code(),
        "Cursor":      (project_dir / ".cursor").is_dir()
                       or shutil.which("cursor") is not None,
        "VS Code":     (project_dir / ".vscode").is_dir()
                       or shutil.which("code") is not None,
        "Codex":       (home / ".codex").is_dir()
                       or shutil.which("codex") is not None,
        "Cline":       _cline_settings_path().is_file(),
        "Continue":    (project_dir / ".continue").is_dir(),
        "Windsurf":    shutil.which("windsurf") is not None
                       or (home / ".codeium" / "windsurf").is_dir(),
        "Zed":         shutil.which("zed") is not None,
    }


def _deep_merge(base: dict, override: dict) -> dict:
    """Recursively merge *override* into *base*, preserving nested dicts."""
    result = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


def _json_merge_write(path: Path, patch: dict, *, deep_key: str | None = None) -> str:
    """
    Deep-merge *patch* into the JSON file at *path*.

    If the file exists, parse it and recursively merge so that nested
    dict keys (e.g. ``mcpServers.other``) are preserved when adding
    ``mcpServers.myco``.
    If the file does not exist (or is invalid JSON), write *patch* as-is.

    Returns a human-readable status string ("merged", "created", "created -- old file was invalid").
    """
    if path.exists():
        try:
            existing = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, ValueError):
            path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
            return "created \u2014 old file was invalid"
        existing = _deep_merge(existing, patch)
        path.write_text(json.dumps(existing, indent=2) + "\n", encoding="utf-8")
        return "merged"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(patch, indent=2) + "\n", encoding="utf-8")
        return "created"


def _toml_merge_write(path: Path, myco_block: str) -> str:
    """
    Merge a TOML snippet (``[mcp_servers.myco]`` block) into *path*.

    Naive but correct for the codex config shape: if the file exists and
    already contains ``[mcp_servers.myco]``, skip; otherwise append.
    """
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if "[mcp_servers.myco]" in existing:
            return "already configured — skipped"
        # Also detect legacy wrong table name from older Myco versions
        if "[mcp.servers.myco]" in existing:
            return "already configured — skipped"
        path.write_text(existing.rstrip() + "\n\n" + myco_block + "\n", encoding="utf-8")
        return "merged"
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(myco_block + "\n", encoding="utf-8")
        return "created"


# ── Per-tool config generators ────────────────────────────────────────

def _gen_claude_code(project_dir: Path) -> str:
    """Generate / merge .mcp.json for Claude Code."""
    payload = {
        "mcpServers": {
            "myco": {**_MYCO_SERVER_STDIO}
        }
    }
    path = project_dir / ".mcp.json"
    return _json_merge_write(path, payload)


def _gen_cursor(project_dir: Path) -> str:
    """Generate / merge .cursor/mcp.json for Cursor."""
    payload = {
        "mcpServers": {
            "myco": {**_MYCO_SERVER_STDIO}
        }
    }
    cursor_dir = project_dir / ".cursor"
    cursor_dir.mkdir(exist_ok=True)
    path = cursor_dir / "mcp.json"
    return _json_merge_write(path, payload)


def _gen_vscode(project_dir: Path) -> str:
    """Generate / merge .vscode/mcp.json for VS Code + Copilot."""
    payload = {
        "servers": {
            "myco": {
                "type": "stdio",
                **_MYCO_SERVER_STDIO,
            }
        }
    }
    vscode_dir = project_dir / ".vscode"
    vscode_dir.mkdir(exist_ok=True)
    path = vscode_dir / "mcp.json"
    return _json_merge_write(path, payload)


def _gen_codex(project_dir: Path) -> str:
    """Generate / merge ~/.codex/config.toml for Codex."""
    block = (
        '[mcp_servers.myco]\n'
        'command = "python"\n'
        'args = ["-m", "myco.mcp_server"]'
    )
    path = Path.home() / ".codex" / "config.toml"
    return _toml_merge_write(path, block)


def _cline_settings_path() -> Path:
    """Return the OS-specific path for Cline's global MCP settings file."""
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
        # Fallback if APPDATA is not set
        return Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    elif sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
    else:
        # Linux and other Unix-like systems
        return Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"


def _gen_cline(project_dir: Path) -> str:
    """Generate / merge cline_mcp_settings.json for Cline (global, OS-specific path)."""
    payload = {
        "mcpServers": {
            "myco": {**_MYCO_SERVER_STDIO}
        }
    }
    path = _cline_settings_path()
    return _json_merge_write(path, payload)


def _gen_continue(project_dir: Path) -> str:
    """Generate .continue/mcpServers/myco.json for Continue.

    Continue auto-imports Claude-Desktop-compatible JSON files from the
    .continue/mcpServers/ directory. This is the simplest and most
    forward-compatible approach (works with both config.json and
    config.yaml eras).
    """
    payload = {
        "mcpServers": {
            "myco": {**_MYCO_SERVER_STDIO}
        }
    }
    mcp_dir = project_dir / ".continue" / "mcpServers"
    mcp_dir.mkdir(parents=True, exist_ok=True)
    path = mcp_dir / "myco.json"
    return _json_merge_write(path, payload)


def _gen_windsurf(project_dir: Path) -> str:
    """Generate / merge ~/.codeium/windsurf/mcp_config.json for Windsurf."""
    payload = {
        "mcpServers": {
            "myco": {**_MYCO_SERVER_STDIO}
        }
    }
    path = Path.home() / ".codeium" / "windsurf" / "mcp_config.json"
    return _json_merge_write(path, payload)


def _gen_zed(project_dir: Path) -> str:
    """Generate / merge settings.json (Zed) with context_servers block."""
    payload = {
        "context_servers": {
            "myco": {
                "source": "custom",
                **_MYCO_SERVER_STDIO,
            }
        }
    }
    # Zed uses a global settings.json; for project-local we write to
    # .zed/settings.json (Zed's project-settings convention).
    zed_dir = project_dir / ".zed"
    zed_dir.mkdir(exist_ok=True)
    path = zed_dir / "settings.json"
    return _json_merge_write(path, payload)


def _gen_claude_md(project_dir: Path, replacements: dict) -> str:
    """Generate / merge CLAUDE.md as the universal entry point."""
    claude_content = fill_template(get_template("CLAUDE.md"), replacements)
    claude_path = project_dir / "CLAUDE.md"
    if claude_path.exists():
        existing = claude_path.read_text(encoding="utf-8")
        if "myco" not in existing.lower() and "Myco" not in existing:
            merged = existing.rstrip() + "\n\n---\n\n" + claude_content
            claude_path.write_text(merged, encoding="utf-8")
            return "Myco section appended"
        else:
            return "already contains Myco config — skipped"
    else:
        claude_path.write_text(claude_content, encoding="utf-8")
        return "created"


# Mapping from tool name to (generator_func, config_path_description)
_TOOL_GENERATORS: dict[str, tuple] = {
    "Claude Code": (_gen_claude_code, ".mcp.json"),
    "Cursor":      (_gen_cursor,      ".cursor/mcp.json"),
    "VS Code":     (_gen_vscode,      ".vscode/mcp.json"),
    "Codex":       (_gen_codex,       "~/.codex/config.toml"),
    "Cline":       (_gen_cline,       "cline_mcp_settings.json (global)"),
    "Continue":    (_gen_continue,    ".continue/mcpServers/myco.json"),
    "Windsurf":    (_gen_windsurf,    "~/.codeium/windsurf/mcp_config.json"),
    "Zed":         (_gen_zed,         ".zed/settings.json"),
}

def run_connect(args) -> int:
    """Connect a project to a global Myco instance.

    Generates .mcp.json (+ platform configs) pointing to MYCO_ROOT.
    Does NOT create notes/, wiki/, _canon.yaml etc. — those live in
    the global Myco directory.
    """
    import os
    myco_root = getattr(args, "myco_root", None) or os.environ.get("MYCO_ROOT")
    if not myco_root:
        # Try to find Myco installation
        candidates = [
            Path.home() / "Myco",
            Path.home() / "Desktop" / "Myco",
            Path.home() / "myco",
        ]
        for c in candidates:
            if (c / "_canon.yaml").exists():
                myco_root = str(c.resolve())
                break
    if not myco_root or not Path(myco_root).exists():
        print("Error: Cannot find Myco installation.")
        print("  Either set MYCO_ROOT environment variable, or pass --myco-root PATH")
        print("  Myco should be installed via: git clone ... && pip install -e '.[mcp]'")
        return 1

    myco_root = str(Path(myco_root).resolve())
    project_dir = Path(getattr(args, "project_dir", ".")).resolve()

    print(f"\n🍄 Myco — Connecting project to global instance")
    print(f"   Myco root: {myco_root}")
    print(f"   Project:   {project_dir}\n")

    # Generate .mcp.json with MYCO_ROOT env var
    server_with_root = {
        "command": "python",
        "args": ["-m", "myco.mcp_server"],
        "env": {
            "PYTHONUNBUFFERED": "1",
            "MYCO_ROOT": myco_root,
        },
    }
    mcp_payload = {"mcpServers": {"myco": server_with_root}}
    mcp_path = project_dir / ".mcp.json"
    _json_merge_write(mcp_path, mcp_payload)
    print(f"  ✅ .mcp.json (pointing to {myco_root})")

    # Auto-detect and configure other platforms
    detected = detect_tools(project_dir)
    for tool_name, is_detected in detected.items():
        if is_detected and tool_name in _TOOL_GENERATORS:
            gen_func, desc = _TOOL_GENERATORS[tool_name]
            # For platform configs, we need to patch MYCO_ROOT into env
            # The generators use _MYCO_SERVER_STDIO which doesn't have MYCO_ROOT
            # So we temporarily patch it
            old_env = _MYCO_SERVER_STDIO.get("env", {})
            _MYCO_SERVER_STDIO["env"] = {**old_env, "MYCO_ROOT": myco_root}
            try:
                status = gen_func(project_dir)
                print(f"  ✅ {desc} ({status})")
            finally:
                _MYCO_SERVER_STDIO["env"] = old_env

    # Generate CLAUDE.md entry point with Myco instructions
    from myco.templates import get_template, fill_template
    replacements = {
        "PROJECT_NAME": project_dir.name,
        "DATE": get_date(),
        "GITHUB_USER": "your-username",
    }
    status = _gen_claude_md(project_dir, replacements)
    print(f"  ✅ CLAUDE.md ({status})")

    # Generate settings.json with auto-allow patterns
    settings_dir = project_dir / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)
    settings_path = settings_dir / "settings.json"
    settings_payload = {
        "permissions": {
            "allow": _MYCO_BASH_PATTERNS
        }
    }
    _json_merge_write(settings_path, settings_payload)
    print(f"  ✅ .claude/settings.json (auto-allow patterns)")

    # Generate Cowork skill stubs
    for skill_name, skill_content in _COWORK_SKILLS.items():
        skill_dir = settings_dir / "skills" / skill_name
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.exists():
            skill_path.write_text(skill_content, encoding="utf-8")
    print(f"  ✅ .claude/skills/myco-*/  (Cowork skill stubs)")

    # Generate scheduled metabolic cycle
    sched_dir = Path.home() / ".claude" / "scheduled-tasks" / "myco-metabolic-cycle"
    sched_dir.mkdir(parents=True, exist_ok=True)
    skill_md = sched_dir / "SKILL.md"
    skill_content = _metabolic_skill_content(myco_root)
    skill_md.write_text(skill_content, encoding="utf-8")
    print(f"  ✅ ~/.claude/scheduled-tasks/myco-metabolic-cycle/")

    # Generate pre-commit hook if .git exists
    _generate_pre_commit_hook(project_dir)
    git_hooks = project_dir / ".git" / "hooks" / "pre-commit"
    if git_hooks.exists():
        print(f"  ✅ .git/hooks/pre-commit (immune gate)")

    print(f"\n🍄 Connected! Myco tools will use knowledge from {myco_root}")
    print(f"   All projects sharing one Myco = one brain, many hands.")
    print(f"   Run `myco diagnose --project-dir .` to verify everything works.\n")
    return 0


# Tip printed after SKILL.md creation to guide first-run permission grant.
_METABOLIC_TIP = (
    "\n"
    "  \U0001f4a1 TIP: Run the metabolic cycle once now to pre-approve tools:\n"
    "     In Claude Code, type: /myco-boot\n"
    "     This grants permissions so the daily cycle runs automatically.\n"
)

# Cowork-compatible skill stubs — single source of truth for both code paths.
# Skills use dual-mode instructions: try MCP first, fall back to CLI via Bash.
# This ensures they work on any platform (Claude Code, Cowork, Cursor, etc.).
_COWORK_SKILLS: dict[str, str] = {
    "myco-boot": (
        "---\nname: myco-boot\n"
        "description: Boot Myco substrate — run hunger check and auto-heal\n"
        "---\n\n"
        "## MCP mode (preferred)\n"
        "Call myco_hunger(execute=true, project_dir=<project_root>) to check\n"
        "substrate health and auto-fix issues.\n\n"
        "## CLI mode (fallback — if MCP tools are not available)\n"
        "Run via Bash: `myco hunger --execute --json`\n"
        "Parse the JSON output for signals and actions.\n\n"
        "## Either mode\n"
        "If any REFLEX HIGH signals appear, address them before other work.\n"
        "Then report substrate status to the user.\n"
    ),
    "myco-eat": (
        "---\nname: myco-eat\n"
        "description: Capture knowledge into Myco — decisions, insights, friction, feedback\n"
        "---\n\n"
        "## MCP mode (preferred)\n"
        "Call myco_eat(content=..., tags=..., project_dir=<project_root>).\n\n"
        "## CLI mode (fallback — if MCP tools are not available)\n"
        "Run via Bash: `myco eat --content \"...\" --tags \"t1,t2\" --json`\n\n"
        "## Either mode\n"
        "Use this whenever: a decision is made, friction is encountered,\n"
        "the user gives feedback, or you learn something important.\n"
        "Always include relevant tags for future retrieval.\n"
    ),
    "myco-search": (
        "---\nname: myco-search\n"
        "description: Search Myco substrate for existing knowledge before answering\n"
        "---\n\n"
        "## MCP mode (preferred)\n"
        "Call myco_sense(query=..., project_dir=<project_root>).\n\n"
        "## CLI mode (fallback — if MCP tools are not available)\n"
        "Run via Bash: `myco memory sense \"<query>\" --json`\n\n"
        "## Either mode\n"
        "Check results BEFORE answering factual questions about the project.\n"
        "The substrate may already have the answer.\n"
    ),
}


def run_auto_detect(args) -> int:
    """Entry point for ``myco seed --auto-detect``."""
    if args.dir:
        project_dir = Path(args.dir)
    else:
        project_dir = Path.cwd() / args.name

    project_dir.mkdir(parents=True, exist_ok=True)

    entry_point = "CLAUDE.md"  # auto-detect always uses CLAUDE.md

    replacements = {
        "PROJECT_NAME": args.name,
        "DATE": get_date(),
        "CURRENT_PHASE": "Phase 0 — Setup",
        "PROJECT_DESCRIPTION": f"[{args.name} — describe your project goal in one sentence]",
        "PROJECT_SUMMARY": "[Describe the project's core objective and methodology in 2-3 sentences]",
        "GITHUB_USER": args.github_user,
        "ENTRY_POINT": entry_point,
    }

    level_names = {0: "Minimal", 1: "Standard", 2: "Full"}

    print(f"\n\U0001f344 Myco \u2014 Initializing project: {args.name}")
    print(f"   Level: L{args.level} ({level_names[args.level]})")
    print(f"   Entry point: {entry_point}")
    print(f"   Location: {project_dir.resolve()}")
    print()

    # Scaffold the project at the requested level
    if args.level == 0:
        init_level_0(project_dir, replacements, entry_point)
    elif args.level == 1:
        init_level_1(project_dir, replacements, entry_point)
    elif args.level == 2:
        init_level_2(project_dir, replacements, entry_point)

    # Detect tools
    detected = detect_tools(project_dir)

    print(f"\n\U0001f344 Myco \u2014 Auto-detected tools:")

    for tool_name, is_detected in detected.items():
        if is_detected:
            gen_fn, config_desc = _TOOL_GENERATORS[tool_name]
            status = gen_fn(project_dir)
            print(f"  \u2705 {tool_name} ({config_desc} {status})")
        else:
            _, config_desc = _TOOL_GENERATORS[tool_name]
            print(f"  \u23ed\ufe0f  {tool_name} (not detected)")

    # Always generate CLAUDE.md as universal entry point
    md_status = _gen_claude_md(project_dir, replacements)
    print(f"  \u2705 CLAUDE.md ({md_status})")

    # Claude Code automation: scheduled task + Cowork skills + settings.json
    # These are generated regardless of whether Claude Code was detected,
    # because --auto-detect users may install Claude Code later.
    import json

    # Scheduled metabolic cycle task
    sched_dir = project_dir / ".claude" / "scheduled-tasks" / "myco-metabolic-cycle"
    sched_dir.mkdir(parents=True, exist_ok=True)
    sched_skill = sched_dir / "SKILL.md"
    if not sched_skill.exists():
        # Use forward slashes for the project_dir in the SKILL.md content
        proj_str = str(project_dir.resolve()).replace("\\", "/")
        sched_skill.write_text(
            _metabolic_skill_content(proj_str),
            encoding="utf-8",
        )
    print(f"  \u2705 .claude/scheduled-tasks/myco-metabolic-cycle/")
    print(_METABOLIC_TIP)

    # Cowork-compatible skill stubs (uses module-level _COWORK_SKILLS)
    for skill_name, skill_content in _COWORK_SKILLS.items():
        skill_dir = project_dir / ".claude" / "skills" / skill_name
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.exists():
            skill_dir.mkdir(parents=True, exist_ok=True)
            skill_file.write_text(skill_content, encoding="utf-8")
    print(f"  \u2705 .claude/skills/myco-*/  (Cowork-compatible skill stubs)")

    # Settings.json with auto-allow for Myco MCP tools (merge into existing)
    settings_dir = project_dir / ".claude"
    settings_file = settings_dir / "settings.json"
    myco_settings = {
        "permissions": {
            "allow": _MYCO_BASH_PATTERNS
        }
    }
    status = _json_merge_write(settings_file, myco_settings)
    print(f"  \u2705 .claude/settings.json ({status})")

    # Pre-commit hook: only if .git/ exists
    if _generate_pre_commit_hook(project_dir):
        print(f"  \u2705 .git/hooks/pre-commit (Myco lint gate)")

    print(f"\n\U0001f344 Done! Myco auto-detect complete.")
    print(f"   MCP configs generated for all detected tools.")
    print(f"   Scheduled metabolic cycle + Cowork skills ready.")
    print(f"   Run your preferred AI tool in {project_dir.resolve()}")
    print(f"")
    print(f"   \u26a0\ufe0f  Cowork users: project-level .mcp.json is NOT auto-loaded by Cowork.")
    print(f"   Install the myco.plugin for full MCP auto-injection.")
    print(f"   See: docs/agent_protocol.md \u00a70.5 'Cowork Plugin' for details.")

    return 0


###############################################################################
# Level-based scaffolding (existing)
###############################################################################

_GITIGNORE_CONTENT = """\
__pycache__/
*.pyc
.myco_state/
.env
.env.*
"""


def _generate_pre_commit_hook(project_dir: Path) -> bool:
    """Generate .git/hooks/pre-commit that runs ``myco immune --quick``.

    Returns True if a hook was written or already present, False if the
    project is not a git repo (no .git/ directory).

    Behavior:
      - If no .git/ exists, return False (not a git repo).
      - If a pre-commit hook already exists and contains "myco", skip.
      - If a pre-commit hook exists but is NOT from Myco, append the
        Myco lint check (respects existing hooks).
      - Otherwise, create a fresh bash hook.
    """
    git_hooks = project_dir / ".git" / "hooks"
    if not git_hooks.parent.exists():  # Not a git repo
        return False
    git_hooks.mkdir(parents=True, exist_ok=True)
    hook_path = git_hooks / "pre-commit"

    # Don't overwrite existing custom hooks
    if hook_path.exists():
        content = hook_path.read_text(encoding="utf-8", errors="replace")
        if "myco" not in content:
            # Existing non-Myco hook — don't overwrite, append instead
            content += (
                "\n\n# Myco pre-commit lint check\n"
                "python -m myco immune --quick --project-dir . || exit 1\n"
            )
            hook_path.write_text(content, encoding="utf-8")
        return True

    hook_content = (
        "#!/bin/bash\n"
        "# Myco pre-commit hook — prevents committing with lint issues\n"
        "# Generated by `myco seed`. Safe to customize.\n"
        "\n"
        "python -m myco immune --quick --project-dir .\n"
        "if [ $? -ne 0 ]; then\n"
        '    echo ""\n'
        '    echo "Myco lint failed. Fix issues before committing."\n'
        '    echo "   Run: myco immune --fix    (auto-repair mechanical issues)"\n'
        '    echo "   Run: myco immune          (see all issues)"\n'
        '    echo ""\n'
        "    exit 1\n"
        "fi\n"
    )
    hook_path.write_text(hook_content, encoding="utf-8")
    # Make executable (on Unix)
    try:
        import stat
        hook_path.chmod(hook_path.stat().st_mode | stat.S_IEXEC)
    except Exception:
        pass
    return True


def init_level_0(project_dir: Path, replacements: dict, entry_point: str):
    """Minimal: entry_point + log.md + .gitignore"""
    entry_content = fill_template(get_template("MYCO.md"), replacements)
    (project_dir / entry_point).write_text(entry_content, encoding="utf-8")

    log_content = fill_template(get_template("log.md"), replacements)
    (project_dir / "log.md").write_text(log_content, encoding="utf-8")

    # .gitignore — only create if absent (never overwrite user's .gitignore)
    gitignore_path = project_dir / ".gitignore"
    if not gitignore_path.exists():
        gitignore_path.write_text(_GITIGNORE_CONTENT, encoding="utf-8")
        print(f"  ✅ .gitignore")

    print(f"  ✅ {entry_point} (L1 Index)")
    print(f"  ✅ log.md (Timeline)")

    # Pre-commit hook: only if .git/ exists
    if _generate_pre_commit_hook(project_dir):
        print(f"  ✅ .git/hooks/pre-commit (Myco lint gate)")


def init_level_1(project_dir: Path, replacements: dict, entry_point: str):
    """Standard: + WORKFLOW.md + _canon.yaml + wiki/ + scripts/"""
    init_level_0(project_dir, replacements, entry_point)

    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "WORKFLOW.md").write_text(
        fill_template(get_template("WORKFLOW.md"), replacements), encoding="utf-8"
    )
    print(f"  ✅ docs/WORKFLOW.md (Thirteen Principles)")

    (project_dir / "_canon.yaml").write_text(
        fill_template(get_template("_canon.yaml"), replacements), encoding="utf-8"
    )
    print(f"  ✅ _canon.yaml (Canonical Values SSoT)")

    (project_dir / "wiki").mkdir(exist_ok=True)
    (project_dir / "docs" / "primordia").mkdir(exist_ok=True)
    (project_dir / "scripts").mkdir(exist_ok=True)
    print(f"  ✅ wiki/ (Knowledge pages — create on demand)")
    print(f"  ✅ docs/primordia/ (Craft debate records — append-only)")
    print(f"  ✅ scripts/ (Tool scripts)")

    # Digestive substrate — notes/ directory with a README stub so the
    # folder isn't empty on first clone. The four-command set (eat/digest/
    # view/hunger) reads and writes here.
    notes_dir = project_dir / "notes"
    notes_dir.mkdir(exist_ok=True)
    notes_readme = notes_dir / "README.md"
    if not notes_readme.exists():
        notes_readme.write_text(
            "# notes/ — Digestive Substrate\n"
            "\n"
            "Atomic notes live here as flat files with YAML frontmatter.\n"
            "Filename pattern: `n_YYYYMMDDTHHMMSS_xxxx.md`\n"
            "\n"
            "## Four-command set\n"
            "\n"
            "- `myco eat`     — capture content as a raw note (zero-friction)\n"
            "- `myco digest`  — move a note through the lifecycle\n"
            "- `myco view`    — list or read notes\n"
            "- `myco hunger`  — metabolic dashboard with actionable signals\n"
            "\n"
            "## Lifecycle\n"
            "\n"
            "`raw → digesting → {extracted | integrated | excreted}`\n"
            "\n"
            "See `_canon.yaml` → `system.notes_schema` for the authoritative\n"
            "schema. L10 lint enforces frontmatter validity on every file\n"
            "matching the filename pattern (this README is ignored).\n",
            encoding="utf-8",
        )
    print(f"  ✅ notes/ (Digestive substrate — eat/digest/view/hunger)")


def init_level_2(project_dir: Path, replacements: dict, entry_point: str):
    """Full: + lint_knowledge.py + complete setup"""
    init_level_1(project_dir, replacements, entry_point)

    # Copy lint script from package
    templates_dir = get_templates_dir()
    lint_src = templates_dir.parent / "lint.py"
    # We provide a standalone copy for projects — from the bundled lint module
    scripts_dir = project_dir / "scripts"
    scripts_dir.mkdir(exist_ok=True)

    # Generate a standalone lint script that works without myco installed
    standalone_lint = (
        "#!/usr/bin/env python3\n"
        '"""Myco Knowledge Lint — standalone version.\n'
        "Run: python scripts/lint_knowledge.py [--quick] [--fix-report]\n"
        "\n"
        "For the full CLI, install myco: pip install -e . && myco immune\n"
        '"""\n'
        "\n"
        "import subprocess, sys\n"
        "\n"
        "try:\n"
        "    from myco.immune import main\n"
        "    sys.exit(main())\n"
        "except ImportError:\n"
        '    print("myco package not installed. Install with: git clone + pip install -e .")\n'
        '    print("Or use the standalone lint from the Myco repository.")\n'
        "    sys.exit(1)\n"
    )
    (scripts_dir / "lint_knowledge.py").write_text(standalone_lint, encoding="utf-8")
    print(f"  ✅ scripts/lint_knowledge.py (30-dimension Lint shim → myco.immune)")

    # Operational narratives
    on_content = fill_template(get_template("operational_narratives.md"), replacements)
    (project_dir / "docs" / "operational_narratives.md").write_text(
        on_content, encoding="utf-8"
    )
    print(f"  ✅ docs/operational_narratives.md (Procedure knowledge)")


def run_init(args) -> int:
    """Entry point called from CLI dispatcher."""
    # Auto-detect mode: detect all tools and generate configs
    if getattr(args, "auto_detect", False):
        return run_auto_detect(args)

    if args.dir:
        project_dir = Path(args.dir)
    else:
        project_dir = Path.cwd() / args.name

    # Wave B1: --agent shortcut overrides entry_point
    agent = getattr(args, "agent", None)
    entry_point = args.entry_point.strip()
    if agent == "claude":
        entry_point = "CLAUDE.md"
    elif agent == "cursor":
        entry_point = "MYCO.md"  # Cursor uses .cursorrules, MYCO.md as fallback index
    elif agent == "gpt":
        entry_point = "GPT.md"
    if not entry_point.endswith(".md"):
        entry_point += ".md"

    project_dir.mkdir(parents=True, exist_ok=True)

    replacements = {
        "PROJECT_NAME": args.name,
        "DATE": get_date(),
        "CURRENT_PHASE": "Phase 0 — Setup",
        "PROJECT_DESCRIPTION": f"[{args.name} — describe your project goal in one sentence]",
        "PROJECT_SUMMARY": "[Describe the project's core objective and methodology in 2-3 sentences]",
        "GITHUB_USER": args.github_user,
        "ENTRY_POINT": entry_point,
    }

    level_names = {0: "Minimal", 1: "Standard", 2: "Full"}

    print(f"\n🍄 Myco — Initializing project: {args.name}")
    print(f"   Level: L{args.level} ({level_names[args.level]})")
    print(f"   Entry point: {entry_point}")
    print(f"   Location: {project_dir.resolve()}")
    print()

    if args.level == 0:
        init_level_0(project_dir, replacements, entry_point)
    elif args.level == 1:
        init_level_1(project_dir, replacements, entry_point)
    elif args.level == 2:
        init_level_2(project_dir, replacements, entry_point)

    # --- MCP SDK check + auto-install (all MCP-capable agents) ---
    def _check_mcp_sdk():
        """Check if MCP SDK is available; auto-install if missing."""
        try:
            import mcp  # noqa: F401
            return True
        except ImportError:
            print(f"\n  ⚠️  MCP SDK not installed. Auto-installing...")
            import subprocess
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "myco[mcp]"],
                capture_output=True, text=True,
            )
            if result.returncode == 0:
                print(f"  ✅ MCP SDK installed successfully")
                return True
            else:
                print(f"  ❌ Auto-install failed. Manual fix: pip install 'myco[mcp]'")
                return False

    # Wave B1: Agent-specific file generation
    if agent == "claude":
        # Generate or APPEND to CLAUDE.md (never overwrite existing content)
        if entry_point == "CLAUDE.md":
            claude_content = fill_template(get_template("CLAUDE.md"), replacements)
            claude_path = project_dir / "CLAUDE.md"
            if claude_path.exists():
                existing = claude_path.read_text(encoding="utf-8")
                if "myco" not in existing.lower() and "Myco" not in existing:
                    # Append Myco section to existing CLAUDE.md
                    merged = existing.rstrip() + "\n\n---\n\n" + claude_content
                    claude_path.write_text(merged, encoding="utf-8")
                    print(f"  ✅ CLAUDE.md (Myco section appended to existing)")
                else:
                    print(f"  ⏭️  CLAUDE.md already contains Myco config — skipped")
            else:
                claude_path.write_text(claude_content, encoding="utf-8")
                print(f"  ✅ CLAUDE.md (Agent-First entry point)")

        # Generate or MERGE .mcp.json (never overwrite existing servers)
        import json
        mcp_path = project_dir / ".mcp.json"
        myco_server = json.loads(get_template("mcp.json"))
        if mcp_path.exists():
            try:
                existing = json.loads(mcp_path.read_text(encoding="utf-8"))
                servers = existing.get("mcpServers", {})
                servers.update(myco_server.get("mcpServers", {}))
                existing["mcpServers"] = servers
                mcp_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                print(f"  ✅ .mcp.json (merged — existing servers preserved)")
            except (json.JSONDecodeError, KeyError):
                mcp_path.write_text(json.dumps(myco_server, indent=2), encoding="utf-8")
                print(f"  ✅ .mcp.json (created — old file was invalid)")
        else:
            mcp_path.write_text(json.dumps(myco_server, indent=2), encoding="utf-8")
            print(f"  ✅ .mcp.json (MCP server auto-discovery)")

        # Scheduled metabolic cycle task (skip if already exists)
        sched_dir = project_dir / ".claude" / "scheduled-tasks" / "myco-metabolic-cycle"
        sched_dir.mkdir(parents=True, exist_ok=True)
        sched_skill = sched_dir / "SKILL.md"
        if not sched_skill.exists():
            proj_str = str(project_dir.resolve()).replace("\\", "/")
            sched_skill.write_text(
                _metabolic_skill_content(proj_str),
                encoding="utf-8",
            )
        print(f"  ✅ .claude/scheduled-tasks/myco-metabolic-cycle/")
        print(_METABOLIC_TIP)

        # Cowork-compatible skill stubs (uses module-level _COWORK_SKILLS)
        for skill_name, skill_content in _COWORK_SKILLS.items():
            skill_dir = project_dir / ".claude" / "skills" / skill_name
            skill_file = skill_dir / "SKILL.md"
            if not skill_file.exists():
                skill_dir.mkdir(parents=True, exist_ok=True)
                skill_file.write_text(skill_content, encoding="utf-8")
        print(f"  ✅ .claude/skills/myco-*/  (Cowork-compatible skill stubs)")

        # Claude Code settings with hooks template (merge into existing)
        settings_dir = project_dir / ".claude"
        settings_file = settings_dir / "settings.json"
        myco_settings = {
            "permissions": {
                "allow": _MYCO_BASH_PATTERNS
            }
        }
        status = _json_merge_write(settings_file, myco_settings)
        print(f"  ✅ .claude/settings.json ({status})")

        has_mcp = _check_mcp_sdk()
        print(f"\n🍄 Done! Myco is wired for Claude Code.")
        print(f"   MCP: {'✅ ready' if has_mcp else '⚠️  install with: pip install myco[mcp]'}")
        print(f"   Editable install: the full system is yours to mutate.")
        print(f"   evolve.py can rewrite kernel code — Myco evolves with you.")
        print(f"   Run `claude` in {project_dir.resolve()} — Myco will auto-load.")

    elif agent == "cursor":
        # Generate or APPEND .cursorrules (never overwrite)
        cursorrules_content = fill_template(get_template("CURSORRULES"), replacements)
        cr_path = project_dir / ".cursorrules"
        if cr_path.exists():
            existing = cr_path.read_text(encoding="utf-8")
            if "myco" not in existing.lower():
                cr_path.write_text(existing.rstrip() + "\n\n" + cursorrules_content, encoding="utf-8")
                print(f"  ✅ .cursorrules (Myco section appended to existing)")
            else:
                print(f"  ⏭️  .cursorrules already contains Myco config — skipped")
        else:
            cr_path.write_text(cursorrules_content, encoding="utf-8")
            print(f"  ✅ .cursorrules (Cursor agent entry point)")

        # Generate or MERGE .mcp.json (same logic as Claude)
        import json
        mcp_path = project_dir / ".mcp.json"
        myco_server = json.loads(get_template("mcp.json"))
        if mcp_path.exists():
            try:
                existing = json.loads(mcp_path.read_text(encoding="utf-8"))
                servers = existing.get("mcpServers", {})
                servers.update(myco_server.get("mcpServers", {}))
                existing["mcpServers"] = servers
                mcp_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")
                print(f"  ✅ .mcp.json (merged — existing servers preserved)")
            except (json.JSONDecodeError, KeyError):
                mcp_path.write_text(json.dumps(myco_server, indent=2), encoding="utf-8")
                print(f"  ✅ .mcp.json (created)")
        else:
            mcp_path.write_text(json.dumps(myco_server, indent=2), encoding="utf-8")
            print(f"  ✅ .mcp.json (MCP server auto-discovery)")

        has_mcp = _check_mcp_sdk()
        print(f"\n🍄 Done! Myco is wired for Cursor.")
        print(f"   MCP: {'✅ ready' if has_mcp else '⚠️  install with: pip install myco[mcp]'}")
        print(f"   Editable install: the full system is yours to mutate.")
        print(f"   evolve.py can rewrite kernel code — Myco evolves with you.")
        print(f"   Open {project_dir.resolve()} in Cursor — .cursorrules loads automatically.")

    elif agent == "gpt":
        gpt_content = fill_template(get_template("GPT.md"), replacements)
        (project_dir / "GPT.md").write_text(gpt_content, encoding="utf-8")
        print(f"  ✅ GPT.md (GPT/Codex agent entry point)")
        print(f"\n🍄 Done! Myco is wired for GPT/Codex.")
        print(f"   GPT uses CLI commands (no MCP). Boot sequence:")
        print(f"   1. Load GPT.md as system prompt context")
        print(f"   2. Run: myco hunger --execute")
        print(f"   3. All Myco tools via: myco <verb> (eat, search, lint, ...)")

    else:
        print(f"\n🍄 Done! Your Myco-powered project is ready.")
        print(f"   Next steps:")
        print(f"   1. Edit {entry_point} — fill in project description and phases")
        print(f"   2. Start working — the system grows organically from practice")
        print(f"   3. Create wiki pages when you need them, not before")
        if args.level >= 1:
            print(f"   4. Run `myco immune` periodically to check consistency")

    return 0