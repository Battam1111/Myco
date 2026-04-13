#!/usr/bin/env python3
"""
Myco MCP Server — Exposes Myco's knowledge metabolism tools via Model Context Protocol.

When configured in .mcp.json, AI agents (Claude Code, Cursor, etc.) automatically
discover these tools and call them at the right moments — no manual prompting needed.

Tools:
    myco_lint       — Run 23-dimensional consistency checks (L0-L22)
    myco_status     — Quick overview of knowledge system health
    myco_search     — Search across wiki/docs/MYCO.md knowledge base
    myco_log        — Append friction/reflection entries to log.md
    myco_reflect    — Trigger session-end reflection prompts
    myco_eat        — Capture a chunk of content as a raw atomic note
    myco_digest     — Move a note through the lifecycle (raw→…→excreted)
    myco_view       — Read-only lens on notes/ (list or single note)
    myco_hunger     — Metabolic dashboard with actionable signals
    myco_compress   — Synthesize notes into extracted knowledge (Wave 43)
    myco_uncompress — Reverse a compression operation (Wave 43)
    myco_prune      — Auto-excrete dead-knowledge notes (Wave 43)
    myco_inlet      — Ingest external content with provenance (Wave 43)
    myco_forage     — Manage external source material (Wave 43)
    myco_graph      — Structural link graph analysis (Wave 47)
    myco_cohort     — Semantic cohort intelligence (Wave 48)
    myco_session    — Session memory search (Wave 52)
    myco_evolve     — Agent-driven skill self-improvement (Wave E3)
    myco_evolve_list — List skills and evolution history (Wave E3)

Transport: stdio (local subprocess of the AI client)
"""
# --- Mycelium references ---
# Protocol:    docs/agent_protocol.md (tool trigger conditions, anti-patterns)
# MCP config:  .mcp.json (client-side wiring)
# Skills:      skills/ (skill resolution for evolved tools)

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
    """Wave A1: delegates to centralized find_project_root (non-strict for MCP)."""
    from myco.project import find_project_root
    return find_project_root(strict=False)


