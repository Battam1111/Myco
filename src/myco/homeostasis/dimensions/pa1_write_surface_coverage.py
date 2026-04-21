"""PA1 — canon ``system.write_surface.allowed`` covers the core paths.

Myco enforces R6 (write surface) via ``write_surface.allowed``: an
agent calling any verb that writes gets its path checked against
this list. A substrate whose list is missing one of the core paths
is effectively broken — e.g. ``myco eat`` can't persist a raw note
if no pattern matches ``notes/raw/<id>.md``.

PA1 emits one MEDIUM finding per uncovered core path. Coverage is
checked by **sampling** — for each core verb's canonical write
target we probe a representative sample path against every allowed
pattern via ``fnmatch.fnmatchcase``. A substrate that declares a
broad pattern like ``notes/**`` covers every narrower v0.5.x
default (``notes/raw/**/*.md``, ``notes/integrated/**/*.md``, etc)
without having to enumerate each one. Narrower declarations that
don't match a sample fire the finding.

Core samples (v0.5.8):

- ``notes/raw/<id>.md`` — ``eat`` writes here
- ``notes/integrated/<id>.md`` — ``assimilate`` / ``digest`` write here
- ``notes/distilled/<id>.md`` — ``sporulate`` writes here
- ``_canon.yaml`` — ``molt`` / ``germinate`` write here
- ``docs/contract_changelog.md`` — ``molt`` appends here

(The ``<id>`` placeholders are angle-bracketed so the circulation-
graph regex treats them as illustrative rather than real doc-ref
edges, avoiding a self-triggered SE1 finding.)

Severity: MEDIUM. Missing coverage is a configuration break, not a
corruption; operators can widen the list and resume.

Fixable: False. Editing a user's canon to widen trust is
inappropriate autofix territory; the operator should decide what
paths are in-scope.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["PA1WriteSurfaceCoverage"]


#: ``(label, sample_path)`` pairs representing the canonical write
#: target for each v0.5.x verb that writes. A pattern under
#: ``canon.system.write_surface.allowed`` that matches ``sample_path``
#: (via ``fnmatch.fnmatchcase``) is deemed to cover that verb.
#: ``label`` is surfaced in the finding message so operators know
#: which verb is affected.
_CORE_SAMPLES: tuple[tuple[str, str], ...] = (
    ("notes/raw/**/*.md (eat)", "notes/raw/sample.md"),
    (
        "notes/integrated/**/*.md (assimilate/digest)",
        "notes/integrated/sample.md",
    ),
    ("notes/distilled/**/*.md (sporulate)", "notes/distilled/sample.md"),
    ("_canon.yaml (molt/germinate)", "_canon.yaml"),
    ("docs/contract_changelog.md (molt)", "docs/contract_changelog.md"),
)


class PA1WriteSurfaceCoverage(Dimension):
    """``canon.system.write_surface.allowed`` covers core v0.5.x paths."""

    id = "PA1"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        system = ctx.substrate.canon.system or {}
        ws = system.get("write_surface") or {}
        allowed = ws.get("allowed") or []
        if not isinstance(allowed, list):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    "canon.system.write_surface.allowed is not a list; "
                    "write_surface enforcement will reject every path."
                ),
                path="_canon.yaml",
            )
            return
        patterns = [str(x) for x in allowed]
        for label, sample in _CORE_SAMPLES:
            if any(fnmatch.fnmatchcase(sample, p) for p in patterns):
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon.system.write_surface.allowed does not match "
                    f"sample path {sample!r} for {label}; the "
                    f"corresponding verb will fail its write-surface "
                    f"check. Add a covering pattern or confirm the "
                    f"substrate is intentionally read-only for that "
                    f"verb."
                ),
                path="_canon.yaml",
            )
