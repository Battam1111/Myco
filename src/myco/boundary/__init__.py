"""Myco boundary subsystem.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.

Boundary unifies the substrate's outward interface layer:

- ``boundary.surface``  — CLI + MCP server + manifest dispatcher
  (physical: ``src/myco/boundary/surface/``).
- ``boundary.install``  — myco-install host writers
  (physical: ``src/myco/boundary/install/``).
- ``boundary.mcp``      — MCP entry-point launcher
  (physical: ``src/myco/boundary/mcp/``).

The 6 fungal-bionic subsystems
(germination/ingestion/digestion/circulation/homeostasis/cycle) drive
the substrate's internal metabolism. The 7th subsystem ``boundary``
captures the substrate's externalization — the surface where the
agent invokes verbs, where MCP hosts connect, and where install
writers seed host config.

Per L0 amendment (Round 4 owner approval):
``L0_VISION.md:185-186`` "No alternate vocabulary" mandate is
narrowly extended to admit ``boundary`` as a doctrine-level term —
the L0 fungal taxonomy has no native word for "outward-interface
layer", and no biological metaphor maps cleanly. The other 6
subsystems' naming remains strictly fungal-bionic.

v0.8.5 — ``boundary.host_integration`` (14 per-host adapter modules
at v0.6.0) was excreted. The 8 pure-stub adapters (claude_code,
claude_desktop, codex_cli, cowork, gemini_cli, jetbrains, openclaw,
windsurf) returned empty ``InstallReport``\\s. The 6 functional
adapters (cursor, cline, continue_dev, goose, vscode, zed) wrote
rule-templates to per-host directories but were never invoked by
the production ``myco-install host <client>`` path — that path
delegates to the data-driven ``boundary.install.clients.JsonClientSpec``
table. Re-introducing "deep install" rule writers, if ever wanted,
should land as a new ``RuleClientSpec`` row inside ``clients.py``
rather than as a parallel registry.
"""

from __future__ import annotations

from . import install, mcp, surface

__all__ = ["surface", "install", "mcp"]
