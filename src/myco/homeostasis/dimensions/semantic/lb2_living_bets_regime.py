"""LB2 — Living Bets observed-regime classifier (v0.8.0+).

Governing doctrine: ``docs/architecture/L0_VISION.md`` § "Appendix —
Living bets" as amended at v0.8.0 per
``docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md``. The
v0.8.0 amendment ratifies Option B (persistence-budget refinement)
from the v0.7.5 Living Bets re-audit and names the **two regimes**
the wager applies to explicitly:

- **Bet wins in**: multi-session / multi-host / federated work where
  the substrate's persistence budget exceeds any single Agent's read
  window.
- **Bet loses in**: ephemeral single-session work where one Agent
  can hold the entire problem in context.

LB1 (shipped v0.7.5) tracks the *cadence* of the periodic re-audit
ritual. LB2 tracks the *substantive* regime classification: it
collects three observable signals from the substrate, classifies the
observed work pattern along the bet/lose axis, and emits a finding
only when the substrate appears to sit in the regime where the bet
**loses** — at which point the agent should explicitly re-decide
whether the substrate is worth keeping (raise persistence budget) or
should be released (delete).

**Three observable signals**:

1. ``session_count`` — total distinct ``session_id`` values ever
   recorded in ``.myco/state/`` JSONL files (currently
   ``shim_hits.json``; future state files that carry a
   ``session_id`` field on each line are picked up automatically by
   the ``_iter_session_ids`` walker). Proxy: "how many distinct
   sessions has this substrate served?". Read with bounded
   line-by-line streaming; never slurps the whole file when only
   distinct session_id values are needed.
2. ``host_count`` — number of host adapters that have evidence of
   write/install activity for this substrate. v0.8.0 MVP heuristic:
   ``1`` (this substrate at least has its own host running it). A
   future extension can plumb richer evidence from
   ``boundary/host_integration/<host>.py::install_basic`` telemetry,
   if/when ``.myco/state/host_install.json`` is introduced.
3. ``peer_count`` — ``len(canon.identity.federation_peers)``. Direct
   reading of the L0 P5 federation field.

**Regime classification**:

- ``peer_count >= 1`` OR ``session_count >= 50``
  → **multi-session/host/federated** (bet-winning regime). Silent.
- ``session_count < 5`` AND ``peer_count == 0``
  → **ephemeral-single-session** (bet-losing regime). Emits LOW
  finding pointing at the explicit decision to make.
- Otherwise (``5 <= session_count < 50`` AND ``peer_count == 0``)
  → **transitional**. Silent (no hard signal in either direction).

**Defensive posture**: any signal that cannot be computed (missing
file, parse error, malformed canon section) silently falls back to
the "transitional" branch and emits no finding. LB2 never raises;
the dim's job is to surface a well-evidenced bet-losing signal, not
to second-guess substrate state when state is itself missing.

Severity: LOW (prompt-shaped — the bet-losing regime is a question
for the agent, not an error). Not auto-fixable: closing the finding
requires either (a) the substrate accruing more sessions/peers, (b)
the agent explicitly raising the persistence budget by federating,
or (c) deletion. None of those are mechanical in-substrate fixes.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["LB2LivingBetsRegime"]


# Threshold gates for the regime classification. Numbers come from
# the v0.8.0 amendment's Round 1.5 calibration (T4 / saprotroph):
# substrate growth + verb usage + cross-reference rates are the
# evidence ladder. We approximate "growth" with session_count, since
# every distinct session is one independent piece of evidence the
# substrate is being persisted across read-windows.
_BET_WINNING_SESSION_THRESHOLD: int = 50
_BET_LOSING_SESSION_THRESHOLD: int = 5


def _iter_session_ids(state_dir: Path) -> Iterable[str]:
    """Yield every ``session_id`` value from JSONL files under ``state_dir``.

    Walks files matching ``*.json`` (which by Myco convention are
    JSONL — one record per line under ``.myco/state/``) and yields
    each record's ``session_id`` field when it parses as a non-empty
    string. Malformed lines, files that fail to open, and files
    whose records lack ``session_id`` are skipped silently — this is
    a best-effort signal collector, not a validator.

    Bounded by line-by-line streaming so a multi-GB telemetry file
    does not balloon memory. Callers de-dup the yielded ids
    themselves (which lets them stop early if needed).
    """
    if not state_dir.is_dir():
        return
    for path in sorted(state_dir.glob("*.json")):
        if not path.is_file():
            continue
        try:
            handle = path.open("r", encoding="utf-8")
        except OSError:
            continue
        with handle as f:
            for raw in f:
                line = raw.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(rec, dict):
                    continue
                sid = rec.get("session_id")
                if isinstance(sid, str) and sid:
                    yield sid


def _compute_session_count(state_dir: Path) -> int:
    """Count distinct ``session_id`` values across ``.myco/state/`` JSONL.

    Returns ``0`` on any failure (missing dir, unreadable files,
    empty corpus). Never raises.
    """
    try:
        return len(set(_iter_session_ids(state_dir)))
    except Exception:
        # Belt-and-suspenders: ``_iter_session_ids`` already swallows
        # individual OS/parse failures, but a pathological path
        # (e.g. permissions error on glob itself) should still leave
        # LB2 silent rather than crashing the immune kernel.
        return 0


def _compute_peer_count(canon_identity: object) -> int:
    """Read ``identity.federation_peers`` length defensively.

    Returns ``0`` if the field is absent, not a list, or otherwise
    unreadable. Never raises.
    """
    if not isinstance(canon_identity, dict):
        return 0
    peers = canon_identity.get("federation_peers")
    if not isinstance(peers, list):
        return 0
    return len(peers)


def _compute_host_count(_state_dir: Path) -> int:
    """v0.8.0 MVP: at least one host (the one running this immune pass).

    The prompt-stated default for v0.8.0: ``1`` because the substrate
    at least has its own host running it. A richer signal would
    probe ``.myco/state/host_install.json`` if it exists; we leave
    the seam (the ``_state_dir`` argument is reserved for that
    future plumbing) but do not depend on its presence today.
    """
    return 1


class LB2LivingBetsRegime(Dimension):
    """L0 Living Bets observed-regime classifier (v0.8.0 amendment)."""

    id = "LB2"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # All three signals are computed defensively; any failure
        # collapses the substrate into the transitional regime
        # (silent), per the dim's "never punish missing evidence"
        # contract.
        state_dir = ctx.substrate.root / ".myco/state"
        session_count = _compute_session_count(state_dir)
        host_count = _compute_host_count(state_dir)  # noqa: F841 — reserved for future plumbing
        peer_count = _compute_peer_count(ctx.substrate.canon.identity)

        # Bet-winning regime: federated OR enough sessions accrued.
        if peer_count >= 1 or session_count >= _BET_WINNING_SESSION_THRESHOLD:
            return

        # Bet-losing regime: ephemeral single-session pattern with no
        # federation evidence. Emit LOW finding asking the agent to
        # re-decide.
        if session_count < _BET_LOSING_SESSION_THRESHOLD and peer_count == 0:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"substrate appears ephemeral "
                    f"(session_count={session_count} < "
                    f"{_BET_LOSING_SESSION_THRESHOLD}, peer_count=0); "
                    f"L0 Living Bets wager is in its losing regime per "
                    f"v0.8.0 amendment. Decide explicitly: is this a "
                    f"substrate that should persist (raise persistence "
                    f"budget — federate, accrue sessions) or be deleted "
                    f"(release the resources)?"
                ),
                path="_canon.yaml",
            )
            return

        # Transitional regime: between the two thresholds. Silent —
        # no hard signal either way.
        return
