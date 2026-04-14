#!/usr/bin/env python3
"""
Myco Migration Tool (Hot-Start) — migrate an existing project to Myco.

Non-destructive: never deletes or overwrites existing files.
Scans for recognized knowledge patterns (CLAUDE.md, MEMORY.md, skills/, etc.)
and maps them to Myco's four-layer architecture.
"""

from pathlib import Path

from myco.templates import get_template, fill_template
from myco.util import get_date


# ─── Pattern Detection ──────────────────────────────────────────────

KNOWN_PATTERNS = {
    "CLAUDE.md":   {"layer": "L1", "type": "entry_point", "desc": "Claude Code knowledge entry"},
    "AGENTS.md":   {"layer": "L1", "type": "entry_point", "desc": "Hermes Agent instructions"},
    "MYCO.md":     {"layer": "L1", "type": "entry_point", "desc": "Myco entry (already migrated?)"},
    "CURSOR.md":   {"layer": "L1", "type": "entry_point", "desc": "Cursor IDE instructions"},
    "MEMORY.md":   {"layer": "L1.5", "type": "memory", "desc": "Persistent memory file (Hermes/OpenClaw)"},
    "USER.md":     {"layer": "L1.5", "type": "memory", "desc": "User profile/preferences"},
    "SOUL.md":     {"layer": "L1.5", "type": "memory", "desc": "Agent identity/personality"},
    "IDENTITY.md": {"layer": "L1.5", "type": "memory", "desc": "Agent identity file"},
    "SKILL.md":    {"layer": "L2", "type": "skill", "desc": "Nuwa-style skill definition"},
    "_canon.yaml": {"layer": "infra", "type": "myco", "desc": "Myco canonical values (already present)"},
    "log.md":      {"layer": "infra", "type": "myco", "desc": "Myco timeline (already present)"},
}

KNOWN_DIRS = {
    "wiki":    {"layer": "L1.5", "desc": "Knowledge wiki pages"},
    "docs":    {"layer": "L2",   "desc": "Documentation/debate records"},
    "skills":  {"layer": "L2",   "desc": "Skill definitions directory"},
    ".hermes": {"layer": "agent", "desc": "Hermes Agent config (agent-specific, not migrated)"},
    ".cursor": {"layer": "agent", "desc": "Cursor IDE config (agent-specific, not migrated)"},
    "scripts": {"layer": "infra", "desc": "Tool scripts"},
    "memory":  {"layer": "L1.5", "desc": "Memory directory (MemPalace/other)"},
}


def scan_project(project_dir: Path) -> dict:
    """Scan project directory for recognized knowledge patterns."""
    findings = {
        "entry_points": [],
        "memory_files": [],
        "skill_files": [],
        "myco_components": [],
        "known_dirs": [],
        "agent_configs": [],
        "unknown_md_files": [],
    }

    for item in project_dir.iterdir():
        if item.is_file() and item.name in KNOWN_PATTERNS:
            pattern = KNOWN_PATTERNS[item.name]
            entry = {"name": item.name, "path": item, **pattern}
            if pattern["type"] == "entry_point":
                findings["entry_points"].append(entry)
            elif pattern["type"] == "memory":
                findings["memory_files"].append(entry)
            elif pattern["type"] == "skill":
                findings["skill_files"].append(entry)
            elif pattern["type"] == "myco":
                findings["myco_components"].append(entry)
        elif item.is_file() and item.suffix == ".md" and item.name not in KNOWN_PATTERNS:
            findings["unknown_md_files"].append(item.name)

    for item in project_dir.iterdir():
        if item.is_dir() and item.name in KNOWN_DIRS:
            dir_info = KNOWN_DIRS[item.name]
            count = sum(1 for f in item.rglob("*") if f.is_file())
            entry = {"name": item.name, "path": item, "file_count": count, **dir_info}
            if dir_info["layer"] == "agent":
                findings["agent_configs"].append(entry)
            else:
                findings["known_dirs"].append(entry)

    for skills_dir in project_dir.rglob("skills"):
        if skills_dir.is_dir() and skills_dir.parent == project_dir:
            continue
        skill_mds = list(skills_dir.glob("*/SKILL.md"))
        for sm in skill_mds:
            findings["skill_files"].append({
                "name": sm.parent.name,
                "path": sm,
                "layer": "L2",
                "type": "skill",
                "desc": f"Skill: {sm.parent.name}",
            })

    return findings


