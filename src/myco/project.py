"""
Myco Project Root Resolution — centralized utility.

Wave A1: Extracted from 6 duplicated _project_root functions across
*_cmd.py files + mcp_server.py. Single source of truth for project
root discovery.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional, Union


class MycoProjectNotFound(Exception):
    """Raised when no _canon.yaml is found in the walk-up chain.

    Wave 20 (v0.19.0): strict mode prevents false-healthy hunger reports
    on unrelated directories. See
    docs/primordia/silent_fail_elimination_craft_2026-04-11.md D3.
    """
    pass


def find_project_root(
    hint: Optional[Union[str, Path]] = None,
    *,
    strict: bool = True,
) -> Path:
    """Resolve the Myco project root by walking up from hint (or cwd).

    Args:
        hint: Starting directory or file path. Defaults to cwd.
        strict: If True (default), raise MycoProjectNotFound when no
            _canon.yaml is found. If False, return the best-guess path
            silently (used by MCP server for non-critical contexts).

    Returns:
        Resolved Path to the project root (directory containing _canon.yaml).

    Raises:
        MycoProjectNotFound: If strict=True and no _canon.yaml found.
            Escape hatch: set MYCO_ALLOW_NO_PROJECT=1 env var.
    """
    raw = str(hint) if hint else "."
    root = Path(raw).resolve()

    # Walk upward for _canon.yaml so callers can run from subdirs.
    for candidate in [root] + list(root.parents):
        if (candidate / "_canon.yaml").exists():
            return candidate

    if not strict:
        return root

    if os.environ.get("MYCO_ALLOW_NO_PROJECT") == "1":
        return root

    raise MycoProjectNotFound(
        f"not a Myco project: no _canon.yaml found at or above "
        f"{root}. Did you forget to cd, or pass --project-dir? "
        f"Set MYCO_ALLOW_NO_PROJECT=1 to override (not recommended)."
    )
