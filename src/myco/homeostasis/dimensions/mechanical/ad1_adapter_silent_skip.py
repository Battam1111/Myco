"""AD1 — adapter silent-skip pattern detection.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
(L0 P2 永恒吞噬 = "missing a signal costs more than eating one too
many"; craft v0.6.0 §F22 / Round 2 T17).

Adapters in ``src/myco/ingestion/adapters/`` historically returned
``[]`` on failure (PDF size cap, HTML parse error, OSError). This
silent-skip violates P2 because the user cannot tell if a 7MB PDF
was successfully ingested-as-empty or silently failed.

v0.6.0 reshaped adapters to return ``IngestResult(... status="failed",
failure_reason=...)`` stub instead. AD1 watches for regressions:
literal ``return []`` patterns inside adapter ``ingest()`` methods.

Severity: LOW at land, ramps to HIGH after 30 sessions.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["AD1AdapterSilentSkip"]

#: Match `return []` (with optional whitespace).
_SILENT_SKIP_RE: re.Pattern[str] = re.compile(r"\breturn\s*\[\s*\]")


class AD1AdapterSilentSkip(Dimension):
    """Adapter modules must not silently return [] on failure."""

    id = "AD1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        adapters_root = ctx.substrate.root / "src" / "myco" / "ingestion" / "adapters"
        if not adapters_root.is_dir():
            return
        for path in adapters_root.glob("*.py"):
            if path.name == "__init__.py" or path.name == "protocol.py":
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for ln_num, line in enumerate(lines, 1):
                # Skip comments + docstrings approximation.
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if _SILENT_SKIP_RE.search(line):
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"adapter silent-skip pattern `return []` at "
                            f"line {ln_num}; return failed-stub "
                            f"IngestResult instead (L0 P2)"
                        ),
                        path=rel,
                    )
