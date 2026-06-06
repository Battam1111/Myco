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

from myco_kernel_tropism.gradient import GradientConfiguration


KERNEL_TROPISM_VERSION: Final[str] = "0.9.0-alpha.2"
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

    **v0.9 owner-key removal**: the ``owner_keys`` history field was removed
    with the rest of the owner-key/anchor subsystem. CI mutations are accepted
    keyless (see ``handlers.governance_ops``), so the dispatcher no longer holds
    any owner-key state.
    """

    gradient: GradientConfiguration = field(default_factory=GradientConfiguration)
    handshake_complete: bool = False
    session_secret: bytes | None = None

    # --- v3.1.1 Sprint 8.G (P03 §10.4) two-phase schema migration ---
    #
    # When the operator opts into the multi-cycle two-phase migration path
    # (submit_mutation with migration_mode=True), the dispatcher builds a
    # CANDIDATE gradient (a deep-copy of `gradient` with the schema_diff
    # applied to the COPY) and holds it here. The active `gradient` is left
    # UNTOUCHED. Each subsequent `advance` advances BOTH `gradient` and
    # `candidate_gradient`, comparing their behaviour (divergence detection).
    # `commit_migration` promotes the candidate to active; `abort_migration`
    # drops it. `None` = no migration in flight (the default).
    candidate_gradient: GradientConfiguration | None = None
    #: The schema_diff op name of the in-flight candidate (e.g.
    #: "modify_axis_threshold"); empty when no migration is in flight.
    candidate_op: str = ""
    #: The schema_diff canonical-bytes of the in-flight candidate (audit /
    #: parity with the substrate's stored copy); empty when none.
    candidate_diff_bytes: bytes = b""
