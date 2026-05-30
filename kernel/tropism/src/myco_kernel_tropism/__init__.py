"""Myco v0.9 — kernel/tropism.

Per L1/TROPISM: the substrate's positive dispatch form — continuously
evolving appetite gradient + substrate-initiated sporocarp emission at
fruiting triggers.

Public surface (re-exported from the submodules for ergonomic imports):

- ``appetite_axis`` — per-axis schema/state + update rules (L1/TROPISM §3 + §B).
- ``gradient`` — the multi-axis :class:`GradientConfiguration` + per-cycle advance.
- ``sporocarp`` — substrate-initiated typed observables + emission helpers.
- ``persistence`` — gradient.cb canonical-bytes save/load (L4 M7).
"""

from __future__ import annotations

from myco_kernel_tropism.appetite_axis import (
    AppetiteAxis,
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
    UpdateRule,
)
from myco_kernel_tropism.gradient import (
    AxisAlreadyRegistered,
    AxisNotFound,
    GradientConfiguration,
    GradientError,
)
from myco_kernel_tropism.persistence import (
    GRADIENT_FILENAME,
    GRADIENT_FORMAT_VERSION,
    PersistenceError,
    gradient_from_canonical_bytes,
    gradient_to_canonical_bytes,
    load_gradient,
    save_gradient,
)
from myco_kernel_tropism.sporocarp import (
    SPOROCARP_TYPE_TAG,
    Sporocarp,
    SporocarpError,
    emit_appetite_fruiting,
    emit_mortality_signal,
)

__version__ = "0.9.0a1"

__all__ = [
    "GRADIENT_FILENAME",
    "GRADIENT_FORMAT_VERSION",
    "SPOROCARP_TYPE_TAG",
    "AppetiteAxis",
    "AxisAlreadyRegistered",
    "AxisClass",
    "AxisNotFound",
    "AxisSchema",
    "DecayRule",
    "GradientConfiguration",
    "GradientError",
    "NoOpRule",
    "PersistenceError",
    "Sporocarp",
    "SporocarpError",
    "UpdateRule",
    "__version__",
    "emit_appetite_fruiting",
    "emit_mortality_signal",
    "gradient_from_canonical_bytes",
    "gradient_to_canonical_bytes",
    "load_gradient",
    "save_gradient",
]
