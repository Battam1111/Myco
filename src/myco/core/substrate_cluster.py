"""Cluster module — v0.8.8 max-aggressive merge of substrate, core_registry.

=== substrate ===
Substrate discovery and loading.

A *substrate* is a directory containing a valid ``_canon.yaml``. This
module walks up from a starting directory to find the innermost such
directory, and bundles the resolved ``Canon`` with its ``SubstratePaths``.

v0.5.3 adds substrate-local plugin autoload: when a substrate has a
``.myco/plugins/__init__.py``, ``Substrate.load`` imports it inside an
isolated module namespace so third-party substrates can register
dimensions, adapters, or overlay handlers without editing the Myco
kernel. History: ``docs/contract_changelog.md`` § v0.5.3
(fungal-vocabulary rename + substrate-local extension seam).
L2 doctrine: homeostasis + surface (substrate-local extension seam).

=== core_registry ===
Global substrate registry — the user-level directory of every
Myco substrate germinated on this machine.

Governing doctrine:
``docs/architecture/L2_DOCTRINE/genesis.md`` — the substrate-birth
subsystem. The registry is a side-effect index written at
``germinate`` time; see also
``docs/architecture/L1_CONTRACT/protocol.md`` R1 boot-ritual for
how routing to the right substrate (multi-project pattern)
interacts with ``_canon.yaml`` resolution.

Lives at ``~/.myco/substrates.yaml`` (XDG-compliant on Linux;
``%APPDATA%/.myco/`` on Windows). Per-user, never committed to
version control, never shared across machines. Modelled on shell
history + editor recent-files: a convenience index Myco writes as
a side effect of its normal operations, readable from any process
that wants to enumerate "what substrates do I have here?".

What it's for
-------------

- ``myco graft --list-substrates`` — enumerate all known substrates
  across projects. Useful when you've germinated several and forget
  which slugs you chose.
- Cross-substrate propagation (``myco propagate``) — resolve a
  target substrate by slug instead of typing the full path.
- Future: auto-germinate suggestion pulse can consult the registry
  to detect "this folder used to have a substrate; it moved."

What it's not for
-----------------

- Authoritative substrate metadata — ``_canon.yaml`` is the SSoT.
  The registry stores only *pointer* data (path, slug,
  last-seen-at) to be cheap to read/write.
- Machine-wide state — only the current user sees their own
  ``~/.myco/substrates.yaml``. Don't share it.

File format
-----------

YAML map keyed by ``substrate_id``:

    entries:
      c3-neurips2026:
        path: /home/user/Desktop/C3
        registered_at: 2026-04-22T13:29:11Z
        last_seen_at: 2026-04-23T08:14:05Z
      myco-self:
        path: /home/user/Desktop/Myco
        registered_at: 2026-04-17T09:00:00Z
        last_seen_at: 2026-04-23T10:22:19Z

Concurrent access: writes are atomic via ``atomic_utf8_write`` so
two ``myco`` processes racing to update ``last_seen_at`` never
corrupt the file — worst case is one update loses (acceptable for
a convenience index).

Opt-out
-------

Operators who do not want Myco to track substrate paths on disk
can set ``no_global_registry: true`` at the top level of any
substrate's ``_canon.yaml::system`` block. The registry will
silently skip updates and reads for *that* substrate. The
registry file itself is harmless to leave empty or delete.

Added in v0.5.16.
"""

from __future__ import annotations

import importlib.util
import os
import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .canon import Canon, load_canon
from .identity_cluster import CanonSchemaError, SubstrateNotFound
from .io_cluster import SubstratePaths, atomic_utf8_write, bounded_read_text

# =========================================================================
# === substrate — formerly substrate.py
# =========================================================================

