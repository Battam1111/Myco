"""LB-cluster — merged dimensions (LB1, LB2).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/semantic/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "LB1LivingBetsOverdue",
    "LB2LivingBetsRegime",
]


# =========================================================================
# LB1 — see module docstring + original git history at parent commits
# =========================================================================

# Substrate canon contract_version: ``v0.7.5`` → (0, 7, 5).
_CANON_VERSION_RE: re.Pattern[str] = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")

# Audit-doc filename: ``v0_7_5_living_bets_audit_2026-05-10.md`` or
# ``v0_6_0_living_bets_audit_craft_2026-04-28.md``. The leading
# ``vN_M_P_`` is the audited substrate version.
_AUDIT_FILENAME_RE: re.Pattern[str] = re.compile(
    r"^v(\d+)_(\d+)_(\d+)_.*living_bets_audit.*\.md$",
    re.IGNORECASE,
)

# The "Living Bets" concept landed at v0.5.6 per L0_VISION.md
# § "Appendix — Living bets (v0.5.6)". The first MAJOR ratchet that
# would have triggered an audit is v0.6.0 (the next MAJOR after
# v0.5.6). Any substrate at MAJOR < (0, 7) with no audit is silent
# because (a) v0.5.x predates the concept proper and (b) the v0.6.0
# audit was implicit inside the v0.6.0 unified-evolution craft, so
# fresh v0.6.x substrates that have not reified that audit into a
# standalone file should not be punished retroactively.
_LB_FIRST_ENFORCED_MAJOR: tuple[int, int] = (0, 7)


def _parse_canon_version(s: str) -> tuple[int, int, int] | None:
    """Parse a canon ``contract_version`` string into a ``(maj, min, patch)`` tuple.

    Returns ``None`` if the string does not match the
    ``v?N.M.P`` shape.
    """
    m = _CANON_VERSION_RE.match(s.strip())
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _parse_audit_filename(name: str) -> tuple[int, int, int] | None:
    """Parse a Living Bets audit filename into a ``(maj, min, patch)`` tuple.

    Returns ``None`` if the basename does not match the
    ``vN_M_P_..._living_bets_audit_...md`` shape.
    """
    m = _AUDIT_FILENAME_RE.match(name)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)))


def _find_most_recent_audit(
    primordia_root: Path,
) -> tuple[Path, tuple[int, int, int]] | None:
    """Walk ``docs/primordia/**`` for ``*living_bets_audit*.md`` and
    return the most-recent ``(path, (maj, min, patch))`` pair.

    "Most recent" is the lexicographic max by basename; given the
    ``vN_M_P_`` prefix this sorts as MAJOR.MINOR.PATCH for the
    realistic substrate domain (single-digit MAJOR/MINOR, ≤ two-digit
    PATCH). LB1 does not pretend to handle MINOR ≥ 10000 cleanly;
    Myco's L0 P3 covers that with a dedicated craft when it ever
    becomes relevant.

    Returns ``None`` if no matching file is found anywhere under
    ``primordia_root`` (including ``_landed/`` archive subtrees).
    """
    if not primordia_root.is_dir():
        return None
    candidates: list[tuple[Path, tuple[int, int, int]]] = []
    for path in primordia_root.rglob("*living_bets_audit*.md"):
        if not path.is_file():
            continue
        parsed = _parse_audit_filename(path.name)
        if parsed is None:
            continue
        candidates.append((path, parsed))
    if not candidates:
        return None
    # Lex-max by basename (the ``vN_M_P_`` prefix gives semantic order
    # within the realistic Myco domain).
    return max(candidates, key=lambda pair: pair[0].name)


def _major_lines_between(older: tuple[int, int], newer: tuple[int, int]) -> int:
    """Count MAJOR-line bumps between two ``(major, minor)`` keys.

    Per the Myco-MAJOR convention codified in ``L0_VISION.md``
    § "Appendix — Living bets" (review cadence "v0.6, v0.7, v1.0"),
    a MAJOR ratchet is **either** a first-digit bump (``v0.x → v1.0``)
    or a second-digit bump while the first is still ``0`` (``v0.6 →
    v0.7``).

    Examples:

    - ``older=(0, 7), newer=(0, 7)`` → 0 (same MAJOR-line)
    - ``older=(0, 7), newer=(0, 8)`` → 1 (one MAJOR ratchet)
    - ``older=(0, 7), newer=(0, 9)`` → 2
    - ``older=(0, 7), newer=(1, 0)`` → 3 (v0.7→v0.8→v0.9→v1.0)
    - ``older >= newer``             → 0

    The function does not pretend to model an unboundedly-deep version
    lattice; for the realistic Myco domain (single-digit MAJORs and
    small MINORs) this gives the intuitive "how many MAJOR ratchets
    happened" answer.
    """
    if newer <= older:
        return 0
    # In the v0.x regime, MINOR bumps ARE MAJOR ratchets; once we're
    # past v1.0, only first-digit bumps count. Compute the bump count
    # by walking the lattice in lexicographic order, which the v0.x
    # MAJOR-line convention treats as: for each (major, minor) step,
    # one ratchet.
    o_maj, o_min = older
    n_maj, n_min = newer
    if n_maj == o_maj == 0:
        return n_min - o_min
    if o_maj == 0 and n_maj >= 1:
        # Crossing v1.0 boundary: count v0.o_min→v0.o_min+1→…→v1.0
        # plus any v1.0→v1.1→… (first-digit bumps only).
        # We don't know exactly how many v0.* releases shipped before
        # v1.0; treat this as a single "to v1.0" ratchet plus
        # (n_maj - 1) ratchets for v1→v2→…
        return 1 + (n_maj - 1) + 0  # MINOR within v1.x+ doesn't ratchet
    # Past v1.0: only first-digit bumps count.
    return n_maj - o_maj


def _severity_for_lag(patch_lag: int) -> Severity:
    """Map "patch versions overdue past a MAJOR-line boundary" to severity.

    Mirrors PA6's within-dim escalation; the thresholds match the
    SH2/PA2 30-session pattern at appropriate scale for release cadence.

    - ``patch_lag >= 10`` → HIGH
    - ``patch_lag >= 5``  → MEDIUM
    - any other value     → LOW (boundary case: just-bumped MAJOR
                                  without yet-shipped audit)
    """
    if patch_lag >= 10:
        return Severity.HIGH
    if patch_lag >= 5:
        return Severity.MEDIUM
    return Severity.LOW


class LB1LivingBetsOverdue(Dimension):
    """L0 Living Bets re-audit overdue at MAJOR-release cadence."""

    id = "LB1"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Substrate version. Silent no-op on parse failure (fresh
        # substrate with no canon, malformed contract_version, etc.).
        canon_version_raw = ctx.substrate.canon.contract_version
        substrate = _parse_canon_version(str(canon_version_raw))
        if substrate is None:
            return
        s_maj, s_min, s_patch = substrate
        substrate_line = (s_maj, s_min)

        # v0.8.4 root-cleanup (2026-05-12): docs/ may be at root (legacy)
        # or .docs/ (Myco-self / v0.8.4+); resolve via paths.docs.
        primordia_root = ctx.substrate.paths.docs / "primordia"
        most_recent = _find_most_recent_audit(primordia_root)

        if most_recent is None:
            # No audit doc found. Silent for substrates predating the
            # first-enforced MAJOR-line; fires LOW for substrates at
            # or past it. Per the prompt:
            #
            #   "Fresh substrate (no audit) AND contract_version MAJOR
            #    is 0.7 or higher → LB1 fires LOW (audit is expected)."
            #
            # The fresh-substrate branch deliberately does NOT ramp:
            # it's a single "first time the cadence is enforced" IOU,
            # not an accumulated debt. Once an audit doc lands and a
            # subsequent MAJOR ships without a fresh audit, the ramp
            # branch below kicks in.
            if substrate_line < _LB_FIRST_ENFORCED_MAJOR:
                return
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.LOW,
                message=(
                    f"Living Bets audit missing: substrate at "
                    f"v{s_maj}.{s_min}.{s_patch} has no "
                    f"docs/primordia/v*_living_bets_audit_*.md craft. "
                    f"L0_VISION.md § 'Appendix — Living bets' mandates "
                    f"re-audit at every MAJOR release (v0.6, v0.7, "
                    f"v1.0, ...). Author a v{s_maj}_{s_min}_*_living_"
                    f"bets_audit_*.md craft to close the IOU."
                ),
                path="docs/primordia/",
            )
            return

        audit_path, audit_version = most_recent
        a_maj, a_min, a_patch = audit_version
        audit_line = (a_maj, a_min)

        # Audit covers the current MAJOR-line → silent. (Cadence is
        # per-MAJOR-line, not per-PATCH; any audit whose
        # ``(major, minor)`` matches the substrate's is live.)
        if audit_line == substrate_line:
            return

        # Audit covers a future MAJOR-line (e.g. forward-looking craft
        # for v1.0 on a v0.7 substrate). Treat as silent — the cadence
        # contract is satisfied because there IS a Living Bets audit
        # in the substrate's reading surface; emitting a finding here
        # would punish forward-thinking ops. Document this branch
        # explicitly so future readers don't regress it.
        if audit_line > substrate_line:
            return

        # Audit covers a strictly older MAJOR-line. Compute patch lag =
        # substrate PATCH + 10-per-MAJOR-line skipped (matching the
        # no-audit branch).
        major_lines_skipped = _major_lines_between(audit_line, substrate_line)
        # `_major_lines_between` returns the count of MAJOR-line bumps
        # between audit and substrate (1 for v0.7→v0.8). Subtract 1 so
        # the v0.8.0-with-v0.7-audit boundary case yields 0+0 = 0 lag.
        patch_lag = s_patch + 10 * max(0, major_lines_skipped - 1)
        severity = _severity_for_lag(patch_lag)

        rel_audit = audit_path.relative_to(ctx.substrate.root).as_posix()
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=severity,
            message=(
                f"Living Bets audit overdue: substrate at "
                f"v{s_maj}.{s_min}.{s_patch} but most-recent audit "
                f"({rel_audit}) covers v{a_maj}.{a_min}.{a_patch}. "
                f"L0_VISION.md § 'Appendix — Living bets' mandates "
                f"re-audit at every MAJOR release. {patch_lag} patch "
                f"version(s) past the v{a_maj}.{a_min} → v{s_maj}.{s_min} "
                f"MAJOR bump without a fresh audit. Author a "
                f"v{s_maj}_{s_min}_*_living_bets_audit_*.md craft."
            ),
            path="docs/primordia/",
        )


# =========================================================================
# LB2 — see module docstring + original git history at parent commits
# =========================================================================

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
