"""Microsoft Agent Framework + Myco MCP demo (v0.6.0).

The Microsoft Agent Framework (formerly AutoGen) supports MCP via
its standard transport.
"""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[microsoft-agent-framework-myco-demo] dry-run OK")
        return 0
    try:
        from agent_framework import AgentApp  # type: ignore
    except ImportError:
        print("[microsoft-agent-framework-myco-demo] agent-framework not installed")
        return 1
    print("[microsoft-agent-framework-myco-demo] MS Agent Framework with Myco MCP")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
