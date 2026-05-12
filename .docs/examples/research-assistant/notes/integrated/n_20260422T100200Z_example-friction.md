---
captured_at: "2026-04-22T10:02:00Z"
integrated_at: "2026-04-22T10:05:00Z"
tags: ["friction", "example", "research"]
source: "example (synthetic)"
stage: "integrated"
references:
  - "notes/integrated/n_20260422T100100Z_example-decision.md"
---

# Friction: vendor-specific MCP config paths

**What snagged**: onboarding Myco across three different MCP
hosts (Claude Desktop, Cursor, Goose) each wanted config in a
different file shape — `mcpServers` JSON block vs
`context_servers` JSON block vs `extensions` YAML table. The
`myco-install` command handles it, but understanding which
host wanted which shape took 20 minutes.

**Why I'm noting this**: friction notes are valuable raw
material. If three people surface the same friction, the
substrate has gathered enough signal to justify a doctrine
revision (e.g. a canonical shape comparison table, or a
clearer "which host?" heuristic in `myco-install`).

This is pre-seeded as an example. Frictions in your own
research substrate accumulate at real session speed.
