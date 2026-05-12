"""RL2 — R3 sense-before-assert discipline signal.

Governing doctrine: ``docs/architecture/L1_CONTRACT/protocol.md`` R3
("Sense before asserting") — historically self-described as "not
mechanically enforceable" (line 124). v0.6.0 lands RL2 as a partial
mechanical signal: when a session log shows risky verbs (molt /
sporulate / propagate / ramify) called without a recent sense() call,
RL2 emits a discipline-signal finding.

Severity: LOW at land, ramps to MEDIUM after 30 sessions per
``severity_promotion``.

The session log is at ``.myco/state/session_calls.jsonl``. RL2 reads
the last 50 entries (sliding window) and looks for risky-verb
invocations without a sense() within ±5 calls.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["RL2SenseDisciplineSignal"]

_RISKY_VERBS: frozenset[str] = frozenset(
    {
        "molt",
        "sporulate",
        "propagate",
        "ramify",
        "assimilate",
    }
)


class RL2SenseDisciplineSignal(Dimension):
    """R3 mechanical anchor: risky verb without recent sense() call."""

    id = "RL2"
    category = Category.SEMANTIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        log_path = ctx.substrate.root / ".myco/state" / "session_calls.jsonl"
        if not log_path.is_file():
            return
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()[-50:]
        except (OSError, UnicodeDecodeError):
            return
        if not lines:
            return
        events: list[str] = []
        for line in lines:
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            verb = entry.get("verb") if isinstance(entry, dict) else None
            if isinstance(verb, str):
                events.append(verb)
        # Check each risky verb has sense() within ±5.
        for i, verb in enumerate(events):
            if verb not in _RISKY_VERBS:
                continue
            window = events[max(0, i - 5) : i + 6]
            if "sense" not in window:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"risky verb {verb!r} called without sense() in "
                        f"±5 surrounding calls (R3 discipline signal)"
                    ),
                    path=".myco/state/session_calls.jsonl",
                )
                # One finding per session is enough.
                return
