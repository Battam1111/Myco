"""Cycle subsystem — life-cycle verbs composing substrate transitions.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/cycle.md``
(landed at v0.6.0). Cycle was named by L0 as the 6th subsystem
since v0.5.3 (``L0_VISION.md:183``); v0.6.0 finally projects that
into ``canon.subsystems`` and authors the L2 doctrine page.

Verbs housed here:

- ``germinate`` (in :mod:`myco.germination`) starts the cycle.
- ``fruit`` authors a dated primordia doc (produces the visible
  reproductive structure).
- ``molt`` advances the contract version (sheds old form).
- ``winnow`` validates a proposal's shape (selection).
- ``ramify`` scaffolds new code (hyphal branching: verbs,
  dimensions, adapters).
- ``senesce`` closes the session (prep for sleep: reflect + immune
  --fix).
- ``graft`` (introspection) enumerates what local code has grafted
  onto this substrate.
- ``brief`` (the lone human-facing exception per L0 P1) renders a
  human-readable rollup of substrate state.

Kept outside ``boundary.surface/`` so that package stays pure
adaptation per L3 package_map invariant 4.

Historical note: a ``myco.meta`` shim package re-exporting
``session_end_run`` was scheduled for v1.0.0 removal in the v0.5.x
doctrine. That shim never shipped to disk — the planned package
was excreted at v0.6.0 along with the other pre-rename top-level
aliases (``myco.surface`` / ``myco.install`` / ``myco.mcp`` /
``myco.symbionts``), and the v0.8.5 audit confirmed no in-tree
caller imports ``session_end_run`` from anywhere outside this
file. The re-export below is therefore a no-op import-target the
Cycle package maintains for the L0 P3 "永恒进化" preservation
clause; future deletion can land via a v0.9+ craft once the
v0.6.0 rename horizon is doctrinally past.
"""

from __future__ import annotations

from .senesce import run as session_end_run

__all__ = ["session_end_run"]
