"""Cluster module — v0.8.8 max-aggressive merge of finding, dimension, skeleton, exit_policy, registry.

=== finding ===
Finding type emitted by lint dimensions.

See ``docs/architecture/L1_CONTRACT/exit_codes.md`` for the four-
category taxonomy and the severity ladder.

=== dimension ===
Dimension base class.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Lint dimensions" (the shape every subclass conforms to).

Every lint dimension subclasses ``Dimension``, overrides ``run``, and
declares three class attributes: ``id``, ``category``,
``default_severity``. Dimensions live one-per-file under
``src/myco/homeostasis/dimensions/``.

v0.5.5 adds a **fixable dimension seam**:

- ``Dimension.fixable`` is a class-level flag (``False`` by default).
  Subclasses that can autonomously repair the finding they emit set
  it to ``True``.
- ``Dimension.fix(ctx, finding)`` is the opt-in repair hook. The
  default implementation is a no-op so non-fixable dimensions don't
  have to override anything; ``myco.homeostasis.kernel.run_immune``
  only calls ``fix`` when ``fixable=True``.

The ``--fix`` flag existed since v0.4.0 but was plumbed through as a
no-op. v0.5.5 lands the first two concrete fixable dimensions (M2
and MB1); future dimensions follow the same shape.

=== skeleton ===
Skeleton-mode downgrade.

Per ``docs/architecture/L1_CONTRACT/exit_codes.md``: when the substrate
is an auto-seeded skeleton (canon-declared marker present), selected
lint dimensions have their CRITICAL findings capped at HIGH so that a
first-run hunger call does not block legitimate adoption.

The set of affected dimensions is canon-driven
(``lint.skeleton_downgrade.affected_dimensions``), never hard-coded.

=== exit_policy ===
Exit-policy grammar parser and evaluator.

Grammar from ``docs/architecture/L1_CONTRACT/exit_codes.md``::

    <spec>         ::= <global> | <per-cat-list>
    <global>       ::= "never" | "critical" | "high"
    <per-cat-list> ::= <cat-rule> ("," <cat-rule>)*
    <cat-rule>     ::= <cat> ":" <threshold>
    <threshold>    ::= "never" | "critical" | "high"

Semantics:

- ``never``     — findings in this category never trip exit ≥1.
- ``critical``  — only CRITICAL findings trip; exit = 2.
- ``high``      — HIGH or CRITICAL findings trip; exit = 1 on HIGH, 2 on CRITICAL.
- Global forms apply the same threshold to all four categories.
- Per-category lists default unnamed categories to ``critical``.
- Unknown category or threshold → :class:`ContractError` (exit 3).

=== registry ===
Dimension registry.

Plain object, not a module-global singleton (per Stage B.2 craft Round
1.5-E). Tests construct their own empty registries; production code
calls :func:`default_registry` to get a fresh populated one.

v0.5.3 adds :func:`register_external_dimension`, the public entry point
substrate-local plugins call at import time to contribute a
:class:`Dimension` subclass without going through entry-points. See
``docs/contract_changelog.md`` § v0.5.3.
"""

from __future__ import annotations

import threading
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any, ClassVar

from myco.core.identity_cluster import ContractError, MycoContext, Severity

# =========================================================================
# === finding — formerly finding.py
# =========================================================================

class Category(str, Enum):
    """The four lint-dimension categories from L1 exit_codes.md."""

    MECHANICAL = "mechanical"
    SHIPPED = "shipped"
    METABOLIC = "metabolic"
    SEMANTIC = "semantic"

    @classmethod
    def from_name(cls, name: str) -> Category:
        """Parse a category name (case-insensitive) into a ``Category``.

        Raises ``ValueError`` with the offending input echoed back
        on any name that's not one of the four canonical categories.
        """
        try:
            return cls(name.lower())
        except ValueError as exc:
            raise ValueError(f"unknown category: {name!r}") from exc


