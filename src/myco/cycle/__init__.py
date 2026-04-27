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

The shim at :mod:`myco.meta` re-exports ``session_end_run`` for
every pre-v0.5.3 caller. Both import paths work across the 0.x line.
v1.0.0 will remove the shim per ``digestion.md:120-122`` alias-removal
schedule (the same schedule applies to all v0.5.2 aliases).

Kept outside ``surface/`` so that package stays pure adaptation per
L3 package_map invariant 4.
"""

from __future__ import annotations

from .senesce import run as session_end_run

__all__ = ["session_end_run"]
