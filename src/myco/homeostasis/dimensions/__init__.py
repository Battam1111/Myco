"""Per-dimension lint rules.

One module per dimension. ``ALL`` lists every Dimension class the
built-in :func:`myco.homeostasis.default_registry` should register.

Stage B.2 ships only the smoke ``L0KernelAlive`` dimension. Real
mechanical / shipped / metabolic / semantic dimensions land in
Stage B.8, authored fresh against L1/L2 needs rather than ported from
the v0.3 30-dimension table.
"""

from __future__ import annotations

from ..dimension import Dimension
from .l0_kernel_alive import L0KernelAlive

__all__ = ["ALL", "L0KernelAlive"]


#: Every built-in dimension class, registered by
#: :func:`myco.homeostasis.default_registry`.
ALL: tuple[type[Dimension], ...] = (L0KernelAlive,)
