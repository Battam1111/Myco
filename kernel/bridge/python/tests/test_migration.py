"""v3.1.1 Sprint 8.G (P03 §10.4) — two-phase schema migration dispatcher tests.

In-process (no subprocess). Exercises the Python half of the migration FSM:

- ``migration_mode=true`` submit_mutation builds a CANDIDATE gradient and
  LEAVES the active gradient unchanged.
- ``commit_migration`` promotes the candidate to active.
- ``abort_migration`` drops the candidate, active untouched.
- ``advance`` advances the candidate alongside the active + reports divergence
  (Option A: candidate mortality fruiting / raise / non-finite).
"""

from __future__ import annotations

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    Bytes as CbBytes,
    Map as CbMap,
    String as CbString,
    expect_bool,
    expect_string,
)
from myco_kernel_governance.schema_evolution import (
    schema_diff_modify_axis_threshold_bytes,
)
from myco_kernel_tropism.appetite_axis import (
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
)

from myco_kernel_bridge.dispatcher import DispatcherState, dispatch
from myco_kernel_bridge.protocol import (
    Message,
    MessageType,
    advance_payload,
    empty_payload,
    hello_payload,
)


def _boot(state: DispatcherState, tmp_path) -> None:  # type: ignore[no-untyped-def]
    """Hello handshake + keyless load_state.

    **v0.9 owner-key removal**: CI mutations are accepted keyless — no owner key
    is initialized and no attestation signature is required.
    """
    dispatch(
        state,
        Message(type=MessageType.HELLO, request_id=1, payload=hello_payload(b"\xaa" * 32)),
    )
    dispatch(
        state,
        Message(
            type=MessageType.LOAD_STATE,
            request_id=2,
            payload=CbMap.from_dict({"state_dir": CbString(str(tmp_path))}),
        ),
    )


def _register_axis(
    state: DispatcherState,
    name: str,
    threshold: float,
    *,
    is_mortality: bool = False,
    axis_class: AxisClass = AxisClass.APPETITE,
    initial: float = 0.0,
    decay: float = 1.0,
) -> None:
    schema = AxisSchema(
        name=name,
        axis_class=axis_class,
        fruiting_threshold=threshold,
        initial_value=initial,
        decay_rate_per_cycle=decay,
        is_mortality_signal=is_mortality,
    )
    rule = DecayRule() if axis_class is AxisClass.DECAY else NoOpRule()
    state.gradient.register_axis(schema, rule)


def _submit_migration(
    state: DispatcherState,
    diff_bytes: bytes,
    request_id: int = 10,
) -> dict:
    """Submit a schema_evolution mutation in migration_mode=true (keyless CI).
    Returns the decoded response fields."""
    response = dispatch(
        state,
        Message(
            type=MessageType.SUBMIT_MUTATION,
            request_id=request_id,
            payload=CbMap.from_dict(
                {
                    "mutation_type": CbString("schema_evolution"),
                    "touched_fields": Array(()),
                    "touched_files": Array(()),
                    "touched_meta_structures": Array(()),
                    "content_canonical_bytes": CbBytes(diff_bytes),
                    "migration_mode": Bool(True),
                }
            ),
        ),
    )
    assert response is not None
    return dict(response.payload.value)


def test_migration_mode_builds_candidate_and_leaves_active_unchanged(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)

    diff = schema_diff_modify_axis_threshold_bytes("hunger", 99.0)
    fields = _submit_migration(state, diff)

    assert expect_bool(fields["accepted"]) is True
    assert expect_bool(fields["migration_mode"]) is True
    assert expect_bool(fields["candidate_built"]) is True
    # schema_apply_attempted must be FALSE in migration mode (the live gradient
    # was not touched — only the candidate copy was).
    assert expect_bool(fields["schema_apply_attempted"]) is False

    # The ACTIVE gradient still has the ORIGINAL threshold.
    assert state.gradient.get_axis("hunger").schema.fruiting_threshold == 10.0
    # A candidate is held with the NEW threshold.
    assert state.candidate_gradient is not None
    assert state.candidate_gradient.get_axis("hunger").schema.fruiting_threshold == 99.0
    assert state.candidate_op == "modify_axis_threshold"
    assert state.candidate_diff_bytes == diff


def test_migration_mode_candidate_build_failure_reports_false(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)

    # modify a non-existent axis → candidate build fails.
    diff = schema_diff_modify_axis_threshold_bytes("does_not_exist", 5.0)
    fields = _submit_migration(state, diff)

    assert expect_bool(fields["accepted"]) is True  # CI gate passed
    assert expect_bool(fields["migration_mode"]) is True
    assert expect_bool(fields["candidate_built"]) is False
    assert state.candidate_gradient is None
    assert expect_string(fields["schema_apply_failure_reason"]) != ""


