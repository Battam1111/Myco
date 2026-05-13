#!/usr/bin/env python3
"""Combined CI verification CLI (v0.8.8 merge of 4 verify_* scripts).

Dispatches to one of four pre-existing verify routines via a leading
subcommand argument. The original per-file scripts (``verify_mcp_boot``,
``verify_mcp_capabilities``, ``verify_install_examples``,
``verify_server_json``) were merged here to drop 3 .py files from the
``.scripts/`` surface while keeping the per-routine review boundary
intact via ``# === <subcommand> — ...`` section markers.

Usage:

    python .scripts/verify.py mcp-boot
    python .scripts/verify.py mcp-capabilities
    python .scripts/verify.py install-examples
    python .scripts/verify.py server-json

Each subcommand preserves the original script's exit code semantics
verbatim. ``ci.yml`` invokes each subcommand as its own step so the
per-routine gate granularity stays intact.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

# =========================================================================
# === mcp-boot — formerly verify_mcp_boot.py (264 LOC)
# =========================================================================

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
    "myco_intake",  # v0.6.0
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


class _BootProc:
    """Thin line-oriented JSON-RPC client over an MCP stdio subprocess."""

    def __init__(self) -> None:
        self.p = subprocess.Popen(
            [sys.executable, "-m", "myco.boundary.mcp"],
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


def _boot_fail(code: int, msg: str, stderr: str | None = None) -> int:
    sys.stderr.write(f"verify_mcp_boot: FAIL ({code}) {msg}\n")
    if stderr:
        sys.stderr.write(f"  server stderr:\n{stderr[:2000]}\n")
    return code


def verify_mcp_boot() -> int:
    proc = _BootProc()
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
            return _boot_fail(1, f"initialize returned: {r}", proc.close())

        # 2. initialized notification (no response expected)
        proc.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

        # 3. tools/list
        proc.send({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        r = proc.recv()
        if r is None or "result" not in r:
            return _boot_fail(2, f"tools/list returned: {r}", proc.close())
        tools = r["result"].get("tools", [])
        names = {t["name"] for t in tools}
        missing = _EXPECTED_TOOLS - names
        extra = names - _EXPECTED_TOOLS
        if missing or extra:
            return _boot_fail(
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
            return _boot_fail(
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
            return _boot_fail(
                3,
                f"high-value params missing examples: {missing_ex}",
                proc.close(),
            )

        # 6. tools/call myco_hunger against a throwaway substrate
        with tempfile.TemporaryDirectory() as td:
            os.makedirs(os.path.join(td, "notes"))
            (Path(td) / "_canon.yaml").write_text(
                'schema_version: "2"\n'
                'contract_version: "v0.6.10"\n'
                "identity:\n"
                '  substrate_id: "verify-mcp-boot"\n'
                "  tags: []\n"
                '  entry_point: "MYCO.md"\n'
                "  federation_peers: []\n"
                "system:\n"
                "  llm_policy: forbidden\n"
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
                return _boot_fail(
                    4, f"tools/call myco_hunger returned: {r}", proc.close()
                )
            content = r["result"].get("content", [])
            if not content or content[0].get("type") != "text":
                return _boot_fail(
                    4,
                    f"myco_hunger response has wrong shape: {r['result']}",
                    proc.close(),
                )

        stderr = proc.close()
        print(
            f"verify_mcp_boot: OK — {len(tools)} tools, all schemas valid, "
            f"handshake + tools/call succeeded"
        )
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
        return _boot_fail(1, f"unexpected exception: {exc!r}", stderr)


# =========================================================================
# === mcp-capabilities — formerly verify_mcp_capabilities.py (145 LOC)
# =========================================================================

EXPECTED_MIN_TOOLS = 20
EXPECTED_MIN_RESOURCES = 5
EXPECTED_MIN_PROMPTS = 22


def _caps_send(proc: subprocess.Popen[bytes], req: dict[str, Any]) -> dict[str, Any]:
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


def verify_mcp_capabilities() -> int:
    proc = subprocess.Popen(
        [sys.executable, "-m", "myco.boundary.mcp", "--transport", "stdio"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        # initialize
        init_resp = _caps_send(
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
        tools_resp = _caps_send(
            proc, {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}
        )
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

        # resources/list (graceful)
        res_resp = _caps_send(
            proc, {"jsonrpc": "2.0", "id": 3, "method": "resources/list"}
        )
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
        prom_resp = _caps_send(
            proc, {"jsonrpc": "2.0", "id": 4, "method": "prompts/list"}
        )
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
            f"[verify_mcp_capabilities] OK: tools={len(tools)} "
            f"resources={len(resources)} prompts={len(prompts)}"
        )
        return 0
    finally:
        try:
            proc.terminate()
            proc.wait(timeout=2.0)
        except subprocess.TimeoutExpired:
            proc.kill()


# v0.8.8 max-aggressive: install-examples subcommand removed alongside
# the .docs/examples/ framework-demo subtree.

# =========================================================================
# === server-json — formerly verify_server_json.py (92 LOC)
# =========================================================================

REQUIRED_TOP_LEVEL = (
    "$schema",
    "name",
    "description",
    "repository",
    "version",
    "packages",
)

PUBLISHER_META_KEY = "io.modelcontextprotocol.registry/publisher-provided"
PUBLISHER_META_BUDGET_BYTES = 4096


def verify_server_json() -> int:
    server_json_path = Path(__file__).resolve().parent.parent / ".meta" / "server.json"
    if not server_json_path.is_file():
        print(
            f"[verify_server_json] server.json missing at {server_json_path}",
            file=sys.stderr,
        )
        return 1
    try:
        data = json.loads(server_json_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"[verify_server_json] invalid JSON: {exc}", file=sys.stderr)
        return 1
    for key in REQUIRED_TOP_LEVEL:
        if key not in data:
            print(f"[verify_server_json] missing required key: {key}", file=sys.stderr)
            return 2
    meta = data.get("_meta") or {}
    if isinstance(meta, dict):
        publisher_meta = meta.get(PUBLISHER_META_KEY)
        if publisher_meta is not None:
            payload = json.dumps(publisher_meta, ensure_ascii=False)
            payload_bytes = len(payload.encode("utf-8"))
            if payload_bytes > PUBLISHER_META_BUDGET_BYTES:
                print(
                    f"[verify_server_json] _meta.publisher-provided exceeds 4KB "
                    f"budget: {payload_bytes} > {PUBLISHER_META_BUDGET_BYTES}",
                    file=sys.stderr,
                )
                return 3
            print(
                f"[verify_server_json] _meta.publisher-provided OK: "
                f"{payload_bytes} bytes (of {PUBLISHER_META_BUDGET_BYTES} budget)"
            )
    packages = data.get("packages") or []
    for i, pkg in enumerate(packages):
        for pkg_key in ("registryType", "identifier", "version"):
            if pkg_key not in pkg:
                print(
                    f"[verify_server_json] packages[{i}] missing {pkg_key}",
                    file=sys.stderr,
                )
                return 4
    print(
        f"[verify_server_json] OK: {len(packages)} packages, "
        f"all required fields present"
    )
    return 0


# =========================================================================
# Subcommand dispatcher
# =========================================================================

_VERBS: dict[str, Callable[[], int]] = {
    "mcp-boot": verify_mcp_boot,
    "mcp-capabilities": verify_mcp_capabilities,
    "server-json": verify_server_json,
}


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if not args or args[0] in ("-h", "--help"):
        print(f"usage: {sys.argv[0]} <subcommand>", file=sys.stderr)
        print(f"  subcommands: {', '.join(_VERBS)}", file=sys.stderr)
        return 0 if args and args[0] in ("-h", "--help") else 2
    verb = args[0]
    if verb not in _VERBS:
        print(
            f"verify.py: unknown subcommand {verb!r}; "
            f"expected one of {', '.join(_VERBS)}",
            file=sys.stderr,
        )
        return 2
    return _VERBS[verb]()


if __name__ == "__main__":
    sys.exit(main())
