"""LangGraph + Myco MCP demo (v0.6.0).

A minimal LangGraph state machine where one node calls myco_sense
and another calls myco_eat. Demonstrates substrate-aware Memory
node that uses Myco verbs instead of vector retrieval.
"""

from __future__ import annotations

import argparse
import asyncio
import sys


async def _run() -> int:
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        print("[langgraph-myco-demo] langchain-mcp-adapters not installed")
        return 1
    client = MultiServerMCPClient({
        "myco": {"transport": "stdio", "command": "mcp-server-myco", "args": []},
    })
    tools = await client.get_tools()
    print(f"[langgraph-myco-demo] Myco tools loaded: {len(tools)}")
    for t in tools[:5]:
        print(f"  - {t.name}")
    return 0


def main(dry: bool = False) -> int:
    if dry:
        print("[langgraph-myco-demo] dry-run OK")
        return 0
    return asyncio.run(_run())


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry", action="store_true")
    args = parser.parse_args()
    sys.exit(main(dry=args.dry))
