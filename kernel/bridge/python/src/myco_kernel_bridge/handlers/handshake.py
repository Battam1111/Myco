"""Handshake handler — the ``hello`` bootstrap that opens a session.

``hello`` is the only message accepted before the handshake completes (the
gate lives in ``dispatcher.dispatch``). It transports the 32-byte session
secret that keys every subsequent message's HMAC, and replies with the
kernel/tropism + Python versions.
"""

from __future__ import annotations

import platform

from myco_kernel_governance.canonical_bytes import Bytes as CbBytes

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import (
    KERNEL_TROPISM_VERSION,
    DispatcherState,
)
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    hello_ack_payload,
)


@handler(MessageType.HELLO)
def _handle_hello(state: DispatcherState, request: Message) -> Message:
    if state.handshake_complete:
        raise BridgeProtocolError("hello received after handshake already complete")
    keys = dict(request.payload.value)
    session_secret_value = keys.get("session_secret")
    if session_secret_value is None or not isinstance(session_secret_value, CbBytes):
        raise BridgeProtocolError("hello payload missing session_secret bytes")
    if len(session_secret_value.value) != 32:
        raise BridgeProtocolError(
            f"hello session_secret must be 32 bytes; got {len(session_secret_value.value)}"
        )
    state.session_secret = session_secret_value.value
    state.handshake_complete = True
    return Message(
        type=MessageType.HELLO_ACK,
        request_id=request.request_id,
        payload=hello_ack_payload(
            kernel_tropism_version=KERNEL_TROPISM_VERSION,
            python_version=platform.python_version(),
        ),
    )
