"""Myco boundary subsystem (v0.6.0 — 7th canonical subsystem, FULL physical layout).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/boundary.md``.
Governing craft: ``docs/primordia/v0_6_0_unified_evolution_and_thorough_refactor_craft_2026-04-28.md``
§A1 + §A3 + Round 5 owner directive ("不许有任何一丝一毫偷懒").

Boundary unifies the substrate's outward interface layer. v0.6.0 ships
the **full physical merger**:

- ``boundary.surface``           — CLI + MCP server + manifest dispatcher
  (physical: ``src/myco/boundary/surface/``).
- ``boundary.install``           — myco-install host writers
  (physical: ``src/myco/boundary/install/``).
- ``boundary.mcp``               — MCP entry-point launcher
  (physical: ``src/myco/boundary/mcp/``).
- ``boundary.host_integration``  — per-host adapters
  (physical: ``src/myco/boundary/host_integration/``).

Top-level legacy packages ``myco.surface`` / ``myco.install`` /
``myco.mcp`` / ``myco.symbionts`` are **REMOVED at v0.6.0**. All
80+ project-internal imports were rewritten to the canonical
``myco.boundary.<sub>`` form. User scripts that imported the legacy
top-level paths must run ``scripts/myco_migrate.py`` to update.

The 6 fungal-bionic subsystems
(germination/ingestion/digestion/circulation/homeostasis/cycle) drive
the substrate's internal metabolism. The 7th subsystem ``boundary``
captures the substrate's externalization — the surface where the
agent invokes verbs, where MCP hosts connect, where install writers
seed config, and where host-specific adapters publish R1-R7 priming.

Per L0 amendment (Round 4 owner approval):
``L0_VISION.md:185-186`` "No alternate vocabulary" mandate is
narrowly extended to admit ``boundary`` as a doctrine-level term —
the L0 fungal taxonomy has no native word for "outward-interface
layer", and no biological metaphor maps cleanly. The other 6
subsystems' naming remains strictly fungal-bionic.
"""

from __future__ import annotations

# Boundary's four subpackages all live physically under boundary/ at
# v0.6.0. No re-export from a non-existent top-level path.
from . import host_integration, install, mcp, surface

__all__ = ["surface", "install", "mcp", "host_integration"]
