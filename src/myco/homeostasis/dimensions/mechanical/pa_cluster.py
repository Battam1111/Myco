"""PA-cluster — merged dimensions (PA1, PA2, PA3, PA4, PA5, PA6).

v0.8.8 merged: this file consolidates the per-dim files that previously
lived as one file per dimension under ``homeostasis/dimensions/mechanical/``.
Class names and behaviour are byte-equivalent — only file locations
changed. Per L1 protocol.md: L3 organization choices are ordinary
code changes; no contract bump required. Original per-dim files are
preserved in git history at parent commits.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/homeostasis.md``
§ "Dimension enumeration".
"""

from __future__ import annotations

import ast
import fnmatch
from collections.abc import Iterable
from typing import ClassVar

from myco.core.identity_cluster import MycoContext, Severity
from myco.core.io_cluster import should_skip_dir, should_skip_path
from myco.homeostasis.primitives_cluster import Category, Dimension, Finding

__all__ = [
    "PA1WriteSurfaceCoverage",
    "PA2MegafileLocCap",
    "PA3SurfacePureAdapter",
    "PA4CoreNoSubsystemDeps",
    "PA5MetaSubsystemLayering",
    "PA6RepoBloat",
]


# =========================================================================
# PA1 — see module docstring + original git history at parent commits
# =========================================================================

#: ``(label, sample_path)`` pairs representing the canonical write
#: target for each v0.5.x verb that writes. A pattern under
#: ``canon.system.write_surface.allowed`` that matches ``sample_path``
#: (via ``fnmatch.fnmatchcase``) is deemed to cover that verb.
#: ``label`` is surfaced in the finding message so operators know
#: which verb is affected.
#: Static samples for verbs whose paths follow the same substrate
#: subdir convention regardless of layout. The dynamic samples
#: (canon, contract_changelog) are resolved from substrate.paths at
#: run() time below, so PA1 correctly checks the substrate's actual
#: declared layout (legacy ``_canon.yaml`` vs v0.8.4+ ``.myco/canon.yaml``).
_STATIC_SAMPLES: tuple[tuple[str, str, str], ...] = (
    ("notes/raw/**/*.md (eat)", "notes_dir", "raw/sample.md"),
    (
        "notes/integrated/**/*.md (assimilate/digest)",
        "notes_dir",
        "integrated/sample.md",
    ),
    ("notes/distilled/**/*.md (sporulate)", "notes_dir", "distilled/sample.md"),
)


class PA1WriteSurfaceCoverage(Dimension):
    """``canon.system.write_surface.allowed`` covers core v0.5.x paths."""

    id = "PA1"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        # Resolve dynamic sample paths from the substrate's declared
        # layout so PA1 works identically across legacy + v0.8.4+ shapes.
        paths = ctx.substrate.paths
        root = ctx.substrate.root
        canon_rel = paths.canon.relative_to(root).as_posix()
        notes_rel = paths.notes.relative_to(root).as_posix()
        docs_rel = paths.docs.relative_to(root).as_posix()
        samples = [
            *_STATIC_SAMPLES,
            ("canon (molt/germinate)", "_canon_path", canon_rel),
            (
                "contract_changelog.md (molt)",
                "_doc_path",
                f"{docs_rel}/contract_changelog.md",
            ),
        ]

        system = ctx.substrate.canon.system or {}
        ws = system.get("write_surface") or {}
        allowed = ws.get("allowed") or []
        if not isinstance(allowed, list):
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=Severity.HIGH,
                message=(
                    "canon.system.write_surface.allowed is not a list; "
                    "write_surface enforcement will reject every path."
                ),
                path=canon_rel,
            )
            return
        patterns = [str(x) for x in allowed]
        for entry in samples:
            label = entry[0]
            kind = entry[1]
            tail = entry[2]
            if kind == "notes_dir":
                sample = f"{notes_rel}/{tail}"
            elif kind in ("_canon_path", "_doc_path"):
                sample = tail
            else:
                sample = tail
            if any(fnmatch.fnmatchcase(sample, p) for p in patterns):
                continue
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    f"canon.system.write_surface.allowed does not match "
                    f"sample path {sample!r} for {label}; the "
                    f"corresponding verb will fail its write-surface "
                    f"check. Add a covering pattern or confirm the "
                    f"substrate is intentionally read-only for that "
                    f"verb."
                ),
                path=canon_rel,
            )


# =========================================================================
# PA2 — see module docstring + original git history at parent commits
# =========================================================================

_LOC_CAP: int = 800


class PA2MegafileLocCap(Dimension):
    """No `.py` file in `src/myco/` may exceed the LoC cap (default 800)."""

    id = "PA2"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        src_root = ctx.substrate.root / "src" / "myco"
        if not src_root.is_dir():
            return
        for path in src_root.rglob("*.py"):
            if any(should_skip_dir(p.name) for p in path.parents):
                continue
            try:
                lines = path.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            if len(lines) > _LOC_CAP:
                rel = path.relative_to(ctx.substrate.root).as_posix()
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"megafile: {len(lines)} LoC > {_LOC_CAP} cap "
                        f"(invariant 5 in package_map.md)"
                    ),
                    path=rel,
                )


# =========================================================================
# PA3 — see module docstring + original git history at parent commits
# =========================================================================

_ALLOWED_INTERNAL_PREFIXES: tuple[str, ...] = (
    "myco.core",
    "myco.boundary.surface",
)

_FORBIDDEN_INTERNAL_PREFIXES: tuple[str, ...] = (
    "myco.ingestion",
    "myco.digestion",
    "myco.circulation",
    "myco.homeostasis",
    "myco.cycle",
    "myco.germination",
)