# ─── Migration Actions ──────────────────────────────────────────────

def create_myco_scaffold(project_dir: Path, replacements: dict, entry_point: str,
                         level: int, findings: dict, dry_run: bool) -> list:
    """Create missing Myco components without touching existing files."""
    actions = []

    # 1. Entry point
    existing_entries = [e["name"] for e in findings["entry_points"]]
    if entry_point in existing_entries:
        actions.append(("SKIP", f"{entry_point} already exists — keeping as L1 entry"))
    elif "MYCO.md" in existing_entries or "CLAUDE.md" in existing_entries:
        existing = "MYCO.md" if "MYCO.md" in existing_entries else "CLAUDE.md"
        actions.append(("SKIP", f"Found {existing} — using as L1 entry (rename to {entry_point} if desired)"))
        entry_point = existing
    else:
        actions.append(("CREATE", f"{entry_point} (L1 Index from template)"))
        if not dry_run:
            content = fill_template(get_template("MYCO.md"), replacements)
            (project_dir / entry_point).write_text(content, encoding="utf-8")

    # 2. log.md
    if (project_dir / "log.md").exists():
        actions.append(("SKIP", "log.md already exists"))
    else:
        actions.append(("CREATE", "log.md (timeline)"))
        if not dry_run:
            content = fill_template(get_template("log.md"), replacements)
            (project_dir / "log.md").write_text(content, encoding="utf-8")

    if level >= 1:
        # 3. _canon.yaml
        if (project_dir / "_canon.yaml").exists():
            actions.append(("SKIP", "_canon.yaml already exists"))
        else:
            actions.append(("CREATE", "_canon.yaml (Canonical Values SSoT)"))
            if not dry_run:
                content = fill_template(get_template("_canon.yaml"), replacements)
                (project_dir / "_canon.yaml").write_text(content, encoding="utf-8")

        # 4. WORKFLOW.md
        docs_dir = project_dir / "docs"
        docs_dir.mkdir(exist_ok=True)
        if (docs_dir / "WORKFLOW.md").exists():
            actions.append(("SKIP", "docs/WORKFLOW.md already exists"))
        else:
            actions.append(("CREATE", "docs/WORKFLOW.md (Thirteen Principles)"))
            if not dry_run:
                content = fill_template(get_template("WORKFLOW.md"), replacements)
                (docs_dir / "WORKFLOW.md").write_text(content, encoding="utf-8")

        # 5. Directories
        for d in ["wiki", "docs/primordia", "scripts"]:
            full = project_dir / d
            if full.exists():
                actions.append(("SKIP", f"{d}/ already exists"))
            else:
                actions.append(("CREATE", f"{d}/ (directory)"))
                if not dry_run:
                    full.mkdir(parents=True, exist_ok=True)

    if level >= 2:
        # 6. Standalone lint script
        lint_dst = project_dir / "scripts" / "lint_knowledge.py"
        if lint_dst.exists():
            actions.append(("SKIP", "scripts/lint_knowledge.py already exists"))
        else:
            actions.append(("CREATE", "scripts/lint_knowledge.py (30-dimension Lint shim → myco.immune)"))
            if not dry_run:
                (project_dir / "scripts").mkdir(exist_ok=True)
                standalone_lint = (
                    "#!/usr/bin/env python3\n"
                    '"""Myco Knowledge Lint — standalone version.\n'
                    "Run: python scripts/lint_knowledge.py [--quick]\n"
                    "Or:  myco immune [--quick]\n"
                    '"""\n\n'
                    "import sys\n\n"
                    "try:\n"
                    "    from myco.immune import main\n"
                    "    sys.exit(main())\n"
                    "except ImportError:\n"
                    '    print("myco package not installed. Install with: pip install myco")\n'
                    "    sys.exit(1)\n"
                )
                lint_dst.write_text(standalone_lint, encoding="utf-8")

    return actions


