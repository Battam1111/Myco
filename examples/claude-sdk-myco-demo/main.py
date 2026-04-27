"""Claude Agent SDK + Myco MCP server (v0.6.0 demo).

The simplest path: pass ``setting_sources=["project"]`` so the SDK
auto-loads ``.mcp.json`` from the project root. Myco's stdio MCP
server appears as a tool surface to the agent.
"""

from __future__ import annotations

import argparse
import sys


def main(dry: bool = False) -> int:
    if dry:
        print("[claude-sdk-myco-demo] dry-run OK (would import claude_agent_sdk)")
        return 0
    try:
        from claude_agent_sdk import ClaudeAgent, ClaudeAgentOptions
    except ImportError:
        print("[claude-sdk-myco-demo] claude_agent_sdk not installed; pip install claude-agent-sdk")
        return 1
    options = ClaudeAgentOptions(setting_sources=["project"])  # auto-loads .mcp.json
    agent = ClaudeAgent(options=options)
    print("[claude-sdk-myco-demo] agent ready; Myco MCP tools auto-discovered")
    print("[claude-sdk-myco-demo] sample query: 'call myco_hunger then myco_brief'")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
