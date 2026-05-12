"""Tests for ``lb_cluster`` — merged per-dim test files (v0.8.8).

Per-dim test files consolidated to mirror the src/ cluster
merge. Each `# === <stem>` section corresponds to one original
per-dim test file; git history preserves the per-dim state.
"""

from __future__ import annotations

import textwrap
import uuid
from pathlib import Path

from myco.core.identity_cluster import MycoContext, Severity
from myco.homeostasis.dimensions.semantic.lb_cluster import (
    LB1LivingBetsOverdue,
    LB2LivingBetsRegime,
    _compute_peer_count,
    _compute_session_count,
)

# =========================================================================
# test_lb1_living_bets_overdue — see git history for original per-dim file
# =========================================================================


def _write_canon(sub: Path, contract_version: str) -> None:
    """Write a minimal valid _canon.yaml at the given contract_version."""
    canon = textwrap.dedent(
        f"""\
        schema_version: "1"
        contract_version: "{contract_version}"
        identity:
          substrate_id: "test-substrate"
          entry_point: "MYCO.md"
        system:
          write_surface:
            allowed:
              - "_canon.yaml"
              - "docs/**"
          hard_contract:
            rule_count: 7
        subsystems:
          genesis:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )
    (sub / "_canon.yaml").write_text(canon, encoding="utf-8")
    (sub / "MYCO.md").write_text("# entry\n", encoding="utf-8")


def _write_audit(
    sub: Path,
    *,
    version_token: str,
    archived: bool = False,
    suffix: str = "2026-05-10",
) -> Path:
    """Place a Living Bets audit doc under docs/primordia/ (or its
    ``_landed/v0_X_x/`` archive when ``archived`` is True).

    ``version_token`` is the ``vN_M_P`` filename prefix; the resulting
    file matches the LB1 detection regex
    (``v.*_living_bets_audit_*.md``).
    """
    if archived:
        # Park the audit under the era-bucketed archive that v0.5.x
        # already uses (`_landed/v0_5_x/`, `_landed/v0_6_x/`, ...).
        # Parse the major.minor from the version_token.
        parts = version_token.lstrip("v").split("_")
        bucket = f"v{parts[0]}_{parts[1]}_x"
        target_dir = sub / "docs" / "primordia" / "_landed" / bucket
    else:
        target_dir = sub / "docs" / "primordia"
    target_dir.mkdir(parents=True, exist_ok=True)
    audit_path = target_dir / f"{version_token}_living_bets_audit_{suffix}.md"
    audit_path.write_text(
        f"# {version_token} Living Bets Re-Audit\n\nbody\n",
        encoding="utf-8",
    )
    return audit_path


def test_lb1_silent_on_fresh_substrate_pre_v0_7(tmp_path: Path) -> None:
    """v0.6.0 substrate with no audit doc anywhere → 0 findings.

    The Living Bets concept landed at v0.5.6 and the v0.6.0 audit was
    implicit inside the unified-evolution craft, so a fresh v0.6.x
    substrate without a standalone audit file should not be punished.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.6.0")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_silent_when_audit_matches_current_major(tmp_path: Path) -> None:
    """v0.7.5 substrate + v0_7_5_living_bets_audit_*.md → 0 findings."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_fires_low_on_v0_7_with_no_audit(tmp_path: Path) -> None:
    """v0.7.5 substrate + no docs/primordia/ at all → 1 LOW finding."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    # NB: no docs/primordia/ written.
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.dimension_id == "LB1"
    assert finding.category.value == "semantic"
    assert finding.severity is Severity.LOW
    assert "missing" in finding.message.lower()


def test_lb1_fires_low_on_v0_8_with_v0_7_audit_only(tmp_path: Path) -> None:
    """v0.8.0 substrate with only v0_7_*_living_bets_audit_*.md → 1 LOW.

    1 MAJOR overdue, < 2 minor accrued past the v0.7→v0.8 bump.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.0")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.dimension_id == "LB1"
    assert finding.severity is Severity.LOW
    assert "v0.7" in finding.message
    assert "v0.8" in finding.message


def test_lb1_ramps_to_medium_after_5_minor(tmp_path: Path) -> None:
    """v0.8.5 substrate with v0.7 audit → MEDIUM (5 minor past the bump)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.5")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.MEDIUM


def test_lb1_ramps_to_high_after_10_minor(tmp_path: Path) -> None:
    """v0.8.10 substrate with v0.7 audit → HIGH (10 minor past the bump)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.8.10")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.HIGH


def test_lb1_picks_most_recent_audit(tmp_path: Path) -> None:
    """Multiple audits: v0_6_0_*, v0_7_0_*, v0_7_5_* present at v0.7.5
    substrate → silent (the v0_7_5 audit is most recent and matches MAJOR)."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v0_6_0")
    _write_audit(sub, version_token="v0_7_0")
    _write_audit(sub, version_token="v0_7_5")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_handles_landed_archive(tmp_path: Path) -> None:
    """An audit doc moved to docs/primordia/_landed/v0_7_x/... is still
    recognized as the most-recent audit for that MAJOR."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    audit_path = _write_audit(sub, version_token="v0_7_5", archived=True)
    # Sanity: confirm the archive parking actually happened.
    assert "_landed" in audit_path.as_posix()
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


def test_lb1_ignores_unrelated_primordia_files(tmp_path: Path) -> None:
    """Only ``*living_bets_audit*.md`` filenames count; an unrelated
    craft of the same MAJOR does NOT satisfy the cadence."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    primordia = sub / "docs" / "primordia"
    primordia.mkdir(parents=True)
    # An ordinary craft, not an audit.
    (primordia / "v0_7_5_p0_to_p6_omnibus_craft_2026-05-10.md").write_text(
        "# omnibus craft\n", encoding="utf-8"
    )
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW


def test_lb1_silent_when_audit_is_forward_looking(tmp_path: Path) -> None:
    """A v1_0_*_living_bets_audit_*.md craft on a v0.7.x substrate is
    treated as forward-thinking; LB1 stays silent rather than punishing
    the substrate for having too much L0 hygiene."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, "v0.7.5")
    _write_audit(sub, version_token="v1_0_0")
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB1LivingBetsOverdue().run(ctx))
    assert findings == []


# =========================================================================
# test_lb2_living_bets_regime — see git history for original per-dim file
# =========================================================================


def _write_canon_lb2(
    sub: Path,
    *,
    contract_version: str = "v0.8.0",
    federation_peers: list[str] | None = None,
) -> None:
    """Write a minimal valid _canon.yaml.

    ``federation_peers`` defaults to ``[]`` (the v0.6.0+ schema-v2
    default). Pass a list of peer ids to simulate a federated
    substrate.
    """
    if federation_peers:
        peers_lines = "\n".join(f'    - "{p}"' for p in federation_peers)
        peers_block = f"  federation_peers:\n{peers_lines}"
    else:
        peers_block = "  federation_peers: []"
    body = (
        f'schema_version: "1"\n'
        f'contract_version: "{contract_version}"\n'
        f"identity:\n"
        f'  substrate_id: "test-substrate"\n'
        f'  entry_point: "MYCO.md"\n'
        f"{peers_block}\n"
        f"system:\n"
        f"  write_surface:\n"
        f"    allowed:\n"
        f'      - "_canon.yaml"\n'
        f'      - "docs/**"\n'
        f"  hard_contract:\n"
        f"    rule_count: 7\n"
        f"subsystems:\n"
        f"  genesis:\n"
        f'    doc: "docs/architecture/L2_DOCTRINE/genesis.md"\n'
    )
    (sub / "_canon.yaml").write_text(body, encoding="utf-8")
    (sub / "MYCO.md").write_text("# entry\n", encoding="utf-8")


def _write_shim_hits(sub: Path, *, distinct_sessions: int) -> Path:
    """Write a synthetic ``.myco/state/shim_hits.json`` JSONL file with
    ``distinct_sessions`` distinct ``session_id`` values.

    Each line carries one synthetic record matching the real shim
    counter's shape (``module``, ``ts``, ``session_id``).
    """
    state = sub / ".myco/state"
    state.mkdir(parents=True, exist_ok=True)
    path = state / "shim_hits.json"
    lines: list[str] = []
    for i in range(distinct_sessions):
        sid = f"sess-{uuid.UUID(int=i).hex}"
        lines.append(
            '{"module": "myco.mcp", '
            f'"ts": "2026-05-10T00:00:{i % 60:02d}Z", '
            f'"session_id": "{sid}"' + "}"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_lb2_silent_on_federated_substrate(tmp_path: Path) -> None:
    """``federation_peers`` non-empty → bet-winning regime → silent."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub, federation_peers=["peer-a", "peer-b"])
    # Even with zero sessions, a federated substrate is in the
    # winning regime (cross-host coordination is the wager's raison
    # d'etre).
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    assert findings == []