def generate_migration_notes(findings: dict) -> list:
    """Generate advisory notes based on detected patterns."""
    notes = []

    for mf in findings["memory_files"]:
        notes.append(
            f"📝 Found `{mf['name']}` ({mf['desc']}). "
            f"Consider creating a wiki/ page from its contents — "
            f"Myco's L1.5 wiki layer provides lint-checked, evolution-enabled knowledge storage."
        )

    for sf in findings["skill_files"]:
        notes.append(
            f"🔧 Found skill `{sf['name']}` ({sf['desc']}). "
            f"Consider importing into docs/ or wiki/ — "
            f"Myco's evolution engine will lint-check and version-track these."
        )

    for ac in findings["agent_configs"]:
        notes.append(
            f"🤖 Found `{ac['name']}/` ({ac['desc']}, {ac['file_count']} files). "
            f"This is agent-specific config — Myco won't modify it. "
            f"The two systems coexist naturally."
        )

    for kd in findings["known_dirs"]:
        if kd["name"] == "wiki" and kd["file_count"] > 0:
            notes.append(
                f"📚 Found existing wiki/ with {kd['file_count']} files. "
                f"Run `myco immune` to check consistency with _canon.yaml."
            )
        if kd["name"] == "docs" and kd["file_count"] > 0:
            notes.append(
                f"📄 Found existing docs/ with {kd['file_count']} files. "
                f"Myco will treat these as L2 documentation. "
                f"Consider adding lifecycle labels ([ACTIVE]/[COMPILED]/[SUPERSEDED])."
            )

    if findings["unknown_md_files"]:
        names = ", ".join(findings["unknown_md_files"][:5])
        extra = f" (+{len(findings['unknown_md_files'])-5} more)" if len(findings["unknown_md_files"]) > 5 else ""
        notes.append(
            f"📋 Found unrecognized .md files at project root: {names}{extra}. "
            f"Consider organizing into wiki/ (compiled knowledge) or docs/primordia/ (debate records)."
        )

    return notes


def write_migration_report(project_dir: Path, findings: dict, actions: list,
                           notes: list, entry_point: str, level: int):
    """Write a migration report summarizing what was done."""
    lines = [
        f"# Myco Migration Report",
        f"",
        f"> Generated: {get_date()}",
        f"> Project: {project_dir.resolve()}",
        f"> Level: L{level} | Entry point: {entry_point}",
        f"",
        f"---",
        f"",
        f"## Detected Knowledge Patterns",
        f"",
    ]

    if findings["entry_points"]:
        lines.append("**Entry Points Found:**")
        for ep in findings["entry_points"]:
            lines.append(f"- `{ep['name']}` — {ep['desc']}")
        lines.append("")

    if findings["memory_files"]:
        lines.append("**Memory Files Found:**")
        for mf in findings["memory_files"]:
            lines.append(f"- `{mf['name']}` — {mf['desc']}")
        lines.append("")

    if findings["skill_files"]:
        lines.append("**Skill Files Found:**")
        for sf in findings["skill_files"]:
            lines.append(f"- `{sf['name']}` — {sf['desc']}")
        lines.append("")

    if findings["known_dirs"]:
        lines.append("**Known Directories:**")
        for kd in findings["known_dirs"]:
            lines.append(f"- `{kd['name']}/` — {kd['desc']} ({kd['file_count']} files)")
        lines.append("")

    if findings["agent_configs"]:
        lines.append("**Agent-Specific Configs (untouched):**")
        for ac in findings["agent_configs"]:
            lines.append(f"- `{ac['name']}/` — {ac['desc']} ({ac['file_count']} files)")
        lines.append("")

    lines.extend(["## Actions Taken", ""])
    for action_type, desc in actions:
        icon = "✅" if action_type == "CREATE" else "⏭️"
        lines.append(f"- {icon} **{action_type}**: {desc}")
    lines.append("")

    if notes:
        lines.extend(["## Recommendations", ""])
        for note in notes:
            lines.append(f"- {note}")
        lines.append("")

    lines.extend([
        "## Next Steps",
        "",
        f"1. Review and customize `{entry_point}` — fill in project description, current phase, and hot zone",
        "2. If you have existing MEMORY.md or skill files, consider importing their content into wiki/ pages",
        "3. Establish your lint baseline now:",
        "   ```bash",
        "   myco immune --project-dir .",
        "   ```",
        "   On a fresh migration this will show **zero issues** — that's expected. The scaffold is internally consistent.",
        "   Start working. The first time lint finds something after you've added content is your **aha moment** — that's Myco working for you.",
        "4. Start working — Myco grows organically from practice. hunger signals (friction sensing) activates automatically.",
        "",
        "---",
        "",
        "*Migration is non-destructive. No existing files were modified or deleted.*",
    ])

    report_path = project_dir / "migration_report.md"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    return report_path


