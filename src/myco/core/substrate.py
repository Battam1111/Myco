"""Substrate discovery and loading.

A *substrate* is a directory containing a valid ``_canon.yaml``. This
module walks up from a starting directory to find the innermost such
directory, and bundles the resolved ``Canon`` with its ``SubstratePaths``.

v0.5.3 adds substrate-local plugin autoload: when a substrate has a
``.myco/plugins/__init__.py``, ``Substrate.load`` imports it inside an
isolated module namespace so third-party substrates can register
dimensions, adapters, or overlay handlers without editing the Myco
kernel. Governing craft:
``docs/primordia/v0_5_3_fungal_vocabulary_craft_2026-04-17.md``.
L2 doctrine: homeostasis + surface (substrate-local extension seam).
"""

from __future__ import annotations

import importlib.util
import sys
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Tuple

from .canon import Canon, load_canon
from .errors import CanonSchemaError, SubstrateNotFound
from .paths import SubstratePaths

__all__ = [
    "Substrate",
    "find_substrate_root",
    "LocalPluginLoadResult",
    "load_local_plugins",
]


def find_substrate_root(start: Path) -> Path:
    """Walk from ``start`` upward, returning the innermost substrate root.

    A directory counts as a substrate root only if ``_canon.yaml`` is
    present **and** parses under a known schema version. Unparseable
    canon files propagate as ``CanonSchemaError`` — the user gets a
    clear message rather than silent fall-through.

    Raises ``SubstrateNotFound`` if no substrate is found before the
    filesystem root.
    """
    start = start.resolve()
    candidates: list[Path] = []
    current = start if start.is_dir() else start.parent
    while True:
        candidates.append(current)
        parent = current.parent
        if parent == current:
            break
        current = parent

    for candidate in candidates:
        canon_path = candidate / "_canon.yaml"
        if not canon_path.is_file():
            continue
        # parse — propagate schema errors; a corrupt canon is a
        # substrate we found but can't use, not a miss.
        load_canon(canon_path)
        return candidate

    raise SubstrateNotFound(
        f"no _canon.yaml found walking up from {start}"
    )


@dataclass(frozen=True)
class LocalPluginLoadResult:
    """Outcome of a ``.myco/plugins/`` import attempt.

    Kept simple and serializable so the MF2 dimension and the
    ``graft`` verb can both inspect it without re-running the loader.
    """

    loaded: bool
    module_name: str | None = None
    errors: tuple[str, ...] = ()


#: Lock around ``sys.path`` and ``sys.modules`` mutation so parallel
#: test runners do not step on each other. The loader is idempotent
#: per-substrate (module_name is derived from substrate_id + root
#: path), but the sys-state mutations themselves must be serialized.
_PLUGIN_LOAD_LOCK = threading.RLock()


def _substrate_plugin_module_name(root: Path, canon: Canon) -> str:
    """Derive a collision-free dotted module name for a substrate's
    local plugin package.

    Uses the substrate_id when present, falling back to a stable hash
    of the root path. The prefix ``myco._substrate_plugins_`` isolates
    the import from any coincidental top-level ``plugins`` package
    (e.g. a monorepo with its own ``plugins/`` package).
    """
    import hashlib

    sid = (canon.substrate_id or "").strip()
    # Keep module names legal (letters, digits, underscore). Everything
    # else collapses to underscore; the hash suffix preserves uniqueness
    # when substrate_id alone could collide across unrelated checkouts.
    safe = "".join(c if c.isalnum() or c == "_" else "_" for c in sid) or "unnamed"
    digest = hashlib.blake2s(
        str(root).encode("utf-8", "replace"), digest_size=6
    ).hexdigest()
    return f"myco._substrate_plugins_{safe}_{digest}"


