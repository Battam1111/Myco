"""XYZ1 — substrate has more than 100 raw notes.

Reference SEMANTIC/LOW dimension shipped by the ``example_overlay``
substrate-local plugin. Exists to exercise the per-substrate
extensibility axis (L0 P5) end-to-end: a substrate-local
:class:`Dimension` subclass registered via
:func:`myco.homeostasis.registry.register_external_dimension`, picked
up by ``default_registry()`` on every immune run, and surfaced in
``myco graft --list``.

Threshold of 100 is intentionally silly. The point is to demonstrate
the contract — a real plugin would key off something substrate-
specific (``decision``-tagged note count, primordium age, etc.).
Substrates that want to police raw-note backlog use the kernel's MB1
dimension instead; XYZ1 is a fixture, not a recommendation.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["XYZ1RawNoteThreshold"]


#: Substrates with more raw notes than this threshold trigger XYZ1.
#: Exposed as a module-level constant so tests can assert against it
#: without re-deriving the magic number.
RAW_NOTE_THRESHOLD: int = 100


class XYZ1RawNoteThreshold(Dimension):
    """Fires when ``notes/raw/`` holds more than ``RAW_NOTE_THRESHOLD`` files."""

    id: ClassVar[str] = "XYZ1"
    category: ClassVar[Category] = Category.SEMANTIC
    default_severity: ClassVar[Severity] = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        raw_dir = ctx.substrate.paths.notes / "raw"
        if not raw_dir.is_dir():
            return
        # Count *.md files only — matches MB1 / hunger semantics.
        count = sum(1 for p in raw_dir.glob("*.md") if p.is_file())
        if count <= RAW_NOTE_THRESHOLD:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"raw-note backlog {count} exceeds the example_overlay "
                f"threshold of {RAW_NOTE_THRESHOLD}; assimilate or excrete"
            ),
            path="notes/raw/",
        )
