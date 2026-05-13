"""Owner-key history — Python implementation (L1_GOVERNANCE §3.1).

The substrate's identity record carries ``owner_key_history`` — a
chronological list of owner public keys with their validity windows. Per
L1_HARD_RULES F3: this field is a contract-identity-level fixed point.

## Active-prefix + archived-tail discipline (per pass-3 saprotroph-1)

Per L1_GOVERNANCE §3.1: monotone tier-1 fields grow unbounded over a
substrate's lifetime. To keep per-cycle validation O(1) regardless of
substrate age:

- **active_prefix** (most-recent K entries) — participates in per-cycle
  tier-1 validation.
- **archived_tail** (older entries) — validated at deep-cycle scope via
  Merkle anchor over the full chain.

Same discipline applies to ``template_version_registry`` (L1_TROPISM §B1)
and the federation peer-set aggregate-reattestation chain (L1_GOVERNANCE §5.2).
The Rust `kernel/shared::active_prefix` module implements the generic
container; this Python module implements an owner-keys-specific variant.

## M2 scope

- Single-key minimum: stores 1+ Ed25519 public keys with validity windows.
- Lookup by anchor-surface timestamp: returns the key active at that moment.
- Append-only: new keys added via ``add_key`` (production: gated by CI
  attestation through the classifier + attestation envelope).

## M3+ deferred

- Full rotation FSM with 30-day cooldown veto window (L1_GOVERNANCE §3.1).
- Owner-succession protocol (L1_GOVERNANCE §3.2; "deferred to L4 as a
  concrete operational protocol, after first real-world need").
- Cryptographic suite rotation (same FSM pattern; M3+).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, Optional

from myco_kernel_governance.crypto import Ed25519PublicKey


@dataclass(frozen=True, slots=True)
class OwnerKeyEntry:
    """One entry in the owner-key history (L1_GOVERNANCE §3.1).

    Fields
    ------
    public_key:
        The Ed25519 public key.
    valid_from_anchor_timestamp:
        Unix-seconds anchor-surface trusted timestamp when this key became
        active. Per L1_GOVERNANCE §3.1 the substrate cannot author
        timestamps; they originate at the anchor surface.
    valid_until_anchor_timestamp:
        Unix-seconds timestamp when this key was retired (or ``None`` if
        still currently valid; the "active" key has no end timestamp).
    rotation_attestation_canonical_bytes_hash:
        Hash of the canonical-bytes of the rotation attestation that
        introduced this key (M3+ field; M2 may set to None for the
        bootstrap-genesis key).
    """

    public_key: Ed25519PublicKey
    valid_from_anchor_timestamp: int
    valid_until_anchor_timestamp: Optional[int] = None
    rotation_attestation_canonical_bytes_hash: Optional[bytes] = None

    def is_active_at(self, anchor_timestamp_unix_seconds: int) -> bool:
        """Whether this key was active at the given anchor-surface timestamp.

        Key is active iff:
            valid_from_anchor_timestamp <= timestamp < valid_until_anchor_timestamp
        (or valid_until is None, meaning currently-active).
        """
        if anchor_timestamp_unix_seconds < self.valid_from_anchor_timestamp:
            return False
        if (
            self.valid_until_anchor_timestamp is not None
            and anchor_timestamp_unix_seconds >= self.valid_until_anchor_timestamp
        ):
            return False
        return True

    def is_currently_valid(self) -> bool:
        """Whether this key has no end timestamp set (i.e., is the active key)."""
        return self.valid_until_anchor_timestamp is None


# Default active-prefix cap from L1_GOVERNANCE §3.1.
DEFAULT_ACTIVE_PREFIX_K: Final[int] = 8


class OwnerKeyHistoryError(Exception):
    """Owner-key-history operation error."""


class NoActiveKey(OwnerKeyHistoryError):
    """No owner key is active at the queried anchor-surface timestamp."""


class HistoryEmpty(OwnerKeyHistoryError):
    """The owner-key history is empty (no genesis entry yet)."""


@dataclass(slots=True)
class OwnerKeyHistory:
    """Owner-key history with active-prefix + archived-tail discipline.

    M2 scope: keeps all entries in-memory. M3+ wires persistence via
    kernel/schema SSoT.
    """

    active_prefix: list[OwnerKeyEntry] = field(default_factory=list)
    """Most-recent K entries (chronological order, oldest first)."""

    active_extra_valid: list[OwnerKeyEntry] = field(default_factory=list)
    """Currently-valid entries older than K. Conceptually part of the
    active prefix for validation purposes; stored separately for clarity."""

    archived_tail: list[OwnerKeyEntry] = field(default_factory=list)
    """Cold-tier-eligible older entries (no longer valid; archived chain)."""

    k: int = DEFAULT_ACTIVE_PREFIX_K
    """Active-prefix cap; L4-tunable per L1_GOVERNANCE §3.1."""

    def add_key(self, entry: OwnerKeyEntry) -> None:
        """Append a new owner key entry to the history.

        Asserts chronological order: the new entry's valid_from must be >=
        the most recent entry's valid_from. Per L1_GOVERNANCE §3.1: rotation
        protocol (cooldown + veto) is enforced UPSTREAM of this call (M3+
        attestation flow); this module is the storage primitive.
        """
        if self.active_prefix or self.active_extra_valid or self.archived_tail:
            most_recent_ts = self._most_recent_valid_from()
            if entry.valid_from_anchor_timestamp < most_recent_ts:
                raise OwnerKeyHistoryError(
                    f"new entry valid_from {entry.valid_from_anchor_timestamp} predates "
                    f"most-recent {most_recent_ts}"
                )

        self.active_prefix.append(entry)
        if len(self.active_prefix) > self.k:
            evicted = self.active_prefix.pop(0)
            if evicted.is_currently_valid():
                self.active_extra_valid.append(evicted)
            else:
                self.archived_tail.append(evicted)

    def active_at(self, anchor_timestamp_unix_seconds: int) -> Ed25519PublicKey:
        """Return the owner public key active at the given anchor-surface timestamp.

        Per L1_GOVERNANCE §2.3 step 2: substrate verifies owner signatures
        against the key valid at the attestation's anchor-surface timestamp.

        Raises:
            NoActiveKey: no key in the history covers the timestamp.
            HistoryEmpty: the history is empty.
        """
        if not (self.active_prefix or self.active_extra_valid or self.archived_tail):
            raise HistoryEmpty("owner_key_history is empty")

        for entry in self._iter_all():
            if entry.is_active_at(anchor_timestamp_unix_seconds):
                return entry.public_key

        raise NoActiveKey(
            f"no owner key was active at anchor-surface timestamp "
            f"{anchor_timestamp_unix_seconds}"
        )

    def current_active(self) -> Ed25519PublicKey:
        """Return the currently-active owner key (the entry with no end timestamp).

        Raises:
            NoActiveKey: no currently-valid key.
            HistoryEmpty: the history is empty.
        """
        if not (self.active_prefix or self.active_extra_valid):
            if not self.archived_tail:
                raise HistoryEmpty("owner_key_history is empty")
            raise NoActiveKey("no currently-valid owner key (all entries archived)")

        for entry in self._iter_active_layer():
            if entry.is_currently_valid():
                return entry.public_key

        raise NoActiveKey("no currently-valid owner key (all entries have valid_until)")

    def total_count(self) -> int:
        """Total entries across all layers."""
        return (
            len(self.active_prefix)
            + len(self.active_extra_valid)
            + len(self.archived_tail)
        )

    def active_layer_count(self) -> int:
        """Entries in the active-prefix + active-extra-valid layers
        (the set participating in per-cycle tier-1 validation)."""
        return len(self.active_prefix) + len(self.active_extra_valid)

    def archived_count(self) -> int:
        """Entries in the cold-tier-eligible archived_tail."""
        return len(self.archived_tail)

    def _iter_all(self) -> "Iterator[OwnerKeyEntry]":  # noqa: F821
        """Iterate all entries (active + extra + archived) in storage order."""
        yield from self.active_extra_valid
        yield from self.active_prefix
        yield from self.archived_tail

    def _iter_active_layer(self) -> "Iterator[OwnerKeyEntry]":  # noqa: F821
        yield from self.active_extra_valid
        yield from self.active_prefix

    def _most_recent_valid_from(self) -> int:
        """Greatest valid_from across all stored entries."""
        max_ts = 0
        for e in self._iter_all():
            if e.valid_from_anchor_timestamp > max_ts:
                max_ts = e.valid_from_anchor_timestamp
        return max_ts


def init_with_genesis_key(
    genesis_key: Ed25519PublicKey,
    genesis_anchor_timestamp_unix_seconds: int,
    k: int = DEFAULT_ACTIVE_PREFIX_K,
) -> OwnerKeyHistory:
    """Initialize an owner-key history with the genesis key as the only entry.

    Per L1_GOVERNANCE §4.1 step 5: the owner signs the substrate-ID tuple
    at genesis (the birth attestation). The genesis key is the first entry
    in owner_key_history with no valid_until.
    """
    history = OwnerKeyHistory(k=k)
    history.add_key(
        OwnerKeyEntry(
            public_key=genesis_key,
            valid_from_anchor_timestamp=genesis_anchor_timestamp_unix_seconds,
        )
    )
    return history
