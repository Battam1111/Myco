"""Dimension base class.

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
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import Any, ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from .finding import Category, Finding

__all__ = ["Dimension"]


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

    #: Stable, versioned identifier (``L0``, ``L1``, ``S1``, …).
    id: ClassVar[str]

    #: Lint category this dimension belongs to.
    category: ClassVar[Category]

    #: Default severity for findings this dimension emits.
    default_severity: ClassVar[Severity]

    #: True iff this dimension can autonomously repair the issue it
    #: emits. Subclasses that override :meth:`fix` set this to True;
    #: the kernel only dispatches to ``fix`` for dimensions where it
    #: is True. Default False so non-fixable dimensions require no
    #: changes. v0.5.5 first-class seam.
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
        # The finding argument is unused in the default no-op, but
        # subclass overrides consume it. Keep the signature stable.
        _ = finding
        _ = ctx
        return {"applied": False, "detail": "no fix implemented"}

    @property
    def explain(self) -> str:
        """Prose description (default: the class docstring).

        Consumed by ``myco immune --explain <id>`` in Stage B.7.
        """
        return (self.__class__.__doc__ or "").strip()
