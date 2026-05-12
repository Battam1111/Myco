"""``surface.mcp_resources`` — MCP resources/list + resources/read (v0.6.0).

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R6
+ craft v0.6.0 §A.1. Exposes substrate content as MCP resources so
host UIs (Claude Desktop resource panel, Cursor 2.0, Continue
context provider) can read substrate-stable content directly,
zero-tool-call.

URI scheme (stable across versions):

- ``myco://canon`` — redacted canon (per ``system.resource_redaction``).
  Default protected scope hides ``identity.federation_peers``,
  ``identity.tags``, ``system.governance``.
- ``myco://canon/raw`` — full canon (requires OAuth scope ``canon:full``).
- ``myco://contract`` — ``docs/architecture/L1_CONTRACT/protocol.md`` (R1-R7).
- ``myco://notes/integrated`` — list of integrated notes (metadata only).
- ``myco://notes/integrated/{note_id}`` — single integrated note.
- ``myco://notes/distilled/{slug}`` — single distilled note.
- ``myco://docs/primordia/{slug}`` — single craft document.
- ``myco://docs/architecture/L{0..3}/{name}`` — doctrine file.

Per craft v0.6.0 §F8 / R8: resources/read injects an R3-discipline
ledger entry into the session log so agents see "you read X via
resource; downstream assertions about X should re-sense() if state
may have changed." This preserves R3 spirit while enabling host UI
direct-read.

This module ships at v0.6.0 as a stub — the FastMCP integration
calls ``register_resources(server, context)`` after server build. The
actual register_resources implementation is wired in
``surface.mcp.build_server`` once the FastMCP API + watchfiles dep
combination is stabilized in v0.6.x.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import yaml

from myco.core.context import MycoContext

# v0.8.4 root-cleanup (2026-05-12): canon may live at .myco/canon.yaml
# (new layout) or _canon.yaml (legacy) — resolve via the central helper.
from myco.core.paths import find_substrate_canon

__all__ = [
    "URI_SCHEMES",
    "list_resources",
    "read_resource",
]

#: Stable URI scheme list. Used by ``resources/list`` to enumerate
#: top-level URI families and by host UIs to decide which resources
#: to subscribe to.
URI_SCHEMES: tuple[str, ...] = (
    "myco://canon",
    "myco://contract",
    "myco://notes/integrated",
    "myco://notes/distilled",
    "myco://docs/primordia",
    "myco://docs/architecture",
    "myco://reflex/queue",
)


def _redact(canon_data: Mapping[str, Any], protected: list[str]) -> dict[str, Any]:
    """Apply path-based redaction to a canon dict. Each path is dotted."""
    out: dict[str, Any] = json.loads(json.dumps(dict(canon_data)))
    for path in protected:
        parts = path.split(".")
        node: Any = out
        for part in parts[:-1]:
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                node = None
                break
        if isinstance(node, dict) and parts[-1] in node:
            node[parts[-1]] = "[REDACTED]"
    return out


def list_resources(
    ctx: MycoContext, *, scope: str = "protected"
) -> list[dict[str, Any]]:
    """Enumerate resources visible at the requested scope.

    Returns a list of ``{uri, title, mimeType, size, mtime, scope}``
    metadata entries. Per craft §F8: this is metadata-only; content
    is fetched via ``read_resource``.
    """
    root = ctx.substrate.root
    out: list[dict[str, Any]] = []
    # v0.8.4 root-cleanup (2026-05-12): canon may live at
    # .myco/canon.yaml (new) or _canon.yaml (legacy); module-top import
    # of find_substrate_canon resolves both.
    canon_path = find_substrate_canon(root)
    if canon_path.is_file():
        out.append(
            {
                "uri": "myco://canon",
                "title": "Canon (redacted)",
                "mimeType": "application/yaml",
                "size": canon_path.stat().st_size,
                "mtime": canon_path.stat().st_mtime,
                "scope": "protected",
            }
        )
        out.append(
            {
                "uri": "myco://canon/raw",
                "title": "Canon (raw — requires canon:full scope)",
                "mimeType": "application/yaml",
                "size": canon_path.stat().st_size,
                "mtime": canon_path.stat().st_mtime,
                "scope": "private",
            }
        )
    contract_path = root / "docs" / "architecture" / "L1_CONTRACT" / "protocol.md"
    if contract_path.is_file():
        out.append(
            {
                "uri": "myco://contract",
                "title": "Hard Contract (R1-R7)",
                "mimeType": "text/markdown",
                "size": contract_path.stat().st_size,
                "mtime": contract_path.stat().st_mtime,
                "scope": "public",
            }
        )
    # v0.8.4 root-cleanup (2026-05-12): notes/ may live at root (legacy)
    # or .myco/notes/ (Myco-self / v0.8.4+); resolve via paths.notes.
    # The MCP URI scheme keeps "notes" as a stable namespace regardless.
    integrated_root = ctx.substrate.paths.notes / "integrated"
    if integrated_root.is_dir():
        for path in sorted(integrated_root.glob("n_*.md")):
            stem = path.stem.removeprefix("n_")
            out.append(
                {
                    "uri": f"myco://notes/integrated/{stem}",
                    "title": stem,
                    "mimeType": "text/markdown",
                    "size": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                    "scope": "protected",
                }
            )
    primordia_root = root / "docs" / "primordia"
    if primordia_root.is_dir():
        for path in sorted(primordia_root.glob("*_craft_*.md")):
            if "_excreted" in path.parts:
                continue
            slug = path.stem
            out.append(
                {
                    "uri": f"myco://docs/primordia/{slug}",
                    "title": slug,
                    "mimeType": "text/markdown",
                    "size": path.stat().st_size,
                    "mtime": path.stat().st_mtime,
                    "scope": "public",
                }
            )
    return out


def read_resource(
    ctx: MycoContext, uri: str, *, scope: str = "protected"
) -> dict[str, Any]:
    """Read a single resource by URI. Honors redaction.

    Returns ``{uri, content, mimeType, scope}``.
    """
    root = ctx.substrate.root
    if uri == "myco://canon":
        canon_path = find_substrate_canon(root)
        try:
            data = yaml.safe_load(canon_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return {
                "uri": uri,
                "content": "",
                "mimeType": "application/yaml",
                "scope": scope,
            }
        redaction = (data.get("system") or {}).get("resource_redaction") or {}
        protected = (redaction.get("paths") or {}).get("protected") or []
        if scope != "private":
            data = _redact(data, protected)
        return {
            "uri": uri,
            "content": yaml.safe_dump(data, sort_keys=False),
            "mimeType": "application/yaml",
            "scope": scope,
        }
    if uri == "myco://canon/raw":
        if scope != "private":
            return {
                "uri": uri,
                "content": "[ACCESS DENIED — requires canon:full scope]",
                "mimeType": "text/plain",
                "scope": scope,
            }
        canon_path = find_substrate_canon(root)
        return {
            "uri": uri,
            "content": canon_path.read_text(encoding="utf-8")
            if canon_path.is_file()
            else "",
            "mimeType": "application/yaml",
            "scope": scope,
        }
    if uri == "myco://contract":
        contract_path = root / "docs" / "architecture" / "L1_CONTRACT" / "protocol.md"
        return {
            "uri": uri,
            "content": contract_path.read_text(encoding="utf-8")
            if contract_path.is_file()
            else "",
            "mimeType": "text/markdown",
            "scope": "public",
        }
    if uri.startswith("myco://notes/integrated/"):
        stem = uri.removeprefix("myco://notes/integrated/")
        # v0.8.4 root-cleanup (2026-05-12): use paths.notes for the
        # filesystem lookup; URI namespace "notes" stays stable.
        path = ctx.substrate.paths.notes / "integrated" / f"n_{stem}.md"
        return {
            "uri": uri,
            "content": path.read_text(encoding="utf-8") if path.is_file() else "",
            "mimeType": "text/markdown",
            "scope": scope,
        }
    if uri.startswith("myco://docs/primordia/"):
        slug = uri.removeprefix("myco://docs/primordia/")
        path = root / "docs" / "primordia" / f"{slug}.md"
        return {
            "uri": uri,
            "content": path.read_text(encoding="utf-8") if path.is_file() else "",
            "mimeType": "text/markdown",
            "scope": "public",
        }
    return {"uri": uri, "content": "", "mimeType": "text/plain", "scope": scope}
