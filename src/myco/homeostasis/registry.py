"""Dimension registry.

Plain object, not a module-global singleton (per Stage B.2 craft Round
1.5-E). Tests construct their own empty registries; production code
calls :func:`default_registry` to get a fresh populated one.
"""

from __future__ import annotations

from myco.core.errors import ContractError

from .dimension import Dimension

__all__ = ["DimensionRegistry", "default_registry"]


class DimensionRegistry:
    """Holds :class:`Dimension` instances keyed by ``id``."""

    def __init__(self) -> None:
        self._dims: dict[str, Dimension] = {}

    def register(self, dim: Dimension) -> None:
        """Register ``dim``. Raises on type mismatch or duplicate id."""
        if not isinstance(dim, Dimension):
            raise TypeError(
                f"expected Dimension instance, got {type(dim).__name__}"
            )
        if dim.id in self._dims:
            raise ContractError(
                f"duplicate dimension id: {dim.id!r}"
                f" (already registered: {type(self._dims[dim.id]).__name__})"
            )
        self._dims[dim.id] = dim

    def get(self, dim_id: str) -> Dimension:
        return self._dims[dim_id]

    def has(self, dim_id: str) -> bool:
        return dim_id in self._dims

    def all(self) -> tuple[Dimension, ...]:
        """All dimensions, sorted by id for deterministic output."""
        return tuple(self._dims[k] for k in sorted(self._dims))

    def __len__(self) -> int:
        return len(self._dims)


def default_registry() -> DimensionRegistry:
    """Build a fresh registry populated with every built-in dimension.

    Lazily imports the ``dimensions`` subpackage to trigger
    registration side effects.
    """
    reg = DimensionRegistry()
    from . import dimensions as _dims  # noqa: F401 - side-effect import

    for cls in _dims.ALL:
        reg.register(cls())
    return reg
