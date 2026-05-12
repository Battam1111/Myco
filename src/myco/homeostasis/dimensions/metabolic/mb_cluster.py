"""MB-cluster — merged dimensions (MB1, MB2, MB3, MB4, MB6, MB8).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/metabolic/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import datetime as dt
import json
import re
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import Any, ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "MB1RawNotesBacklog",
    "MB2NoIntegratedYet",
    "MB3RawNotesHighWatermark",
    "MB4SporulatedReabsorbed",
    "MB6StaleDraftOrDistilled",
    "MB8ShimHitCounter",
]


# =========================================================================
# MB1 — see module docstring + original git history at parent commits
# =========================================================================

_BACKLOG_MEDIUM_THRESHOLD = 10


class MB1RawNotesBacklog(Dimension):
    """``notes/raw/`` backlog; >10 files is MEDIUM, 1-10 is LOW."""

    id = "MB1"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM

    #: v0.5.5 — MB1 delegates to :func:`myco.digestion.assimilate.reflect`
    #: to drain the raw-notes backlog in place. See :meth:`fix`.
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        raw_dir = ctx.substrate.paths.notes / "raw"
        if not raw_dir.is_dir():
            return
        raws = [p for p in raw_dir.glob("*.md") if p.is_file()]
        n = len(raws)
        if n == 0:
            return
        if n > _BACKLOG_MEDIUM_THRESHOLD:
            severity = Severity.MEDIUM
            msg = (
                f"{n} raw notes in notes/raw/ (over threshold "
                f"{_BACKLOG_MEDIUM_THRESHOLD}); run `myco assimilate`"
            )
        else:
            severity = Severity.LOW
            msg = f"{n} raw note(s) in notes/raw/ pending digest"
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=severity,
            message=msg,
            path="notes/raw",
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Bulk-promote raw notes by calling ``reflect`` in-process.

        Narrow contract (v0.5.5):

        - Does **not** shell out to ``myco reflect`` — calls the
          Python API directly so the fix is deterministic and can
          surface per-note errors without scraping stdout.
        - Promotes whatever ``reflect`` decides to promote; this
          dimension does not second-guess the pipeline.
        - Reports back promoted / already-integrated / error counts
          in the fix entry (exposed via ``**outcome`` extras in
          :func:`myco.homeostasis.kernel._apply_fix`).
        - ``applied`` is True iff at least one note was promoted.
          An empty raw dir (should be impossible if MB1 fired, but
          harmless) or an all-errors run reports ``applied=False``.
        """
        # Imported here rather than at module top-level to keep
        # ``myco.homeostasis.dimensions`` importable before the
        # digestion subsystem has loaded (and to keep the dimension
        # module cheap for ``myco immune --list``).
        from myco.digestion.cluster import reflect

        summary = reflect(ctx=ctx)
        # reflect() returns a ``dict[str, object]`` shape; narrow the
        # int-valued keys via an isinstance guard so mypy is happy and
        # stray non-int values (shouldn't happen, belt + suspenders)
        # degrade to 0 instead of raising.
        _promoted = summary.get("promoted", 0)
        promoted = _promoted if isinstance(_promoted, int) else 0
        _already = summary.get("already_integrated", 0)
        already = _already if isinstance(_already, int) else 0
        errors = summary.get("errors") or []
        err_count = len(errors) if isinstance(errors, list) else 0

        if promoted > 0:
            detail = f"assimilated {promoted} raw note(s)" + (
                f" ({already} already-integrated, {err_count} error(s))"
                if (already or err_count)
                else ""
            )
            return {
                "applied": True,
                "detail": detail,
                "promoted": promoted,
                "already_integrated": already,
                "errors": err_count,
            }

        # Nothing promoted — either the queue was empty by the time we
        # got here (unlikely race), or every candidate errored. Either
        # way, not counted as an applied fix.
        detail = (
            f"no notes promoted ({already} already-integrated, {err_count} error(s))"
        )
        return {
            "applied": False,
            "detail": detail,
            "promoted": 0,
            "already_integrated": already,
            "errors": err_count,
        }


# =========================================================================
# MB2 — see module docstring + original git history at parent commits
# =========================================================================


