#!/usr/bin/env python3
"""
Myco Import Command — semi-automated content import from external tools.

Semi-automated = Myco handles the mechanical work (scan, create stubs, lint),
and the agent handles the semantic work (filling in content, classification).

Supported sources:
    --from hermes [dir]      Import SKILL.md files from Hermes Agent skills directory
    --from openclaw [file]   Import MEMORY.md sections from OpenClaw memory file

Usage:
    myco import --from hermes ~/.hermes/skills/
    myco import --from hermes ~/.hermes/skills/ --all     (skip confirmation)
    myco import --from openclaw ./MEMORY.md
    myco import --from openclaw ./MEMORY.md --dry-run
"""

import re
import sys
from datetime import datetime
from pathlib import Path


def get_date():
    return datetime.now().strftime("%Y-%m-%d")


# ── Hermes Import ────────────────────────────────────────────────────────────

def scan_hermes_skills(source_dir: Path) -> list[dict]:
    """Scan a Hermes skills directory for SKILL.md files."""
    skills = []
    if not source_dir.exists():
        return skills

    for skill_dir in sorted(source_dir.iterdir()):
        if not skill_dir.is_dir():
            continue
        skill_md = skill_dir / "SKILL.md"
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8", errors="replace")
            # Extract first line as skill name if SKILL.md starts with # heading
            lines = [l.strip() for l in content.splitlines() if l.strip()]
            name = skill_dir.name
            description = lines[0].lstrip("#").strip() if lines else skill_dir.name
            size = len(content)
            skills.append({
                "name": name,
                "dir": skill_dir,
                "path": skill_md,
                "description": description,
                "size": size,
                "content": content,
            })
    return skills


def select_skills(skills: list[dict], all_flag: bool) -> list[dict]:
    """Interactive or automatic selection of skills to import."""
    if not skills:
        return []

    if all_flag:
        return skills

    print(f"\n  Found {len(skills)} skills:")
    for i, skill in enumerate(skills):
        print(f"    [{i+1}] {skill['name']} — {skill['description'][:60]} ({skill['size']} bytes)")

    print(f"\n  Which skills to import? (e.g. '1,3,5' or 'all' or 'q' to quit)")
    try:
        choice = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return []

    if choice in ("q", "quit", ""):
        return []
    if choice == "all":
        return skills

    selected = []
    for part in choice.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(skills):
                selected.append(skills[idx])
        except ValueError:
            pass
    return selected


def hermes_skill_to_wiki(skill: dict, project_dir: Path, dry_run: bool) -> dict:
    """
    Create a wiki/ stub from a Hermes SKILL.md.
    Returns info about what was created.
    """
    wiki_dir = project_dir / "wiki"
    wiki_dir.mkdir(exist_ok=True)

    slug = skill["name"].lower().replace(" ", "_").replace("-", "_")
    wiki_path = wiki_dir / f"{slug}.md"

    if wiki_path.exists():
        return {"action": "SKIP", "path": wiki_path, "reason": "already exists in wiki/"}

    # Build W8-format stub
    content_lines = [
        f"---",
        f"type: operations",
        f"date: {get_date()}",
        f"cross_references:",
        f"  - MYCO.md",
        f"---",
        f"",
        f"# {skill['name']}",
        f"",
        f"> Imported from Hermes skill: `{skill['path']}`",
        f"> Status: stub — fill in content from original SKILL.md",
        f"",
        f"## Overview",
        f"",
        f"<!-- Paste or summarize the skill's purpose here -->",
        f"",
        f"## Procedure",
        f"",
        f"<!-- Convert SKILL.md steps into Myco procedure format -->",
        f"<!-- P-NNN format: P-001: [action] -->",
        f"",
        f"## When to Use",
        f"",
        f"<!-- Describe triggers and context where this skill applies -->",
        f"",
        f"## Source",
        f"",
        f"Original SKILL.md content:",
        f"",
        f"```",
    ]
    # Include first 50 lines of original SKILL.md as reference
    original_lines = skill["content"].splitlines()[:50]
    content_lines.extend(original_lines)
    if len(skill["content"].splitlines()) > 50:
        content_lines.append(f"... ({len(skill['content'].splitlines()) - 50} more lines — see original)")
    content_lines.extend([
        f"```",
        f"",
        f"---",
        f"",
        f"← Back to MYCO.md",
    ])

    content = "\n".join(content_lines)

    if not dry_run:
        wiki_path.write_text(content, encoding="utf-8")

    return {"action": "CREATE", "path": wiki_path, "reason": f"stub from {skill['path']}"}


