"""Owner-key history persistence — canonical-bytes save/load (L4 M10).

## On-disk schema (owner_keys.cb)

A canonical-bytes Map with five keys:

- ``format_version``: Uint(2) — schema version pin.
- ``k``: Uint — active-prefix cap (typically 8).
- ``active_prefix``: Array of OwnerKeyEntry Maps (most-recent K entries).
- ``active_extra_valid``: Array of OwnerKeyEntry Maps (currently-valid
  entries older than K — conceptually part of active layer).
- ``archived_tail``: Array of OwnerKeyEntry Maps (cold-tier-eligible).

Each OwnerKeyEntry Map:

- ``public_key``: Bytes(32) — Ed25519 public key.
- ``valid_from_anchor_timestamp``: Uint — when this key became active.
- ``valid_until_anchor_timestamp``: Uint(0 sentinel) — when retired
  (0 means still currently valid; the active key).
- ``valid_until_set``: Bool — True if valid_until is meaningful.
- ``rotation_attestation_hash``: Bytes — hash of the rotation attestation
  that introduced this key, OR empty bytes for genesis.
- ``cooldown_expired_at_anchor_timestamp``: Uint(0 sentinel) — C70: when the
  30-day cooldown veto window for THIS key's successor elapsed (v2+).
- ``cooldown_expired_at_set``: Bool — True if ``cooldown_expired_at`` is
  meaningful (v2+).

## Versioning (v1 → v2 shim)

C70 added the two ``cooldown_expired_at`` columns, bumping the format to 2. A
v1 file (no ``cooldown_expired_at`` columns on its entries) is still readable:
``owner_keys_from_canonical_bytes`` accepts both versions and treats absent
``cooldown_expired_at`` as ``None`` (the genesis / never-rotated state). v2 is
written going forward. A future-version (>2) file returns ``None`` (incompatible)
exactly as before.

## Atomicity

Writes go to ``owner_keys.cb.tmp`` first, then ``os.replace`` atomically
swaps onto ``owner_keys.cb`` (same pattern as gradient.cb persistence).

## Doctrine

- L1/GOVERNANCE §3.1 — active-prefix + archived-tail discipline preserved
  across persistence boundary.
- L1/HARD_RULES F3 — owner_key_history is a contract-identity-level fixed
  point; persistence integrity is critical.
- L0/cards/AS_anchor_surface §3 — canonical-bytes determinism.

## M10 scope

M10 ships the persistence primitive + genesis initialization. M11+ adds
rotation FSM + cooldown veto + cryptographic-suite migration.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes as CbBytes,
    CanonicalBytesError,
    Map as CbMap,
    Uint as CbUint,
    Value,
    decode,
    encode,
    expect_array,
    expect_bool,
    expect_bytes,
    expect_map,
    expect_uint,
)
from myco_kernel_governance.crypto import Ed25519PublicKey
from myco_kernel_governance.owner_keys import (
    DEFAULT_ACTIVE_PREFIX_K,
    OwnerKeyEntry,
    OwnerKeyHistory,
)


OWNER_KEYS_FILENAME: Final[str] = "owner_keys.cb"
"""Filename for the owner-key history file within a substrate state directory."""

OWNER_KEYS_FORMAT_VERSION: Final[int] = 2
"""On-disk format version. Bumped on any breaking schema change. v2 (C70)
added the ``cooldown_expired_at`` entry columns; v1 files remain readable via
the shim in :func:`owner_keys_from_canonical_bytes`."""


class OwnerKeysPersistenceError(Exception):
    """Owner-key-history persistence error (I/O, malformed data, version mismatch)."""


def _entry_to_value(entry: OwnerKeyEntry) -> Value:
    """Encode one OwnerKeyEntry as a canonical-bytes Map (v2)."""
    valid_until = entry.valid_until_anchor_timestamp
    rot_hash = entry.rotation_attestation_canonical_bytes_hash
    cooldown = entry.cooldown_expired_at_anchor_timestamp
    return CbMap.from_dict(
        {
            "public_key": CbBytes(entry.public_key.bytes_),
            "valid_from_anchor_timestamp": CbUint(
                entry.valid_from_anchor_timestamp
            ),
            "valid_until_anchor_timestamp": CbUint(valid_until or 0),
            "valid_until_set": Bool(valid_until is not None),
            "rotation_attestation_hash": CbBytes(rot_hash if rot_hash else b""),
            # C70 (v2): the cooldown-window-elapsed instant for this key's
            # successor. v1 files lack these columns; the decoder defaults them.
            "cooldown_expired_at_anchor_timestamp": CbUint(cooldown or 0),
            "cooldown_expired_at_set": Bool(cooldown is not None),
        }
    )


def _entry_from_value(value: Value) -> OwnerKeyEntry:
    """Decode one OwnerKeyEntry from a canonical-bytes Map.

    v1 → v2 shim: the ``cooldown_expired_at`` columns are OPTIONAL. A v1 entry
    (without them) decodes with ``cooldown_expired_at_anchor_timestamp=None``.
    """
    entry_map = expect_map(value)
    fields = dict(entry_map.value)
    try:
        pubkey_bytes = expect_bytes(fields["public_key"])
        valid_from = expect_uint(fields["valid_from_anchor_timestamp"])
        valid_until_raw = expect_uint(fields["valid_until_anchor_timestamp"])
        valid_until_set = expect_bool(fields["valid_until_set"])
        rot_hash_bytes = expect_bytes(fields["rotation_attestation_hash"])
    except (KeyError, CanonicalBytesError) as e:
        raise OwnerKeysPersistenceError(
            f"OwnerKeyEntry decode error: {e}"
        ) from e
    # C70 (v2) columns — absent in v1 files → None.
    cooldown_expired_at: int | None = None
    if "cooldown_expired_at_set" in fields:
        try:
            cooldown_set = expect_bool(fields["cooldown_expired_at_set"])
            cooldown_raw = expect_uint(
                fields["cooldown_expired_at_anchor_timestamp"]
            )
        except (KeyError, CanonicalBytesError) as e:
            raise OwnerKeysPersistenceError(
                f"OwnerKeyEntry cooldown_expired_at decode error: {e}"
            ) from e
        cooldown_expired_at = int(cooldown_raw) if cooldown_set else None
    return OwnerKeyEntry(
        public_key=Ed25519PublicKey(pubkey_bytes),
        valid_from_anchor_timestamp=int(valid_from),
        valid_until_anchor_timestamp=(
            int(valid_until_raw) if valid_until_set else None
        ),
        rotation_attestation_canonical_bytes_hash=(
            rot_hash_bytes if rot_hash_bytes else None
        ),
        cooldown_expired_at_anchor_timestamp=cooldown_expired_at,
    )


def owner_keys_to_canonical_bytes(history: OwnerKeyHistory) -> bytes:
    """Encode an :class:`OwnerKeyHistory` as canonical bytes (M10)."""
    active_prefix_array = Array(
        tuple(_entry_to_value(e) for e in history.active_prefix)
    )
    active_extra_array = Array(
        tuple(_entry_to_value(e) for e in history.active_extra_valid)
    )
    archived_array = Array(
        tuple(_entry_to_value(e) for e in history.archived_tail)
    )
    out = CbMap.from_dict(
        {
            "format_version": CbUint(OWNER_KEYS_FORMAT_VERSION),
            "k": CbUint(history.k),
            "active_prefix": active_prefix_array,
            "active_extra_valid": active_extra_array,
            "archived_tail": archived_array,
        }
    )
    return encode(out).bytes_


def owner_keys_from_canonical_bytes(data: bytes) -> OwnerKeyHistory | None:
    """Decode an OwnerKeyHistory from canonical bytes.

    Accepts format versions 1 and 2 (the C70 v1 → v2 shim handles the absent
    ``cooldown_expired_at`` columns per-entry). Returns ``None`` on a
    higher-than-supported version (forward-incompatible). Raises on malformed
    data.
    """
    try:
        decoded = decode(data)
    except CanonicalBytesError as e:
        raise OwnerKeysPersistenceError(
            f"owner_keys decode failed: {e}"
        ) from e
    root_map = expect_map(decoded)
    fields = dict(root_map.value)
    try:
        version = expect_uint(fields["format_version"])
    except (KeyError, CanonicalBytesError) as e:
        raise OwnerKeysPersistenceError(
            f"owner_keys missing format_version: {e}"
        ) from e
    if version not in (1, OWNER_KEYS_FORMAT_VERSION):
        return None
    try:
        k = expect_uint(fields["k"])
        active_prefix_array = expect_array(fields["active_prefix"])
        active_extra_array = expect_array(fields["active_extra_valid"])
        archived_array = expect_array(fields["archived_tail"])
    except (KeyError, CanonicalBytesError) as e:
        raise OwnerKeysPersistenceError(
            f"owner_keys missing required field: {e}"
        ) from e

    history = OwnerKeyHistory(k=int(k))
    history.active_prefix = [_entry_from_value(v) for v in active_prefix_array]
    history.active_extra_valid = [
        _entry_from_value(v) for v in active_extra_array
    ]
    history.archived_tail = [_entry_from_value(v) for v in archived_array]
    return history


def save_owner_key_history(
    history: OwnerKeyHistory, state_dir: str | Path
) -> None:
    """Atomically write owner-key history to ``<state_dir>/owner_keys.cb``."""
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    target = state_path / OWNER_KEYS_FILENAME
    tmp = state_path / f"{OWNER_KEYS_FILENAME}.tmp"
    data = owner_keys_to_canonical_bytes(history)
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


def load_owner_key_history(
    state_dir: str | Path,
) -> OwnerKeyHistory | None:
    """Load owner-key history from ``<state_dir>/owner_keys.cb``.

    Returns ``None`` if the file does not exist OR is incompatible.
    Raises :class:`OwnerKeysPersistenceError` on malformed data.
    """
    state_path = Path(state_dir)
    target = state_path / OWNER_KEYS_FILENAME
    if not target.exists():
        return None
    with open(target, "rb") as f:
        data = f.read()
    return owner_keys_from_canonical_bytes(data)
