#!/usr/bin/env python3
"""
Myco MCP Server — Exposes Myco's knowledge metabolism tools via Model Context Protocol.

When configured in .mcp.json, AI agents (Claude Code, Cursor, etc.) automatically
discover these tools and call them at the right moments — no manual prompting needed.

Tools:
    myco_lint       — Run 9-dimensional consistency checks
    myco_status     — Quick overview of knowledge system health
    myco_search     — Search across wiki/docs/MYCO.md knowledge base
    myco_log        — Append friction/reflection entries to log.md
    myco_reflect    — Trigger Gear 2 session-end reflection prompts

Transport: stdio (local subprocess of the AI client)
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any

try:
    import yaml
except ImportError:
    yaml = None

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print(
        "Error: MCP SDK not installed. Run: pip install 'myco[mcp]'",
        file=sys.stderr,
    )
    sys.exit(1)

# ---------------------------------------------------------------------------
# Server Initialization
# ---------------------------------------------------------------------------

mcp = FastMCP("myco_mcp")

# ---------------------------------------------------------------------------
# Project Discovery
# ---------------------------------------------------------------------------

def _find_project_root() -> Path:
    """Walk up from cwd to find a directory containing _canon.yaml."""
    current = Path.cwd()
    for parent in [current] + list(current.parents):
        if (parent / "_canon.yaml").exists():
            return parent
    return current


def _load_canon(root: Path) -> dict:
    """Load _canon.yaml from project root."""
    if yaml is None:
        return {"error": "PyYAML not installed"}
    canon_path = root / "_canon.yaml"
    if not canon_path.exists():
        return {"error": f"_canon.yaml not found at {root}"}
    with open(canon_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _read_file(path: Path) -> Optional[str]:
    """Read a file, returning None on error."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Tool: myco_lint
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_lint",
    annotations={
        "title": "Myco Lint — 9-Dimension Consistency Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def myco_lint(
    project_dir: Optional[str] = None,
    quick: bool = False,
) -> str:
    """Run Myco's 9-dimensional lint checks on the knowledge system.

    Call this after modifying wiki pages, docs, MYCO.md, or _canon.yaml to catch
    contradictions, orphan files, stale references, and version drift. This is the
    immune system of the knowledge substrate.

    Checks: L0 Canon schema, L1 Reference integrity, L2 Number consistency,
    L3 Stale patterns, L4 Orphan detection, L5 Log coverage, L6 Date consistency,
    L7 Wiki format, L8 .original sync.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.
        quick: If True, only run L0-L3 (fast checks). Default: False.

    Returns:
        Structured lint report with pass/fail per dimension and issue details.
    """
    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    canon = _load_canon(root)
    if "error" in canon:
        return json.dumps({"error": canon["error"]}, indent=2)

    # Import lint functions from the existing module
    from myco.lint import (
        lint_canon_schema, lint_references, lint_numbers,
        lint_stale_patterns, lint_orphans, lint_log,
        lint_dates, lint_wiki_format, lint_original_sync,
    )

    checks = [
        ("L0 Canon Self-Check", lint_canon_schema),
        ("L1 Reference Integrity", lint_references),
        ("L2 Number Consistency", lint_numbers),
        ("L3 Stale Pattern Scan", lint_stale_patterns),
    ]
    if not quick:
        checks.extend([
            ("L4 Orphan Detection", lint_orphans),
            ("L5 Log Coverage", lint_log),
            ("L6 Date Consistency", lint_dates),
            ("L7 Wiki Format", lint_wiki_format),
            ("L8 .original Sync", lint_original_sync),
        ])

    results = []
    total_issues = 0
    for name, checker in checks:
        issues = checker(canon, root)
        total_issues += len(issues)
        results.append({
            "check": name,
            "status": "FAIL" if issues else "PASS",
            "issues": [
                {"level": i[0], "severity": i[1], "file": i[2], "message": i[3]}
                for i in issues
            ],
        })

    report = {
        "project": str(root),
        "timestamp": datetime.now().isoformat(),
        "mode": "quick (L0-L3)" if quick else "full (L0-L8)",
        "total_issues": total_issues,
        "all_passed": total_issues == 0,
        "checks": results,
    }

    if total_issues == 0:
        report["summary"] = "✅ ALL CHECKS PASSED — knowledge system is healthy."
    else:
        report["summary"] = (
            f"⚠ {total_issues} issue(s) found. "
            "Review the issues list and fix inconsistencies."
        )

    return json.dumps(report, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_status
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_status",
    annotations={
        "title": "Myco Status — Knowledge System Overview",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def myco_status(
    project_dir: Optional[str] = None,
) -> str:
    """Get a quick overview of the Myco knowledge system state.

    Call this at the start of a session to understand the project's current
    knowledge health: how many files, wiki pages, recent log entries, pending
    tasks, and lint status. Helps the agent orient quickly.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON overview of knowledge system state.
    """
    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    canon = _load_canon(root)
    if "error" in canon:
        return json.dumps({"error": canon["error"]}, indent=2)

    # Count wiki pages
    wiki_dir = root / "wiki"
    wiki_count = len(list(wiki_dir.glob("*.md"))) if wiki_dir.exists() else 0

    # Count docs
    docs_dir = root / "docs"
    docs_count = len(list(docs_dir.rglob("*.md"))) if docs_dir.exists() else 0

    # Read log.md last 5 entries
    log_path = root / "log.md"
    recent_log = []
    if log_path.exists():
        log_content = _read_file(log_path)
        if log_content:
            entries = re.findall(r"^## \[.*?\].*$", log_content, re.MULTILINE)
            recent_log = entries[-5:] if entries else []

    # Read task queue from MYCO.md
    entry_point = canon.get("system", {}).get("entry_point", "MYCO.md")
    myco_path = root / entry_point
    tasks = []
    if myco_path.exists():
        myco_content = _read_file(myco_path)
        if myco_content:
            # Extract task table rows
            task_matches = re.findall(
                r"\|\s*\d+\s*\|\s*([^\|]+)\|\s*([^\|]+)\|", myco_content
            )
            tasks = [
                {"status": s.strip(), "task": t.strip()}
                for s, t in task_matches[:10]
            ]

    # Adapter status
    adapters_dir = root / "adapters"
    adapter_count = (
        len([f for f in adapters_dir.glob("*.yaml") if f.name != "README.md"])
        if adapters_dir.exists()
        else 0
    )

    status = {
        "project": canon.get("project", {}).get("name", "Unknown"),
        "version": canon.get("package", {}).get("version", "?"),
        "phase": canon.get("project", {}).get("current_phase", "?"),
        "knowledge": {
            "wiki_pages": wiki_count,
            "docs_files": docs_count,
            "adapters": adapter_count,
            "principles_count": canon.get("system", {}).get("principles_count", "?"),
            "evolution_gears": canon.get("system", {}).get("evolution_gears", "?"),
        },
        "recent_log_entries": recent_log,
        "task_queue": tasks,
        "hint": (
            "Run myco_lint to check for inconsistencies. "
            "Use myco_search to find specific knowledge. "
            "Use myco_log to record friction or reflections."
        ),
    }

    return json.dumps(status, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_search
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_search",
    annotations={
        "title": "Myco Search — Knowledge Base Lookup",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def myco_search(
    query: str,
    project_dir: Optional[str] = None,
    scope: str = "all",
) -> str:
    """Search across the Myco knowledge base for relevant content.

    Searches MYCO.md, wiki pages, docs, log.md, and operational narratives
    for the given query string. Use this when you need specific knowledge
    from the project's persistent memory instead of guessing.

    Args:
        query: Search string (case-insensitive). Matches against file content.
        project_dir: Path to Myco project root. Auto-detected if omitted.
        scope: Where to search. Options: 'all' (default), 'wiki', 'docs',
               'log', 'myco' (entry point only).

    Returns:
        JSON list of matches with file path, line number, and context.
    """
    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    # Determine search paths based on scope
    search_paths: List[Path] = []
    if scope in ("all", "myco"):
        canon = _load_canon(root)
        ep = canon.get("system", {}).get("entry_point", "MYCO.md") if isinstance(canon, dict) else "MYCO.md"
        if (root / ep).exists():
            search_paths.append(root / ep)
        if (root / "_canon.yaml").exists():
            search_paths.append(root / "_canon.yaml")

    if scope in ("all", "wiki"):
        wiki_dir = root / "wiki"
        if wiki_dir.exists():
            search_paths.extend(wiki_dir.glob("*.md"))

    if scope in ("all", "docs"):
        docs_dir = root / "docs"
        if docs_dir.exists():
            search_paths.extend(docs_dir.rglob("*.md"))

    if scope in ("all", "log"):
        log_path = root / "log.md"
        if log_path.exists():
            search_paths.append(log_path)
        narratives = root / "docs" / "operational_narratives.md"
        if narratives.exists() and narratives not in search_paths:
            search_paths.append(narratives)

    if not search_paths:
        return json.dumps({"matches": [], "message": f"No files found in scope '{scope}'"})

    # Search
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    matches = []
    for filepath in search_paths:
        content = _read_file(filepath)
        if not content:
            continue
        lines = content.splitlines()
        for i, line in enumerate(lines, 1):
            if pattern.search(line):
                # Provide 1 line of context before and after
                context_start = max(0, i - 2)
                context_end = min(len(lines), i + 1)
                context_lines = lines[context_start:context_end]
                matches.append({
                    "file": str(filepath.relative_to(root)),
                    "line": i,
                    "match": line.strip(),
                    "context": "\n".join(context_lines),
                })

    result = {
        "query": query,
        "scope": scope,
        "total_matches": len(matches),
        "matches": matches[:50],  # Cap at 50 results
    }
    if len(matches) > 50:
        result["truncated"] = True
        result["message"] = f"Showing first 50 of {len(matches)} matches. Narrow your query."

    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_log
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_log",
    annotations={
        "title": "Myco Log — Record Friction or Reflection",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
    },
)
async def myco_log(
    entry_type: str,
    message: str,
    project_dir: Optional[str] = None,
) -> str:
    """Append a timestamped entry to the project's log.md.

    Use this to record friction (Gear 1), reflections (Gear 2), or milestone
    notes. The log is append-only and forms the project's episodic memory.

    Call this when:
    - You encounter unexpected behavior or friction during work
    - A session is ending and you want to capture reflections
    - A milestone is reached or a decision is made

    Args:
        entry_type: One of 'friction', 'reflection', 'milestone', 'system', 'deploy'.
        message: The log entry content. Keep it concise but informative.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        Confirmation message with the logged entry.
    """
    valid_types = {"friction", "reflection", "milestone", "system", "deploy"}
    if entry_type not in valid_types:
        return json.dumps({
            "error": f"Invalid entry_type '{entry_type}'. Must be one of: {', '.join(sorted(valid_types))}",
        })

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()
    log_path = root / "log.md"

    if not log_path.exists():
        return json.dumps({"error": f"log.md not found at {root}"})

    date_str = datetime.now().strftime("%Y-%m-%d")
    entry = f"\n## [{date_str}] {entry_type} | {message}\n"

    try:
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(entry)
        return json.dumps({
            "status": "ok",
            "logged": entry.strip(),
            "file": str(log_path.relative_to(root)),
        })
    except Exception as e:
        return json.dumps({"error": f"Failed to write log: {e}"})


# ---------------------------------------------------------------------------
# Tool: myco_reflect
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_reflect",
    annotations={
        "title": "Myco Reflect — Gear 2 Session-End Prompts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
async def myco_reflect(
    project_dir: Optional[str] = None,
) -> str:
    """Generate Gear 2 reflection prompts for the current session.

    Call this at the end of a work session. Returns reflection questions
    based on the project's current state: recent log entries, lint results,
    and knowledge gaps. The agent should use these prompts to produce a
    brief reflection that gets logged via myco_log.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        Structured reflection prompts based on current project state.
    """
    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    canon = _load_canon(root)
    if "error" in canon:
        return json.dumps({"error": canon["error"]}, indent=2)

    # Gather recent friction entries
    log_path = root / "log.md"
    friction_entries = []
    if log_path.exists():
        log_content = _read_file(log_path)
        if log_content:
            friction_entries = re.findall(
                r"^## \[\d{4}-\d{2}-\d{2}\] friction \|.*$",
                log_content, re.MULTILINE,
            )[-5:]

    # Quick lint check
    from myco.lint import (
        lint_canon_schema, lint_references, lint_numbers, lint_stale_patterns,
    )
    quick_issues = []
    for _, checker in [
        ("L0", lint_canon_schema),
        ("L1", lint_references),
        ("L2", lint_numbers),
        ("L3", lint_stale_patterns),
    ]:
        quick_issues.extend(checker(canon, root))

    # Build reflection prompts
    prompts = [
        "What knowledge was created or modified this session?",
        "Were there any moments of friction or confusion? What caused them?",
        "Is there anything this session revealed that should change the system's structure?",
    ]

    if friction_entries:
        prompts.append(
            f"Recent friction log has {len(friction_entries)} entries. "
            "Are there patterns? Should any become an operational narrative?"
        )

    if quick_issues:
        prompts.append(
            f"Lint found {len(quick_issues)} issue(s). "
            "Were any caused by this session's work? Fix them before ending."
        )
    else:
        prompts.append(
            "Lint is clean. Good session hygiene. "
            "Consider: is there knowledge that should be promoted from docs/ to wiki/?"
        )

    reflection = {
        "gear": "Gear 2 — Session-End Reflection",
        "timestamp": datetime.now().isoformat(),
        "recent_friction": friction_entries,
        "lint_status": "clean" if not quick_issues else f"{len(quick_issues)} issues",
        "prompts": prompts,
        "instruction": (
            "Answer these prompts briefly, then call myco_log with "
            "entry_type='reflection' to persist your reflection."
        ),
    }

    return json.dumps(reflection, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
