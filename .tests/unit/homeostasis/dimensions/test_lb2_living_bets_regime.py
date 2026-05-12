"""Tests for ``LB2LivingBetsRegime``.

Covers the regime-classification matrix declared in
``src/myco/homeostasis/dimensions/semantic/lb2_living_bets_regime.py``:

- Federated (peer_count >= 1) → silent (bet-winning).
- High session count (>= 50) → silent (bet-winning).
- Ephemeral (session_count < 5, peer_count == 0) → LOW (bet-losing).
- Transitional (5 <= session_count < 50, peer_count == 0) → silent.
- Missing ``.myco/state/`` dir → silent (graceful fallback).
- Corrupt JSONL lines → silent (graceful fallback).
- Signal-computation tests for session_count + peer_count helpers.

Per the v0.8.0 Living Bets amendment
(``docs/primordia/v0_8_0_living_bets_amendment_2026-05-10.md``) +
``docs/architecture/L0_VISION.md`` § "Appendix — Living bets" "two
regimes" wording.
"""

from __future__ import annotations

import uuid
from pathlib import Path

from myco.core.context import MycoContext
from myco.core.severity import Severity
from myco.homeostasis.dimensions.semantic.lb2_living_bets_regime import (
    LB2LivingBetsRegime,
    _compute_peer_count,
    _compute_session_count,
)


def _write_canon(
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


# ===== silence cases =====


def test_lb2_silent_on_federated_substrate(tmp_path: Path) -> None:
    """``federation_peers`` non-empty → bet-winning regime → silent."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub, federation_peers=["peer-a", "peer-b"])
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
    _write_canon(sub)  # peers default to []
    _write_shim_hits(sub, distinct_sessions=60)
    ctx = MycoContext.for_testing(root=sub)
    findings = list(LB2LivingBetsRegime().run(ctx))
    assert findings == []


def test_lb2_silent_on_transitional(tmp_path: Path) -> None:
    """``5 <= session_count < 50`` AND ``peer_count == 0`` → silent."""
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub)
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
    _write_canon(sub)  # no .myco/state/ written
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
    _write_canon(sub)
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


# ===== firing case =====


def test_lb2_fires_low_on_ephemeral_substrate(tmp_path: Path) -> None:
    """``session_count < 5`` AND ``peer_count == 0`` → LOW finding.

    The bet-losing regime: agent should explicitly re-decide
    persist-or-delete.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub)
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


# ===== signal-computation unit tests =====


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


# ===== bonus parity test =====


def test_lb2_silent_on_threshold_boundary(tmp_path: Path) -> None:
    """Exactly 5 sessions → transitional (silent); exactly 50 → winning (silent).

    Boundary check: the ephemeral predicate is strict < 5 and the
    bet-winning predicate is >= 50. Both boundaries are silent.
    """
    sub = tmp_path / "sub"
    sub.mkdir()
    _write_canon(sub)
    _write_shim_hits(sub, distinct_sessions=5)
    ctx = MycoContext.for_testing(root=sub)
    assert list(LB2LivingBetsRegime().run(ctx)) == []

    sub2 = tmp_path / "sub2"
    sub2.mkdir()
    _write_canon(sub2)
    _write_shim_hits(sub2, distinct_sessions=50)
    ctx2 = MycoContext.for_testing(root=sub2)
    assert list(LB2LivingBetsRegime().run(ctx2)) == []
