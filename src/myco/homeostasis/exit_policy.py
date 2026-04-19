"""Exit-policy grammar parser and evaluator.

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
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum

from myco.core.errors import ContractError
from myco.core.severity import Severity

from .finding import Category, Finding

__all__ = ["Threshold", "ExitPolicy", "parse_exit_policy"]


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
            # MEDIUM and LOW never trip the exit code, regardless of threshold.
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
        # Global form.
        if spec not in _GLOBAL_KEYWORDS:
            raise ContractError(
                f"unknown global --exit-on keyword: {spec!r}"
                f" (expected one of {sorted(_GLOBAL_KEYWORDS)})"
            )
        t = Threshold(spec)
        return ExitPolicy(dict.fromkeys(Category, t))

    # Per-category list.
    explicit: dict[Category, Threshold] = {}
    for piece in spec.split(","):
        piece = piece.strip()
        if ":" not in piece:
            raise ContractError(
                f"--exit-on per-category rule must contain ':' — got {piece!r}"
            )
        cat_raw, _, thr_raw = piece.partition(":")
        cat_raw, thr_raw = cat_raw.strip(), thr_raw.strip()
        try:
            cat = Category.from_name(cat_raw)
        except ValueError as exc:
            raise ContractError(
                f"unknown category in per-cat rule {piece!r}: {cat_raw!r}"
            ) from exc
        if thr_raw not in _GLOBAL_KEYWORDS:
            raise ContractError(
                f"unknown threshold in per-cat rule {piece!r}: {thr_raw!r}"
                f" (expected one of {sorted(_GLOBAL_KEYWORDS)})"
            )
        if cat in explicit:
            raise ContractError(
                f"category {cat.value!r} specified twice in --exit-on spec"
            )
        explicit[cat] = Threshold(thr_raw)

    # Default unnamed categories to CRITICAL (per exit_codes.md).
    thresholds = {c: explicit.get(c, Threshold.CRITICAL) for c in Category}
    return ExitPolicy(thresholds)
