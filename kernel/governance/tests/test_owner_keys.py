"""Tests for owner-key history (L1_GOVERNANCE §3.1)."""

from __future__ import annotations

import pytest

from myco_kernel_governance.crypto import Ed25519PrivateKey
from myco_kernel_governance.owner_keys import (
    DEFAULT_ACTIVE_PREFIX_K,
    HistoryEmpty,
    NoActiveKey,
    OwnerKeyEntry,
    OwnerKeyHistory,
    OwnerKeyHistoryError,
    init_with_genesis_key,
)


def _key(seed_byte: int):
    return Ed25519PrivateKey.from_seed(bytes([seed_byte] * 32)).public_key()


# ---------------------------------------------------------------------------
# Genesis initialization.
# ---------------------------------------------------------------------------


def test_init_with_genesis_key() -> None:
    genesis_pub = _key(0x01)
    history = init_with_genesis_key(genesis_pub, genesis_anchor_timestamp_unix_seconds=100)
    assert history.total_count() == 1
    assert history.active_layer_count() == 1
    assert history.archived_count() == 0
    assert history.current_active() == genesis_pub


def test_empty_history_raises() -> None:
    history = OwnerKeyHistory()
    with pytest.raises(HistoryEmpty):
        history.current_active()
    with pytest.raises(HistoryEmpty):
        history.active_at(100)


# ---------------------------------------------------------------------------
# active_at — lookup by anchor-surface timestamp.
# ---------------------------------------------------------------------------


def test_active_at_genesis_timestamp() -> None:
    pub = _key(0x01)
    history = init_with_genesis_key(pub, 100)
    assert history.active_at(100) == pub
    assert history.active_at(1000) == pub


def test_active_at_before_genesis_raises() -> None:
    pub = _key(0x01)
    history = init_with_genesis_key(pub, 100)
    with pytest.raises(NoActiveKey):
        history.active_at(50)  # before genesis


def test_active_at_with_rotation() -> None:
    """After rotation, active_at returns the key valid at the queried timestamp."""
    pub1 = _key(0x01)
    pub2 = _key(0x02)

    history = init_with_genesis_key(pub1, 100)
    # Rotate at t=200: close pub1's window and add pub2.
    # M2 model: we don't have a rotate() method yet; manually update.
    # In M3 this would be wrapped in a rotate() with cooldown + veto.
    closed_entry = OwnerKeyEntry(
        public_key=pub1,
        valid_from_anchor_timestamp=100,
        valid_until_anchor_timestamp=200,
    )
    # Rebuild history with the closed entry first, then pub2.
    history = OwnerKeyHistory()
    history.add_key(closed_entry)
    history.add_key(
        OwnerKeyEntry(public_key=pub2, valid_from_anchor_timestamp=200)
    )

    # Queries within pub1's window return pub1.
    assert history.active_at(150) == pub1
    # Queries within pub2's window return pub2.
    assert history.active_at(250) == pub2
    # Boundary: at t=200 pub2 is active (valid_from is inclusive).
    assert history.active_at(200) == pub2


# ---------------------------------------------------------------------------
# Chronological-order enforcement.
# ---------------------------------------------------------------------------


def test_add_key_out_of_order_rejected() -> None:
    pub1 = _key(0x01)
    pub2 = _key(0x02)
    history = init_with_genesis_key(pub1, 200)
    with pytest.raises(OwnerKeyHistoryError, match="predates"):
        history.add_key(
            OwnerKeyEntry(public_key=pub2, valid_from_anchor_timestamp=100)
        )


# ---------------------------------------------------------------------------
# Active-prefix + archived-tail discipline.
# ---------------------------------------------------------------------------


def test_active_prefix_caps_at_k_with_invalid_entries() -> None:
    """Insert 10 keys, each with valid_until set (so they become invalid).
    Active prefix should cap at K (default 8); the rest go to archived_tail.
    """
    history = OwnerKeyHistory(k=DEFAULT_ACTIVE_PREFIX_K)
    for i in range(10):
        # Each key valid from t=i*100 to t=(i+1)*100 (then becomes invalid).
        entry = OwnerKeyEntry(
            public_key=_key(0x10 + i),
            valid_from_anchor_timestamp=i * 100,
            valid_until_anchor_timestamp=(i + 1) * 100,
        )
        history.add_key(entry)

    # All 10 inserted.
    assert history.total_count() == 10
    # Active prefix capped at K=8.
    assert len(history.active_prefix) == DEFAULT_ACTIVE_PREFIX_K
    # The 2 evicted (oldest) → archived_tail (none are currently valid).
    assert history.archived_count() == 10 - DEFAULT_ACTIVE_PREFIX_K
    assert len(history.active_extra_valid) == 0


