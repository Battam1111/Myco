"""evolve verb: validate a proposal document's shape against gates.

MAJOR 9 (v0.5, scoped down from the legacy v0.3 mutation/selection
engine): reads a proposal markdown file, runs a small set of gates
against its frontmatter and body, returns a pass/fail verdict.

Scope discipline: v0.5 ships only the *shape* gates (body-non-empty,
size-bounds, round-marker presence). The redact-based "no secret
leak" gate and the full skill-mutation engine from
``legacy_v0_3/src/myco/evolve.py`` are deferred to v0.6+ — they
require a concurrent port of ``myco.redact`` plus a proposal-versus-
current-state diff harness.

Exit codes:

- ``0`` — every gate passed; the proposal is well-formed.
- ``1`` — at least one gate failed; details in ``payload.violations``.
- ``3`` — operational error (file not found, unreadable). Raised as
  ``ContractError`` / ``UsageError`` by the gate pre-checks.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/surface.md``
(governance-verbs appendix, v0.5). Legacy reference:
``legacy_v0_3/docs/craft_protocol.md`` body-schema lint (Round 3).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Mapping

from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, UsageError

__all__ = ["run"]


#: Floor for total body chars. Shorter proposals are effectively
#: empty; we refuse to even evaluate the round structure.
_MIN_BODY_CHARS: int = 300

#: Floor for per-round body chars. Matches the legacy v0.3
#: ``min_round_body_chars`` default (``craft_protocol.md``:310).
_MIN_ROUND_BODY_CHARS: int = 150

#: Ceiling for total body chars, belt-and-suspenders against a
#: pathologically large proposal file. 250k ~= the upper bound of a
#: human-authored multi-round craft; anything larger should be
#: split into sibling proposals.
_MAX_BODY_CHARS: int = 250_000

#: Round-marker pattern. Matches the v0.4 convention
#: (``## Round 1 — 主张``, ``## Round 1.5 — 自我反驳``, etc.) and the
#: legacy aliases (``## R(N)`` / ``## 第N轮`` / ``## ラウンド N``).
_ROUND_MARKER_RE = re.compile(
    r"^##\s+(?:Round|R\()\s*(\d+(?:\.\d+)?)\)?|"
    r"^##\s+第\s*\d+\s*轮|"
    r"^##\s+ラウンド\s*\d+",
    re.MULTILINE,
)

#: Accept the compact ``## Round 1.5 — 自我反驳`` form without the
#: paren variant the legacy regex required. (Supplementary to the
#: main regex above — union applied in :func:`_count_rounds`.)
_ROUND_MARKER_FALLBACK_RE = re.compile(
    r"^##\s+Round\s+\d+(?:\.\d+)?", re.MULTILINE
)


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    """Split a markdown file into (frontmatter dict, body text).

    Returns ``({}, text)`` if no frontmatter block is present.
    """
    if not text.startswith("---"):
        return {}, text
    match = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    if not match:
        return {}, text
    fm_text = match.group(1)
    body = text[match.end():]

    import yaml

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ContractError(
            f"evolve: frontmatter is not valid YAML: {exc}"
        ) from exc
    if not isinstance(fm, dict):
        raise ContractError(
            "evolve: frontmatter top-level must be a YAML mapping"
        )
    return fm, body


def _count_rounds(body: str) -> int:
    hits = set()
    for m in _ROUND_MARKER_RE.finditer(body):
        hits.add(m.group(0))
    for m in _ROUND_MARKER_FALLBACK_RE.finditer(body):
        hits.add(m.group(0))
    return len(hits)


def _round_body_lengths(body: str) -> list[int]:
    """Segment the body by round markers and return each segment's length.

    Uses the fallback regex (simpler, matches v0.4 crafts directly).
    """
    positions = [m.start() for m in _ROUND_MARKER_FALLBACK_RE.finditer(body)]
    if not positions:
        return []
    positions.append(len(body))
    return [
        positions[i + 1] - positions[i]
        for i in range(len(positions) - 1)
    ]


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    raw_path = args.get("proposal")
    if not raw_path:
        raise UsageError("evolve: --proposal <path> is required")
    target = Path(str(raw_path))
    if not target.is_absolute():
        target = ctx.substrate.root / target
    if not target.is_file():
        raise UsageError(f"evolve: proposal file not found: {target}")

    try:
        text = target.read_text(encoding="utf-8")
    except OSError as exc:
        raise ContractError(
            f"evolve: cannot read proposal: {exc}"
        ) from exc

    fm, body = _parse_frontmatter(text)
    violations: list[dict[str, str]] = []

    # Gate G1 — frontmatter has type=proposal or type=craft (accept
    # either since v0.5 crafts ARE proposals; a full schema split is
    # a post-v0.5 decision).
    fm_type = str(fm.get("type") or "").strip().lower()
    if fm_type not in {"proposal", "craft"}:
        violations.append(
            {
                "gate": "G1_frontmatter_type",
                "message": (
                    f"proposal must declare `type: proposal` or "
                    f"`type: craft` in its YAML frontmatter; got "
                    f"{fm_type!r}"
                ),
            }
        )

    # Gate G2 — frontmatter has a non-empty title/topic.
    title = fm.get("title") or fm.get("topic")
    if not title or not str(title).strip():
        violations.append(
            {
                "gate": "G2_frontmatter_title",
                "message": (
                    "proposal must carry a non-empty `title:` or `topic:` "
                    "field in its YAML frontmatter"
                ),
            }
        )

    # Gate G3 — body is non-empty and within size bounds.
    body_stripped = body.strip()
    body_len = len(body_stripped)
    if body_len < _MIN_BODY_CHARS:
        violations.append(
            {
                "gate": "G3_body_min",
                "message": (
                    f"proposal body is {body_len} chars, below the "
                    f"{_MIN_BODY_CHARS}-char floor"
                ),
            }
        )
    if body_len > _MAX_BODY_CHARS:
        violations.append(
            {
                "gate": "G3_body_max",
                "message": (
                    f"proposal body is {body_len} chars, above the "
                    f"{_MAX_BODY_CHARS}-char ceiling"
                ),
            }
        )

    # Gate G4 — at least two distinct round markers.
    round_count = _count_rounds(body)
    if round_count < 2:
        violations.append(
            {
                "gate": "G4_round_count",
                "message": (
                    f"proposal has {round_count} round marker(s); "
                    f"the three-round craft convention requires at least 2 "
                    f"(claim + revision); 3 (claim + revision + reflection) "
                    f"is the recommended floor"
                ),
            }
        )

    # Gate G5 — every round body segment clears the per-round floor.
    per_round = _round_body_lengths(body)
    if per_round:
        short_rounds = [
            i + 1 for i, length in enumerate(per_round)
            if length < _MIN_ROUND_BODY_CHARS
        ]
        if short_rounds:
            violations.append(
                {
                    "gate": "G5_round_body_min",
                    "message": (
                        f"round section(s) {short_rounds} fall below the "
                        f"{_MIN_ROUND_BODY_CHARS}-char per-round floor"
                    ),
                }
            )

    verdict = "pass" if not violations else "fail"
    exit_code = 0 if not violations else 1
    return Result(
        exit_code=exit_code,
        payload={
            "proposal": str(target.relative_to(ctx.substrate.root)
                            if target.is_relative_to(ctx.substrate.root)
                            else target),
            "verdict": verdict,
            "round_count": round_count,
            "body_chars": body_len,
            "violations": violations,
            "frontmatter_keys": sorted(fm.keys()) if fm else [],
        },
    )
