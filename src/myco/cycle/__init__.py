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

v0.8.6 excretion: the dangling ``session_end_run`` re-export of
``senesce.run`` is removed. The shim was a leftover from the
v0.5.x → v0.6.0 rename horizon (when ``myco.meta`` was the pre-
rename home for the verb); the v0.6.0 audit confirmed no caller
imports ``session_end_run`` anywhere in-tree, and the v0.8.x
codebase calls ``cycle.senesce.run`` directly. The doctrine note
that scheduled the deletion via "a v0.9+ craft once the rename
horizon is doctrinally past" is now satisfied — we are five minor
versions past v0.6.0, well outside the rename window. Callers
import :func:`myco.cycle.senesce.run` directly.
"""

from __future__ import annotations

__all__: tuple[str, ...] = ()