class MB2NoIntegratedYet(Dimension):
    """Raw notes exist but ``notes/integrated/`` is empty."""

    id = "MB2"
    category = Category.METABOLIC
    default_severity = Severity.LOW

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        notes = ctx.substrate.paths.notes
        raw_dir = notes / "raw"
        integrated_dir = notes / "integrated"
        if not raw_dir.is_dir():
            return
        raws = [p for p in raw_dir.glob("*.md") if p.is_file()]
        if not raws:
            return
        integrated = (
            [p for p in integrated_dir.glob("*.md") if p.is_file()]
            if integrated_dir.is_dir()
            else []
        )
        if integrated:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"{len(raws)} raw note(s) present but notes/integrated/ "
                f"is empty; `myco digest` or `myco assimilate` to promote"
            ),
            path="notes/integrated",
        )


# =========================================================================
# MB3 — see module docstring + original git history at parent commits
# =========================================================================

#: Absolute ceiling on raw-notes backlog before MB3 fires HIGH.
#: Tuned to match the 500-item MCP context budget: a raw-note list
#: approaching this size swamps an ``eat --path`` preview or a
#: ``sense`` query.
_HIGH_WATERMARK: int = 50


class MB3RawNotesHighWatermark(Dimension):
    """Raw-notes backlog over the high watermark (default 50)."""

    id = "MB3"
    category = Category.METABOLIC
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        raw_dir = ctx.substrate.paths.notes / "raw"
        if not raw_dir.is_dir():
            return
        count = sum(1 for _ in raw_dir.glob("*.md"))
        if count < _HIGH_WATERMARK:
            return
        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=self.default_severity,
            message=(
                f"{count} raw notes in notes/raw/ (over high watermark "
                f"{_HIGH_WATERMARK}); backlog at this size makes "
                f"`sense` and `eat --path` previews unusable. Run "
                f"`myco assimilate` immediately."
            ),
            path="notes/raw",
            fixable=True,
        )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        """Bulk-promote raw notes via the shared ``reflect`` helper."""
        _ = finding
        from myco.digestion.cluster import reflect

        summary = reflect(ctx=ctx)
        _promoted = summary.get("promoted", 0)
        promoted = _promoted if isinstance(_promoted, int) else 0
        errors = summary.get("errors") or []
        err_count = len(errors) if isinstance(errors, list) else 0
        if promoted > 0:
            return {
                "applied": True,
                "detail": (
                    f"assimilated {promoted} raw note(s) ({err_count} error(s))"
                ),
                "promoted": promoted,
                "errors": err_count,
            }
        return {
            "applied": False,
            "detail": f"no notes promoted ({err_count} error(s))",
            "promoted": 0,
            "errors": err_count,
        }


# =========================================================================
# MB4 — see module docstring + original git history at parent commits
# =========================================================================

_FRONTMATTER_RE: re.Pattern[str] = re.compile(r"^---\s*\n(.*?)\n---", re.DOTALL)
_STAGE_RE: re.Pattern[str] = re.compile(r"^stage:\s*sporulated\s*$", re.MULTILINE)
_PROP_RE: re.Pattern[str] = re.compile(
    r"^propagated_doctrine:\s*(.+?)\s*$", re.MULTILINE
)


class MB4SporulatedReabsorbed(Dimension):
    """sporulated distilled notes must reference a real doctrine doc."""

    id = "MB4"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # v0.8.5 — canon-configurable notes_dir (Myco-self uses .myco/notes/).
        distilled_root = ctx.substrate.paths.notes / "distilled"
        if not distilled_root.is_dir():
            return
        for path in distilled_root.glob("*.md"):
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fm_match = _FRONTMATTER_RE.search(text)
            if not fm_match:
                continue
            fm = fm_match.group(1)
            if not _STAGE_RE.search(fm):
                continue  # not sporulated
            prop_match = _PROP_RE.search(fm)
            rel = path.relative_to(ctx.substrate.root).as_posix()
            if not prop_match:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        "distilled note marked stage=sporulated has no "
                        "propagated_doctrine: <docpath> frontmatter field"
                    ),
                    path=rel,
                )
                continue
            doctrine_path = prop_match.group(1).strip().strip("\"'")
            if not (ctx.substrate.root / doctrine_path).is_file():
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"propagated_doctrine target {doctrine_path!r} "
                        f"does not exist on disk"
                    ),
                    path=rel,
                )


# =========================================================================
# MB6 — see module docstring + original git history at parent commits
# =========================================================================

_STATUS_DRAFT_RE: re.Pattern[str] = re.compile(r"^status:\s*DRAFT\s*$", re.MULTILINE)
_DATE_RE: re.Pattern[str] = re.compile(
    r"^date:\s*([0-9]{4}-[0-9]{2}-[0-9]{2})\s*$", re.MULTILINE
)


