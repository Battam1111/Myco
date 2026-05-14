"""Gradient persistence — save/load to canonical-bytes file (L4 M7).

## On-disk schema (gradient.cb)

A canonical-bytes Map with two keys:

- ``format_version``: Uint(1) — bumped on any breaking schema change.
- ``axes``: Array of per-axis Maps:

  - ``name``: String
  - ``axis_class``: String("appetite" or "decay")
  - ``fruiting_threshold_repr``: String (float as repr)
  - ``initial_value_repr``: String
  - ``decay_rate_per_cycle_repr``: String
  - ``is_mortality_signal``: Bool
  - ``update_rule_kind``: String("noop" or "decay")
  - ``current_value_repr``: String
  - ``fruiting_count``: Uint
  - ``last_fruiting_cycle``: Uint (0 sentinel for "never fruited")
  - ``last_fruiting_cycle_set``: Bool (True if axis has ever fruited)

## Atomicity

Writes go to ``gradient.cb.tmp`` first, then ``os.replace`` atomically
swaps onto ``gradient.cb``. On POSIX this is atomic by spec; on Windows
``os.replace`` calls ``MoveFileExW`` with replace semantics.

## Failure modes

Read failures (missing, malformed, unknown format_version) return ``None``.
The caller treats that as a genesis condition.

## Doctrine

- L1_TROPISM §3 — gradient configuration is substrate-resident state;
  must survive across processes.
- L0 §9.3 — canonical-bytes determinism preserved across disk boundary.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final

from myco_kernel_governance.canonical_bytes import (
    Array,
    Bool,
    CanonicalBytesError,
    Map as CbMap,
    String,
    Uint,
    Value,
    decode,
    encode,
    expect_array,
    expect_bool,
    expect_map,
    expect_string,
    expect_uint,
)

from myco_kernel_tropism.appetite_axis import (
    AppetiteAxis,
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
    UpdateRule,
)
from myco_kernel_tropism.gradient import GradientConfiguration


GRADIENT_FILENAME: Final[str] = "gradient.cb"
"""Filename for the gradient state file within a substrate state directory."""

GRADIENT_FORMAT_VERSION: Final[int] = 1
"""On-disk format version. Bumped on any breaking schema change."""


class PersistenceError(Exception):
    """Gradient persistence error (I/O, malformed data, version mismatch)."""


# ---------------------------------------------------------------------------
# Serialization.
# ---------------------------------------------------------------------------


def gradient_to_canonical_bytes(gradient: GradientConfiguration) -> bytes:
    """Encode a :class:`GradientConfiguration` as canonical bytes.

    Both the axis schema (CI-protected per L1_HARD_RULES F7) and the
    operational state (current value, fruiting count) are captured. Sorting
    axes by name ensures byte-determinism across saves of the same state.
    """
    axes_array: list[Value] = []
    for name in sorted(gradient.axes.keys()):
        axis = gradient.axes[name]
        rule = gradient.update_rules[name]
        rule_kind = _rule_kind_label(rule)
        axes_array.append(
            CbMap.from_dict(
                {
                    "name": String(name),
                    "axis_class": String(axis.schema.axis_class.value),
                    "fruiting_threshold_repr": String(
                        repr(axis.schema.fruiting_threshold)
                    ),
                    "initial_value_repr": String(repr(axis.schema.initial_value)),
                    "decay_rate_per_cycle_repr": String(
                        repr(axis.schema.decay_rate_per_cycle)
                    ),
                    "is_mortality_signal": Bool(axis.schema.is_mortality_signal),
                    "update_rule_kind": String(rule_kind),
                    "current_value_repr": String(repr(axis.value)),
                    "fruiting_count": Uint(axis.fruiting_count),
                    "last_fruiting_cycle": Uint(
                        axis.last_fruiting_cycle or 0
                    ),
                    "last_fruiting_cycle_set": Bool(
                        axis.last_fruiting_cycle is not None
                    ),
                }
            )
        )
    out = CbMap.from_dict(
        {
            "format_version": Uint(GRADIENT_FORMAT_VERSION),
            "axes": Array(tuple(axes_array)),
        }
    )
    return encode(out).bytes_


def gradient_from_canonical_bytes(data: bytes) -> GradientConfiguration | None:
    """Decode a gradient state blob.

    Returns ``None`` on version mismatch (caller falls back to genesis).
    Raises :class:`PersistenceError` on malformed data.
    """
    try:
        decoded = decode(data)
    except CanonicalBytesError as e:
        raise PersistenceError(f"gradient decode failed: {e}") from e
    try:
        root_map = expect_map(decoded)
    except CanonicalBytesError as e:
        raise PersistenceError(f"gradient root is not a Map: {e}") from e
    fields = dict(root_map.value)
    try:
        version = expect_uint(fields["format_version"])
    except (KeyError, CanonicalBytesError) as e:
        raise PersistenceError(f"gradient missing format_version: {e}") from e
    if version != GRADIENT_FORMAT_VERSION:
        return None

    try:
        axes_array = expect_array(fields["axes"])
    except (KeyError, CanonicalBytesError) as e:
        raise PersistenceError(f"gradient missing axes array: {e}") from e

    gradient = GradientConfiguration()
    for axis_value in axes_array:
        try:
            axis_map = expect_map(axis_value)
        except CanonicalBytesError as e:
            raise PersistenceError(f"axis entry not a Map: {e}") from e
        fields_axis = dict(axis_map.value)
        try:
            name = expect_string(fields_axis["name"])
            axis_class_str = expect_string(fields_axis["axis_class"])
            fruiting_threshold = float(
                expect_string(fields_axis["fruiting_threshold_repr"])
            )
            initial_value = float(
                expect_string(fields_axis["initial_value_repr"])
            )
            decay_rate_per_cycle = float(
                expect_string(fields_axis["decay_rate_per_cycle_repr"])
            )
            is_mortality_signal = expect_bool(
                fields_axis["is_mortality_signal"]
            )
            update_rule_kind = expect_string(fields_axis["update_rule_kind"])
            current_value = float(
                expect_string(fields_axis["current_value_repr"])
            )
            fruiting_count = expect_uint(fields_axis["fruiting_count"])
            last_fruiting_cycle_raw = expect_uint(
                fields_axis["last_fruiting_cycle"]
            )
            last_fruiting_cycle_set = expect_bool(
                fields_axis["last_fruiting_cycle_set"]
            )
        except (KeyError, CanonicalBytesError, ValueError) as e:
            raise PersistenceError(f"axis decode error: {e}") from e

        axis_class: AxisClass
        if axis_class_str == "appetite":
            axis_class = AxisClass.APPETITE
        elif axis_class_str == "decay":
            axis_class = AxisClass.DECAY
        else:
            raise PersistenceError(
                f"unknown axis_class: {axis_class_str!r}"
            )

        rule: UpdateRule
        if update_rule_kind == "noop":
            rule = NoOpRule()
        elif update_rule_kind == "decay":
            rule = DecayRule()
        else:
            raise PersistenceError(
                f"unknown update_rule_kind: {update_rule_kind!r}"
            )

        schema = AxisSchema(
            name=name,
            axis_class=axis_class,
            fruiting_threshold=fruiting_threshold,
            initial_value=initial_value,
            decay_rate_per_cycle=decay_rate_per_cycle,
            is_mortality_signal=is_mortality_signal,
        )
        axis = AppetiteAxis(
            schema=schema,
            value=current_value,
            fruiting_count=fruiting_count,
            last_fruiting_cycle=(
                last_fruiting_cycle_raw if last_fruiting_cycle_set else None
            ),
        )
        gradient.axes[name] = axis
        gradient.update_rules[name] = rule
    return gradient


def _rule_kind_label(rule: UpdateRule) -> str:
    """Return the persistence-tag for an UpdateRule. Mirrors the
    ``update_rule_kind`` field in :func:`register_axis_payload`."""
    if isinstance(rule, NoOpRule):
        return "noop"
    if isinstance(rule, DecayRule):
        return "decay"
    raise PersistenceError(
        f"cannot persist unknown UpdateRule type: {type(rule).__name__}"
    )


# ---------------------------------------------------------------------------
# Disk I/O.
# ---------------------------------------------------------------------------


def save_gradient(gradient: GradientConfiguration, state_dir: str | Path) -> None:
    """Atomically write the gradient state to ``<state_dir>/gradient.cb``.

    Creates ``state_dir`` if it does not exist. Writes to a ``.tmp`` file
    first, then atomically renames onto the target.
    """
    state_path = Path(state_dir)
    state_path.mkdir(parents=True, exist_ok=True)
    target = state_path / GRADIENT_FILENAME
    tmp = state_path / f"{GRADIENT_FILENAME}.tmp"
    data = gradient_to_canonical_bytes(gradient)
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, target)


def load_gradient(state_dir: str | Path) -> GradientConfiguration | None:
    """Load gradient state from ``<state_dir>/gradient.cb``.

    Returns:
        :class:`GradientConfiguration` on success, ``None`` on missing
        file or version mismatch.

    Raises:
        :class:`PersistenceError` on malformed data.
    """
    state_path = Path(state_dir)
    target = state_path / GRADIENT_FILENAME
    if not target.exists():
        return None
    with open(target, "rb") as f:
        data = f.read()
    return gradient_from_canonical_bytes(data)
