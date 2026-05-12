"""PA1 — canon ``system.write_surface.allowed`` covers the core paths.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


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
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA1WriteSurfaceCoverage"]


#: ``(label, sample_path)`` pairs representing the canonical write
#: target for each v0.5.x verb that writes. A pattern under
#: ``canon.system.write_surface.allowed`` that matches ``sample_path``
#: (via ``fnmatch.fnmatchcase``) is deemed to cover that verb.
#: ``label`` is surfaced in the finding message so operators know
#: which verb is affected.
#: Static samples for verbs whose paths follow the same substrate
#: subdir convention regardless of layout. The dynamic samples
#: (canon, contract_changelog) are resolved from substrate.paths at
#: run() time below, so PA1 correctly checks the substrate's actual
#: declared layout (legacy ``_canon.yaml`` vs v0.8.4+ ``.myco/canon.yaml``).
_STATIC_SAMPLES: tuple[tuple[str, str, str], ...] = (
    ("notes/raw/**/*.md (eat)", "notes_dir", "raw/sample.md"),
    (
        "notes/integrated/**/*.md (assimilate/digest)",
        "notes_dir",
        "integrated/sample.md",
    ),
    ("notes/distilled/**/*.md (sporulate)", "notes_dir", "distilled/sample.md"),
)


class PA1WriteSurfaceCoverage(Dimension):
    """``canon.system.write_surface.allowed`` covers core v0.5.x paths."""

    id = "PA1"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Resolve dynamic sample paths from the substrate's declared
        # layout so PA1 works identically across legacy + v0.8.4+ shapes.
        paths = ctx.substrate.paths
        root = ctx.substrate.root
        canon_rel = paths.canon.relative_to(root).as_posix()
        notes_rel = paths.notes.relative_to(root).as_posix()
        docs_rel = paths.docs.relative_to(root).as_posix()
        samples = [
            *_STATIC_SAMPLES,
            ("canon (molt/germinate)", "_canon_path", canon_rel),
            (
                "contract_changelog.md (molt)",
                "_doc_path",
                f"{docs_rel}/contract_changelog.md",
            ),
        ]

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
                path=canon_rel,
            )
            return
        patterns = [str(x) for x in allowed]
        for entry in samples:
            label = entry[0]
            kind = entry[1]
            tail = entry[2]
            if kind == "notes_dir":
                sample = f"{notes_rel}/{tail}"
            elif kind in ("_canon_path", "_doc_path"):
                sample = tail
            else:
                sample = tail
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
                path=canon_rel,
            )