def test_currently_valid_entry_stays_active_when_evicted_from_prefix() -> None:
    """A currently-valid entry (no valid_until) older than K stays in
    active_extra_valid, not archived."""
    history = OwnerKeyHistory(k=2)
    # Insert one currently-valid entry then K=2 more without valid_until is
    # nonsensical (multiple currently-valid simultaneously isn't allowed in
    # production); for the test we use valid_until on the later ones.
    history.add_key(OwnerKeyEntry(public_key=_key(0x01), valid_from_anchor_timestamp=100))
    # Subsequent entries close earlier windows.
    history.add_key(
        OwnerKeyEntry(
            public_key=_key(0x02),
            valid_from_anchor_timestamp=200,
            valid_until_anchor_timestamp=300,
        )
    )
    history.add_key(
        OwnerKeyEntry(
            public_key=_key(0x03),
            valid_from_anchor_timestamp=300,
            valid_until_anchor_timestamp=400,
        )
    )
    history.add_key(
        OwnerKeyEntry(
            public_key=_key(0x04),
            valid_from_anchor_timestamp=400,
            valid_until_anchor_timestamp=500,
        )
    )

    # K=2 means active_prefix has the 2 most-recent.
    # 0x01 entry got evicted but is currently-valid (no valid_until set) →
    # should be in active_extra_valid, not archived.
    # Actually wait: 0x01 has no valid_until so is_currently_valid()=True.
    # Let me trace:
    #   insert 0x01: active=[0x01]
    #   insert 0x02: active=[0x01, 0x02]; len=2==K; no eviction
    #   insert 0x03: active=[0x01, 0x02, 0x03]; len=3>K; evict 0x01;
    #                0x01.is_currently_valid()==True → active_extra_valid=[0x01]
    #   insert 0x04: active=[0x02, 0x03, 0x04]; len=3>K; evict 0x02;
    #                0x02.is_currently_valid()==False → archived=[0x02]
    assert history.active_layer_count() == 3  # [0x03, 0x04] in active + [0x01] in extra
    assert history.archived_count() == 1
    assert history.total_count() == 4

    # 0x01 still queryable via active_at:
    assert history.active_at(150) == _key(0x01)


# ---------------------------------------------------------------------------
# current_active behavior.
# ---------------------------------------------------------------------------


def test_current_active_returns_no_valid_until_entry() -> None:
    pub1 = _key(0x01)
    pub2 = _key(0x02)
    history = OwnerKeyHistory()
    history.add_key(
        OwnerKeyEntry(
            public_key=pub1, valid_from_anchor_timestamp=100, valid_until_anchor_timestamp=200
        )
    )
    history.add_key(OwnerKeyEntry(public_key=pub2, valid_from_anchor_timestamp=200))
    assert history.current_active() == pub2


def test_current_active_no_open_entry_raises() -> None:
    pub = _key(0x01)
    history = OwnerKeyHistory()
    history.add_key(
        OwnerKeyEntry(
            public_key=pub,
            valid_from_anchor_timestamp=100,
            valid_until_anchor_timestamp=200,
        )
    )
    with pytest.raises(NoActiveKey, match="no currently-valid"):
        history.current_active()


# ---------------------------------------------------------------------------
# OwnerKeyEntry behavior.
# ---------------------------------------------------------------------------


def test_owner_key_entry_is_active_at() -> None:
    entry = OwnerKeyEntry(
        public_key=_key(0x01),
        valid_from_anchor_timestamp=100,
        valid_until_anchor_timestamp=200,
    )
    assert not entry.is_active_at(50)
    assert entry.is_active_at(100)  # valid_from inclusive
    assert entry.is_active_at(150)
    assert not entry.is_active_at(200)  # valid_until exclusive
    assert not entry.is_active_at(250)


def test_owner_key_entry_open_window() -> None:
    """Entry with no valid_until is active from valid_from onward indefinitely."""
    entry = OwnerKeyEntry(
        public_key=_key(0x01),
        valid_from_anchor_timestamp=100,
    )
    assert entry.is_currently_valid()
    assert entry.is_active_at(100)
    assert entry.is_active_at(10_000_000_000)  # far future
    assert not entry.is_active_at(50)  # before valid_from
