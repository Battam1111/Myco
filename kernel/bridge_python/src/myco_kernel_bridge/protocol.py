"""Bridge wire protocol — message types, body encode/decode, HMAC integrity.

## Wire frame

A bridge message is a length-prefixed frame on stdio::

    [u32 BE length, 4 bytes] [hmac, 32 bytes] [body, length-32 bytes]

Where:

- ``length`` is the size of ``hmac + body`` (so the body alone is ``length - 32``).
- ``hmac`` is HMAC-SHA256 over the body bytes, keyed by ``session_secret``
  (or ``BOOTSTRAP_KEY`` for the ``hello`` message).
- ``body`` is the canonical-bytes encoding of a :class:`Map` with four keys
  (``v``, ``type``, ``request_id``, ``payload``), canonically sorted.

This module ships:

- :class:`MessageType` — string-enum of all M5 message types.
- :class:`Message` — typed message data carrier (type + request_id + payload Map).
- :func:`body_to_canonical_bytes` / :func:`canonical_bytes_to_body` — encode/decode
  the body Map portion.
- :func:`encode_message` / :func:`decode_message` — encode/decode a full frame
  (length + hmac + body) given an HMAC key.

The :mod:`myco_kernel_bridge.framing` module is the I/O layer that reads/writes
these frames on stdio.

## Bootstrap key

The deterministic ``BOOTSTRAP_KEY`` = ``SHA-256(b"myco-bridge-protocol-v1-bootstrap")``
is used for the ``hello`` message only. The handshake transports a fresh
``session_secret`` (32 random bytes) which keys every subsequent message.

## Doctrine

- L0 §9.3 — canonical-bytes serialization carries across the IPC boundary.
- L1_SKIN §2 — envelope_digest HMAC discipline applied per message.
- Bootstrap key is NOT a real secret; it is a constant chosen to make
  rolling out a v2 protocol explicit. The IPC channel itself is the trust
  boundary (subprocess inherits parent's stdio).
"""

from __future__ import annotations

import hashlib
import hmac as _stdlib_hmac
from dataclasses import dataclass
from enum import Enum
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Bool,
    Bytes as CbBytes,
    CanonicalBytes,
    CanonicalBytesError,
    Map as CbMap,
    String as CbString,
    Uint as CbUint,
    Value,
    decode as cb_decode,
    encode as cb_encode,
    expect_map,
    expect_string,
    expect_uint,
)


# ---------------------------------------------------------------------------
# Constants.
# ---------------------------------------------------------------------------


PROTOCOL_VERSION: Final[int] = 1
"""Bridge wire protocol version. Bumped on any breaking change."""


BOOTSTRAP_KEY: Final[bytes] = hashlib.sha256(
    b"myco-bridge-protocol-v1-bootstrap"
).digest()
"""Deterministic key for the ``hello`` message HMAC. NOT a real secret.

Both Rust and Python compute this constant identically at module load.
Any change here is a protocol-version bump.
"""


MAX_FRAME_BODY_SIZE: Final[int] = 1024 * 1024
"""Maximum body+hmac size on the wire (1 MiB). Frames exceeding this are
rejected as a DoS protection."""


HMAC_SIZE: Final[int] = 32
"""HMAC-SHA256 output size in bytes."""


# ---------------------------------------------------------------------------
# Message type enum.
# ---------------------------------------------------------------------------


class MessageType(str, Enum):
    """All M5 bridge message types.

    Subclassing ``str`` so the value is directly usable as a canonical-bytes
    String.
    """

    HELLO = "hello"
    """Rust → Python: bootstrap handshake; transports the session_secret."""

    HELLO_ACK = "hello_ack"
    """Python → Rust: acknowledges hello; reports tropism + python versions."""

    REGISTER_AXIS = "register_axis"
    """Rust → Python: register a gradient axis with schema + update rule."""

    REGISTER_AXIS_ACK = "register_axis_ack"
    """Python → Rust: axis registered successfully."""

    PERTURB = "perturb"
    """Rust → Python: apply a delta to a gradient axis."""

    PERTURB_ACK = "perturb_ack"
    """Python → Rust: perturbation applied."""

    ADVANCE = "advance"
    """Rust → Python: run one cycle of gradient evolution."""

    ADVANCE_RESPONSE = "advance_response"
    """Python → Rust: advance complete; reports fruited axes + sporocarps."""

    SNAPSHOT = "snapshot"
    """Rust → Python: read current gradient state."""

    SNAPSHOT_RESPONSE = "snapshot_response"
    """Python → Rust: current axis values."""

    SHUTDOWN = "shutdown"
    """Rust → Python: graceful exit signal."""

    SHUTDOWN_ACK = "shutdown_ack"
    """Python → Rust: about to exit; written immediately before process exit."""

    ERROR = "error"
    """Either direction: error envelope echoing a request_id."""

    SAVE_STATE = "save_state"
    """Rust → Python: persist gradient state to a state_dir on disk (M7)."""

    SAVE_STATE_ACK = "save_state_ack"
    """Python → Rust: gradient state persisted to disk."""

    LOAD_STATE = "load_state"
    """Rust → Python: load gradient state from a state_dir on disk (M7)."""

    LOAD_STATE_ACK = "load_state_ack"
    """Python → Rust: gradient state hydrated (or genesis-on-missing)."""

    COMPUTE_INTENT = "compute_intent"
    """Operator/Rust → Python: derive intent from a DAG subset via kernel/trajectory (M8)."""

    COMPUTE_INTENT_RESPONSE = "compute_intent_response"
    """Python → Rust: clusters resulting from cluster_C over the DAG subset."""

    SUBMIT_MUTATION = "submit_mutation"
    """Operator/Rust → Python: classify a mutation + (for CI) verify owner attestation (M10)."""

    SUBMIT_MUTATION_RESPONSE = "submit_mutation_response"
    """Python → Rust: classification + accepted/rejected + content for DAG commit."""