def run_hermes_import(source_arg: str | None, project_dir: Path, all_flag: bool, dry_run: bool) -> int:
    """Import from Hermes skills directory."""
    if source_arg:
        source_dir = Path(source_arg).expanduser().resolve()
    else:
        # Default: ~/.hermes/skills/
        source_dir = Path.home() / ".hermes" / "skills"

    print(f"\n🔍 Scanning Hermes skills: {source_dir}")

    if not source_dir.exists():
        print(f"❌ Directory not found: {source_dir}")
        print(f"   Specify your Hermes skills directory: myco import --from hermes /path/to/skills/")
        return 1

    skills = scan_hermes_skills(source_dir)
    if not skills:
        print(f"   No SKILL.md files found in {source_dir}")
        return 0

    selected = select_skills(skills, all_flag)
    if not selected:
        print("   No skills selected. Exiting.")
        return 0

    print(f"\n{'🔍 DRY RUN — ' if dry_run else ''}📥 Importing {len(selected)} skill(s)...")
    results = []
    for skill in selected:
        result = hermes_skill_to_wiki(skill, project_dir, dry_run)
        icon = "✅" if result["action"] == "CREATE" else "⏭️"
        label = "WOULD CREATE" if (dry_run and result["action"] == "CREATE") else result["action"]
        print(f"   {icon} {label}: {result['path'].relative_to(project_dir)} — {result['reason']}")
        results.append(result)

    created = sum(1 for r in results if r["action"] == "CREATE")
    skipped = sum(1 for r in results if r["action"] == "SKIP")

    if not dry_run and created > 0:
        # Append log entry
        log_path = project_dir / "log.md"
        if log_path.exists():
            log_entry = (
                f"\n## [{get_date()}] milestone | "
                f"Imported {created} Hermes skill(s) into wiki/ via myco import "
                f"(stubs created — agent to fill content)\n"
            )
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)

        print(f"\n✨ Created {created} stub(s), skipped {skipped} (already exist)")
        print(f"   Next: Fill in each wiki/ stub with actual content from the SKILL.md")
        print(f"   Then: myco lint --project-dir . to verify W8 format")
    elif dry_run:
        print(f"\n   (dry run — would create {created} stub(s), skip {skipped})")

    return 0


# ── OpenClaw Import ──────────────────────────────────────────────────────────

MEMORY_SECTIONS = {
    "Current Tasks": ("MYCO.md", "hot_zone"),
    "Key Facts": ("wiki/", "knowledge_page"),
    "Active Decisions": ("docs/primordia/", "decision_record"),
    "Team": ("wiki/", "knowledge_page"),
    "Project": ("wiki/", "knowledge_page"),
    "Goals": ("MYCO.md", "hot_zone"),
    "Architecture": ("wiki/", "knowledge_page"),
    "Warnings": ("MYCO.md", "hot_zone"),
    "Notes": ("wiki/", "knowledge_page"),
}


