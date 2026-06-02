"""Owner-key history — Python implementation (L1/GOVERNANCE §3.1).

The substrate's identity record carries ``owner_key_history`` — a
chronological list of owner public keys with their validity windows. Per
L1/HARD_RULES F3: this field is a contract-identity-level fixed point.

## Active-prefix + archived-tail discipline (per pass-3 saprotroph-1)

Per L1/GOVERNANCE §3.1: monotone tier-1 fields grow unbounded over a
substrate's lifetime. To keep per-cycle validation O(1) regardless of
substrate age:

- **active_prefix** (most-recent K entries) — participates in per-cycle
  tier-1 validation.
- **archived_tail** (older entries) — validated at deep-cycle scope via
  Merkle anchor over the full chain.

Same discipline applies to ``template_version_registry`` (L1/TROPISM §B1)
and the federation peer-set aggregate-reattestation chain (L1/GOVERNANCE §5.2).
The Rust `kernel/shared::active_prefix` module implements the generic
container; this Python module implements an owner-keys-specific variant.

## M2 scope

- Single-key minimum: stores 1+ Ed25519 public keys with validity windows.
- Lookup by anchor-surface timestamp: returns the key active at that moment.
- Append-only: new keys added via ``add_key`` (production: gated by CI
  attestation through the classifier + attestation envelope).

## C70 rotation FSM

- The 3-state rotation FSM with the 30-anchor-day cooldown veto window
  (L1/GOVERNANCE §3.1) is implemented in :class:`RotationFSM`. The Rust
  substrate drives it end-to-end (request → cooldown → dual-cosign activate);
  this module's :class:`RotationFSM` is the storage-side helper that applies a
  completed rotation onto an :class:`OwnerKeyHistory` (add the new key, set the
  old key's ``valid_until`` + ``cooldown_expired_at``).

## M3+ deferred

- n-of-m multisig + quorum-emergency cooldown-bypass (L2/TRUST_MODEL §10.A.1).
- Owner-succession protocol (L1/GOVERNANCE §3.2; "deferred to L4 as a
  concrete operational protocol, after first real-world need").
- Cryptographic suite rotation (same FSM pattern; M3+).
"""

from __future__ import annotations

import enum
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from typing import Final

from myco_kernel_governance.crypto import Ed25519PublicKey


@dataclass(frozen=True, slots=True)
class OwnerKeyEntry:
    """One entry in the owner-key history (L1/GOVERNANCE §3.1).

    Fields
    ------
    public_key:
        The Ed25519 public key.
    valid_from_anchor_timestamp:
        Unix-seconds anchor-surface trusted timestamp when this key became
        active. Per L1/GOVERNANCE §3.1 the substrate cannot author
        timestamps; they originate at the anchor surface.
    valid_until_anchor_timestamp:
        Unix-seconds timestamp when this key was retired (or ``None`` if
        still currently valid; the "active" key has no end timestamp).
    rotation_attestation_canonical_bytes_hash:
        Hash of the canonical-bytes of the rotation attestation that
        introduced this key (M3+ field; M2 may set to None for the
        bootstrap-genesis key).
    cooldown_expired_at_anchor_timestamp:
        C70: the anchor-surface timestamp at which the 30-day cooldown veto
        window for the rotation that RETIRED this key elapsed (i.e. the moment
        the successor became eligible for dual-cosign activation). Set on the
        OUTGOING key when its successor activates; ``None`` for a key that has
        not been retired (the active key) or for the genesis key. Persisted as
        the GOVERNANCE §3.1 ``cooldown_expired_at`` history column.
    """

    public_key: Ed25519PublicKey
    valid_from_anchor_timestamp: int
    valid_until_anchor_timestamp: int | None = None
    rotation_attestation_canonical_bytes_hash: bytes | None = None
    cooldown_expired_at_anchor_timestamp: int | None = None

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


