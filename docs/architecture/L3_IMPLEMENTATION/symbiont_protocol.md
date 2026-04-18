# L3 — Symbiont Protocol

> **Status**: APPROVED (v0.5.5, 2026-04-17). Stub — no concrete
> symbionts shipped yet; this page defines what the slot IS so
> future releases can populate it without design backlog.
> **Layer**: L3. Subordinate to L0/L1/L2.
> **Mandate**: `src/myco/symbionts/` is the **per-host Agent-sugar
> seam**. Each module here is an adapter that wires Myco's manifest
> verbs into a specific Agent-host environment's native
> extension surface (skills, slash-commands, shortcuts, file-watch
> hooks, etc.) — without the downstream host having to know
> anything about Myco internals.

---

## Why this exists

v0.5.3 added `.myco/plugins/` as the **substrate-local** extension
seam — the place where one specific project's Agent registers a
project-specific lint rule, adapter, or verb. Substrate-local means
"this substrate only"; uninstall = delete the `.myco/plugins/`
folder.

But there is another extension axis orthogonal to that one:
**per-host** integration. Example axis:

- Claude Code has `.claude/skills/` and `.claude/hooks/` —
  Anthropic-specific surfaces the Agent can use to register custom
  slash-commands and file-watchers.
- Cursor has `~/.cursor/rules/` for custom rule files.
- VS Code has `tasks.json` and `launch.json`.
- Windsurf has `.windsurf/memories/`.
- OpenHands has its own microagent config.

A per-host integration does NOT want to live per-substrate (it
should work across every Myco substrate the user ever creates on
that host); it does NOT want to live in the Myco kernel (it's
host-specific — every host has a different file shape). It wants
to live in a shared host-adapter layer that Myco ships.

`src/myco/symbionts/` is that layer.

## The name

Symbiosis, in biology, is a persistent cooperative relationship
between two organisms of different species. Myco's relationship
with Claude Code / Cursor / Windsurf / Zed is exactly this:
two independently-maintained systems that cooperate at a shared
interface (MCP + filesystem hooks) to produce something neither
could alone. A symbiont module is the shape of that cooperation
for one specific host.

## What a symbiont does

A symbiont module exposes two things:

1. **A `discover()` function** — detects whether the host it targets
   is installed on this system (e.g. Claude Code's config dir
   exists; Cursor executable is on PATH). Returns a
   `SymbiontProbe` dataclass or None.
2. **An `install(host_probe, substrate)` function** — writes the
   per-host adapter files (skill definitions, hook configs,
   rule files, etc.) into the user's home or the substrate root,
   as appropriate for that host. Idempotent + preservation-
   friendly (don't clobber sibling entries).

Both are called by `myco-install host <client>` in a new execution
mode (`--with-symbionts`, to be added alongside the first concrete
symbiont). Until a symbiont exists the mode is inert — hence why
v0.5.5 ships the protocol stub but zero concrete symbionts.

## Reference shape (Python)

```python
# src/myco/symbionts/<host>.py

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from myco.core.substrate import Substrate


@dataclass(frozen=True)
class SymbiontProbe:
    host: str                       # "claude-code", "cursor", etc.
    detected: bool
    config_root: Optional[Path]     # e.g. ~/.claude/
    version: Optional[str]          # best-effort host version string


def discover() -> SymbiontProbe | None:
    """Return a probe if the target host is installed locally.

    Must never raise; returns None on absence. Cheap (filesystem
    existence check at most).
    """
    ...


def install(probe: SymbiontProbe, substrate: Substrate) -> dict:
    """Write this symbiont's host-side adapter files.

    Idempotent: re-running must be a no-op. Preserves sibling
    entries (host config files may contain user-authored content
    alongside ours). Returns a summary dict the caller surfaces to
    the human via ``myco-install`` output.
    """
    ...
```

## Boundary from `.myco/plugins/`

| Question | `.myco/plugins/` | `src/myco/symbionts/` |
|---|---|---|
| Scope | One substrate | All substrates on one host |
| Lives in | `<substrate_root>/.myco/plugins/` | Myco kernel source |
| Registers | Dimensions / adapters / overlay verbs | Host-side adapter files (skills, hooks, rules) |
| Installed by | `myco ramify --substrate-local` | `myco-install host <client> --with-symbionts` (future) |
| Uninstalled by | `rm -rf .myco/plugins/` | `myco-install host <client> --uninstall --with-symbionts` |
| Audited by | `myco graft --list`, MF2 dimension | (future) `myco graft --hosts` |

These two seams are orthogonal. A user can have both: `.myco/plugins/`
for their project's custom lint rules, plus the claude-code
symbiont sugar so every new substrate they germinate auto-registers
a `/myco:hunger` slash command in Claude Code.

## What v0.5.5 ships

This document (L3 protocol stub) + an updated
`src/myco/symbionts/__init__.py` that points at this doctrine +
a line in the L2 package_map noting the slot is defined-but-empty.
Zero concrete symbionts. Authoring the first concrete symbiont
(Claude Code: skill generation + hook registration) is a separate
release (v0.6+ or earlier if demand surfaces).

## What the first concrete symbiont will look like

`src/myco/symbionts/claude_code.py` — auto-registers per-substrate
Claude Code skills from the manifest:

1. `discover()` checks for `~/.claude/` OR `<project>/.claude/`
2. `install()` reads Myco's `manifest.yaml`, generates one
   `SKILL.md` per verb under `<config_root>/skills/myco-<verb>/SKILL.md`,
   generates a `hooks.json` entry that fires `myco hunger` on
   SessionStart + `myco senesce` on PreCompact
3. Idempotent: if `SKILL.md` already exists with our signature
   header, leave alone; if sibling SKILL.md for non-Myco skills
   exist, don't touch

When this ships, `myco-install host claude-code --with-symbionts`
does the above in one step. Until then, the manual plugin-install
path (already documented in `docs/INSTALL.md`) covers the same
ground.

## Governing craft

`docs/primordia/v0_5_5_close_audit_loose_threads_craft_2026-04-17.md`
§MAJOR-D.