def test_lb2_silent_on_high_session_count(tmp_path: Path) -> None:
    """``session_count >= 50`` → bet-winning regime → silent.

    50 distinct sessions is enough cross-read-window evidence to
    classify the substrate as multi-session even without peers.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)  # peers default to []
    _write_shim_hits(sub, distinct_sessions=60)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    assert findings == []


def test_lb2_silent_on_transitional(tmp_path: Path) -> None:
    """``5 <= session_count < 50`` AND ``peer_count == 0`` → silent."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)
    _write_shim_hits(sub, distinct_sessions=20)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    assert findings == []


def test_lb2_silent_on_missing_state_dir(tmp_path: Path) -> None:
    """No ``.myco/state/`` at all → graceful fallback (silent).

    A fresh substrate with no telemetry corpus has session_count=0,
    which IS in the ephemeral threshold range — but the test below
    (``test_lb2_fires_low_on_ephemeral_substrate``) covers the
    "fires when ephemeral" case explicitly. The "missing state dir"
    test instead asserts that the dim does not raise on an absent
    ``.myco/state/`` and degrades to the same ephemeral verdict
    (i.e. fires LOW, since session_count=0 < 5 and peer_count=0).
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)  # no .myco/state/ written
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    # Missing state dir → session_count=0, peer_count=0 → ephemeral
    # → LOW. The "graceful fallback" guarantee here is "does not
    # raise"; the regime verdict is whatever the signals support.
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW
    assert findings[0].dimension_id == "LB2"


def test_lb2_silent_on_corrupt_jsonl(tmp_path: Path) -> None:
    """Corrupt JSONL lines are skipped silently; valid lines still count.

    Asserts the parse-error fallback path: a file with a mix of
    valid and malformed lines yields only the valid ``session_id``
    values (deduped) without raising. Here we craft the file so
    only 2 valid distinct sessions remain → ephemeral → LOW.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)
    state = sub / ".myco/state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "shim_hits.json").write_text(
        "this is not json\n"
        '{"module": "myco.mcp", "ts": "2026-05-10T00:00:00Z", '
        '"session_id": "valid-1"}\n'
        "{ broken json (\n"
        '{"module": "myco.mcp", "ts": "2026-05-10T00:00:01Z", '
        '"session_id": "valid-2"}\n'
        "\n"
        '{"module": "myco.mcp", "ts": "2026-05-10T00:00:02Z", '
        '"session_id": "valid-1"}\n'  # dup of valid-1
        '"a string, not an object"\n',
        encoding="utf-8",
    )
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    # 2 distinct session_ids → ephemeral → LOW.
    assert len(findings) == 1
    assert findings[0].severity is Severity.LOW