def parse_memory_md(memory_path: Path) -> list[dict]:
    """Parse MEMORY.md into sections."""
    content = memory_path.read_text(encoding="utf-8", errors="replace")
    sections = []

    current_section = None
    current_lines = []

    for line in content.splitlines():
        header_match = re.match(r'^#{1,3}\s+(.+)$', line)
        if header_match:
            if current_section and current_lines:
                sections.append({
                    "name": current_section,
                    "content": "\n".join(current_lines).strip(),
                    "line_count": len([l for l in current_lines if l.strip()]),
                })
            current_section = header_match.group(1).strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_section and current_lines:
        sections.append({
            "name": current_section,
            "content": "\n".join(current_lines).strip(),
            "line_count": len([l for l in current_lines if l.strip()]),
        })

    return sections


def classify_section(section: dict) -> dict:
    """Classify a MEMORY.md section to its Myco target."""
    name = section["name"]
    for pattern, (target_loc, target_type) in MEMORY_SECTIONS.items():
        if pattern.lower() in name.lower():
            return {"target_location": target_loc, "target_type": target_type}
    # Default: wiki page
    return {"target_location": "wiki/", "target_type": "knowledge_page"}


def select_sections(sections: list[dict], all_flag: bool) -> list[dict]:
    """Interactive or automatic selection of sections."""
    if not sections:
        return []
    if all_flag:
        return sections

    print(f"\n  Found {len(sections)} sections in MEMORY.md:")
    for i, sec in enumerate(sections):
        classification = classify_section(sec)
        target = classification["target_location"]
        preview = sec["content"][:60].replace("\n", " ")
        print(f"    [{i+1}] ## {sec['name']} → {target} ({sec['line_count']} lines) — {preview}...")

    print(f"\n  Which sections to import? ('all', '1,3', or 'q' to quit)")
    try:
        choice = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return []

    if choice in ("q", "quit", ""):
        return []
    if choice == "all":
        return sections

    selected = []
    for part in choice.replace(" ", "").split(","):
        try:
            idx = int(part) - 1
            if 0 <= idx < len(sections):
                selected.append(sections[idx])
        except ValueError:
            pass
    return selected


def create_section_stub(section: dict, project_dir: Path, dry_run: bool) -> dict:
    """Create a stub file from a MEMORY.md section."""
    classification = classify_section(section)
    target_loc = classification["target_location"]
    target_type = classification["target_type"]

    slug = re.sub(r'[^a-z0-9_]', '_', section["name"].lower().replace(" ", "_"))
    slug = re.sub(r'_+', '_', slug).strip('_')

    if target_loc == "MYCO.md":
        # For hot zone sections: generate an advisory note, not a file
        advisory = (
            f"   💡 '{section['name']}' section → MYCO.md hot zone\n"
            f"      Manually paste relevant lines into your MYCO.md hot zone section.\n"
            f"      Content preview: {section['content'][:100]}..."
        )
        return {"action": "ADVISORY", "path": None, "advisory": advisory}

    elif target_loc == "wiki/":
        wiki_dir = project_dir / "wiki"
        wiki_dir.mkdir(exist_ok=True)
        stub_path = wiki_dir / f"{slug}.md"

        if stub_path.exists():
            return {"action": "SKIP", "path": stub_path, "reason": "already exists"}

        content = "\n".join([
            f"---",
            f"type: concept",
            f"date: {get_date()}",
            f"cross_references:",
            f"  - MYCO.md",
            f"---",
            f"",
            f"# {section['name']}",
            f"",
            f"> Imported from OpenClaw MEMORY.md section `## {section['name']}`",
            f"> Status: stub — review and refine content",
            f"",
            section["content"],
            f"",
            f"---",
            f"",
            f"← Back to MYCO.md",
        ])

        if not dry_run:
            stub_path.write_text(content, encoding="utf-8")
        return {"action": "CREATE", "path": stub_path, "reason": f"wiki page from '{section['name']}'"}

    elif target_loc == "docs/primordia/":
        docs_dir = project_dir / "docs" / "current"
        docs_dir.mkdir(parents=True, exist_ok=True)
        stub_path = docs_dir / f"openclaw_{slug}_{get_date()}.md"

        if stub_path.exists():
            return {"action": "SKIP", "path": stub_path, "reason": "already exists"}

        content = "\n".join([
            f"# {section['name']} (from OpenClaw)",
            f"> Date: {get_date()} | Source: OpenClaw MEMORY.md | Status: [ACTIVE]",
            f"",
            section["content"],
            f"",
            f"---",
            f"",
            f"← [Back to MYCO.md](../../MYCO.md)",
        ])

        if not dry_run:
            stub_path.write_text(content, encoding="utf-8")
        return {"action": "CREATE", "path": stub_path, "reason": f"decision record from '{section['name']}'"}

    return {"action": "SKIP", "path": None, "reason": "unclassified"}


