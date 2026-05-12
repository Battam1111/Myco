"""Tests for the v0.6.14 senesce ``_reap_vetoed_intents`` step.

The reaper is best-effort + shell-out only (no LLM call; substrate-side
L0 P1 stays strict). It reads new comments from the auto-evolve tracking
issue via ``gh issue view`` and queues ``vetoed_intent`` JSON blobs to
``.myco/state/auto_evolve_vetoed_pending.json``.

Coverage strategy: monkeypatch ``subprocess.run`` to feed canned ``gh``
output without spawning real processes. Substrate is a minimal genesis
fixture with the v0.6.14 governance block.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
import yaml

from myco.core.context import MycoContext
from myco.cycle.senesce import _reap_vetoed_intents


def _seed_v0_6_14_substrate(
    tmp_path: Path,
    *,
    tracking_issue_id: int | None = 42,
) -> MycoContext:
    """Create a minimal v0.6.14-shaped substrate with governance block.

    Mirrors the canon's v0.6.14 schema enough that the reaper can read
    governance.auto_evolve_tracking_issue_id. Other v0.6.14 fields are
    not load-bearing for reaper tests but included for shape-fidelity.
    """
    canon_dict = {
        "schema_version": "2",
        "contract_version": "v0.6.14",
        "synced_contract_version": "v0.6.14",
        "identity": {
            "substrate_id": "test-substrate",
            "tags": [],
            "entry_point": "MYCO.md",
            "federation_peers": [],
        },
        "system": {
            "write_surface": {"allowed": ["**"]},
            "hard_contract": {
                "rules_ref": "docs/architecture/L1_CONTRACT/protocol.md",
                "rule_count": 7,
            },
            "llm_policy": "forbidden",
            "governance": {
                "auto_propose_enabled": False,
                "auto_evolve_tracking_issue_id": tracking_issue_id,
                "last_winnowed_proposals": [],
            },
        },
        "lint": {
            "categories": ["mechanical", "shipped", "metabolic", "semantic"],
            "exit_policy": {"default": "mechanical:critical"},
        },
        # Canon requires non-empty subsystems map; a minimal fixture entry
        # satisfies the schema gate.
        "subsystems": {
            "ingestion": {
                "doc": "docs/architecture/L2_DOCTRINE/ingestion.md",
                "package": "src/myco/ingestion/",
            }
        },
    }
    canon_path = tmp_path / "_canon.yaml"
    canon_path.write_text(yaml.safe_dump(canon_dict), encoding="utf-8")
    (tmp_path / "MYCO.md").write_text("# test\n", encoding="utf-8")
    (tmp_path / "notes").mkdir()
    (tmp_path / "notes" / "raw").mkdir()
    (tmp_path / "notes" / "integrated").mkdir()
    (tmp_path / "notes" / "distilled").mkdir()
    (tmp_path / ".myco/state").mkdir(parents=True, exist_ok=True)
    return MycoContext.for_testing(root=tmp_path)


def test_reaper_skips_when_tracking_issue_unset(tmp_path: Path) -> None:
    """Tracking issue id None → return early with skipped_reason."""
    ctx = _seed_v0_6_14_substrate(tmp_path, tracking_issue_id=None)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
    assert "skipped_reason" in result
    assert "null" in result["skipped_reason"]


def test_reaper_skips_when_gh_unavailable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gh CLI missing → return early with skipped_reason."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    def _fake_run(*args, **kwargs):
        raise FileNotFoundError("gh: command not found")

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
    assert "skipped_reason" in result
    assert "gh CLI" in result["skipped_reason"]


def test_reaper_skips_when_gh_returns_non_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gh issue view exit non-zero → return early."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    def _fake_run(*args, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd="gh", stderr="auth missing"
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
    assert "skipped_reason" in result


def test_reaper_skips_when_gh_returns_non_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """gh returns non-JSON output → graceful skip."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="not valid json {{{",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
    assert "non-JSON" in result["skipped_reason"]


def test_reaper_extracts_vetoed_intent_blob(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Real-shape comment with vetoed_intent JSON blob → queued in pending file."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    fake_comment = {
        "id": "IC_kwDO12345",
        "createdAt": "2026-04-29T15:30:00Z",
        "body": (
            "**vetoed_intent** (auto-revert.yml on PR #7 closed-without-merge)\n\n"
            '```json\n{"slug": "test-slug", "pr_number": 7, "branch": "fruiting/test-slug-2026-04-29", "closed_at": "2026-04-29T15:30:00Z", "reason": "owner-closed-without-merge"}\n```\n\n'
            "Branch deleted."
        ),
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 1
    assert result["tracking_issue_id"] == 42

    # Pending queue file written.
    pending_file = tmp_path / ".myco/state" / "auto_evolve_vetoed_pending.json"
    assert pending_file.is_file()
    pending = json.loads(pending_file.read_text(encoding="utf-8"))
    assert len(pending) == 1
    assert pending[0]["slug"] == "test-slug"
    assert pending[0]["pr_number"] == 7
    assert pending[0]["vetoed_at"] == "2026-04-29T15:30:00Z"
    assert pending[0]["reason"] == "owner-closed-without-merge"


def test_reaper_cursor_skips_already_reaped_comments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Comments at or before cursor timestamp are not re-reaped (idempotency)."""
    ctx = _seed_v0_6_14_substrate(tmp_path)
    # Pre-seed cursor to a future-relative timestamp.
    cursor_file = tmp_path / ".myco/state" / "last_intent_reap.txt"
    cursor_file.write_text("2026-04-29T20:00:00Z\n", encoding="utf-8")

    fake_comment = {
        "id": "IC_old",
        "createdAt": "2026-04-29T15:00:00Z",  # before cursor
        "body": '```json\n{"slug": "old-slug"}\n```',
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0


def test_reaper_advances_cursor_to_latest_seen_comment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Cursor file advances to the latest createdAt seen, even on no match."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(
                {
                    "comments": [
                        {
                            "id": "IC_a",
                            "createdAt": "2026-04-29T16:00:00Z",
                            "body": "no JSON blob here, just narrative",
                        },
                        {
                            "id": "IC_b",
                            "createdAt": "2026-04-29T17:00:00Z",
                            "body": "also no blob",
                        },
                    ]
                }
            ),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
    cursor_file = tmp_path / ".myco/state" / "last_intent_reap.txt"
    assert cursor_file.is_file()
    assert cursor_file.read_text(encoding="utf-8").strip() == "2026-04-29T17:00:00Z"


def test_reaper_dedup_when_pending_already_has_slug(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pending queue dedups by slug — same slug not re-added."""
    ctx = _seed_v0_6_14_substrate(tmp_path)
    pending_file = tmp_path / ".myco/state" / "auto_evolve_vetoed_pending.json"
    pending_file.write_text(
        json.dumps(
            [
                {
                    "slug": "already-queued",
                    "vetoed_at": "2026-04-28T10:00:00Z",
                    "reason": "earlier",
                }
            ]
        ),
        encoding="utf-8",
    )

    fake_comment = {
        "id": "IC_new",
        "createdAt": "2026-04-29T18:00:00Z",
        "body": '```json\n{"slug": "already-queued", "pr_number": 99}\n```',
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    # No new reap — slug already in pending.
    assert result["reaped_count"] == 0
    pending = json.loads(pending_file.read_text(encoding="utf-8"))
    assert len(pending) == 1  # unchanged


def test_reaper_corrupt_pending_file_recovers(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Corrupt .myco/state/auto_evolve_vetoed_pending.json → reaper resets to empty list."""
    ctx = _seed_v0_6_14_substrate(tmp_path)
    pending_file = tmp_path / ".myco/state" / "auto_evolve_vetoed_pending.json"
    pending_file.write_text("garbage{{ not json", encoding="utf-8")

    fake_comment = {
        "id": "IC_recover",
        "createdAt": "2026-04-29T19:00:00Z",
        "body": '```json\n{"slug": "recovery-slug", "pr_number": 1}\n```',
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 1
    pending = json.loads(pending_file.read_text(encoding="utf-8"))
    assert len(pending) == 1
    assert pending[0]["slug"] == "recovery-slug"


def test_reaper_malformed_intent_json_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Malformed JSON inside the comment body is gracefully skipped.

    The regex captures `{...}` with a `slug:` substring; if the captured
    text is not parseable JSON (e.g., unquoted value), json.loads raises
    JSONDecodeError which the reaper catches.
    """
    ctx = _seed_v0_6_14_substrate(tmp_path)

    # Regex captures the {...} block (contains "slug":), but inner content
    # is not valid JSON (unquoted bare word).
    fake_comment = {
        "id": "IC_bad",
        "createdAt": "2026-04-29T20:00:00Z",
        "body": '```json\n{"slug": broken_unquoted_word}\n```',
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    # json.loads raises → intent is None → no append. 0 reap, no crash.
    assert result["reaped_count"] == 0


def test_reaper_intent_without_slug_skipped(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """JSON blob parses but has no `slug` key → skipped (defensive)."""
    ctx = _seed_v0_6_14_substrate(tmp_path)

    fake_comment = {
        "id": "IC_noslug",
        "createdAt": "2026-04-29T21:00:00Z",
        "body": '```json\n{"slug": "", "pr_number": 5}\n```',  # empty slug
    }

    def _fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps({"comments": [fake_comment]}),
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", _fake_run)
    result = _reap_vetoed_intents(ctx)
    assert result["reaped_count"] == 0
