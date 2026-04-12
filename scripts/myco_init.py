#!/usr/bin/env python3
"""
Myco Project Initializer
========================
Initialize a new project with the Myco knowledge system.

Usage:
    python myco_init.py <project-name>                           # Level 1 (default)
    python myco_init.py <project-name> --level 0                 # Minimal
    python myco_init.py <project-name> --level 2                 # Full
    python myco_init.py <project-name> --entry-point CLAUDE.md   # Use CLAUDE.md instead of MYCO.md
    python myco_init.py <project-name> --dir /path/to/dir        # Custom location

Bootstrap Levels:
    L0 (5 min):   MYCO.md (minimal) + log.md
    L1 (30 min):  + WORKFLOW.md + _canon.yaml + wiki/ + scripts/
    L2 (2 hours): + lint_knowledge.py + full WORKFLOW + evolution engine active

Entry Point:
    Default: MYCO.md (Myco naming)
    Alternative: CLAUDE.md (Claude agent compatibility)
    Custom: Any filename via --entry-point flag
"""

import os
import sys
import shutil
import argparse
from datetime import datetime
from pathlib import Path

# Resolve paths
SCRIPT_DIR = Path(__file__).resolve().parent
MYCO_ROOT = SCRIPT_DIR.parent
TEMPLATES_DIR = MYCO_ROOT / "templates"
SCRIPTS_DIR = MYCO_ROOT / "scripts"


def get_date():
    return datetime.now().strftime("%Y-%m-%d")


def fill_template(content: str, replacements: dict) -> str:
    """Replace {{PLACEHOLDER}} tokens with actual values."""
    for key, value in replacements.items():
        content = content.replace(f"{{{{{key}}}}}", value)
    return content


def init_level_0(project_dir: Path, replacements: dict, entry_point: str):
    """Minimal: entry_point + log.md"""
    # Load template from MYCO.md
    template_path = TEMPLATES_DIR / "MYCO.md"
    template_content = template_path.read_text(encoding="utf-8")
    entry_content = fill_template(template_content, replacements)
    (project_dir / entry_point).write_text(entry_content, encoding="utf-8")

    # log.md
    log_template = (TEMPLATES_DIR / "log.md").read_text(encoding="utf-8")
    log_content = fill_template(log_template, replacements)
    (project_dir / "log.md").write_text(log_content, encoding="utf-8")

    print(f"  ✅ {entry_point} (L1 Index)")
    print(f"  ✅ log.md (Timeline)")


def init_level_1(project_dir: Path, replacements: dict, entry_point: str):
    """Standard: + WORKFLOW.md + _canon.yaml + wiki/ + scripts/"""
    init_level_0(project_dir, replacements, entry_point)

    # WORKFLOW.md
    wf_template = (TEMPLATES_DIR / "WORKFLOW.md").read_text(encoding="utf-8")
    docs_dir = project_dir / "docs"
    docs_dir.mkdir(exist_ok=True)
    (docs_dir / "WORKFLOW.md").write_text(
        fill_template(wf_template, replacements), encoding="utf-8"
    )
    print(f"  ✅ docs/WORKFLOW.md (Twelve Principles)")

    # _canon.yaml
    canon_template = (TEMPLATES_DIR / "_canon.yaml").read_text(encoding="utf-8")
    (project_dir / "_canon.yaml").write_text(
        fill_template(canon_template, replacements), encoding="utf-8"
    )
    print(f"  ✅ _canon.yaml (Canonical Values SSoT)")

    # Empty directories
    (project_dir / "wiki").mkdir(exist_ok=True)
    (project_dir / "docs" / "current").mkdir(exist_ok=True)
    (project_dir / "scripts").mkdir(exist_ok=True)
    print(f"  ✅ wiki/ (Knowledge pages — create on demand)")
    print(f"  ✅ docs/primordia/ (Debate records — append-only)")
    print(f"  ✅ scripts/ (Tool scripts)")


