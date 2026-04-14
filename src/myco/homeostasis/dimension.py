"""Dimension base class.

Every lint dimension subclasses ``Dimension``, overrides ``run``, and
declares three class attributes: ``id``, ``category``,
``default_severity``. Dimensions live one-per-file under
``src/myco/homeostasis/dimensions/``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar, Iterable

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
    """

    #: Stable, versioned identifier (``L0``, ``L1``, ``S1``, …).
    id: ClassVar[str]

    #: Lint category this dimension belongs to.
    category: ClassVar[Category]

    #: Default severity for findings this dimension emits.
    default_severity: ClassVar[Severity]

    @abstractmethod
    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        """Yield findings for the substrate in ``ctx``.

        Dimensions that find nothing return an empty iterable. Raising
        propagates upward — per Stage B.2 craft Round 2.5-A, a
        dimension that crashes is a bug, not a finding.
        """

    @property
    def explain(self) -> str:
        """Prose description (default: the class docstring).

        Consumed by ``myco immune --explain <id>`` in Stage B.7.
        """
        return (self.__class__.__doc__ or "").strip()
