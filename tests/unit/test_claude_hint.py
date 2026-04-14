"""Tests for claude_hint computation (Wave 56)."""

from pathlib import Path

import pytest

from myco.mcp_server import _compute_claude_hint, _inject_sidecar


class TestComputeClaudeHint:
    def test_boot_warning_dominates(self, tmp_path):
        sidecar = {"WARNING": "boot ritual missed", "raw_count": 0}
        hint = _compute_claude_hint(sidecar, "myco_pulse", tmp_path)
        assert hint is not None
        assert "hunger" in hint.lower()

    def test_eat_returns_digest_hint(self, tmp_path):
        sidecar = {"raw_count": 2}
        hint = _compute_claude_hint(sidecar, "myco_eat", tmp_path)
        assert hint is not None
        assert "digest" in hint.lower()

    def test_scent_returns_eat_hint(self, tmp_path):
        sidecar = {"raw_count": 0}
        hint = _compute_claude_hint(sidecar, "myco_scent", tmp_path)
        assert hint is not None
        assert "eat" in hint.lower()

    def test_digest_returns_verify_hint(self, tmp_path):
        sidecar = {"raw_count": 1}
        hint = _compute_claude_hint(sidecar, "myco_digest", tmp_path)
        assert hint is not None
        assert "immune" in hint.lower()

    def test_hunger_low_raw_none(self, tmp_path):
        sidecar = {"raw_count": 1}
        hint = _compute_claude_hint(sidecar, "myco_hunger", tmp_path)
        # Low raw count on hunger → no hint
        assert hint is None

    def test_hunger_high_raw_digest(self, tmp_path):
        sidecar = {"raw_count": 10}
        hint = _compute_claude_hint(sidecar, "myco_hunger", tmp_path)
        assert hint is not None
        assert "digest" in hint.lower()

    def test_global_backlog_fallback(self, tmp_path):
        sidecar = {"raw_count": 12}
        hint = _compute_claude_hint(sidecar, "myco_trace", tmp_path)
        assert hint is not None
        assert "backlog" in hint.lower() or "digest" in hint.lower()


class TestInjectSidecar:
    def test_injects_hint_on_dict_response(self, tmp_path):
        import json
        # Prepare a fake project root (sidecar compute is safe with empty dir)
        response = json.dumps({"status": "ok"})
        injected = _inject_sidecar(response, tmp_path, tool_name="myco_eat")
        data = json.loads(injected)
        assert "_myco_sidecar" in data
        # eat hint should be present (sidecar has no WARNING since brief doesn't exist — boot_stale=True)
        # With boot_stale, WARNING fires and dominates.
        assert "claude_hint" in data

    def test_no_hint_doesnt_break(self, tmp_path):
        import json
        # Write boot_brief so boot isn't stale
        bd = tmp_path / ".myco_state"
        bd.mkdir()
        (bd / "boot_brief.md").write_text("fresh")
        response = json.dumps({"status": "ok"})
        injected = _inject_sidecar(response, tmp_path, tool_name="myco_hunger")
        data = json.loads(injected)
        assert "_myco_sidecar" in data
        # hunger with zero raw shouldn't produce a hint
        # (it's ok if a hint is present; just verify JSON is valid)