def init_level_2(project_dir: Path, replacements: dict, entry_point: str):
    """Full: + lint_knowledge.py + complete setup"""
    init_level_1(project_dir, replacements, entry_point)

    # lint_knowledge.py
    lint_src = SCRIPTS_DIR / "lint_knowledge.py"
    if lint_src.exists():
        shutil.copy2(lint_src, project_dir / "scripts" / "lint_knowledge.py")
        print(f"  ✅ scripts/lint_knowledge.py (19-dimension Lint shim → myco.lint)")
    else:
        print(f"  ⚠️  lint_knowledge.py not found in Myco scripts/")

    # compress_original.py (v2.5 tool)
    compress_src = SCRIPTS_DIR / "compress_original.py"
    if compress_src.exists():
        shutil.copy2(compress_src, project_dir / "scripts" / "compress_original.py")
        print(f"  ✅ scripts/compress_original.py (v2.5 compression)")

    # Create operational_narratives.md from template
    on_template = (TEMPLATES_DIR / "operational_narratives.md").read_text(encoding="utf-8")
    on_content = fill_template(on_template, replacements)
    (project_dir / "docs" / "operational_narratives.md").write_text(
        on_content, encoding="utf-8"
    )
    print(f"  ✅ docs/operational_narratives.md (Procedure knowledge)")


def main():
    parser = argparse.ArgumentParser(
        description="Initialize a new Myco-powered project"
    )
    parser.add_argument("name", help="Project name")
    parser.add_argument(
        "--level", type=int, default=1, choices=[0, 1, 2],
        help="Bootstrap level: 0=minimal, 1=standard (default), 2=full"
    )
    parser.add_argument(
        "--dir", type=str, default=None,
        help="Target directory (default: ./<name>)"
    )
    parser.add_argument(
        "--entry-point", type=str, default="MYCO.md",
        help="Entry point filename (default: MYCO.md, alternative: CLAUDE.md)"
    )
    parser.add_argument(
        "--github-user", type=str, default="your-username",
        help="GitHub username for Myco link in entry point document"
    )
    args = parser.parse_args()

    # Determine project directory
    if args.dir:
        project_dir = Path(args.dir)
    else:
        project_dir = Path.cwd() / args.name

    # Check templates exist
    if not TEMPLATES_DIR.exists():
        print(f"❌ Templates directory not found: {TEMPLATES_DIR}")
        print(f"   Make sure myco_init.py is inside the Myco repository's scripts/ folder.")
        sys.exit(1)

    # Create project directory
    project_dir.mkdir(parents=True, exist_ok=True)

    # Validate entry point
    entry_point = args.entry_point.strip()
    if not entry_point.endswith(".md"):
        entry_point = entry_point + ".md"

    # Template replacements
    replacements = {
        "PROJECT_NAME": args.name,
        "DATE": get_date(),
        "CURRENT_PHASE": "Phase 0 — Setup",
        "PROJECT_DESCRIPTION": f"[{args.name} — 一句话描述项目目标]",
        "PROJECT_SUMMARY": "[2-3 句话描述项目的核心目标和方法]",
        "GITHUB_USER": args.github_user,
        "ENTRY_POINT": entry_point,
    }

    # Level descriptions
    level_names = {0: "Minimal", 1: "Standard", 2: "Full"}

    print(f"\n🍄 Myco — Initializing project: {args.name}")
    print(f"   Level: L{args.level} ({level_names[args.level]})")
    print(f"   Entry point: {entry_point}")
    print(f"   Location: {project_dir.resolve()}")
    print()

    # Execute initialization
    if args.level == 0:
        init_level_0(project_dir, replacements, entry_point)
    elif args.level == 1:
        init_level_1(project_dir, replacements, entry_point)
    elif args.level == 2:
        init_level_2(project_dir, replacements, entry_point)

    print(f"\n🍄 Done! Your Myco-powered project is ready.")
    print(f"   Next steps:")
    print(f"   1. Edit {entry_point} — fill in project description and phases")
    print(f"   2. Start working — the system grows organically from practice")
    print(f"   3. Create wiki pages when you need them, not before")
    if args.level >= 1:
        print(f"   4. Run `python scripts/lint_knowledge.py` periodically")


if __name__ == "__main__":
    main()