# Default active-prefix cap from L1/GOVERNANCE §3.1.
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
    """Active-prefix cap; L4-tunable per L1/GOVERNANCE §3.1."""

    def add_key(self, entry: OwnerKeyEntry) -> None:
        """Append a new owner key entry to the history.

        Asserts chronological order: the new entry's valid_from must be >=
        the most recent entry's valid_from. Per L1/GOVERNANCE §3.1: rotation
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

    def retire_active_key(
        self,
        retired_public_key: Ed25519PublicKey,
        valid_until_anchor_timestamp: int,
        cooldown_expired_at_anchor_timestamp: int,
    ) -> None:
        """C70: close out the currently-active key on rotation activation.

        Locates the currently-valid (``valid_until is None``) entry whose
        public key matches ``retired_public_key`` and stamps it with both the
        retirement instant (``valid_until``) and the moment the 30-day cooldown
        veto window for its successor elapsed (``cooldown_expired_at``). Entries
        are frozen, so the matched entry is replaced in place within its layer.

        Raises:
            NoActiveKey: no currently-valid entry matches ``retired_public_key``.
        """
        target_bytes = retired_public_key.bytes_
        for layer in (self.active_prefix, self.active_extra_valid):
            for i, e in enumerate(layer):
                if e.is_currently_valid() and e.public_key.bytes_ == target_bytes:
                    layer[i] = replace(
                        e,
                        valid_until_anchor_timestamp=valid_until_anchor_timestamp,
                        cooldown_expired_at_anchor_timestamp=(
                            cooldown_expired_at_anchor_timestamp
                        ),
                    )
                    return
        raise NoActiveKey(
            "retire_active_key: no currently-valid entry matches the "
            "retired public key"
        )

    def active_at(self, anchor_timestamp_unix_seconds: int) -> Ed25519PublicKey:
        """Return the owner public key active at the given anchor-surface timestamp.

        Per L1/GOVERNANCE §2.3 step 2: substrate verifies owner signatures
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

    def _iter_all(self) -> Iterator[OwnerKeyEntry]:
        """Iterate all entries (active + extra + archived) in storage order."""
        yield from self.active_extra_valid
        yield from self.active_prefix
        yield from self.archived_tail

    def _iter_active_layer(self) -> Iterator[OwnerKeyEntry]:
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

    Per L1/GOVERNANCE §4.1 step 5: the owner signs the substrate-ID tuple
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


# ---------------------------------------------------------------------------
# C70 — owner key-rotation FSM (L1/GOVERNANCE §3.1).
# ---------------------------------------------------------------------------

#: The cooldown veto window, in anchor-surface seconds (30 anchor-days). Per
#: L1/GOVERNANCE §3.1 a freshly-requested rotation may NOT activate until this
#: window has elapsed, during which any pre-registered key may veto. The Rust
#: substrate holds the authoritative copy (``OWNER_KEY_ROTATION_COOLDOWN_SECS``);
#: this mirror keeps the pure-Python FSM self-contained for unit testing.
COOLDOWN_ANCHOR_SECONDS: Final[int] = 30 * 24 * 60 * 60  # 2_592_000


class RotationState(enum.Enum):
    """The three states of a single owner key-rotation (L1/GOVERNANCE §3.1)."""

    NONE = "none"
    """No rotation in flight."""

    PENDING_COOLDOWN = "pending_cooldown"
    """A new candidate was requested (current-key-signed); the 30-day veto
    window is open. Any pre-registered key MAY veto; the candidate MAY activate
    once the cooldown has elapsed (dual-cosign)."""

    VETOED = "vetoed"
    """A pre-registered key vetoed within the window; the candidate is discarded
    (terminal)."""

    ACTIVATED = "activated"
    """The dual-cosign activation succeeded post-cooldown; the new key is the
    active owner key (terminal)."""


class RotationError(OwnerKeyHistoryError):
    """An owner key-rotation transition was attempted out of order or against a
    violated guard (e.g. activation before the cooldown elapsed → the C70
    condition; veto without a pending rotation)."""


