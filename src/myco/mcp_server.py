#!/usr/bin/env python3
"""
Myco MCP Server — Exposes Myco's knowledge metabolism tools via Model Context Protocol.

When configured in .mcp.json, AI agents (Claude Code, Cursor, etc.) automatically
discover these tools and call them at the right moments — no manual prompting needed.

Tools:
    myco_immune       — Run 29-dimensional consistency checks (L0-L28)
    myco_pulse     — Quick overview of knowledge system health
    myco_sense     — Search across wiki/docs/MYCO.md knowledge base
    myco_trace        — Append friction/reflection entries to log.md
    myco_reflect    — Trigger session-end reflection prompts
    myco_eat        — Capture a chunk of content as a raw atomic note
    myco_digest     — Move a note through the lifecycle (raw→…→excreted)
    myco_observe       — Read-only lens on notes/ (list or single note)
    myco_hunger     — Metabolic dashboard with actionable signals
    myco_condense   — Synthesize notes into extracted knowledge (Wave 43)
    myco_expand — Reverse a compression operation (Wave 43)
    myco_prune      — Auto-excrete dead-knowledge notes (Wave 43)
    myco_absorb      — Ingest external content with provenance (Wave 43)
    myco_forage     — Manage external source material (Wave 43)
    myco_mycelium      — Structural link graph analysis (Wave 47)
    myco_colony     — Semantic cohort intelligence (Wave 48)
    myco_memory    — Session memory search (Wave 52)
    myco_evolve     — Agent-driven skill self-improvement (Wave E3)
    myco_evolve_list — List skills and evolution history (Wave E3)

Transport: stdio (local subprocess of the AI client)
"""
# --- Mycelium references ---
# Protocol:    docs/agent_protocol.md (tool trigger conditions, anti-patterns)
# MCP config:  .mcp.json (client-side wiring)
# Skills:      skills/ (skill resolution for evolved tools)

import functools
import json
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
    """Find Myco project root. Priority: MYCO_ROOT env var > walk-up search.

    MYCO_ROOT allows global Myco: install once, connect from any project.

    Wave 56 zero-touch: if no _canon.yaml is found in the walk-up chain,
    trigger first-contact auto-seed so the user never has to type
    `myco init`. Opt-out via MYCO_NO_AUTOSEED=1.
    """
    import os
    myco_root = os.environ.get("MYCO_ROOT")
    if myco_root:
        p = Path(myco_root).resolve()
        if (p / "_canon.yaml").exists():
            return p
    from myco.project import find_project_root
    root = find_project_root(strict=False)
    # First-contact auto-seed: if this dir isn't a Myco project yet,
    # silently seed L1 defaults so any MCP tool call works immediately.
    if os.environ.get("MYCO_NO_AUTOSEED") != "1" and not (root / "_canon.yaml").exists():
        try:
            from myco.inoculate import first_contact_seed
            first_contact_seed(root, silent=True)
        except Exception:
            pass
    return root


def _get_root(project_dir: Optional[str] = None) -> Path:
    """Resolve project root from project_dir parameter or auto-discovery.

    Consolidates the repeated pattern: Path(project_dir) if project_dir else _find_project_root()
    """
    return Path(project_dir).resolve() if project_dir else _find_project_root()


def _check_canon(root: Path) -> tuple[dict, Optional[dict]]:
    """Load _canon.yaml and return (canon_dict, error_dict_or_None).

    Consolidates the repeated error pattern:
        canon = _load_canon(root)
        if "error" in canon:
            return json.dumps({"error": canon["error"]}, indent=2)

    Returns:
        (canon_dict, None) if successful
        ({}, {"error": "..."}) if _canon.yaml not found or invalid
    """
    canon = _load_canon(root)
    if "error" in canon:
        return {}, canon
    return canon, None


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
        # Check if boot ritual was executed this session.
        # If boot_brief is older than 2 hours, Agent likely hasn't run
        # myco_hunger(execute=true) this session → nag.
        import time as _time
        boot_stale = True
        if brief.exists():
            age_seconds = _time.time() - brief.stat().st_mtime
            boot_stale = age_seconds > 7200  # 2 hours

        result = {
            "raw_count": raw,
            "signals_count": signals_count,
            "top_signal": top_signal,
        }
        if boot_stale:
            result["WARNING"] = (
                "Boot ritual not executed this session! "
                "Call myco_hunger(execute=true) IMMEDIATELY — "
                "this is the FIRST action every session per MYCO.md."
            )
        return result
    except Exception:
        return {"raw_count": -1, "signals_count": -1, "top_signal": "error"}


def _compute_claude_hint(sidecar: dict, tool_name: str, root: Path) -> Optional[str]:
    """Wave 56: next-action hint for the Agent.

    Zero-forget layer — small rules produce a directive the Agent can
    follow without reasoning from scratch. Returns None if no hint.
    """
    try:
        # Highest priority: boot ritual missed.
        if sidecar.get("WARNING"):
            return "Call myco_hunger(execute=true) NOW — boot ritual not executed this session."
        raw = sidecar.get("raw_count", 0)
        # Post-eat: tell Agent to digest soon, not immediately.
        if tool_name == "myco_eat":
            return (
                "Note captured. When the conversation reaches a natural break, "
                "call myco_digest to move raw notes toward extracted/integrated."
            )
        if tool_name == "myco_digest":
            return "After digest, call myco_immune to verify nutrient placement was valid."
        if tool_name == "myco_scent":
            return "Scent returned candidate sources — call myco_eat on the most relevant chunk."
        if tool_name == "myco_hunger":
            if raw > 5:
                return f"{raw} raw notes pending — run myco_digest on the oldest batch."
            return None
        # Global fallback: raw notes backlog.
        if raw >= 8:
            return f"Backlog: {raw} raw notes. Consider running myco_digest soon."
        # Freshness debt hint — cheap heuristic: check recent notes count.
        notes_dir = root / "notes"
        if notes_dir.is_dir():
            stale = sum(1 for f in notes_dir.glob("n_*.md")
                        if "quarantine_reason:" in f.read_text(encoding="utf-8", errors="replace")[:400])
            if stale >= 3:
                return f"{stale} quarantined notes — run myco_verify to revalidate."
    except Exception:
        return None
    return None


def _inject_sidecar(response_str: str, root: Path, tool_name: str = "") -> str:
    """Inject hunger sidecar + claude_hint into any JSON response."""
    try:
        data = json.loads(response_str)
        sidecar = _compute_sidecar(root)
        hint = _compute_claude_hint(sidecar, tool_name, root)
        if isinstance(data, dict):
            data["_myco_sidecar"] = sidecar
            if hint and "claude_hint" not in data:
                data["claude_hint"] = hint
            return json.dumps(data, indent=2, ensure_ascii=False)
        if isinstance(data, list):
            # Wrap bare lists so sidecar can be attached
            wrapped = {"items": data, "_myco_sidecar": sidecar}
            if hint:
                wrapped["claude_hint"] = hint
            return json.dumps(wrapped, indent=2, ensure_ascii=False)
    except (json.JSONDecodeError, TypeError):
        pass
    return response_str


def _with_sidecar(fn):
    """Decorator: inject hunger sidecar into every MCP tool response.

    Wave B2+: push-mode substrate health — Agent always sees it without
    explicitly calling myco_hunger. Applied to ALL 25 MCP tools.
    """
    @functools.wraps(fn)
    async def wrapper(*args, **kwargs):
        result = await fn(*args, **kwargs)
        # Resolve project root from the project_dir kwarg (present on every tool)
        project_dir = kwargs.get("project_dir")
        if project_dir is None:
            # Also check positional args — but project_dir is always a kwarg
            # in MCP tool signatures. Fall back to auto-detection.
            pass
        try:
            root = Path(project_dir).resolve() if project_dir else _find_project_root().resolve()
            tool_name = getattr(fn, "__name__", "")
            return _inject_sidecar(result, root, tool_name=tool_name)
        except Exception:
            return result
    return wrapper


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


