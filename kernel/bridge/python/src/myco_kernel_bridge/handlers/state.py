"""Dispatcher state — the mutable kernel state held across requests.

This module owns the :class:`DispatcherState` dataclass and the
:data:`KERNEL_TROPISM_VERSION` constant reported in ``hello_ack``. It lives
in the ``handlers`` package (rather than in ``dispatcher.py``) so that
handler modules can depend on the state type without importing
``dispatcher`` — which itself imports the handler modules. Keeping the state
here breaks that cycle: handlers → state, dispatcher → handlers → state.

``dispatcher.py`` re-exports :class:`DispatcherState` and
:data:`KERNEL_TROPISM_VERSION` so existing imports
(``from myco_kernel_bridge.dispatcher import DispatcherState``) keep working
unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from myco_kernel_governance.owner_keys import OwnerKeyHistory
from myco_kernel_tropism.gradient import GradientConfiguration


KERNEL_TROPISM_VERSION: Final[str] = "0.9.0-alpha.1"
"""Version reported in hello_ack. Tracks kernel/tropism's pyproject version."""


@dataclass(slots=True)
class DispatcherState:
    """Mutable state held by the dispatcher across requests.

    Fields
    ------
    gradient:
        The live gradient configuration. Initially empty; populated by
        ``register_axis`` requests from the Rust controller.
    handshake_complete:
        Whether the ``hello`` handshake has occurred. Must be True before
        any other message type is accepted.
    session_secret:
        The session secret transported by ``hello``. Used by the daemon
        loop to verify subsequent message HMACs.
    owner_keys:
        Owner-key history (M10). Initialized either by load_state from disk
        or by the load_state's ``genesis_owner_pubkey`` field on first sight.
        Consulted by ``submit_mutation`` for CI-attestation verification.
    """

    gradient: GradientConfiguration = field(default_factory=GradientConfiguration)
    handshake_complete: bool = False
    session_secret: bytes | None = None
    owner_keys: OwnerKeyHistory | None = None
