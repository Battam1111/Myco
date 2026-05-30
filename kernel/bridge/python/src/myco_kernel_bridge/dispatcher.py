"""Bridge dispatcher — map incoming requests to kernel/tropism operations.

This module is the Python worker's request router: each request type
corresponds to one operation on a held :class:`GradientConfiguration`, and
each response carries the canonical-bytes-encoded result.

## Why a separate dispatcher module?

The :mod:`myco_kernel_bridge.daemon` module owns the I/O loop and session
state (session_secret, sequence). This module owns the **routing** — turning
a decoded :class:`Message` into the one handler that processes it. The
**stateful kernel work** (the gradient configuration that lives across
requests, the sporocarp emissions queued for response, the owner-key history)
lives in the handlers, operating on the :class:`DispatcherState` defined in
:mod:`myco_kernel_bridge.handlers.state`.

Separating these concerns lets the dispatcher and each handler be
unit-tested without spawning a subprocess.

## Dispatch structure

Dispatch is a **registry lookup**, not an if/elif chain. Each handler
registers itself for its message type via the
:func:`~myco_kernel_bridge.handlers.registry.handler` decorator (see the
per-family modules in :mod:`myco_kernel_bridge.handlers`); importing the
handlers package populates
:data:`~myco_kernel_bridge.handlers.registry.REGISTRY` with the complete
``MessageType → handler`` table. :func:`dispatch` performs the handshake
gate, one dict lookup, and the unknown-type fallback.

This is purely a restructuring of the dispatch *mechanism*. The handler
bodies, message-type strings, canonical-bytes fields, narrowed ``except``
clauses, and return shapes are unchanged — the protocol contract is
preserved byte-for-byte.

## Doctrine

Per L1/TROPISM §3: kernel/tropism owns gradient state. The dispatcher is
a thin adapter — it does not contain new doctrine; it only routes
requests across the IPC boundary.

The dispatcher's responses are deterministic given the same request
sequence: replaying the same requests on a fresh dispatcher yields
identical gradient state and identical sporocarp hashes. This is
critical for L1/HARD_RULES C7 retro-edit detection: every sporocarp's
canonical bytes are reproducible from its inputs.
"""

from __future__ import annotations

from myco_kernel_bridge.handlers import REGISTRY
from myco_kernel_bridge.handlers.state import (
    KERNEL_TROPISM_VERSION,
    DispatcherState,
)
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    error_payload,
)


__all__ = [
    "KERNEL_TROPISM_VERSION",
    "DispatcherState",
    "build_error_response",
    "dispatch",
]


# ---------------------------------------------------------------------------
# Dispatcher.
# ---------------------------------------------------------------------------


def dispatch(state: DispatcherState, request: Message) -> Message | None:
    """Process one request and return the response (or None for shutdown).

    Args:
        state: mutable dispatcher state.
        request: decoded incoming message.

    Returns:
        The response message, or ``None`` if the daemon should exit
        (after sending the response).

    Raises:
        BridgeProtocolError: on invalid request structure (caller catches
            and returns an ERROR envelope).
    """
    # Handshake gating: only HELLO is accepted before handshake_complete.
    if not state.handshake_complete and request.type is not MessageType.HELLO:
        raise BridgeProtocolError(
            f"received {request.type.value!r} before hello handshake"
        )

    handler = REGISTRY.get(request.type)
    if handler is None:
        raise BridgeProtocolError(
            f"dispatcher cannot handle {request.type.value!r} (not a request type)"
        )
    return handler(state, request)


# ---------------------------------------------------------------------------
# Error envelope builder.
# ---------------------------------------------------------------------------


def build_error_response(
    in_response_to: int, code: str, message: str
) -> Message:
    """Construct an ``error`` envelope echoing a failed request's ID."""
    return Message(
        type=MessageType.ERROR,
        request_id=in_response_to,
        payload=error_payload(
            code=code,
            message=message,
            in_response_to=in_response_to,
        ),
    )