def run_migrate(args) -> int:
    """Entry point called from CLI dispatcher."""
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return 1

    if not project_dir.is_dir():
        print(f"❌ Not a directory: {project_dir}")
        return 1

    entry_point = args.entry_point.strip()
    if not entry_point.endswith(".md"):
        entry_point += ".md"

    replacements = {
        "PROJECT_NAME": project_dir.name,
        "DATE": get_date(),
        "CURRENT_PHASE": "Phase N — [migrated from existing project]",
        "PROJECT_DESCRIPTION": f"[{project_dir.name} — fill in project goal]",
        "PROJECT_SUMMARY": "[Describe the project's core objective and methodology]",
        "GITHUB_USER": "your-username",
        "ENTRY_POINT": entry_point,
    }

    dry_run = args.dry_run
    mode_label = "DRY RUN" if dry_run else "MIGRATING"
    print(f"\n🍄 Myco — {mode_label}: {project_dir.name}")
    print(f"   Level: L{args.level}")
    print(f"   Entry point: {entry_point}")
    print(f"   Location: {project_dir}")
    print()

    # Phase 1: Scan
    print("🔍 Scanning project for existing knowledge patterns...")
    findings = scan_project(project_dir)

    entry_count = len(findings["entry_points"])
    mem_count = len(findings["memory_files"])
    skill_count = len(findings["skill_files"])
    myco_count = len(findings["myco_components"])
    dir_count = len(findings["known_dirs"])
    agent_count = len(findings["agent_configs"])

    print(f"   Found: {entry_count} entry points, {mem_count} memory files, "
          f"{skill_count} skills, {dir_count} knowledge dirs, {agent_count} agent configs")
    if myco_count > 0:
        names = ", ".join(c["name"] for c in findings["myco_components"])
        print(f"   ⚠️  Existing Myco components detected: {names}")
    print()

    # Phase 2: Create scaffold
    print("🏗️  Creating Myco scaffold (non-destructive)...")
    actions = create_myco_scaffold(
        project_dir, replacements, entry_point, args.level, findings, dry_run
    )
    for action_type, desc in actions:
        icon = "✅" if action_type == "CREATE" else "⏭️"
        label = action_type
        if dry_run and action_type == "CREATE":
            label = "WOULD CREATE"
        print(f"  {icon} {label}: {desc}")
    print()

    # Phase 3: Generate recommendations
    notes = generate_migration_notes(findings)

    # Phase 4: Write report
    if not dry_run:
        report_path = write_migration_report(
            project_dir, findings, actions, notes, entry_point, args.level
        )
        print(f"📋 Migration report: {report_path}")
    else:
        print("📋 Migration report: [skipped in dry-run mode]")

    if notes:
        print(f"\n💡 Recommendations ({len(notes)}):")
        for note in notes:
            print(f"   {note}")

    created = sum(1 for a, _ in actions if a == "CREATE")
    skipped = sum(1 for a, _ in actions if a == "SKIP")
    print(f"\n🍄 {'Would create' if dry_run else 'Created'} {created} files/dirs, skipped {skipped} (already exist)")
    if not dry_run:
        print(f"   ✨ Your project is now Myco-powered!")
        print(f"   Next: Edit {entry_point} → fill in project description → start working")
        print()
        print(f"   🔍 Establish your lint baseline:")
        print(f"      myco immune --project-dir {project_dir}")
        print(f"   A clean scaffold shows zero issues. The first inconsistency lint catches")
        print(f"   after you start working is your aha moment — that's Myco working for you.")

    return 0
