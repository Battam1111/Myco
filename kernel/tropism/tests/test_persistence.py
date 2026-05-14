"""Tests for kernel/tropism gradient persistence (M7)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from myco_kernel_tropism.appetite_axis import (
    AxisClass,
    AxisSchema,
    DecayRule,
    NoOpRule,
)
from myco_kernel_tropism.gradient import GradientConfiguration
from myco_kernel_tropism.persistence import (
    GRADIENT_FILENAME,
    GRADIENT_FORMAT_VERSION,
    PersistenceError,
    gradient_from_canonical_bytes,
    gradient_to_canonical_bytes,
    load_gradient,
    save_gradient,
)


def _build_basic_gradient() -> GradientConfiguration:
    g = GradientConfiguration()
    g.register_axis(
        AxisSchema(
            name="curiosity",
            axis_class=AxisClass.APPETITE,
            fruiting_threshold=5.0,
            initial_value=0.0,
            decay_rate_per_cycle=1.0,
            is_mortality_signal=False,
        ),
        NoOpRule(),
    )
    g.register_axis(
        AxisSchema(
            name="mortality",
            axis_class=AxisClass.DECAY,
            fruiting_threshold=0.1,
            initial_value=1.0,
            decay_rate_per_cycle=0.9,
            is_mortality_signal=True,
        ),
        DecayRule(),
    )
    return g


# ---------------------------------------------------------------------------
# Canonical-bytes roundtrip (in-memory).
# ---------------------------------------------------------------------------


def test_empty_gradient_roundtrips() -> None:
    g_in = GradientConfiguration()
    data = gradient_to_canonical_bytes(g_in)
    g_out = gradient_from_canonical_bytes(data)
    assert g_out is not None
    assert g_out.axis_count() == 0


def test_basic_gradient_roundtrips() -> None:
    g_in = _build_basic_gradient()
    g_in.perturb_axis("curiosity", 2.5)
    data = gradient_to_canonical_bytes(g_in)
    g_out = gradient_from_canonical_bytes(data)
    assert g_out is not None
    assert sorted(g_out.axis_names()) == ["curiosity", "mortality"]
    assert g_out.get_axis("curiosity").value == 2.5
    assert g_out.get_axis("mortality").value == 1.0


def test_post_fruiting_state_roundtrips() -> None:
    g_in = _build_basic_gradient()
    g_in.perturb_axis("curiosity", 6.0)  # above threshold
    fruited = g_in.advance(1)
    g_in.reset_after_fruiting(fruited, 1)
    assert g_in.get_axis("curiosity").value == 0.0  # reset
    assert g_in.get_axis("curiosity").fruiting_count == 1

    data = gradient_to_canonical_bytes(g_in)
    g_out = gradient_from_canonical_bytes(data)
    assert g_out is not None
    cur = g_out.get_axis("curiosity")
    assert cur.value == 0.0
    assert cur.fruiting_count == 1
    assert cur.last_fruiting_cycle == 1


def test_unperturbed_decay_axis_roundtrips() -> None:
    g_in = _build_basic_gradient()
    # 10 cycles of 0.9x decay: 1.0 → 1 * 0.9^10 ≈ 0.3486
    for cycle in range(1, 11):
        g_in.advance(cycle)
    data = gradient_to_canonical_bytes(g_in)
    g_out = gradient_from_canonical_bytes(data)
    assert g_out is not None
    # Floats roundtrip via repr() with full precision.
    assert g_out.get_axis("mortality").value == g_in.get_axis("mortality").value


def test_version_mismatch_returns_none(tmp_path: Path) -> None:
    # Write a gradient.cb file with version 999.
    from myco_kernel_governance.canonical_bytes import (
        Array as CbArray,
        Map as CbMap,
        Uint as CbUint,
        encode,
    )

    bad = CbMap.from_dict(
        {
            "format_version": CbUint(999),
            "axes": CbArray(()),
        }
    )
    target = tmp_path / GRADIENT_FILENAME
    target.write_bytes(encode(bad).bytes_)
    g = load_gradient(tmp_path)
    assert g is None


def test_malformed_bytes_raises() -> None:
    with pytest.raises(PersistenceError):
        gradient_from_canonical_bytes(b"not-canonical-bytes")


def test_missing_format_version_field_raises() -> None:
    from myco_kernel_governance.canonical_bytes import (
        Array as CbArray,
        Map as CbMap,
        encode,
    )

    bad = CbMap.from_dict({"axes": CbArray(())})
    with pytest.raises(PersistenceError, match="format_version"):
        gradient_from_canonical_bytes(encode(bad).bytes_)


# ---------------------------------------------------------------------------
# Disk save/load.
# ---------------------------------------------------------------------------


def test_save_and_load_via_disk(tmp_path: Path) -> None:
    g_in = _build_basic_gradient()
    g_in.perturb_axis("curiosity", 3.5)
    save_gradient(g_in, tmp_path)
    g_out = load_gradient(tmp_path)
    assert g_out is not None
    assert g_out.get_axis("curiosity").value == 3.5


def test_load_returns_none_when_file_missing(tmp_path: Path) -> None:
    assert load_gradient(tmp_path) is None


def test_save_is_atomic_no_tmp_leftover(tmp_path: Path) -> None:
    g_in = _build_basic_gradient()
    save_gradient(g_in, tmp_path)
    tmp_file = tmp_path / f"{GRADIENT_FILENAME}.tmp"
    target_file = tmp_path / GRADIENT_FILENAME
    assert not tmp_file.exists()
    assert target_file.exists()


def test_save_creates_nested_state_dir(tmp_path: Path) -> None:
    nested = tmp_path / "deep" / "nested" / "path"
    g_in = _build_basic_gradient()
    save_gradient(g_in, nested)
    assert (nested / GRADIENT_FILENAME).exists()


def test_save_overwrites_existing(tmp_path: Path) -> None:
    g1 = _build_basic_gradient()
    g1.perturb_axis("curiosity", 1.0)
    save_gradient(g1, tmp_path)

    g2 = _build_basic_gradient()
    g2.perturb_axis("curiosity", 9.0)
    save_gradient(g2, tmp_path)

    g_out = load_gradient(tmp_path)
    assert g_out is not None
    assert g_out.get_axis("curiosity").value == 9.0


def test_roundtrip_preserves_mortality_signal_flag(tmp_path: Path) -> None:
    g_in = _build_basic_gradient()
    save_gradient(g_in, tmp_path)
    g_out = load_gradient(tmp_path)
    assert g_out is not None
    assert g_out.get_axis("mortality").schema.is_mortality_signal is True
    assert g_out.get_axis("curiosity").schema.is_mortality_signal is False


def test_roundtrip_preserves_decay_rate(tmp_path: Path) -> None:
    g_in = _build_basic_gradient()
    save_gradient(g_in, tmp_path)
    g_out = load_gradient(tmp_path)
    assert g_out is not None
    assert g_out.get_axis("mortality").schema.decay_rate_per_cycle == 0.9
    assert g_out.get_axis("curiosity").schema.decay_rate_per_cycle == 1.0


def test_continue_metabolism_after_load(tmp_path: Path) -> None:
    """End-to-end: save mid-metabolism, load, continue, verify continuity."""
    g_in = _build_basic_gradient()
    g_in.perturb_axis("curiosity", 2.0)
    # 3 cycles of decay first, then save.
    for cycle in range(1, 4):
        g_in.advance(cycle)
    mortality_before = g_in.get_axis("mortality").value
    save_gradient(g_in, tmp_path)

    # Load fresh and continue.
    g_out = load_gradient(tmp_path)
    assert g_out is not None
    assert g_out.get_axis("mortality").value == mortality_before
    assert g_out.get_axis("curiosity").value == 2.0

    # Continue metabolism — 3 more decay cycles.
    for cycle in range(4, 7):
        g_out.advance(cycle)
    assert g_out.get_axis("mortality").value < mortality_before


def test_roundtrip_format_version_pin() -> None:
    """Pin format_version so any change is an explicit bump."""
    assert GRADIENT_FORMAT_VERSION == 1
