"""Trigger-path tests for v0.7.2 永恒删减 ratchet dims.

Covers MB8 (shim-hit counter), PA6 (repo bloat), MF5 (mirror integrity),
SE5 (version-anchor freshness). Mirrors the test_v0_6_dims_triggers.py
shape: each test sets up the trigger condition + asserts emission.

v0.8.5 — the v0.7.2 risk_classifier recursion-cutter test cluster
that previously lived in this file (5 tests + helper) was excreted
together with ``src/myco/core/risk_classifier.py`` — the module had
zero production-code imports across the 4 minor releases since
v0.6.0. The shim ``__main__`` counter-write hook tests already
moved to ``tests/unit/boundary/test_legacy_mcp_shim_warning.py``
in v0.7.5.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.identity_cluster import MycoContext
from myco.homeostasis.dimensions.mechanical.mf_cluster import (
    MF5GeneratedMirrorIntegrity,
)
from myco.homeostasis.dimensions.mechanical.pa_cluster import PA6RepoBloat
from myco.homeostasis.dimensions.metabolic.mb_cluster import (
    MB8ShimHitCounter,
)
from myco.homeostasis.dimensions.semantic.se_cluster import (
    SE5VersionAnchorFreshness,
)


def _write_minimal_canon(sub: Path, **extra_yaml: str) -> None:
    """Write a minimal _canon.yaml + entry-point file for ctx.for_testing."""
    base = (
        'schema_version: "2"\ncontract_version: "v0.7.2"\n'
        'synced_contract_version: "v0.7.2"\n'
        'identity:\n  substrate_id: "x"\n  entry_point: "M.md"\n'
        "system:\n  write_surface:\n    allowed: ['_canon.yaml']\n"
        "  hard_contract:\n    rule_count: 7\n"
        "subsystems:\n  ingestion:\n    package: 'src/'\n"
    )
    if "metrics_block" in extra_yaml:
        base += extra_yaml["metrics_block"]
    (sub / "_canon.yaml").write_text(base, encoding="utf-8")
    (sub / "M.md").write_text("# x", encoding="utf-8")


# ===== MB8 — shim-hit counter =====


def test_mb8_no_state_file_silent(tmp_path: Path) -> None:
    """Fresh substrate (no .myco/state/shim_hits.json) → no findings."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(MB8ShimHitCounter().run(ctx)) == []


def test_mb8_emits_on_recorded_hits(tmp_path: Path) -> None:
    """Substrate with shim_hits.json entries → MB8 emits one finding per module."""
    sub = tmp_path / "sub"
    state_dir = sub / ".myco/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    hits = state_dir / "shim_hits.json"
    hits.write_text(
        '{"module": "myco.mcp", "ts": "2026-04-30T00:00:00Z", "session_id": "s1"}\n'
        '{"module": "myco.mcp", "ts": "2026-04-30T01:00:00Z", "session_id": "s2"}\n'
        '{"module": "myco.mcp", "ts": "2026-04-30T02:00:00Z", "session_id": "s3"}\n',
        encoding="utf-8",
    )
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MB8ShimHitCounter().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MB8"
    assert "myco.mcp" in findings[0].message
    assert "3 time(s)" in findings[0].message


def test_mb8_skips_malformed_jsonl_lines(tmp_path: Path) -> None:
    """Malformed JSONL lines are silently skipped (best-effort telemetry)."""
    sub = tmp_path / "sub"
    state_dir = sub / ".myco/state"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "shim_hits.json").write_text(
        '{"module": "myco.mcp", "ts": "2026-04-30T00:00:00Z"}\n'
        "not json at all\n"
        '{"module": "myco.mcp", "ts": "2026-04-30T01:00:00Z"}\n'
        '{"module": null, "ts": "2026-04-30T02:00:00Z"}\n'  # invalid module type
        "\n",  # blank line
        encoding="utf-8",
    )
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MB8ShimHitCounter().run(ctx))
    assert len(findings) == 1
    assert "2 time(s)" in findings[0].message  # 2 valid records, 3 skipped


