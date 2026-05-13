"""Gradient configuration — multi-axis state + per-cycle advance (L1_TROPISM §3).

## Doctrine

Per L1_TROPISM §3: gradient configuration is multi-dimensional, with one
axis per appetite. The substrate calls :meth:`GradientConfiguration.advance`
once per metabolic cycle, which:

1. Applies each axis's update rule.
2. Checks each axis for fruiting-threshold crossing.
3. Returns a list of axes ready to fruit (caller emits sporocarps from
   :mod:`sporocarp`).

The gradient configuration is **substrate-resident state**; operator-
emitted deltas perturb axes via :meth:`AppetiteAxis.perturb` at delta
absorption step (cycle step 3 per L1_CONTINUITY §1.1).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from myco_kernel_tropism.appetite_axis import (
    AppetiteAxis,
    AxisSchema,
    UpdateRule,
)


class GradientError(Exception):
    """Gradient-configuration error."""


class AxisAlreadyRegistered(GradientError):
    """Axis with the same name is already in the configuration."""


class AxisNotFound(GradientError):
    """No axis registered with the given name."""


@dataclass(slots=True)
class GradientConfiguration:
    """Live multi-axis appetite gradient.

    Holds one :class:`AppetiteAxis` per registered axis. Per-axis update
    rules are held in parallel (one rule per axis name).
    """

    axes: dict[str, AppetiteAxis] = field(default_factory=dict)
    update_rules: dict[str, UpdateRule] = field(default_factory=dict)

    def register_axis(self, schema: AxisSchema, update_rule: UpdateRule) -> None:
        """Register a new axis with its update rule.

        Raises:
            AxisAlreadyRegistered: if an axis with the same name exists.
        """
        if schema.name in self.axes:
            raise AxisAlreadyRegistered(
                f"axis already registered: {schema.name}"
            )
        self.axes[schema.name] = AppetiteAxis.from_schema(schema)
        self.update_rules[schema.name] = update_rule

    def get_axis(self, name: str) -> AppetiteAxis:
        """Look up an axis by name; raises if not registered."""
        if name not in self.axes:
            raise AxisNotFound(f"axis not registered: {name}")
        return self.axes[name]

    def perturb_axis(self, name: str, delta: float) -> None:
        """Apply a perturbation to a specific axis.

        Per L1_TROPISM §3 + L1_CONTINUITY cycle step 3: deltas absorbed in
        cycle step 3 perturb axes through this method.

        Raises:
            AxisNotFound: if the axis is not registered.
        """
        self.get_axis(name).perturb(delta)

    def advance(self, current_cycle: int) -> list[str]:
        """Run one cycle's worth of gradient evolution.

        Per L1_TROPISM §3 + L1_CONTINUITY §1.1 cycle step 2:

        1. Apply each axis's update rule.
        2. Identify which axes have crossed their fruiting threshold.

        Returns:
            List of axis names that are ready to fruit. The caller should
            invoke :mod:`sporocarp` emission for each, then call
            :meth:`reset_after_fruiting` on the corresponding axes.
        """
        ready_to_fruit: list[str] = []
        for name, axis in self.axes.items():
            rule = self.update_rules[name]
            rule.update(axis, current_cycle)
            if axis.is_at_fruiting_threshold():
                ready_to_fruit.append(name)
        return ready_to_fruit

    def reset_after_fruiting(self, axis_names: list[str], at_cycle: int) -> None:
        """Reset the given axes after sporocarp emission.

        Per L1_TROPISM §3: APPETITE axes reset to initial_value after
        fruiting; DECAY axes don't reset.
        """
        for name in axis_names:
            if name not in self.axes:
                raise AxisNotFound(f"cannot reset unknown axis: {name}")
            self.axes[name].reset_after_fruiting(at_cycle)

    def axis_count(self) -> int:
        """Number of registered axes."""
        return len(self.axes)

    def axis_names(self) -> list[str]:
        """Sorted list of registered axis names."""
        return sorted(self.axes.keys())

    def snapshot_values(self) -> dict[str, float]:
        """Return a snapshot of current axis values (for observability /
        tier-1 invariant validation)."""
        return {name: axis.value for name, axis in self.axes.items()}
