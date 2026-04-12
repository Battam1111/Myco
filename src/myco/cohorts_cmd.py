"""
CLI dispatch for ``myco cohort`` — semantic cohort analysis.

Wave 48 (contract v0.37.0).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def _project_root(args: Any) -> Path:
    """Resolve project root from --project-dir or walk up."""
    raw = getattr(args, "project_dir", None) or "."
    candidate = Path(raw).resolve()
    p = candidate
    for _ in range(10):
        if (p / "_canon.yaml").exists():
            return p
        if p.parent == p:
            break
        p = p.parent
    return candidate


def run_cohort(args: Any) -> int:
    """Dispatch ``myco cohort`` subcommands."""
    from myco.cohorts import (
        compression_cohort_suggest,
        gap_detection,
        tag_cooccurrence,
    )

    root = _project_root(args)
    use_json = getattr(args, "json", False)
    limit = getattr(args, "limit", 20) or 20
    sub = getattr(args, "cohort_subcommand", None)

    if sub is None:
        print("Usage: myco cohort {matrix|suggest|gaps}", file=sys.stderr)
        return 1

    if sub == "matrix":
        pairs = tag_cooccurrence(root)
        if use_json:
            print(json.dumps([{"tag_a": a, "tag_b": b, "count": c}
                              for a, b, c in pairs[:limit]], indent=2))
        else:
            print(f"Tag co-occurrence (top {min(limit, len(pairs))}):")
            for a, b, count in pairs[:limit]:
                print(f"  {a} + {b} : {count}")
            if not pairs:
                print("  (no co-occurring tags found)")
        return 0

    if sub == "suggest":
        suggestions = compression_cohort_suggest(root)
        if use_json:
            print(json.dumps(suggestions[:limit], indent=2))
        else:
            if suggestions:
                print(f"Compression cohort suggestions ({len(suggestions)}):")
                for s in suggestions[:limit]:
                    print(f"  tag={s['tag']}  notes={s['note_count']}  "
                          f"oldest={s['oldest_age_days']}d  score={s['cohort_score']}")
            else:
                print("No compression cohorts ripe for synthesis.")
        return 0

    if sub == "gaps":
        gaps = gap_detection(root)
        if use_json:
            print(json.dumps(gaps[:limit], indent=2))
        else:
            if gaps:
                print(f"Knowledge gaps ({len(gaps)}) — tags with only raw/digesting notes:")
                for g in gaps[:limit]:
                    print(f"  {g['tag']}  raw={g['raw_count']}  "
                          f"digesting={g['digesting_count']}  total={g['total']}")
            else:
                print("No knowledge gaps found — all active tags have synthesized output.")
        return 0

    print(f"Unknown subcommand: {sub}", file=sys.stderr)
    return 1
