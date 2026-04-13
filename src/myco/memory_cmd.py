"""
CLI dispatch for ``myco memory`` — session memory management.

Wave 52 (contract v0.40.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _project_root(args: Any) -> Path:
    """Wave A1: delegates to centralized find_project_root."""
    from myco.project import find_project_root
    return find_project_root(getattr(args, "project_dir", None), strict=False)


def run_session(args: Any) -> int:
    """Dispatch ``myco memory`` subcommands."""
    from myco.memory import index_sessions, prune_sessions, search_sessions

    root = _project_root(args)
    use_json = getattr(args, "json", False)
    sub = getattr(args, "session_subcommand", None)

    if sub is None:
        print("Usage: myco memory {index|sense|prune}", file=sys.stderr)
        return 1

    if sub == "index":
        stats = index_sessions(root)
        if use_json:
            print(json.dumps(stats, indent=2))
        else:
            if "error" in stats:
                print(f"Session indexing disabled: {stats['error']}")
            else:
                print(f"Session indexing complete:")
                print(f"  Indexed files: {stats['indexed_files']}")
                print(f"  Indexed turns: {stats['indexed_turns']}")
                print(f"  Skipped files: {stats['skipped_files']}")
                print(f"  DB path:       {stats['db_path']}")
        return 0

    if sub == "sense":
        query = getattr(args, "query", None)
        if not query:
            print("Usage: myco memory sense <query>", file=sys.stderr)
            return 1
        limit = getattr(args, "limit", 20) or 20
        results = search_sessions(root, query, limit=limit)
        if use_json:
            print(json.dumps(results, indent=2))
        else:
            if results:
                print(f"Session search: {len(results)} result(s) for '{query}':")
                for r in results:
                    print(f"  [{r['role']}] {r['session_file']}:{r['turn_index']}")
                    print(f"    {r['snippet']}")
            else:
                print(f"No session results for '{query}'")
        return 0

    if sub == "prune":
        max_age = getattr(args, "max_age_days", 90) or 90
        stats = prune_sessions(root, max_age_days=max_age)
        if use_json:
            print(json.dumps(stats, indent=2))
        else:
            print(f"Session prune: {stats['removed_turns']} turns removed, "
                  f"{stats['remaining_turns']} remaining")
        return 0

    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    return 1
