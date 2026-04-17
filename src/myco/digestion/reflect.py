"""Deprecation shim for ``myco.digestion.reflect`` → ``myco.digestion.assimilate``.

v0.5.3 renamed the reflection verb ``reflect`` → ``assimilate``. The
fungal-biology metaphor: an integrator thread *assimilates* raw notes
into the mycelium, it doesn't "reflect" on them. This shim re-exports
the v0.5.2 public symbols.

Scheduled for removal at v1.0.0.
"""
from __future__ import annotations

import warnings as _w

from .assimilate import reflect, assimilate, run

__all__ = ["reflect", "assimilate", "run"]


_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    _w.warn(
        "myco.digestion.reflect is a deprecated shim for "
        "myco.digestion.assimilate (renamed at v0.5.3). Both import "
        "paths work through the 0.x line.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_once()