def test_lb2_fires_low_on_ephemeral_substrate(tmp_path: Path) -> None:
    """``session_count < 5`` AND ``peer_count == 0`` → LOW finding.

    The bet-losing regime: agent should explicitly re-decide
    persist-or-delete.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)
    _write_shim_hits(sub, distinct_sessions=2)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    assert len(findings) == 1
    finding = findings[0]
    assert finding.dimension_id == "LB2"
    assert finding.category.value == "semantic"
    assert finding.severity is Severity.LOW
    # The message should surface both the regime label and the
    # substantive decision question it forces.
    msg_lower = finding.message.lower()
    assert "ephemeral" in msg_lower
    assert "persist" in msg_lower or "delete" in msg_lower
    # Should reference the v0.8.0 amendment context so a reader can
    # find the doctrine without grep-searching.
    assert "v0.8.0" in finding.message or "losing" in msg_lower


def test_lb2_signal_computation_session_count_from_shim_hits(
    tmp_path: Path,
) -> None:
    """``_compute_session_count`` de-dups session_ids across JSONL lines."""
    state = tmp_path / ".myco/state"
    state.mkdir(parents=True, exist_ok=True)
    (state / "shim_hits.json").write_text(
        '{"module": "myco.mcp", "ts": "t", "session_id": "a"}\n'
        '{"module": "myco.mcp", "ts": "t", "session_id": "b"}\n'
        '{"module": "myco.mcp", "ts": "t", "session_id": "a"}\n'  # dup
        '{"module": "myco.mcp", "ts": "t", "session_id": "c"}\n',
        encoding="utf-8",
    )
    assert _compute_session_count(state) == 3

    # A second JSONL file in the same dir contributes additional
    # distinct sessions (forward-compat: any future state file with a
    # ``session_id`` key gets picked up).
    (state / "future_state.json").write_text(
        '{"session_id": "d"}\n{"session_id": "a"}\n',  # already counted
        encoding="utf-8",
    )
    assert _compute_session_count(state) == 4

    # Missing dir → 0, never raises.
    assert _compute_session_count(tmp_path / "does-not-exist") == 0


def test_lb2_signal_computation_peer_count_from_canon(
    tmp_path: Path,
) -> None:
    """``_compute_peer_count`` reads ``identity.federation_peers`` length.

    Returns 0 for empty list, missing field, non-list shape, and
    non-mapping identity. Never raises.
    """
    assert _compute_peer_count({"federation_peers": []}) == 0
    assert _compute_peer_count({"federation_peers": ["a"]}) == 1
    assert _compute_peer_count({"federation_peers": ["a", "b", "c"]}) == 3
    # Field absent.
    assert _compute_peer_count({"substrate_id": "x"}) == 0
    # Wrong shape — not a list.
    assert _compute_peer_count({"federation_peers": "not-a-list"}) == 0
    assert _compute_peer_count({"federation_peers": {"k": "v"}}) == 0
    # Identity isn't a mapping at all.
    assert _compute_peer_count(None) == 0
    assert _compute_peer_count("string-identity") == 0


def test_lb2_silent_on_threshold_boundary(tmp_path: Path) -> None:
    """Exactly 5 sessions → transitional (silent); exactly 50 → winning (silent).

    Boundary check: the ephemeral predicate is strict < 5 and the
    bet-winning predicate is >= 50. Both boundaries are silent.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon_lb2(sub)
    _write_shim_hits(sub, distinct_sessions=5)
    ctx = MycoContext.for_testing(root=sub)
    assert list(LB2LivingBetsRegime().run(ctx)) == []

    sub2 = tmp_path / "sub2"
    sub2.mkdir()
    _write_canon_lb2(sub2)
    _write_shim_hits(sub2, distinct_sessions=50)
    ctx2 = MycoContext.for_testing(root=sub2)
    assert list(LB2LivingBetsRegime().run(ctx2)) == []
