"""Tests for kernel/tropism: appetite axes + gradient + sporocarp emission."""

from __future__ import annotations

import pytest

from myco_kernel_governance.canonical_bytes import CanonicalBytes
from myco_kernel_governance.crypto import NodeHash
from myco_kernel_tropism.appetite_axis import (
    AppetiteAxis,
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
    UpdateRule,
)
from myco_kernel_tropism.gradient import (
    AxisAlreadyRegistered,
    AxisNotFound,
    GradientConfiguration,
)
from myco_kernel_tropism.sporocarp import (
    Sporocarp,
    emit_appetite_fruiting,
    emit_mortality_signal,
)


# ---------------------------------------------------------------------------
# AppetiteAxis basic behavior.
# ---------------------------------------------------------------------------


def test_axis_initialization_from_schema() -> None:
    schema = AxisSchema(
        name="test_appetite",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
        initial_value=0.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    assert axis.value == 0.0
    assert axis.fruiting_count == 0
    assert axis.last_fruiting_cycle is None


def test_axis_perturb_accumulates() -> None:
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    axis.perturb(3.0)
    axis.perturb(2.5)
    assert axis.value == 5.5


def test_appetite_axis_crosses_threshold_above() -> None:
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    assert not axis.is_at_fruiting_threshold()
    axis.perturb(9.9)
    assert not axis.is_at_fruiting_threshold()
    axis.perturb(0.1)  # exactly at threshold
    assert axis.is_at_fruiting_threshold()


def test_decay_axis_crosses_threshold_below() -> None:
    """For DECAY (mortality-signal) axes: crossing is downward."""
    schema = AxisSchema(
        name="mortality",
        axis_class=AxisClass.DECAY,
        fruiting_threshold=2.0,  # cross when value drops below 2
        initial_value=10.0,
        decay_rate_per_cycle=0.99,
        is_mortality_signal=True,
    )
    axis = AppetiteAxis.from_schema(schema)
    assert not axis.is_at_fruiting_threshold()
    # Bring value down to 1.5; threshold is 2.0; crossed downward.
    axis.value = 1.5
    assert axis.is_at_fruiting_threshold()


def test_appetite_axis_resets_after_fruiting() -> None:
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
        initial_value=2.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    axis.perturb(8.0)  # value=10
    axis.reset_after_fruiting(at_cycle=100)
    assert axis.value == 2.0  # reset to initial
    assert axis.fruiting_count == 1
    assert axis.last_fruiting_cycle == 100


def test_decay_axis_does_not_reset_after_fruiting() -> None:
    """DECAY axes don't reset; mortality-signal continues approaching zero."""
    schema = AxisSchema(
        name="mortality",
        axis_class=AxisClass.DECAY,
        fruiting_threshold=2.0,
        initial_value=10.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    axis.value = 1.0  # below threshold
    axis.reset_after_fruiting(at_cycle=100)
    # Value NOT reset.
    assert axis.value == 1.0
    assert axis.fruiting_count == 1


# ---------------------------------------------------------------------------
# DecayRule + NoOpRule.
# ---------------------------------------------------------------------------


def test_decay_rule_applies_decay_rate() -> None:
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.DECAY,
        fruiting_threshold=0.1,
        initial_value=10.0,
        decay_rate_per_cycle=0.5,
    )
    axis = AppetiteAxis.from_schema(schema)
    rule = DecayRule()
    rule.update(axis, 1)
    assert axis.value == 5.0
    rule.update(axis, 2)
    assert axis.value == 2.5


def test_noop_rule_does_nothing() -> None:
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
        initial_value=3.0,
    )
    axis = AppetiteAxis.from_schema(schema)
    rule = NoOpRule()
    rule.update(axis, 1)
    assert axis.value == 3.0


# ---------------------------------------------------------------------------
# GradientConfiguration: registration + advance.
# ---------------------------------------------------------------------------


