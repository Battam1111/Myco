"""
Myco Propagate — push _canon.yaml SSoT values to all cited_in surfaces.

Reads ``system.numeric_claims`` from ``_canon.yaml`` and rewrites stale
numeric values in every file listed under ``cited_in`` for each claim.

Usage::

    myco propagate [--project-dir /path]

Idempotent: running twice produces the same output. Only files whose
content actually differs are rewritten.
"""

from __future__ import annotations

import re
from pathlib import Path

from myco.project import find_project_root


def _load_canon(root: Path) -> dict:
    """Load and return parsed _canon.yaml."""
    import yaml

    canon_path = root / "_canon.yaml"
    with open(canon_path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


# ---------------------------------------------------------------------------
# Per-claim replacement logic
# ---------------------------------------------------------------------------

def _replace_claim_value(content: str, claim_name: str, value) -> str:
    """Replace stale numeric values for *claim_name* in *content*.

    Each claim has characteristic patterns in the narrative surfaces.
    We use regex replacements scoped to expected patterns so we don't
    accidentally mutate unrelated numbers.
    """
    v = str(value)

    if claim_name == "mcp_tool_count":
        # English: "N tools", "N MCP tools"
        content = re.sub(r"\b\d+ tools\b", f"{v} tools", content)
        content = re.sub(r"\b\d+ MCP tools\b", f"{v} MCP tools", content)
        # Chinese: "N 个工具", "N个工具"
        content = re.sub(r"\d+\s*个工具", f"{v} 个工具", content)
        # Japanese: "Nのツール"
        content = re.sub(r"\d+のツール", f"{v}のツール", content)

    elif claim_name == "lint_dimensions":
        # "N-dimension", "N dimensions"
        content = re.sub(r"\b\d+-dimension\b", f"{v}-dimension", content)
        content = re.sub(r"\b\d+ dimensions?\b", f"{v} dimensions", content)
        # Chinese: "N 维", "N维"
        content = re.sub(r"\d+\s*维", f"{v} 维", content)
        # Fraction form: "N/N" in lint dimension count refs (e.g. "23/23")
        content = re.sub(r"\b\d+/\d+\b(?=\s*(?:lint|dimension|check))",
                         f"{v}/{v}", content)

    elif claim_name == "test_count":
        # "N tests", "N 个测试"
        content = re.sub(r"\b\d+ tests?\b", f"{v} tests", content)
        content = re.sub(r"\d+\s*个测试", f"{v} 个测试", content)

    elif claim_name == "principles_count":
        # "N principles", "N 原则", "N 原则" variants
        content = re.sub(r"\b\d+ principles?\b", f"{v} principles", content)
        content = re.sub(r"\d+\s*原则", f"{v} 原则", content)
        # "W1-WN" anchor range references
        content = re.sub(r"\bW1-W\d+\b", f"W1-W{v}", content)

    return content


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_propagate(args) -> int:
    """Push _canon.yaml numeric claims to all cited_in surfaces."""
    root = find_project_root(getattr(args, "project_dir", "."))
    canon = _load_canon(root)

    claims = (
        canon.get("system", {}).get("traceability", {}).get("numeric_claims", {})
        or canon.get("system", {}).get("numeric_claims", {})
    )
    if not claims:
        print("  No numeric_claims found in _canon.yaml.")
        return 0

    total_fixed = 0

    for claim_name, claim_data in claims.items():
        value = claim_data.get("value")
        cited_in = claim_data.get("cited_in", [])
        if value is None or not cited_in:
            continue

        for filepath in cited_in:
            full_path = root / filepath
            if not full_path.exists():
                print(f"  Warning: {filepath} not found (cited_in for {claim_name})")
                continue

            content = full_path.read_text(encoding="utf-8")
            new_content = _replace_claim_value(content, claim_name, value)
            if new_content != content:
                full_path.write_text(new_content, encoding="utf-8")
                total_fixed += 1
                print(f"  Updated {filepath}: {claim_name} -> {value}")

    if total_fixed == 0:
        print("  All surfaces already aligned with _canon.yaml SSoT.")
    else:
        print(f"\n  Propagated {total_fixed} value(s). Run `myco immune` to verify.")
    return 0
