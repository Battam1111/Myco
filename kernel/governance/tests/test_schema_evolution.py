"""Unit tests for M17 P3 永恒进化 schema_evolution module."""

from __future__ import annotations

import pytest
from myco_kernel_tropism.appetite_axis import (
    AxisClass,
    AxisSchema,
    NoOpRule,
)
from myco_kernel_tropism.gradient import (
    GradientConfiguration,
)

from myco_kernel_governance.schema_evolution import (
    SchemaDiff,
    SchemaDiffOp,
    SchemaEvolutionError,
    apply_schema_diff,
    parse_schema_diff,
    schema_diff_add_axis_bytes,
    schema_diff_modify_axis_threshold_bytes,
)


def _make_gradient_with_axis(name: str = "curiosity", threshold: float = 10.0):
    g = GradientConfiguration()
    schema = AxisSchema(
        name=name,
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=threshold,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
    )
    g.register_axis(schema, NoOpRule())
    return g


def test_schema_diff_modify_threshold_bytes_parses_correctly():
    bytes_ = schema_diff_modify_axis_threshold_bytes("curiosity", 25.5)
    diff = parse_schema_diff(bytes_)
    assert diff.op is SchemaDiffOp.MODIFY_AXIS_THRESHOLD
    assert diff.axis_name == "curiosity"


def test_apply_modify_threshold_changes_threshold():
    g = _make_gradient_with_axis("curiosity", 10.0)
    bytes_ = schema_diff_modify_axis_threshold_bytes("curiosity", 50.0)
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert result.succeeded
    assert g.get_axis("curiosity").schema.fruiting_threshold == 50.0


def test_apply_modify_threshold_on_unknown_axis_rolls_back():
    g = _make_gradient_with_axis("curiosity", 10.0)
    bytes_ = schema_diff_modify_axis_threshold_bytes("nonexistent", 50.0)
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert not result.succeeded
    assert "AxisNotFound" in result.failure_reason or "nonexistent" in result.failure_reason
    # State preserved: original axis threshold unchanged.
    assert g.get_axis("curiosity").schema.fruiting_threshold == 10.0


def test_apply_add_axis_registers_new_axis():
    g = GradientConfiguration()
    bytes_ = schema_diff_add_axis_bytes(
        axis_name="hunger",
        axis_class="appetite",
        fruiting_threshold=5.0,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
        update_rule_kind="noop",
    )
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert result.succeeded
    assert g.axis_count() == 1
    assert g.get_axis("hunger").schema.fruiting_threshold == 5.0


def test_apply_add_axis_duplicate_rolls_back():
    g = _make_gradient_with_axis("curiosity", 10.0)
    # Try to add curiosity again — should rollback.
    bytes_ = schema_diff_add_axis_bytes(
        axis_name="curiosity",
        axis_class="appetite",
        fruiting_threshold=99.0,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
        update_rule_kind="noop",
    )
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert not result.succeeded
    # Original threshold preserved (not changed to 99.0).
    assert g.get_axis("curiosity").schema.fruiting_threshold == 10.0
    assert g.axis_count() == 1


def test_apply_add_axis_with_unknown_class_rolls_back():
    g = GradientConfiguration()
    # Manually build malformed schema_diff bytes (unknown axis_class).
    bytes_ = schema_diff_add_axis_bytes(
        axis_name="x",
        axis_class="nonsense_class",
        fruiting_threshold=5.0,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
        update_rule_kind="noop",
    )
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert not result.succeeded
    assert g.axis_count() == 0  # no axis registered


def test_parse_schema_diff_unknown_op_raises():
    from myco_kernel_governance.canonical_bytes import (
        Map as CbMap,
    )
    from myco_kernel_governance.canonical_bytes import (
        String as CbString,
    )
    from myco_kernel_governance.canonical_bytes import (
        encode as cb_encode,
    )

    bad = CbMap.from_dict(
        {"op": CbString("nonsense_op"), "axis_name": CbString("x")}
    )
    bad_bytes = cb_encode(bad).bytes_
    with pytest.raises(SchemaEvolutionError, match="unknown op"):
        parse_schema_diff(bad_bytes)


def test_parse_schema_diff_missing_keys_raises():
    from myco_kernel_governance.canonical_bytes import (
        Map as CbMap,
    )
    from myco_kernel_governance.canonical_bytes import (
        String as CbString,
    )
    from myco_kernel_governance.canonical_bytes import (
        encode as cb_encode,
    )

    bad = CbMap.from_dict({"op": CbString(SchemaDiffOp.MODIFY_AXIS_THRESHOLD.value)})
    bad_bytes = cb_encode(bad).bytes_
    with pytest.raises(SchemaEvolutionError, match="missing required key"):
        parse_schema_diff(bad_bytes)


def test_modify_threshold_to_negative_value_succeeds_at_apply_layer():
    # The apply layer doesn't validate threshold semantics — that's a higher
    # layer's job. M17-MV records every successful apply faithfully.
    g = _make_gradient_with_axis("x", 10.0)
    bytes_ = schema_diff_modify_axis_threshold_bytes("x", -5.0)
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)
    assert result.succeeded
    assert g.get_axis("x").schema.fruiting_threshold == -5.0


