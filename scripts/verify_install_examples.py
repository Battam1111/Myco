#!/usr/bin/env python3
"""verify_install_examples.py — 8 framework demo dry-run smoke (v0.6.0).

For each ``examples/<framework>-myco-demo/`` subdirectory, runs
``python main.py --dry`` and asserts exit code 0. Validates that
each framework demo at least imports cleanly.

CI uses an isolated ``uv venv`` per demo (per craft §F14) to avoid
the framework dependency conflicts (CrewAI ↔ LangChain ↔ DSPy
litellm/pydantic version dance). This local smoke runs in the
current env so missing optional deps are reported as warnings, not
failures (each demo's main.py exits 1 with a "<pkg> not installed"
message).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples"

EXPECTED_DEMOS = (
    "claude-sdk-myco-demo",
    "langgraph-myco-demo",
    "crewai-myco-demo",
    "dspy-myco-demo",
    "smolagents-myco-demo",
    "agno-myco-demo",
    "praisonai-myco-demo",
    "microsoft-agent-framework-myco-demo",
)


def main() -> int:
    if not EXAMPLES_DIR.is_dir():
        print(
            f"[verify_install_examples] examples/ not found at {EXAMPLES_DIR}",
            file=sys.stderr,
        )
        return 1
    failures = 0
    for demo in EXPECTED_DEMOS:
        demo_dir = EXAMPLES_DIR / demo
        main_py = demo_dir / "main.py"
        if not main_py.is_file():
            print(f"[verify_install_examples] MISSING demo: {demo}", file=sys.stderr)
            failures += 1
            continue
        result = subprocess.run(
            [sys.executable, str(main_py), "--dry"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            print(
                f"[verify_install_examples] {demo} --dry exit {result.returncode}: "
                f"{result.stdout.strip()} | {result.stderr.strip()}",
                file=sys.stderr,
            )
            failures += 1
        else:
            print(f"[verify_install_examples] OK: {demo}")
    if failures:
        print(
            f"[verify_install_examples] FAIL: {failures}/{len(EXPECTED_DEMOS)}",
            file=sys.stderr,
        )
        return 2
    print(f"[verify_install_examples] OK: all {len(EXPECTED_DEMOS)} demos --dry exit 0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
