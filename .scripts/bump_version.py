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

# Windows default console encoding is cp936 (gbk) or cp1252 — both
# fail on the `✓` / `→` glyphs the script uses for readability on
# Linux/macOS + modern Windows Terminal. Reconfigure stdout/stderr to
# UTF-8 with a `replace` error handler so the script never crashes
# on a decorative print, and falls back to a replacement char when a
# legacy console can't render the glyph. Python 3.7+ only.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (OSError, ValueError):
            pass

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
        help="Skip the trailing pytest + lint + type verification.",
    )
    parser.add_argument(
        "--no-lint",
        action="store_true",
        help="Skip ruff + mypy checks (still runs pytest unless --no-test).",
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
    changes += _bump_pyversion(
        REPO / "src" / "myco" / "__init__.py", target, args.dry_run
    )
    changes += _bump_plugin_json(
        REPO / ".claude-plugin" / "plugin.json", target, args.dry_run
    )
    # v0.8.5: The standalone `.cowork-plugin/.claude-plugin/plugin.json`
    # mirror was excreted. The Cowork .zip bundle is now derived from
    # `.claude-plugin/plugin.json` (the single source of truth) at
    # build time, so version stays in lockstep automatically — no
    # separate bump needed.
    # v0.8.4 root-cleanup (2026-05-12): CITATION.cff moved from repo
    # root to .github/ (GitHub's citation feature auto-discovers
    # either location). Path updated; bumping logic unchanged.
    changes += _bump_citation_cff(
        REPO / ".github" / "CITATION.cff", target, args.dry_run
    )
    # v0.8.4 root-cleanup (2026-05-12): server.json moved to .meta/.
    changes += _bump_server_json(REPO / ".meta" / "server.json", target, args.dry_run)
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

    # v0.7.3 — sync plugin mirrors. Idempotent; ensures
    # `.claude/{agents,commands}/X.md` ↔ `<repo>/{agents,commands}/X.md`
    # are byte-identical before the molt commit. Runs always (even
    # with --skip-molt) because the molt commit captures the synced
    # state regardless of whether contract bumps.
    sync_cmd = [sys.executable, "scripts/sync_plugin_mirrors.py"]
    print(f"\n→ [sync_plugin_mirrors] {' '.join(sync_cmd)}")
    rc = subprocess.call(sync_cmd, cwd=REPO)
    if rc != 0:
        _err(
            f"sync_plugin_mirrors failed (exit {rc}). "
            "Investigate before retrying the bump."
        )
        return 4

    # v0.7.5 — auto-refresh canon.metrics so test_count + lint_dim_count
    # never go stale. Replaces the manual "remember to update canon.metrics"
    # step that drifted between v0.7.0 and v0.7.4 (test_count fell out of
    # sync with reality by 2; lint_dim_count was missing entirely while
    # all 3 READMEs advertised an outdated 46 instead of the real 50).
    # Reads live measurements (pytest --collect-only + _canon_lint.yaml
    # dimension count) and surgically rewrites just those two lines.
    refresh_changes = _refresh_canon_metrics(REPO, dry_run=False)
    print()
    for line in refresh_changes:
        print("  " + line)

    if not args.no_test:
        # Mirror ci.yml's "test" job exactly so the bump pre-flight
        # catches everything CI would catch. Historical gap: v0.5.13
        # prep missed `ruff format --check` locally because only
        # `ruff check` was in the mental checklist; CI caught it on
        # the push. Running the full quintet here closes the gap.
        gates: list[tuple[str, list[str]]] = []
        if not args.no_lint:
            gates.append(
                ("ruff lint", [sys.executable, "-m", "ruff", "check", "src", "tests"])
            )
            gates.append(
                (
                    "ruff format (check only)",
                    [sys.executable, "-m", "ruff", "format", "--check", "src", "tests"],
                )
            )
            gates.append(("mypy", [sys.executable, "-m", "mypy", "src/myco"]))
        gates.append(
            (
                "pytest",
                [sys.executable, "-m", "pytest", "tests", "-q", "-x", "--no-header"],
            )
        )
        gates.append(("myco immune", [sys.executable, "-m", "myco", "immune"]))

        for label, cmd in gates:
            print(f"\n→ [{label}] {' '.join(cmd)}")
            rc = subprocess.call(cmd, cwd=REPO)
            if rc != 0:
                _err(
                    f"{label} failed (exit {rc}). The bump left your worktree "
                    "modified; inspect + `git restore` to roll back, fix the "
                    "underlying issue, then re-run the bump."
                )
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
        return [
            f"[skip]  {_rel(path)} already at {target} ({len(before_matches)} line(s))"
        ]
    new = re.sub(pattern, rf'\1"{target}"\3', text)
    if not dry_run:
        path.write_text(new, encoding="utf-8")
    distinct_before = {v for _, v in before_matches}
    return [
        f"[bump]  {_rel(path)} version {sorted(distinct_before)} → {target} "
        f"({len(before_matches)} line(s))"
    ]


def _measure_test_count(repo: Path) -> int | None:
    """Count tests via ``pytest --collect-only -q``; parse "N tests collected"."""
    try:
        r = subprocess.run(
            [sys.executable, "-m", "pytest", "--collect-only", "-q", "tests"],
            cwd=repo,
            capture_output=True,
            text=True,
            check=False,
            timeout=120,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None
    if r.returncode != 0:
        return None
    # "N tests collected in T s" — last line of stdout in -q mode.
    m = re.search(r"^(\d+) tests collected", r.stdout, re.MULTILINE)
    return int(m.group(1)) if m else None


def _measure_lint_dim_count(repo: Path) -> int | None:
    """Count lint dims by reading ``.myco/canon_lint.yaml::dimensions`` keys.

    v0.8.4 root-cleanup (2026-05-12): the lint-dimension SSoT moved from
    repo-root ``_canon_lint.yaml`` to ``.myco/canon_lint.yaml`` (referenced
    from canon via ``lint.dimensions_ref``). Falls back to the legacy
    location for any downstream substrate still on the pre-v0.8.4 layout.
    """
    path = repo / ".myco" / "canon_lint.yaml"
    if not path.is_file():
        # Legacy fallback for downstream substrates on pre-v0.8.4 layout.
        path = repo / "_canon_lint.yaml"
    if not path.is_file():
        return None
    try:
        import yaml as _yaml  # type: ignore[import-not-found]
    except ImportError:
        return None
    try:
        data = _yaml.safe_load(path.read_text(encoding="utf-8"))
    except (_yaml.YAMLError, OSError):
        return None
    dims = data.get("dimensions") if isinstance(data, dict) else None
    if isinstance(dims, dict):
        return len(dims)
    if isinstance(dims, list):
        return len(dims)
    return None


def _refresh_canon_metrics(repo: Path, *, dry_run: bool) -> list[str]:
    """Surgically refresh ``canon::metrics.{test_count,lint_dim_count}``.

    Reads live measurements (pytest --collect-only count + canon_lint dim
    count) and rewrites just the two target lines via regex. Same surgical
    approach as :func:`_bump_pyversion` so YAML comments + structure are
    preserved. If a measurement fails (e.g. pytest can't be invoked), that
    metric is left untouched — better stale than wrong.

    Inserts ``lint_dim_count: <N>`` if the line is absent and the new
    schema_version "3" is targeted (v0.7.5+). Insertion point: right after
    the ``test_count:`` line within the ``metrics:`` block.

    v0.8.5 — canon may live at ``.myco/canon.yaml`` (Myco-self / v0.8.4+)
    or ``_canon.yaml`` (legacy / downstream). Probe both, same pattern as
    sync_plugin_mirrors.py.
    """
    canon_path = repo / ".myco" / "canon.yaml"
    if not canon_path.is_file():
        canon_path = repo / "_canon.yaml"
    if not canon_path.is_file():
        return [f"[skip]  {_rel(canon_path)} (file missing)"]

    text = canon_path.read_text(encoding="utf-8")
    changes: list[str] = []

    # Refresh test_count.
    measured_tests = _measure_test_count(repo)
    if measured_tests is not None:
        pattern = r"(?m)^(\s*test_count:\s*)(\d+)([ \t\r]*)$"
        m = re.search(pattern, text)
        if m and int(m.group(2)) != measured_tests:
            text = re.sub(pattern, rf"\g<1>{measured_tests}\g<3>", text, count=1)
            changes.append(
                f"[refresh] {_rel(canon_path)} metrics.test_count {m.group(2)} → "
                f"{measured_tests}"
            )
        elif m:
            changes.append(
                f"[skip]    {_rel(canon_path)} metrics.test_count already at "
                f"{measured_tests}"
            )
    else:
        changes.append(
            "[skip]    metrics.test_count refresh (pytest --collect-only failed; "
            "left as-is)"
        )

    # Refresh or insert lint_dim_count.
    measured_dims = _measure_lint_dim_count(repo)
    if measured_dims is not None:
        pattern = r"(?m)^(\s*lint_dim_count:\s*)(\d+|null)([ \t\r]*)$"
        m = re.search(pattern, text)
        if m:
            current = m.group(2)
            if current != str(measured_dims):
                text = re.sub(pattern, rf"\g<1>{measured_dims}\g<3>", text, count=1)
                changes.append(
                    f"[refresh] {_rel(canon_path)} metrics.lint_dim_count "
                    f"{current} → {measured_dims}"
                )
            else:
                changes.append(
                    f"[skip]    {_rel(canon_path)} metrics.lint_dim_count "
                    f"already at {measured_dims}"
                )
        else:
            # Insert new line right after test_count: <N>. Required for
            # v3 schema (lint_dim_count is a v0.7.5 v2 → v3 addition).
            insert_pattern = r"(?m)^(\s*)(test_count:\s*\d+[ \t\r]*)$"
            m_insert = re.search(insert_pattern, text)
            if m_insert:
                indent = m_insert.group(1)
                replacement = (
                    f"{indent}{m_insert.group(2)}\n"
                    f"{indent}lint_dim_count: {measured_dims}"
                )
                text = re.sub(insert_pattern, replacement, text, count=1)
                changes.append(
                    f"[insert]  {_rel(canon_path)} metrics.lint_dim_count: "
                    f"{measured_dims} (new field)"
                )
            else:
                changes.append(
                    "[skip]    metrics.lint_dim_count insert (no test_count: "
                    "anchor found in canon)"
                )
    else:
        changes.append(
            "[skip]    metrics.lint_dim_count refresh (canon_lint.yaml unreadable)"
        )

    if (
        not dry_run
        and changes
        and any(c.startswith("[refresh]") or c.startswith("[insert]") for c in changes)
    ):
        canon_path.write_text(text, encoding="utf-8")

    return changes


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
