"""Agno + Myco MCP demo (v0.6.0)."""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[agno-myco-demo] dry-run OK")
        return 0
    try:
        from agno.agent import Agent
        from agno.tools.mcp import MCPTools
    except ImportError:
        print("[agno-myco-demo] agno not installed; pip install agno")
        return 1
    print("[agno-myco-demo] Agno Agent with Myco MCPTools")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
