"""``myco.homeostasis`` — immune system + sanctioned evolution.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``.
Stage B.2 surface — kernel infrastructure only; real dimensions land
in Stage B.8.
"""

from __future__ import annotations

from .kernel import run_immune
from .primitives_cluster import (
    Category,
    Dimension,
    DimensionRegistry,
    ExitPolicy,
    Finding,
    Threshold,
    apply_skeleton_downgrade,
    default_registry,
    parse_exit_policy,
)

__all__ = [
    "Category",
    "Finding",
    "Dimension",
    "DimensionRegistry",
    "default_registry",
    "Threshold",
    "ExitPolicy",
    "parse_exit_policy",
    "apply_skeleton_downgrade",
    "run_immune",
]