def find_substrate_root(start: Path) -> Path:
    """Walk from ``start`` upward, returning the innermost substrate root.

    A directory counts as a substrate root only if a canon file is
    present (either v0.8.4+ ``.myco/canon.yaml`` or legacy
    ``_canon.yaml``) **and** the canon parses under a known schema
    version. Unparseable canon files propagate as ``CanonSchemaError`` —
    the user gets a clear message rather than silent fall-through.

    Raises ``SubstrateNotFound`` if no substrate is found before the
    filesystem root.
    """
    from .io_cluster import find_substrate_canon, has_substrate

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
        if not has_substrate(candidate):
            continue
        canon_path = find_substrate_canon(candidate)
        load_canon(canon_path)
        return candidate
    raise SubstrateNotFound(
        f"no canon file (.myco/canon.yaml or _canon.yaml) found walking up from {start}"
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
    if canon is None:
        from .io_cluster import find_substrate_canon

        canon = load_canon(find_substrate_canon(root))
    module_name = _substrate_plugin_module_name(root, canon)
    with _PLUGIN_LOAD_LOCK:
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
                    errors=(f"could not build import spec for {init_file}",),
                )
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            try:
                spec.loader.exec_module(module)
            except Exception as exc:
                sys.modules.pop(module_name, None)
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
        except Exception as exc:
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
    return LocalPluginLoadResult(loaded=True, module_name=module_name, errors=())


@dataclass(frozen=True)
class Substrate:
    """A loaded Myco substrate: root path, canon, paths, plugin state."""

    root: Path
    canon: Canon
    paths: SubstratePaths
    local_plugins_loaded: bool = False
    local_plugin_errors: tuple[str, ...] = field(default_factory=tuple)
    local_plugins_module: str | None = None

    @classmethod
    def load(cls, root: Path) -> Substrate:
        """Load a substrate given its root (no walk-up).

        Raises ``CanonSchemaError`` if the canon (either ``.myco/canon.yaml``
        for v0.8.4+ or legacy ``_canon.yaml``) is missing or invalid.
        Auto-imports ``<root>/.myco/plugins/__init__.py`` when present;
        import failures are captured on ``local_plugin_errors`` rather
        than raised (MF2 reports them).
        """
        from .io_cluster import find_substrate_canon, has_substrate

        root = root.resolve()
        if not has_substrate(root):
            raise CanonSchemaError(
                f"no canon file (.myco/canon.yaml or _canon.yaml) found at substrate root: {root}"
            )
        canon_path = find_substrate_canon(root)
        canon = load_canon(canon_path)
        plugin_result = load_local_plugins(root, canon=canon)
        canon_filename = canon_path.relative_to(root).as_posix()
        system_block = canon.system if isinstance(canon.system, dict) else {}
        notes_dir = str(system_block.get("notes_dir") or "notes")
        docs_dir = str(system_block.get("docs_dir") or "docs")
        return cls(
            root=root,
            canon=canon,
            paths=SubstratePaths(
                root=root,
                canon_filename=canon_filename,
                notes_dir=notes_dir,
                docs_dir=docs_dir,
            ),
            local_plugins_loaded=plugin_result.loaded,
            local_plugin_errors=plugin_result.errors,
            local_plugins_module=plugin_result.module_name,
        )

    @classmethod
    def discover(cls, start: Path) -> Substrate:
        """Walk up from ``start`` and load the innermost substrate."""
        root = find_substrate_root(start)
        return cls.load(root)

    @property
    def is_skeleton(self) -> bool:
        """True iff the substrate is in auto-seeded skeleton mode.

        The immune kernel (B.2) consumes this via the canon-declared
        marker path; here we honor the default location (per
        ``canon_schema.md``: ``.myco/state/autoseeded.txt``).
        """
        return self.paths.autoseeded_marker.exists()


# =========================================================================
# === core_registry — formerly registry.py
# =========================================================================

@dataclass(frozen=True)
class SubstrateEntry:
    """One row of the registry."""

    substrate_id: str
    path: Path
    registered_at: datetime
    last_seen_at: datetime

    @property
    def exists(self) -> bool:
        """True when the recorded path still has a ``_canon.yaml``.

        Used by callers to mark stale entries ("substrate deleted or
        moved") without deleting them from the registry — deletion is
        a separate explicit action so users don't lose pointers to
        moved-but-recoverable substrates.
        """
        from myco.core.io_cluster import has_substrate

        return has_substrate(self.path)


def registry_path(home: Path | None = None) -> Path:
    """Location of ``substrates.yaml`` for the current user.

    ``home`` is injectable for tests; production defaults to
    :func:`Path.home`.
    """
    return (home or Path.home()) / ".myco" / "substrates.yaml"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        s = str(raw).replace("Z", "+00:00")
        return datetime.fromisoformat(s).astimezone(timezone.utc)
    except Exception:
        return _utc_now()