def test_gradient_register_and_lookup() -> None:
    g = GradientConfiguration()
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
    )
    g.register_axis(schema, NoOpRule())
    assert g.axis_count() == 1
    assert g.get_axis("x").value == 0.0


def test_gradient_duplicate_registration_rejected() -> None:
    g = GradientConfiguration()
    schema = AxisSchema(
        name="x",
        axis_class=AxisClass.APPETITE,
        fruiting_threshold=10.0,
    )
    g.register_axis(schema, NoOpRule())
    with pytest.raises(AxisAlreadyRegistered):
        g.register_axis(schema, NoOpRule())


def test_gradient_unknown_axis_raises() -> None:
    g = GradientConfiguration()
    with pytest.raises(AxisNotFound):
        g.get_axis("nonexistent")
    with pytest.raises(AxisNotFound):
        g.perturb_axis("nonexistent", 1.0)


def test_gradient_advance_fires_ready_axes() -> None:
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="ready",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
            initial_value=10.0,  # already at threshold
        ),
        NoOpRule(),
    )
    g.register_axis(
        AxisSchema(
            name="not_ready",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
            initial_value=5.0,  # below threshold
        ),
        NoOpRule(),
    )
    ready = g.advance(current_cycle=1)
    assert ready == ["ready"]


def test_gradient_decay_then_threshold_cross() -> None:
    """Mortality-signal scenario: DECAY rule drives value down to threshold."""
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="mortality",
            axis_class=AxisClass.DECAY,
            fruiting_threshold=2.0,
            initial_value=10.0,
            decay_rate_per_cycle=0.5,
            is_mortality_signal=True,
        ),
        DecayRule(),
    )
    # Cycle 1: 10 → 5; not yet below 2.
    ready = g.advance(current_cycle=1)
    assert ready == []
    # Cycle 2: 5 → 2.5; still above.
    ready = g.advance(current_cycle=2)
    assert ready == []
    # Cycle 3: 2.5 → 1.25; below 2.
    ready = g.advance(current_cycle=3)
    assert ready == ["mortality"]


def test_gradient_perturb_axis_changes_value() -> None:
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="x",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
        ),
        NoOpRule(),
    )
    g.perturb_axis("x", 3.0)
    assert g.get_axis("x").value == 3.0


def test_gradient_reset_after_fruiting_resets_appetite_only() -> None:
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="a",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
            initial_value=0.0,
        ),
        NoOpRule(),
    )
    g.register_axis(
        AxisSchema(
            name="d",
            axis_class=AxisClass.DECAY,
            fruiting_threshold=2.0,
            initial_value=10.0,
        ),
        NoOpRule(),
    )
    g.perturb_axis("a", 10.0)
    g.perturb_axis("d", -8.5)  # value: 1.5
    g.reset_after_fruiting(["a", "d"], at_cycle=42)
    assert g.get_axis("a").value == 0.0  # reset
    assert g.get_axis("d").value == 1.5  # not reset


def test_gradient_snapshot_values() -> None:
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="x",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
        ),
        NoOpRule(),
    )
    g.perturb_axis("x", 5.0)
    snap = g.snapshot_values()
    assert snap == {"x": 5.0}


def test_gradient_axis_names_sorted() -> None:
    g = GradientConfiguration()
    for name in ["zebra", "apple", "mango"]:
        g.register_axis(
            AxisSchema(
                name=name,
                axis_class=AxisClass.APPETITE,
                fruiting_threshold=10.0,
            ),
            NoOpRule(),
        )
    assert g.axis_names() == ["apple", "mango", "zebra"]


# ---------------------------------------------------------------------------
# Sporocarp emission.
# ---------------------------------------------------------------------------


def test_sporocarp_canonical_bytes_deterministic() -> None:
    s = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="test",
        fruiting_value=10.0,
        at_cycle=100,
    )
    assert s.to_canonical_bytes().bytes_ == s.to_canonical_bytes().bytes_


def test_sporocarp_hash_deterministic() -> None:
    s = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="test",
        fruiting_value=10.0,
        at_cycle=100,
    )
    assert s.hash() == s.hash()


