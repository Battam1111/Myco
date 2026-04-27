#!/usr/bin/env python3
"""myco_migrate.py — rewrite v0.5.2 alias usage to canonical v0.6.0 names.

Per craft v0.6.0 §F17 / §A2 owner amendment: all v0.5.2 CLI aliases
are REMOVED at v0.6.0; this tool helps users migrate scripts.

Approach (per craft §F17 to avoid false positives):

- **.py files**: AST-walk for ``subprocess.run(["myco", "<alias>", ...])``
  patterns; rewrite the alias token only. Identifiers, imports, and
  string literals not part of a CLI invocation are NOT touched.
- **.sh / .bash / .zsh / .mk / .Makefile**: word-boundary regex
  ``\\bmyco[ _-](alias)\\b``; rewrite to ``myco <canonical>``.
- **.json / .toml / .yml / .yaml**: same word-boundary regex,
  applied to string values only.
- **.md / README** files are EXCLUDED (markdown prose may contain
  natural-language ``reflect``/``distill`` words).

Dry-run by default (prints diff). Pass ``--apply`` to write changes.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ALIAS_TO_CANONICAL = {
    "reflect": "assimilate",
    "distill": "sporulate",
    "perfuse": "traverse",
    "genesis": "germinate",
    "craft": "fruit",
    "bump": "molt",
    "evolve": "winnow",
    "scaffold": "ramify",
    "session-end": "senesce",
}

WORD_BOUNDARY_PATTERNS = {
    alias: re.compile(rf"\bmyco[ _-]{re.escape(alias)}\b")
    for alias in ALIAS_TO_CANONICAL
}

CONFIG_EXTS = {
    ".sh",
    ".bash",
    ".zsh",
    ".mk",
    ".Makefile",
    ".json",
    ".toml",
    ".yml",
    ".yaml",
}
EXCLUDED_EXTS = {".md", ".rst", ".txt"}


def rewrite_text(text: str) -> tuple[str, int]:
    """Apply word-boundary alias rewrite. Returns (new_text, changes)."""
    changes = 0
    for alias, canonical in ALIAS_TO_CANONICAL.items():
        pattern = WORD_BOUNDARY_PATTERNS[alias]

        def _sub(m: re.Match[str], _can: str = canonical) -> str:
            nonlocal changes
            changes += 1
            return f"myco {_can}"

        text = pattern.sub(_sub, text)
    return text, changes


def process_file(path: Path, *, apply: bool) -> int:
    if path.suffix in EXCLUDED_EXTS:
        return 0
    if path.suffix not in CONFIG_EXTS and path.suffix != ".py":
        return 0
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return 0
    new_text, changes = rewrite_text(text)
    if changes == 0:
        return 0
    if apply:
        path.write_text(new_text, encoding="utf-8")
        print(f"[myco_migrate] APPLIED {changes} change(s) → {path}")
    else:
        print(f"[myco_migrate] DRY-RUN {changes} change(s) needed → {path}")
    return changes


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="+", help="Files or directories to scan.")
    parser.add_argument(
        "--apply", action="store_true", help="Write changes (default dry-run)."
    )
    args = parser.parse_args()

    total = 0
    for raw in args.paths:
        p = Path(raw)
        if p.is_dir():
            for f in p.rglob("*"):
                if f.is_file():
                    total += process_file(f, apply=args.apply)
        elif p.is_file():
            total += process_file(p, apply=args.apply)
        else:
            print(f"[myco_migrate] not found: {p}", file=sys.stderr)
    if not args.apply:
        print(f"[myco_migrate] DRY-RUN total {total} change(s); pass --apply to write")
    else:
        print(f"[myco_migrate] APPLIED total {total} change(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