def test_commit_migration_promotes_candidate_to_active(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)
    _submit_migration(state, schema_diff_modify_axis_threshold_bytes("hunger", 77.0))
    assert state.candidate_gradient is not None

    response = dispatch(
        state,
        Message(type=MessageType.COMMIT_MIGRATION, request_id=20, payload=empty_payload()),
    )
    assert response is not None
    assert response.type is MessageType.COMMIT_MIGRATION_ACK
    # The active gradient now carries the candidate's threshold; candidate cleared.
    assert state.gradient.get_axis("hunger").schema.fruiting_threshold == 77.0
    assert state.candidate_gradient is None
    assert state.candidate_op == ""
    assert state.candidate_diff_bytes == b""


def test_abort_migration_drops_candidate_active_untouched(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)
    _submit_migration(state, schema_diff_modify_axis_threshold_bytes("hunger", 55.0))
    assert state.candidate_gradient is not None

    response = dispatch(
        state,
        Message(type=MessageType.ABORT_MIGRATION, request_id=30, payload=empty_payload()),
    )
    assert response is not None
    assert response.type is MessageType.ABORT_MIGRATION_ACK
    # Active gradient unchanged (still original threshold); candidate dropped.
    assert state.gradient.get_axis("hunger").schema.fruiting_threshold == 10.0
    assert state.candidate_gradient is None


def test_commit_and_abort_are_idempotent_noops_without_candidate(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    assert state.candidate_gradient is None
    # Both must ack without raising even when no migration is in flight.
    r1 = dispatch(
        state,
        Message(type=MessageType.COMMIT_MIGRATION, request_id=40, payload=empty_payload()),
    )
    assert r1 is not None and r1.type is MessageType.COMMIT_MIGRATION_ACK
    r2 = dispatch(
        state,
        Message(type=MessageType.ABORT_MIGRATION, request_id=41, payload=empty_payload()),
    )
    assert r2 is not None and r2.type is MessageType.ABORT_MIGRATION_ACK


# ---------------------------------------------------------------------------
# advance dual-validation: divergence detection (Option A).
# ---------------------------------------------------------------------------


def _advance(state: DispatcherState, cycle: int, request_id: int = 50) -> dict:
    response = dispatch(
        state,
        Message(
            type=MessageType.ADVANCE,
            request_id=request_id,
            payload=advance_payload(cycle),
        ),
    )
    assert response is not None
    return dict(response.payload.value)


def test_advance_without_migration_reports_candidate_inactive(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)
    fields = _advance(state, 1)
    assert expect_bool(fields["candidate_active"]) is False
    assert expect_bool(fields["candidate_diverged"]) is False


def test_advance_equivalent_candidate_does_not_diverge(tmp_path) -> None:  # type: ignore[no-untyped-def]
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(state, "hunger", 10.0)
    # A modify_axis_threshold candidate that doesn't change fruiting behaviour
    # at the current value (value 0, threshold 10 vs 99 — neither fruits).
    _submit_migration(state, schema_diff_modify_axis_threshold_bytes("hunger", 99.0))
    fields = _advance(state, 1)
    assert expect_bool(fields["candidate_active"]) is True
    assert expect_bool(fields["candidate_diverged"]) is False
    assert expect_string(fields["divergence_reason"]) == ""


def test_advance_candidate_mortality_fruiting_diverges(tmp_path) -> None:  # type: ignore[no-untyped-def]
    # Active gradient: a DECAY mortality axis that does NOT fruit this cycle
    # (threshold far below current value). The candidate LOWERS the mortality
    # axis threshold above the current value so the candidate FRUITS its
    # mortality_signal where the active does not → Option-A divergence.
    state = DispatcherState()
    _boot(state, tmp_path)
    _register_axis(
        state,
        "death",
        threshold=-100.0,  # active: only fruits when value <= -100 (won't this cycle)
        is_mortality=True,
        axis_class=AxisClass.DECAY,
        initial=10.0,
        decay=0.9,
    )
    # Candidate raises the mortality threshold to 100 → value (9 after decay)
    # <= 100 → candidate fruits its mortality_signal; active (threshold -100)
    # does not. DIVERGENCE.
    diff = schema_diff_modify_axis_threshold_bytes("death", 100.0)
    _submit_migration(state, diff)
    fields = _advance(state, 1)
    assert expect_bool(fields["candidate_active"]) is True
    assert expect_bool(fields["candidate_diverged"]) is True
    assert "mortality" in expect_string(fields["divergence_reason"])
