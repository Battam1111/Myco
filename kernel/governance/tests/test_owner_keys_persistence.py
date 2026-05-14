"""Tests for owner_keys persistence (M10)."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco_kernel_governance.crypto import Ed25519PublicKey
from myco_kernel_governance.owner_keys import (
    OwnerKeyEntry,
    OwnerKeyHistory,
    init_with_genesis_key,
)
from myco_kernel_governance.owner_keys_persistence import (
    OWNER_KEYS_FILENAME,
    OWNER_KEYS_FORMAT_VERSION,
    OwnerKeysPersistenceError,
    load_owner_key_history,
    owner_keys_from_canonical_bytes,
    owner_keys_to_canonical_bytes,
    save_owner_key_history,
)


def _pubkey(byte: int) -> Ed25519PublicKey:
    return Ed25519PublicKey(bytes([byte] * 32))


def test_empty_history_roundtrips() -> None:
    h_in = OwnerKeyHistory()
    data = owner_keys_to_canonical_bytes(h_in)
    h_out = owner_keys_from_canonical_bytes(data)
    assert h_out is not None
    assert h_out.total_count() == 0


def test_genesis_history_roundtrips() -> None:
    h_in = init_with_genesis_key(_pubkey(0xAA), 1700000000)
    data = owner_keys_to_canonical_bytes(h_in)
    h_out = owner_keys_from_canonical_bytes(data)
    assert h_out is not None
    assert h_out.total_count() == 1
    assert h_out.current_active().bytes_ == _pubkey(0xAA).bytes_


def test_multi_key_history_roundtrips() -> None:
    h_in = init_with_genesis_key(_pubkey(0xAA), 1000)
    # Retire the genesis key (set its valid_until).
    h_in.active_prefix[0] = OwnerKeyEntry(
        public_key=_pubkey(0xAA),
        valid_from_anchor_timestamp=1000,
        valid_until_anchor_timestamp=2000,
    )
    # Add a second key, active from 2000.
    h_in.add_key(
        OwnerKeyEntry(public_key=_pubkey(0xBB), valid_from_anchor_timestamp=2000)
    )

    data = owner_keys_to_canonical_bytes(h_in)
    h_out = owner_keys_from_canonical_bytes(data)
    assert h_out is not None
    assert h_out.total_count() == 2
    assert h_out.current_active().bytes_ == _pubkey(0xBB).bytes_
    # Key 0xAA is still active at timestamp 1500 (between valid_from + valid_until).
    assert h_out.active_at(1500).bytes_ == _pubkey(0xAA).bytes_


def test_active_prefix_eviction_roundtrips() -> None:
    """When more than k keys exist, older ones evict to archived_tail or
    active_extra_valid. Persistence must preserve all three layers."""
    h_in = OwnerKeyHistory(k=2)
    # Add 4 keys; some retired (valid_until set), some still active.
    h_in.add_key(
        OwnerKeyEntry(
            public_key=_pubkey(0x01),
            valid_from_anchor_timestamp=1000,
            valid_until_anchor_timestamp=2000,
        )
    )
    h_in.add_key(
        OwnerKeyEntry(
            public_key=_pubkey(0x02),
            valid_from_anchor_timestamp=2000,
            valid_until_anchor_timestamp=3000,
        )
    )
    h_in.add_key(
        OwnerKeyEntry(public_key=_pubkey(0x03), valid_from_anchor_timestamp=3000)
    )
    h_in.add_key(
        OwnerKeyEntry(public_key=_pubkey(0x04), valid_from_anchor_timestamp=4000)
    )
    assert h_in.total_count() == 4
    # 0x01 should be archived (retired + evicted from prefix when 0x03 was added)
    assert h_in.archived_count() >= 1

    data = owner_keys_to_canonical_bytes(h_in)
    h_out = owner_keys_from_canonical_bytes(data)
    assert h_out is not None
    assert h_out.total_count() == 4
    assert h_out.archived_count() == h_in.archived_count()
    assert h_out.active_layer_count() == h_in.active_layer_count()


def test_save_and_load_via_disk(tmp_path: Path) -> None:
    h_in = init_with_genesis_key(_pubkey(0x42), 1700000000)
    save_owner_key_history(h_in, tmp_path)
    h_out = load_owner_key_history(tmp_path)
    assert h_out is not None
    assert h_out.current_active().bytes_ == _pubkey(0x42).bytes_


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    assert load_owner_key_history(tmp_path) is None


def test_save_is_atomic_no_tmp_leftover(tmp_path: Path) -> None:
    h_in = init_with_genesis_key(_pubkey(0x33), 1000)
    save_owner_key_history(h_in, tmp_path)
    tmp_file = tmp_path / f"{OWNER_KEYS_FILENAME}.tmp"
    target = tmp_path / OWNER_KEYS_FILENAME
    assert not tmp_file.exists()
    assert target.exists()


def test_version_mismatch_returns_none(tmp_path: Path) -> None:
    from myco_kernel_governance.canonical_bytes import (
        Array as CbArray,
        Map as CbMap,
        Uint as CbUint,
        encode,
    )

    bad = CbMap.from_dict(
        {
            "format_version": CbUint(999),
            "k": CbUint(8),
            "active_prefix": CbArray(()),
            "active_extra_valid": CbArray(()),
            "archived_tail": CbArray(()),
        }
    )
    target = tmp_path / OWNER_KEYS_FILENAME
    target.write_bytes(encode(bad).bytes_)
    assert load_owner_key_history(tmp_path) is None


def test_malformed_bytes_raises() -> None:
    with pytest.raises(OwnerKeysPersistenceError):
        owner_keys_from_canonical_bytes(b"not-canonical-bytes")


def test_save_overwrites_existing(tmp_path: Path) -> None:
    h1 = init_with_genesis_key(_pubkey(0x11), 1000)
    save_owner_key_history(h1, tmp_path)
    h2 = init_with_genesis_key(_pubkey(0x22), 2000)
    save_owner_key_history(h2, tmp_path)
    h_out = load_owner_key_history(tmp_path)
    assert h_out is not None
    assert h_out.current_active().bytes_ == _pubkey(0x22).bytes_


def test_format_version_pin() -> None:
    assert OWNER_KEYS_FORMAT_VERSION == 1
