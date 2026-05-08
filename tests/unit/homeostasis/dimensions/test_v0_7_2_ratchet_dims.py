"""Trigger-path tests for v0.7.2 永恒删减 ratchet dims.

Covers MB8 (shim-hit counter), PA6 (repo bloat), MF5 (mirror integrity),
SE5 (version-anchor freshness). Mirrors the test_v0_6_dims_triggers.py
shape: each test sets up the trigger condition + asserts emission.

Plus tests for the v0.7.2 risk_classifier extensions:
- shim-hits.json + src/myco/mcp/** in recursion-cutter PATH_PATTERNS
- metrics.* + governance.shim_sunset_* in CANON_KEYS
- multi-cluster compound trigger.

Plus a test for the shim's __main__.py counter-write hook.
"""

from __future__ import annotations

import json
from pathlib import Path

from myco.core.context import MycoContext
from myco.core.risk_classifier import (
    RiskTier,
    classify_craft_via_path_allowlist,
)
from myco.homeostasis.dimensions.mechanical.mf5_generated_mirror_integrity import (
    MF5GeneratedMirrorIntegrity,
)
from myco.homeostasis.dimensions.mechanical.pa6_repo_bloat import PA6RepoBloat
from myco.homeostasis.dimensions.metabolic.mb8_shim_hit_counter import (
    MB8ShimHitCounter,
)
from myco.homeostasis.dimensions.semantic.se5_version_anchor_freshness import (
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
    """Fresh substrate (no .myco_state/shim_hits.json) → no findings."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(MB8ShimHitCounter().run(ctx)) == []


def test_mb8_emits_on_recorded_hits(tmp_path: Path) -> None:
    """Substrate with shim_hits.json entries → MB8 emits one finding per module."""
    sub = tmp_path / "sub"
    state_dir = sub / ".myco_state"
    state_dir.mkdir(parents=True)
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
    state_dir = sub / ".myco_state"
    state_dir.mkdir(parents=True)
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


# ===== MF5 — generated-mirror integrity =====


def test_mf5_intended_v0_6_11_mirror_silent_when_synced(tmp_path: Path) -> None:
    """v0.7.3 reclassified: byte-identical .claude/agents/X.md ↔
    <repo>/agents/X.md is the desired state per v0.6.11 plugin spec
    (both project + bundle scopes mandated). NO finding emitted."""
    sub = tmp_path / "sub"
    project_dir = sub / ".claude" / "agents"
    bundle_dir = sub / "agents"
    project_dir.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    same_bytes = "---\nname: foo\n---\n\n# Foo agent\n" + ("body line\n" * 30)
    (project_dir / "foo.md").write_text(same_bytes, encoding="utf-8")
    (bundle_dir / "foo.md").write_text(same_bytes, encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(MF5GeneratedMirrorIntegrity().run(ctx)) == []


def test_mf5_drift_emits_medium(tmp_path: Path) -> None:
    """v0.7.3: same filename in project + bundle dirs but byte-divergent →
    MIRROR_DRIFT MEDIUM finding."""
    sub = tmp_path / "sub"
    project_dir = sub / ".claude" / "agents"
    bundle_dir = sub / "agents"
    project_dir.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    (project_dir / "foo.md").write_text("project version\n", encoding="utf-8")
    (bundle_dir / "foo.md").write_text("bundle version\n", encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(MF5GeneratedMirrorIntegrity().run(ctx))
    assert len(findings) == 1
    assert findings[0].dimension_id == "MF5"
    assert "MIRROR_DRIFT" in findings[0].message
    assert findings[0].severity.name == "MEDIUM"


def test_mf5_unbalanced_pair_silent(tmp_path: Path) -> None:
    """v0.7.3: file in only one of the two mirror dirs → silent (might
    be in-flight addition)."""
    sub = tmp_path / "sub"
    project_dir = sub / ".claude" / "agents"
    bundle_dir = sub / "agents"
    project_dir.mkdir(parents=True)
    bundle_dir.mkdir(parents=True)
    (project_dir / "foo.md").write_text("only-in-project\n", encoding="utf-8")
    _write_minimal_canon(sub)
    ctx = MycoContext.for_testing(root=sub)
    assert list(MF5GeneratedMirrorIntegrity().run(ctx)) == []


# ===== SE5 — version-anchor freshness =====


def test_se5_stale_anchor_in_doctrine_emits(tmp_path: Path) -> None:
    """A stale `v0.3.0` anchor in docs/architecture/L2_DOCTRINE/foo.md
    with current=v0.7.2 (delta = 4 minor, > 3 default window) → finding."""
    sub = tmp_path / "sub"
    doctrine = sub / "docs" / "architecture" / "L2_DOCTRINE"
    doctrine.mkdir(parents=True)
    (doctrine / "foo.md").write_text(
        "Current state at v0.3.0 — this is stale.\n",
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


# ===== Risk classifier — v0.7.2 recursion-cutter extensions =====


def _write_craft(tmp_path: Path, name: str, *, path_allowlist: list[str]) -> Path:
    """Helper: write a v0.6.15-shaped craft markdown."""
    fm_lines = [
        "type: craft",
        f"slug: {name}",
        "kind: design",
        "date: 2026-04-30",
        "rounds: 3",
        "status: DRAFT",
        "authored_by: claude-code-agent",
        "path_allowlist:",
    ]
    for p in path_allowlist:
        fm_lines.append(f"  - {p}")
    fm = "\n".join(fm_lines)
    text = f"---\n{fm}\n---\n\n# {name}\n\nbody\n"
    p = tmp_path / f"{name}.md"
    p.write_text(text, encoding="utf-8")
    return p


def test_recursion_cutter_shim_hits_json_path(tmp_path: Path) -> None:
    """Touching .myco_state/shim_hits.json forces HIGH (mycoparasite T1)."""
    craft = _write_craft(
        tmp_path,
        "zero_shim_counter",
        path_allowlist=[".myco_state/shim_hits.json"],
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH


def test_recursion_cutter_shim_package_path(tmp_path: Path) -> None:
    """Touching src/myco/mcp/__init__.py forces HIGH (mycoparasite T1)."""
    craft = _write_craft(
        tmp_path,
        "delete_shim",
        path_allowlist=["src/myco/mcp/__init__.py"],
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH


def test_recursion_cutter_compound_two_clusters(tmp_path: Path) -> None:
    """v0.7.2 multi-cluster trigger: state + shim simultaneously → HIGH (mycoparasite T6)."""
    # Note: each path here individually triggers HIGH via _RECURSION_CUTTER_PATH_PATTERNS,
    # so the compound check is also redundant here. The compound trigger's value is
    # for path combinations where individual paths are MEDIUM/LOW. Test that case below.
    craft = _write_craft(
        tmp_path,
        "compound_shim_state",
        path_allowlist=[
            ".myco_state/shim_hits.json",
            "src/myco/mcp/__init__.py",
        ],
    )
    result = classify_craft_via_path_allowlist(craft)
    assert result.tier is RiskTier.HIGH
    # Either single-path cutter OR compound triggers — both are HIGH.
    assert "recursion-cutter" in result.rationale.lower()


def test_recursion_cutter_metrics_canon_key(tmp_path: Path) -> None:
    """A craft touching _canon.yaml + body mentioning `repo_size_max_bytes:`
    in YAML form → HIGH (mycoparasite T3 — metrics threshold protection).

    The body-key check looks for the key followed by `:` or `=` (yaml/python
    mutation form), so the test body stages the actual proposed mutation.
    """
    fm = (
        "---\n"
        "type: craft\nslug: bump_threshold\nkind: design\n"
        "date: 2026-04-30\nrounds: 3\nstatus: DRAFT\n"
        "authored_by: claude-code-agent\n"
        "path_allowlist:\n  - _canon.yaml\n"
        "---\n\n"
        "# Bump threshold\n\n"
        "Change `metrics.repo_size_max_bytes` from 50 MB to 5 GB:\n\n"
        "```yaml\n"
        "metrics:\n"
        "  repo_size_max_bytes: 5000000000\n"
        "```\n"
    )
    p = tmp_path / "bump.md"
    p.write_text(fm, encoding="utf-8")
    result = classify_craft_via_path_allowlist(p)
    assert result.tier is RiskTier.HIGH
    assert "recursion-cutter" in result.rationale.lower()


def test_recursion_cutter_shim_sunset_canon_key(tmp_path: Path) -> None:
    """A craft touching _canon.yaml + body mentioning shim_sunset_min_zero_cycles → HIGH."""
    fm = (
        "---\n"
        "type: craft\nslug: weaken_sunset\nkind: design\n"
        "date: 2026-04-30\nrounds: 3\nstatus: DRAFT\n"
        "authored_by: claude-code-agent\n"
        "path_allowlist:\n  - _canon.yaml\n"
        "---\n\n"
        "# Weaken sunset\n\n"
        "Reduce `governance.shim_sunset_min_zero_cycles`:\n\n"
        "```yaml\n"
        "governance:\n"
        "  shim_sunset_min_zero_cycles: 0\n"
        "```\n"
    )
    p = tmp_path / "weaken.md"
    p.write_text(fm, encoding="utf-8")
    result = classify_craft_via_path_allowlist(p)
    assert result.tier is RiskTier.HIGH


# ===== Shim __main__.py counter-write hook =====


def test_shim_main_records_hit_to_substrate(tmp_path: Path, monkeypatch) -> None:
    """When the shim's __main__._record_shim_hit() runs against a
    substrate root, it appends a JSONL line to .myco_state/shim_hits.json.
    Best-effort: read-only / missing canon → silent no-op."""
    sub = tmp_path / "sub"
    sub.mkdir()
    (sub / "_canon.yaml").write_text(
        'schema_version: "2"\ncontract_version: "v0.7.2"\n', encoding="utf-8"
    )
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(sub))
    # Import the function under the env override.
    from myco.mcp.__main__ import _record_shim_hit

    _record_shim_hit()
    hits_path = sub / ".myco_state" / "shim_hits.json"
    assert hits_path.is_file()
    lines = [
        line for line in hits_path.read_text(encoding="utf-8").splitlines() if line
    ]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["module"] == "myco.mcp"
    assert "ts" in rec and "session_id" in rec


def test_shim_main_silent_on_missing_canon(tmp_path: Path, monkeypatch) -> None:
    """No _canon.yaml → silent no-op (read-only / non-substrate cwd protection).

    v0.7.0 incident lesson: the shim must NEVER fail to boot the MCP
    server because of telemetry.
    """
    bare = tmp_path / "not_a_substrate"
    bare.mkdir()
    monkeypatch.setenv("MYCO_PROJECT_DIR", str(bare))
    from myco.mcp.__main__ import _record_shim_hit

    # Must not raise.
    _record_shim_hit()
    assert not (bare / ".myco_state").exists()