# ===== PA6 — repo bloat =====


def test_pa6_under_threshold_silent(tmp_path: Path) -> None:
    """Repo well under threshold (50 MB default) → no findings."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "small.txt").write_text("x" * 1000, encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(PA6RepoBloat().run(ctx)) == []


def test_pa6_over_threshold_emits_high(tmp_path: Path) -> None:
    """Repo over threshold → HIGH severity finding."""
    sub = tmp_path / "sub"
    sub.mkdir()
    # 5 MB file with a 4 MB threshold
    (sub / "big.bin").write_bytes(b"x" * (5 * 1024 * 1024))
    _write_minimal_canon(
        sub,
        metrics_block="metrics:\n  repo_size_max_bytes: 4194304\n",  # 4 MB
    )
    ctx = MycoContext.for_testing(root=sub)
    findings = list(PA6RepoBloat().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "PA6"
    assert "exceeded" in findings[0].message


def test_pa6_excluded_globs_protect_ingestion(tmp_path: Path) -> None:
    """Files under metrics.repo_size_excluded globs are NOT counted (rhizomorph T1)."""
    sub = tmp_path / "sub"
    notes = sub / "notes"
    notes.mkdir(parents=True)
    # 5 MB inside notes/ — must NOT trigger
    (notes / "big.bin").write_bytes(b"x" * (5 * 1024 * 1024))
    _write_minimal_canon(
        sub,
        metrics_block=(
            "metrics:\n"
            "  repo_size_max_bytes: 4194304\n"
            "  repo_size_excluded: ['notes/**']\n"
        ),
    )
    ctx = MycoContext.for_testing(root=sub)
    assert list(PA6RepoBloat().run(ctx)) == []


# ===== MF5 — drift detector for retired mirror paths (v0.8.8) =====


def test_mf5_silent_when_no_forbidden_mirror_exists(tmp_path: Path) -> None:
    """v0.8.8: only `.claude/agents/` exists, `.plugin/agents/` absent →
    silent (the desired single-source-of-truth state)."""
    sub = tmp_path / "sub"
    canon_dir = sub / ".claude" / "agents"
    canon_dir.mkdir(parents=True)
    body = "---\nname: foo\n---\n\n# Foo agent\n" + ("body line\n" * 30)
    (canon_dir / "foo.md").write_text(body, encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(MF5GeneratedMirrorIntegrity().run(ctx)) == []


def test_mf5_unintended_duplicate_emits_medium(tmp_path: Path) -> None:
    """v0.8.8: file appears at both `.claude/agents/` AND `.plugin/agents/`
    (the retired mirror path), byte-identical → UNINTENDED_DUPLICATE MEDIUM."""
    sub = tmp_path / "sub"
    canon_dir = sub / ".claude" / "agents"
    forbidden_dir = sub / ".plugin" / "agents"
    canon_dir.mkdir(parents=True)
    forbidden_dir.mkdir(parents=True)
    same_bytes = "---\nname: foo\n---\n\n# Foo agent\n" + ("body line\n" * 30)
    (canon_dir / "foo.md").write_text(same_bytes, encoding="utf-8")
    (forbidden_dir / "foo.md").write_text(same_bytes, encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MF5GeneratedMirrorIntegrity().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MF5"
    assert "UNINTENDED_DUPLICATE" in findings[0].message
    assert findings[0].severity.name == "MEDIUM"


def test_mf5_mirror_drift_emits_medium(tmp_path: Path) -> None:
    """v0.8.8: file at both paths with divergent bytes → MIRROR_DRIFT
    MEDIUM (the retired-mirror copy is stale doctrine; delete it)."""
    sub = tmp_path / "sub"
    canon_dir = sub / ".claude" / "agents"
    forbidden_dir = sub / ".plugin" / "agents"
    canon_dir.mkdir(parents=True)
    forbidden_dir.mkdir(parents=True)
    (canon_dir / "foo.md").write_text("canon version\n", encoding="utf-8")
    (forbidden_dir / "foo.md").write_text("stale mirror version\n", encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MF5GeneratedMirrorIntegrity().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MF5"
    assert "MIRROR_DRIFT" in findings[0].message
    assert findings[0].severity.name == "MEDIUM"


def test_mf5_mirror_resurrected_emits_medium(tmp_path: Path) -> None:
    """v0.8.8: file appears ONLY at the retired `.plugin/agents/` path
    (with canonical `.claude/agents/` empty) → MIRROR_RESURRECTED MEDIUM."""
    sub = tmp_path / "sub"
    canon_dir = sub / ".claude" / "agents"
    forbidden_dir = sub / ".plugin" / "agents"
    canon_dir.mkdir(parents=True)
    forbidden_dir.mkdir(parents=True)
    (forbidden_dir / "stray.md").write_text("only-in-forbidden\n", encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MF5GeneratedMirrorIntegrity().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MF5"
    assert "MIRROR_RESURRECTED" in findings[0].message
    assert findings[0].severity.name == "MEDIUM"


# ===== SE5 — version-anchor freshness =====


def test_se5_stale_anchor_in_doctrine_emits(tmp_path: Path) -> None:
    """A stale `v0.3.0` anchor in docs/architecture/L2_DOCTRINE/foo.md
    with current=v0.7.2 (delta = 4 minor, > 3 default window) → finding.

    v0.8.5 — the fixture text avoids natural-English historical tokens
    (``the v``, ``at v``, ``before v``, etc.) so the anchor fires
    cleanly. SE5's permissive prose suppression treats most contextual
    English as historical; a genuine stale claim like "Use vX.Y.Z" with
    no surrounding context is the canonical stale shape.
    """
    sub = tmp_path / "sub"
    doctrine = sub / "docs" / "architecture" / "L2_DOCTRINE"
    doctrine.mkdir(parents=True)
    (doctrine / "foo.md").write_text(
        "Use v0.3.0 in production code paths today.\n",
        encoding="utf-8",
    )
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(SE5VersionAnchorFreshness().run(ctx))
    stale_messages = [f.message for f in findings if "v0.3.0" in f.message]
    assert len(stale_messages) >= 1
    assert "stale version anchor" in stale_messages[0]


def test_se5_historical_context_suppresses(tmp_path: Path) -> None:
    """A clearly-stale `v0.3.0` anchor preceded by 'shipped at' is treated as
    legitimate historical reference (mycorrhiza T7 heuristic)."""
    sub = tmp_path / "sub"
    doctrine = sub / "docs" / "architecture" / "L2_DOCTRINE"
    doctrine.mkdir(parents=True)
    (doctrine / "foo.md").write_text(
        "This feature was shipped at v0.3.0 and refined later.\n",
        encoding="utf-8",
    )
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(SE5VersionAnchorFreshness().run(ctx))
    assert all("v0.3.0" not in f.message for f in findings)


def test_se5_recent_anchor_silent(tmp_path: Path) -> None:
    """A `v0.7.0` anchor with current=v0.7.2 (delta = 2 minor, within window)
    → no finding."""
    sub = tmp_path / "sub"
    doctrine = sub / "docs" / "architecture" / "L2_DOCTRINE"
    doctrine.mkdir(parents=True)
    (doctrine / "foo.md").write_text("Current at v0.7.0 behavior\n", encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(SE5VersionAnchorFreshness().run(ctx))
    assert all("v0.7.0" not in f.message for f in findings)


# v0.8.5 — the v0.7.2 risk_classifier recursion-cutter test cluster
# (5 tests + _write_craft helper) was excreted with the module.
# The shim __main__.py counter-write hook tests live at
# ``tests/unit/boundary/test_legacy_mcp_shim_warning.py``.
