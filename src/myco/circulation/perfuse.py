"""Deprecation shim for ``myco.circulation.perfuse`` → ``myco.circulation.traverse``.

v0.5.3 renamed the circulation-walk verb ``perfuse`` → ``traverse``
(every verb in circulation now names the action it performs on the
graph, not the vascular metaphor). Backward-compat re-exports the
v0.5.2 public symbols.

Scheduled for removal at v1.0.0.
"""
from __future__ import annotations

import warnings as _w

from .traverse import perfuse, run, Scope

__all__ = ["perfuse", "run", "Scope"]


_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    _w.warn(
        "myco.circulation.perfuse is a deprecated shim for "
        "myco.circulation.traverse (renamed at v0.5.3). Both import "
        "paths work through the 0.x line.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_once()
