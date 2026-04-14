#!/usr/bin/env python3
"""
Generate CHANGELOG.md entry from conventional commits since a given tag.

Wave 55 (vision_closure_craft_2026-04-14.md §G9).

Usage:
    python scripts/generate_changelog.py --since v0.40.0 --version 0.41.0
    python scripts/generate_changelog.py --since v0.40.0 --version 0.41.0 --stdout
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from datetime import date


ROOT = Path(__file__).resolve().parent.parent
CHANGELOG = ROOT / "CHANGELOG.md"


CATEGORIES = [
    ("feat!", "Breaking Changes"),
    ("BREAKING", "Breaking Changes"),
    ("feat", "Features"),
    ("fix", "Bug Fixes"),
    ("perf", "Performance"),
    ("refactor", "Refactors"),
    ("docs", "Documentation"),
    ("test", "Tests"),
    ("chore", "Chores"),
]


def _resolve_since(since: str) -> str | None:
    """Resolve `since` to an existing ref, else fall back to most recent
    tag that IS reachable. Returns None if no tag exists at all.

    Wave 59 fix (2026-04-14): previously an unresolvable --since (e.g.
    v0.4.0 referenced but tag push had failed) fell through to a full
    `git log` which duplicated every commit into every subsequent
    release entry (v0.4.0/v0.5.0 both listed the same features). Now we
    walk back to the newest reachable tag instead of replaying history.
    """
    # Is `since` itself a real ref?
    try:
        subprocess.check_output(
            ["git", "rev-parse", "--verify", f"{since}^{{commit}}"],
            cwd=ROOT, stderr=subprocess.DEVNULL,
        )
        return since
    except subprocess.CalledProcessError:
        pass
    # Walk back through tags, newest first, pick the first one that resolves.
    try:
        tags = subprocess.check_output(
            ["git", "tag", "--sort=-creatordate"],
            cwd=ROOT, encoding="utf-8", errors="replace",
        ).splitlines()
    except subprocess.CalledProcessError:
        return None
    for tag in tags:
        tag = tag.strip()
        if not tag:
            continue
        try:
            subprocess.check_output(
                ["git", "rev-parse", "--verify", f"{tag}^{{commit}}"],
                cwd=ROOT, stderr=subprocess.DEVNULL,
            )
            return tag
        except subprocess.CalledProcessError:
            continue
    return None


def git_log(since: str) -> list[str]:
    # encoding="utf-8" + errors="replace" — avoid GBK decode errors on
    # Windows when commit messages contain non-ASCII (Chinese text,
    # em-dashes, etc.). text=True uses locale default which breaks on GBK.
    resolved = _resolve_since(since)
    if resolved is not None:
        out = subprocess.check_output(
            ["git", "log", f"{resolved}..HEAD", "--pretty=format:%s", "--no-merges"],
            cwd=ROOT,
            encoding="utf-8",
            errors="replace",
        )
    else:
        # No tags at all — first release. Emit full history.
        out = subprocess.check_output(
            ["git", "log", "--pretty=format:%s", "--no-merges"],
            cwd=ROOT,
            encoding="utf-8",
            errors="replace",
        )
    return [line for line in out.splitlines() if line.strip()]


def categorize(commits: list[str]) -> dict[str, list[str]]:
    buckets: dict[str, list[str]] = {}
    for msg in commits:
        # Skip release-chore commits
        if msg.startswith("chore(release):"):
            continue
        placed = False
        for prefix, label in CATEGORIES:
            # Match "prefix:" or "prefix(scope):"
            pattern = rf"^{re.escape(prefix)}(\(.+?\))?:"
            if re.match(pattern, msg):
                buckets.setdefault(label, []).append(msg)
                placed = True
                break
        if not placed:
            buckets.setdefault("Other", []).append(msg)
    return buckets


def render(version: str, buckets: dict[str, list[str]]) -> str:
    today = date.today().isoformat()
    lines = [f"## v{version} — {today}", ""]
    # Preserve category order
    label_order = ["Breaking Changes", "Features", "Bug Fixes", "Performance",
                   "Refactors", "Documentation", "Tests", "Chores", "Other"]
    for label in label_order:
        if label in buckets and buckets[label]:
            lines.append(f"### {label}")
            for msg in buckets[label]:
                lines.append(f"- {msg}")
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def prepend_to_changelog(entry: str) -> None:
    header = "# Changelog\n\nAll notable changes to this project are documented here.\nFormat follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).\n\n"
    if CHANGELOG.exists():
        existing = CHANGELOG.read_text(encoding="utf-8")
        # Strip existing header if present, keep prior entries
        if existing.startswith("# Changelog"):
            parts = existing.split("\n\n", 2)
            tail = parts[2] if len(parts) == 3 else ""
        else:
            tail = existing
        new_content = header + entry + "\n" + tail
    else:
        new_content = header + entry
    CHANGELOG.write_text(new_content, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", required=True, help="Tag to diff from (e.g. v0.40.0)")
    ap.add_argument("--version", required=True, help="New version string (no v prefix)")
    ap.add_argument("--stdout", action="store_true", help="Print to stdout instead of writing CHANGELOG.md")
    args = ap.parse_args()

    commits = git_log(args.since)
    buckets = categorize(commits)
    entry = render(args.version, buckets)

    if args.stdout:
        sys.stdout.write(entry)
    else:
        prepend_to_changelog(entry)
        print(f"Wrote v{args.version} entry to CHANGELOG.md ({sum(len(v) for v in buckets.values())} commits)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
