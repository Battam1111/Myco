"""Global substrate registry — the user-level directory of every
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

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .io_atomic import atomic_utf8_write, bounded_read_text

__all__ = [
    "SubstrateEntry",
    "registry_path",
    "load_registry",
    "register_substrate",
    "touch_substrate",
    "list_substrates",
]


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
        return (self.path / "_canon.yaml").is_file()


# ----------------------------------------------------------------- paths


def registry_path(home: Path | None = None) -> Path:
    """Location of ``substrates.yaml`` for the current user.

    ``home`` is injectable for tests; production defaults to
    :func:`Path.home`.
    """
    return (home or Path.home()) / ".myco" / "substrates.yaml"


# ------------------------------------------------------------- low-level


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime) -> str:
    # ``2026-04-22T13:29:11Z`` — minute-stable and YAML-safe.
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_iso(raw: Any) -> datetime:
    if isinstance(raw, datetime):
        return raw if raw.tzinfo else raw.replace(tzinfo=timezone.utc)
    try:
        # Accept ``Z`` suffix and offset-aware strings alike.
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
    entries: dict[str, SubstrateEntry],
    home: Path | None = None,
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


# -------------------------------------------------------- public surface


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
