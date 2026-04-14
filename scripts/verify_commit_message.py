#!/usr/bin/env python3
"""
Verify commit message follows conventional-commits grammar.

Wave 58 / Wave 3: closes the auto-release loop. If a commit lands on
main without a conventional prefix, auto-release.yml silently skips
the bump — the maintainer thinks a release happened; it didn't.

This script exits 0 on valid messages, 1 on invalid. Wired into:
  - .git/hooks/commit-msg (optional, per-repo)
  - .github/workflows/lint-commits.yml (runs on PRs)

Valid prefixes:
    feat! | BREAKING | feat | fix | perf | refactor | docs | test
    chore | minor | style | build | ci
    chore(release): ...   (skipped by auto-release)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


VALID_PREFIXES = [
    r"feat!",
    r"BREAKING",
    r"feat",
    r"fix",
    r"perf",
    r"refactor",
    r"docs",
    r"test",
    r"chore",
    r"minor",
    r"style",
    r"build",
    r"ci",
    r"revert",
]

_PATTERN = re.compile(
    r"^(" + "|".join(VALID_PREFIXES) + r")(\([^)]+\))?:\s+\S",
)


def validate(msg: str) -> tuple[bool, str]:
    first = msg.strip().splitlines()[0] if msg.strip() else ""
    if not first:
        return False, "empty commit message"
    if first.startswith("Merge ") or first.startswith("Revert "):
        return True, ""  # default git messages ok
    if _PATTERN.match(first):
        return True, ""
    return False, (
        f"non-conventional first line: {first!r}\n"
        f"Expected one of: {', '.join(VALID_PREFIXES)} "
        f"(optional scope) then ': message'."
    )


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: verify_commit_message.py <msg-file-or-str>", file=sys.stderr)
        return 2
    arg = argv[1]
    p = Path(arg)
    if p.exists() and p.is_file():
        msg = p.read_text(encoding="utf-8", errors="replace")
    else:
        msg = arg
    ok, reason = validate(msg)
    if not ok:
        print(f"[commit-msg] {reason}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