def _extract_title(path: Path) -> str:
    """Extract the first H1/H2 heading from a markdown file, or return stem."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line.lstrip("# ").strip()
                if line.startswith("## "):
                    return line.lstrip("# ").strip()
        return path.stem
    except Exception:
        return path.stem


def _doc_lifecycle_status(content: str) -> str:
    """Extract [ACTIVE]/[COMPILED]/[SUPERSEDED] from doc content, or 'unknown'."""
    for tag in ("ACTIVE", "COMPILED", "SUPERSEDED", "COMPILED→Myco"):
        if f"[{tag}]" in content:
            return tag
    return "unknown"


def compute_interconnection_map(root: Path) -> dict:
    """Build a cross-layer interconnection map of the entire project.

    Scans ALL project files, extracts section-level concepts, and builds
    a graph of which concepts appear in which (file, section, layer) tuples.
    This enables the Agent to see cross-layer relationships and detect
    potential inconsistencies when a concept changes in one layer.

    Three layers:
      - knowledge: wiki/*.md, notes/n_*.md
      - engineering: src/**/*.py, scripts/*.py, .claude/**
      - document: docs/**/*.md, *.md (top-level), README*

    Section extraction:
      - Markdown: split by H2/H3 headings
      - Python: split by class/function definitions

    Concept extraction:
      - Extract significant terms (2+ chars, not stopwords) from each section
      - Match terms across layers to find cross-layer connections

    Craft: docs/primordia/universal_interconnection_craft_2026-04-14.md

    Returns:
        dict with 'concept_map', 'cross_layer_summary', and 'interconnection_hint'.
    """
    import re as _re

    # --- Layer classification ---
    def _classify_layer(rel_path: str) -> str:
        """Classify a file into knowledge / engineering / document layer."""
        if rel_path.startswith("wiki/") or rel_path.startswith("notes/"):
            return "knowledge"
        if (rel_path.startswith("src/") or rel_path.startswith("scripts/")
                or rel_path.startswith(".claude/")):
            return "engineering"
        # docs/, top-level .md, README*
        return "document"

    # --- Section extraction ---
    _H23_RE = _re.compile(r"^(#{2,3})\s+(.+)", _re.MULTILINE)
    _PYDEF_RE = _re.compile(r"^(class |def )(\w+)", _re.MULTILINE)

    def _extract_sections_md(content: str, rel_path: str):
        """Extract sections from markdown. Returns list of (section_id, heading)."""
        sections = []
        matches = list(_H23_RE.finditer(content))
        if not matches:
            return [(rel_path, _extract_title_from_content(content))]
        for m in matches:
            level = len(m.group(1))
            heading = m.group(2).strip()
            section_id = f"{rel_path}#{'##' if level == 2 else '###'} {heading}"
            sections.append((section_id, heading))
        return sections if sections else [(rel_path, rel_path)]

    def _extract_sections_py(content: str, rel_path: str):
        """Extract sections from Python. Returns list of (section_id, name)."""
        sections = []
        for m in _PYDEF_RE.finditer(content):
            kind = "class" if m.group(1).startswith("class") else "def"
            name = m.group(2)
            section_id = f"{rel_path}#{kind} {name}"
            sections.append((section_id, name))
        return sections if sections else [(rel_path, rel_path)]

    def _extract_title_from_content(content: str) -> str:
        for line in content.split("\n")[:10]:
            line = line.strip()
            if line.startswith("# "):
                return line.lstrip("# ").strip()
        return ""

    # --- Concept extraction ---
    # Key terms from _canon.yaml concepts + wiki page titles + function names
    # form the concept vocabulary. Then scan all sections for these terms.

    # Step 1: Build concept vocabulary from wiki titles and key project terms
    concept_vocab = {}  # term_lower → canonical_name

    wiki_dir = root / "wiki"
    if wiki_dir.exists():
        for p in sorted(wiki_dir.glob("*.md")):
            if p.name.startswith("_"):
                continue
            title = _extract_title(p)
            stem = p.stem.replace("-", " ").replace("_", " ")
            # Register both title words and stem words
            for term in [stem, title.lower()]:
                if len(term) > 3:
                    concept_vocab[term.lower()] = f"wiki:{p.stem}"

    # Step 2: Scan all project files and extract sections + concept mentions
    _SKIP_DIRS = {".git", "node_modules", "__pycache__", ".myco_state",
                  ".pytest_cache", ".eggs", "forage"}
    _SCAN_EXTENSIONS = {".md", ".py", ".yaml", ".yml"}

    # concept_name → list of {file, section, layer, heading}
    concept_locations = {}
    # layer → list of {file, section_count, concepts_found}
    layer_stats = {"knowledge": [], "engineering": [], "document": []}

    import os as _os
    for dirpath, dirnames, filenames in _os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS
                       and not d.endswith(".egg-info")]
        for fname in filenames:
            _, ext = _os.path.splitext(fname)
            if ext not in _SCAN_EXTENSIONS:
                continue
            full_path = _os.path.join(dirpath, fname)
            rel = _os.path.relpath(full_path, root).replace("\\", "/")
            # Skip test files, primordia archive, notes (too noisy)
            if any(rel.startswith(p) for p in (
                "tests/", "docs/primordia/archive/", "examples/",
            )):
                continue
            content = _read_file(Path(full_path))
            if not content:
                continue

            layer = _classify_layer(rel)

            # Extract sections
            if ext == ".py":
                sections = _extract_sections_py(content, rel)
            elif ext == ".md":
                sections = _extract_sections_md(content, rel)
            else:
                sections = [(rel, rel)]

            # Find concept mentions in this file
            content_lower = content.lower()
            file_concepts = set()
            for term, concept_name in concept_vocab.items():
                if term in content_lower:
                    file_concepts.add(concept_name)
                    if concept_name not in concept_locations:
                        concept_locations[concept_name] = []
                    concept_locations[concept_name].append({
                        "file": rel,
                        "layer": layer,
                        "section_count": len(sections),
                    })

            layer_stats[layer].append({
                "file": rel,
                "section_count": len(sections),
                "concepts_found": len(file_concepts),
            })

    # Step 3: Identify cross-layer concepts and isolated concepts
    cross_layer_concepts = []
    single_layer_concepts = []
    for concept_name, locations in concept_locations.items():
        layers_present = set(loc["layer"] for loc in locations)
        entry = {
            "concept": concept_name,
            "layers": sorted(layers_present),
            "file_count": len(locations),
            "files": sorted(set(loc["file"] for loc in locations))[:8],  # cap at 8
        }
        if len(layers_present) >= 2:
            cross_layer_concepts.append(entry)
        else:
            single_layer_concepts.append(entry)

    # Sort by cross-layer breadth, then file count
    cross_layer_concepts.sort(key=lambda x: (-len(x["layers"]), -x["file_count"]))
    single_layer_concepts.sort(key=lambda x: -x["file_count"])

    # Step 4: Compute health metrics
    total_concepts = len(concept_locations)
    cross_count = len(cross_layer_concepts)
    isolated_count = len(single_layer_concepts)
    connectivity_ratio = cross_count / max(total_concepts, 1)

    return {
        "cross_layer_concepts": cross_layer_concepts[:20],  # top 20
        "single_layer_concepts": single_layer_concepts[:10],  # top 10 isolated
        "health": {
            "total_concepts": total_concepts,
            "cross_layer_count": cross_count,
            "single_layer_count": isolated_count,
            "connectivity_ratio": round(connectivity_ratio, 2),
            "layer_file_counts": {
                layer: len(files) for layer, files in layer_stats.items()
            },
        },
        "interconnection_hint": (
            "Above shows the cross-layer interconnection map of the project. "
            "cross_layer_concepts are well-connected (appear in 2+ layers). "
            "single_layer_concepts are isolated in one layer — consider whether "
            "they should be referenced in other layers. When modifying a concept, "
            "check its file list to see all places that may need updating."
        ),
    }


def compute_synaptic_context(root: Path) -> dict:
    """Build the wiki inter-connection map — which pages link to which.

    Reuses mycelium.build_link_graph() but filters to wiki↔wiki subgraph.
    No ranking, no recommendations — Agent applies its own judgment.

    Craft: docs/primordia/synaptogenesis_craft_2026-04-14.md

    Returns:
        dict with wiki_connectivity (per-page links) and health summary.
    """
    try:
        from myco.mycelium import build_link_graph
    except ImportError:
        return {"error": "mycelium module not available"}

    graph = build_link_graph(root)

    wiki_pages = [n for n in graph if n.startswith("wiki/") and n.endswith(".md")]
    connectivity = []
    isolated_count = 0

    for page in sorted(wiki_pages):
        data = graph.get(page, {"forward": [], "backlinks": []})
        # Filter to only wiki↔wiki links (not notes or docs)
        outbound_wiki = [t for t in data["forward"] if t.startswith("wiki/") and t != page]
        inbound_wiki = [s for s in data["backlinks"] if s.startswith("wiki/") and s != page]
        # Also track non-wiki connections for full picture
        inbound_notes = [s for s in data["backlinks"] if s.startswith("notes/")]
        inbound_docs = [s for s in data["backlinks"] if s.startswith("docs/")]

        is_isolated = len(outbound_wiki) == 0 and len(inbound_wiki) == 0
        if is_isolated:
            isolated_count += 1

        connectivity.append({
            "page": page,
            "outbound_wiki": outbound_wiki,
            "inbound_wiki": inbound_wiki,
            "inbound_notes": len(inbound_notes),
            "inbound_docs": len(inbound_docs),
            "isolated": is_isolated,
        })

    total_wiki = len(wiki_pages)
    return {
        "wiki_connectivity": connectivity,
        "health": {
            "total_wiki_pages": total_wiki,
            "isolated_wiki_pages": isolated_count,
            "connectivity_ratio": round(
                (total_wiki - isolated_count) / total_wiki, 2
            ) if total_wiki > 0 else 0,
        },
        "synaptogenesis_hint": (
            "Above shows how wiki pages connect to each other. "
            "When writing to a wiki page, consider adding cross-references "
            "to related pages (e.g., 'see also wiki/X.md'). "
            "Isolated pages represent knowledge islands — connect them."
        ),
    }


def compute_perfusion(root: Path) -> dict:
    """Build a perfusion map — lightweight catalog of available knowledge tissue.

    Pure filesystem metadata collection. No NLP, no ranking, no filtering.
    The Agent applies its own intelligence to decide what to read.

    Craft: docs/primordia/perfusion_system_craft_2026-04-14.md

    Returns:
        dict with 'wiki_pages' and 'docs_active' lists.
    """
    wiki_dir = root / "wiki"
    docs_current = root / "docs" / "current"

    wiki_pages = []
    if wiki_dir.exists():
        for p in sorted(wiki_dir.glob("*.md")):
            if p.name.startswith("_"):
                continue  # skip internal/test files
            stat = p.stat()
            wiki_pages.append({
                "path": f"wiki/{p.name}",
                "title": _extract_title(p),
                "last_modified": datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d"),
                "size_kb": round(stat.st_size / 1024, 1),
            })

    docs_active = []
    if docs_current.exists():
        for p in sorted(docs_current.glob("*.md")):
            content = _read_file(p)
            if not content:
                continue
            status = _doc_lifecycle_status(content)
            if status not in ("ACTIVE",):
                continue  # only surface active docs
            stat = p.stat()
            docs_active.append({
                "path": f"docs/current/{p.name}",
                "title": _extract_title(p),
                "status": status,
                "last_modified": datetime.datetime.fromtimestamp(
                    stat.st_mtime
                ).strftime("%Y-%m-%d"),
            })

    return {
        "wiki_pages": wiki_pages,
        "docs_active": docs_active,
        "perfusion_hint": (
            "Above is the full catalog of available knowledge tissue. "
            "Based on your current task, decide which pages to read before proceeding. "
            "Use Read tool or myco_sense to access specific content."
        ),
    }


# ---------------------------------------------------------------------------
# Tool: myco_immune
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_immune",
    annotations={
        "title": "Myco Immune — 29-Dimension Consistency Check",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_immune(
    project_dir: Optional[str] = None,
    quick: bool = False,
    fix: bool = False,
) -> str:
    """Check the project for contradictions, stale references, and knowledge drift.

    Auto-invoke when: the user says "check", "verify", "lint", "are there
    inconsistencies", "did I break anything", or at the end of any session that
    modified wiki/, docs/, MYCO.md, _canon.yaml, or notes/. Also run after any
    milestone retrospective retrospective or before commits that touch multiple knowledge files.

    This is the 29-dimensional immune system of the knowledge substrate. It
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
    root = _get_root(project_dir)

    canon, err = _check_canon(root)
    if err:
        return json.dumps(err, indent=2)

    # Import the dispatch SSoT directly — Wave 38 D9: mcp_server.py
    # MUST NOT maintain a duplicate checks list. len(FULL_CHECKS) is the
    # canonical LINT_DIMENSION_COUNT (Wave 38 D1) and any local cache here
    # would silently drop newly added dimensions (the very bug Wave 38 fixes).
    from myco.immune import FULL_CHECKS, QUICK_CHECKS

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
        "mode": "quick (L0-L3)" if quick else "full (L0-L28)",
        "total_issues": total_issues,
        "all_passed": total_issues == 0,
        "checks": results,
    }

    # Auto-fix if requested
    if fix and total_issues > 0:
        try:
            from myco.immune import auto_fix_issues
            all_issues = []
            for r in results:
                for iss in r.get("issues", []):
                    all_issues.append((
                        iss["level"], iss["severity"],
                        iss["file"], iss["message"]
                    ))
            fixed_count = auto_fix_issues(root, all_issues, canon)
            report["auto_fixed"] = fixed_count
            # Re-check after fix
            recheck_issues = 0
            for name, checker in checks:
                recheck_issues += len(checker(canon, root))
            report["total_issues_after_fix"] = recheck_issues
            total_issues = recheck_issues
        except Exception as e:
            report["auto_fix_error"] = str(e)

    if total_issues == 0:
        report["summary"] = "✅ ALL CHECKS PASSED — knowledge system is healthy."
    else:
        report["summary"] = (
            f"⚠ {total_issues} issue(s) found. "
            "Review the issues list and fix inconsistencies."
        )

    return json.dumps(report, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_pulse
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_pulse",
    annotations={
        "title": "Myco Pulse — Knowledge System Overview",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_pulse(
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
            (`myco_pulse` → `myco_hunger`) into one atomic call so that
            contract_drift + raw_backlog reflex signals surface before any
            task work. **Setting `include_hunger=False` while raw_backlog
            is above threshold is a W1 autopilot violation** — see
            docs/primordia/boot_reflex_arc_craft_2026-04-11.md.

    Returns:
        JSON overview of knowledge system state.
    """
    root = _get_root(project_dir)

    canon, err = _check_canon(root)
    if err:
        return json.dumps(err, indent=2)

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
            "Run myco_immune to check for inconsistencies. "
            "Use myco_sense to find specific knowledge. "
            "Use myco_trace to record friction or reflections."
        ),
    }

    # Perfusion: attach full knowledge catalog so Agent can decide what to read
    try:
        status["perfusion"] = compute_perfusion(root)
    except Exception as e:
        status["perfusion"] = {"error": str(e)}

    # Wave 46 (万物互联): cross-layer interconnection map — shows which
    # concepts span multiple layers so Agent can see the full dependency web.
    try:
        status["interconnection"] = compute_interconnection_map(root)
    except Exception as e:
        status["interconnection"] = {"error": str(e)}

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
# Tool: myco_sense
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_sense",
    annotations={
        "title": "Myco Sense — Knowledge Base Lookup",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_sense(
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
    root = _get_root(project_dir)

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

    return json.dumps(result, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_trace
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_trace",
    annotations={
        "title": "Myco Trace — Record Friction or Reflection",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_trace(
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

    root = _get_root(project_dir)
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
        "title": "Myco Reflect — Session-End Prompts",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_reflect(
    project_dir: Optional[str] = None,
) -> str:
    """Ask "what should the knowledge system itself improve?" at session end.

    Auto-invoke when: the user signals a session is wrapping up ("let's stop
    here", "end session", "that's enough for today"), or after any retrospective
    trigger like "what did we learn", or whenever an operation finishes cleanly
    and ≥3 log entries were added during the session.

    Returns session reflection prompts derived from recent log entries, lint
    results, and knowledge gaps. The agent should answer the prompts and log
    the reflection via myco_trace. session reflection is how the substrate evolves its own
    rules — skipping it is how drift compounds.

    Args:
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        Structured reflection prompts based on current project state.
    """
    root = _get_root(project_dir)

    canon, err = _check_canon(root)
    if err:
        return json.dumps(err, indent=2)

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
    from myco.immune import (
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
        from myco.mycelium import build_link_graph, find_orphans
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
            "Answer these prompts briefly, then call myco_trace with "
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
@_with_sidecar
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

    root = _get_root(project_dir)

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

    # Reflex chain (Wave 57 Wave 2): detect near-duplicate older notes and
    # surface them as supersede candidates. Non-destructive — the Agent
    # decides whether to apply.
    supersede_info: Dict[str, Any] = {"supersedes": [], "errors": []}
    try:
        from myco.reflex import detect_supersede_candidates
        supersede_info = detect_supersede_candidates(root, path.stem)
    except Exception as e:
        supersede_info = {"supersedes": [], "errors": [f"reflex: {e}"]}

    response = {
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
    }
    if supersede_info.get("supersedes"):
        old_ids = [c["note_id"] for c in supersede_info["supersedes"]]
        response["reflex"] = {
            "chain": "eat_to_supersede",
            "candidates": supersede_info["supersedes"],
            "suggested_call": (
                f"myco_supersede(new_note_id='{path.stem}', "
                f"old_note_ids={old_ids})"
            ),
        }
    return json.dumps(response, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_digest  —  lifecycle transition + reflection prompts
# ---------------------------------------------------------------------------

_DIGEST_PROMPTS = [
    "What is the ONE core claim or insight in this note? (one sentence)",
    "Which file should this claim live in? (wiki/*.md / docs/*.md / MYCO.md)",
    "Write the claim into that file with a <!-- nutrient-from: NOTE_ID --> marker, "
    "then call: myco_digest(note_id, to_status='extracted', "
    "absorption_site='<path>', nutrient='<claim>')",
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
@_with_sidecar
async def myco_digest(
    note_id: Optional[str] = None,
    to_status: Optional[str] = None,
    excrete_reason: Optional[str] = None,
    absorption_site: Optional[str] = None,
    nutrient: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Move a note along the digestive lifecycle with proof-of-work gates.

    Contract: docs/agent_protocol.md §2.2. L10 + L24 enforce compliance.

    == REAL DIGESTION WORKFLOW (4 phases) ==

    Phase 1 — CLAIM: call digest(note_id) with no to_status.
      Returns the note body + structured prompts. Agent reads the content,
      identifies the core claim, decides which wiki/doc file it belongs in.
      Status: raw → digesting.

    Phase 2 — PLACE: Agent writes the claim into the target file.
      Add a <!-- nutrient-from: NOTE_ID --> marker near the extracted content.
      This step is done by the Agent using Write/Edit tools, NOT by digest.

    Phase 3 — SEAL: call digest(note_id, to_status="extracted",
      absorption_site="wiki/xxx.md", nutrient="the claim").
      Tool VERIFIES: target file exists AND contains the source marker.
      Only then does the status transition to extracted.
      If verification fails → error, no status change.

    Phase 4 — VERIFY: immune L24 periodically scans all extracted/integrated
      notes to catch "phantom digestion" (status changed without real extraction).

    == GATE RULES ==
    - to_status="extracted" or "integrated" REQUIRES absorption_site +
      nutrient. Without them → error.
    - to_status="excreted" REQUIRES excrete_reason. No proof needed.
    - to_status="digesting" or "raw" → free transition.
    - Backfill mode: if note is already extracted/integrated and you just
      want to add missing proof fields, pass absorption_site + nutrient
      without to_status.

    ANTI-PATTERNS (do NOT do these):
      - Calling to_status='extracted' without absorption_site (BLOCKED)
      - Manually editing notes/*.md to change status
      - Skipping Phase 2 (actually writing the claim) before Phase 3

    Args:
        note_id: Target note id (e.g. 'n_20260410T143027_7f3a'). If None,
                 picks the oldest raw note in the queue.
        to_status: Explicit transition target.
        excrete_reason: If set, marks the note as excreted with this reason.
        absorption_site: Relative path to the file where the claim was written.
                          REQUIRED when to_status is 'extracted' or 'integrated'.
        nutrient: One-sentence summary of what was extracted.
                           REQUIRED when to_status is 'extracted' or 'integrated'.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with note id, new status, body preview, and reflection prompts.
    """
    from myco.notes import (
        read_note, update_note, list_notes, id_to_filename, VALID_STATUSES,
        verify_absorption, ABSORPTION_REQUIRED_STATUSES,
    )

    root = _get_root(project_dir)

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

    # Backfill mode: add extraction proof to an already-extracted note
    if absorption_site and not to_status and not excrete_reason:
        ok, msg = verify_absorption(root, target.stem, absorption_site)
        if not ok:
            return json.dumps({"error": msg, "gate": "extraction_verification"})
        try:
            update_note(
                target,
                absorption_site=absorption_site,
                nutrient=nutrient or "",
                absorbed_at=datetime.now().isoformat(),
            )
        except Exception as e:
            return json.dumps({"error": f"Backfill failed: {e}"})
        return json.dumps({
            "status": "ok",
            "id": target.stem,
            "mode": "backfill",
            "absorption_site": absorption_site,
            "nutrient": nutrient or "",
            "message": "Extraction proof added to existing note.",
        }, ensure_ascii=False)

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

    # Explicit transition with extraction gate
    if to_status:
        if to_status not in VALID_STATUSES:
            return json.dumps({
                "error": f"Invalid to_status {to_status!r}. Expected: {list(VALID_STATUSES)}",
            })

        # GATE: extracted/integrated require proof-of-work
        if to_status in ABSORPTION_REQUIRED_STATUSES:
            if not absorption_site or not nutrient:
                return json.dumps({
                    "error": (
                        f"Transition to '{to_status}' requires absorption_site "
                        f"and nutrient. You must first write the note's "
                        f"core claim into a wiki/doc file with a "
                        f"'<!-- nutrient-from: {target.stem} -->' marker, then pass "
                        f"absorption_site='<relative_path>' and "
                        f"nutrient='<one sentence claim>'."
                    ),
                    "gate": "absorption_proof_required",
                    "hint": _DIGEST_PROMPTS,
                })
            # Verify the extraction actually happened
            ok, msg = verify_absorption(root, target.stem, absorption_site)
            if not ok:
                return json.dumps({
                    "error": msg,
                    "gate": "extraction_verification",
                })

        try:
            update_fields = dict(status=to_status, _increment_digest=True)
            if absorption_site:
                update_fields["absorption_site"] = absorption_site
                update_fields["nutrient"] = nutrient or ""
                update_fields["absorbed_at"] = datetime.now().isoformat()
            update_note(target, **update_fields)
        except Exception as e:
            return json.dumps({"error": f"Transition failed: {e}"})

        # Synaptogenesis: post-seal weaving hint — show the absorption
        # site's current connectivity so Agent can check cross-links.
        weaving_hint = None
        if absorption_site and to_status in ABSORPTION_REQUIRED_STATUSES:
            try:
                synaptic = compute_synaptic_context(root)
                site_data = next(
                    (p for p in synaptic.get("wiki_connectivity", [])
                     if p["page"] == absorption_site),
                    None,
                )
                if site_data:
                    if site_data["isolated"]:
                        weaving_hint = (
                            f"⚠️ '{absorption_site}' is currently ISOLATED — "
                            f"no cross-references to/from other wiki pages. "
                            f"Consider adding 'See also: [page](wiki/xxx.md)' "
                            f"links to connect it to the knowledge network."
                        )
                    else:
                        weaving_hint = (
                            f"'{absorption_site}' connects to: "
                            f"outbound={site_data['outbound_wiki']}, "
                            f"inbound={site_data['inbound_wiki']}. "
                            f"Verify these connections still make sense."
                        )
            except Exception:
                pass  # best-effort

        return json.dumps({
            "status": "ok",
            "id": target.stem,
            "transition": f"{meta.get('status')} → {to_status}",
            **({"absorption_site": absorption_site} if absorption_site else {}),
            **({"nutrient": nutrient} if nutrient else {}),
            **({"weaving_hint": weaving_hint} if weaving_hint else {}),
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

    # Synaptogenesis: provide wiki interconnection map so Agent considers
    # cross-linking when deciding where to place the nutrient.
    synaptic = {}
    try:
        synaptic = compute_synaptic_context(root)
    except Exception:
        pass  # best-effort

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
            "1. Identify the core nutrient (claim/insight). "
            "2. Write it into the absorption site (wiki/docs file) with "
            "a <!-- nutrient-from: NOTE_ID --> marker. "
            "3. When writing, ADD cross-references to related wiki pages "
            "(check synaptic_context below for current connections). "
            "4. Seal: myco_digest(note_id, to_status='extracted', "
            "absorption_site='<path>', nutrient='<one sentence>')."
        ),
        "synaptic_context": synaptic,
    }, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Tool: myco_observe  —  read-only lens on notes/
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_observe",
    annotations={
        "title": "Myco Observe — List or Read Atomic Notes",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_observe(
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
          myco_observe status='raw' or 'digesting' shows the active queue.
      (c) Starting a new task on a known topic → myco_observe with a
          specific note_id or status filter to rehydrate context.
      (d) Phase ② prep → myco_observe status='raw' filters to notes tagged
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

    root = _get_root(project_dir)

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
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
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

    root = _get_root(project_dir)

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
                    from myco.condense_cmd import run_compress
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
                elif verb == "auto_link_orphans":
                    # Retroactively link orphan notes to the mycelium
                    from myco.mycelium import build_link_graph, find_orphans
                    from myco.notes import _auto_link_note
                    import yaml as _yaml
                    graph = build_link_graph(root)
                    orphans = find_orphans(graph)
                    linked = 0
                    for orphan_rel in orphans:
                        if not orphan_rel.startswith("notes/"):
                            continue
                        orphan_path = root / orphan_rel
                        if not orphan_path.exists():
                            continue
                        try:
                            oc = orphan_path.read_text(encoding="utf-8")
                            parts = oc.split("---", 2)
                            if len(parts) >= 3:
                                fm = _yaml.safe_load(parts[1])
                                tags = fm.get("tags", [])
                                title = fm.get("title", orphan_path.stem)
                                _auto_link_note(root, orphan_path, tags, title)
                                linked += 1
                        except Exception:
                            continue
                    exec_result["status"] = f"ok: linked {linked} orphan notes"
                elif verb == "evolve":
                    skill_file = action.get("args", {}).get("skill", "")
                    exec_result["status"] = (
                        f"advisory (skill '{skill_file}' needs evolution — "
                        f"call myco_evolve(skill='{skill_file}') to propose mutation)"
                    )
                elif verb == "inlet":
                    exec_result["status"] = "advisory (inlet needs human/agent decision)"
                else:
                    exec_result["status"] = f"skipped (unknown verb: {verb})"
            except Exception as e:
                exec_result["status"] = f"error: {e}"
            execution_results.append(exec_result)
        result["execution_results"] = execution_results

    # Perfusion: attach knowledge catalog + task context for Agent's own
    # relevance judgment. No tool-side filtering — Agent decides what matters.
    try:
        perfusion = compute_perfusion(root)
        # Also include raw task queue text so Agent can correlate
        canon = _load_canon(root)
        entry_point = canon.get("system", {}).get("entry_point", "MYCO.md")
        myco_path = root / entry_point
        task_text = ""
        if myco_path.exists():
            mc = _read_file(myco_path)
            if mc:
                # Extract task table section
                task_matches = re.findall(
                    r"\|\s*\d+\s*\|\s*[^\|]+\|\s*[^\|]+\|[^\n]*", mc
                )
                task_text = "\n".join(task_matches[:10])
        perfusion["current_tasks_raw"] = task_text or "(no task queue found)"
        result["perfusion"] = perfusion
    except Exception as e:
        result["perfusion"] = {"error": str(e)}

    # Wave 46 (万物互联): cross-layer interconnection map
    try:
        result["interconnection"] = compute_interconnection_map(root)
    except Exception as e:
        result["interconnection"] = {"error": str(e)}

    # Sprint Pipeline hint (absorbed from gstack): tell Agent where they are
    # in the development loop based on current substrate state.
    has_gaps = any("inlet_ripe" in s or "cold_start" in s or "cohort_staleness" in s
                    for s in report.signals)
    if report.signals and any("healthy" in s for s in report.signals):
        result["pipeline_hint"] = "Build — substrate healthy, proceed with task work"
    elif report.actions:
        result["pipeline_hint"] = "Think — substrate needs attention, execute actions first"
    elif has_gaps:
        result["pipeline_hint"] = "Discover — knowledge gaps detected, use myco_colony(action='gaps') then myco_absorb to ingest"
    else:
        result["pipeline_hint"] = "Build — signals advisory only, proceed with caution"
    result["pipeline_ref"] = "skills/sprint-pipeline.md"

    # Reflex chain (Wave 57 Wave 2): hunger → scent.
    # Surface concrete myco_scent(topic=…) calls derived from scent-verb
    # actions in the hunger report. Zero side-effects; Agent executes.
    try:
        from myco.reflex import hunger_to_scent
        reflex_payload = hunger_to_scent(root, report, execute=False)
        if reflex_payload.get("scents"):
            result["reflex_scents"] = reflex_payload["scents"]
    except Exception as e:
        result["reflex_scents_error"] = str(e)

    # Wave 58 (Wave 3): auto-verify batch. Surface up to 5 oldest
    # time_sensitive notes past their freshness window so the Agent can
    # verify them in a single pass. Computed cheaply from disk.
    try:
        from myco.notes import read_note
        stale_batch: List[Dict[str, Any]] = []
        now_v = datetime.now()
        thresholds = {"time_sensitive": 90, "live": 7}
        for p in sorted((root / "notes").glob("n_*.md")):
            try:
                meta, _ = read_note(p)
            except Exception:
                continue
            if meta.get("status") not in ("extracted", "integrated"):
                continue
            fresh = meta.get("freshness", "time_sensitive")
            if fresh == "static":
                continue
            lv = meta.get("last_verified") or meta.get("created")
            try:
                lv_dt = datetime.strptime(str(lv), "%Y-%m-%dT%H:%M:%S")
            except Exception:
                continue
            age = (now_v - lv_dt).days
            thr = thresholds.get(fresh, 90)
            if age > thr:
                stale_batch.append({
                    "note_id": meta.get("id"),
                    "freshness": fresh,
                    "age_days": age,
                    "threshold_days": thr,
                    "suggested_call": f"myco_verify(note_id='{meta.get('id')}')",
                })
            if len(stale_batch) >= 5:
                break
        if stale_batch:
            result["verify_batch"] = stale_batch
    except Exception as e:
        result["verify_batch_error"] = str(e)

    # Refresh boot brief so sidecar knows hunger was run this session
    try:
        from myco.notes import write_boot_brief
        write_boot_brief(root, report)
    except Exception:
        pass  # best-effort

    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_condense  —  forward compression synthesis
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_condense",
    annotations={
        "title": "Myco Condense — Synthesize Notes into Extracted Knowledge",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_condense(
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

    root = _get_root(project_dir)

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

    from myco.condense_cmd import run_compress
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
# Tool: myco_expand  —  reverse compression
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_expand",
    annotations={
        "title": "Myco Expand — Reverse a Compression Operation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_expand(
    output_id: str,
    project_dir: Optional[str] = None,
) -> str:
    """Reverse a previous compression — restore input notes and delete the output.

    WHEN TO CALL:
      (a) When a compression was done incorrectly.
      (b) When you need to re-process the original inputs differently.

    Args:
        output_id: The id of the extracted (output) note to reverse.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with restored note ids and status.
    """
    import argparse

    root = _get_root(project_dir)

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    args = argparse.Namespace(
        output_id=output_id,
        json=True,
        project_dir=str(root),
    )

    from myco.condense_cmd import run_uncompress
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
@_with_sidecar
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

    root = _get_root(project_dir)

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
# Tool: myco_absorb  —  external content ingestion
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_absorb",
    annotations={
        "title": "Myco Absorb — Ingest External Content with Provenance",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_absorb(
    content: str,
    provenance: str,
    tags: Optional[str] = None,
    project_dir: Optional[str] = None,
) -> str:
    """Ingest external content into the metabolic pipeline with full provenance tracking.

    WHEN TO CALL:
      (a) You already have the content body in hand (fetched via
          WebFetch, pasted by user, copied from a README) and need
          it to become a raw note with full provenance.
      (b) User shares a document/URL body and asks Myco to remember it.
      (c) A cohort gap (myco_colony action='gaps') points at a topic
          you have fresh external material for.

    DO NOT CALL WHEN:
      - You only have a URL and no body yet — use `myco_scent`
        (autonomous fetch + filter) or `myco_forage action='add'`
        (register for later manual digest) instead.
      - The material is an internal project artifact — use `myco_eat`.

    Each inlet note gets provenance fields: inlet_origin, inlet_method,
    inlet_fetched_at, inlet_content_hash (SHA256). The note enters the
    standard raw→digesting→integrated pipeline; call `myco_digest`
    when ready to route it into wiki/MYCO.md.

    Args:
        content: The external content body to ingest.
        provenance: Origin label (URL, file path, or description).
        tags: Comma-separated tags (default: "inlet").
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with the new note's id, path, and provenance metadata.
    """
    import argparse

    root = _get_root(project_dir)

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

    from myco.absorb_cmd import run_inlet
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
@_with_sidecar
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
      (a) You found an external repo/paper/article worth absorbing
          *later* but don't have time now — `action='add'` parks it
          with a `why` statement so future-you (or another agent)
          can pick it up.
      (b) `forage_backlog` hunger signal fires — `action='list'`
          shows what's waiting, then digest the top item.
      (c) After producing digest notes from a foraged item —
          `action='digest'` updates the manifest so the backlog
          shrinks honestly.

    DO NOT CALL WHEN:
      - You want to ingest content right now — use `myco_absorb`
        (you have the body) or `myco_scent` (autonomous topical fetch).
      - Forage is a *to-read queue*, not an inbox.

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

    root = _get_root(project_dir)

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
# Wave 55 (v0.46.0): Autonomous foraging — opportunistic scent-driven fetch
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_scent",
    annotations={
        "title": "Myco Scent — opportunistic on-demand foraging",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": False,
        "openWorldHint": True,
        "modelHint": "haiku",  # lightweight task
    },
)
@_with_sidecar
async def myco_scent(
    topic: str,
    budget: int = 5,
    project_dir: Optional[str] = None,
) -> str:
    """Opportunistic autonomous forage — discover and ingest content on demand.

    WHEN TO CALL:
      (a) Current task reveals a knowledge gap in a topic that isn't
          in wiki and that the user hasn't supplied material for.
          Hand over the topic name; Myco does the arxiv query +
          license/dedup/interest filter and drops survivors into the
          forage manifest as `raw_fetch`.
      (b) A `cohort_gap` or `wiki_miss` hunger signal names a topic —
          scent it to populate the intake end of the pipeline.

    DO NOT CALL WHEN:
      - You already have the body in hand — use `myco_absorb`.
      - You want to register a specific URL you found yourself —
        use `myco_forage action='add'`.
      - You're searching existing substrate memory — use `myco_sense`.

    Args:
        topic: Search query/topic name (e.g., "reinforcement learning").
        budget: Max candidates to fetch and process (default 5).
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON with {added: N, rejected: M, reasons: [...]}.

    Implementation:
      1. Query arxiv for topic (top `budget` results).
      2. Run each through immune_filter (dedup + interests + license).
      3. Auto-add passing candidates to forage/_index.yaml status=raw_fetch.
      4. Return summary.
    """
    from myco.feeds import immune_filter
    from myco.forage import add_item, generate_forage_id

    root = _get_root(project_dir)

    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    try:
        from myco.feeds import _fetch_arxiv
        candidates = _fetch_arxiv(topic, limit=budget)
    except Exception as exc:
        return json.dumps({"error": f"Failed to fetch topic '{topic}': {exc}"})

    added = 0
    rejected = 0
    reasons = []

    for candidate in candidates:
        passed, reason = immune_filter(root, candidate)
        if passed:
            try:
                # Auto-add to forage manifest
                forage_id = generate_forage_id()
                add_item(
                    root,
                    source_url=candidate["source_url"],
                    source_type=candidate["source_type"],
                    local_path=None,
                    license=candidate["license_guess"],
                    why=f"Scent-triggered fetch for topic '{topic}'",
                )
                added += 1
            except Exception as e:
                rejected += 1
                reasons.append(f"Failed to add {candidate['source_url']}: {e}")
        else:
            rejected += 1
            reasons.append(f"Rejected {candidate['title']}: {reason}")

    return json.dumps({
        "topic": topic,
        "added": added,
        "rejected": rejected,
        "reasons": reasons[:10],  # cap at 10 for output
    })


# ---------------------------------------------------------------------------
# Wave 47 (v0.36.0): Link graph analysis
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_mycelium",
    annotations={
        "title": "Myco Mycelium — structural link analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_mycelium(
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
    from myco.mycelium import (
        build_link_graph,
        find_clusters,
        find_orphans,
        graph_stats,
        query_backlinks,
    )

    root = _get_root(project_dir)

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
    name="myco_colony",
    annotations={
        "title": "Myco Colony — tag co-occurrence and gap analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_colony(
    action: str,
    limit: int = 10,
    project_dir: Optional[str] = None,
) -> str:
    """Analyze tag-based cohorts across notes for compression and gap detection.

    WHEN TO CALL:
      (a) Before `myco_condense` — run `action='suggest'` to pick
          the cohort with the highest compression payoff instead of
          guessing which tag to compress.
      (b) `cohort_staleness` / `inlet_ripe` hunger signals fire —
          `action='gaps'` reveals which knowledge domains are stuck
          in raw/digesting and need a digest pass.
      (c) Planning a refactor of the knowledge layer —
          `action='matrix'` surfaces tag co-occurrence so you can
          see which topics cluster.
      (d) Cross-project reconnaissance — `action='cross'` for
          clusters across projects, `action='auto_promote'` to
          promote cross-project nutrients to `wiki/cross_project/`.

    DO NOT CALL WHEN:
      - Searching for a specific note — use `myco_sense`.
      - Inspecting the wiki link graph — use `myco_mycelium`.

    Actions:
      matrix       — tag co-occurrence pairs (which tags appear together?)
      suggest      — compression cohort suggestions (which notes to compress together?)
      gaps         — knowledge gaps (tags where all notes are raw/digesting)
      cross        — cross-project tag clusters (Wave 58)
      auto_promote — cross-project auto-promote to wiki/cross_project/ (Wave 58)

    Args:
        action: One of 'matrix', 'suggest', 'gaps', 'cross', 'auto_promote'.
        limit: Max results to return (default 10).
        project_dir: Path to Myco project root. Auto-detected if omitted.
    """
    from myco.colony import (
        auto_promote_cross_project,
        compression_cohort_suggest,
        cross_project_cluster,
        gap_detection,
        tag_cooccurrence,
    )

    root = _get_root(project_dir)

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

    if action == "cross":
        cc = cross_project_cluster(min_cluster_size=2)
        return json.dumps(cc, ensure_ascii=False, indent=2)

    if action == "auto_promote":
        out = auto_promote_cross_project(root)
        return json.dumps(out, ensure_ascii=False, indent=2)

    return json.dumps({
        "error": f"Unknown action: {action}. "
                 "Use matrix/suggest/gaps/cross/auto_promote."
    })


# ---------------------------------------------------------------------------
# Wave 52 (v0.40.0): Session memory + search
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_memory",
    annotations={
        "title": "Myco Memory — FTS5 search across agent conversations",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",  # agent-routing: recommended model class
    },
)
@_with_sidecar
async def myco_memory(
    action: str,
    query: Optional[str] = None,
    max_age_days: int = 90,
    project_dir: Optional[str] = None,
) -> str:
    """Index and search agent conversation transcripts (session memory).

    WHEN TO CALL:
      (a) `session_index_missing` hunger signal → `action='index'`
          to build / refresh the SQLite FTS5 index over .jsonl
          transcripts.
      (b) User asks "what did we talk about last time?" / "what
          did we decide about X?" / "when did we first hit this
          bug?" → `action='search'` with the topic.
      (c) You're about to redo work and want to check whether a
          past session already explored the same ground →
          `action='search'` first.
      (d) Weekly-ish maintenance → `action='index'` to catch new
          transcripts.
      (e) Index has grown beyond `max_age_days` → `action='prune'`.

    DO NOT CALL WHEN:
      - Searching substrate notes / wiki — use `myco_sense` (that
        operates on the digested layer; `myco_memory` operates on
        raw transcripts).

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
    from myco.memory import index_sessions, prune_sessions, search_sessions

    root = _get_root(project_dir)

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
@_with_sidecar
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

    root = _get_root(project_dir)

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
@_with_sidecar
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

    root = _get_root(project_dir)

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
# Tool: myco_session_end — Zero-touch close-out ritual (Wave 56)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_session_end",
    annotations={
        "title": "Myco Session End — Automated Close-Out",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",
    },
)
@_with_sidecar
async def myco_session_end(
    summary: Optional[str] = None,
    prune: bool = True,
    refresh_brief: bool = True,
    project_dir: Optional[str] = None,
) -> str:
    """Run the session-end ritual: eat summary, auto-prune, refresh boot brief.

    WHEN TO CALL — at the end of a working session, or when the user
    signals they are wrapping up ("let's call it", "session end",
    "before I go", "that's enough for today"). Do not wait for explicit
    permission; this is the agent's zero-forget counterpart to the
    session-start hunger ritual.

    Args:
        summary: Short summary of what happened this session. Auto-eaten
                 as a raw note tagged [session-end, auto]. Omit to skip.
        prune: If True (default), call auto-prune to excrete multipath-
               orphaned notes.
        refresh_brief: If True (default), regenerate boot_brief.md so the
                       next session opens hot.
        project_dir: Path to Myco project root. Auto-detected if omitted.

    Returns:
        JSON: {ate, pruned, brief_refreshed, errors}.
    """
    from myco.session_hook import run_session_end

    root = _get_root(project_dir)
    result = run_session_end(
        root,
        summary=summary,
        prune=prune,
        refresh_brief=refresh_brief,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_observe_turn — Agent reflex arc (Wave 57 / Wave 2)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_observe_turn",
    annotations={
        "title": "Myco Observe Turn — Agent Reflex Suggestions",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
@_with_sidecar
async def myco_observe_turn(
    user_turn_text: str,
    previous_assistant_text: str = "",
    project_dir: Optional[str] = None,
) -> str:
    """Analyze the most-recent user turn and return reflex suggestions.

    WHEN TO CALL — once per user turn, as cheaply as possible. This is
    the Agent's introspection hook: it scans for decision markers,
    new vocabulary, unfamiliar topics, freshness-dependent claims, and
    completion markers, then returns concrete `suggested_calls` the
    Agent can execute without protocol reasoning.

    Zero LLM calls under the hood — pattern matching only, <1ms latency.

    Args:
        user_turn_text: The text of the user's most recent message.
        previous_assistant_text: Optional — the assistant's prior response,
                                 used for context (currently unused, reserved).
        project_dir: Myco project root. Auto-detected if omitted.

    Returns:
        JSON: {
          should_eat, should_scent, should_verify, should_digest,
          suggested_calls: [{tool, args, reason, priority}, ...],
          reasons: [...], turn_length, confidence
        }
    """
    from myco.observe_turn import observe_turn

    try:
        root = _get_root(project_dir)
    except Exception:
        root = None
    result = observe_turn(
        user_turn_text,
        root=root,
        previous_assistant_text=previous_assistant_text,
    )
    return json.dumps(result, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_verify — Truth immune (Wave 57 Wave 2 exposure of G3 CLI)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_verify",
    annotations={
        "title": "Myco Verify — Truth Immune Re-validation",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
        "modelHint": "opus",
    },
)
@_with_sidecar
async def myco_verify(
    note_id: Optional[str] = None,
    mark: Optional[str] = None,
    scope: str = "time_sensitive",
    limit: int = 20,
    project_dir: Optional[str] = None,
) -> str:
    """Re-validate time-sensitive notes. Part of the truth-immune loop.

    WHEN TO CALL:
      - After myco_hunger surfaces a `verify_batch`, loop through each
        entry and call this tool with the note_id.
      - When a user claim references 'latest' / 'current' / 'still valid',
        call with scope='time_sensitive' to list stale notes.
      - When external research contradicts a note, call with
        mark='contradicted' — this quarantines the note AND triggers
        the verify→rescent reflex chain.

    Args:
        note_id: If provided together with `mark`, applies the mark.
                 If provided alone, returns the note's freshness state.
        mark: One of {'still_true', 'ambiguous', 'contradicted'}. When
              'contradicted', a scent suggestion is appended for rescue.
        scope: 'time_sensitive' | 'live' | 'all' — scope for listing.
        limit: Max stale notes to return when listing.
        project_dir: Myco project root. Auto-detected if omitted.

    Returns:
        JSON: list-mode → {stale_count, notes[...]}; mark-mode →
              {id, mark, reflex: {...}} (reflex present iff mark='contradicted').
    """
    from myco.notes import read_note, update_note, _now_iso

    root = _get_root(project_dir)
    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    # Mark mode
    if note_id and mark:
        if mark not in {"still_true", "ambiguous", "contradicted"}:
            return json.dumps({"error": f"invalid mark: {mark}"})
        from myco.notes import id_to_filename
        target = root / "notes" / id_to_filename(note_id)
        if not target.exists():
            return json.dumps({"error": f"note not found: {note_id}"})
        now = datetime.now()
        try:
            if mark == "still_true":
                update_note(target, last_verified=_now_iso(now))
            elif mark == "ambiguous":
                meta, _ = read_note(target)
                old = meta.get("freshness_window_days", 90)
                update_note(
                    target,
                    last_verified=_now_iso(now),
                    freshness_window_days=max(1, old // 2),
                )
            else:  # contradicted
                update_note(
                    target,
                    status="quarantine",
                    quarantine_reason=f"contradicted during verify at {_now_iso(now)}",
                )
        except Exception as e:
            return json.dumps({"error": f"update failed: {e}"})

        response: Dict[str, Any] = {"status": "ok", "id": note_id, "mark": mark}

        # Reflex chain: contradicted → rescent the topic.
        if mark == "contradicted":
            try:
                from myco.reflex import verify_to_scent
                rx = verify_to_scent(root, note_id, mark, execute=False)
                if rx.get("triggered"):
                    response["reflex"] = {
                        "chain": "verify_to_rescent",
                        "topic": rx["topic"],
                        "suggested_call": rx["suggested_call"],
                        "reason": (
                            "Note was contradicted — forage fresh sources "
                            "to replace stale claim."
                        ),
                    }
            except Exception as e:
                response["reflex_error"] = str(e)
        return json.dumps(response, ensure_ascii=False, indent=2)

    # List mode
    if note_id and not mark:
        from myco.notes import id_to_filename
        target = root / "notes" / id_to_filename(note_id)
        if not target.exists():
            return json.dumps({"error": f"note not found: {note_id}"})
        meta, _ = read_note(target)
        return json.dumps({
            "id": note_id,
            "freshness": meta.get("freshness"),
            "last_verified": meta.get("last_verified"),
            "status": meta.get("status"),
        }, ensure_ascii=False, indent=2)

    # Listing mode
    now = _dt.datetime.now()
    thresholds = {"time_sensitive": 90, "live": 7, "all": 0}
    stale: List[Dict[str, Any]] = []
    for p in sorted((root / "notes").glob("n_*.md")):
        try:
            meta, _ = read_note(p)
        except Exception:
            continue
        if meta.get("status") not in ("extracted", "integrated"):
            continue
        f = meta.get("freshness", "time_sensitive")
        if scope != "all" and f != scope:
            continue
        if f == "static":
            continue
        lv = meta.get("last_verified") or meta.get("created")
        try:
            lv_dt = _dt.datetime.strptime(str(lv), "%Y-%m-%dT%H:%M:%S")
        except Exception:
            continue
        age = (now - lv_dt).days
        thr = thresholds.get(f, 90)
        if age > thr:
            stale.append({
                "id": meta.get("id"),
                "freshness": f,
                "age_days": age,
                "threshold_days": thr,
            })
        if len(stale) >= limit:
            break
    stale.sort(key=lambda x: -x["age_days"])
    return json.dumps({"stale_count": len(stale), "notes": stale}, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_supersede — Apply eat→supersede reflex decision
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_supersede",
    annotations={
        "title": "Myco Supersede — Apply Supersede Reflex",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
@_with_sidecar
async def myco_supersede(
    new_note_id: str,
    old_note_ids: List[str],
    project_dir: Optional[str] = None,
) -> str:
    """Mark old notes as superseded by a new one and record the link.

    WHEN TO CALL — after myco_eat returns a `reflex.candidates` block,
    review the candidates and call this tool with the ids you want to
    supersede. Writes `supersedes: [...]` on the new note and
    `superseded_by: <new_id>` on each old note. Excretion of old notes
    is handled by the next prune cycle (superseded is one of its
    multipath signals).

    Args:
        new_note_id: The fresh note.
        old_note_ids: Ids of notes to mark as superseded by `new_note_id`.
        project_dir: Myco project root. Auto-detected if omitted.
    """
    from myco.reflex import apply_supersede

    root = _get_root(project_dir)
    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    out = apply_supersede(root, new_note_id, list(old_note_ids or []))
    return json.dumps(out, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Tool: myco_ingest_transcript — Passive session ingest (Wave 58 / Wave 3)
# ---------------------------------------------------------------------------

@mcp.tool(
    name="myco_ingest_transcript",
    annotations={
        "title": "Myco Ingest Transcript — Passive Auto-Eat",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    },
)
@_with_sidecar
async def myco_ingest_transcript(
    chunks: List[Dict[str, Any]],
    max_eat: int = 5,
    dry_run: bool = False,
    project_dir: Optional[str] = None,
) -> str:
    """Scan transcript chunks and auto-eat decision / preference / vocab /
    root-cause findings as raw notes.

    WHEN TO CALL — host hooks invoke this on idle ticks or at session end.
    Agents may also call it on demand with the last N turns. Deduped by
    content hash against .myco_state/transcript_ingested.json.

    Disable globally by touching .myco_state/transcript_monitor.off.

    Args:
        chunks: list of {"role": "user"|"assistant", "text": str}.
        max_eat: per-call upper bound on new notes (default 5).
        dry_run: if True, classify but do not write notes.
        project_dir: Myco project root. Auto-detected if omitted.

    Returns:
        JSON summary: scanned, classified, ate, skipped_duplicate, disabled.
    """
    from myco.transcript_monitor import ingest_transcript

    root = _get_root(project_dir)
    if not (root / "_canon.yaml").exists():
        return json.dumps({"error": f"Not a Myco project (no _canon.yaml at {root})"})

    out = ingest_transcript(root, chunks, max_eat=max_eat, dry_run=dry_run)
    return json.dumps(out, ensure_ascii=False, indent=2)
