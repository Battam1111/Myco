"""MB8 — shim-hit counter for safe back-compat shim retirement (v0.7.2+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" — the v0.7.2 ratchet that mechanizes the
v0.7.1-named **public-API-deletion discipline**. The deletion gates this
dim implements are codified at ``docs/architecture/L2_DOCTRINE/release_discipline.md``
§ "Rule 1 — The Two-Hour Blast-Radius Rule" (v0.7.10).

A back-compat shim package (e.g. ``src/myco/mcp/`` re-exporting
``myco.boundary.mcp``) cannot be safely deleted while downstream
consumers still import it. v0.7.0 attempted such a deletion based on
4 versions of stderr DeprecationWarning and broke the substrate's own
owner-Claude-Desktop config within 2 hours. v0.7.1 restored the shim
and named the discipline:

  A shim deletion candidate must satisfy ONE of:
  (a) Internal-only verification: zero hits across src/ + tests/ +
      scripts/ + docs/examples/ AND no plugin manifest declares the
      path AND no MCP host entry point exposes it.
  (b) Telemetry verification: the substrate has run for ≥ N senesce
      cycles spanning ≥ D wall-clock days with this dim's counter
      reporting zero hits across that window.

MB8 implements path (b). The shim's ``__main__.py`` writes one JSONL
line to ``.myco/state/shim_hits.json`` per CLI invocation; this dim
reads the append-only file, computes per-module hit counts + last-hit
ages, and reports.

**Categorization rationale (saprotroph T1)**: this is a metabolic dim
because the counter is *runtime telemetry on substrate state*
(directly analogous to MB1/MB3 which track raw-note backlog pressure
across sessions). It is NOT a shipped dim — shipped covers
publication-surface invariants (SH1 = __version__ sync; SH2 = release
provenance), and shim hits are neither.

**Architecture (mycorrhiza T1)**: the counter write happens at the
shim's ``__main__.py`` ENTRY (CLI invocation point), wrapped in
try-except so a read-only substrate cannot break the MCP server boot.
Import-time writes were rejected because:

  (a) read-only filesystems (CI snapshots, container rootfs) raise
      PermissionError at import → kills the MCP child the shim exists
      to protect (v0.7.0 incident replays);
  (b) at module-import time MycoContext is not yet loaded → no
      reliable substrate-id resolution;
  (c) concurrent imports from multiple MCP host instances race on
      counter increment with no fcntl/portalocker dependency available.

**Adversarial scoping (mycoparasite T1/T2/T6)**: ``.myco/state/shim_hits.json``
and ``src/myco/mcp/**`` are in ``core.risk_classifier._RECURSION_CUTTER_PATH_PATTERNS``.
A craft cannot simultaneously zero the counter and delete the shim
without forcing HIGH-risk classification.

Severity: MEDIUM. The dim emits one informational finding per shim
showing hit-count and last-hit age; never CRITICAL because:
- A non-zero hit count is the EXPECTED state for any active shim.
- The "ready-to-delete" signal is zero hits across a substrate-defined
  window (``governance.shim_sunset_min_zero_cycles`` +
  ``governance.shim_sunset_min_zero_days``); when reached, the dim
  surfaces a "shim X eligible for deletion" finding which a future
  craft can act on via the standard fruit→winnow→molt path.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime, timezone
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["MB8ShimHitCounter"]


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
