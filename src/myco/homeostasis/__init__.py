"""``myco.homeostasis`` — immune system + sanctioned evolution.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``.
Stage B.2 surface — kernel infrastructure only; real dimensions land
in Stage B.8.
"""

from __future__ import annotations

from .dimension import Dimension
from .exit_policy import ExitPolicy, Threshold, parse_exit_policy
from .finding import Category, Finding
from .kernel import run_immune
from .registry import DimensionRegistry, default_registry
from .skeleton import apply_skeleton_downgrade

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
