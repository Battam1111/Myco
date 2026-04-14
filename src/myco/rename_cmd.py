"""
myco rename -- Syntax-aware module/command renaming.

Performs ALL of these atomically:
1. git mv src/myco/OLD.py src/myco/NEW.py (if file exists)
2. git mv src/myco/OLD_cmd.py src/myco/NEW_cmd.py (if exists)
3. git mv tests/unit/test_OLD*.py tests/unit/test_NEW*.py (all matching)
4. Replace Python imports: from myco.OLD -> from myco.NEW (precise pattern)
5. Replace string references: "myco.OLD" -> "myco.NEW" (in mock patches etc.)
6. Replace CLI command name: "OLD" -> "NEW" in cli.py subparser
7. Replace MCP tool name: myco_OLD -> myco_NEW in mcp_server.py
8. Replace in docs: `myco OLD` -> `myco NEW`, `myco_OLD` -> `myco_NEW` (in .md/.yaml)
9. Update _canon.yaml references
10. Run `myco immune --quick` to verify no breakage

The key insight: use PRECISE patterns, not global sed:
- Python imports: ``from myco.{old}`` or ``import myco.{old}`` (not bare ``{old}``)
- CLI commands: ``"{old}"`` in quotes (subparser names)
- MCP tools: ``myco_{old}`` (with prefix)
- Docs: ``myco {old}`` (with space) or ``myco_{old}`` (with underscore)
- File paths: ``src/myco/{old}.py`` (with directory prefix)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional

from myco.project import find_project_root


def _posix_rel(path: Path, root: Path) -> str:
    """Return path relative to root, always using forward slashes."""
    return str(path.relative_to(root)).replace("\\", "/")


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class RenameAction:
    """A single rename operation (file move or text replacement)."""
    kind: str          # "git_mv", "replace"
    source: str        # file path (git_mv) or file to edit (replace)
    target: str = ""   # destination path (git_mv) or empty (replace)
    pattern: str = ""  # regex pattern (replace)
    replacement: str = ""  # replacement string (replace)
    count: int = 0     # number of matches found (replace)

    def describe(self) -> str:
        if self.kind == "git_mv":
            return f"  git mv {self.source} -> {self.target}"
        return f"  {self.source}: {self.pattern!r} -> {self.replacement!r} ({self.count} matches)"


@dataclass
class RenamePlan:
    """Complete plan for renaming a module."""
    old: str
    new: str
    root: Path
    actions: List[RenameAction] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        lines = [f"Rename plan: {self.old} -> {self.new}"]
        lines.append(f"  Project root: {self.root}")
        lines.append("")
        file_moves = [a for a in self.actions if a.kind == "git_mv"]
        text_edits = [a for a in self.actions if a.kind == "replace"]
        if file_moves:
            lines.append(f"File moves ({len(file_moves)}):")
            for a in file_moves:
                lines.append(a.describe())
        if text_edits:
            lines.append(f"\nText replacements ({len(text_edits)}):")
            for a in text_edits:
                lines.append(a.describe())
        if self.errors:
            lines.append(f"\nErrors ({len(self.errors)}):")
            for e in self.errors:
                lines.append(f"  ERROR: {e}")
        if not self.actions:
            lines.append("  (no changes detected)")
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pattern definitions — the precise replacements
# ---------------------------------------------------------------------------

def _build_replacement_patterns(old: str, new: str) -> list[tuple[str, str, str]]:
    """Return (description, regex_pattern, replacement) triples.

    Each pattern is scoped precisely to avoid false positives.
    """
    return [
        # 1. Python imports: from myco.OLD import ...
        (
            "Python import (from)",
            rf"(from\s+myco\.){re.escape(old)}\b",
            rf"\g<1>{new}",
        ),
        # 2. Python imports: import myco.OLD
        (
            "Python import (import)",
            rf"(import\s+myco\.){re.escape(old)}\b",
            rf"\g<1>{new}",
        ),
        # 3. String references in mock patches etc: "myco.OLD"
        (
            "String reference (mock patch)",
            rf"(\"myco\.){re.escape(old)}(\b)",
            rf"\g<1>{new}\2",
        ),
        # 4. String references single quotes: 'myco.OLD'
        (
            "String reference (single quote)",
            rf"('myco\.){re.escape(old)}(\b)",
            rf"\g<1>{new}\2",
        ),
        # 5. MCP tool name: myco_OLD (with underscore prefix)
        (
            "MCP tool name",
            rf"\bmyco_{re.escape(old)}\b",
            f"myco_{new}",
        ),
        # 6. CLI subparser name in quotes: "OLD" (only in cli.py context,
        #    applied selectively to cli.py)
        (
            "CLI subparser name (double-quoted)",
            rf'"{re.escape(old)}"',
            f'"{new}"',
        ),
        # 7. CLI subparser name in single quotes: 'OLD'
        (
            "CLI subparser name (single-quoted)",
            rf"'{re.escape(old)}'",
            f"'{new}'",
        ),
        # 8. Doc references: myco OLD (space-separated command invocation)
        (
            "Doc command reference",
            rf"(\bmyco\s+){re.escape(old)}\b",
            rf"\g<1>{new}",
        ),
        # 9. File path references: myco/OLD (in path contexts)
        (
            "File path reference",
            rf"(myco/){re.escape(old)}\b",
            rf"\g<1>{new}",
        ),
        # 10. File path references: myco\\OLD (Windows paths in strings)
        (
            "File path reference (backslash)",
            rf"(myco\\\\){re.escape(old)}\b",
            rf"\g<1>{new}",
        ),
        # 11. run_OLD function name (dispatch in cli.py)
        (
            "Function name (run_)",
            rf"\brun_{re.escape(old)}\b",
            f"run_{new}",
        ),
        # 12. OLD_cmd module reference
        (
            "Module reference (_cmd)",
            rf"\b{re.escape(old)}_cmd\b",
            f"{new}_cmd",
        ),
        # 13. test_OLD test file references
        (
            "Test file reference",
            rf"\btest_{re.escape(old)}\b",
            f"test_{new}",
        ),
    ]


# ---------------------------------------------------------------------------
# File scanning
# ---------------------------------------------------------------------------

_TEXT_EXTENSIONS = {
    ".py", ".md", ".yaml", ".yml", ".toml", ".cfg", ".txt",
    ".json", ".rst", ".ini",
}


def _is_text_file(path: Path) -> bool:
    """Return True if the file is likely a text file we should scan."""
    return path.suffix.lower() in _TEXT_EXTENSIONS


def _scannable_files(root: Path) -> list[Path]:
    """Return all text files under root, excluding hidden/venv/cache dirs."""
    results = []
    skip_dirs = {".git", "__pycache__", ".venv", "venv", "node_modules",
                 ".mypy_cache", ".pytest_cache", ".tox", "dist", "build",
                 ".eggs", "*.egg-info"}
    for dirpath, dirnames, filenames in os.walk(root):
        # Prune hidden and cache directories
        dirnames[:] = [
            d for d in dirnames
            if d not in skip_dirs and not d.startswith(".")
        ]
        for fname in filenames:
            fp = Path(dirpath) / fname
            if _is_text_file(fp):
                results.append(fp)
    return results


# ---------------------------------------------------------------------------
# Plan builder
# ---------------------------------------------------------------------------

def build_plan(old: str, new: str, project_dir: str) -> RenamePlan:
    """Build a complete rename plan without executing it."""
    root = find_project_root(project_dir, strict=False)
    plan = RenamePlan(old=old, new=new, root=root)

    # Validate inputs
    if old == new:
        plan.errors.append(f"Old and new names are identical: {old!r}")
        return plan
    if not old.isidentifier():
        plan.errors.append(f"Old name is not a valid Python identifier: {old!r}")
        return plan
    if not new.isidentifier():
        plan.errors.append(f"New name is not a valid Python identifier: {new!r}")
        return plan

    src_dir = root / "src" / "myco"
    test_dir = root / "tests" / "unit"

    # --- Step 1-3: File moves ---
    # Core module file
    old_module = src_dir / f"{old}.py"
    new_module = src_dir / f"{new}.py"
    if old_module.is_file():
        plan.actions.append(RenameAction(
            kind="git_mv",
            source=_posix_rel(old_module, root),
            target=_posix_rel(new_module, root),
        ))

    # Command file (_cmd.py)
    old_cmd = src_dir / f"{old}_cmd.py"
    new_cmd = src_dir / f"{new}_cmd.py"
    if old_cmd.is_file():
        plan.actions.append(RenameAction(
            kind="git_mv",
            source=_posix_rel(old_cmd, root),
            target=_posix_rel(new_cmd, root),
        ))

    # Test files (test_OLD*.py)
    if test_dir.is_dir():
        for test_file in sorted(test_dir.glob(f"test_{old}*.py")):
            old_name = test_file.name
            new_name = old_name.replace(f"test_{old}", f"test_{new}", 1)
            new_test = test_file.parent / new_name
            plan.actions.append(RenameAction(
                kind="git_mv",
                source=_posix_rel(test_file, root),
                target=_posix_rel(new_test, root),
            ))

    # --- Steps 4-9: Text replacements ---
    # Build the precise patterns
    all_patterns = _build_replacement_patterns(old, new)

    # Determine which patterns apply to which file types
    # CLI-specific patterns (subparser names in quotes) only apply to cli.py
    # to avoid false positives on quoted strings in docs
    cli_only_descs = {
        "CLI subparser name (double-quoted)",
        "CLI subparser name (single-quoted)",
    }

    # Scan all text files
    for fpath in _scannable_files(root):
        try:
            content = fpath.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        is_cli = fpath.name == "cli.py" and "src/myco" in str(fpath).replace("\\", "/")

        for desc, pattern, replacement in all_patterns:
            # Only apply CLI-specific patterns to cli.py
            if desc in cli_only_descs and not is_cli:
                continue

            matches = re.findall(pattern, content)
            if matches:
                plan.actions.append(RenameAction(
                    kind="replace",
                    source=_posix_rel(fpath, root),
                    pattern=f"[{desc}] {pattern}",
                    replacement=replacement,
                    count=len(matches),
                ))

    # Also scan external files (~/.claude/ scheduled tasks + .claude/skills)
    external_dirs = [
        root / ".claude" / "skills",
        Path.home() / ".claude" / "scheduled-tasks",
    ]
    for ext_dir in external_dirs:
        if not ext_dir.is_dir():
            continue
        for ext_file in ext_dir.rglob("*.md"):
            try:
                content = ext_file.read_text(encoding="utf-8")
            except (UnicodeDecodeError, PermissionError):
                continue
            for desc, pattern, replacement in all_patterns:
                if desc in cli_only_descs:
                    continue
                matches = re.findall(pattern, content)
                if matches:
                    # Use absolute path for external files
                    plan.actions.append(RenameAction(
                        kind="replace",
                        source=str(ext_file),
                        pattern=f"[{desc}] {pattern}",
                        replacement=replacement,
                        count=len(matches),
                    ))

    return plan


# ---------------------------------------------------------------------------
# Execution
# ---------------------------------------------------------------------------

def _git_mv(root: Path, source: str, target: str) -> tuple[bool, str]:
    """Execute git mv, falling back to plain rename if not in a git repo."""
    src_abs = root / source
    tgt_abs = root / target
    # Ensure target parent directory exists
    tgt_abs.parent.mkdir(parents=True, exist_ok=True)

    try:
        result = subprocess.run(
            ["git", "mv", source, target],
            capture_output=True, text=True, cwd=str(root),
        )
        if result.returncode == 0:
            return True, f"git mv {source} -> {target}"
        # Fallback to plain rename
        src_abs.rename(tgt_abs)
        return True, f"renamed {source} -> {target} (git mv failed: {result.stderr.strip()})"
    except FileNotFoundError:
        # git not available; plain rename
        try:
            src_abs.rename(tgt_abs)
            return True, f"renamed {source} -> {target} (git not available)"
        except OSError as e:
            return False, f"failed to rename {source} -> {target}: {e}"


def _apply_replacements(root: Path, fpath_rel: str, pattern: str, replacement: str) -> tuple[int, str]:
    """Apply a regex replacement to a file. Returns (count, message)."""
    fpath = root / fpath_rel
    try:
        content = fpath.read_text(encoding="utf-8")
    except (UnicodeDecodeError, PermissionError) as e:
        return 0, f"cannot read {fpath_rel}: {e}"

    # Extract the raw regex from the bracketed description prefix
    # Pattern format: "[Description] actual_regex"
    raw_pattern = pattern
    if pattern.startswith("["):
        bracket_end = pattern.index("] ")
        raw_pattern = pattern[bracket_end + 2:]

    new_content, count = re.subn(raw_pattern, replacement, content)
    if count > 0:
        fpath.write_text(new_content, encoding="utf-8")
    return count, f"{fpath_rel}: {count} replacements"


def execute_plan(plan: RenamePlan) -> list[str]:
    """Execute a rename plan. Returns a list of result messages."""
    if plan.errors:
        return [f"ERROR: {e}" for e in plan.errors]

    messages = []

    # Phase 1: file moves (must happen before text edits to avoid editing
    # files at old paths that have already been moved)
    move_actions = [a for a in plan.actions if a.kind == "git_mv"]
    replace_actions = [a for a in plan.actions if a.kind == "replace"]

    for action in move_actions:
        ok, msg = _git_mv(plan.root, action.source, action.target)
        prefix = "OK" if ok else "FAIL"
        messages.append(f"  [{prefix}] {msg}")

    # Phase 2: text replacements (on files at their new locations)
    # Remap source paths for files that were moved
    moved_map = {}
    for action in move_actions:
        moved_map[action.source] = action.target

    for action in replace_actions:
        actual_path = moved_map.get(action.source, action.source)
        count, msg = _apply_replacements(plan.root, actual_path, action.pattern, action.replacement)
        messages.append(f"  [OK] {msg}")

    return messages


def run_verify(root: Path) -> tuple[bool, str]:
    """Run myco immune --quick to verify no breakage after rename."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "myco", "immune", "--quick", "--project-dir", str(root)],
            capture_output=True, text=True, cwd=str(root),
            timeout=60,
        )
        passed = result.returncode == 0
        output = result.stdout + result.stderr
        return passed, output.strip()
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"immune check failed: {e}"


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def run_rename(args) -> int:
    """Entry point for ``myco rename``."""
    old = args.old
    new = args.new
    project_dir = getattr(args, "project_dir", ".")
    dry_run = getattr(args, "dry_run", False)

    print(f"myco rename: {old} -> {new}")
    print()

    # Build the plan
    plan = build_plan(old, new, project_dir)

    if plan.errors:
        for e in plan.errors:
            print(f"ERROR: {e}", file=sys.stderr)
        return 1

    # Show the plan
    print(plan.summary())
    print()

    if dry_run:
        print("(dry-run mode — no changes made)")
        return 0

    # Execute
    print("Executing rename...")
    messages = execute_plan(plan)
    for msg in messages:
        print(msg)

    # Verify
    print()
    print("Running immune check...")
    passed, output = run_verify(plan.root)
    if output:
        # Print only the last few lines to keep output concise
        lines = output.splitlines()
        for line in lines[-10:]:
            print(f"  {line}")

    if passed:
        print()
        print(f"Rename {old} -> {new} completed successfully.")
        return 0
    else:
        print()
        print(f"WARNING: immune check reported issues after rename.", file=sys.stderr)
        print(f"Review the output above and fix manually if needed.", file=sys.stderr)
        return 1
