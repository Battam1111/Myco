"""
Myco autoseed — zero-friction first-contact initializer.

Wave 62 (v0.3.3): Plugin SessionStart hook expectation is that Myco
"just works" on any project the user opens. Historically `myco hunger`
raised MycoProjectNotFound when `_canon.yaml` was missing, which broke
session boot for unseeded projects. This module closes that gap by
providing a safe, minimal auto-seed invoked by hunger --execute when
no substrate is found.

Design principles:
1. **Minimal footprint**: create only `_canon.yaml` + `notes/` + `.myco_state/`.
   Do NOT touch entry-point files (CLAUDE.md / MYCO.md) — users may
   already have their own, or may not want one.
2. **Safety first**: only auto-seed when the target directory looks
   like a real project. Refuse home dirs, system dirs, and dirs with
   no project markers.
3. **Idempotent**: running autoseed twice on the same dir is a no-op.
4. **Opt-out**: env var MYCO_NO_AUTOSEED=1 disables auto-seed entirely.
5. **Visible**: every auto-seed emits a status record the caller can
   surface to the agent/user via JSON.

The seed content mirrors init_level_1 minimal subset from seed_cmd.py
(canon + notes/) but skips the heavier scaffolding (WORKFLOW.md, wiki/,
docs/primordia/, scripts/, entry-point file).
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any


# Project markers — presence of any one makes autoseed proceed.
# Kept in priority order (most specific first).
PROJECT_MARKERS = (
    ".git",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Gemfile",
    "requirements.txt",
    "setup.py",
    "Makefile",
    "CMakeLists.txt",
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    ".cursorrules",
)

# Directories we refuse to seed even if they pass marker checks.
# Protect against accidental seed of the user's home or system dirs.
BLOCKED_DIRS_ABSOLUTE = (
    "/",
    "/root",
    "/home",
    "/tmp",
    "/var",
    "/usr",
    "/etc",
    "/opt",
    "/bin",
    "/sbin",
    "/lib",
    "/lib64",
    "/dev",
    "/proc",
    "/sys",
    "/mnt",
    "/media",
)


def _looks_like_project(root: Path) -> tuple[bool, str]:
    """Return (ok, reason). ok=True means autoseed is safe to proceed."""
    try:
        resolved = root.resolve()
    except Exception as e:
        return False, f"could not resolve path: {e}"

    # Block literal system/home dirs
    resolved_str = str(resolved).replace("\\", "/")
    for blocked in BLOCKED_DIRS_ABSOLUTE:
        if resolved_str == blocked or resolved_str == blocked.rstrip("/"):
            return False, f"refusing to seed system/home dir: {resolved}"

    # Block the user's home dir itself (cross-platform)
    try:
        home = Path.home().resolve()
        if resolved == home:
            return False, f"refusing to seed home dir: {resolved}"
    except Exception:
        pass

    # Look for at least one project marker
    for marker in PROJECT_MARKERS:
        if (resolved / marker).exists():
            return True, f"marker found: {marker}"

    # Fallback: directory has at least one .md or source file (loose heuristic)
    try:
        for pattern in ("*.md", "*.py", "*.js", "*.ts", "*.go", "*.rs"):
            if any(resolved.glob(pattern)):
                return True, f"source file pattern matched: {pattern}"
    except Exception:
        pass

    return False, "no project markers found (not a project directory)"


# Minimal _canon.yaml content — one seed, one metabolism.
# Kept inline (not from template) to avoid template-path coupling and
# so autoseed has zero file dependencies beyond stdlib.
_MINIMAL_CANON_TEMPLATE = """# Myco canonical values — single source of truth.
# Auto-seeded by `myco hunger --execute` on first contact.
# Edit freely; this is yours.

project:
  name: {project_name}
  entry_point: {entry_point}
  autoseeded: true
  autoseed_version: "0.3.3"

system:
  notes_dir: notes
  write_surface:
    allowed:
      - "_canon.yaml"
      - "notes/**"
      - ".myco_state/**"
      - "log.md"
      - "CLAUDE.md"
      - "MYCO.md"
      - "AGENTS.md"
      - "wiki/**"
      - "docs/**"
  tests:
    test_dir: tests