def run_openclaw_import(source_arg: str | None, project_dir: Path, all_flag: bool, dry_run: bool) -> int:
    """Import from OpenClaw MEMORY.md file."""
    if source_arg:
        memory_path = Path(source_arg).expanduser().resolve()
    else:
        memory_path = project_dir / "MEMORY.md"

    print(f"\n🔍 Scanning OpenClaw memory: {memory_path}")

    if not memory_path.exists():
        print(f"❌ File not found: {memory_path}")
        print(f"   Specify your MEMORY.md path: myco import --from openclaw /path/to/MEMORY.md")
        return 1

    sections = parse_memory_md(memory_path)
    if not sections:
        print(f"   No sections found in {memory_path}")
        return 0

    selected = select_sections(sections, all_flag)
    if not selected:
        print("   No sections selected. Exiting.")
        return 0

    print(f"\n{'🔍 DRY RUN — ' if dry_run else ''}📥 Importing {len(selected)} section(s)...")
    results = []
    for section in selected:
        result = create_section_stub(section, project_dir, dry_run)
        if result["action"] == "ADVISORY":
            print(f"\n{result['advisory']}")
        else:
            icon = "✅" if result["action"] == "CREATE" else "⏭️"
            label = "WOULD CREATE" if (dry_run and result["action"] == "CREATE") else result["action"]
            rel_path = result["path"].relative_to(project_dir) if result["path"] else "N/A"
            print(f"   {icon} {label}: {rel_path} — {result['reason']}")
        results.append(result)

    created = sum(1 for r in results if r["action"] == "CREATE")
    skipped = sum(1 for r in results if r["action"] == "SKIP")

    if not dry_run and created > 0:
        log_path = project_dir / "log.md"
        if log_path.exists():
            log_entry = (
                f"\n## [{get_date()}] milestone | "
                f"Imported {created} OpenClaw section(s) from MEMORY.md via myco import "
                f"(stubs created — review and refine)\n"
            )
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(log_entry)

        print(f"\n✨ Created {created} stub(s), skipped {skipped} (already exist)")
        print(f"   Next: Review each stub, remove the 'imported from' header if no longer needed")
        print(f"   Then: myco lint --project-dir . to verify format")
        print(f"   Note: Do NOT import all of MEMORY.md as-is — each section should be reviewed")
    elif dry_run:
        print(f"\n   (dry run — would create {created} stub(s), skip {skipped})")

    return 0


# ── Entry Point ──────────────────────────────────────────────────────────────

def run_import(args) -> int:
    """Entry point called from CLI dispatcher."""
    project_dir = Path(args.project_dir).resolve()

    if not project_dir.exists():
        print(f"❌ Project directory not found: {project_dir}")
        return 1

    source = args.from_tool.lower()
    source_path = args.source  # Optional path argument

    if source == "hermes":
        return run_hermes_import(source_path, project_dir, args.all, args.dry_run)
    elif source == "openclaw":
        return run_openclaw_import(source_path, project_dir, args.all, args.dry_run)
    else:
        print(f"❌ Unknown source: '{source}'")
        print(f"   Supported: hermes, openclaw")
        print(f"   Example: myco import --from hermes ~/.hermes/skills/")
        return 1
