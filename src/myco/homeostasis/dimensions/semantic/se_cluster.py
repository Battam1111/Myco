"""SE-cluster — merged dimensions (SE1, SE2, SE3, SE5).

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

import re
from collections.abc import Iterable
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "SE1DanglingRefs",
    "SE2OrphanIntegrated",
    "SE3LinkSelfCycle",
    "SE5VersionAnchorFreshness",
]


# =========================================================================
# SE1 — see module docstring + original git history at parent commits
# =========================================================================


class SE1DanglingRefs(Dimension):
    """One finding per dangling edge in the substrate graph."""

    id = "SE1"
    category = Category.SEMANTIC
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = True

    def fix(self, ctx: MycoContext, finding: Finding) -> dict[str, object]:
        """v0.6.0 §F18: narrow advisory fix.

        SE1 fix is intentionally narrow because rewriting a markdown
        link in source code is a delicate operation (could break
        formatting, table cells, frontmatter). v0.6.0 reports the fix
        as advisory; agent or operator removes the dangling reference
        manually. Future v0.6.x patch may add proper AST-aware
        markdown surgery.
        """
        return {
            "applied": False,
            "detail": (
                "SE1 fixable=True at v0.6.0 is advisory: dangling-link "
                "removal is delicate (could disturb formatting). "
                "Manual edit recommended. Path: " + str(finding.path)
            ),
        }

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Lazy import: keeps dimensions/__init__ cheap and breaks any
        # potential cycle if circulation reaches back into homeostasis.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        # v0.5.8 perf: Graph.nodes is already the canonical "resolved,
        # inside the substrate" set. Any edge whose dst is not in that
        # set is, by the graph builder's construction, dangling —
        # either the destination string never pointed anywhere that
        # resolved, or it escaped the substrate. Either way SE1 should
        # flag it. Filesystem stat(2) is avoided entirely.
        nodes = graph.nodes
        for edge in graph.edges:
            if edge.dst in nodes:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(f"{edge.src} references missing {edge.dst} ({edge.kind})"),
                path=edge.src,
            )


# =========================================================================
# SE2 — see module docstring + original git history at parent commits
# =========================================================================


class SE2OrphanIntegrated(Dimension):
    """Integrated notes with no inbound edges in the graph."""

    id = "SE2"
    category = Category.SEMANTIC
    default_severity = Severity.LOW

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        from myco.circulation.graph import build_graph

        integrated_dir = ctx.substrate.paths.notes / "integrated"
        if not integrated_dir.is_dir():
            return
        integrated = [p for p in integrated_dir.glob("*.md") if p.is_file()]
        if not integrated:
            return

        graph = build_graph(ctx)
        referenced = {edge.dst for edge in graph.edges}
        root = ctx.substrate.root

        for note_path in integrated:
            rel = note_path.relative_to(root).as_posix()
            if rel in referenced:
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=f"integrated note {rel} has no inbound references",
                path=rel,
            )


# =========================================================================
# SE3 — see module docstring + original git history at parent commits
# =========================================================================


class SE3LinkSelfCycle(Dimension):
    """No substrate file references itself as a graph edge."""

    id = "SE3"
    category = Category.SEMANTIC
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Lazy import to avoid pulling circulation into the dimension
        # package import graph.
        from myco.circulation.graph import build_graph

        graph = build_graph(ctx)
        for edge in graph.edges:
            if edge.src == edge.dst:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"{edge.src} references itself "
                        f"({edge.kind} edge) — drop the self-reference."
                    ),
                    path=edge.src,
                )


# =========================================================================
# SE5 — see module docstring + original git history at parent commits
# =========================================================================

# Live-doc scope (anchored relative paths from substrate root).
# Each entry: glob pattern. Order is irrelevant; the union is scanned.
_LIVE_DOC_GLOBS: tuple[str, ...] = (
    "docs/architecture/**/*.md",
    "MYCO.md",
    "README.md",
    # v0.8.4 root-cleanup (2026-05-12): non-English READMEs moved
    # under docs/i18n/ to declutter the repo root. SE5 scans them
    # the same way — only the path changed.
    "docs/i18n/README_zh.md",
    "docs/i18n/README_ja.md",
    "_canon.yaml",
    "pyproject.toml",
)

# Version anchor regex: matches v0.6.15, v0.7.0, v1.2.3, etc.
# Captures the (major, minor, patch) groups for comparison.
_VERSION_ANCHOR_RE = re.compile(r"\bv(\d+)\.(\d+)\.(\d+)\b")

# Historical-context tokens preceding a version anchor: presence
# within a small left-context window suppresses the finding.
# v0.7.3 expansion: added more "tag/preserved/example" patterns after
# the v0.7.2 SE5 false-positives at canon_schema/versioning/MYCO.
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
    # v0.7.3 additions — tag / preservation / example references.
    "preserved at ",
    "preserved as ",
    "preserves it",
    "preserves",
    "anchor tag",
    "tag `",  # "tag `v0.3.4-final`"
    "tag '",
    "at tag ",
    "git tag",
    "after `v",  # versioning example: "v0.6.1 after `v0.3.3` is forbidden"
    "after v",
    "before `v",
    "before v",
    "is forbidden",
    "rewrite from v",
    "rewrite (v",
    "the v",  # "The v0.3.4 canon" — historical descriptor
    "the pre-rewrite v",
    "(v0.",  # parenthesized historical references
    "v0.3.4-final",  # the tag itself, used as a literal identifier
    # v0.8.5 — doctrine-prose patterns surfaced by the SE5 sweep:
    # "the v0.4.0 schema" / "Under v0.4.0" / "from `v0.4.0`" / "at v0.4.0".
    # Safe because SE5 only fires on anchors < current - 3 minor; a
    # forward-looking "at v" would describe a NON-stale anchor that
    # SE5 doesn't flag anyway. All tokens are natural-prose patterns
    # (no version-anchor self-silencers).
    "at v",
    "at `v",
    "under v",
    "from v",
    "from `v",
    "for v",
    # Doctrine-specific phrases that signal historical context:
    "next release",  # "v0.4.0 is the authoritative next release"
    "starts a clean",  # "starts a clean, monotone sequence from v0.4.0"
    "filename",  # "keeps its v0.4.0 filename" → historical
    "schema (",  # "_canon.yaml — v0.4.0 schema (example shape; ..."
    "instance at",  # "the v0.4.0 canon instance at L4"
    "twelve verbs",  # "v0.4.0 shipped twelve verbs"
    "during development",  # "v0.4.0-alpha.1 during development"
    "at release",  # "v0.4.0 at release"
    "ssot-only",  # "The v0.4.0 canon is SSoT-only"
    "audit gap",  # "closing the v0.4.1 audit gap"
    "dimension set",  # "The v0.4.0 dimension set"
    "homeostasis at",  # "budget for Homeostasis at v0.4.0"
    "registry; v",  # "(registry; v0.4.2)"
    "(was `genesis",  # "(was `genesis/` at v0.4.0-v0.5.2)"
)

# Window of characters before the match to scan for historical tokens.
_HIST_WINDOW = 40

# v0.8.5 — symmetric right-context window so tokens like "the v" /
# "before v" / "from `v" naturally self-silence single-anchor lines.
# Previously these tokens only worked on multi-anchor lines (e.g.
# "rewrite from v0.3.4 to v0.4.0") because the v of the matched
# anchor was outside left_context. With the right window, the match
# itself contributes to the search space and "the v0.4.0" suppresses
# correctly.
_HIST_RIGHT_WINDOW = 50


def _is_historical_context(
    line: str,
    match_start: int,
    match_end: int,
) -> bool:
    """Return True if a historical-context token appears within
    [_HIST_WINDOW chars before, match span, _HIST_RIGHT_WINDOW chars
    after] the version anchor."""
    window_start = max(0, match_start - _HIST_WINDOW)
    window_end = min(len(line), match_end + _HIST_RIGHT_WINDOW)
    context = line[window_start:window_end].lower()
    return any(tok in context for tok in _HISTORICAL_TOKENS)


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

        # v0.8.4 root-cleanup (2026-05-12): docs/ may be relocated to
        # .docs/ (Myco-self) or stay at root (downstream). Remap any
        # glob that starts with "docs/" through paths.docs.
        docs_dir = ctx.substrate.paths.docs_dir
        # v0.8.6 — also remap the entry-page glob (`MYCO.md`) + canon
        # glob (`_canon.yaml`) through canon-configured locations.
        # Previously these were hardcoded literals, so Myco-self's
        # `.myco/MYCO.md` + `.myco/canon.yaml` were silently excluded
        # from the SE5 freshness sweep — critical reading-surface
        # version anchors went unchecked.
        entry_point = ctx.substrate.canon.entry_point
        canon_rel = ctx.substrate.paths.canon.relative_to(
            ctx.substrate.root.resolve()
        ).as_posix()
        effective_globs: tuple[str, ...] = tuple(
            (
                f"{docs_dir}/" + p[len("docs/") :]
                if p.startswith("docs/") and docs_dir != "docs"
                else (
                    entry_point
                    if p == "MYCO.md"
                    else (canon_rel if p == "_canon.yaml" else p)
                )
            )
            for p in _LIVE_DOC_GLOBS
        )

        seen_paths: set[str] = set()
        for pattern in effective_globs:
            for path in root.glob(pattern):
                if not path.is_file():
                    continue
                rel_posix = path.relative_to(root).as_posix()
                if rel_posix in seen_paths:
                    continue
                # v0.7.3 — exclude any archive path. The pattern
                # `docs/architecture/**/*.md` correctly matches
                # `docs/architecture/L3_IMPLEMENTATION/_archive/...`,
                # but archived files are immutable history and their
                # version anchors are correct for the era they describe.
                if "/_archive/" in rel_posix or "/_landed/" in rel_posix:
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
                        if _is_historical_context(line, m.start(), m.end()):
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
