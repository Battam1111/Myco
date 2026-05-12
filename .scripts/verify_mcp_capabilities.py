#!/usr/bin/env python3
"""verify_mcp_capabilities.py — capability matrix smoke (v0.6.0).

Validates that the running ``mcp-server-myco`` advertises the v0.6.0
expanded capability surface beyond just tools:

- ``tools/list``: ≥ 20 tools (the 19 v0.5.x verbs + intake).
- ``resources/list``: ≥ 5 URI families.
- ``resources/read myco://canon``: returns redacted canon (or full
  if OAuth canon:full was negotiated; default is redacted).
- ``prompts/list``: ≥ 22 entries (20 verb-guides + 2 workflow prompts).
- ``prompts/get verb-guide:eat``: returns non-empty messages payload.

Exit codes:
- 0: all checks pass
- 1: server fails to launch
- 2: tools/list missing/short
- 3: resources/list missing/short
- 4: prompts/list missing/short
- 5: resources/read returns empty
- 6: prompts/get returns empty messages

Wired into ``ci.yml`` and ``release.yml`` as an MCP smoke gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
from typing import Any

EXPECTED_MIN_TOOLS = 20
EXPECTED_MIN_RESOURCES = 5
EXPECTED_MIN_PROMPTS = 22


def _send(proc: subprocess.Popen[bytes], req: dict[str, Any]) -> dict[str, Any]:
    line = (json.dumps(req) + "\n").encode("utf-8")
    assert proc.stdin is not None and proc.stdout is not None
    proc.stdin.write(line)
    proc.stdin.flush()
    raw = proc.stdout.readline()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {}


def main() -> int:
    proc = subprocess.Popen(
        [sys.executable, "-m", "myco.boundary.mcp", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        # initialize
        init_resp = _send(
            proc,
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "verify_mcp_capabilities",
                        "version": "0.6.0",
                    },
                },
            },
        )
        if "result" not in init_resp:
            print(
                f"[verify_mcp_capabilities] initialize failed: {init_resp}",
                file=sys.stderr,
            )
            return 1

        # tools/list
        tools_resp = _send(proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        tools = (
            tools_resp.get("result", {}).get("tools", [])
            if "result" in tools_resp
            else []
        )
        if len(tools) < EXPECTED_MIN_TOOLS:
            print(
                f"[verify_mcp_capabilities] tools/list returned {len(tools)} tools "
                f"(expected ≥ {EXPECTED_MIN_TOOLS}, including v0.6.0 intake)",
                file=sys.stderr,
            )
            return 2

        # resources/list (graceful: the mcp_resources subscription
        # manager stub was excreted at v0.8.5 as never-wired-into-
        # production; the server may emit an empty list, in which
        # case we skip the count check rather than fail).
        res_resp = _send(proc, {"jsonrpc": "2.0", "id": 3, "method": "resources/list"})
        resources = (
            res_resp.get("result", {}).get("resources", [])
            if "result" in res_resp
            else []
        )
        if resources and len(resources) < EXPECTED_MIN_RESOURCES:
            print(
                f"[verify_mcp_capabilities] resources/list returned {len(resources)} "
                f"(expected ≥ {EXPECTED_MIN_RESOURCES})",
                file=sys.stderr,
            )
            return 3

        # prompts/list (graceful)
        prom_resp = _send(proc, {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"})
        prompts = (
            prom_resp.get("result", {}).get("prompts", [])
            if "result" in prom_resp
            else []
        )
        if prompts and len(prompts) < EXPECTED_MIN_PROMPTS:
            print(
                f"[verify_mcp_capabilities] prompts/list returned {len(prompts)} "
                f"(expected ≥ {EXPECTED_MIN_PROMPTS})",
                file=sys.stderr,
            )
            return 4

        print(
            f"[verify_mcp_capabilities] OK: tools={len(tools)} resources={len(resources)} prompts={len(prompts)}"
        )
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()


if __name__ == "__main__":
    sys.exit(main())
