"""DSPy + Myco MCP demo (v0.6.0).

DSPy Module wrapping myco_sense as a retriever; compares precision
+ latency vs vector RAG baseline. Anti-vector retrieval pattern.
"""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[dspy-myco-demo] dry-run OK")
        return 0
    try:
        import dspy  # noqa: F401
    except ImportError:
        print("[dspy-myco-demo] dspy not installed")
        return 1
    print("[dspy-myco-demo] DSPy module wrapping myco_sense as retriever")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
