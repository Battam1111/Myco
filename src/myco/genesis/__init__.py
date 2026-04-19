"""Deprecation shim for ``myco.genesis`` → ``myco.germination``.

v0.5.3 renamed the subsystem ``genesis`` → ``germination`` to match
the fungal vocabulary project-wide (a spore ``germinates``; Greek-
theological ``genesis`` was a holdover from pre-Myco naming). This
module keeps every v0.4 / v0.5.x import path working with a one-
shot DeprecationWarning so any out-of-tree caller that pinned
``from myco.genesis import bootstrap`` keeps running unchanged
through the entire 0.x line.

Scheduled for removal at v1.0.0.
"""

from __future__ import annotations

import warnings as _w

from myco.germination import (
    DEFAULT_CONTRACT_VERSION,
    DEFAULT_ENTRY_POINT,
    bootstrap,
    run_cli,
)

_WARNED = False


def _warn_once() -> None:
    global _WARNED
    if _WARNED:
        return
    _WARNED = True
    _w.warn(
        "myco.genesis is a deprecated shim for myco.germination "
        "(renamed at v0.5.3 for fungal-vocabulary consistency). "
        "Both import paths work across the 0.x line; the shim is "
        "scheduled for removal at v1.0.0.",
        DeprecationWarning,
        stacklevel=2,
    )


_warn_once()

__all__ = [
    "bootstrap",
    "run_cli",
    "DEFAULT_CONTRACT_VERSION",
    "DEFAULT_ENTRY_POINT",
]
