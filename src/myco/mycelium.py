"""
Myco Link Graph — structural link analysis across the substrate.

Wave 47 (contract v0.36.0): Build and query a link graph across all Myco
surfaces (MYCO.md, wiki/, docs/, notes/, log.md, src/myco/*.py). Computes
forward links, backlinks, orphan detection, and connected-component
clusters on-demand from the file system — no cached state, same philosophy
as lint.

Authoritative design: plan Waves 47-53 §Wave 47.
"""
# --- Mycelium references ---
# Architecture:  docs/architecture.md §Link graph
# Open problems: docs/open_problems.md §5 (structural decay, orphan drift)

from __future__ import annotations

import os
import re
from collections import defaultdict, deque
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# ---------------------------------------------------------------------------
# Link extraction patterns
# ---------------------------------------------------------------------------

# Markdown links: text  — capture path portion
_MD_LINK_RE = re.compile(r"\[.*?\]\(([^)#]+?)(?:#[^)]*)?\)")

# Backtick file paths: some/path.md or some/path.yaml
_BACKTICK_PATH_RE = re.compile(r"`([a-zA-Z0-9_./\\-]+\.(?:md|yaml|yml))`")

# Note ID references: n_YYYYMMDDTHHMMSS_XXXX (in body text or YAML values)
_NOTE_ID_RE = re.compile(r"\b(n_\d{8}T\d{6}_[0-9a-f]{4})\b")

# Craft file references: docs/primordia/xxx_craft_YYYY-MM-DD.md
_CRAFT_REF_RE = re.compile(
    r"(docs/primordia/[a-z0-9_]+_craft_\d{4}-\d{2}-\d{2}(?:_[0-9a-f]{4})?\.md)"
)

# YAML list values that look like note IDs (compressed_from field)
_YAML_LIST_ID_RE = re.compile(r"- (n_\d{8}T\d{6}_[0-9a-f]{4})")

# Python comment/string references to substrate files (mycelium references).
# Matches paths like docs/architecture.md, wiki/page.md, _canon.yaml, MYCO.md,
# notes/n_xxx.md, src/myco/lint.py — appearing in comments or string literals.
_PY_PATH_RE = re.compile(
    r"(?:^|\s|[\"'`])"                        # boundary: start, space, or quote
    r"((?:docs|wiki|notes|src)/[a-zA-Z0-9_./-]+\.(?:md|yaml|yml|py)"  # dir-prefixed
    r"|_canon\.yaml"                           # top-level _canon.yaml
    r"|MYCO\.md"                               # top-level MYCO.md
    r"|log\.md"                                # top-level log.md
    r"|README(?:_[a-z]{2})?\.md"               # README variants
    r")"
)

# Structural roots that are never orphans (they are entry points by design)
_STRUCTURAL_ROOTS = {
    "MYCO.md", "_canon.yaml", "log.md", "README.md", "README_zh.md",
    "README_ja.md", "CONTRIBUTING.md", "LICENSE", "CODE_OF_CONDUCT.md",
    "SECURITY.md", "pyproject.toml", ".gitignore",
}

# Directories to scan for .md files
_SCAN_DIRS = ["notes", "wiki", "docs", "docs/primordia"]

# Directories to scan for .py files (mycelium network includes source code)
_PY_SCAN_DIRS = ["src/myco"]

# Top-level .md files to include
_TOP_LEVEL_MD = ["MYCO.md", "log.md", "README.md", "README_zh.md",
                 "README_ja.md", "CONTRIBUTING.md"]


def _normalize(path_str: str) -> str:
    """Normalize a path string to forward-slash relative form."""
    return path_str.replace("\\", "/").strip()


def _resolve_link(link_raw: str, source_file: str, root: Path) -> Optional[str]:
    """Resolve a raw link target to a root-relative path, or None if invalid."""
    link = _normalize(link_raw)

    # Skip URLs, anchors, mailto, etc.
    if link.startswith(("http://", "https://", "mailto:", "#", "data:")):
        return None

    # Resolve relative links against source file's directory
    source_dir = str(Path(source_file).parent)
    if link.startswith("./") or link.startswith("../") or not "/" in link:
        resolved = os.path.normpath(os.path.join(source_dir, link))
    else:
        resolved = os.path.normpath(link)

    resolved = resolved.replace("\\", "/")

    # Verify the target exists on disk (to avoid phantom links)
    if (root / resolved).exists():
        return resolved
    return None