def load_local_plugins(
    root: Path, *, canon: Canon | None = None
) -> LocalPluginLoadResult:
    """Import ``<root>/.myco/plugins/__init__.py`` under an isolated name.

    Returns a :class:`LocalPluginLoadResult` rather than raising —
    a broken substrate-local plugin must not brick ``Substrate.load``
    (MF2 surfaces the error so the user sees it next time they run
    ``myco immune``).

    Semantics:

    - No ``.myco/plugins/__init__.py`` → ``loaded=False``, no errors.
    - File exists + imports cleanly → ``loaded=True``.
    - File exists + raises on import → ``loaded=False`` plus a one-
      element ``errors`` tuple describing the exception.

    The plugin package is registered in ``sys.modules`` under an
    isolated name (see :func:`_substrate_plugin_module_name`) so a
    second substrate in the same process does not clobber the first.
    We also prepend ``<root>/.myco/`` to ``sys.path`` so the plugin
    package can import its own submodules via ``from plugins.x
    import y`` semantics — local overrides win over installed
    packages but never shadow kernel modules (the prepend is popped
    on failure).
    """
    plugins_dir = root / ".myco" / "plugins"
    init_file = plugins_dir / "__init__.py"
    if not init_file.is_file():
        return LocalPluginLoadResult(loaded=False, module_name=None, errors=())

    # Defer canon load to the caller when the Substrate already has
    # one — re-parsing here would be wasteful and couple us to I/O.
    if canon is None:
        canon = load_canon(root / "_canon.yaml")

    module_name = _substrate_plugin_module_name(root, canon)

    with _PLUGIN_LOAD_LOCK:
        # Idempotency: a second Substrate.load() for the same root
        # returns the already-imported module.
        if module_name in sys.modules:
            return LocalPluginLoadResult(
                loaded=True, module_name=module_name, errors=()
            )

        myco_dir = str((root / ".myco").resolve())
        path_injected = False
        if myco_dir not in sys.path:
            sys.path.insert(0, myco_dir)
            path_injected = True

        try:
            spec = importlib.util.spec_from_file_location(
                module_name,
                str(init_file),
                submodule_search_locations=[str(plugins_dir.resolve())],
            )
            if spec is None or spec.loader is None:
                return LocalPluginLoadResult(
                    loaded=False,
                    module_name=module_name,
                    errors=(
                        f"could not build import spec for {init_file}",
                    ),
                )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception as exc:  # noqa: BLE001 - defensive for plugin failures
                # Back out the sys.modules registration + path inject so
                # the environment is unchanged by a broken plugin.
                sys.modules.pop(module_name, None)
                if path_injected and myco_dir in sys.path:
                    try:
                        sys.path.remove(myco_dir)
                    except ValueError:
                        pass
                return LocalPluginLoadResult(
                    loaded=False,
                    module_name=module_name,
                    errors=(
                        f"{type(exc).__name__}: {exc}",
                    ),
                )
        except Exception as exc:  # noqa: BLE001 - spec building edge cases
            if path_injected and myco_dir in sys.path:
                try:
                    sys.path.remove(myco_dir)
                except ValueError:
                    pass
            return LocalPluginLoadResult(
                loaded=False,
                module_name=module_name,
                errors=(f"{type(exc).__name__}: {exc}",),
            )

    return LocalPluginLoadResult(
        loaded=True, module_name=module_name, errors=()
    )


@dataclass(frozen=True)
class Substrate:
    """A loaded Myco substrate: root path, canon, paths, plugin state."""

    root: Path
    canon: Canon
    paths: SubstratePaths
    #: True iff ``.myco/plugins/__init__.py`` exists and imported cleanly.
    #: Default False when there is no plugins package or import failed;
    #: MF2 surfaces the import-failure case as a finding.
    local_plugins_loaded: bool = False
    #: Tuple of human-readable error strings captured during local plugin
    #: load. Empty when the load was clean (whether or not any plugins
    #: were found). Never re-raises; broken plugins must not brick load.
    local_plugin_errors: Tuple[str, ...] = field(default_factory=tuple)
    #: Isolated module name the plugin package was imported under. Used
    #: by ``graft --explain`` / ``graft --validate`` to introspect the
    #: already-loaded plugin space without re-importing.
    local_plugins_module: str | None = None

    @classmethod
    def load(cls, root: Path) -> "Substrate":
        """Load a substrate given its root (no walk-up).

        Raises ``CanonSchemaError`` if ``root/_canon.yaml`` is missing
        or invalid. Auto-imports ``<root>/.myco/plugins/__init__.py``
        when present; import failures are captured on
        ``local_plugin_errors`` rather than raised (MF2 reports them).
        """
        root = root.resolve()
        canon_path = root / "_canon.yaml"
        if not canon_path.is_file():
            raise CanonSchemaError(
                f"_canon.yaml not found at substrate root: {root}"
            )
        canon = load_canon(canon_path)
        plugin_result = load_local_plugins(root, canon=canon)
        return cls(
            root=root,
            canon=canon,
            paths=SubstratePaths(root=root),
            local_plugins_loaded=plugin_result.loaded,
            local_plugin_errors=plugin_result.errors,
            local_plugins_module=plugin_result.module_name,
        )

    @classmethod
    def discover(cls, start: Path) -> "Substrate":
        """Walk up from ``start`` and load the innermost substrate."""
        root = find_substrate_root(start)
        return cls.load(root)

    @property
    def is_skeleton(self) -> bool:
        """True iff the substrate is in auto-seeded skeleton mode.

        The immune kernel (B.2) consumes this via the canon-declared
        marker path; here we honor the default location (per
        ``canon_schema.md``: ``.myco_state/autoseeded.txt``).
        """
        return self.paths.autoseeded_marker.exists()
