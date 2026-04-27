"""RL3 — R4 eat-on-decision discipline signal.

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R4
("Eat insights the moment they occur"). Historically not
mechanically enforceable. RL3 partial mechanical signal: when
session events show decision-keyword hits but few myco_eat calls,
emit signal.

Two-channel detection:
1. Explicit ``decision_marker: bool`` agent-tag in session events
   (preferred, low false-positive).
2. Keyword heuristic on session events' textual fields (fallback).

Severity: LOW always (fallback is heuristic).
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["RL3EatDisciplineSignal"]

_DECISION_KEYWORDS: frozenset[str] = frozenset(
    {
        "decided",
        "决定",
        "choose",
        "rejected",
        "friction",
        "pivot",
        "insight",
        "选定",
        "拒绝",
        "摩擦",
    }
)


class RL3EatDisciplineSignal(Dimension):
    """R4 mechanical anchor: decision marker / keyword without eat()."""

    id = "RL3"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        log_path = ctx.substrate.root / ".myco_state" / "session_calls.jsonl"
        if not log_path.is_file():
            return
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()[-50:]
        except (OSError, UnicodeDecodeError):
            return
        if not lines:
            return
        eat_count = 0
        decision_count = 0
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            verb = entry.get("verb")
            if verb == "eat":
                eat_count += 1
            if entry.get("decision_marker") is True:
                decision_count += 1
            text = " ".join(
                str(v) for v in entry.values() if isinstance(v, str)
            ).lower()
            for kw in _DECISION_KEYWORDS:
                if kw in text:
                    decision_count += 1
                    break
        # Heuristic threshold: > 3 decisions per eat call.
        if eat_count == 0 and decision_count == 0:
            return
        ratio = decision_count / max(eat_count, 1)
        if ratio > 3.0:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"decision/eat ratio {ratio:.1f} (decisions={decision_count}, "
                    f"eats={eat_count}) suggests R4 eat-on-decision discipline "
                    f"is being deferred"
                ),
                path=".myco_state/session_calls.jsonl",
            )