def _compute_sidecar(root: Path) -> dict:
    """Wave B2: lightweight hunger summary for sidecar injection.

    Attached to every MCP tool response so Agent always sees substrate health
    without explicitly calling hunger. Push-mode, not pull-mode.
    """
    try:
        notes_dir = root / "notes"
        if not notes_dir.is_dir():
            return {"raw_count": 0, "signals_count": 0, "top_signal": "healthy"}
        raw = sum(1 for f in notes_dir.glob("n_*.md")
                  if "status: raw" in f.read_text(encoding="utf-8", errors="replace")[:200])
        # Quick signal count from last boot brief if available
        brief = root / ".myco_state" / "boot_brief.md"
        signals_count = 0
        top_signal = "healthy"
        if brief.exists():
            brief_text = brief.read_text(encoding="utf-8", errors="replace")
            signals_count = brief_text.count("•")
            for line in brief_text.split("\n"):
                if "•" in line and "healthy" not in line:
                    top_signal = line.split("•")[-1].strip()[:60]
                    break
        return {
            "raw_count": raw,
            "signals_count": signals_count,
            "top_signal": top_signal,
        }
    except Exception:
        return {"raw_count": -1, "signals_count": -1, "top_signal": "error"}


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
        "title": "Myco Lint — 23-Dimension Consistency Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_lint(
    project_dir: Optional[str] = None,
    quick: bool = False,
) -> str:
    """Check the project for contradictions, stale references, and knowledge drift.

    Auto-invoke when: the user says "check", "verify", "lint", "are there
    inconsistencies", "did I break anything", or at the end of any session that
    modified wiki/, docs/, MYCO.md, _canon.yaml, or notes/. Also run after any
    milestone retrospective retrospective or before commits that touch multiple knowledge files.

    This is the 55-dimensional immune system of the knowledge substrate. It
    catches contradictions across files, orphan references, stale patterns,
    version drift, write-surface violations, craft
    protocol schema violations, forage substrate hygiene issues, craft reflex
    arc compliance, boot brief freshness, contract drift, compression
    integrity, lint dimension count drift, translation mirror skeleton drift,
    inline contract version drift, and wave-seed lifecycle orphans — things
    markdown linters and prose linters cannot see because they
    check syntax, not cross-file semantic consistency.

    Checks: L0 Canon schema, L1 Reference integrity, L2 Number consistency,
    L3 Stale patterns, L4 Orphan detection, L5 Log coverage, L6 Date consistency,
    L7 Wiki format, L8 .original sync, L9 Vision anchor, L10 Notes schema,
    L11 Write surface (agent contract from docs/agent_protocol.md §1),
    L13 Craft Protocol schema (docs/primordia/*_craft_*.md frontmatter),
    L14 Forage Hygiene (forage/_index.yaml manifest + lifecycle),
    L15 Craft Reflex (craft must accompany kernel/public_claim surface touches),
    L16 Boot Brief Freshness (.myco_state/boot_brief.md staleness),
    L17 Contract Drift (synced_contract_version lag detection),
    L18 Compression Integrity (.original / extracted note hash audit),
    L19 Lint Dimension Count Consistency (downstream-cache integrity for
    LINT_DIMENSION_COUNT — narrative surfaces must mirror len(lint.FULL_CHECKS)),
    L20 Translation Mirror Consistency (locale README skeleton parity —
    h2/h3/code-fence/table-row/badge counts must match across en/zh/ja),
    L21 Contract Version Inline Consistency (inline contract version SSoT —
    forward-looking pattern; narrative surfaces must mirror canon contract_version),
    L22 Wave-Seed Lifecycle (raw wave-seed orphan detection — seven-step
    pipeline post-condition: a wave-{N}-seed tagged raw note must advance
    out of raw before its wave's milestone lands in log.md).

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

    # Import the dispatch SSoT directly — Wave 38 D9: mcp_server.py
    # MUST NOT maintain a duplicate checks list. len(FULL_CHECKS) is the
    # canonical LINT_DIMENSION_COUNT (Wave 38 D1) and any local cache here
    # would silently drop newly added dimensions (the very bug Wave 38 fixes).
    from myco.lint import FULL_CHECKS, QUICK_CHECKS

    checks = list(QUICK_CHECKS) if quick else list(FULL_CHECKS)

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
        "mode": "quick (L0-L3)" if quick else "full (L0-L22)",
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
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_status(
    project_dir: Optional[str] = None,
    include_hunger: bool = True,
) -> str:
    """Show a quick dashboard of the project's knowledge health.

    Auto-invoke when: starting a new session (orient first), the user asks
    "where are we", "what's the state of the project", "what happened last
    session", or before any decision that depends on knowing what's already
    tracked.

    Returns a dashboard of files counted, wiki pages, recent log entries,
    pending tasks, and lint status. This is the cheapest way to orient before
    doing real work.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.
        include_hunger: When True (default, Wave 13 / v0.12.0), the status
            response includes a `hunger_signals` block scanned from
            `compute_hunger_report`. This folds the boot sequence
            (`myco_status` → `myco_hunger`) into one atomic call so that
            contract_drift + raw_backlog reflex signals surface before any
            task work. **Setting `include_hunger=False` while raw_backlog
            is above threshold is a W1 autopilot violation** — see
            docs/primordia/boot_reflex_arc_craft_2026-04-11.md.

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
        "contract_version": canon.get("system", {}).get("contract_version", "?"),
        "synced_contract_version": canon.get("system", {}).get("synced_contract_version", "?"),
        "knowledge": {
            "wiki_pages": wiki_count,
            "docs_files": docs_count,
            "adapters": adapter_count,
            "principles_count": canon.get("system", {}).get("principles_count", "?"),
            "metabolic_phases": canon.get("system", {}).get("metabolic_phases", "?"),
        },
        "recent_log_entries": recent_log,
        "task_queue": tasks,
        "hint": (
            "Run myco_lint to check for inconsistencies. "
            "Use myco_search to find specific knowledge. "
            "Use myco_log to record friction or reflections."
        ),
    }

    # Wave 13 (contract v0.12.0): boot reflex arc — fold hunger into status
    # so reflex signals (contract_drift, raw_backlog HIGH, craft_reflex)
    # surface on boot before any task work. `include_hunger=False` bypass
    # while raw_backlog is hot is a W1 violation (see
    # docs/primordia/boot_reflex_arc_craft_2026-04-11.md).
    if include_hunger:
        try:
            from myco.notes import compute_hunger_report
            report = compute_hunger_report(root)
            reflex_signals = [s for s in report.signals if s.startswith("[REFLEX HIGH]")]
            advisory_signals = [s for s in report.signals if not s.startswith("[REFLEX HIGH]")]
            status["hunger_signals"] = {
                "reflex": reflex_signals,
                "advisory": advisory_signals,
                "by_status": report.by_status,
                "total_notes": report.total,
            }
            if reflex_signals:
                status["hint"] = (
                    "⚠️ REFLEX HIGH signals present — resolve them before "
                    "any task work. See hunger_signals.reflex for details."
                )
        except Exception as e:
            status["hunger_signals"] = {"error": str(e)}

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
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_search(
    query: str,
    project_dir: Optional[str] = None,
    scope: str = "all",
) -> str:
    """Find content across the project's wiki, docs, notes, and log.

    Auto-invoke when: the user asks "do we have anything on X", "have we
    decided Y before", "what did I write about Z last week", or before
    answering any factual question about the project. **Always search before
    guessing** — the project's persistent memory is the source of truth.

    Searches MYCO.md, wiki pages, docs, log.md, notes, and operational
    narratives for the given query string.

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

    # Wave 49 (v0.38.0): record search miss for inlet trigger detection.
    if len(matches) == 0:
        try:
            from myco.notes import record_search_miss
            record_search_miss(root, query)
        except Exception:
            pass  # best-effort — don't break search on tracking failure

    # Wave B2: hunger sidecar — Agent sees substrate health on search calls
    result["_myco_sidecar"] = _compute_sidecar(root)

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
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_log(
    entry_type: str,
    message: str,
    project_dir: Optional[str] = None,
) -> str:
    """Record a friction, reflection, or milestone to the project timeline.

    Auto-invoke when: you hit unexpected behavior or tool friction (hunger sensing),
    a session is ending and you have reflections (session reflection), a milestone is
    reached, a decision is made, or anything happens that future you would
    want to find 3 weeks from now.

    The log is append-only episodic memory — it never rewrites, only grows.
    Prefer logging over silence: the cost of capturing a friction is seconds;
    the cost of re-hitting the same friction next session is minutes.

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
        "title": "Myco Reflect — session reflection Session-End Prompts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_reflect(
    project_dir: Optional[str] = None,
) -> str:
    """Ask "what should the knowledge system itself improve?" at session end.

    Auto-invoke when: the user signals a session is wrapping up ("let's stop
    here", "end session", "that's enough for today"), or after any retrospective
    trigger like "what did we learn", or whenever an operation finishes cleanly
    and ≥3 log entries were added during the session.

    Returns session reflection reflection prompts derived from recent log entries, lint
    results, and knowledge gaps. The agent should answer the prompts and log
    the reflection via myco_log. session reflection is how the substrate evolves its own
    rules — skipping it is how drift compounds.

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

    # Mycelium self-maintenance: check for orphans at session end
    try:
        from myco.graph import build_link_graph, find_orphans
        graph = build_link_graph(root)
        orphans = find_orphans(graph)
        note_orphans = [o for o in orphans if o.startswith("notes/")]
        if note_orphans:
            prompts.append(
                f"MYCELIUM: {len(note_orphans)} orphaned note(s) with zero inbound links. "
                f"Add ## Related cross-references to connect them. "
                f"Disconnected knowledge is dead knowledge. Top orphans: "
                f"{', '.join(note_orphans[:5])}"
            )
    except Exception:
        pass  # graph module not available

    # Learning Loop (absorbed from gstack): auto-capture execution summary
    # as a note with execution-learning tag. This is NOT just a document —
    # it's code that runs every time reflect is called.
    learning_note_id = None
    try:
        from myco.notes import write_note
        learning_body = (
            f"## Execution Learning (auto-captured at session end)\n\n"
            f"Friction entries this session: {len(friction_entries)}\n"
            f"Lint status: {'clean' if not quick_issues else f'{len(quick_issues)} issues'}\n"
        )
        if friction_entries:
            learning_body += f"Recent friction: {'; '.join(f[:60] for f in friction_entries[-3:])}\n"
        path = write_note(
            root, learning_body,
            tags=["execution-learning", "auto-captured", "reflection"],
            source="eat",
        )
        learning_note_id = path.stem
    except Exception:
        pass  # best-effort; never block reflection

    reflection = {
        "phase": "session reflection — Session-End Reflection",
        "timestamp": datetime.now().isoformat(),
        "recent_friction": friction_entries,
        "lint_status": "clean" if not quick_issues else f"{len(quick_issues)} issues",
        "prompts": prompts,
        "learning_note": learning_note_id,
        "instruction": (
            "Answer these prompts briefly, then call myco_log with "
            "entry_type='reflection' to persist your reflection. "
            "An execution-learning note was auto-captured."
        ),
    }

    return json.dumps(reflection, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_eat  —  digestive substrate ingestion
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_eat",
    annotations={
        "title": "Myco Eat — Capture Content as Raw Atomic Note",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_eat(
    content: str,
    tags: Optional[List[str]] = None,
    title: Optional[str] = None,
    source: str = "chat",
    project_dir: Optional[str] = None,
) -> str:
    """Capture a chunk of content as a raw atomic note in notes/.

    WHEN TO CALL — do not wait for permission, do not wait for session end.
    Call IMMEDIATELY when the user shares any of:
      (a) a piece of code that worked, a config, a command line that fixed something
      (b) a decision with reasoning ("we chose X because Y")
      (c) a root cause found after debugging
      (d) a file, log excerpt, URL, or paper they pasted into the conversation
      (e) phrasing like "TIL", "note to self", "remember this", "mark this"
      (f) any hard-won piece of knowledge that would be painful to re-derive

    Do NOT ask "should I save this?" — the whole point of `eat` is
    zero-friction capture. A raw note costs almost nothing; a lost insight
    costs everything. If in doubt, eat.

    The note enters as status='raw'. Later, the agent (or human) calls
    myco_digest to transition it toward extracted / integrated / excreted.

    Args:
        content: The text to capture. Can be code, prose, YAML, anything.
        tags: Optional list of free-form tag strings (e.g. ["vision","lint"]).
        title: Optional H1 title to prepend (if body doesn't already start
               with a heading).
        source: Provenance label. Use 'chat' when auto-capturing from
                conversation context, 'eat' for explicit user invocation.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with the new note's id and relative path.
    """
    from myco.notes import write_note, VALID_SOURCES

    if source not in VALID_SOURCES:
        return json.dumps({
            "error": f"Invalid source {source!r}. Expected one of: {list(VALID_SOURCES)}",
        })

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({
            "error": f"Not a Myco project (no _canon.yaml at {root})",
        })

    try:
        path = write_note(
            root, content,
            tags=tags or [],
            source=source,
            status="raw",
            title=title,
        )
    except Exception as e:
        return json.dumps({"error": f"Failed to write note: {e}"})

    rel = str(path.relative_to(root))
    return json.dumps({
        "status": "ok",
        "id": path.stem,
        "file": rel,
        "tags": tags or [],
        "source": source,
        "hint": (
            "Call myco_digest when the note is ready to be processed. "
            "IMPORTANT: add cross-references (## Related section) linking "
            "this note to related notes/docs. Orphaned knowledge is dead knowledge."
        ),
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_digest  —  lifecycle transition + reflection prompts
# ---------------------------------------------------------------------------

_DIGEST_PROMPTS = [
    "What is the single most compressible claim in this note?",
    "Is there an existing wiki page or MYCO.md section this belongs to?",
    "If this were lost tomorrow, what would break?",
    "What should the new status be: extracted / integrated / excreted?",
]


@mcp.tool(
    name="myco_digest",
    annotations={
        "title": "Myco Digest — Advance a Note Through the Lifecycle",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_digest(
    note_id: Optional[str] = None,
    to_status: Optional[str] = None,
    excrete_reason: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Move a note along the digestive lifecycle: raw → digesting → {extracted | integrated | excreted}.

    Contract: docs/agent_protocol.md §2.2 + §2.3. L10 lint enforces frontmatter.

    WHEN TO CALL (trigger conditions):
      (a) At session start, after myco_hunger — if hunger reports
          raw_backlog or stale_raw, call myco_digest with no note_id to
          process the oldest raw note.
      (b) Before extracting a note's claim into wiki/ or MYCO.md — run
          digest first to walk the reflection prompts, THEN transition.
      (c) When a note is obsolete / duplicate / wrong → call with
          excrete_reason (required by L10).
      (d) Non-linear jumps (raw → integrated, raw → excreted) are legal
          but MUST go through this tool. Never hand-edit the status
          frontmatter field.

    ANTI-PATTERNS (do NOT do these):
      - Manually editing notes/*.md to change status
      - Skipping digest and writing directly into wiki/ or MYCO.md
      - Calling excreted without excrete_reason
      - Bulk-transitioning many notes at once without reading them

    Modes:
      1. Reflective (default): note_id=None or omit to_status → picks
         oldest raw note, flips it to 'digesting', returns prompts.
      2. Transition: supply to_status in {raw, digesting, extracted,
         integrated, excreted}.
      3. Shortcut: supply excrete_reason → marks as excreted with reason.

    Args:
        note_id: Target note id (e.g. 'n_20260410T143027_7f3a'). If None,
                 picks the oldest raw note in the queue.
        to_status: Explicit transition target. Takes precedence over
                   the default reflective flow.
        excrete_reason: If set, marks the note as excreted with this reason.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with note id, new status, body preview, and reflection prompts.
    """
    from myco.notes import (
        read_note, update_note, list_notes, id_to_filename, VALID_STATUSES,
    )

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    # Resolve target
    if note_id:
        nid = note_id if note_id.startswith("n_") else f"n_{note_id}"
        target = root / "notes" / id_to_filename(nid)
        if not target.exists():
            return json.dumps({"error": f"Note not found: {nid}"})
    else:
        raw_notes = list_notes(root, status="raw")
        if not raw_notes:
            return json.dumps({
                "status": "empty",
                "message": "No raw notes to digest. Queue is clean.",
            })
        target = raw_notes[0]

    try:
        meta, body = read_note(target)
    except Exception as e:
        return json.dumps({"error": f"Failed to read note: {e}"})

    # Excrete shortcut
    if excrete_reason:
        try:
            new_meta = update_note(
                target,
                status="excreted",
                excrete_reason=excrete_reason,
                _increment_digest=True,
            )
        except Exception as e:
            return json.dumps({"error": f"Excrete failed: {e}"})
        return json.dumps({
            "status": "ok",
            "id": target.stem,
            "transition": f"{meta.get('status')} → excreted",
            "reason": excrete_reason,
        }, ensure_ascii=False)

    # Explicit transition
    if to_status:
        if to_status not in VALID_STATUSES:
            return json.dumps({
                "error": f"Invalid to_status {to_status!r}. Expected: {list(VALID_STATUSES)}",
            })
        try:
            update_note(target, status=to_status, _increment_digest=True)
        except Exception as e:
            return json.dumps({"error": f"Transition failed: {e}"})
        return json.dumps({
            "status": "ok",
            "id": target.stem,
            "transition": f"{meta.get('status')} → {to_status}",
        }, ensure_ascii=False)

    # Default: flip raw → digesting and return prompts
    try:
        if meta.get("status") == "raw":
            update_note(target, status="digesting", _increment_digest=True)
            current = "digesting"
        else:
            update_note(target, _increment_digest=True)
            current = meta.get("status", "raw")
    except Exception as e:
        return json.dumps({"error": f"Update failed: {e}"})

    preview_lines = body.splitlines()[:20]
    return json.dumps({
        "status": "reflect",
        "id": target.stem,
        "transition": f"{meta.get('status')} → {current}",
        "tags": meta.get("tags") or [],
        "digest_count": int(meta.get("digest_count") or 0) + 1,
        "body_preview": "\n".join(preview_lines),
        "body_truncated": len(body.splitlines()) > 20,
        "prompts": _DIGEST_PROMPTS,
        "instruction": (
            "Answer the prompts, then call myco_digest again with "
            "to_status='extracted' | 'integrated' | 'excreted' (with "
            "excrete_reason if excreted)."
        ),
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_view  —  read-only lens on notes/
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_view",
    annotations={
        "title": "Myco View — List or Read Atomic Notes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_view(
    note_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    project_dir: Optional[str] = None,
) -> str:
    """List notes in notes/ (optionally filtered by status) or read a single note.

    Contract: docs/agent_protocol.md §2.2. Read-only — cannot corrupt substrate.

    WHEN TO CALL (trigger conditions):
      (a) BEFORE answering any question that might already live in notes/
          — grep your memory substrate first, not your training weights.
      (b) User asks "what were we doing?" / "where did we leave off?" →
          myco_view status='raw' or 'digesting' shows the active queue.
      (c) Starting a new task on a known topic → myco_view with a
          specific note_id or status filter to rehydrate context.
      (d) Phase ② prep → myco_view status='raw' filters to notes tagged
          'friction-phase2' to review accumulated friction signals.

    ANTI-PATTERNS:
      - Answering from memory when a search would have found the answer
      - Reading notes/ directly via filesystem — this tool applies the
        canonical ordering and schema parse

    Args:
        note_id: If set, return that single note's full body + metadata.
        status: Filter list mode by status (raw/digesting/extracted/
                integrated/excreted).
        limit: Max notes to return in list mode (default 50, most recent).
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON: single note dict, or list of note summaries.
    """
    from myco.notes import read_note, list_notes, id_to_filename, VALID_STATUSES

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if note_id:
        nid = note_id if note_id.startswith("n_") else f"n_{note_id}"
        path = root / "notes" / id_to_filename(nid)
        if not path.exists():
            return json.dumps({"error": f"Note not found: {nid}"})
        try:
            meta, body = read_note(path)
        except Exception as e:
            return json.dumps({"error": f"Failed to read note: {e}"})
        return json.dumps({
            "id": meta.get("id"),
            "metadata": meta,
            "body": body,
            "file": str(path.relative_to(root)),
        }, ensure_ascii=False)

    if status and status not in VALID_STATUSES:
        return json.dumps({
            "error": f"Invalid status {status!r}. Expected: {list(VALID_STATUSES)}",
        })

    paths = list_notes(root, status=status)
    paths = paths[-limit:]
    out = []
    for p in paths:
        try:
            meta, body = read_note(p)
        except Exception:
            continue
        title = ""
        for line in body.splitlines():
            if line.strip().startswith("#"):
                title = line.strip().lstrip("#").strip()
                break
        out.append({
            "id": meta.get("id"),
            "file": str(p.relative_to(root)),
            "status": meta.get("status"),
            "tags": meta.get("tags") or [],
            "digest_count": meta.get("digest_count"),
            "last_touched": meta.get("last_touched"),
            "title": title or "(untitled)",
        })
    return json.dumps({
        "filter": status or "all",
        "count": len(out),
        "notes": out,
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_hunger  —  metabolic dashboard
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_hunger",
    annotations={
        "title": "Myco Hunger — Metabolic Substrate Dashboard",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_hunger(
    execute: bool = False,
    project_dir: Optional[str] = None,
) -> str:
    """The substrate's metabolic dashboard — your FIRST call every session.

    == AGENT BOOT RITUAL (mandatory) ==
    1. Call myco_hunger(execute=true) at session start
    2. The substrate auto-heals: digests stale notes, compresses ripe
       cohorts, prunes dead knowledge
    3. Read the signals list — if anything other than "healthy", address
       it before doing the human's task
    4. Call myco_hunger() again before session end to confirm healthy state

    == WHAT THIS TOOL DOES ==
    Scans the entire knowledge substrate and reports:
    - Status counts (raw/digesting/extracted/integrated/excreted)
    - Hunger signals (what's wrong, sorted by urgency)
    - Recommended actions (what to do about it, with exact verb+args)
    - Graph connectivity (orphan files count)
    - Session memory status

    == EXECUTE MODE (execute=true) ==
    When execute=true, the tool automatically runs all recommended actions:
    - digest stale/backlogged notes
    - compress ripe cohorts (--cohort auto)
    - prune dead knowledge
    - (inlet is advisory-only — logged but not auto-triggered)
    This is the normal mode. Use execute=false only to inspect without acting.

    == SIGNALS (sorted by urgency) ==
    [REFLEX HIGH] raw_backlog — must digest NOW before any other work
    stale_raw — old unprocessed notes
    compression_pressure — accumulating faster than synthesizing
    compression_ripe — tag cohort ready for compression
    inlet_ripe — knowledge gaps detected, consider external acquisition
    graph_orphans — files with zero inbound links (disconnected knowledge)
    session_index_missing — no session memory index, run myco session index
    dead_knowledge — terminal notes going cold
    healthy — everything is fine

    Args:
        execute: If true, auto-execute all recommended actions (default false).
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON HungerReport with totals, signals, actions, and execution results.
    """
    from myco.notes import compute_hunger_report

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    try:
        report = compute_hunger_report(root)
    except Exception as e:
        return json.dumps({"error": f"Hunger computation failed: {e}"})

    result = report.to_dict()

    # Wave 54: auto-execute recommended actions
    if execute and report.actions:
        execution_results = []
        for action in report.actions:
            verb = action.get("verb", "")
            a_args = action.get("args", {})
            reason = action.get("reason", "")
            exec_result = {"verb": verb, "reason": reason}
            try:
                if verb == "digest":
                    note_id = a_args.get("note_id")
                    if note_id:
                        import argparse
                        ns = argparse.Namespace(
                            note_id=note_id, project_dir=str(root),
                            to_status=a_args.get("to_status"),
                            json=False, excrete=None)
                        from myco.notes_cmd import run_digest
                        import io, contextlib
                        buf = io.StringIO()
                        with contextlib.redirect_stdout(buf):
                            rc = run_digest(ns)
                        exec_result["status"] = "ok" if rc == 0 else f"exit {rc}"
                    else:
                        exec_result["status"] = "skipped (bulk digest needs note selection)"
                elif verb == "compress":
                    tag = a_args.get("tag")
                    cohort = a_args.get("cohort")
                    import argparse
                    ns = argparse.Namespace(
                        tag=tag, note_ids=[], rationale=f"auto: {reason[:100]}",
                        status=None, confidence=0.85, dry_run=False,
                        json=False, project_dir=str(root),
                        cohort=cohort)
                    from myco.compress_cmd import run_compress
                    import io, contextlib
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        rc = run_compress(ns)
                    exec_result["status"] = "ok" if rc == 0 else f"exit {rc}"
                    exec_result["output"] = buf.getvalue().strip()[:200]
                elif verb == "prune":
                    import argparse
                    ns = argparse.Namespace(
                        apply=True, json=False, project_dir=str(root))
                    from myco.notes_cmd import run_prune
                    import io, contextlib
                    buf = io.StringIO()
                    with contextlib.redirect_stdout(buf):
                        rc = run_prune(ns)
                    exec_result["status"] = "ok" if rc == 0 else f"exit {rc}"
                elif verb == "inlet":
                    exec_result["status"] = "advisory (inlet needs human/agent decision)"
                else:
                    exec_result["status"] = f"skipped (unknown verb: {verb})"
            except Exception as e:
                exec_result["status"] = f"error: {e}"
            execution_results.append(exec_result)
        result["execution_results"] = execution_results

    # Sprint Pipeline hint (absorbed from gstack): tell Agent where they are
    # in the development loop based on current substrate state.
    has_gaps = any("inlet_ripe" in s or "cold_start" in s or "cohort_staleness" in s
                    for s in report.signals)
    if report.signals and any("healthy" in s for s in report.signals):
        result["pipeline_hint"] = "Build — substrate healthy, proceed with task work"
    elif report.actions:
        result["pipeline_hint"] = "Think — substrate needs attention, execute actions first"
    elif has_gaps:
        result["pipeline_hint"] = "Discover — knowledge gaps detected, use myco_cohort(action='gaps') then myco_inlet to ingest"
    else:
        result["pipeline_hint"] = "Build — signals advisory only, proceed with caution"
    result["pipeline_ref"] = "skills/sprint-pipeline.md"

    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_compress  —  forward compression synthesis
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_compress",
    annotations={
        "title": "Myco Compress — Synthesize Notes into Extracted Knowledge",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_compress(
    rationale: str,
    tag: Optional[str] = None,
    note_ids: Optional[List[str]] = None,
    confidence: float = 0.85,
    dry_run: bool = False,
    project_dir: Optional[str] = None,
) -> str:
    """Compress multiple notes into one extracted note with audit trail.

    WHEN TO CALL:
      (a) When myco_hunger reports compression_ripe signal.
      (b) When you see 3+ raw/digesting notes with the same tag cohort.
      (c) After completing a wave that produced multiple seed notes.

    The inputs are marked excreted; the output carries compressed_from
    back-references and your rationale for what was preserved vs dropped.

    Args:
        rationale: Compression synthesis prose — what was preserved and why.
        tag: Tag-based cohort selector (selects all raw/digesting notes with this tag).
        note_ids: Explicit list of note ids to compress (mutually exclusive with tag).
        confidence: Self-reported compression confidence [0.0, 1.0].
        dry_run: If True, show what would happen without writing.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with output note id, input count, and compression metadata.
    """
    import argparse

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    if not rationale:
        return json.dumps({"error": "rationale is required for compression"})

    if tag and note_ids:
        return json.dumps({"error": "Provide tag OR note_ids, not both"})

    if not tag and not note_ids:
        return json.dumps({"error": "Provide either tag or note_ids"})

    args = argparse.Namespace(
        tag=tag,
        note_ids=note_ids or [],
        rationale=rationale,
        status=None,
        confidence=confidence,
        dry_run=dry_run,
        json=True,
        project_dir=str(root),
    )

    from myco.compress_cmd import run_compress
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = run_compress(args)

    output = buf.getvalue().strip()
    if exit_code == 0:
        try:
            return output if output else json.dumps({"status": "ok"})
        except Exception:
            return json.dumps({"status": "ok", "output": output})
    else:
        return json.dumps({"error": f"Compression failed (exit {exit_code})", "output": output})


# ---------------------------------------------------------------------------
# Tool: myco_uncompress  —  reverse compression
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_uncompress",
    annotations={
        "title": "Myco Uncompress — Reverse a Compression Operation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_uncompress(
    output_id: str,
    project_dir: Optional[str] = None,
) -> str:
    """Reverse a previous compression — restore input notes and delete the output.

    Use when a compression was done incorrectly or when you need to
    re-process the original inputs differently.

    Args:
        output_id: The id of the extracted (output) note to reverse.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with restored note ids and status.
    """
    import argparse

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    args = argparse.Namespace(
        output_id=output_id,
        json=True,
        project_dir=str(root),
    )

    from myco.compress_cmd import run_uncompress
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = run_uncompress(args)

    output = buf.getvalue().strip()
    if exit_code == 0:
        return output if output else json.dumps({"status": "ok"})
    else:
        return json.dumps({"error": f"Uncompress failed (exit {exit_code})", "output": output})


# ---------------------------------------------------------------------------
# Tool: myco_prune  —  dead knowledge auto-excretion
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_prune",
    annotations={
        "title": "Myco Prune — Auto-Excrete Dead Knowledge",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_prune(
    apply: bool = False,
    threshold_days: Optional[int] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Scan for dead-knowledge notes and optionally excrete them.

    WHEN TO CALL:
      (a) When myco_hunger reports dead_knowledge signal.
      (b) During periodic substrate maintenance (every few sessions).

    Dead knowledge = terminal status + untouched for threshold days + low view count.

    SAFE BY DEFAULT: dry-run mode unless apply=True. Always preview first.

    Args:
        apply: If True, actually excrete the dead notes. Default: False (dry-run).
        threshold_days: Override the dead-knowledge threshold (default from canon).
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with list of candidates and whether they were pruned.
    """
    import argparse

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    args = argparse.Namespace(
        apply=apply,
        threshold_days=threshold_days,
        json=True,
        project_dir=str(root),
    )

    from myco.notes_cmd import run_prune
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = run_prune(args)

    output = buf.getvalue().strip()
    if exit_code == 0:
        return output if output else json.dumps({"status": "ok", "candidates": []})
    else:
        return json.dumps({"error": f"Prune failed (exit {exit_code})", "output": output})


# ---------------------------------------------------------------------------
# Tool: myco_inlet  —  external content ingestion
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_inlet",
    annotations={
        "title": "Myco Inlet — Ingest External Content with Provenance",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_inlet(
    content: str,
    provenance: str,
    tags: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Ingest external content into the metabolic pipeline with full provenance tracking.

    WHEN TO CALL:
      (a) After fetching external content (web page, repo README, paper abstract).
      (b) When the user shares a document or URL content for the substrate to absorb.
      (c) When a cohort gap or wiki miss suggests the substrate needs external knowledge.

    Each inlet note gets provenance fields: inlet_origin, inlet_method,
    inlet_fetched_at, inlet_content_hash (SHA256).

    Args:
        content: The external content body to ingest.
        provenance: Origin label (URL, file path, or description).
        tags: Comma-separated tags (default: "inlet").
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with the new note's id, path, and provenance metadata.
    """
    import argparse

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    args = argparse.Namespace(
        source=None,
        content=content,
        provenance=provenance,
        tags=tags or "inlet",
        json=True,
        project_dir=str(root),
    )

    from myco.inlet_cmd import run_inlet
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = run_inlet(args)

    output = buf.getvalue().strip()
    if exit_code == 0:
        return output if output else json.dumps({"status": "ok"})
    else:
        return json.dumps({"error": f"Inlet failed (exit {exit_code})", "output": output})


# ---------------------------------------------------------------------------
# Tool: myco_forage  —  external material management
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_forage",
    annotations={
        "title": "Myco Forage — Manage External Source Material",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_forage(
    action: str,
    source_url: Optional[str] = None,
    source_type: Optional[str] = None,
    local_path: Optional[str] = None,
    license: Optional[str] = None,
    why: Optional[str] = None,
    item_id: Optional[str] = None,
    status: Optional[str] = None,
    digest_target: Optional[List[str]] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Manage the forage substrate — register, list, and digest external material.

    WHEN TO CALL:
      (a) After discovering an external repo/paper/article worth absorbing.
      (b) When forage_backlog hunger signal fires.
      (c) After producing digest notes from a foraged item.

    Actions:
      - add: Register a new external source (requires source_url, source_type, license, why).
      - list: Show forage manifest (optional status filter).
      - digest: Mark an item as digested after producing notes (requires item_id, status).

    Args:
        action: One of 'add', 'list', 'digest'.
        source_url: URL of the external source (for 'add').
        source_type: Type: 'repo', 'paper', 'article', 'docs' (for 'add').
        local_path: Local clone/download path (for 'add', optional).
        license: License identifier (for 'add'; unknown triggers quarantine).
        why: Intent statement — why is this being foraged? (for 'add').
        item_id: Manifest item id (for 'digest').
        status: New status for the item (for 'digest').
        digest_target: List of note ids produced from this item (for 'digest').
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with action result.
    """
    import argparse

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    if action not in ("add", "list", "digest"):
        return json.dumps({"error": f"Invalid action {action!r}. Use 'add', 'list', or 'digest'."})

    args = argparse.Namespace(
        forage_subcommand=action,
        source_url=source_url,
        source_type=source_type,
        local_path=local_path,
        license=license,
        why=why,
        item_id=item_id,
        status=status,
        digest_target=digest_target or [],
        json=True,
        project_dir=str(root),
    )

    from myco.forage_cmd import run_forage
    import io, contextlib
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        exit_code = run_forage(args)

    output = buf.getvalue().strip()
    if exit_code == 0:
        return output if output else json.dumps({"status": "ok"})
    else:
        return json.dumps({"error": f"Forage {action} failed (exit {exit_code})", "output": output})


# ---------------------------------------------------------------------------
# Wave 47 (v0.36.0): Link graph analysis
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_graph",
    annotations={
        "title": "Myco Link Graph — structural link analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_graph(
    action: str,
    target_file: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Query the substrate's structural link graph.

    WHEN TO CALL:
      (a) Need to know who references a specific file → action='backlinks'
      (b) Detect disconnected knowledge islands → action='clusters'
      (c) hunger reports graph_orphans signal → action='orphans' to see full list
      (d) Before refactoring: assess impact scope → action='backlinks'
      (e) Periodic structural health check → action='stats'

    Computes forward links, backlinks, orphan detection, and connected
    components on-demand across all .md files. No cached state — the graph
    IS the files.

    Actions:
      backlinks <file> — who references this file?
      orphans          — files with zero inbound links (structural roots excluded)
      clusters         — connected components (knowledge islands)
      stats            — summary: nodes, edges, orphans, hub, authority

    Args:
        action: One of 'backlinks', 'orphans', 'clusters', 'stats'.
        target_file: Required for 'backlinks'. Relative path to the target file.
        project_dir: Path to Myco project root. Auto-detected if omitted.
    """
    from myco.graph import (
        build_link_graph,
        find_clusters,
        find_orphans,
        graph_stats,
        query_backlinks,
    )

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    graph = build_link_graph(root)

    if action == "backlinks":
        if not target_file:
            return json.dumps({"error": "target_file is required for 'backlinks' action"})
        bl = query_backlinks(graph, target_file)
        return json.dumps({"target": target_file, "backlinks": bl, "count": len(bl)})

    if action == "orphans":
        orphans = find_orphans(graph)
        return json.dumps({"orphans": orphans, "count": len(orphans)})

    if action == "clusters":
        clusters = find_clusters(graph)
        return json.dumps({
            "clusters": clusters,
            "cluster_count": len(clusters),
        })

    if action == "stats":
        stats = graph_stats(graph)
        return json.dumps(stats)

    return json.dumps({"error": f"Unknown action: {action}. Use backlinks/orphans/clusters/stats."})


# ---------------------------------------------------------------------------
# Wave 48 (v0.37.0): Semantic cohort intelligence
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_cohort",
    annotations={
        "title": "Myco Cohort Intelligence — tag co-occurrence and gap analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_cohort(
    action: str,
    limit: int = 10,
    project_dir: Optional[str] = None,
) -> str:
    """Analyze tag-based cohorts across notes for compression and gap detection.

    WHEN TO CALL:
      (a) Before running myco_compress — use action='suggest' to pick the
          best cohort instead of guessing which tag to compress
      (b) hunger reports cohort_staleness or inlet_ripe — use action='gaps'
          to see which knowledge domains are unprocessed
      (c) Exploring tag relationships — use action='matrix' to see which
          topics co-occur (helps understand knowledge structure)

    Actions:
      matrix  — tag co-occurrence pairs (which tags appear together?)
      suggest — compression cohort suggestions (which notes to compress together?)
      gaps    — knowledge gaps (tags where all notes are raw/digesting)

    Args:
        action: One of 'matrix', 'suggest', 'gaps'.
        limit: Max results to return (default 10).
        project_dir: Path to Myco project root. Auto-detected if omitted.
    """
    from myco.cohorts import (
        compression_cohort_suggest,
        gap_detection,
        tag_cooccurrence,
    )

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if action == "matrix":
        pairs = tag_cooccurrence(root)
        return json.dumps([{"tag_a": a, "tag_b": b, "count": c}
                           for a, b, c in pairs[:limit]])

    if action == "suggest":
        suggestions = compression_cohort_suggest(root)
        return json.dumps(suggestions[:limit])

    if action == "gaps":
        gaps = gap_detection(root)
        return json.dumps(gaps[:limit])

    return json.dumps({"error": f"Unknown action: {action}. Use matrix/suggest/gaps."})


# ---------------------------------------------------------------------------
# Wave 52 (v0.40.0): Session memory + search
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_session",
    annotations={
        "title": "Myco Session Memory — FTS5 search across agent conversations",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_session(
    action: str,
    query: Optional[str] = None,
    max_age_days: int = 90,
    project_dir: Optional[str] = None,
) -> str:
    """Index and search agent conversation transcripts.

    WHEN TO CALL:
      (a) hunger reports session_index_missing → action='index' to build index
      (b) Need to recall what was discussed in a previous session →
          action='search', query='the topic'
      (c) Human asks "what did we talk about last time?" → action='search'
      (d) Periodically (weekly) to keep index current → action='index'
      (e) Index getting large → action='prune' to remove old entries

    Actions:
      index — Scan .jsonl session files, index into SQLite FTS5
      search <query> — Full-text search across indexed sessions
      prune — Remove old index entries

    Args:
        action: One of 'index', 'search', 'prune'.
        query: Search query (required for 'search' action).
        max_age_days: Max age for indexing/pruning (default 90).
        project_dir: Path to Myco project root. Auto-detected if omitted.
    """
    from myco.sessions import index_sessions, prune_sessions, search_sessions

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if action == "index":
        stats = index_sessions(root, max_age_days=max_age_days)
        return json.dumps(stats)

    if action == "search":
        if not query:
            return json.dumps({"error": "query is required for 'search' action"})
        results = search_sessions(root, query)
        return json.dumps(results)

    if action == "prune":
        stats = prune_sessions(root, max_age_days=max_age_days)
        return json.dumps(stats)

    return json.dumps({"error": f"Unknown action: {action}. Use index/search/prune."})




# ---------------------------------------------------------------------------
# Wave E3: Skill Evolution — Agent-driven self-improvement
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_evolve",
    annotations={
        "title": "Myco Evolve — Agent-Driven Skill Self-Improvement",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_evolve(
    skill_path: str,
    action: str = "propose",
    mutation_prompt: str = "",
    new_body: str = "",
    dry_run: bool = False,
    project_dir: Optional[str] = None,
) -> str:
    """Evolve a skill through Agent-driven mutation with constraint gates.

    Since MCP tools cannot call an LLM mid-execution, this works in two
    phases — the Agent IS the intelligence (Bitter Lesson compliance):

    Phase 1 — action='propose':
      Returns the current skill content so the Agent can apply its
      intelligence to improve it.

    Phase 2 — action='apply':
      Accepts the Agent's improved body, runs constraint gates
      (frontmatter preserved, body non-empty, no secret leak, size
      growth cap), and if all pass, saves to skills/.evolved/.

    WHEN TO CALL:
      (a) Metabolic cycle detects a skill with low success rate
          (below system.evolution.skill_success_threshold in _canon.yaml)
      (b) Agent identifies an improvement opportunity during session work
      (c) After absorbing external patterns that could improve a skill

    ANTI-PATTERNS:
      - Calling 'apply' without first calling 'propose' (context loss)
      - Skipping gate failures — they exist to prevent skill corruption
      - Evolving more than max_mutations_per_cycle skills per session

    Args:
        skill_path: Relative path to skill file (e.g. "skills/metabolic-cycle.md").
        action: 'propose' (get current content) or 'apply' (submit improved body).
        mutation_prompt: What to improve — Agent provides this (required for 'apply').
        new_body: The Agent's improved skill body (required for 'apply').
        dry_run: If True, run gates but don't save (default False).
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with skill content (propose) or gate results + diff summary (apply).
    """
    from myco.evolve import (
        SkillVariant, check_gates, diff_variants, export_evolved_skill,
        parse_skill, serialize_skill,
    )

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    skill_file = root / skill_path
    if not skill_file.exists():
        return json.dumps({"error": f"Skill not found: {skill_path}"})

    if action == "propose":
        original = parse_skill(skill_file)
        return json.dumps({
            "action": "propose",
            "skill_path": skill_path,
            "meta": original.meta,
            "body": original.body,
            "content_hash": original.content_hash,
            "generation": original.generation,
            "instruction": (
                "Apply your intelligence to improve this skill body based on "
                "your mutation_prompt. Then call myco_evolve again with "
                "action='apply', the same skill_path, your mutation_prompt, "
                "and the improved body in new_body. Preserve the meaning; "
                "improve clarity, completeness, or correctness."
            ),
        }, ensure_ascii=False)

    if action == "apply":
        if not new_body.strip():
            return json.dumps({"error": "new_body is required for 'apply' action"})
        if not mutation_prompt:
            return json.dumps({"error": "mutation_prompt is required for 'apply' action"})

        original = parse_skill(skill_file)

        # Build the mutated variant — Agent already applied intelligence
        mutated = SkillVariant(
            meta=dict(original.meta),  # Preserve metadata immutably
            body=new_body.strip(),
            parent_hash=original.content_hash,
            generation=original.generation + 1,
        )

        # Run constraint gates
        gate_failures = check_gates(original, mutated)

        if gate_failures:
            return json.dumps({
                "action": "apply",
                "status": "gates_failed",
                "skill_path": skill_path,
                "gate_failures": gate_failures,
                "hint": (
                    "Fix the issues and call myco_evolve action='apply' again. "
                    "Common fixes: ensure body is non-empty, don't grow body "
                    "more than 50%, don't include secrets."
                ),
            })

        # Gates passed — compute diff
        diff = diff_variants(original, mutated)

        if dry_run:
            return json.dumps({
                "action": "apply",
                "status": "dry_run_pass",
                "skill_path": skill_path,
                "diff": diff,
                "gates_passed": True,
                "gate_count": 4,
            })

        # Save to skills/.evolved/
        evolved_dir = root / "skills" / ".evolved"
        evolved_dir.mkdir(parents=True, exist_ok=True)

        skill_name = skill_file.stem
        evolved_filename = (
            f"{skill_name}_gen{mutated.generation}_{mutated.content_hash}.md"
        )
        evolved_path = evolved_dir / evolved_filename
        evolved_path.write_text(
            serialize_skill(mutated), encoding="utf-8",
        )

        # Also save export bundle for cross-instance transfer
        canon = _load_canon(root)
        project_name = canon.get("project", {}).get("name", "Myco")
        bundle = export_evolved_skill(
            mutated,
            source_project=project_name,
            evolution_metrics={
                "mutation_prompt": mutation_prompt[:200],
                "gates_passed": True,
                "gate_count": 4,
            },
        )
        bundle_path = evolved_dir / (
            f"{skill_name}_gen{mutated.generation}_{mutated.content_hash}"
            f".bundle.json"
        )
        bundle_path.write_text(
            json.dumps(bundle, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        return json.dumps({
            "action": "apply",
            "status": "evolved",
            "skill_path": skill_path,
            "evolved_file": str(evolved_path.relative_to(root)),
            "bundle_file": str(bundle_path.relative_to(root)),
            "diff": diff,
            "generation": mutated.generation,
            "content_hash": mutated.content_hash,
            "gates_passed": True,
        }, ensure_ascii=False)

    return json.dumps({
        "error": f"Unknown action: {action!r}. Use 'propose' or 'apply'.",
    })


# ---------------------------------------------------------------------------
# Wave E3: Skill Evolution — list + history
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_evolve_list",
    annotations={
        "title": "Myco Evolve List — Skills and Evolution History",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
async def myco_evolve_list(
    project_dir: Optional[str] = None,
) -> str:
    """List available skills and their evolution history.

    WHEN TO CALL:
      (a) Before evolving a skill — see what's available and current state
      (b) After evolving — verify the new variant was saved
      (c) Reviewing evolution health — check generation counts and drift

    Returns each skill's path, metadata, current generation, and a list
    of evolved variants in skills/.evolved/.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with skill list, each including evolution history.
    """
    from myco.evolve import parse_skill

    root = Path(project_dir) if project_dir else _find_project_root()
    root = root.resolve()

    skills_dir = root / "skills"
    if not skills_dir.exists():
        return json.dumps({"skills": [], "message": "No skills/ directory found."})

    # Enumerate current skills (top-level .md files)
    skills = []
    for skill_file in sorted(skills_dir.glob("*.md")):
        variant = parse_skill(skill_file)
        skill_name = skill_file.stem

        # Find evolved variants for this skill
        evolved_dir = skills_dir / ".evolved"
        evolved_variants = []
        if evolved_dir.exists():
            for ef in sorted(evolved_dir.glob(f"{skill_name}_gen*.md")):
                ev = parse_skill(ef)
                evolved_variants.append({
                    "file": str(ef.relative_to(root)),
                    "generation": ev.generation,
                    "content_hash": ev.content_hash,
                    "parent_hash": ev.parent_hash,
                    "body_length": len(ev.body),
                })
            # Also check for bundle files
            for bf in sorted(evolved_dir.glob(f"{skill_name}_gen*.bundle.json")):
                try:
                    bundle = json.loads(bf.read_text(encoding="utf-8"))
                    metrics = bundle.get("metrics", {})
                    for ev_entry in evolved_variants:
                        if bundle.get("content_hash") in ev_entry.get("file", ""):
                            ev_entry["mutation_prompt"] = metrics.get(
                                "mutation_prompt", "",
                            )
                            break
                except Exception:
                    pass

        skills.append({
            "path": str(skill_file.relative_to(root)),
            "name": skill_name,
            "meta": variant.meta,
            "generation": variant.generation,
            "content_hash": variant.content_hash,
            "body_length": len(variant.body),
            "evolved_variants": evolved_variants,
            "evolution_count": len(evolved_variants),
        })

    return json.dumps({
        "skills": skills,
        "total_skills": len(skills),
        "total_evolved_variants": sum(s["evolution_count"] for s in skills),
    }, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mcp.run()
