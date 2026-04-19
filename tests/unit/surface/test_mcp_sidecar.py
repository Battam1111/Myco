"""Tests for the substrate-pulse sidecar and initialization instructions.

These are the cross-platform enforcement mechanism for R1-R7 — they
fire on every MCP client (Claude Code, Cursor, Zed, Codex, Windsurf,
Gemini, Continue, Claude Desktop) regardless of whether the host
supports session hooks. Tests here pin the contract of that sidecar
so future refactors cannot silently drop the substrate_pulse or
strip the R1-R7 block from the initialization instructions.
"""

from __future__ import annotations

from pathlib import Path

from myco.surface.manifest import load_manifest
from myco.surface.mcp import (
    _compute_substrate_pulse,
    _invoke,
    _ServerState,
    build_initialization_instructions,
)

# ---------------------------------------------------------------------------
# build_initialization_instructions
# ---------------------------------------------------------------------------


def test_instructions_name_every_rule() -> None:
    text = build_initialization_instructions()
    for rule_marker in ("R1 ", "R2 ", "R3 ", "R4 ", "R5 ", "R6 ", "R7 "):
        assert rule_marker in text, rule_marker


def test_instructions_reference_protocol_doc() -> None:
    text = build_initialization_instructions()
    assert "docs/architecture/L1_CONTRACT/protocol.md" in text


def test_instructions_count_verbs_from_manifest() -> None:
    m = load_manifest()
    text = build_initialization_instructions(m)
    assert str(len(m.commands)) in text


def test_instructions_mention_substrate_pulse_field() -> None:
    text = build_initialization_instructions()
    assert "substrate_pulse" in text, (
        "The agent must be told what to look for in every tool response."
    )


# ---------------------------------------------------------------------------
# _compute_substrate_pulse
# ---------------------------------------------------------------------------


def test_pulse_has_required_keys() -> None:
    pulse = _compute_substrate_pulse("hunger")
    for key in ("substrate_id", "contract_version", "hard_contract_ref", "rules_hint"):
        assert key in pulse, key


def test_pulse_reads_canon_when_present(tmp_path: Path) -> None:
    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.4.1-test'\n"
        "identity:\n"
        "  substrate_id: 'pulse-test'\n"
        "  entry_point: 'MYCO.md'\n",
        encoding="utf-8",
    )
    pulse = _compute_substrate_pulse("sense", project_dir=tmp_path)
    assert pulse["substrate_id"] == "pulse-test"
    assert pulse["contract_version"] == "v0.4.1-test"


def test_pulse_degrades_gracefully_without_canon(tmp_path: Path) -> None:
    pulse = _compute_substrate_pulse("hunger", project_dir=tmp_path)
    assert "no substrate detected" in pulse["substrate_id"]
    assert pulse["contract_version"] == "(unknown)"


def test_pulse_hint_steers_toward_r1_before_hunger() -> None:
    pulse = _compute_substrate_pulse("eat", hunger_called=False)
    assert "R1" in pulse["rules_hint"]
    assert "myco_hunger" in pulse["rules_hint"]


def test_pulse_hint_steers_toward_r3_after_hunger() -> None:
    pulse = _compute_substrate_pulse("eat", hunger_called=True)
    assert "R3" in pulse["rules_hint"]
    assert "myco_sense" in pulse["rules_hint"]


def test_pulse_hint_acknowledges_boot_when_hunger_is_the_call() -> None:
    pulse = _compute_substrate_pulse("hunger", hunger_called=False)
    assert "Boot ritual" in pulse["rules_hint"]


# ---------------------------------------------------------------------------
# _ServerState + _invoke wrapping
# ---------------------------------------------------------------------------


def test_server_state_starts_cold() -> None:
    state = _ServerState()
    assert state.hunger_called is False


def test_invoke_wraps_response_with_pulse(tmp_path: Path) -> None:
    """Every tool response must carry a substrate_pulse dict — the
    very point of the sidecar.
    """
    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.4.1-test'\n"
        "identity:\n"
        "  substrate_id: 'invoke-test'\n"
        "  entry_point: 'MYCO.md'\n"
        "system:\n"
        "  write_surface:\n"
        "    allowed: ['notes/**']\n",
        encoding="utf-8",
    )
    m = load_manifest()
    sense_spec = m.by_name("sense")
    state = _ServerState()
    result = _invoke(
        sense_spec,
        m,
        {"query": "x", "project_dir": str(tmp_path)},
        state,
    )
    assert "substrate_pulse" in result
    assert result["substrate_pulse"]["substrate_id"] == "invoke-test"


def test_invoke_sets_hunger_called_on_hunger(tmp_path: Path) -> None:
    """After a hunger invocation, subsequent pulses should hint at R3
    rather than R1.
    """
    (tmp_path / "_canon.yaml").write_text(
        "schema_version: '1'\n"
        "contract_version: 'v0.4.1-test'\n"
        "identity:\n"
        "  substrate_id: 'hunger-tracking-test'\n"
        "  entry_point: 'MYCO.md'\n"
        "system:\n"
        "  write_surface:\n"
        "    allowed: ['notes/**']\n",
        encoding="utf-8",
    )
    m = load_manifest()
    hunger_spec = m.by_name("hunger")
    state = _ServerState()
    assert state.hunger_called is False
    _invoke(hunger_spec, m, {"project_dir": str(tmp_path)}, state)
    assert state.hunger_called is True

    sense_spec = m.by_name("sense")
    second = _invoke(
        sense_spec,
        m,
        {"query": "x", "project_dir": str(tmp_path)},
        state,
    )
    assert "R3" in second["substrate_pulse"]["rules_hint"]