@dataclass(frozen=True)
class Finding:
    """A single lint finding emitted by one dimension.

    ``path`` is stored as ``str | None`` rather than ``Path | None`` to
    avoid platform-dependent hashing surprises and to keep ``Finding``
    trivially serializable for ``--json`` output in Stage B.7.
    """

    dimension_id: str
    category: Category
    severity: Severity
    message: str
    path: str | None = None
    line: int | None = None
    fixable: bool = False

    @classmethod
    def from_path(
        cls,
        *,
        dimension_id: str,
        category: Category,
        severity: Severity,
        message: str,
        path: Path | None = None,
        line: int | None = None,
        fixable: bool = False,
    ) -> Finding:
        """Ergonomic constructor that accepts a ``Path`` instead of a string."""
        return cls(
            dimension_id=dimension_id,
            category=category,
            severity=severity,
            message=message,
            path=str(path) if path is not None else None,
            line=line,
            fixable=fixable,
        )


# =========================================================================
# === dimension — formerly dimension.py
# =========================================================================

class Dimension(ABC):
    """Base class for lint dimensions.

    Subclasses MUST set ``id``, ``category``, and ``default_severity``
    as class attributes. ``default_severity`` is the severity the
    dimension will use for most findings; individual findings may
    override (e.g. a mostly-MEDIUM dimension can emit a single
    CRITICAL).

    Subclasses that can repair the issue they detect set
    ``fixable = True`` and override :meth:`fix`. The default
    :attr:`fixable` is ``False`` and :meth:`fix` is a safe no-op, so
    dimensions that only detect (never repair) need no changes.
    """

    id: ClassVar[str]
    category: ClassVar[Category]
    default_severity: ClassVar[Severity]
    fixable: ClassVar[bool] = False

    @abstractmethod
    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        """Yield findings for the substrate in ``ctx``.

        Dimensions that find nothing return an empty iterable. Raising
        propagates upward — per Stage B.2 craft Round 2.5-A, a
        dimension that crashes is a bug, not a finding.
        """

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Attempt to repair a single ``finding`` emitted by this dimension.

        Default implementation is a no-op that returns
        ``{"applied": False, "detail": "no fix implemented"}``. Only
        called by :func:`myco.homeostasis.kernel.run_immune` when the
        kernel sees ``type(self).fixable is True`` — i.e. the default
        never runs.

        Fixable subclasses override this to:

        - create or correct **exactly one** file or field,
        - never delete,
        - never overwrite a non-empty file,
        - respect the substrate write-surface (the kernel's safety
          guard checks this before calling ``fix``; subclasses that
          write outside their declared target may still be skipped).

        Return shape: ``{"applied": bool, "detail": str}``. The
        ``applied`` flag is ``True`` only when the fix actually wrote
        something; idempotent no-ops (target already correct) return
        ``applied=False`` with a descriptive detail. Unexpected
        failures raise — the kernel records them as ``error``.
        """
        _ = finding
        _ = ctx
        return {"applied": False, "detail": "no fix implemented"}

    @property
    def explain(self) -> str:
        """Prose description (default: the class docstring).

        Consumed by ``myco immune --explain <id>`` in Stage B.7.
        """
        return (self.__class__.__doc__ or "").strip()


# =========================================================================
# === skeleton — formerly skeleton.py
# =========================================================================

def apply_skeleton_downgrade(
    findings: Iterable[Finding], *, ctx: MycoContext
) -> tuple[Finding, ...]:
    """Cap CRITICAL→HIGH for canon-declared dimensions when skeleton mode is active.

    No-op when the substrate is not in skeleton mode (no
    ``.myco/state/autoseeded.txt`` marker) or when the canon's
    ``lint.skeleton_downgrade.affected_dimensions`` list is empty.
    """
    findings_t = tuple(findings)
    if not ctx.substrate.is_skeleton:
        return findings_t
    lint = ctx.substrate.canon.lint or {}
    sd = lint.get("skeleton_downgrade") or {}
    affected = set(sd.get("affected_dimensions") or ())
    if not affected:
        return findings_t
    out: list[Finding] = []
    for f in findings_t:
        if f.dimension_id in affected and f.severity == Severity.CRITICAL:
            out.append(replace(f, severity=Severity.HIGH))
        else:
            out.append(f)
    return tuple(out)


# =========================================================================
# === exit_policy — formerly exit_policy.py
# =========================================================================

class Threshold(str, Enum):
    """Per-category exit threshold."""

    NEVER = "never"
    CRITICAL = "critical"
    HIGH = "high"


_GLOBAL_KEYWORDS: frozenset[str] = frozenset(t.value for t in Threshold)


@dataclass(frozen=True)
class ExitPolicy:
    """Category → threshold mapping plus :meth:`compute`."""

    thresholds: Mapping[Category, Threshold]

    def compute(self, findings: Iterable[Finding]) -> int:
        """Return the exit code (0 / 1 / 2) implied by ``findings``."""
        worst = 0
        for f in findings:
            threshold = self.thresholds[f.category]
            if threshold is Threshold.NEVER:
                continue
            if f.severity is Severity.CRITICAL:
                worst = max(worst, 2)
            elif f.severity is Severity.HIGH and threshold is Threshold.HIGH:
                worst = max(worst, 1)
        return worst


def parse_exit_policy(spec: str) -> ExitPolicy:
    """Parse a ``--exit-on`` spec into an :class:`ExitPolicy`.

    Raises :class:`ContractError` on any grammar violation.
    """
    if not isinstance(spec, str):
        raise ContractError(
            f"--exit-on spec must be a string, got {type(spec).__name__}"
        )
    spec = spec.strip()
    if not spec:
        raise ContractError("--exit-on spec must not be empty")
    if ":" not in spec:
        if spec not in _GLOBAL_KEYWORDS:
            raise ContractError(
                f"unknown global --exit-on keyword: {spec!r} (expected one of {sorted(_GLOBAL_KEYWORDS)})"
            )
        t = Threshold(spec)
        return ExitPolicy(dict.fromkeys(Category, t))
    explicit: dict[Category, Threshold] = {}
    for piece in spec.split(","):
        piece = piece.strip()
        if ":" not in piece:
            raise ContractError(
                f"--exit-on per-category rule must contain ':' — got {piece!r}"
            )
        cat_raw, _, thr_raw = piece.partition(":")
        cat_raw, thr_raw = (cat_raw.strip(), thr_raw.strip())
        try:
            cat = Category.from_name(cat_raw)
        except ValueError as exc:
            raise ContractError(
                f"unknown category in per-cat rule {piece!r}: {cat_raw!r}"
            ) from exc
        if thr_raw not in _GLOBAL_KEYWORDS:
            raise ContractError(
                f"unknown threshold in per-cat rule {piece!r}: {thr_raw!r} (expected one of {sorted(_GLOBAL_KEYWORDS)})"
            )
        if cat in explicit:
            raise ContractError(
                f"category {cat.value!r} specified twice in --exit-on spec"
            )
        explicit[cat] = Threshold(thr_raw)
    thresholds = {c: explicit.get(c, Threshold.CRITICAL) for c in Category}
    return ExitPolicy(thresholds)


# =========================================================================
# === registry — formerly registry.py
# =========================================================================

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
                f"duplicate dimension id: {dim.id!r} (already registered: {type(self._dims[dim.id]).__name__})"
            )
        self._dims[dim.id] = dim

    def get(self, dim_id: str) -> Dimension:
        """Return the registered ``Dimension`` for ``dim_id`` (raises KeyError if absent)."""
        return self._dims[dim_id]

    def has(self, dim_id: str) -> bool:
        """Return True iff ``dim_id`` is a registered dimension."""
        return dim_id in self._dims

    def all(self) -> tuple[Dimension, ...]:
        """All dimensions, sorted by id for deterministic output."""
        return tuple(self._dims[k] for k in sorted(self._dims))

    def __len__(self) -> int:
        return len(self._dims)


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
            f"register_external_dimension: expected a Dimension subclass (or instance), got {cls!r}"
        )
    dim_id = getattr(cls, "id", None)
    if not isinstance(dim_id, str) or not dim_id:
        raise ContractError(
            f"dimension class {cls.__name__!r} must declare a non-empty 'id' class attribute before it can be registered"
        )
    with _EXTERNAL_LOCK:
        for existing in _EXTERNAL_DIMENSION_CLASSES:
            if getattr(existing, "id", None) == dim_id:
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
            import warnings

            warnings.warn(
                f"dimension class {cls.__name__!r} is shadowed by an earlier registration for id {getattr(cls, 'id', '??')!r}. Skipping.",
                UserWarning,
                stacklevel=2,
            )

    for cls in _dims.discover_dimension_classes():
        _try_register(cls)
    for cls in external_dimension_classes():
        _try_register(cls)
    return reg
