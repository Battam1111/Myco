"""Smolagents + Myco MCP demo (v0.6.0)."""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[smolagents-myco-demo] dry-run OK")
        return 0
    try:
        from smolagents import CodeAgent, MCPServerStdio  # type: ignore
    except ImportError:
        print("[smolagents-myco-demo] smolagents not installed; pip install smolagents")
        return 1
    print("[smolagents-myco-demo] smolagents CodeAgent with Myco MCPServerStdio")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