class MB6StaleDraftOrDistilled(Dimension):
    """DRAFT crafts / distilled notes must not stagnate beyond thresholds."""

    id = "MB6"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        thresholds = (ctx.substrate.canon.lint or {}).get("thresholds") or {}
        warn_days = int(thresholds.get("stale_draft_warn_days", 14))
        # v0.8.5 — canon-configurable docs_dir (Myco-self uses .docs/).
        primordia_root = ctx.substrate.paths.docs / "primordia"
        today = ctx.now.date() if hasattr(ctx.now, "date") else dt.date.today()
        if primordia_root.is_dir():
            for path in primordia_root.glob("*_craft_*.md"):
                if "_excreted" in path.parts:
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                fm_match = _FRONTMATTER_RE.search(text)
                if not fm_match:
                    continue
                fm = fm_match.group(1)
                if not _STATUS_DRAFT_RE.search(fm):
                    continue
                date_match = _DATE_RE.search(fm)
                if not date_match:
                    continue
                try:
                    craft_date = dt.date.fromisoformat(date_match.group(1))
                except ValueError:
                    continue
                age_days = (today - craft_date).days
                if age_days >= warn_days:
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"DRAFT craft {age_days} days old (threshold "
                            f"{warn_days}); land via winnow or excrete"
                        ),
                        path=rel,
                    )

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, Any]:
        # v0.6.0 lands MB6 as fixable but the auto-excrete path is
        # deferred to v0.6.x patches — auto-excretion of crafts is
        # destructive and merits an additional review cycle. v0.6.0
        # only emits findings; agent / owner manually winnows or
        # excretes.
        return {
            "applied": False,
            "detail": (
                "MB6 fix at v0.6.0 is informational only; "
                "auto-excrete deferred to v0.6.x"
            ),
        }


# =========================================================================
# MB8 — see module docstring + original git history at parent commits
# =========================================================================


def _parse_iso(ts: str) -> datetime | None:
    """Parse an ISO-8601 timestamp; return None on malformed input."""
    try:
        # Python 3.11+ understands "Z" suffix natively; older versions need replace.
        return datetime.fromisoformat(ts.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


class MB8ShimHitCounter(Dimension):
    """Report shim-hit telemetry from ``.myco/state/shim_hits.json``."""

    id = "MB8"
    category = Category.METABOLIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Append-only JSONL; one line per shim invocation. Missing file
        # = fresh substrate, zero hits observed → silent no-op (mycorrhiza T2).
        hits_path = ctx.substrate.root / ".myco/state" / "shim_hits.json"
        if not hits_path.is_file():
            return

        try:
            text = hits_path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return

        # Parse JSONL: one record per line. Skip malformed lines silently
        # (telemetry is best-effort).
        # Per-module slot: (count, first_ts, last_ts). Tuple unpacking
        # gives mypy concrete types instead of dict[str, object].
        counts: dict[str, int] = {}
        first_ts: dict[str, str] = {}
        last_ts: dict[str, str] = {}
        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(rec, dict):
                continue
            module = rec.get("module")
            ts = rec.get("ts")
            if not isinstance(module, str) or not isinstance(ts, str):
                continue
            counts[module] = counts.get(module, 0) + 1
            # Track first + last by lexicographic ISO-8601 ordering (works for UTC).
            if module not in first_ts or ts < first_ts[module]:
                first_ts[module] = ts
            if module not in last_ts or ts > last_ts[module]:
                last_ts[module] = ts

        if not counts:
            return

        # Read sunset thresholds from canon governance (additive within
        # schema v2; absent → defaults).
        gov = (ctx.substrate.canon.system or {}).get("governance") or {}
        if not isinstance(gov, dict):
            gov = {}
        min_cycles = int(gov.get("shim_sunset_min_zero_cycles", 7) or 7)
        min_days = int(gov.get("shim_sunset_min_zero_days", 7) or 7)

        now = datetime.now(timezone.utc)
        for module in sorted(counts):
            count = counts[module]
            module_last_ts = last_ts[module]
            last_dt = _parse_iso(module_last_ts)
            age_days = (now - last_dt).days if last_dt else 0
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"shim {module!r} has been invoked {count} time(s); "
                    f"last hit {age_days}d ago at {module_last_ts}. "
                    f"Sunset gate: ≥ {min_cycles} senesce cycles + "
                    f"≥ {min_days} days with zero hits before deletion is "
                    f"safe per v0.7.1 discipline."
                ),
                path=".myco/state/shim_hits.json",
            )
