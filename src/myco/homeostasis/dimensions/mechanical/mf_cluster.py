"""MF-cluster — merged dimensions (MF1, MF2, MF4, MF5).

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

import hashlib
from collections.abc import Iterable
from pathlib import Path
from typing import ClassVar

import yaml

from myco.boundary.surface.manifest import load_manifest
from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimension import Dimension
from myco.homeostasis.finding import Category, Finding

__all__ = [
    "MF1DeclaredSubsystemsExist",
    "MF2SubstrateLocalPluginHealth",
    "MF4OverlaySubsystemValidity",
    "MF5GeneratedMirrorIntegrity",
]


# =========================================================================
# MF1 — see module docstring + original git history at parent commits
# =========================================================================


class MF1DeclaredSubsystemsExist(Dimension):
    """Every ``subsystems.<name>.package`` path exists under substrate root."""

    id = "MF1"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root
        subsystems = ctx.substrate.canon.subsystems or {}
        for name, spec in subsystems.items():
            if not isinstance(spec, dict):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"canon.subsystems.{name} must be a mapping, "
                        f"got {type(spec).__name__}"
                    ),
                    path="_canon.yaml",
                )
                continue
            pkg = spec.get("package")
            if pkg is None:
                # Optional field. If absent the canon is using
                # subsystems for pure documentation tagging — no
                # filesystem claim to check.
                continue
            pkg_path = root / str(pkg)
            if not pkg_path.is_dir():
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"canon.subsystems.{name}.package does not "
                        f"resolve to a directory: {pkg}"
                    ),
                    path="_canon.yaml",
                )


# =========================================================================
# MF2 — see module docstring + original git history at parent commits
# =========================================================================


class MF2SubstrateLocalPluginHealth(Dimension):
    """``.myco/plugins/`` and ``.myco/manifest_overlay.yaml`` parse cleanly."""

    id = "MF2"
    category = Category.MECHANICAL
    default_severity = Severity.HIGH

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        paths = ctx.substrate.paths
        plugins_dir = paths.local_plugins_dir
        init_file = paths.local_plugins_init

        # (1) Directory without __init__.py is a broken package.
        if plugins_dir.is_dir() and not init_file.is_file():
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(
                    "substrate-local plugins directory needs an __init__.py "
                    "(found .myco/plugins/ but no .myco/plugins/__init__.py)."
                ),
                path=".myco/plugins/",
            )

        # (2) Every import-time error captured on the substrate surfaces
        # as its own finding so the user sees the exception text.
        for err in ctx.substrate.local_plugin_errors:
            yield Finding(
                dimension_id=self.id,
                category=self.category,
                severity=self.default_severity,
                message=(f"substrate-local plugin package failed to import: {err}"),
                path=".myco/plugins/__init__.py",
            )

        # (3) + (4) Overlay file: parse gate + collision gate.
        overlay_path = paths.manifest_overlay
        if overlay_path.is_file():
            try:
                from myco.core.io_atomic import bounded_read_text

                raw = yaml.safe_load(bounded_read_text(overlay_path)) or {}
            except yaml.YAMLError as exc:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(f"manifest overlay is malformed: {exc}"),
                    path=".myco/manifest_overlay.yaml",
                )
                return

            if not isinstance(raw, dict):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        "manifest overlay is malformed: top level must be a "
                        f"mapping, got {type(raw).__name__}"
                    ),
                    path=".myco/manifest_overlay.yaml",
                )
                return

            commands = raw.get("commands") or []
            if not isinstance(commands, list):
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=("manifest overlay is malformed: commands must be a list"),
                    path=".myco/manifest_overlay.yaml",
                )
                return

            # Build the packaged name/alias index once.
            base = load_manifest()
            reserved: dict[str, str] = {}
            for c in base.commands:
                reserved[c.name] = c.name
                for a in c.aliases:
                    reserved[a] = f"alias of {c.name}"

            for entry in commands:
                if not isinstance(entry, dict):
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            "manifest overlay is malformed: every command "
                            "entry must be a mapping"
                        ),
                        path=".myco/manifest_overlay.yaml",
                    )
                    continue
                name = entry.get("name")
                if not isinstance(name, str):
                    continue
                if name in reserved:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=self.default_severity,
                        message=(
                            f"overlay verb name {name!r} collides with "
                            f"packaged verb {reserved[name]!r}"
                        ),
                        path=".myco/manifest_overlay.yaml",
                    )
                aliases = entry.get("aliases") or ()
                if isinstance(aliases, list):
                    for a in aliases:
                        if isinstance(a, str) and a in reserved:
                            yield Finding(
                                dimension_id=self.id,
                                category=self.category,
                                severity=self.default_severity,
                                message=(
                                    f"overlay alias {a!r} for {name!r} "
                                    f"collides with packaged verb "
                                    f"{reserved[a]!r}"
                                ),
                                path=".myco/manifest_overlay.yaml",
                            )


# =========================================================================
# MF4 — see module docstring + original git history at parent commits
# =========================================================================


class MF4OverlaySubsystemValidity(Dimension):
    """Each overlay_verb's subsystem must exist in canon.subsystems."""

    id = "MF4"
    category = Category.MECHANICAL
    default_severity = Severity.MEDIUM
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        overlay_path = ctx.substrate.root / ".myco" / "manifest_overlay.yaml"
        if not overlay_path.is_file():
            return
        try:
            data = yaml.safe_load(overlay_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            return
        if not isinstance(data, dict):
            return
        commands = data.get("commands") or []
        if not isinstance(commands, list):
            return
        valid_subsystems = set((ctx.substrate.canon.subsystems or {}).keys())
        for cmd in commands:
            if not isinstance(cmd, dict):
                continue
            subsys = cmd.get("subsystem")
            if not subsys:
                continue
            if subsys not in valid_subsystems:
                name = cmd.get("name") or "<unknown>"
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"overlay_verb {name!r} declares subsystem "
                        f"{subsys!r} not in canon.subsystems "
                        f"(known: {sorted(valid_subsystems)})"
                    ),
                    path=".myco/manifest_overlay.yaml",
                )


