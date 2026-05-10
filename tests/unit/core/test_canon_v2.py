"""Tests for v0.6.0 canon schema v2 features."""

from __future__ import annotations

from pathlib import Path

from myco.core.canon import (
    KNOWN_SCHEMA_VERSIONS,
    _v1_to_v2,
    _v1_to_v2_federation_peers_field,
    _v1_to_v2_lint_dimensions_subfile,
    _v1_to_v2_llm_policy_enum,
    load_canon,
)


def test_known_schema_versions_includes_v2():
    assert "1" in KNOWN_SCHEMA_VERSIONS
    assert "2" in KNOWN_SCHEMA_VERSIONS


def test_v1_to_v2_llm_policy_bool_true_to_forbidden():
    raw = {"system": {"no_llm_in_substrate": True}}
    out = _v1_to_v2_llm_policy_enum(raw)
    assert out["system"]["llm_policy"] == "forbidden"
    assert "no_llm_in_substrate" not in out["system"]


def test_v1_to_v2_llm_policy_bool_false_to_providers_declared():
    raw = {"system": {"no_llm_in_substrate": False}}
    out = _v1_to_v2_llm_policy_enum(raw)
    assert out["system"]["llm_policy"] == "providers-declared"


def test_v1_to_v2_llm_policy_default_when_missing():
    raw = {"system": {}}
    out = _v1_to_v2_llm_policy_enum(raw)
    assert out["system"]["llm_policy"] == "forbidden"


def test_v1_to_v2_llm_policy_preserves_explicit_enum():
    raw = {"system": {"llm_policy": "opt-in"}}
    out = _v1_to_v2_llm_policy_enum(raw)
    assert out["system"]["llm_policy"] == "opt-in"


def test_v1_to_v2_federation_peers_added():
    # v0.6.0 upgrader is defensive: empty identity is left untouched so the
    # empty-identity gate in load_canon still fires. A non-empty identity
    # missing federation_peers receives it as an additive field.
    raw = {"identity": {"substrate_id": "x"}}
    out = _v1_to_v2_federation_peers_field(raw)
    assert out["identity"]["federation_peers"] == []


def test_v1_to_v2_federation_peers_preserved():
    raw = {"identity": {"substrate_id": "x", "federation_peers": ["already-there"]}}
    out = _v1_to_v2_federation_peers_field(raw)
    assert out["identity"]["federation_peers"] == ["already-there"]


def test_v1_to_v2_federation_peers_skips_empty_identity():
    # Empty identity stays empty so the empty-identity gate fires later.
    raw = {"identity": {}}
    out = _v1_to_v2_federation_peers_field(raw)
    assert "federation_peers" not in out["identity"]


def test_v1_to_v2_lint_dimensions_subfile():
    raw = {"lint": {"dimensions": {"M1": "mechanical"}}}
    out = _v1_to_v2_lint_dimensions_subfile(raw)
    assert out["lint"]["dimensions_ref"] == "_canon_lint.yaml"


def test_v1_to_v2_full_chain():
    raw = {
        "schema_version": "1",
        "identity": {"substrate_id": "x"},
        "system": {"no_llm_in_substrate": True},
        "lint": {"dimensions": {"M1": "mechanical"}},
    }
    out = _v1_to_v2(raw)
    assert out["schema_version"] == "2"
    assert out["system"]["llm_policy"] == "forbidden"
    assert out["identity"]["federation_peers"] == []
    assert out["lint"]["dimensions_ref"] == "_canon_lint.yaml"


def test_load_canon_with_sibling_lint_yaml(tmp_path: Path):
    """Sibling _canon_lint.yaml is merged into lint.dimensions."""
    canon_text = """schema_version: "2"
contract_version: "v0.6.0"
identity:
  substrate_id: "test"
  entry_point: "X.md"
system:
  write_surface:
    allowed: ["_canon.yaml"]
  hard_contract:
    rule_count: 7
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
lint:
  dimensions_ref: "_canon_lint.yaml"
"""
    (tmp_path / "_canon.yaml").write_text(canon_text, encoding="utf-8")
    (tmp_path / "_canon_lint.yaml").write_text(
        "dimensions:\n  M1: mechanical\n  PA1: mechanical\n", encoding="utf-8"
    )
    canon = load_canon(tmp_path / "_canon.yaml")
    assert "M1" in (canon.lint.get("dimensions") or {})
    assert "PA1" in (canon.lint.get("dimensions") or {})


def test_load_canon_v1_auto_upgrades(tmp_path: Path):
    """A v1 substrate is silently upgraded by the registered _v1_to_v2."""
    canon_text = """schema_version: "1"
contract_version: "v0.5.24"
identity:
  substrate_id: "test"
  entry_point: "X.md"
system:
  no_llm_in_substrate: true
  write_surface:
    allowed: ["_canon.yaml"]
  hard_contract:
    rule_count: 7
subsystems:
  ingestion:
    package: "src/myco/ingestion/"
"""
    (tmp_path / "_canon.yaml").write_text(canon_text, encoding="utf-8")
    canon = load_canon(tmp_path / "_canon.yaml")
    # v0.6.0: auto-upgrade lifted v1→v2; llm_policy enum present.
    # v0.7.5: chain extends to v3, so end-state is "3" with
    # metrics.lint_dim_count seeded to None.
    assert canon.schema_version == "3"
    assert (canon.system or {}).get("llm_policy") == "forbidden"
    assert (canon.metrics or {}).get("lint_dim_count") is None
