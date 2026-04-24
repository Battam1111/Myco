"""Verify the Myco MCP server boots cleanly and answers a full handshake.

This is the first-line diagnostic when a registry (Glama, MCP Registry,
Claude Desktop, …) reports that ``mcp-server-myco`` failed to start.
It simulates the exact wire-level handshake an MCP host performs:

1. Spawn ``python -m myco.mcp`` as a subprocess with stdio pipes.
2. Send ``initialize`` → expect a ``result`` with
   ``protocolVersion: "2024-11-05"``.
3. Send the ``notifications/initialized`` notification.
4. Send ``tools/list`` → expect exactly the canonical 19 verbs
   (no deprecated aliases; that's a v0.5.24 invariant).
5. For every tool, inspect ``inputSchema`` and assert that each
   parameter carries a non-empty ``description``; assert that
   high-value params (``note-id``, ``reason``, paths, slugs)
   carry ``examples: [...]``.
6. Call ``tools/call`` for ``myco_hunger`` against a throwaway
   substrate and verify the response payload decodes as JSON.

Fail-fast exit codes so CI / release pipelines can gate on this:

    0  all checks passed
    1  handshake failed (server didn't initialize)
    2  tools/list failed or wrong tool count
    3  inputSchema regression (missing descriptions or examples)
    4  tools/call failed

Run as: ``python scripts/verify_mcp_boot.py``. No args. Intentionally
kernel-self; doesn't reach out to network. Add to a Dockerfile
``RUN`` step or a release job to catch the class of regressions
that only manifest once the server actually spawns.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

_EXPECTED_TOOLS = {
    "myco_assimilate",
    "myco_brief",
    "myco_digest",
    "myco_eat",
    "myco_excrete",  # v0.5.24
    "myco_forage",
    "myco_fruit",
    "myco_germinate",
    "myco_graft",
    "myco_hunger",
    "myco_immune",
    "myco_molt",
    "myco_propagate",
    "myco_ramify",
    "myco_senesce",
    "myco_sense",
    "myco_sporulate",
    "myco_traverse",
    "myco_winnow",
}

# Params that MUST carry ``examples: [...]`` in the JSON schema.
# Regression lock for the v0.5.24 Field(examples=[…]) thread-through.
_PARAMS_REQUIRING_EXAMPLES = {
    ("myco_germinate", "project_dir"),
    ("myco_germinate", "substrate_id"),
    ("myco_eat", "content"),
    ("myco_sense", "query"),
    ("myco_excrete", "note_id"),
    ("myco_excrete", "reason"),
    ("myco_molt", "contract"),
}


class _Proc:
    """Thin line-oriented JSON-RPC client over an MCP stdio subprocess."""

    def __init__(self) -> None:
        self.p = subprocess.Popen(
            [sys.executable, "-m", "myco.mcp"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )

    def send(self, obj: dict[str, Any]) -> None:
        assert self.p.stdin is not None
        self.p.stdin.write((json.dumps(obj) + "\n").encode("utf-8"))
        self.p.stdin.flush()

    def recv(self) -> dict[str, Any] | None:
        assert self.p.stdout is not None
        line = self.p.stdout.readline()
        if not line:
            return None
        return json.loads(line.decode("utf-8"))

    def close(self) -> str:
        self.p.terminate()
        try:
            self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.p.kill()
        assert self.p.stderr is not None
        return self.p.stderr.read().decode("utf-8", errors="replace")


def _fail(code: int, msg: str, stderr: str | None = None) -> int:
    sys.stderr.write(f"verify_mcp_boot: FAIL ({code}) {msg}\n")
    if stderr:
        sys.stderr.write(f"  server stderr:\n{stderr[:2000]}\n")
    return code


def main() -> int:
    proc = _Proc()
    try:
        # 1. initialize
        proc.send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {"name": "verify_mcp_boot", "version": "1.0"},
                },
            }
        )
        r = proc.recv()
        if r is None or "result" not in r:
            return _fail(1, f"initialize returned: {r}", proc.close())

        # 2. initialized notification (no response expected)
        proc.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3. tools/list
        proc.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r = proc.recv()
        if r is None or "result" not in r:
            return _fail(2, f"tools/list returned: {r}", proc.close())
        tools = r["result"].get("tools", [])
        names = {t["name"] for t in tools}
        missing = _EXPECTED_TOOLS - names
        extra = names - _EXPECTED_TOOLS
        if missing or extra:
            return _fail(
                2,
                f"tool set mismatch: missing={sorted(missing)} extra={sorted(extra)}",
                proc.close(),
            )

        # 4. every param carries a description
        missing_desc: list[str] = []
        for t in tools:
            sch = t.get("inputSchema", {})
            for pname, pdef in sch.get("properties", {}).items():
                if not pdef.get("description"):
                    missing_desc.append(f"{t['name']}.{pname}")
        if missing_desc:
            return _fail(
                3,
                f"{len(missing_desc)} param(s) lack description: {missing_desc[:5]}...",
                proc.close(),
            )

        # 5. high-value params carry examples
        missing_ex: list[str] = []
        by_name = {t["name"]: t for t in tools}
        for tool_name, param in _PARAMS_REQUIRING_EXAMPLES:
            t = by_name.get(tool_name)
            if t is None:
                missing_ex.append(f"{tool_name} (tool missing)")
                continue
            pdef = t.get("inputSchema", {}).get("properties", {}).get(param, {})
            ex = pdef.get("examples")
            if not ex:
                missing_ex.append(f"{tool_name}.{param}")
        if missing_ex:
            return _fail(
                3,
                f"high-value params missing examples: {missing_ex}",
                proc.close(),
            )

        # 6. tools/call myco_hunger against a throwaway substrate
        with tempfile.TemporaryDirectory() as td:
            # Minimal but valid _canon.yaml for the hunger call.
            os.makedirs(os.path.join(td, "notes"))
            (Path(td) / "_canon.yaml").write_text(
                'schema_version: "1"\n'
                'contract_version: "v0.5.24"\n'
                "identity:\n"
                '  substrate_id: "verify-mcp-boot"\n'
                "  tags: []\n"
                '  entry_point: "MYCO.md"\n'
                "system:\n"
                "  write_surface:\n"
                "    allowed:\n"
                '      - "_canon.yaml"\n'
                '      - "notes/**"\n'
                "  hard_contract:\n"
                "    rule_count: 7\n"
                "subsystems:\n"
                "  ingestion: {}\n",
                encoding="utf-8",
            )
            (Path(td) / "MYCO.md").write_text("# verify\n", encoding="utf-8")

            proc.send(
                {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "myco_hunger",
                        "arguments": {"project_dir": td},
                    },
                }
            )
            r = proc.recv()
            if r is None or "result" not in r:
                return _fail(4, f"tools/call myco_hunger returned: {r}", proc.close())
            content = r["result"].get("content", [])
            if not content or content[0].get("type") != "text":
                return _fail(
                    4,
                    f"myco_hunger response has wrong shape: {r['result']}",
                    proc.close(),
                )

        stderr = proc.close()
        print(
            f"verify_mcp_boot: OK — {len(tools)} tools, all schemas valid, "
            f"handshake + tools/call succeeded"
        )
        # Print server stderr if it has anything non-trivial (warnings,
        # deprecation notices) so a CI reader can grep for regressions.
        meaningful = [
            ln
            for ln in stderr.splitlines()
            if ln.strip() and "Processing request" not in ln and "INFO" not in ln
        ]
        if meaningful:
            print("server stderr (non-INFO lines):")
            for ln in meaningful[:20]:
                print(f"  {ln}")
        return 0
    except Exception as exc:
        stderr = proc.close()
        return _fail(1, f"unexpected exception: {exc!r}", stderr)


if __name__ == "__main__":
    sys.exit(main())
