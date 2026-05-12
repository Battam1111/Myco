"""PA6 — repo-bloat detector against canon-declared threshold (v0.7.2+).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "永恒删减 (eternal pruning)" — the v0.7.2 ratchet that catches
accumulated working-tree weight before it reaches the v0.7.0
incident's "11 MB legacy_v0_3 hidden 4 fail-silent dims" threshold.

**Categorization rationale (saprotroph T2)**: this is a mechanical dim
because repo size in bytes is a filesystem invariant (analogous to
PA1's write_surface coverage check). It is NOT metabolic — metabolic
covers agent-throughput pressure (raw-note backlog, sporulation
queue depth), not byte-size of the substrate's own git working tree.

**Exclusion-list discipline (rhizomorph T1, mycorrhiza T3)**:

- Filesystem-level skips use ``myco.core.skip_dirs.should_skip_path``
  (the v0.5.8-consolidated canonical skip list — covers .git/, dist/,
  __pycache__/, .myco/state/, etc.). Walkers that re-implement an
  inline list diverge over time.
- Substrate-level skips read ``canon.metrics.repo_size_excluded``
  (new at v0.7.2; defaults to ``["notes/**", "docs/primordia/_landed/**",
  "docs/_archive/**"]`` if absent). This protects L0 P2 (永恒吞噬):
  the substrate's own ingestion targets (notes/) and immutable history
  (_landed/ + _archive/) are NOT counted against the bloat threshold.
  Otherwise the substrate's ingestion is its own bloat-cause —
  adversarial.

**Resolution path (chytrid T3)**: when the threshold is breached, the
agent resolves AUTONOMOUSLY via the standard ``fruit → winnow →
molt`` cycle (or directly via ``myco excrete`` for raw notes). PA6
finding does NOT participate in ``exit_policy: mechanical:critical``
under any future amendment — bloat-shedding stays agent-driven, not
owner-merge-gated. L0 P1 ("Only For Agent") is preserved.

**Threshold semantics**: ``canon.metrics.repo_size_max_bytes`` (new
field; defaults to 50 MB if absent — generous starting cap for
typical Myco substrates). Behaviour:

- ≥ 80% of threshold → MEDIUM finding "approaching bloat threshold".
- ≥ 100% of threshold → HIGH finding "exceeded bloat threshold".

Severity ramps within the dim itself (not promoted across the
roster). Default declared severity is MEDIUM; HIGH emits only when
threshold is fully exceeded.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Iterable
from typing import ClassVar

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.core.skip_dirs import should_skip_path
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = ["PA6RepoBloat"]


_DEFAULT_THRESHOLD_BYTES = 50 * 1024 * 1024  # 50 MB
_DEFAULT_EXCLUDED_GLOBS = (
    "notes/**",
    "docs/primordia/_landed/**",
    "docs/_archive/**",
    "docs/contract_changelog/_archive/**",
)


def _matches_any_glob(rel_posix: str, patterns: tuple[str, ...]) -> bool:
    """Return True if rel_posix matches any of the substrate-level
    exclusion glob patterns (``**`` semantics)."""
    for pat in patterns:
        # fnmatch doesn't natively understand **; expand to a 2-pass
        # match: ``a/**`` matches ``a/x``, ``a/x/y``, etc.
        if pat.endswith("/**"):
            prefix = pat[:-3]  # drop "/**"
            if rel_posix == prefix or rel_posix.startswith(prefix + "/"):
                return True
        elif fnmatch.fnmatchcase(rel_posix, pat):
            return True
    return False


class PA6RepoBloat(Dimension):
    """Repo-size bloat against canon-declared threshold."""

    id = "PA6"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        metrics = ctx.substrate.canon.metrics or {}
        if not isinstance(metrics, dict):
            metrics = {}

        threshold_raw = metrics.get("repo_size_max_bytes", _DEFAULT_THRESHOLD_BYTES)
        try:
            threshold = int(threshold_raw)
        except (TypeError, ValueError):
            threshold = _DEFAULT_THRESHOLD_BYTES
        if threshold <= 0:
            return  # disabled

        excluded_raw = metrics.get("repo_size_excluded")
        if isinstance(excluded_raw, list) and all(
            isinstance(p, str) for p in excluded_raw
        ):
            excluded_globs: tuple[str, ...] = tuple(excluded_raw)
        else:
            excluded_globs = _DEFAULT_EXCLUDED_GLOBS

        root = ctx.substrate.root
        total_bytes = 0
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            # Filesystem-level skip via canonical helper (covers .git/,
            # dist/, __pycache__/, .myco/state/, .ruff_cache/, etc.).
            if should_skip_path(path, root=root):
                continue
            # Substrate-level skip via canon-declared globs.
            try:
                rel_posix = path.relative_to(root).as_posix()
            except ValueError:
                continue
            if _matches_any_glob(rel_posix, excluded_globs):
                continue
            try:
                total_bytes += path.stat().st_size
            except OSError:
                continue

        ratio = total_bytes / threshold
        if ratio < 0.80:
            return  # under the warning floor; silent

        if ratio >= 1.0:
            severity = Severity.HIGH
            verb = "exceeded"
        else:
            severity = Severity.MEDIUM
            verb = "approaching"

        yield Finding(
            dimension_id=self.id,
            category=self.category,
            severity=severity,
            message=(
                f"repo working tree {verb} bloat threshold: "
                f"{total_bytes:,} B / {threshold:,} B ({100 * ratio:.1f}%). "
                f"Resolve autonomously via myco excrete (raw notes) or "
                f"fruit→winnow→molt (doctrine archival). Excluded globs: "
                f"{list(excluded_globs)}."
            ),
            path="_canon.yaml",
        )