# =========================================================================
# MF5 — see module docstring + original git history at parent commits
# =========================================================================

# v0.8.8 — directories under which a byte-identical duplicate would
# indicate accidental mirror resurrection. Pairs of (canonical_scope,
# forbidden_duplicate_scope). MF5 fires when a file with identical
# bytes appears in BOTH paths.
_FORBIDDEN_DUPLICATE_PAIRS: tuple[tuple[str, str], ...] = (
    (".claude/agents", ".plugin/agents"),
    (".claude/commands", ".plugin/commands"),
)


def _hash_file(path: Path) -> str | None:
    """SHA-256 hex digest of file content; None on read failure."""
    try:
        h = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


class MF5GeneratedMirrorIntegrity(Dimension):
    """Detect accidental byte-identical duplicates under retired mirror paths."""

    id = "MF5"
    category = Category.MECHANICAL
    default_severity = Severity.LOW
    fixable: ClassVar[bool] = False

    def run(self, ctx: MycoContext) -> Iterable[Finding]:
        root = ctx.substrate.root

        # v0.8.8 — if a forbidden duplicate path exists at all, every
        # file under it is a candidate. Canonical-scope content stays
        # silent (it's the single source of truth); duplicates trigger
        # the dim.
        for canon_rel, forbidden_rel in _FORBIDDEN_DUPLICATE_PAIRS:
            forbidden_dir = root / forbidden_rel
            canon_dir = root / canon_rel
            if not forbidden_dir.is_dir():
                # Forbidden path is absent — the desired state.
                continue
            if not canon_dir.is_dir():
                # Canonical source missing entirely is a separate
                # invariant problem; MF5 doesn't claim that surface.
                continue

            canon_files = {p.name: p for p in canon_dir.glob("*.md") if p.is_file()}
            forbidden_files = {
                p.name: p for p in forbidden_dir.glob("*.md") if p.is_file()
            }

            for name in sorted(forbidden_files):
                fpath = forbidden_files[name]
                cpath = canon_files.get(name)
                f_digest = _hash_file(fpath)
                if f_digest is None:
                    continue
                c_digest = _hash_file(cpath) if cpath is not None else None
                f_rel = fpath.relative_to(root).as_posix()
                c_rel = (
                    cpath.relative_to(root).as_posix() if cpath is not None else None
                )
                if c_digest is None:
                    # Only the forbidden copy exists. Still
                    # surface — the file lives at the retired path.
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"MIRROR_RESURRECTED: {f_rel!r} lives at the "
                            f"retired mirror path. The v0.8.8 doctrine "
                            f"named {canon_rel!r} as the single source of "
                            f"truth — move the file there and remove "
                            f"{forbidden_rel!r}."
                        ),
                        path=f_rel,
                    )
                    continue
                if c_digest == f_digest:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"UNINTENDED_DUPLICATE: {f_rel!r} is byte-"
                            f"identical to {c_rel!r}. The v0.8.8 doctrine "
                            f"retired the {forbidden_rel!r} mirror — "
                            f"plugin.json now references "
                            f"{canon_rel!r} directly. Delete the "
                            f"duplicate at {f_rel!r}."
                        ),
                        path=f_rel,
                    )
                else:
                    yield Finding(
                        dimension_id=self.id,
                        category=self.category,
                        severity=Severity.MEDIUM,
                        message=(
                            f"MIRROR_DRIFT: {c_rel!r} and {f_rel!r} have "
                            f"diverged (sha256 {c_digest[:8]}... vs "
                            f"{f_digest[:8]}...). The {forbidden_rel!r} "
                            f"mirror was retired at v0.8.8; this file "
                            f"is stale doctrine. Delete {f_rel!r} to "
                            f"restore the single-source-of-truth state."
                        ),
                        path=f_rel,
                    )
