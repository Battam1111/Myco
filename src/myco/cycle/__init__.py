"""Life-cycle verbs — the Agent's composer of substrate transitions.

v0.5.3 renamed ``myco.meta`` → ``myco.cycle`` because every verb in
this package is a life-cycle event of the fungal substrate:

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

The shim at :mod:`myco.meta` re-exports ``session_end_run`` for
every pre-v0.5.3 caller. Both import paths work across the 0.x line.

Kept outside ``surface/`` so that package stays pure adaptation per
L3 package_map invariant 4. The ``cycle`` package is *not* a
subsystem (it does not appear in ``canon.subsystems``); it is a
cross-cutting verb composer.
"""

from __future__ import annotations

from .senesce import run as session_end_run

__all__ = ["session_end_run"]
