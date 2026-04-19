"""Dimension registry.

Plain object, not a module-global singleton (per Stage B.2 craft Round
1.5-E). Tests construct their own empty registries; production code
calls :func:`default_registry` to get a fresh populated one.

v0.5.3 adds :func:`register_external_dimension`, the public entry point
substrate-local plugins call at import time to contribute a
:class:`Dimension` subclass without going through entry-points. See
``docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md``.
"""

from __future__ import annotations

import threading

from myco.core.errors import ContractError

from .dimension import Dimension

__all__ = [
    "DimensionRegistry",
    "default_registry",
    "register_external_dimension",
    "external_dimension_classes",
]


class DimensionRegistry:
    """Holds :class:`Dimension` instances keyed by ``id``."""

    def __init__(self) -> None:
        self._dims: dict[str, Dimension] = {}

    def register(self, dim: Dimension) -> None:
        """Register ``dim``. Raises on type mismatch or duplicate id."""
        if not isinstance(dim, Dimension):
            raise TypeError(f"expected Dimension instance, got {type(dim).__name__}")
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


#: Substrate-local plugins register dimension classes here at import
#: time. :func:`default_registry` drains this list after entry-points
#: discovery so local overrides NEVER silently shadow a packaged
#: dimension (duplicate ids are skipped with a :class:`UserWarning`).
_EXTERNAL_DIMENSION_CLASSES: list[type[Dimension]] = []
_EXTERNAL_LOCK = threading.RLock()


def register_external_dimension(cls_or_instance: object) -> type[Dimension]:
    """Register a :class:`Dimension` subclass for substrate-local plugins.

    Accepts either a class or an instance (the instance's ``type``
    gets registered so ``default_registry`` can instantiate fresh).
    Idempotent per id: a second call with the same ``id`` attribute is
    a no-op (not an error) so repeated imports during test runs don't
    explode.

    Returns the class that ended up registered (useful for
    `@register_external_dimension` decorator style even though that's
    not required).
    """
    if isinstance(cls_or_instance, type):
        cls = cls_or_instance
    else:
        cls = type(cls_or_instance)

    if not (isinstance(cls, type) and issubclass(cls, Dimension)):
        raise TypeError(
            f"register_external_dimension: expected a Dimension subclass "
            f"(or instance), got {cls!r}"
        )

    dim_id = getattr(cls, "id", None)
    if not isinstance(dim_id, str) or not dim_id:
        raise ContractError(
            f"dimension class {cls.__name__!r} must declare a non-empty "
            f"'id' class attribute before it can be registered"
        )

    with _EXTERNAL_LOCK:
        for existing in _EXTERNAL_DIMENSION_CLASSES:
            if getattr(existing, "id", None) == dim_id:
                # Idempotent: same id already registered — no-op.
                return existing
        _EXTERNAL_DIMENSION_CLASSES.append(cls)
    return cls


def external_dimension_classes() -> tuple[type[Dimension], ...]:
    """Snapshot of the externally-registered dimension class list."""
    with _EXTERNAL_LOCK:
        return tuple(_EXTERNAL_DIMENSION_CLASSES)


def default_registry() -> DimensionRegistry:
    """Build a fresh registry populated with every discovered dimension.

    v0.5+: discovery is driven by
    ``importlib.metadata.entry_points(group="myco.dimensions")``.
    See ``myco.homeostasis.dimensions.discover_dimension_classes``
    for fallback semantics and third-party plugin registration.

    v0.5.3: after entry-points + fallback discovery, drain
    :func:`external_dimension_classes` (substrate-local plugins) so
    `.myco/plugins/` authors can register dimensions without touching
    ``pyproject.toml``. A duplicate id (local + packaged) logs a
    :class:`UserWarning` and is skipped — packaged wins.
    """
    reg = DimensionRegistry()
    from . import dimensions as _dims

    def _try_register(cls: type[Dimension]) -> None:
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

    for cls in _dims.discover_dimension_classes():
        _try_register(cls)
    for cls in external_dimension_classes():
        _try_register(cls)
    return reg
