"""Handler registry — the dispatch table mapping message types to handlers.

## Why a registry?

The dispatcher's job is to route one decoded :class:`Message` to the one
function that knows how to process it. Historically this was a 12-arm
``if request.type is MessageType.X: return _handle_x(...)`` chain inside
``dispatcher.py``. Each arm was a thin restatement of a fact that already
lives next to the handler: *"this handler processes this message type."*

This module makes that fact the single source of truth. Each handler
registers itself for its message type via the :func:`handler` decorator;
``dispatcher.dispatch`` then performs one dict lookup instead of walking a
linear chain. Adding a message type means writing one decorated function —
no second edit to a dispatch chain that could drift out of sync.

## Wire-behavior invariance

The registry changes *only* the dispatch mechanism. It does not touch any
handler body, message-type string, canonical-bytes field, error-handling
clause, or return shape. A registry lookup that resolves ``MessageType.X``
to ``_handle_x`` is byte-for-byte equivalent to the ``if`` arm it replaces:
the same handler runs with the same arguments and produces the same
:class:`Message`. The protocol contract (per L0/cards/AS_anchor_surface §3
canonical-bytes determinism) is preserved exactly.

## Registration discipline

Registration is explicit and collision-checked: registering two handlers
for the same :class:`MessageType` raises at import time, so a copy-paste
mistake fails loudly rather than silently shadowing a handler.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from myco_kernel_bridge.protocol import Message, MessageType

if TYPE_CHECKING:
    from myco_kernel_bridge.dispatcher import DispatcherState


HandlerFn = Callable[["DispatcherState", Message], Message]
"""Signature shared by every request handler.

A handler takes the mutable :class:`DispatcherState` and the decoded
request :class:`Message`, and returns the response :class:`Message`. Handlers
never return ``None`` — the shutdown sentinel is interpreted by the daemon
loop from the response's message type, not from a ``None`` handler result
(matching the pre-refactor behavior, where ``_handle_shutdown`` returned a
``shutdown_ack`` Message and the loop exited on ``request.type``).
"""


REGISTRY: dict[MessageType, HandlerFn] = {}
"""The dispatch table: message type → handler function.

Populated at import time by the :func:`handler` decorator as each handler
module is imported. ``dispatcher.dispatch`` reads this table.
"""


def handler(message_type: MessageType) -> Callable[[HandlerFn], HandlerFn]:
    """Register the decorated function as the handler for ``message_type``.

    The decorator returns the function unchanged, so the handler remains a
    plain callable usable directly in tests.

    Args:
        message_type: the request type this handler processes.

    Raises:
        ValueError: if a handler is already registered for ``message_type``
            (collision guard — a registration mistake fails loudly).
    """

    def register(fn: HandlerFn) -> HandlerFn:
        if message_type in REGISTRY:
            existing = REGISTRY[message_type].__name__
            raise ValueError(
                f"duplicate handler registration for {message_type.value!r}: "
                f"{existing!r} already registered, cannot also register "
                f"{fn.__name__!r}"
            )
        REGISTRY[message_type] = fn
        return fn

    return register
