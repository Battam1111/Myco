"""Myco kernel/bridge_python — Rust↔Python cross-process bridge worker (L4 M5).

## Doctrine

Per L1_CONTINUITY §1.1 + L3_PACKAGE_MAP: the substrate's metabolic cycle is
orchestrated by `kernel/continuity` (Rust). Step 2 (gradient advance) and the
sporocarp-emission part of step 3 are L3-mapped to `kernel/tropism` (Python).
Crossing that language boundary requires a stable IPC contract — this package
is the Python worker side of that contract.

This is the M5 minimum-viable cross-process organism: one Rust controller
spawns one Python worker subprocess; the controller drives the gradient
through stdio; the worker emits sporocarps. The same wire protocol is the
seed for the M6+ networked transport (kernel/skin TCP/Unix-socket).

## Wire format (M5 v1)

Each message on stdio is one length-prefixed frame::

    [u32 BE length, 4 bytes] [hmac, 32 bytes] [body, length-32 bytes]

The body is the canonical-bytes encoding (per L0 §9.3 + L1_SCHEMA §3.1) of a
:class:`Map` with four keys (canonically sorted):

- ``v`` (Uint): protocol version, always 1 for M5.
- ``type`` (String): message type (e.g., ``"hello"``, ``"advance"``).
- ``request_id`` (Uint): correlation ID; responses echo the request's id.
- ``payload`` (Map): type-specific payload.

The HMAC is HMAC-SHA256 over the body bytes, keyed by ``session_secret``
(established during the ``hello`` handshake) — except the ``hello`` message
itself, which is keyed by the deterministic ``BOOTSTRAP_KEY``.

## Doctrine traceability

- L1_CONTINUITY §1.1 — step 2 gradient_advance dispatch.
- L1_TROPISM §3 — kernel/tropism is the gradient-state owner.
- L3_OUTLINE §5 + L3_PACKAGE_MAP §6 — Python is L3-mapped for tropism.
- L1_SKIN §2 — envelope_digest HMAC discipline carried into IPC.
- L0 §9.3 — canonical-bytes determinism preserved across IPC boundary.

## Status

DRAFT 1 — M5 minimum-viable. Future M6+ work: networked transport,
async I/O, multiplexing multiple subprocess workers, hardened crash
recovery, OS-sealed session secret derivation.
"""

from __future__ import annotations

from myco_kernel_bridge.protocol import (
    BOOTSTRAP_KEY,
    BridgeProtocolError,
    Message,
    MessageType,
    PROTOCOL_VERSION,
    body_to_canonical_bytes,
    canonical_bytes_to_body,
    decode_message,
    encode_message,
)

__all__ = [
    "BOOTSTRAP_KEY",
    "BridgeProtocolError",
    "Message",
    "MessageType",
    "PROTOCOL_VERSION",
    "body_to_canonical_bytes",
    "canonical_bytes_to_body",
    "decode_message",
    "encode_message",
]
