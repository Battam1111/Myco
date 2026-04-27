"""``surface.mcp_prompts`` — MCP prompts/list + prompts/get (v0.6.0).

Governing doctrine: craft v0.6.0 §A.2. Exposes the 20 manifest verb
descriptions as MCP prompts under name ``verb-guide:<name>``, plus
2 workflow prompts:

- ``myco-bootstrap`` — 5-step substrate-bootstrap walkthrough.
- ``myco-contract-r1-r7`` — full R1-R7 contract text.

Prompts are zero-cost: descriptions are already in
``surface/manifest.yaml``. This module adapts them to MCP prompt
shape so host slash commands and quick-action menus surface them
natively.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

__all__ = ["list_prompts", "get_prompt"]

_BOOTSTRAP_BODY = """# Myco substrate bootstrap (5 steps)

1. **R1**: Call `mcp__myco__myco_hunger` to see what the substrate
   currently needs (raw backlog, contract drift, reflex signals).
2. **Survey**: Call `mcp__myco__myco_brief` for a human-readable
   rollup of substrate state.
3. **Read context**: For any factual claim about the substrate, call
   `mcp__myco__myco_sense` first (R3). Memory is not a source; the
   substrate is.
4. **Capture**: When a decision or insight occurs, call
   `mcp__myco__myco_eat` immediately (R4). Defer-and-batch loses
   material.
5. **Senesce**: Before /compact, call `mcp__myco__myco_senesce` (R2)
   to assimilate raw notes and apply immune fixes. The PreCompact
   hook in Claude Code automates this.
"""

_CONTRACT_BODY = """# Myco Hard Contract — R1 to R7

- R1 — Session boot is ritualized: every session starts with
  `myco_hunger`.
- R2 — Session end is ritualized: every session ends with
  `myco_senesce`.
- R3 — Sense before asserting: call `myco_sense` before factual
  claims about the substrate. Memory is not a source.
- R4 — Eat insights the moment they occur: call `myco_eat` on
  every decision, friction, or feedback.
- R5 — Cross-reference on creation: orphaned files are dead
  knowledge.
- R6 — Write only to paths in `_canon.yaml::system.write_surface.allowed`.
- R7 — Top-down subordination is non-negotiable: L0 > L1 > L2 > L3 > L4.

Full contract: `docs/architecture/L1_CONTRACT/protocol.md`.
"""


def list_prompts(manifest_commands: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Enumerate prompts: 20 verb-guides + 2 workflows."""
    out: list[dict[str, Any]] = []
    for cmd in manifest_commands:
        name = cmd.get("name") if isinstance(cmd, Mapping) else None
        if not name:
            continue
        out.append(
            {
                "name": f"verb-guide:{name}",
                "description": cmd.get("summary") or f"Guide for myco_{name}",
                "arguments": [
                    {
                        "name": str(arg.get("name", "")),
                        "description": str(arg.get("help", "")),
                        "required": bool(arg.get("required", False)),
                    }
                    for arg in (cmd.get("args") or [])
                    if isinstance(arg, Mapping)
                ],
            }
        )
    out.append(
        {
            "name": "myco-bootstrap",
            "description": "5-step Myco substrate bootstrap walkthrough.",
            "arguments": [],
        }
    )
    out.append(
        {
            "name": "myco-contract-r1-r7",
            "description": "Full text of the R1-R7 hard contract.",
            "arguments": [],
        }
    )
    return out


def get_prompt(name: str, manifest_commands: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Return the messages payload for a single prompt by name."""
    if name == "myco-bootstrap":
        return {
            "description": "Myco substrate bootstrap walkthrough",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": "Walk me through bootstrapping a Myco substrate session.",
                    },
                },
                {
                    "role": "assistant",
                    "content": {"type": "text", "text": _BOOTSTRAP_BODY},
                },
            ],
        }
    if name == "myco-contract-r1-r7":
        return {
            "description": "Myco Hard Contract R1-R7",
            "messages": [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": "Show me the Myco Hard Contract.",
                    },
                },
                {
                    "role": "assistant",
                    "content": {"type": "text", "text": _CONTRACT_BODY},
                },
            ],
        }
    if name.startswith("verb-guide:"):
        verb = name.removeprefix("verb-guide:")
        for cmd in manifest_commands:
            if isinstance(cmd, Mapping) and cmd.get("name") == verb:
                return {
                    "description": f"Guide for myco_{verb}",
                    "messages": [
                        {
                            "role": "user",
                            "content": {
                                "type": "text",
                                "text": f"How do I use myco_{verb}?",
                            },
                        },
                        {
                            "role": "assistant",
                            "content": {
                                "type": "text",
                                "text": str(
                                    cmd.get("description") or cmd.get("summary") or ""
                                ),
                            },
                        },
                    ],
                }
    return {
        "description": f"Unknown prompt: {name}",
        "messages": [],
    }
