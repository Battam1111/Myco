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
    """Build a fresh registry populated with every discovered dimension.

    v0.5+: discovery is driven by
    ``importlib.metadata.entry_points(group="myco.dimensions")``.
    See ``myco.homeostasis.dimensions.discover_dimension_classes``
    for fallback semantics and third-party plugin registration.
    """
    reg = DimensionRegistry()
    from . import dimensions as _dims  # noqa: F401 - side-effect import

    for cls in _dims.discover_dimension_classes():
        try:
            reg.register(cls())
        except ContractError:
            # Duplicate id across entry-points (e.g. built-in + a
            # third-party that picked the same id). Myco's built-ins
            # win because they appear first; surface the clash as a
            # warning, not a crash, so the immune kernel still runs.
            import warnings
            warnings.warn(
                f"dimension class {cls.__name__!r} is shadowed by an "
                f"earlier registration for id {getattr(cls, 'id', '??')!r}. "
                f"Skipping.",
                UserWarning,
                stacklevel=2,
            )
    return reg
