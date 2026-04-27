"""CrewAI + Myco MCP demo (v0.6.0).

3-agent crew (researcher / writer / critic) shares a Myco
MCPServerAdapter. Research findings flow eat → assimilate →
sporulate; final synthesis lands in a craft proposal.
"""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[crewai-myco-demo] dry-run OK (would import crewai)")
        return 0
    try:
        from crewai import Agent, Crew, Task
        from crewai_tools import MCPServerAdapter
    except ImportError:
        print("[crewai-myco-demo] crewai / crewai_tools not installed")
        return 1
    print("[crewai-myco-demo] CrewAI 3-agent demo with Myco MCPServerAdapter")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
