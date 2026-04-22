#!/usr/bin/env python
"""Atomic version bump across every version-carrying file in the substrate.

Myco's contract_version + package version + plugin manifest version
+ CITATION.cff version + server.json (root + packages[0]) version
must all move in lockstep at release time. ``.github/workflows/release.yml``
verifies this alignment on every tag push and refuses to publish when
any file is out of sync, but that only catches drift after it has
already been committed.

This script is the pre-commit side of that gate: one command moves
every knob at once and then hands off to ``myco molt`` to update the
canon + contract changelog. It refuses to run against a dirty git
worktree (so rollback is always ``git restore``) and refuses to
downgrade without ``--allow-downgrade``.

Usage::

    python scripts/bump_version.py --to 0.5.13
    python scripts/bump_version.py --to 0.5.13 --dry-run

After a successful run, the only remaining ceremony is:

  1. Open ``docs/contract_changelog.md`` and replace the auto-stubbed
     ``(Fill in: ...)`` paragraphs with the real narrative for this
     release — the Release workflow uses that section as the
     GitHub-release body via the ``contract_changelog.md`` fallback.
  2. ``git add -A && git commit -m 'vX.Y.Z — <summary>'``
  3. ``git tag vX.Y.Z``
  4. ``git push origin main vX.Y.Z``
  5. Watch the Release workflow fan out to PyPI + MCP Registry +
     GitHub release (~3 min).

Exit codes follow Myco's conventions (see ``MycoError``):
  0  success
  3  usage / validation error (bad semver, downgrade, dirty worktree)
  4  dependency error (myco molt failed, pytest failed)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

# Permissive-ish semver (majors + minors + patch). Pre-release and
# build-metadata tails are allowed so we accept 0.6.0-rc1 / 1.0.0+gitsha
# forms transparently — same class the PyPI version parser accepts.
SEMVER_RE = re.compile(r"^(\d+)\.(\d+)\.(\d+)(?:[-+].*)?$")


# ------------------------------------------------------------------ main


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atomic Myco version bump across all version-carrying files.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--to",
        required=True,
        metavar="VERSION",
        help="Target semver version without leading 'v' (e.g. 0.5.13 or 0.6.0-rc1).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the diff that would be written; do not touch any file.",
    )
    parser.add_argument(
        "--allow-downgrade",
        action="store_true",
        help="Permit writing a version lower than the current one (dangerous).",
    )
    parser.add_argument(
        "--skip-molt",
        action="store_true",
        help="Skip the trailing `myco molt --contract vX.Y.Z` step.",
    )
    parser.add_argument(
        "--no-test",
        action="store_true",
        help="Skip the trailing `pytest tests -q -x` verification.",
    )
    args = parser.parse_args()

    target = args.to.lstrip("v").strip()
    if not SEMVER_RE.match(target):
        _err(f"not a valid semver string: {target!r}")
        return 3

    current = _read_current_version()
    print(f"current version: {current}")
    print(f"target version:  {target}")

    if current == target:
        print("already at target; nothing to do.")
        return 0

    if not args.allow_downgrade and _as_tuple(target) < _as_tuple(current):
        _err(
            f"{target} is a downgrade from {current}. Pass --allow-downgrade "
            "if this is intentional (it almost never is)."
        )
        return 3

    if not args.dry_run and not _git_worktree_clean():
        _err(
            "git worktree is not clean. Stash or commit pending changes first "
            "so the bump is a single reviewable commit."
        )
        return 3

    print()  # blank line before diff
    changes: list[str] = []
    changes += _bump_pyversion(REPO / "src" / "myco" / "__init__.py", target, args.dry_run)
    changes += _bump_plugin_json(REPO / ".claude-plugin" / "plugin.json", target, args.dry_run)
    changes += _bump_citation_cff(REPO / "CITATION.cff", target, args.dry_run)
    changes += _bump_server_json(REPO / "server.json", target, args.dry_run)
    for line in changes:
        print("  " + line)

    if args.dry_run:
        print("\n(dry-run; no files written, no subcommands run.)")
        return 0

    if not args.skip_molt:
        cmd = [sys.executable, "-m", "myco", "molt", "--contract", f"v{target}"]
        print(f"\n→ {' '.join(cmd)}")
        rc = subprocess.call(cmd, cwd=REPO)
        if rc != 0:
            _err(
                f"myco molt failed (exit {rc}). "
                "Inspect with `git diff` + `git restore` to roll back."
            )
            return 4

    if not args.no_test:
        cmd = [sys.executable, "-m", "pytest", "tests", "-q", "-x", "--no-header"]
        print(f"\n→ {' '.join(cmd)}")
        rc = subprocess.call(cmd, cwd=REPO)
        if rc != 0:
            _err(f"pytest failed (exit {rc}). The bump left your worktree modified; inspect + fix.")
            return 4

    print(f"\n✓ bumped: {current} → {target}")
    print(
        "next: replace the auto-stubbed `(Fill in: ...)` block in "
        "docs/contract_changelog.md, commit, tag v"
        + target
        + ", push main + tag. Release workflow handles the rest."
    )
    return 0


# --------------------------------------------------------------- helpers


def _err(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)


def _read_current_version() -> str:
    text = (REPO / "src" / "myco" / "__init__.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__ = "([^"]+)"\s*$', text, re.MULTILINE)
    if m is None:
        raise RuntimeError("cannot locate __version__ in src/myco/__init__.py")
    return m.group(1)


def _as_tuple(v: str) -> tuple[int, int, int]:
    m = SEMVER_RE.match(v)
    if m is None:
        return (0, 0, 0)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _git_worktree_clean() -> bool:
    try:
        r = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=REPO,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        # No git on PATH; don't block the bump — user is in a tarball build or similar.
        print("warning: git not found; skipping worktree-clean check.", file=sys.stderr)
        return True
    return r.returncode == 0 and not r.stdout.strip()


def _rel(p: Path) -> str:
    try:
        return str(p.relative_to(REPO).as_posix())
    except ValueError:
        return str(p)


# ---------------------------------------------------------- file bumpers


def _bump_pyversion(path: Path, target: str, dry_run: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    # Capture trailing whitespace (CR, spaces, tabs) in group 3 so the
    # rewrite preserves CRLF line endings and any trailing newline the
    # file happens to have. `\s*$` without capture would silently eat
    # the newline, changing file hash even when only the version moved.
    pattern = r'(?m)^(__version__ = )"([^"]+)"([ \t\r]*)$'
    m = re.search(pattern, text)
    if m is None:
        return [f"[skip]  {_rel(path)} (no __version__ line)"]
    if m.group(2) == target:
        return [f"[skip]  {_rel(path)} already at {target}"]
    new = re.sub(pattern, rf'\1"{target}"\3', text, count=1)
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    return [f"[bump]  {_rel(path)} __version__ {m.group(2)} → {target}"]


def _bump_plugin_json(path: Path, target: str, dry_run: bool) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    before = data.get("version")
    if before == target:
        return [f"[skip]  {_rel(path)} already at {target}"]
    data["version"] = target
    if not dry_run:
        # Match existing file style: 2-space indent, LF newlines, trailing newline.
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return [f"[bump]  {_rel(path)} version {before} → {target}"]


def _bump_citation_cff(path: Path, target: str, dry_run: bool) -> list[str]:
    text = path.read_text(encoding="utf-8")
    # CITATION.cff has two `version: "..."` lines: one at the top
    # level and one inside `preferred-citation:`. Both must move.
    # Match horizontal whitespace + CR only (not LF) so we preserve
    # the newline — same reasoning as in _bump_pyversion.
    pattern = r'(?m)^(\s*version: )"([^"]+)"([ \t\r]*)$'
    before_matches = [(lead, ver) for lead, ver, _ in re.findall(pattern, text)]
    if not before_matches:
        return [f"[skip]  {_rel(path)} (no version: lines)"]
    if all(v == target for _, v in before_matches):
        return [f"[skip]  {_rel(path)} already at {target} ({len(before_matches)} line(s))"]
    new = re.sub(pattern, rf'\1"{target}"\3', text)
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    distinct_before = {v for _, v in before_matches}
    return [
        f"[bump]  {_rel(path)} version {sorted(distinct_before)} → {target} "
        f"({len(before_matches)} line(s))"
    ]


def _bump_server_json(path: Path, target: str, dry_run: bool) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    changed: list[str] = []
    before_top = data.get("version")
    if before_top != target:
        data["version"] = target
        changed.append(f"version {before_top} → {target}")
    for i, pkg in enumerate(data.get("packages", [])):
        before_pkg = pkg.get("version")
        if before_pkg != target:
            pkg["version"] = target
            changed.append(f"packages[{i}].version {before_pkg} → {target}")
    if not changed:
        return [f"[skip]  {_rel(path)} already at {target}"]
    if not dry_run:
        path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return [f"[bump]  {_rel(path)} " + "; ".join(changed)]


if __name__ == "__main__":
    raise SystemExit(main())