def test_sporocarp_different_inputs_different_hash() -> None:
    s1 = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="a",
        fruiting_value=10.0,
        at_cycle=100,
    )
    s2 = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="b",  # different
        fruiting_value=10.0,
        at_cycle=100,
    )
    assert s1.hash() != s2.hash()


def test_sporocarp_with_causal_parents() -> None:
    p1 = NodeHash(b"\x01" * 32)
    p2 = NodeHash(b"\x02" * 32)
    s = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="x",
        fruiting_value=10.0,
        at_cycle=100,
        causal_parent_hashes=(p1, p2),
    )
    # Different parents → different hash.
    s_no_parents = Sporocarp(
        sporocarp_type="appetite_fruiting",
        axis_name="x",
        fruiting_value=10.0,
        at_cycle=100,
    )
    assert s.hash() != s_no_parents.hash()


def test_emit_appetite_fruiting_helper() -> None:
    s = emit_appetite_fruiting(
        axis_name="test_axis",
        fruiting_value=10.5,
        at_cycle=42,
    )
    assert s.sporocarp_type == "appetite_fruiting"
    assert s.axis_name == "test_axis"
    assert s.at_cycle == 42


def test_emit_mortality_signal_helper() -> None:
    parent = NodeHash(b"\xab" * 32)
    s = emit_mortality_signal(
        axis_name="mortality",
        fruiting_value=1.5,
        at_cycle=100,
        causal_parents=(parent,),
    )
    assert s.sporocarp_type == "mortality_signal_threshold_crossed"
    assert s.causal_parent_hashes == (parent,)


def test_sporocarp_with_payload() -> None:
    """Payload canonical bytes are included in the sporocarp's canonical
    representation."""
    payload1 = CanonicalBytes(b"payload_v1")
    payload2 = CanonicalBytes(b"payload_v2")
    s1 = Sporocarp(
        sporocarp_type="x",
        axis_name="a",
        fruiting_value=10.0,
        at_cycle=1,
        payload_canonical_bytes=payload1,
    )
    s2 = Sporocarp(
        sporocarp_type="x",
        axis_name="a",
        fruiting_value=10.0,
        at_cycle=1,
        payload_canonical_bytes=payload2,
    )
    # Different payloads → different canonical bytes → different hash.
    assert s1.to_canonical_bytes().bytes_ != s2.to_canonical_bytes().bytes_
    assert s1.hash() != s2.hash()


# ---------------------------------------------------------------------------
# End-to-end: gradient advance → sporocarp emission → reset.
# ---------------------------------------------------------------------------


def test_e2e_gradient_to_sporocarp_emission_to_reset() -> None:
    """Full M3 flow: gradient evolves; axis crosses threshold; substrate
    emits sporocarp; resets the axis."""
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="kernel_evolution_tension",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=10.0,
            initial_value=0.0,
        ),
        NoOpRule(),
    )

    # Cycle 1: operator emits delta perturbing axis by 4.0.
    g.perturb_axis("kernel_evolution_tension", 4.0)
    ready = g.advance(current_cycle=1)
    assert ready == []

    # Cycle 2: operator emits another delta of 7.0; total now 11.0.
    g.perturb_axis("kernel_evolution_tension", 7.0)
    ready = g.advance(current_cycle=2)
    assert ready == ["kernel_evolution_tension"]

    # Substrate emits sporocarp.
    sporocarp = emit_appetite_fruiting(
        axis_name="kernel_evolution_tension",
        fruiting_value=g.get_axis("kernel_evolution_tension").value,
        at_cycle=2,
    )
    assert sporocarp.axis_name == "kernel_evolution_tension"
    assert sporocarp.fruiting_value == 11.0

    # Substrate resets the axis.
    g.reset_after_fruiting(["kernel_evolution_tension"], at_cycle=2)
    assert g.get_axis("kernel_evolution_tension").value == 0.0
    assert g.get_axis("kernel_evolution_tension").fruiting_count == 1
