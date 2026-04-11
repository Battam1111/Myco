#!/usr/bin/env python3
"""
Myco Knowledge System — Automated Lint (SHIM)
==============================================
Thin entry-point shim that delegates to myco.lint.main.

**This file is a shim as of contract v1.6.0 (re-baselined to v0.6.0 in
Wave 8).** Prior to Wave 6 this file and src/myco/lint.py were
dual-maintained physical copies of the same 14-dimensional lint
implementation. The dual-write was Myco's largest
structural debt — every new lint dimension required synchronous edits at
two sites, and drift was caught only by L8 (.original sync) which does
not actually check the two files against each other.

Wave 6 collapses both sites to a single source of truth in
``src/myco/lint.py``. This script exists purely to preserve the
CLI invocation path that has been documented since v0.8 —
``python scripts/lint_knowledge.py [--project-dir PATH] [--quick] [--fix-report]``.

Why keep the script file at all?
--------------------------------
Three reasons:

1. **CLI discoverability**: ``python scripts/...`` is the idiom a new
   reader naturally discovers when exploring the repo; requiring them to
   know the Python import path would raise the onboarding floor.
2. **Canon reference preservation**: ``_canon.yaml::upstream_channels.class_z``
   lists this path as a review-required contract file. Removing the file
   would churn the canon reference.
3. **Stable invocation**: log.md, MYCO.md, and docs/WORKFLOW.md all
   reference ``python scripts/lint_knowledge.py`` — a shim preserves
   backward compatibility with zero migration cost.

What changed
------------
Before Wave 6: 940 lines of duplicated logic.
After Wave 6:  ~50 lines of thin argument-parsing + delegation.

Craft record: docs/primordia/lint_ssot_craft_2026-04-11.md (Wave 6)
"""

import sys
from pathlib import Path

# Ensure src/ is on sys.path so ``from myco.lint import main`` works when
# this script is invoked directly from the repo root. The canonical
# install path is ``pip install -e .`` which puts myco on sys.path via
# entry_points, but many users / CI systems run the script without an
# editable install.
REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = REPO_ROOT / "src"
if SRC_DIR.exists() and str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from myco.lint import main as _lint_main  # noqa: E402


def _parse_args(argv):
    """Minimal argparse-free parser — keeps the shim dependency-light."""
    project_dir = REPO_ROOT
    quick = False
    fix_report = False
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--project-dir":
            i += 1
            if i >= len(argv):
                print("ERROR: --project-dir requires a PATH argument", file=sys.stderr)
                sys.exit(2)
            project_dir = Path(argv[i]).resolve()
        elif arg.startswith("--project-dir="):
            project_dir = Path(arg.split("=", 1)[1]).resolve()
        elif arg == "--quick":
            quick = True
        elif arg == "--fix-report":
            fix_report = True
        elif arg in ("-h", "--help"):
            print(__doc__)
            sys.exit(0)
        else:
            print(f"ERROR: unknown argument {arg!r}", file=sys.stderr)
            sys.exit(2)
        i += 1
    return project_dir, quick, fix_report


def main():
    project_dir, quick, fix_report = _parse_args(sys.argv[1:])
    return _lint_main(root=project_dir, quick=quick, fix_report=fix_report)


if __name__ == "__main__":
    sys.exit(main())
