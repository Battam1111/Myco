"""Persistence handlers — save / load / snapshot gradient state to disk.

These handlers bridge to ``kernel/tropism``'s on-disk persistence (M7):

- ``save_state`` — persist gradient to a state_dir.
- ``load_state`` — hydrate gradient from a state_dir; supports the M21.3
  ``skip_disk_load`` DAG-replay path.
- ``snapshot_gradient_to_dir`` — clone the gradient into a child substrate's
  state_dir (M20 P8 永恒繁衍 sprout primitive).

**v0.9 owner-key removal**: the M10 owner-key history persistence (save/load
``owner_keys.cb`` + the ``genesis_owner_pubkey`` first-init path) was removed
with the rest of the owner-key/anchor subsystem. The substrate no longer
supplies a genesis owner key; CI mutations are accepted keyless.
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Bool,
    Map as CbMap,
    Uint as CbUint,
    expect_string,
)
from myco_kernel_tropism.persistence import (
    PersistenceError,
    load_gradient,
    save_gradient,
)

from myco_kernel_bridge.handlers.registry import handler
from myco_kernel_bridge.handlers.state import DispatcherState
from myco_kernel_bridge.protocol import (
    BridgeProtocolError,
    Message,
    MessageType,
    empty_payload,
    load_state_ack_payload,
)


@handler(MessageType.SNAPSHOT_GRADIENT_TO_DIR)
def _handle_snapshot_gradient_to_dir(
    state: DispatcherState, request: Message
) -> Message:
    """M20 P8 永恒繁衍: snapshot the gradient state to a target directory.

    This is the Python-side primitive used by sprout_child: writes a fresh
    `gradient.cb` containing the parent's axes + schemas + current values
    into the child substrate's state_dir.

    The child receives a CLONE of the parent's gradient (axes registered;
    initial axis values = parent's current values). The L1 decision: M20-MV
    transfers gradient state but NOT the parent's causal DAG (child starts
    its own causal history per L1 design).
    """
    keys = dict(request.payload.value)
    try:
        target_dir = expect_string(keys["target_dir"])
    except KeyError as e:
        raise BridgeProtocolError(
            f"snapshot_gradient_to_dir missing target_dir: {e}"
        ) from e
    try:
        save_gradient(state.gradient, target_dir)
    except (PersistenceError, OSError) as e:
        raise BridgeProtocolError(
            f"snapshot_gradient_to_dir save failed: {e}"
        ) from e
    return Message(
        type=MessageType.SNAPSHOT_GRADIENT_TO_DIR_ACK,
        request_id=request.request_id,
        payload=CbMap.from_dict(
            {"axis_count": CbUint(state.gradient.axis_count())}
        ),
    )


@handler(MessageType.SAVE_STATE)
def _handle_save_state(state: DispatcherState, request: Message) -> Message:
    """Persist the current gradient state to a directory on disk."""
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"save_state missing state_dir: {e}") from e
    try:
        save_gradient(state.gradient, state_dir)
    except (PersistenceError, OSError) as e:
        raise BridgeProtocolError(f"save_state failed: {e}") from e
    return Message(
        type=MessageType.SAVE_STATE_ACK,
        request_id=request.request_id,
        payload=empty_payload(),
    )


@handler(MessageType.LOAD_STATE)
def _handle_load_state(state: DispatcherState, request: Message) -> Message:
    """Hydrate gradient state from a directory on disk.

    M21.3 P5 万物互联: accepts an optional ``skip_disk_load`` Bool field.
    When True, Python does NOT read gradient.cb from disk; Rust will
    subsequently REPLAY DAG events (axis_registered / axis_perturbed / etc.)
    to reconstruct state in-memory. This is the path used when the DAG is the
    authoritative source of truth (post-M21 substrate).

    **v0.9 owner-key removal**: the M10 owner-key loading (``owner_keys.cb``)
    and the ``genesis_owner_pubkey`` first-init path were removed. Any
    ``genesis_owner_pubkey`` field a caller still sends is ignored; CI
    mutations are accepted keyless.
    """
    keys = dict(request.payload.value)
    try:
        state_dir = expect_string(keys["state_dir"])
    except KeyError as e:
        raise BridgeProtocolError(f"load_state missing state_dir: {e}") from e

    # M21.3: skip_disk_load flag — Python won't read state files; Rust
    # will reconstruct state via DAG event replay.
    skip_disk_load = False
    if "skip_disk_load" in keys:
        skip_disk_value = keys["skip_disk_load"]
        if not isinstance(skip_disk_value, Bool):
            raise BridgeProtocolError(
                f"skip_disk_load must be Bool; got {type(skip_disk_value).__name__}"
            )
        skip_disk_load = bool(skip_disk_value.value)

    # Load gradient (M7) — skipped under M21.3 skip_disk_load.
    if skip_disk_load:
        loaded_gradient = None
    else:
        try:
            loaded_gradient = load_gradient(state_dir)
        except PersistenceError as e:
            raise BridgeProtocolError(f"load_state gradient failed: {e}") from e
        except OSError as e:
            raise BridgeProtocolError(f"load_state I/O: {e}") from e
    if loaded_gradient is not None:
        state.gradient = loaded_gradient

    axis_count = state.gradient.axis_count()
    hydrated = loaded_gradient is not None
    return Message(
        type=MessageType.LOAD_STATE_ACK,
        request_id=request.request_id,
        payload=load_state_ack_payload(
            axis_count=axis_count,
            hydrated=hydrated,
        ),
    )
