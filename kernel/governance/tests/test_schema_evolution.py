"""Unit tests for M17 P3 永恒进化 schema_evolution module."""

from __future__ import annotations

import pytest

from myco_kernel_governance.schema_evolution import (
    ApplyResult,
    SchemaDiff,
    SchemaDiffOp,
    SchemaEvolutionError,
    apply_schema_diff,
    parse_schema_diff,
    schema_diff_add_axis_bytes,
    schema_diff_modify_axis_threshold_bytes,
)
from myco_kernel_tropism.appetite_axis import (
    AxisClass,
    AxisSchema,
    NoOpRule,
)
from myco_kernel_tropism.gradient import (
    AxisAlreadyRegistered,
    GradientConfiguration,
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
        String as CbString,
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
        String as CbString,
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
        String as CbString,
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
