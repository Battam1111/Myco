"""Tests for ``myco.core.registry`` — the global substrate registry.

Covers the round-trip (register + list), stale detection,
timestamp semantics, and graceful degradation on malformed files.
Added in v0.5.16.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path


def test_register_and_list_round_trip(tmp_path: Path) -> None:
    from myco.core.registry import list_substrates, register_substrate

    sub = tmp_path / "alpha-substrate"
    sub.mkdir()
    (sub / "_canon.yaml").write_text("x")
    register_substrate("alpha", sub, home=tmp_path)

    entries = list_substrates(home=tmp_path)
    assert len(entries) == 1
    e = entries[0]
    assert e.substrate_id == "alpha"
    assert e.path == sub.resolve()
    assert e.exists is True


def test_list_substrates_empty_when_file_missing(tmp_path: Path) -> None:
    from myco.core.registry import list_substrates

    assert list_substrates(home=tmp_path) == []


def test_register_multiple_then_list_sorted_desc(tmp_path: Path) -> None:
    """Most-recently-seen entries come first."""
    from myco.core.registry import list_substrates, register_substrate

    sub_a = tmp_path / "a"
    sub_b = tmp_path / "b"
    sub_a.mkdir()
    sub_b.mkdir()

    # Register in order a, b with explicit timestamps so the sort is
    # deterministic.
    register_substrate(
        "alpha",
        sub_a,
        home=tmp_path,
        now=datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc),
    )
    register_substrate(
        "beta",
        sub_b,
        home=tmp_path,
        now=datetime(2026, 2, 1, 12, 0, tzinfo=timezone.utc),
    )

    entries = list_substrates(home=tmp_path)
    assert [e.substrate_id for e in entries] == ["beta", "alpha"]


def test_reregister_updates_last_seen_but_keeps_registered_at(tmp_path: Path) -> None:
    from myco.core.registry import list_substrates, register_substrate

    sub = tmp_path / "sub"
    sub.mkdir()
    t1 = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
    register_substrate("sub", sub, home=tmp_path, now=t1)
    register_substrate("sub", sub, home=tmp_path, now=t2)
    [e] = list_substrates(home=tmp_path)
    assert e.registered_at == t1
    assert e.last_seen_at == t2


def test_stale_entry_still_returned_but_exists_false(tmp_path: Path) -> None:
    """An entry whose path has been deleted survives in the registry
    but ``exists`` is False so callers can filter."""
    from myco.core.registry import list_substrates, register_substrate

    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "_canon.yaml").write_text("x")
    register_substrate("sub", sub, home=tmp_path)
    # Delete the substrate on disk.
    (sub / "_canon.yaml").unlink()
    sub.rmdir()

    [e] = list_substrates(home=tmp_path)
    assert e.substrate_id == "sub"
    assert e.exists is False


def test_malformed_registry_yields_empty_list(tmp_path: Path) -> None:
    """Corrupted YAML must not break callers — return empty list."""
    from myco.core.registry import list_substrates, registry_path

    (tmp_path / ".myco").mkdir()
    registry_path(home=tmp_path).write_text(
        "this isn't: yaml: at all: [[[", encoding="utf-8"
    )
    assert list_substrates(home=tmp_path) == []


def test_touch_substrate_is_same_as_register_for_new_entries(tmp_path: Path) -> None:
    from myco.core.registry import list_substrates, touch_substrate

    sub = tmp_path / "sub"
    sub.mkdir()
    touch_substrate("sub", sub, home=tmp_path)
    [e] = list_substrates(home=tmp_path)
    assert e.substrate_id == "sub"


def test_touch_substrate_swallows_errors(tmp_path: Path) -> None:
    """touch_substrate is best-effort — a registry-write failure must
    never propagate to the surrounding operation.
    """
    from myco.core.registry import touch_substrate

    # Pass a path whose parent can't be created (a file).
    blocker = tmp_path / "blocker"
    blocker.write_text("x")
    # home resolves to .../blocker/.myco/substrates.yaml which will fail
    # because blocker is a file not a directory — but touch_substrate
    # catches the error silently.
    touch_substrate("sub", tmp_path, home=blocker)
    # No assertion needed; the test passes if no exception propagated.
