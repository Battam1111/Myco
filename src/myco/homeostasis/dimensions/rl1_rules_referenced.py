"""RL1 — every rule in the Hard Contract is referenced by some artefact.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration" (v0.5.8 addition).


The Hard Contract at
``docs/architecture/L1_CONTRACT/protocol.md`` enumerates R1-R7.
For the contract to remain enforceable, each rule must appear in
at least one of:

- a reflex signal (``myco.core.reflex``),
- a dimension docstring (this directory),
- a test (``tests/**/*.py``),
- a craft or integrated note under ``notes/``.

RL1 walks those scopes, collects every ``R1``…``R7`` token, and
emits one LOW finding per rule that has zero references. A rule
that nothing mentions is a dead clause — either the doctrine
drifted from implementation or the implementation forgot the
doctrine. Either way, the agent needs to know.

Severity: LOW. Missing references don't corrupt runtime; they
erode the linkage between doctrine and code over time.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_dir

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["RL1RulesReferenced"]

#: The Hard-Contract rules enumerated at L1. Update in lockstep with
#: ``docs/architecture/L1_CONTRACT/protocol.md`` and the R1-R7 block in
#: :mod:`myco.surface.mcp`'s initialization template.
_RULES: tuple[str, ...] = ("R1", "R2", "R3", "R4", "R5", "R6", "R7")

#: Match e.g. "R3", "(R3)", "R3 —", but not "R30" (word boundary).
_RULE_RE: re.Pattern[str] = re.compile(r"\bR[1-7]\b")


class RL1RulesReferenced(Dimension):
    """Every ``R1``-``R7`` rule has at least one artefact reference."""

    id = "RL1"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        seen: set[str] = set()
        for path in _iter_scannable(root):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for match in _RULE_RE.findall(text):
                seen.add(match)
                if len(seen) == len(_RULES):
                    # All rules covered — short-circuit.
                    return
        for rule in _RULES:
            if rule in seen:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"Hard-Contract rule {rule} has no reference in "
                    f"substrate code, docs, or notes — either the "
                    f"rule was retired (update L1 protocol.md) or the "
                    f"implementation is missing its link."
                ),
                path="docs/architecture/L1_CONTRACT/protocol.md",
            )


def _iter_scannable(root: Path) -> Iterator[Path]:
    """Yield Python / Markdown / YAML files under ``root``, pruning skip dirs."""
    stack: list[Path] = [root]
    wanted = {".py", ".md", ".yaml", ".yml"}
    while stack:
        here = stack.pop()
        try:
            entries = list(here.iterdir())
        except OSError:
            continue
        for entry in entries:
            if entry.is_symlink():
                continue
            if entry.is_dir():
                if should_skip_dir(entry.name):
                    continue
                stack.append(entry)
            elif entry.is_file() and entry.suffix.lower() in wanted:
                yield entry
