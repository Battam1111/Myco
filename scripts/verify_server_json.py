#!/usr/bin/env python3
"""verify_server_json.py — server.json JSON-Schema + 4KB _meta budget (v0.6.0).

Validates:

1. ``server.json`` parses as valid JSON.
2. Top-level required fields present per MCP Registry generic schema:
   $schema, name, description, repository, version, packages.
3. ``_meta.io.modelcontextprotocol.registry/publisher-provided``
   payload (if present) serializes to ≤ 4096 bytes.
4. ``packages[*].registryType``, ``identifier``, ``version`` present.

Exit codes:
- 0: all checks pass
- 1: missing or invalid JSON
- 2: required field missing
- 3: _meta payload exceeds 4KB
- 4: package entry incomplete
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

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


def main() -> int:
    # v0.8.4 root-cleanup (2026-05-12): server.json moved to .meta/ to
    # consolidate external registry metadata under a single hidden dir.
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
                    f"[verify_server_json] _meta.publisher-provided exceeds 4KB budget: "
                    f"{payload_bytes} > {PUBLISHER_META_BUDGET_BYTES}",
                    file=sys.stderr,
                )
                return 3
            print(
                f"[verify_server_json] _meta.publisher-provided OK: {payload_bytes} bytes "
                f"(of {PUBLISHER_META_BUDGET_BYTES} budget)"
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
        f"[verify_server_json] OK: {len(packages)} packages, all required fields present"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
