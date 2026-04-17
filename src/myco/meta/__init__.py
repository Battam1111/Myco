"""Cross-cutting meta-verbs that compose multiple subsystems.

v0.5 (MAJOR 9/10): what was a single-file ``meta.py`` in v0.4 is now
a package. The five meta-verbs — ``session-end``, ``craft``,
``bump``, ``evolve``, ``scaffold`` — each live in their own
submodule, mirroring the one-verb-per-file discipline that the
subsystem packages already follow.

The ``session_end_run`` re-export below preserves backward compatibility
for any out-of-tree caller that imported it from the old
``myco.meta`` module. The manifest (v0.5+) points directly at
``myco.meta.session_end:run``; the alias here is purely defensive.

Kept outside ``surface/`` so that package stays pure adaptation
per L3 package_map invariant 4. The ``meta`` package is *not* a
subsystem (it does not appear in ``canon.subsystems``); it is a
cross-cutting verb composer — see ``L3_IMPLEMENTATION/package_map.md``.
"""

from __future__ import annotations

from .session_end import run as session_end_run

__all__ = ["session_end_run"]
