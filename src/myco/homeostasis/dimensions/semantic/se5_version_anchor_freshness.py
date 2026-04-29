"""SE5 — version-anchor freshness in live agent-facing docs (v0.7.2+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" — the v0.7.2 ratchet that catches
hardcoded version anchors before they accumulate to the v0.6.16 sweep
threshold (2747-line contract_changelog.md, 1632-line CHANGELOG.md,
27 pre-v0.6 LANDED crafts on the main reading surface).

The v0.6.16 sweep manually fixed dozens of stale ``v0.5.7`` /
``v0.6.12`` anchors. SE5 mechanizes detection so the next sweep's
candidate set is auto-surfaced rather than discovered via a 4-agent
parallel audit.

**Why a new dim, not SE2 extension** (correcting saprotroph T4):
saprotroph claimed SE2 already covers "canon-cited numbers and paths
match observed reality". Inspection shows ``SE2OrphanIntegrated``
actually checks orphan integrated notes — a different semantic. The
``homeostasis.md:143`` description is **stale doctrine** (likely from
the v0.5.8 25-dim era, where SE2 was a different check; the v0.6.0
expansion redefined SE2 without updating the table). v0.7.2 ships
SE5 as a genuinely-new check AND fixes the SE2 description in the
same molt.

**Live-doc scope (rhizomorph T3)**: SE5 scans ONLY:

- ``docs/architecture/**`` (L0/L1/L2/L3)
- ``MYCO.md``
- ``README*.md`` (3-language trilogy)
- ``_canon.yaml``
- ``pyproject.toml``

It explicitly EXCLUDES:

- ``docs/_archive/**`` and ``docs/contract_changelog/_archive/**``
  (frozen historical entries by design)
- ``docs/primordia/**`` (LANDED crafts and ``_landed/v0_X_x/`` are
  immutable history; their version anchors are correct for the era)
- ``docs/contract_changelog.md`` (current major's changelog; entries
  are time-stamped historical claims, not "live state")
- ``CHANGELOG.md`` (frozen since v0.5.9)
- ``notes/**`` (filenames embed timestamps + slugs that are legitimately
  immutable per L2 digestion.md no-delete rule)

**False-positive heuristic (mycorrhiza T7)**: a hardcoded
``v0.X.Y`` anchor preceded by historical-context tokens
(``shipped at``, ``landed in``, ``as of``, ``since``, ``pre-``,
``post-``, ``frozen at``, ``retired``, ``legacy``, ``v0.X.Y craft``)
is treated as a legitimate historical reference and NOT flagged.
Otherwise the anchor must be ≥ current version (forward-looking,
e.g. roadmap docs) or ≥ current minus 3 minor versions (recent-
enough to still describe live state).

Severity: LOW. Stale anchors are doctrine-hygiene, not a correctness
failure. The substrate continues to operate; the dim surfaces the
candidate set for the next neat-freak sweep.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["SE5VersionAnchorFreshness"]


# Live-doc scope (anchored relative paths from substrate root).
# Each entry: glob pattern. Order is irrelevant; the union is scanned.
_LIVE_DOC_GLOBS: tuple[str, ...] = (
    "docs/architecture/**/*.md",
    "MYCO.md",
    "README.md",
    "README_zh.md",
    "README_ja.md",
    "_canon.yaml",
    "pyproject.toml",
)

# Version anchor regex: matches v0.6.15, v0.7.0, v1.2.3, etc.
# Captures the (major, minor, patch) groups for comparison.
_VERSION_ANCHOR_RE = re.compile(r"\bv(\d+)\.(\d+)\.(\d+)\b")

# Historical-context tokens preceding a version anchor: presence
# within a small left-context window suppresses the finding.
_HISTORICAL_TOKENS = (
    "shipped at ",
    "shipped in ",
    "landed at ",
    "landed in ",
    "as of ",
    "since ",
    "pre-",
    "post-",
    "frozen at ",
    "retired at ",
    "retired in ",
    "legacy ",
    "deprecated at ",
    "deprecated in ",
    "introduced at ",
    "introduced in ",
    "added at ",
    "added in ",
    "removed at ",
    "removed in ",
    "fixed at ",
    "fixed in ",
    "v0.6.0 amendment",
    "v0.6.0 §",
    "per craft v",
    "predecessor: v",
    "schema v",  # "schema v2"
)

# Window of characters before the match to scan for historical tokens.
_HIST_WINDOW = 40


def _is_historical_context(line: str, match_start: int) -> bool:
    """Return True if the version anchor at match_start is preceded
    (within _HIST_WINDOW chars) by a historical-context token."""
    window_start = max(0, match_start - _HIST_WINDOW)
    left_context = line[window_start:match_start].lower()
    return any(tok in left_context for tok in _HISTORICAL_TOKENS)


def _parse_current_version(
    canon_extras: dict[str, object],
) -> tuple[int, int, int] | None:
    """Read the current __version__ from canon if available, else None."""
    cv = (
        canon_extras.get("contract_version") if isinstance(canon_extras, dict) else None
    )
    if isinstance(cv, str):
        m = _VERSION_ANCHOR_RE.search(cv)
        if m:
            return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return None


def _is_stale(
    anchor: tuple[int, int, int],
    current: tuple[int, int, int],
    *,
    minor_window: int = 3,
) -> bool:
    """Return True if the anchor is older than current minus minor_window
    minor versions (within the same major)."""
    a_maj, a_min, _ = anchor
    c_maj, c_min, _ = current
    if a_maj < c_maj:
        return True
    if a_maj > c_maj:
        return False  # forward-looking, not stale
    return (c_min - a_min) > minor_window


class SE5VersionAnchorFreshness(Dimension):
    """Hardcoded version anchors > 3 minor versions stale in live docs."""

    id = "SE5"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root

        # Determine current version. Prefer canon contract_version;
        # fall back to silent no-op if unavailable (fresh substrate).
        cv_raw = None
        # contract_version lives at top level of canon (not under .system).
        try:
            cv_raw = ctx.substrate.canon.contract_version
        except AttributeError:
            cv_raw = None
        current = None
        if isinstance(cv_raw, str):
            m = _VERSION_ANCHOR_RE.search(cv_raw)
            if m:
                current = (int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if current is None:
            return  # fresh substrate or missing canon — silent no-op

        seen_paths: set[str] = set()
        for pattern in _LIVE_DOC_GLOBS:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                rel_posix = path.relative_to(root).as_posix()
                if rel_posix in seen_paths:
                    continue
                seen_paths.add(rel_posix)

                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue

                for line_no, line in enumerate(text.splitlines(), start=1):
                    for m in _VERSION_ANCHOR_RE.finditer(line):
                        anchor = (
                            int(m.group(1)),
                            int(m.group(2)),
                            int(m.group(3)),
                        )
                        if not _is_stale(anchor, current):
                            continue
                        if _is_historical_context(line, m.start()):
                            continue
                        yield Finding(
                            dimension_id=self.id,
                            category=self.category,
                            severity=self.default_severity,
                            message=(
                                f"stale version anchor v{anchor[0]}.{anchor[1]}.{anchor[2]} "
                                f"at {rel_posix}:{line_no} (current "
                                f"v{current[0]}.{current[1]}.{current[2]}, "
                                f"window = ±3 minor versions). Add a "
                                f"historical-context token (shipped at / "
                                f"landed in / as of / since / pre-) or "
                                f"refresh the anchor to current."
                            ),
                            path=f"{rel_posix}:{line_no}",
                        )