dimensions:
  principles_count: 13
  lint_dimensions: 29
  mcp_tool_count: 25
"""


_MINIMAL_NOTES_README = """# notes/

Myco digestive substrate. Raw captures land here via `myco eat`;
digestion and compression happen in place.

This directory is created by autoseed — populate it by using
`myco eat` to capture decisions, insights, friction, and feedback
as you work.
"""


_GITIGNORE_ENTRIES = (
    "# Myco operational state",
    ".myco_state/",
)


def is_seeded(root: Path) -> bool:
    """True if `root` already has a Myco substrate."""
    return (root / "_canon.yaml").exists()


def autoseed(
    root: Path,
    *,
    force: bool = False,
    entry_point: str = "CLAUDE.md",
) -> Dict[str, Any]:
    """Attempt to auto-seed a minimal Myco substrate at `root`.

    Args:
        root: Target directory.
        force: If True, skip safety heuristic (still refuses system dirs).
        entry_point: Default entry-point filename to record in _canon.yaml.
            Does NOT create this file — only references it.

    Returns:
        {
            "seeded": bool,        # True if substrate now exists
            "action": str,         # "created" | "already_seeded" | "refused"
            "reason": str,         # human-readable why
            "root": str,           # resolved path
            "created": [str, ...], # paths created (relative to root)
        }
    """
    result: Dict[str, Any] = {
        "seeded": False,
        "action": "refused",
        "reason": "",
        "root": str(root),
        "created": [],
    }

    # Opt-out gate
    if os.environ.get("MYCO_NO_AUTOSEED") == "1":
        result["reason"] = "MYCO_NO_AUTOSEED=1 set"
        return result

    if is_seeded(root):
        result.update(
            seeded=True, action="already_seeded",
            reason="_canon.yaml exists",
        )
        return result

    # Safety heuristic — unless forced
    if not force:
        ok, reason = _looks_like_project(root)
        if not ok:
            result["reason"] = reason
            return result

    # Proceed with minimal seed
    try:
        root = Path(root).resolve()
        root.mkdir(parents=True, exist_ok=True)

        # _canon.yaml
        canon_path = root / "_canon.yaml"
        canon_path.write_text(
            _MINIMAL_CANON_TEMPLATE.format(
                project_name=root.name or "myco_project",
                entry_point=entry_point,
            ),
            encoding="utf-8",
        )
        result["created"].append("_canon.yaml")

        # notes/
        notes_dir = root / "notes"
        notes_dir.mkdir(exist_ok=True)
        notes_readme = notes_dir / "README.md"
        if not notes_readme.exists():
            notes_readme.write_text(_MINIMAL_NOTES_README, encoding="utf-8")
            result["created"].append("notes/README.md")

        # .myco_state/
        state_dir = root / ".myco_state"
        state_dir.mkdir(exist_ok=True)
        state_marker = state_dir / "autoseeded.txt"
        if not state_marker.exists():
            state_marker.write_text(
                "Auto-seeded by Myco v0.3.3 on first-contact hunger.\n"
                "This substrate is minimal. Run `myco seed --level 1` to\n"
                "upgrade to the full scaffolding (WORKFLOW.md, wiki/,\n"
                "docs/primordia/ etc).\n",
                encoding="utf-8",
            )
            result["created"].append(".myco_state/autoseeded.txt")

        # .gitignore append (non-destructive)
        gitignore = root / ".gitignore"
        if gitignore.exists():
            existing = gitignore.read_text(encoding="utf-8", errors="replace")
            needed = [e for e in _GITIGNORE_ENTRIES if e not in existing]
            if needed:
                with open(gitignore, "a", encoding="utf-8") as f:
                    if not existing.endswith("\n"):
                        f.write("\n")
                    f.write("\n" + "\n".join(needed) + "\n")
                result["created"].append(".gitignore (appended)")

        result.update(
            seeded=True,
            action="created",
            reason="minimal substrate created",
        )
    except Exception as e:
        result.update(
            seeded=False,
            action="refused",
            reason=f"seed failed: {type(e).__name__}: {e}",
        )

    return result
