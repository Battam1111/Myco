"""Tests for ``myco.core.canon``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.canon import Canon, load_canon
from myco.core.errors import CanonSchemaError


def test_minimal_valid_parses(seeded_substrate: Path) -> None:
    c = load_canon(seeded_substrate / "_canon.yaml")
    assert isinstance(c, Canon)
    # v0.6.0: v1 substrates are silently auto-upgraded by the
    # registered _v1_to_v2 chain. v0.7.5: the chain extends to v3
    # via _v2_to_v3, so the fixture (schema_version "1") now lands
    # at "3" without warning. ``metrics.lint_dim_count`` is seeded
    # to ``None`` by the v2→v3 partial.
    assert c.schema_version == "3"
    assert c.metrics.get("lint_dim_count") is None
    assert c.contract_version == "v0.4.0-alpha.1"
    assert c.substrate_id == "test-substrate"
    assert c.tags == ("test",)
    assert c.entry_point == "MYCO.md"


def test_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(CanonSchemaError, match="not found"):
        load_canon(tmp_path / "_canon.yaml")


def test_invalid_yaml_raises(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text("key: [unterminated\n", encoding="utf-8")
    with pytest.raises(CanonSchemaError, match="not valid YAML"):
        load_canon(p)


def test_non_mapping_root_raises(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text("- just\n- a\n- list\n", encoding="utf-8")
    with pytest.raises(CanonSchemaError, match="must be a mapping"):
        load_canon(p)


def test_empty_file_raises(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text("", encoding="utf-8")
    with pytest.raises(CanonSchemaError, match="empty"):
        load_canon(p)


def test_missing_required_key_raises(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text(
        'schema_version: "1"\ncontract_version: "v0.4.0"\n',
        encoding="utf-8",
    )
    with pytest.raises(CanonSchemaError, match="missing required key"):
        load_canon(p)


def test_unknown_schema_version_warns(tmp_path: Path, minimal_canon_text: str) -> None:
    """Forward-compat (v0.5): unknown schema_version warns, does not raise.

    "You never migrate again" requires that an older kernel reading a
    newer canon emits a warning and proceeds best-effort rather than
    halting the agent's session. See
    ``docs/primordia/v0_5_0_major_6_10_craft_2026-04-17.md``.
    """
    p = tmp_path / "_canon.yaml"
    p.write_text(
        minimal_canon_text.replace('schema_version: "1"', 'schema_version: "999"'),
        encoding="utf-8",
    )
    with pytest.warns(UserWarning, match="schema_version"):
        c = load_canon(p)
    assert c.schema_version == "999"


def test_schema_upgrader_runs_and_silences_warning(
    tmp_path: Path, minimal_canon_text: str
) -> None:
    """A registered upgrader transforms the raw mapping to a known version.

    v0.6.0 update: schema "1" and "2" are now both KNOWN_SCHEMA_VERSIONS;
    we use a hypothetical "999" → "2" upgrader chain to demonstrate the
    silencing behavior. The actual production upgrader (`_v1_to_v2`)
    is exercised by `test_canon_schema_v1_to_v2.py` (separate file).

    v0.7.5 update: ``_apply_upgraders`` no longer early-exits when the
    next version happens to be in ``KNOWN_SCHEMA_VERSIONS`` — it walks
    the chain to the latest registered version (no upgrader). So a
    "999" → "2" hop now continues "2" → "3" via the production v2→v3
    upgrader. The end-state observed by ``load_canon`` is therefore
    "3" (the latest), not "2". The silencing-warning property is what
    this test pins; the exact landing version drifts forward whenever
    a new schema version ships, which is the point of the chain.
    """
    from myco.core import canon as _canon

    def _v999_to_v2(raw):
        raw = dict(raw)
        raw["schema_version"] = "2"
        return raw

    _canon.schema_upgraders["999"] = _v999_to_v2
    try:
        p = tmp_path / "_canon.yaml"
        p.write_text(
            minimal_canon_text.replace('schema_version: "1"', 'schema_version: "999"'),
            encoding="utf-8",
        )
        import warnings as _w

        with _w.catch_warnings():
            _w.simplefilter("error")  # any UserWarning would raise
            c = load_canon(p)
        # v0.7.5: chain runs to latest. "999" → "2" → "3".
        assert c.schema_version == "3"
    finally:
        _canon.schema_upgraders.pop("999", None)


def test_schema_upgrader_cycle_raises(tmp_path: Path, minimal_canon_text: str) -> None:
    from myco.core import canon as _canon

    def _loop(raw):
        raw = dict(raw)
        raw["schema_version"] = "loop"
        return raw

    _canon.schema_upgraders["loop"] = _loop
    try:
        p = tmp_path / "_canon.yaml"
        p.write_text(
            minimal_canon_text.replace('schema_version: "1"', 'schema_version: "loop"'),
            encoding="utf-8",
        )
        with pytest.raises(CanonSchemaError, match="cycle"):
            load_canon(p)
    finally:
        _canon.schema_upgraders.pop("loop", None)


def test_unknown_top_level_preserved_in_extras(
    tmp_path: Path, minimal_canon_text: str
) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text(
        minimal_canon_text + 'custom_field:\n  foo: "bar"\n',
        encoding="utf-8",
    )
    c = load_canon(p)
    assert "custom_field" in c.extras
    assert c.extras["custom_field"] == {"foo": "bar"}


def test_identity_must_be_mapping(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text(
        'schema_version: "1"\n'
        'contract_version: "v0.4.0"\n'
        "identity: not-a-mapping\n"
        "system:\n  x: y\n"
        "subsystems:\n  y: z\n",
        encoding="utf-8",
    )
    with pytest.raises(CanonSchemaError, match="must be a mapping"):
        load_canon(p)


def test_empty_identity_raises(tmp_path: Path) -> None:
    p = tmp_path / "_canon.yaml"
    p.write_text(
        'schema_version: "1"\n'
        'contract_version: "v0.4.0"\n'
        "identity: {}\n"
        "system: {x: 1}\n"
        "subsystems: {y: 1}\n",
        encoding="utf-8",
    )
    with pytest.raises(CanonSchemaError, match="identity"):
        load_canon(p)