def _resolve_note_id(note_id: str, root: Path) -> Optional[str]:
    """Resolve a note ID to its relative file path, or None."""
    notes_dir = root / "notes"
    if not notes_dir.is_dir():
        return None
    candidate = notes_dir / f"{note_id}.md"
    if candidate.exists():
        return f"notes/{note_id}.md"
    return None


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def extract_links(filepath: Path, root: Path) -> List[str]:
    """Extract all outbound link targets from a single file.

    Returns root-relative paths of targets that exist on disk.
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []

    source_rel = str(filepath.relative_to(root)).replace("\\", "/")
    targets: Set[str] = set()

    # Skip content inside code fences
    in_fence = False
    lines = content.split("\n")
    filtered_lines = []
    for line in lines:
        if line.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            filtered_lines.append(line)
    text = "\n".join(filtered_lines)

    # Markdown links
    for m in _MD_LINK_RE.finditer(text):
        resolved = _resolve_link(m.group(1), source_rel, root)
        if resolved and resolved != source_rel:
            targets.add(resolved)

    # Backtick paths
    for m in _BACKTICK_PATH_RE.finditer(text):
        resolved = _resolve_link(m.group(1), source_rel, root)
        if resolved and resolved != source_rel:
            targets.add(resolved)

    # Craft file references (often bare, not in backticks)
    for m in _CRAFT_REF_RE.finditer(text):
        path = _normalize(m.group(1))
        if (root / path).exists() and path != source_rel:
            targets.add(path)

    # Note ID references (resolve to notes/n_xxx.md)
    for m in _NOTE_ID_RE.finditer(text):
        resolved = _resolve_note_id(m.group(1), root)
        if resolved and resolved != source_rel:
            targets.add(resolved)

    # YAML list items (compressed_from etc.)
    for m in _YAML_LIST_ID_RE.finditer(text):
        resolved = _resolve_note_id(m.group(1), root)
        if resolved and resolved != source_rel:
            targets.add(resolved)

    return sorted(targets)


def extract_links_py(filepath: Path, root: Path) -> List[str]:
    """Extract outbound link targets from a Python source file.

    Scans comments and string literals for references to substrate files
    (docs/, wiki/, notes/, _canon.yaml, MYCO.md, etc.).  These are the
    "mycelium references" that connect code to the knowledge substrate.

    Unlike .md links which are relative to the source file, Python
    mycelium references are always resolved from the project root
    (they reference substrate paths like ``docs/architecture.md`` or
    ``_canon.yaml``, not sibling files).
    """
    try:
        content = filepath.read_text(encoding="utf-8", errors="replace")
    except (OSError, UnicodeDecodeError):
        return []

    source_rel = str(filepath.relative_to(root)).replace("\\", "/")
    targets: Set[str] = set()

    for m in _PY_PATH_RE.finditer(content):
        raw = _normalize(m.group(1))
        # Python mycelium refs are always root-relative — resolve from root
        normalized = os.path.normpath(raw).replace("\\", "/")
        if (root / normalized).exists() and normalized != source_rel:
            targets.add(normalized)

    # Note ID references (same as .md scanning)
    for m in _NOTE_ID_RE.finditer(content):
        resolved = _resolve_note_id(m.group(1), root)
        if resolved and resolved != source_rel:
            targets.add(resolved)

    return sorted(targets)


def build_link_graph(
    root: Path,
) -> Dict[str, Dict[str, List[str]]]:
    """Build a link graph across all .md and .py files in the substrate.

    Returns: {relative_path: {"forward": [targets], "backlinks": [sources]}}
    """
    root = root.resolve()

    # Collect all .md files
    all_files: List[str] = []

    # Top-level files
    for name in _TOP_LEVEL_MD:
        if (root / name).exists():
            all_files.append(name)

    # Directory scans (.md)
    for dirname in _SCAN_DIRS:
        dirpath = root / dirname
        if not dirpath.is_dir():
            continue
        for f in sorted(dirpath.rglob("*.md")):
            rel = str(f.relative_to(root)).replace("\\", "/")
            if rel not in all_files:
                all_files.append(rel)

    # Collect .py files from source directories
    py_files: List[str] = []
    for dirname in _PY_SCAN_DIRS:
        dirpath = root / dirname
        if not dirpath.is_dir():
            continue
        for f in sorted(dirpath.rglob("*.py")):
            rel = str(f.relative_to(root)).replace("\\", "/")
            py_files.append(rel)

    # Pass 1: build forward map — .md files
    forward: Dict[str, List[str]] = {}
    for rel in all_files:
        fpath = root / rel
        forward[rel] = extract_links(fpath, root)

    # Pass 1b: build forward map — .py files
    for rel in py_files:
        fpath = root / rel
        forward[rel] = extract_links_py(fpath, root)

    # Pass 2: invert to build backlinks
    backlinks: Dict[str, List[str]] = defaultdict(list)
    for source, targets in forward.items():
        for target in targets:
            backlinks[target].append(source)

    # Assemble graph
    # Include all files that appear as either source or target
    all_nodes = set(all_files) | set(py_files)
    for targets in forward.values():
        all_nodes.update(targets)
    for target in backlinks:
        all_nodes.add(target)

    graph: Dict[str, Dict[str, List[str]]] = {}
    for node in sorted(all_nodes):
        graph[node] = {
            "forward": forward.get(node, []),
            "backlinks": sorted(backlinks.get(node, [])),
        }

    return graph


def query_backlinks(graph: Dict[str, Dict[str, List[str]]], target: str) -> List[str]:
    """Return all files that link to target."""
    target = _normalize(target)
    entry = graph.get(target)
    if entry is None:
        return []
    return list(entry["backlinks"])


def find_orphans(graph: Dict[str, Dict[str, List[str]]]) -> List[str]:
    """Find files with zero inbound links, excluding structural roots.

    Archived primordia are excluded — they are historical records stored
    in git history that are not expected to be referenced.

    Notes ARE included because unreferenced notes represent knowledge
    that is accumulating but not flowing.  However, the hunger signal
    layer may choose to filter very recent notes (< threshold days)
    since they haven't had time to be referenced yet.
    """
    # Only archived primordia are exempt — notes stay visible as orphans
    _ORPHAN_EXEMPT_PREFIXES = ("docs/primordia/archive/", "docs\\primordia\\archive\\")
    # .py source files participate in the graph (forward links + backlinks)
    # but are never orphans themselves — orphan detection tracks knowledge flow
    _ORPHAN_EXEMPT_SUFFIXES = (".py",)
    orphans = []
    for node, data in sorted(graph.items()):
        # Skip structural roots
        basename = Path(node).name
        if basename in _STRUCTURAL_ROOTS:
            continue
        # Skip directories (README.md in subdirs are charters)
        if basename.lower() == "readme.md":
            continue
        # Skip archived primordia — historical records
        if node.startswith(_ORPHAN_EXEMPT_PREFIXES):
            continue
        # Skip source code files — they are infrastructure, not knowledge
        if node.endswith(_ORPHAN_EXEMPT_SUFFIXES):
            continue
        if not data["backlinks"]:
            orphans.append(node)
    return orphans


def find_clusters(graph: Dict[str, Dict[str, List[str]]]) -> List[List[str]]:
    """Find connected components in the undirected form of the link graph."""
    # Build undirected adjacency
    adj: Dict[str, Set[str]] = defaultdict(set)
    for node, data in graph.items():
        for target in data["forward"]:
            if target in graph:
                adj[node].add(target)
                adj[target].add(node)
        for source in data["backlinks"]:
            if source in graph:
                adj[node].add(source)
                adj[source].add(node)

    visited: Set[str] = set()
    clusters: List[List[str]] = []

    for node in sorted(graph.keys()):
        if node in visited:
            continue
        # BFS
        component: List[str] = []
        queue = deque([node])
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            visited.add(current)
            component.append(current)
            for neighbor in sorted(adj.get(current, set())):
                if neighbor not in visited:
                    queue.append(neighbor)
        clusters.append(sorted(component))

    return clusters


def graph_stats(graph: Dict[str, Dict[str, List[str]]]) -> Dict[str, Any]:
    """Compute summary statistics for the link graph."""
    total_nodes = len(graph)
    total_edges = sum(len(d["forward"]) for d in graph.values())
    orphans = find_orphans(graph)
    clusters = find_clusters(graph)

    # Hub: most backlinks (most referenced)
    hub = max(graph.items(), key=lambda x: len(x[1]["backlinks"]),
              default=("", {"backlinks": []}))
    # Authority: most forward links (references the most)
    authority = max(graph.items(), key=lambda x: len(x[1]["forward"]),
                    default=("", {"forward": []}))

    return {
        "total_nodes": total_nodes,
        "total_edges": total_edges,
        "orphan_count": len(orphans),
        "cluster_count": len(clusters),
        "hub": {"file": hub[0], "backlink_count": len(hub[1]["backlinks"])},
        "authority": {"file": authority[0], "forward_count": len(authority[1]["forward"])},
    }