@dataclass(slots=True)
class RotationFSM:
    """Pure 3-state FSM for one owner key-rotation (L1/GOVERNANCE §3.1).

    This is the storage-side mirror of the authoritative Rust substrate FSM. It
    models the request → cooldown → veto/activate transitions so the cooldown,
    veto-window, and single-in-flight guards are unit-testable in isolation, and
    :meth:`apply_activation` performs the actual :class:`OwnerKeyHistory`
    mutation an accepted activation entails (add the new key; retire the old key
    with its ``valid_until`` + ``cooldown_expired_at``).

    Anchor-time is operator-supplied (the substrate trusts the envelope's
    ``anchor_timestamp_unix_seconds`` at this MVP; full F4 anchor-signature
    closure is follow-up). All timestamps are anchor-surface unix seconds.
    """

    state: RotationState = RotationState.NONE
    new_public_key: Ed25519PublicKey | None = None
    prior_public_key: Ed25519PublicKey | None = None
    request_anchor_timestamp: int | None = None
    cooldown_expires_at_anchor_timestamp: int | None = None

    def request(
        self,
        prior_public_key: Ed25519PublicKey,
        new_public_key: Ed25519PublicKey,
        request_anchor_timestamp: int,
    ) -> int:
        """Open a rotation: PENDING_COOLDOWN. Returns ``cooldown_expires_at``.

        Single-in-flight: a request while one is already PENDING_COOLDOWN is a
        :class:`RotationError`. A no-op rotation (``new == prior``) is refused.
        """
        if self.state is RotationState.PENDING_COOLDOWN:
            raise RotationError(
                "a rotation is already pending (single-in-flight); veto or "
                "activate it before requesting another"
            )
        if new_public_key.bytes_ == prior_public_key.bytes_:
            raise RotationError(
                "rotation request: new_public_key equals prior_public_key "
                "(no-op rotation refused)"
            )
        self.state = RotationState.PENDING_COOLDOWN
        self.prior_public_key = prior_public_key
        self.new_public_key = new_public_key
        self.request_anchor_timestamp = request_anchor_timestamp
        self.cooldown_expires_at_anchor_timestamp = (
            request_anchor_timestamp + COOLDOWN_ANCHOR_SECONDS
        )
        return self.cooldown_expires_at_anchor_timestamp

    def veto(self, veto_anchor_timestamp: int) -> None:
        """Veto a pending rotation within the window → VETOED (terminal).

        Requires a PENDING_COOLDOWN rotation. A veto at/after the cooldown
        expiry is moot (the window is closed) → :class:`RotationError`.
        """
        if self.state is not RotationState.PENDING_COOLDOWN:
            raise RotationError("veto requires a pending rotation")
        assert self.cooldown_expires_at_anchor_timestamp is not None
        if veto_anchor_timestamp >= self.cooldown_expires_at_anchor_timestamp:
            raise RotationError(
                "veto after the cooldown window elapsed is moot "
                "(window already closed)"
            )
        self.state = RotationState.VETOED

    def activate(self, activate_anchor_timestamp: int) -> None:
        """Activate a pending rotation post-cooldown → ACTIVATED (terminal).

        Requires a PENDING_COOLDOWN rotation. Activation BEFORE the cooldown
        elapses is the **C70** ``rotation_veto_window_violation`` condition and
        raises :class:`RotationError`. Activation that runs the clock BACKWARD
        relative to the request is also refused.

        Note: the dual-cosignature verification is the SUBSTRATE's
        responsibility (it holds the new-key cosignature + the Ed25519 verify);
        this FSM models only the cooldown/state guards.
        """
        if self.state is not RotationState.PENDING_COOLDOWN:
            raise RotationError("activate requires a pending rotation")
        assert self.cooldown_expires_at_anchor_timestamp is not None
        assert self.request_anchor_timestamp is not None
        if activate_anchor_timestamp < self.request_anchor_timestamp:
            raise RotationError(
                "activation anchor timestamp runs backward relative to the "
                "request"
            )
        if activate_anchor_timestamp < self.cooldown_expires_at_anchor_timestamp:
            raise RotationError(
                "C70 rotation_veto_window_violation: activation attempted "
                f"at {activate_anchor_timestamp} before the cooldown expires "
                f"at {self.cooldown_expires_at_anchor_timestamp} "
                "(30-day veto window not elapsed)"
            )
        self.state = RotationState.ACTIVATED

    def apply_activation(
        self,
        history: OwnerKeyHistory,
        activate_anchor_timestamp: int,
        rotation_attestation_canonical_bytes_hash: bytes | None = None,
    ) -> None:
        """Mutate ``history`` to reflect an ACTIVATED rotation.

        Retires the prior (currently-active) key — stamping its ``valid_until``
        = the new key's ``valid_from`` = ``activate_anchor_timestamp`` and its
        ``cooldown_expired_at`` = the rotation's ``cooldown_expires_at`` — and
        adds the new key as the now-active entry. Must be called only after
        :meth:`activate` has moved the FSM to ACTIVATED.

        Raises:
            RotationError: the FSM is not in the ACTIVATED state.
        """
        if self.state is not RotationState.ACTIVATED:
            raise RotationError(
                "apply_activation requires the FSM to be ACTIVATED"
            )
        assert self.prior_public_key is not None
        assert self.new_public_key is not None
        assert self.cooldown_expires_at_anchor_timestamp is not None
        history.retire_active_key(
            retired_public_key=self.prior_public_key,
            valid_until_anchor_timestamp=activate_anchor_timestamp,
            cooldown_expired_at_anchor_timestamp=(
                self.cooldown_expires_at_anchor_timestamp
            ),
        )
        history.add_key(
            OwnerKeyEntry(
                public_key=self.new_public_key,
                valid_from_anchor_timestamp=activate_anchor_timestamp,
                rotation_attestation_canonical_bytes_hash=(
                    rotation_attestation_canonical_bytes_hash
                ),
            )
        )
