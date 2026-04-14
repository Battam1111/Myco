"""
Myco Bootstrap — First-contact auto-seed.

Wave 56 (zero-touch UX, vision_closure_craft_2026-04-14.md Wave 1):
  When an Agent calls any MCP tool in a directory that isn't yet a
  Myco project (no _canon.yaml), silently run init_level_1 with
  inferred defaults so the user never has to type `myco init`.

Contract:
  - Infer project name from directory name (sanitized).
  - Default github_user = "user" — non-blocking placeholder.
  - Set entry_point = CLAUDE.md (safe default; overwritten if Cursor/GPT
    detected via env).
  - Write .myco_state/bootstrapped sentinel so we don't re-attempt on
    every tool call, even if seeding partially fails.
  - Silent mode: suppress stdout from init_level_1 so MCP stdio stays
    clean.

Philosophy: "用户几乎什么都不用做就能够自动化无感知地用起来一切".
"""
from __future__ import annotations

import io
import os
import re
import sys
from pathlib import Path
from typing import Optional


def _infer_project_name(root: Path) -> str:
    """Infer project name from directory. Sanitize to alphanumeric+dash."""
    name = root.name or "myco_project"
    # Strip leading dots, collapse non-alnum to dash
    name = re.sub(r"[^A-Za-z0-9_\-]", "-", name).strip("-.")
    return name or "myco_project"


def _infer_entry_point() -> str:
    """Pick agent entry point from env hints.

    CLAUDE.md default; Cursor/GPT detected via MYCO_AGENT env var.
    """
    agent = os.environ.get("MYCO_AGENT", "").lower()
    if agent == "cursor":
        return "MYCO.md"
    if agent in ("gpt", "codex"):
        return "GPT.md"
    return "CLAUDE.md"


def is_bootstrapped(root: Path) -> bool:
    """True if root is already a Myco project OR bootstrap was attempted."""
    if (root / "_canon.yaml").exists():
        return True
    sentinel = root / ".myco_state" / "bootstrapped"
    return sentinel.exists()


def first_contact_seed(root: Path, *, silent: bool = True) -> Optional[dict]:
    """Attempt first-contact auto-seed at root.

    Returns a dict describing what was done (keys: name, entry_point, level)
    on success, or None if seeding is unnecessary / failed.

    Never raises — first-contact must never break the calling tool.
    """
    try:
        root = Path(root).resolve()
    except (OSError, TypeError, RuntimeError):
        return None

    if is_bootstrapped(root):
        return None

    # Guard: only auto-seed directories that look like a project workspace.
    # Skip obvious "should not auto-seed" locations (tmp, home dir, /).
    _reject_roots = {
        Path.home().resolve() if Path.home() else None,
        Path("/").resolve(),
        Path("/tmp").resolve() if os.path.exists("/tmp") else None,
    }
    if root in _reject_roots:
        return None

    name = _infer_project_name(root)
    entry_point = _infer_entry_point()

    # Mark sentinel FIRST so we don't loop on repeated failures.
    try:
        (root / ".myco_state").mkdir(parents=True, exist_ok=True)
        (root / ".myco_state" / "bootstrapped").write_text(
            f"auto-seeded at {name} via {entry_point}\n", encoding="utf-8"
        )
    except OSError:
        # Read-only filesystem or similar — abort silently.
        return None

    # Build args namespace matching seed_cmd.run_init expectations.
    class _Args:
        pass

    args = _Args()
    args.name = name
    args.dir = str(root)
    args.level = 1  # Standard: wiki/ + _canon.yaml + docs/
    args.entry_point = entry_point
    args.github_user = "user"
    args.agent = None
    args.auto_detect = False

    from myco.seed_cmd import run_init

    if silent:
        # Redirect stdout to keep MCP stdio clean.
        stash_out, stash_err = sys.stdout, sys.stderr
        sys.stdout = io.StringIO()
        sys.stderr = io.StringIO()
    try:
        run_init(args)
    except SystemExit:
        pass  # run_init may call sys.exit(0) — treat as success
    except Exception:
        if silent:
            sys.stdout, sys.stderr = stash_out, stash_err
        return None
    finally:
        if silent:
            sys.stdout, sys.stderr = stash_out, stash_err

    return {"name": name, "entry_point": entry_point, "level": 1}