# ---------------------------------------------------------------------------
# Error types.
# ---------------------------------------------------------------------------


class BridgeProtocolError(Exception):
    """Bridge wire-protocol error (malformed frame, bad version, HMAC fail, etc)."""


class HmacMismatchError(BridgeProtocolError):
    """Frame HMAC did not verify against the expected key.

    Per L1_HARD_RULES C18 / C2 family: this is a CRITICAL skin breach in
    networked contexts. In the M5 stdio-only context, this most likely
    indicates a protocol-version skew or wire corruption.
    """


class VersionMismatchError(BridgeProtocolError):
    """Frame's protocol version does not match :data:`PROTOCOL_VERSION`."""


class FrameTooLargeError(BridgeProtocolError):
    """Frame body+hmac size exceeds :data:`MAX_FRAME_BODY_SIZE`."""


# ---------------------------------------------------------------------------
# Message dataclass.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Message:
    """A bridge message — decoded form.

    The body Map's four keys are surfaced as typed fields. The payload
    Map is left as a generic :class:`CbMap` for per-message-type handlers
    to interpret.
    """

    type: MessageType
    """Message type tag."""

    request_id: int
    """Correlation ID — request and response share this value."""

    payload: CbMap
    """Type-specific payload (canonical-bytes Map)."""

    version: int = PROTOCOL_VERSION
    """Protocol version of this message. Always equal to PROTOCOL_VERSION
    on a valid local frame, but kept as a field for verification clarity."""


# ---------------------------------------------------------------------------
# Body encode / decode.
# ---------------------------------------------------------------------------


def body_to_canonical_bytes(message: Message) -> CanonicalBytes:
    """Encode the body Map of a :class:`Message` to canonical bytes.

    Body = Map({"v": Uint, "type": String, "request_id": Uint, "payload": Map}).
    """
    body_map = CbMap.from_dict(
        {
            "v": CbUint(message.version),
            "type": CbString(message.type.value),
            "request_id": CbUint(message.request_id),
            "payload": message.payload,
        }
    )
    return cb_encode(body_map)


def canonical_bytes_to_body(body_bytes: bytes) -> Message:
    """Decode a canonical-bytes body into a :class:`Message`.

    Raises:
        BridgeProtocolError: on any structural error (missing key, wrong
            type, unknown message type, version mismatch).
    """
    try:
        decoded = cb_decode(body_bytes)
    except CanonicalBytesError as e:
        raise BridgeProtocolError(f"body decode failed: {e}") from e
    body_map = expect_map(decoded)
    # Extract the four required keys.
    keys = dict(body_map.value)
    try:
        v = expect_uint(keys["v"])
        type_str = expect_string(keys["type"])
        request_id = expect_uint(keys["request_id"])
        payload = expect_map(keys["payload"])
    except KeyError as e:
        raise BridgeProtocolError(f"body missing required key: {e}") from e
    except CanonicalBytesError as e:
        raise BridgeProtocolError(f"body key has wrong type: {e}") from e
    if v != PROTOCOL_VERSION:
        raise VersionMismatchError(
            f"protocol version mismatch: got {v}, expected {PROTOCOL_VERSION}"
        )
    try:
        msg_type = MessageType(type_str)
    except ValueError as e:
        raise BridgeProtocolError(f"unknown message type: {type_str!r}") from e
    return Message(
        type=msg_type,
        request_id=request_id,
        payload=payload,
        version=v,
    )


# ---------------------------------------------------------------------------
# Full frame encode / decode (body + HMAC).
# ---------------------------------------------------------------------------


def compute_hmac(body_bytes: bytes, key: bytes) -> bytes:
    """Compute HMAC-SHA256 over the body bytes with the given key.

    Returns 32 bytes.
    """
    if len(key) == 0:
        raise BridgeProtocolError("HMAC key cannot be empty (per L1_SKIN §2)")
    return _stdlib_hmac.new(key, body_bytes, hashlib.sha256).digest()


