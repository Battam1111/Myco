"""PraisonAI + Myco MCP demo (v0.6.0)."""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[praisonai-myco-demo] dry-run OK")
        return 0
    try:
        import praisonaiagents  # noqa: F401
    except ImportError:
        print("[praisonai-myco-demo] praisonaiagents not installed")
        return 1
    print("[praisonai-myco-demo] PraisonAI agent with Myco MCP server")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
