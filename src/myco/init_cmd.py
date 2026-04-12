#!/usr/bin/env python3
"""
Myco Project Initializer — creates a new Myco-powered project scaffold.
"""

import shutil
from datetime import datetime
from pathlib import Path

from myco.templates import get_templates_dir, get_template, fill_template


def get_date():
    return datetime.now().strftime("%Y-%m-%d")


def init_level_0(project_dir: Path, replacements: dict, entry_point: str):
    """Minimal: entry_point + log.md"""
    entry_content = fill_template(get_template("MYCO.md"), replacements)
    (project_dir / entry_point).write_text(entry_content, encoding="utf-8")

    log_content = fill_template(get_template("log.md"), replacements)
    (project_dir / "log.md").write_text(log_content, encoding="utf-8")

    print(f"  ✅ {entry_point} (L1 Index)")
    print(f"  ✅ log.md (Timeline)")


def init_level_1(project_dir: Path, replacements: dict, entry_point: str):
    """Standard: + WORKFLOW.md + _canon.yaml + wiki/ + scripts/"""
    init_level_0(project_dir, replacements, entry_point)

    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "WORKFLOW.md").write_text(
        fill_template(get_template("WORKFLOW.md"), replacements), encoding="utf-8"
    )
    print(f"  ✅ docs/WORKFLOW.md (Twelve Principles)")

    (project_dir / "_canon.yaml").write_text(
        fill_template(get_template("_canon.yaml"), replacements), encoding="utf-8"
    )
    print(f"  ✅ _canon.yaml (Canonical Values SSoT)")

    (project_dir / "wiki").mkdir(exist_ok=True)
    (project_dir / "docs" / "current").mkdir(exist_ok=True)
    (project_dir / "scripts").mkdir(exist_ok=True)
    print(f"  ✅ wiki/ (Knowledge pages — create on demand)")
    print(f"  ✅ docs/primordia/ (Debate records — append-only)")
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
        "For the full CLI, install myco: pip install myco && myco lint\n"
        '"""\n'
        "\n"
        "import subprocess, sys\n"
        "\n"
        "try:\n"
        "    from myco.lint import main\n"
        "    sys.exit(main())\n"
        "except ImportError:\n"
        '    print("myco package not installed. Install with: pip install myco")\n'
        '    print("Or use the standalone lint from the Myco repository.")\n'
        "    sys.exit(1)\n"
    )
    (scripts_dir / "lint_knowledge.py").write_text(standalone_lint, encoding="utf-8")
    print(f"  ✅ scripts/lint_knowledge.py (23-dimension Lint shim → myco.lint)")

    # Operational narratives
    on_content = fill_template(get_template("operational_narratives.md"), replacements)
    (project_dir / "docs" / "operational_narratives.md").write_text(
        on_content, encoding="utf-8"
    )
    print(f"  ✅ docs/operational_narratives.md (Procedure knowledge)")


def run_init(args) -> int:
    """Entry point called from CLI dispatcher."""
    if args.dir:
        project_dir = Path(args.dir)
    else:
        project_dir = Path.cwd() / args.name

    # Wave B1: --agent shortcut overrides entry_point
    agent = getattr(args, "agent", None)
    entry_point = args.entry_point.strip()
    if agent == "claude":
        entry_point = "CLAUDE.md"
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

    # Wave B1: Agent-specific file generation
    if agent == "claude":
        # Generate CLAUDE.md from template (may override MYCO.md entry)
        if entry_point == "CLAUDE.md":
            claude_content = fill_template(get_template("CLAUDE.md"), replacements)
            (project_dir / "CLAUDE.md").write_text(claude_content, encoding="utf-8")
            print(f"  ✅ CLAUDE.md (Agent-First entry point)")

        # Generate .mcp.json
        import json
        mcp_config = json.loads(get_template("mcp.json"))
        (project_dir / ".mcp.json").write_text(
            json.dumps(mcp_config, indent=2), encoding="utf-8")
        print(f"  ✅ .mcp.json (MCP server auto-discovery)")

        print(f"\n🍄 Done! Myco is wired for Claude Code.")
        print(f"   Run `claude` in {project_dir.resolve()} — Myco is ready.")
    else:
        print(f"\n🍄 Done! Your Myco-powered project is ready.")
        print(f"   Next steps:")
        print(f"   1. Edit {entry_point} — fill in project description and phases")
        print(f"   2. Start working — the system grows organically from practice")
        print(f"   3. Create wiki pages when you need them, not before")
        if args.level >= 1:
            print(f"   4. Run `myco lint` periodically to check consistency")

    return 0
