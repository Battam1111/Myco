"""MF2 — substrate-local plugin health.

v0.5.3 introduces ``.myco/plugins/`` as the substrate-local extension
seam (dimensions, adapters, overlay handlers). MF2 is the homeostasis
dimension that keeps it honest: when a substrate ships a ``.myco/``
directory, this dimension confirms the plugin package is well-formed
and loadable.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/homeostasis.md`` (substrate-local
plugin health). Governing craft:
``docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md``.

Fires MECHANICAL:HIGH findings for:

- ``.myco/plugins/`` exists but ``__init__.py`` is missing — the
  directory is an incomplete Python package.
- ``Substrate.local_plugin_errors`` is non-empty — import-time failure
  captured at :func:`myco.core.substrate.Substrate.load`.
- ``.myco/manifest_overlay.yaml`` exists but fails to parse as YAML.
- An overlay verb name collides with a packaged canonical verb or
  alias.

No-op for substrates that don't use ``.myco/``. That's the common
case and MF2 must not cost anything.
"""

from __future__ import annotations

from typing import Iterable

import yaml

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.surface.manifest import load_manifest

from ..dimension import Dimension
from ..finding import Category, Finding

__all__ = ["MF2SubstrateLocalPluginHealth"]


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
                message=(
                    f"substrate-local plugin package failed to import: {err}"
                ),
                path=".myco/plugins/__init__.py",
            )

        # (3) + (4) Overlay file: parse gate + collision gate.
        overlay_path = paths.manifest_overlay
        if overlay_path.is_file():
            try:
                raw = yaml.safe_load(
                    overlay_path.read_text(encoding="utf-8")
                ) or {}
            except yaml.YAMLError as exc:
                yield Finding(
                    dimension_id=self.id,
                    category=self.category,
                    severity=self.default_severity,
                    message=(
                        f"manifest overlay is malformed: {exc}"
                    ),
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
                    message=(
                        "manifest overlay is malformed: commands must be a list"
                    ),
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