def load_registry(home: Path | None = None) -> dict[str, SubstrateEntry]:
    """Read the registry file. Missing/empty/malformed ⇒ empty dict.

    Never raises; a corrupted registry is a convenience-index issue,
    not a fatal error for the surrounding Myco operation.
    """
    p = registry_path(home)
    if not p.exists():
        return {}
    try:
        text = bounded_read_text(p)
    except Exception:
        return {}
    if not text.strip():
        return {}
    try:
        raw = yaml.safe_load(text)
    except Exception:
        return {}
    if not isinstance(raw, dict):
        return {}
    entries_raw = raw.get("entries", {})
    if not isinstance(entries_raw, dict):
        return {}
    out: dict[str, SubstrateEntry] = {}
    for key, row in entries_raw.items():
        if not isinstance(row, dict):
            continue
        path_str = row.get("path")
        if not path_str:
            continue
        out[str(key)] = SubstrateEntry(
            substrate_id=str(key),
            path=Path(str(path_str)),
            registered_at=_parse_iso(row.get("registered_at")),
            last_seen_at=_parse_iso(row.get("last_seen_at")),
        )
    return out


def _write_registry(
    entries: dict[str, SubstrateEntry], home: Path | None = None
) -> None:
    """Serialize + atomically write the registry back to disk."""
    data = {
        "entries": {
            e.substrate_id: {
                "path": str(e.path),
                "registered_at": _iso(e.registered_at),
                "last_seen_at": _iso(e.last_seen_at),
            }
            for e in entries.values()
        }
    }
    text = yaml.safe_dump(data, default_flow_style=False, sort_keys=True)
    target = registry_path(home)
    target.parent.mkdir(parents=True, exist_ok=True)
    atomic_utf8_write(target, text)


def _registry_disabled() -> bool:
    """True when ``MYCO_REGISTRY_DISABLED=1`` is set in the environment.

    Used by the test suite (via a conftest autouse fixture) to prevent
    germinate tests from polluting the operator's real
    ``~/.myco/substrates.yaml`` with pytest tmp-dir paths. Also gives
    privacy-conscious operators a runtime opt-out without needing to
    edit canon.
    """
    return os.environ.get("MYCO_REGISTRY_DISABLED", "").strip() in {"1", "true", "yes"}


def register_substrate(
    substrate_id: str,
    path: Path,
    *,
    home: Path | None = None,
    now: datetime | None = None,
) -> None:
    """Record / upsert a substrate in the registry.

    If ``substrate_id`` is new, both ``registered_at`` and
    ``last_seen_at`` are set to now. If it already exists, only
    ``last_seen_at`` + ``path`` are updated (handles the "substrate
    moved to a new location" case cleanly).

    Respects the ``MYCO_REGISTRY_DISABLED`` env var opt-out (tests
    and privacy-conscious operators).
    """
    if _registry_disabled():
        return
    entries = load_registry(home)
    stamp = now or _utc_now()
    existing = entries.get(substrate_id)
    entries[substrate_id] = SubstrateEntry(
        substrate_id=substrate_id,
        path=path.resolve(),
        registered_at=existing.registered_at if existing else stamp,
        last_seen_at=stamp,
    )
    _write_registry(entries, home)


def touch_substrate(
    substrate_id: str,
    path: Path,
    *,
    home: Path | None = None,
    now: datetime | None = None,
) -> None:
    """Update ``last_seen_at`` for an already-registered substrate.

    Idempotent: missing entries are registered (same effect as
    :func:`register_substrate`). Failures are swallowed — this is a
    best-effort convenience call made on every ``build_context``
    success; a registry-write error must never break the main
    operation.
    """
    try:
        register_substrate(substrate_id, path, home=home, now=now)
    except Exception:
        pass


def list_substrates(home: Path | None = None) -> list[SubstrateEntry]:
    """Enumerate every registered substrate, sorted by
    ``last_seen_at`` desc (most recent first).

    Entries whose path no longer contains ``_canon.yaml`` are still
    returned — callers can filter via ``entry.exists`` to distinguish
    live from stale.
    """
    entries = load_registry(home)
    return sorted(entries.values(), key=lambda e: e.last_seen_at, reverse=True)
