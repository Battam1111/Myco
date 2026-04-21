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

Governing manifest: ``docs/architecture/L3_IMPLEMENTATION/command_manifest.md``
(governance-verbs section, v0.5 — per v0.5.0 craft §R13, no new L2
surface.md was created; governance-verbs content lives at L3).
Legacy reference: the pre-rewrite ``craft_protocol.md`` under
``legacy_v0_3/`` (body-schema lint, Round 3).
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from myco.core.context import MycoContext, Result
from myco.core.errors import ContractError, UsageError
from myco.core.io_atomic import bounded_read_text

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

#: Fraction of body lines that may match fruit-template signatures
#: before ``G6_template_boilerplate`` fires. v0.5.4 gate added after
#: dogfood observation #4: a freshly-fruited craft skeleton passed
#: G1-G5 with no content filled in, which defeats winnow's purpose
#: as a "did the agent actually do the craft work" signal.
#:
#: The threshold is 40%: a fresh skeleton is ~70% template signatures,
#: a modest craft that quotes a few template lines while filling in
#: real content stays below 40%.
_MAX_BOILERPLATE_FRACTION: float = 0.40

#: Fingerprint substrings the fruit template emits verbatim. A body
#: with many of these lines is a skeleton the agent has not filled
#: in. Patterns are listed as substrings (not exact lines) so minor
#: edits (whitespace, added punctuation) do not bypass the gate.
_BOILERPLATE_MARKERS: tuple[str, ...] = (
    # L0/contract-sketch placeholders
    "TBD (L0",
    "TBD (files",
    "TBD (L0 principles",
    # Direct "fill in" prompts
    "(Fill in.)",
    "(Fill in",
    "(Brief bullets on what surfaced",
    "(tension)",
    "(addresses T",
    # Round-skeleton lists the template plants verbatim
    "- **T1**: (tension)",
    "- **T2**: (tension)",
    "- **T3**: (tension)",
    "- **R1** (addresses T1):",
    "- **R2** (addresses T2):",
    "- **R3** (addresses T3):",
    "- **F1**:",
    "- **F2**:",
    "- **F3**:",
    # Distinctive instructional prose the template ships
    "State the initial proposal clearly. What is being changed",
    "List the strongest tensions against the claim. Number them",
    "Answer each tension. Key each response with R1/R2/R3",
    "Run a second adversarial pass. Do any revisions introduce",
    "Final synthesis. Which revisions are accepted? Which are",
    "### What this craft revealed",
    "(file) — what lands, where.",
    "(test) — what proves it lands correctly.",
    "(doctrine) — what L0/L1/L2/L3 edits ride with this craft.",
    "(pytest) — passing command(s).",
    "(behavioral) — agent-observable changes that must hold.",
    "(non-regression) — what must NOT break.",
)


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
_ROUND_MARKER_FALLBACK_RE = re.compile(r"^##\s+Round\s+\d+(?:\.\d+)?", re.MULTILINE)


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
    body = text[match.end() :]

    import yaml

    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError as exc:
        raise ContractError(f"evolve: frontmatter is not valid YAML: {exc}") from exc
    if not isinstance(fm, dict):
        raise ContractError("evolve: frontmatter top-level must be a YAML mapping")
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
    return [positions[i + 1] - positions[i] for i in range(len(positions) - 1)]


def run(args: Mapping[str, object], *, ctx: MycoContext) -> Result:
    """Manifest handler: gate-check a craft proposal's shape.

    Reads ``args["proposal"]`` (a path), verifies the three-round
    markers exist + status advanced appropriately, and returns a
    Result whose ``exit_code`` is non-zero on shape violations.
    """
    raw_path = args.get("proposal")
    if not raw_path:
        raise UsageError("evolve: --proposal <path> is required")
    target = Path(str(raw_path))
    if not target.is_absolute():
        target = ctx.substrate.root / target
    if not target.is_file():
        raise UsageError(f"evolve: proposal file not found: {target}")

    try:
        text = bounded_read_text(target)
    except OSError as exc:
        raise ContractError(f"evolve: cannot read proposal: {exc}") from exc

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

    # Gate G6 — body is not mostly template boilerplate (v0.5.4).
    # Counts lines that match any ``_BOILERPLATE_MARKERS`` token; if
    # the ratio exceeds ``_MAX_BOILERPLATE_FRACTION``, the proposal
    # is flagged as "fruit skeleton, not filled in yet". Guards the
    # v0.5.4 dogfood finding where a fresh fruit-template doc passed
    # G1-G5 by construction.
    body_lines = [ln for ln in body.splitlines() if ln.strip()]
    if body_lines:
        boilerplate_lines = sum(
            1
            for ln in body_lines
            if any(marker in ln for marker in _BOILERPLATE_MARKERS)
        )
        fraction = boilerplate_lines / len(body_lines)
        if fraction > _MAX_BOILERPLATE_FRACTION:
            violations.append(
                {
                    "gate": "G6_template_boilerplate",
                    "message": (
                        f"proposal body is {fraction:.0%} template "
                        f"boilerplate (threshold "
                        f"{_MAX_BOILERPLATE_FRACTION:.0%}); the "
                        f"agent has not filled in the craft sections."
                    ),
                }
            )

    # Gate G5 — every round body segment clears the per-round floor.
    per_round = _round_body_lengths(body)
    if per_round:
        short_rounds = [
            i + 1
            for i, length in enumerate(per_round)
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
            "proposal": str(
                target.relative_to(ctx.substrate.root)
                if target.is_relative_to(ctx.substrate.root)
                else target
            ),
            "verdict": verdict,
            "round_count": round_count,
            "body_chars": body_len,
            "violations": violations,
            "frontmatter_keys": sorted(fm.keys()) if fm else [],
        },
    )
