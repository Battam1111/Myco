"""Bridge request handlers — one function per message type, registry-dispatched.

Each request :class:`~myco_kernel_bridge.protocol.MessageType` maps to exactly
one handler function. Handlers are grouped into family modules:

============================  ============================================
Module                        Message types
============================  ============================================
:mod:`.handshake`             ``hello``
:mod:`.gradient_ops`          ``register_axis`` / ``perturb`` / ``advance``
                              / ``snapshot``
:mod:`.persistence_ops`       ``save_state`` / ``load_state``
                              / ``snapshot_gradient_to_dir``
:mod:`.lifecycle`             ``shutdown`` / ``query_gradient_schemas``
:mod:`.trajectory_ops`        ``compute_intent``
:mod:`.governance_ops`        ``submit_mutation``
============================  ============================================

Importing this package imports every family module, which (via the
``@handler`` decorator) populates :data:`.registry.REGISTRY` with the full
dispatch table. ``dispatcher.dispatch`` then resolves a message type to its
handler with a single dict lookup.

Registration is explicit (this module names every family module) rather than
filesystem-scanned, so the dispatch table is deterministic and a missing
import fails loudly at module load instead of silently dropping a handler.
"""

from __future__ import annotations

# Importing the family modules triggers @handler registration into REGISTRY.
# Order is irrelevant (each handler registers a distinct message type), but is
# kept stable for readability. These imports are load-bearing side effects, not
# unused — hence the noqa.
from myco_kernel_bridge.handlers import (  # noqa: F401
    governance_ops,
    gradient_ops,
    handshake,
    lifecycle,
    persistence_ops,
    trajectory_ops,
)
from myco_kernel_bridge.handlers.registry import REGISTRY, HandlerFn, handler
from myco_kernel_bridge.handlers.state import (
    KERNEL_TROPISM_VERSION,
    DispatcherState,
)

__all__ = [
    "KERNEL_TROPISM_VERSION",
    "REGISTRY",
    "DispatcherState",
    "HandlerFn",
    "handler",
]
