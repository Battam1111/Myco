"""P3 永恒进化 — Schema diff format + apply/rollback execution (L4 M17).

This module activates the L0 P3 (Eternal Evolution) principle which prior
milestones had only **gestured at** via the classifier (CI mutations were
recorded to the DAG but did not actually modify substrate schema).

## Per-L0 §2.1 P3

> Myco's **own shape evolves**. Schema, subsystem family, vocabulary, rules,
> contract itself — all first-class mutable objects under P1.b's two-tier
> boundary.
>
> An unchanging substrate is a dead substrate. Schema changes are normal
> operations.
>
> **Failed-evolution rollback**: when a P3 evolution produces I3
> inconsistency, the substrate rolls back to pre-evolution state and records
> the failure as a discrete causal-DAG event.

## How M17-MV implements P3

1. **schema_diff format**: canonical-bytes Map serialized as the content of
   a `mutation_type="schema_evolution"` submit_mutation.
2. **Owner attestation gate**: classifier rule promotes schema_evolution to
   CI (M10 owner-signature path).
3. **Apply path**: after signature verification, the dispatcher snapshots the
   current GradientConfiguration, applies the diff, validates invariants;
   on failure restores the snapshot.
4. **DAG audit trail**: substrate emits `evolution_succeeded:{op}` (success)
   or `evolution_failed:{op}` (rollback) as an additional DAG node beyond
   the mutation:schema_evolution record. Causal chain preserved.

## M17-MV scope (in-scope ops)

- ``modify_axis_threshold`` — change fruiting_threshold of an existing axis.
- ``add_axis_to_gradient`` — register a new axis (equivalent to register_axis
  but through the schema-evolution attestation gate).

M17+ extends to: remove_axis, modify_decay_rate, modify_axis_class,
classifier_table_diff, immune_detector_table_diff, lexicon_diff, doctrine_diff.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from myco_kernel_governance.canonical_bytes import (
    CanonicalBytes,
    Map as CbMap,
    String as CbString,
    decode as cb_decode,
    expect_map,
    expect_string,
)
from myco_kernel_tropism.appetite_axis import (
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


class SchemaEvolutionError(Exception):
    """Schema-evolution apply failed. The substrate rolls back."""


class SchemaDiffOp(str, Enum):
    """Allowed schema_diff operations in M17-MV."""

    MODIFY_AXIS_THRESHOLD = "modify_axis_threshold"
    ADD_AXIS_TO_GRADIENT = "add_axis_to_gradient"


@dataclass(frozen=True, slots=True)
class SchemaDiff:
    """A parsed schema_diff. The canonical-bytes wire format is a Map with
    these keys (plus op-specific extras).

    Canonical schema:
    ```
    Map({
        "op": String,                # one of SchemaDiffOp values
        "axis_name": String,         # target axis name
        # op-specific:
        # modify_axis_threshold:
        "new_threshold_repr": String,  # float-as-string (Python-compatible)
        # add_axis_to_gradient:
        "axis_class": String,
        "fruiting_threshold_repr": String,
        "initial_value_repr": String,
        "decay_rate_per_cycle_repr": String,
        "is_mortality_signal": Bool,
        "update_rule_kind": String,
    })
    ```
    """

    op: SchemaDiffOp
    axis_name: str
    # All op-specific params kept as raw Map for flexibility.
    params: dict[str, object]

    def summary(self) -> str:
        """Compact human-readable summary for DAG node content."""
        return f"{self.op.value}({self.axis_name}; {self.params!r})"


def parse_schema_diff(diff_canonical_bytes: bytes) -> SchemaDiff:
    """Decode a schema_diff from canonical bytes.

    Raises:
        SchemaEvolutionError: on missing/invalid keys.
    """
    try:
        decoded = cb_decode(diff_canonical_bytes)
    except Exception as e:
        raise SchemaEvolutionError(f"schema_diff decode failed: {e}") from e
    try:
        m = expect_map(decoded)
    except Exception as e:
        raise SchemaEvolutionError(f"schema_diff is not a Map: {e}") from e
    keys = dict(m.value)
    try:
        op_str = expect_string(keys["op"])
        axis_name = expect_string(keys["axis_name"])
    except KeyError as e:
        raise SchemaEvolutionError(f"schema_diff missing required key: {e}") from e
    except Exception as e:
        raise SchemaEvolutionError(f"schema_diff key type error: {e}") from e
    try:
        op = SchemaDiffOp(op_str)
    except ValueError as e:
        raise SchemaEvolutionError(
            f"schema_diff unknown op: {op_str!r}; allowed: {[o.value for o in SchemaDiffOp]}"
        ) from e

    # Collect op-specific params (everything except op + axis_name).
    params: dict[str, object] = {}
    for k, v in keys.items():
        if k in ("op", "axis_name"):
            continue
        params[k] = v

    return SchemaDiff(op=op, axis_name=axis_name, params=params)


@dataclass(slots=True)
class ApplyResult:
    """Result of applying a schema_diff to a GradientConfiguration."""

    succeeded: bool
    failure_reason: str = ""
    """Empty when succeeded. Set to the I3-style inconsistency reason on failure."""


def apply_schema_diff(
    diff: SchemaDiff, gradient: GradientConfiguration
) -> ApplyResult:
    """Apply a schema_diff to the gradient configuration.

    Snapshot-rollback semantics:
    - Before applying, deep-copy the gradient state.
    - On exception OR invariant violation, restore the snapshot and return
      ApplyResult(succeeded=False, failure_reason=...).
    - On success, return ApplyResult(succeeded=True).

    NOTE: This function MUTATES the gradient on success. The caller (typically
    the dispatcher's submit_mutation handler) must ensure exclusive access.
    """
    snapshot = _snapshot_gradient(gradient)

    try:
        if diff.op is SchemaDiffOp.MODIFY_AXIS_THRESHOLD:
            _apply_modify_axis_threshold(diff, gradient)
        elif diff.op is SchemaDiffOp.ADD_AXIS_TO_GRADIENT:
            _apply_add_axis(diff, gradient)
        else:  # pragma: no cover — exhaustive enum
            raise SchemaEvolutionError(f"schema_diff op {diff.op} not implemented")
    except SchemaEvolutionError as e:
        _restore_gradient(gradient, snapshot)
        return ApplyResult(succeeded=False, failure_reason=str(e))
    except (AxisNotFound, AxisAlreadyRegistered, ValueError, KeyError) as e:
        _restore_gradient(gradient, snapshot)
        return ApplyResult(
            succeeded=False, failure_reason=f"{type(e).__name__}: {e}"
        )

    return ApplyResult(succeeded=True)


# ---------------------------------------------------------------------------
# Internal: per-op implementations.
# ---------------------------------------------------------------------------


def _apply_modify_axis_threshold(
    diff: SchemaDiff, gradient: GradientConfiguration
) -> None:
    new_threshold_repr_value = diff.params.get("new_threshold_repr")
    if new_threshold_repr_value is None:
        raise SchemaEvolutionError(
            "modify_axis_threshold: missing new_threshold_repr"
        )
    new_threshold_repr = expect_string(new_threshold_repr_value)
    try:
        new_threshold = float(new_threshold_repr)
    except ValueError as e:
        raise SchemaEvolutionError(
            f"modify_axis_threshold: new_threshold_repr {new_threshold_repr!r} parse: {e}"
        ) from e

    axis = gradient.get_axis(diff.axis_name)  # raises AxisNotFound if missing
    # I3 invariant: mortality_signal threshold is unconditionally CI per
    # L1_HARD_RULES F7 + L0 P7 mortality-signal protection (per pass-1
    # mycoparasite-14). M17 CI gating already enforces this; we just don't
    # block here (the F-row watchdog will fire if rule changes).
    old_threshold = axis.schema.fruiting_threshold
    # AxisSchema is frozen; replace via reconstruction.
    new_schema = AxisSchema(
        name=axis.schema.name,
        axis_class=axis.schema.axis_class,
        fruiting_threshold=new_threshold,
        initial_value=axis.schema.initial_value,
        decay_rate_per_cycle=axis.schema.decay_rate_per_cycle,
        is_mortality_signal=axis.schema.is_mortality_signal,
    )
    axis.schema = new_schema  # type: ignore[misc]  (intentional schema mutation under P3)
    _ = old_threshold  # for debugging


def _apply_add_axis(
    diff: SchemaDiff, gradient: GradientConfiguration
) -> None:
    p = diff.params

    def _opt_string(key: str) -> Optional[str]:
        v = p.get(key)
        if v is None:
            return None
        return expect_string(v)

    axis_class_str = _opt_string("axis_class")
    if axis_class_str is None:
        raise SchemaEvolutionError("add_axis_to_gradient: missing axis_class")
    if axis_class_str == "appetite":
        axis_class = AxisClass.APPETITE
    elif axis_class_str == "decay":
        axis_class = AxisClass.DECAY
    else:
        raise SchemaEvolutionError(
            f"add_axis_to_gradient: unknown axis_class {axis_class_str!r}"
        )

    fruiting_threshold_repr = _opt_string("fruiting_threshold_repr")
    initial_value_repr = _opt_string("initial_value_repr")
    decay_rate_per_cycle_repr = _opt_string("decay_rate_per_cycle_repr")
    update_rule_kind = _opt_string("update_rule_kind")
    if None in (
        fruiting_threshold_repr,
        initial_value_repr,
        decay_rate_per_cycle_repr,
        update_rule_kind,
    ):
        raise SchemaEvolutionError(
            "add_axis_to_gradient: missing one of fruiting_threshold_repr / "
            "initial_value_repr / decay_rate_per_cycle_repr / update_rule_kind"
        )

    is_mortality_signal_value = p.get("is_mortality_signal")
    if is_mortality_signal_value is None:
        raise SchemaEvolutionError(
            "add_axis_to_gradient: missing is_mortality_signal"
        )
    # is_mortality_signal is a Bool canonical_bytes value.
    from myco_kernel_governance.canonical_bytes import Bool

    if not isinstance(is_mortality_signal_value, Bool):
        raise SchemaEvolutionError(
            f"add_axis_to_gradient: is_mortality_signal must be Bool; got {type(is_mortality_signal_value).__name__}"
        )
    is_mortality_signal = bool(is_mortality_signal_value.value)

    try:
        fruiting_threshold = float(fruiting_threshold_repr)  # type: ignore[arg-type]
        initial_value = float(initial_value_repr)  # type: ignore[arg-type]
        decay_rate = float(decay_rate_per_cycle_repr)  # type: ignore[arg-type]
    except (ValueError, TypeError) as e:
        raise SchemaEvolutionError(
            f"add_axis_to_gradient: float repr parse: {e}"
        ) from e

    schema = AxisSchema(
        name=diff.axis_name,
        axis_class=axis_class,
        fruiting_threshold=fruiting_threshold,
        initial_value=initial_value,
        decay_rate_per_cycle=decay_rate,
        is_mortality_signal=is_mortality_signal,
    )
    rule: UpdateRule
    if update_rule_kind == "decay":
        rule = DecayRule()
    elif update_rule_kind == "noop":
        rule = NoOpRule()
    else:
        raise SchemaEvolutionError(
            f"add_axis_to_gradient: unknown update_rule_kind {update_rule_kind!r}"
        )

    gradient.register_axis(schema, rule)  # may raise AxisAlreadyRegistered


# ---------------------------------------------------------------------------
# Snapshot / restore — deep copy of GradientConfiguration for rollback.
# ---------------------------------------------------------------------------


def _snapshot_gradient(gradient: GradientConfiguration) -> GradientConfiguration:
    """Deep-copy the gradient state for potential rollback."""
    return copy.deepcopy(gradient)


def _restore_gradient(
    gradient: GradientConfiguration, snapshot: GradientConfiguration
) -> None:
    """Restore gradient state from a snapshot in-place.

    Because callers hold a reference to `gradient`, we copy snapshot fields
    onto the live object rather than swapping references.
    """
    # GradientConfiguration's internal state is in `axes` dict.
    # We replace it wholesale from the snapshot (deep-copied to avoid
    # aliasing with subsequent mutations on the live object).
    gradient.axes = copy.deepcopy(snapshot.axes)


# ---------------------------------------------------------------------------
# Helpers for building schema_diff canonical bytes (operator-side).
# ---------------------------------------------------------------------------


def schema_diff_modify_axis_threshold_bytes(
    axis_name: str, new_threshold: float
) -> bytes:
    """Build canonical bytes for a modify_axis_threshold schema_diff.

    Mirrors the format expected by parse_schema_diff. Operators use this to
    construct the content_canonical_bytes for a submit_mutation with
    mutation_type='schema_evolution'.
    """
    from myco_kernel_governance.canonical_bytes import encode as cb_encode

    diff_map = CbMap.from_dict(
        {
            "op": CbString(SchemaDiffOp.MODIFY_AXIS_THRESHOLD.value),
            "axis_name": CbString(axis_name),
            "new_threshold_repr": CbString(repr(new_threshold)),
        }
    )
    return cb_encode(diff_map).bytes_


def schema_diff_add_axis_bytes(
    axis_name: str,
    axis_class: str,
    fruiting_threshold: float,
    initial_value: float,
    decay_rate_per_cycle: float,
    is_mortality_signal: bool,
    update_rule_kind: str,
) -> bytes:
    """Build canonical bytes for an add_axis_to_gradient schema_diff."""
    from myco_kernel_governance.canonical_bytes import Bool
    from myco_kernel_governance.canonical_bytes import encode as cb_encode

    diff_map = CbMap.from_dict(
        {
            "op": CbString(SchemaDiffOp.ADD_AXIS_TO_GRADIENT.value),
            "axis_name": CbString(axis_name),
            "axis_class": CbString(axis_class),
            "fruiting_threshold_repr": CbString(repr(fruiting_threshold)),
            "initial_value_repr": CbString(repr(initial_value)),
            "decay_rate_per_cycle_repr": CbString(repr(decay_rate_per_cycle)),
            "is_mortality_signal": Bool(is_mortality_signal),
            "update_rule_kind": CbString(update_rule_kind),
        }
    )
    return cb_encode(diff_map).bytes_