def test_apply_modify_threshold_with_unparseable_repr_rolls_back():
    from myco_kernel_governance.canonical_bytes import (
        Map as CbMap,
    )
    from myco_kernel_governance.canonical_bytes import (
        String as CbString,
    )
    from myco_kernel_governance.canonical_bytes import (
        encode as cb_encode,
    )

    g = _make_gradient_with_axis("x", 10.0)
    bad_diff = CbMap.from_dict(
        {
            "op": CbString(SchemaDiffOp.MODIFY_AXIS_THRESHOLD.value),
            "axis_name": CbString("x"),
            "new_threshold_repr": CbString("not_a_float"),
        }
    )
    diff = parse_schema_diff(cb_encode(bad_diff).bytes_)
    result = apply_schema_diff(diff, g)
    assert not result.succeeded
    # Original threshold preserved.
    assert g.get_axis("x").schema.fruiting_threshold == 10.0


def test_snapshot_rollback_is_deep_copy_not_reference():
    g = _make_gradient_with_axis("x", 10.0)
    # Snapshot via failed apply (forces rollback path).
    bytes_ = schema_diff_modify_axis_threshold_bytes("nonexistent", 99.0)
    diff = parse_schema_diff(bytes_)
    _ = apply_schema_diff(diff, g)
    # Now mutate the live gradient — the rollback should NOT have shared state.
    g.get_axis("x").value = 42.0
    # Apply another (failing) diff; rollback should preserve value=42.
    diff2 = parse_schema_diff(
        schema_diff_modify_axis_threshold_bytes("nonexistent", 100.0)
    )
    _ = apply_schema_diff(diff2, g)
    assert g.get_axis("x").value == 42.0


# ---------------------------------------------------------------------------
# Regression: rollback must restore BOTH axes AND update_rules.
#
# GradientConfiguration holds parallel `axes` and `update_rules` dicts;
# register_axis (used by add_axis_to_gradient) writes BOTH. A prior bug had
# _restore_gradient restore only `axes`, leaving an orphan update_rules entry
# behind after a rolled-back schema mutation that had registered an axis.
# ---------------------------------------------------------------------------


def test_restore_gradient_restores_update_rules_not_just_axes():
    """Directly exercise the snapshot/restore primitive: a mutation that
    writes an update_rule (register_axis) then rolls back must leave NEITHER
    axes nor update_rules polluted."""
    from myco_kernel_tropism.appetite_axis import DecayRule

    from myco_kernel_governance.schema_evolution import (
        _restore_gradient,
        _snapshot_gradient,
    )

    g = _make_gradient_with_axis("base", 10.0)
    snapshot = _snapshot_gradient(g)

    # Simulate the live half of a schema mutation: register a new axis, which
    # writes BOTH gradient.axes["evolved"] and gradient.update_rules["evolved"].
    new_schema = AxisSchema(
        name="evolved",
        axis_class=AxisClass.DECAY,
        fruiting_threshold=3.0,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
    )
    g.register_axis(new_schema, DecayRule())
    assert "evolved" in g.axes
    assert "evolved" in g.update_rules  # the update_rule write we must undo

    # Roll back.
    _restore_gradient(g, snapshot)

    # The orphan update_rules entry must be gone (this is the regression).
    assert "evolved" not in g.axes
    assert "evolved" not in g.update_rules
    # Both dicts stay in lockstep with the pre-mutation snapshot.
    assert set(g.axes.keys()) == {"base"}
    assert set(g.update_rules.keys()) == {"base"}
    assert g.axes.keys() == g.update_rules.keys()


def test_apply_schema_diff_rolls_back_update_rules_on_post_register_failure(
    monkeypatch,
):
    """End-to-end via apply_schema_diff: when an add-axis op registers an axis
    (writing an update_rule) and THEN fails validation, the rollback must
    restore BOTH axes AND update_rules — no orphan rule may survive."""
    from myco_kernel_tropism.appetite_axis import DecayRule

    import myco_kernel_governance.schema_evolution as se

    g = _make_gradient_with_axis("base", 10.0)

    # Simulate a (future, multi-step) add-axis op that writes the update_rule
    # via register_axis and only afterwards hits an invariant violation.
    def _failing_add_axis(diff: SchemaDiff, gradient: GradientConfiguration):
        schema = AxisSchema(
            name=diff.axis_name,
            axis_class=AxisClass.DECAY,
            fruiting_threshold=3.0,
            initial_value=0.0,
            decay_rate_per_cycle=1.0,
            is_mortality_signal=False,
        )
        gradient.register_axis(schema, DecayRule())  # writes axes + update_rules
        # ...then a post-write invariant check fails:
        raise SchemaEvolutionError("post-register invariant violated")

    monkeypatch.setattr(se, "_apply_add_axis", _failing_add_axis)

    bytes_ = schema_diff_add_axis_bytes(
        axis_name="evolved",
        axis_class="decay",
        fruiting_threshold=3.0,
        initial_value=0.0,
        decay_rate_per_cycle=1.0,
        is_mortality_signal=False,
        update_rule_kind="decay",
    )
    diff = parse_schema_diff(bytes_)
    result = apply_schema_diff(diff, g)

    assert not result.succeeded
    assert "post-register invariant violated" in result.failure_reason
    # Rollback restored BOTH dicts: the half-applied axis + its update_rule
    # are both gone.
    assert "evolved" not in g.axes
    assert "evolved" not in g.update_rules
    assert set(g.axes.keys()) == {"base"}
    assert set(g.update_rules.keys()) == {"base"}