class PA3SurfacePureAdapter(Dimension):
    """surface/ may not import subsystem packages directly."""

    id = "PA3"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        surface_root = ctx.substrate.root / "src" / "myco" / "surface"
        if not surface_root.is_dir():
            return
        for path in surface_root.rglob("*.py"):
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                module: str | None = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        break
                if not module:
                    continue
                if any(module.startswith(p) for p in _FORBIDDEN_INTERNAL_PREFIXES):
                    rel = path.relative_to(ctx.substrate.root).as_posix()
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"surface/ imports subsystem package {module!r}; "
                            f"surface should be pure adapter "
                            f"(invariant 4 in package_map.md)"
                        ),
                        path=rel,
                    )


# =========================================================================
# PA4 — see module docstring + original git history at parent commits
# =========================================================================


#: Files inside core/ that may legitimately reference subsystem
#: package names by string (NOT by import). Allow-list is path-based.
_PA4_PERMITS: frozenset[str] = frozenset(
    {
        # canon.py registers schema_upgraders by string-keyed callable;
        # the callables don't import subsystems either, but if a future
        # registration grows complexity it would land here first.
        "src/myco/core/canon.py",
    }
)


class PA4CoreNoSubsystemDeps(Dimension):
    """core/ may not import any subsystem package."""

    id = "PA4"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        core_root = ctx.substrate.root / "src" / "myco" / "core"
        if not core_root.is_dir():
            return
        for path in core_root.rglob("*.py"):
            rel = path.relative_to(ctx.substrate.root).as_posix()
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, SyntaxError):
                continue
            for node in ast.walk(tree):
                module: str | None = None
                if isinstance(node, ast.ImportFrom):
                    module = node.module
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        module = alias.name
                        break
                if not module:
                    continue
                if any(module.startswith(p) for p in _FORBIDDEN_INTERNAL_PREFIXES):
                    if rel in _PA4_PERMITS:
                        continue
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"core/ imports subsystem package {module!r} "
                            f"(invariant 2 in package_map.md)"
                        ),
                        path=rel,
                    )


# =========================================================================
# PA5 — see module docstring + original git history at parent commits
# =========================================================================

_FORBIDDEN_META: tuple[str, ...] = (
    "myco.boundary.surface",
    "myco.boundary.install",
    "myco.boundary.mcp",
    "myco.boundary",
)

#: Per-subsystem allowlist of cross-layer imports legitimized by doctrine.
#: ``manifest`` is the canonical contract surface (SSoT for verb declarations
#: and overlay merging) — subsystems read it as data, not as a meta-adapter,
#: so the import does not violate the layering invariant per L2 doctrine
#: ``boundary.md`` § "Manifest as contract surface" (v0.6.0 craft §F19).
#: Without this allowlist, PA5 would flag legitimate manifest reads in
#: ``ingestion/hunger`` (local plugins summary) and ``homeostasis/MF2``
#: (overlay-verb subsystem validity check).
_ALLOWED_META_IMPORTS: frozenset[str] = frozenset(
    {
        "myco.boundary.surface.manifest",
    }
)

_SUBSYSTEM_ROOTS: tuple[str, ...] = (
    "germination",
    "ingestion",
    "digestion",
    "circulation",
    "homeostasis",
    # cycle is excepted: it composes transitions across subsystems.
)


class PA5MetaSubsystemLayering(Dimension):
    """Subsystems may not depend on meta-subsystem (surface/install/mcp/symbionts)."""

    id = "PA5"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        for subsys in _SUBSYSTEM_ROOTS:
            sub_root = ctx.substrate.root / "src" / "myco" / subsys
            if not sub_root.is_dir():
                continue
            for path in sub_root.rglob("*.py"):
                rel = path.relative_to(ctx.substrate.root).as_posix()
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except (OSError, UnicodeDecodeError, SyntaxError):
                    continue
                for node in ast.walk(tree):
                    module: str | None = None
                    if isinstance(node, ast.ImportFrom):
                        module = node.module
                    elif isinstance(node, ast.Import):
                        for alias in node.names:
                            module = alias.name
                            break
                    if not module:
                        continue
                    # v0.6.0: doctrine-allowlisted meta imports (manifest as
                    # contract surface) are exempt — see _ALLOWED_META_IMPORTS.
                    if module in _ALLOWED_META_IMPORTS:
                        continue
                    if any(module.startswith(p) for p in _FORBIDDEN_META):
                        yield Finding(
                            dimension_id=self.id,
                            category=self.category,
                            severity=self.default_severity,
                            message=(
                                f"subsystem {subsys!r} imports meta-subsystem "
                                f"package {module!r}; meta packages are "
                                f"cross-cutting adapters and must not be "
                                f"depended upon by subsystems"
                            ),
                            path=rel,
                        )


# =========================================================================
# PA6 — see module docstring + original git history at parent commits
# =========================================================================

_DEFAULT_THRESHOLD_BYTES = 50 * 1024 * 1024  # 50 MB
_DEFAULT_EXCLUDED_GLOBS = (
    "notes/**",
    "docs/primordia/_landed/**",
    "docs/_archive/**",
    "docs/contract_changelog/_archive/**",
    # v0.8.5 — also cover .docs/ + .myco/notes/ for substrates that have
    # adopted the v0.8.4+ relocated layout. Substrates can still override
    # via canon.metrics.repo_size_excluded; these defaults cover both
    # legacy and relocated shapes out-of-the-box.
    ".myco/notes/**",
    ".docs/primordia/_landed/**",
    ".docs/_archive/**",
    ".docs/contract_changelog/_archive/**",
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
