"""Deprecation shim for ``myco.digestion.distill`` → ``myco.digestion.sporulate``.

v0.5.3 renamed the distillation verb ``distill`` → ``sporulate`` (a
fungus sporulates to propagate; "distill" was the generic programming
name). This shim re-exports every v0.5.2 public symbol under the old
module path so existing imports keep working.

Scheduled for removal at v1.0.0.
"""
from __future__ import annotations

import warnings as _w

from .sporulate import distill_proposal, run

__all__ = ["distill_proposal", "run"]


_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    _w.warn(
        "myco.digestion.distill is a deprecated shim for "
        "myco.digestion.sporulate (renamed at v0.5.3). Both import "
        "paths work through the 0.x line.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_once()