def encode_message(message: Message, key: bytes) -> bytes:
    """Encode a :class:`Message` to the on-the-wire frame body (hmac + body).

    Returns the **frame body** (hmac + body) — the caller is responsible
    for prepending the u32 BE length prefix (:mod:`myco_kernel_bridge.framing`
    does this).

    Args:
        message: the message to encode.
        key: HMAC key (BOOTSTRAP_KEY for hello; session_secret otherwise).
    """
    body = body_to_canonical_bytes(message).bytes_
    hmac_bytes = compute_hmac(body, key)
    return hmac_bytes + body


def decode_message(frame_body: bytes, key: bytes) -> Message:
    """Decode a frame body (hmac + body) to a :class:`Message`.

    Args:
        frame_body: the bytes inside the length-prefixed frame
            (i.e., the 32-byte HMAC followed by the canonical-bytes body).
        key: expected HMAC key.

    Raises:
        BridgeProtocolError: on length, HMAC, or canonical-bytes errors.
    """
    if len(frame_body) < HMAC_SIZE:
        raise BridgeProtocolError(
            f"frame body too small: {len(frame_body)} < HMAC size {HMAC_SIZE}"
        )
    hmac_received = frame_body[:HMAC_SIZE]
    body_bytes = frame_body[HMAC_SIZE:]
    hmac_expected = compute_hmac(body_bytes, key)
    if not _stdlib_hmac.compare_digest(hmac_received, hmac_expected):
        raise HmacMismatchError(
            "frame HMAC verification failed (wrong session_secret or wire corruption)"
        )
    return canonical_bytes_to_body(body_bytes)


# ---------------------------------------------------------------------------
# Convenience builders for common payloads.
# ---------------------------------------------------------------------------


def hello_payload(session_secret: bytes) -> CbMap:
    """Build the payload for a ``hello`` message.

    Per protocol: ``hello`` transports the 32-byte session_secret which
    keys all subsequent message HMACs.
    """
    if len(session_secret) != 32:
        raise BridgeProtocolError(
            f"session_secret must be exactly 32 bytes; got {len(session_secret)}"
        )
    return CbMap.from_dict({"session_secret": CbBytes(session_secret)})


def hello_ack_payload(
    kernel_tropism_version: str, python_version: str
) -> CbMap:
    """Build the payload for a ``hello_ack`` reply."""
    return CbMap.from_dict(
        {
            "kernel_tropism_version": CbString(kernel_tropism_version),
            "python_version": CbString(python_version),
        }
    )


def error_payload(code: str, message: str, in_response_to: int) -> CbMap:
    """Build the payload for an ``error`` envelope."""
    return CbMap.from_dict(
        {
            "code": CbString(code),
            "message": CbString(message),
            "in_response_to": CbUint(in_response_to),
        }
    )


def register_axis_payload(
    name: str,
    axis_class: str,
    fruiting_threshold: float,
    initial_value: float,
    decay_rate_per_cycle: float,
    is_mortality_signal: bool,
    update_rule_kind: str,
) -> CbMap:
    """Build the payload for a ``register_axis`` request."""
    if axis_class not in ("appetite", "decay"):
        raise BridgeProtocolError(f"invalid axis_class: {axis_class!r}")
    if update_rule_kind not in ("decay", "noop"):
        raise BridgeProtocolError(
            f"invalid update_rule_kind: {update_rule_kind!r}"
        )
    return CbMap.from_dict(
        {
            "name": CbString(name),
            "axis_class": CbString(axis_class),
            "fruiting_threshold_repr": CbString(repr(fruiting_threshold)),
            "initial_value_repr": CbString(repr(initial_value)),
            "decay_rate_per_cycle_repr": CbString(repr(decay_rate_per_cycle)),
            "is_mortality_signal": Bool(is_mortality_signal),
            "update_rule_kind": CbString(update_rule_kind),
        }
    )


def perturb_payload(axis_name: str, delta: float) -> CbMap:
    """Build the payload for a ``perturb`` request."""
    return CbMap.from_dict(
        {
            "axis_name": CbString(axis_name),
            "delta_repr": CbString(repr(delta)),
        }
    )


def advance_payload(current_cycle: int) -> CbMap:
    """Build the payload for an ``advance`` request."""
    return CbMap.from_dict({"current_cycle": CbUint(current_cycle)})


def empty_payload() -> CbMap:
    """Empty payload (snapshot request, *_ack messages, shutdown, etc.)."""
    return CbMap(tuple())


def state_dir_payload(state_dir: str) -> CbMap:
    """Build the payload for a ``save_state`` or ``load_state`` request."""
    return CbMap.from_dict({"state_dir": CbString(state_dir)})


def load_state_ack_payload(axis_count: int, hydrated: bool) -> CbMap:
    """Build the payload for a ``load_state_ack`` response."""
    return CbMap.from_dict(
        {
            "axis_count": CbUint(axis_count),
            "hydrated": Bool(hydrated),
        }
    )
