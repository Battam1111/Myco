"""Appetite axes — per-axis state + update rules (L1_TROPISM §3 + §B-rows).

## Doctrine

Per L1_TROPISM §3: gradient configuration is multi-dimensional; each axis
is one **appetite**. The substrate updates each axis on every metabolic
cycle via per-axis **update rules**. When an axis crosses its **fruiting
trigger**, the substrate emits a sporocarp (see :mod:`sporocarp`).

Per L1_TROPISM §B-rows: axes have caller-defined schemas. M3 ships the
abstract `AppetiteAxis` + `UpdateRule` interfaces; substrate genesis
populates the concrete axis schema at L4.

## Axis classes (per L1_TROPISM)

- **Appetite** (default): gradient grows toward fruiting trigger as deltas
  reinforce. Resets after fruiting.
- **Decay** (special class): gradient decays toward zero on each cycle
  unless perturbed (mortality-signal axis is a decay-class).
- **Threshold-emergence** (deferred to M4 — L1_TROPISM §B2): threshold
  itself emerges from operating data once enough cycles accumulate.

Per L1_HARD_RULES F7: mortality-signal axis is CI-protected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Protocol


class AxisClass(Enum):
    """Per L1_TROPISM §3 + §B-rows axis class taxonomy."""

    APPETITE = "appetite"
    """Default: gradient grows toward fruiting trigger; resets after fruit."""

    DECAY = "decay"
    """Decays toward zero each cycle unless perturbed (mortality-signal etc)."""


@dataclass(frozen=True, slots=True)
class AxisSchema:
    """The schema definition for one appetite axis.

    Per L1_TROPISM §B-rows: the schema set is CI-protected (mutations to it
    go through L1_GOVERNANCE classifier as CI mutations).

    Fields
    ------
    name:
        Stable identifier (e.g., ``"kernel_evolution_tension"``).
    axis_class:
        Whether this axis behaves as APPETITE (grows toward trigger) or
        DECAY (decays toward zero).
    fruiting_threshold:
        Gradient value at which the substrate fruits a sporocarp. Crossed
        from below for APPETITE; from above (downward toward zero) for
        DECAY-mortality-signaling case (L1_HARD_RULES F7 CI-gated).
    initial_value:
        Gradient value at genesis. Reset value after sporocarp emission
        for APPETITE axes; never reset for DECAY axes.
    decay_rate_per_cycle:
        Multiplicative decay factor per cycle for DECAY axes (e.g., 0.99
        means 1% per-cycle decay). Ignored for APPETITE.
    is_mortality_signal:
        Per L1_HARD_RULES F7: mortality-signal axis threshold + update_rule
        is CI-protected. M3 flags it via this bit; M4 wires the classifier
        check.
    """

    name: str
    axis_class: AxisClass
    fruiting_threshold: float
    initial_value: float = 0.0
    decay_rate_per_cycle: float = 1.0
    is_mortality_signal: bool = False


@dataclass(slots=True)
class AppetiteAxis:
    """Live state of one appetite axis.

    Mutable counterpart to :class:`AxisSchema` — holds the current gradient
    value + how many times it has fruited. Initialized from the schema.
    """

    schema: AxisSchema
    """Read-only schema this axis was instantiated from."""

    value: float
    """Current gradient value."""

    fruiting_count: int = 0
    """How many times this axis has fruited a sporocarp since genesis."""

    last_fruiting_cycle: int | None = None
    """The metabolic-cycle counter at the most-recent fruiting (or None)."""

    @classmethod
    def from_schema(cls, schema: AxisSchema) -> AppetiteAxis:
        """Instantiate an axis from its schema, starting at initial_value."""
        return cls(schema=schema, value=schema.initial_value)

    def is_at_fruiting_threshold(self) -> bool:
        """Whether the gradient has crossed the fruiting threshold.

        For APPETITE: True iff value >= threshold.
        For DECAY (mortality-signal): True iff value <= threshold (crossing
        downward — substrate is approaching mortality).
        """
        if self.schema.axis_class is AxisClass.APPETITE:
            return self.value >= self.schema.fruiting_threshold
        return self.value <= self.schema.fruiting_threshold

    def perturb(self, delta: float) -> None:
        """Add a delta to the gradient value (substrate or operator
        perturbation).

        Per L1_TROPISM §3: gradient layer is jointly perturbed — substrate
        via internal update-rules; operator via skin-validated deltas. This
        method is the unified perturbation entry point.
        """
        self.value += delta

    def reset_after_fruiting(self, at_cycle: int) -> None:
        """Reset value to initial_value after sporocarp emission (APPETITE
        only; DECAY axes don't reset)."""
        if self.schema.axis_class is AxisClass.APPETITE:
            self.value = self.schema.initial_value
        self.fruiting_count += 1
        self.last_fruiting_cycle = at_cycle


class UpdateRule(Protocol):
    """Per-axis update rule (L1_TROPISM §B-rows).

    The substrate calls one of these per axis per cycle to advance the
    gradient. Update rules can encode arbitrary substrate-internal logic
    (decay, half-life, accumulation, etc.). M3 ships two concrete rules
    (DecayRule + AccumulateRule); L4 substrates may register custom rules
    via CI mutation of the registry.
    """

    def update(self, axis: AppetiteAxis, current_cycle: int) -> None:
        """Apply this update rule to the axis at the given cycle.

        Per L1_TROPISM: per-cycle update_rule applies BEFORE delta absorption
        in the cycle order. Decay-class axes decay first, then operator
        deltas perturb.
        """
        ...


# ---------------------------------------------------------------------------
# Concrete update rules (M3 ships two; M4+ adds more).
# ---------------------------------------------------------------------------


class DecayRule:
    """Multiplicative per-cycle decay: ``value *= decay_rate_per_cycle``.

    Used for DECAY-class axes (e.g., mortality-signal: continues to decay
    each cycle unless perturbed by a "still healthy" signal).
    """

    def update(self, axis: AppetiteAxis, current_cycle: int) -> None:  # noqa: D102
        _ = current_cycle  # unused
        axis.value *= axis.schema.decay_rate_per_cycle


class NoOpRule:
    """Update rule that does nothing.

    Used for APPETITE-class axes where perturbation by operator deltas
    drives gradient change; the substrate's own update has nothing to add.
    """

    def update(self, axis: AppetiteAxis, current_cycle: int) -> None:  # noqa: D102
        _ = (axis, current_cycle)
