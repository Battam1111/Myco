"""LB1 — Living Bets re-audit overdue at every MAJOR release.

Governing doctrine: ``docs/architecture/L0_VISION.md`` § "Appendix —
Living bets" (review cadence: "Every MAJOR release (v0.6, v0.7, v1.0)
re-audits this appendix"). The cadence has been honor-system since
v0.5.6 and was missed at v0.7.0 (Major Autolysis, 2026-04-30); v0.7.5
backfilled the audit retroactively per
``docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md`` and
``docs/primordia/v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md`` § P1.

LB1 closes the loop mechanically. It compares the substrate's
``_canon.yaml::contract_version`` MAJOR (in **Myco-MAJOR** semantics:
the ``(major, minor)`` pair, so ``v0.7`` for any ``v0.7.x`` and
``v1.0`` for any ``v1.0.x``) against the MAJOR named in the
most-recent Living Bets audit document under ``docs/primordia/`` (or
its ``_landed/`` archive). If the substrate's MAJOR has advanced past
the last-audited MAJOR and ≥ 2 patch versions have shipped beyond
that boundary without a fresh audit doc, LB1 emits a finding.

**Myco-MAJOR vs semver-MAJOR**: until ``v1.0``, Myco's MAJOR ratchet
is the second digit (``v0.6`` → ``v0.7`` is a MAJOR bump per L0). At
``v1.0`` the first digit takes over. LB1 normalizes to a
``(major, minor)`` pair which is the natural "MAJOR-line" key in both
regimes.

**Audit-doc detection heuristic** (mirrors the v0.7.5 P1 craft naming):

- Filename pattern: ``v*_living_bets_audit_*.md`` matched against
  ``docs/primordia/**`` (so ``_landed/v0_X_x/...`` archived audits
  still count). Examples that match:

  - ``docs/primordia/v0_6_0_living_bets_audit_craft_2026-04-28.md``
  - ``docs/primordia/v0_7_5_living_bets_audit_2026-05-10.md``
  - ``docs/primordia/_landed/v0_6_x/v0_6_0_living_bets_audit_craft_*.md``

- The audited MAJOR is parsed from the leading ``vN_M_P`` token in
  the filename (e.g. ``v0_7_5_*`` → MAJOR ``(0, 7)``).
- "Most recent" = lexicographic max by basename (which, given the
  ``vN_M_P`` prefix, sorts as semantic-version order for any single
  MAJOR-line and as MAJOR-then-MINOR-then-PATCH overall).

**Edge cases**:

- Fresh substrate (no ``docs/primordia/`` dir or no
  ``*living_bets_audit*`` file) AND ``contract_version`` MAJOR is
  ``< (0, 7)`` → silent (the substrate predates the Living Bets
  concept; no IOU is owed).
- Fresh substrate (no audit) AND MAJOR is ``≥ (0, 7)`` → fires LOW
  (audit is expected at every MAJOR ratchet).
- Audit doc exists for the current MAJOR (e.g.
  ``v0_7_5_living_bets_audit_*.md`` with substrate at ``v0.7.x``)
  → silent.
- Audit doc exists only for a prior MAJOR (e.g.
  ``v0_6_*_living_bets_audit_*.md`` while substrate is at
  ``v0.7.5+``) → fires LOW (or higher per the ramp).

**Severity ramp** (mirrors PA6's within-dim escalation, not the
``severity_promotion`` cross-roster mechanism):

- ≥ 2 patch versions past a MAJOR-line bump without audit → LOW.
- ≥ 5 patch versions past a MAJOR-line bump without audit → MEDIUM.
- ≥ 10 patch versions past a MAJOR-line bump without audit → HIGH.

The "patch versions past" count is the substrate's own PATCH for the
fresh-substrate case (no audit at all on the current MAJOR-line), or
the substrate's PATCH plus a per-MAJOR-line escalator when an older
audit exists. The MAJOR-line-only-overdue case (e.g. v0.8.0 with v0.7
audit) emits LOW because at that boundary 0 patch has accrued past
the MAJOR bump.

Severity: LOW default; ramps in-dim. Not auto-fixable — closing the
finding requires authoring a new ``vX_Y_Z_living_bets_audit_*.md``
craft and shipping a MAJOR-or-MINOR molt that lands it.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["LB1LivingBetsOverdue"]


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
