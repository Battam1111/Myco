"""Tests for ``myco.surface.cli``."""

from __future__ import annotations

import io
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import pytest

from myco.surface.cli import build_parser, main


def test_build_parser_lists_all_verbs() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    # v0.5: the verb set grew from 12 to 16. This test asserts the
    # baseline set is still surfaced; additions after v0.5 do not
    # require an edit here.
    for verb in (
        "genesis",
        "hunger",
        "eat",
        "sense",
        "forage",
        "reflect",
        "digest",
        "distill",
        "perfuse",
        "propagate",
        "immune",
        "session-end",
        # v0.5 governance + scaffold
        "craft",
        "bump",
        "evolve",
        "scaffold",
    ):
        assert verb in help_text


def test_cli_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


# ---------------------------------------------------------------------------
# v0.5.7 — senesce end-to-end CLI coverage
# ---------------------------------------------------------------------------


def test_cli_senesce_full_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, genesis_substrate: Path
) -> None:
    """``myco senesce`` (no --quick) runs full mode end-to-end via CLI.

    Closes the test-coverage gap surfaced by the v0.5.7 audit: the
    senesce-quick flag was covered through the handler and dispatcher
    paths, but the full argparse → dispatch round-trip was not
    regression-protected before now.
    """
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _stderr = _run(["--json", "senesce"])
    assert rc == 0
    import json

    data = json.loads(stdout)
    assert data["exit_code"] == 0
    assert data["payload"]["mode"] == "full"
    # Full mode payload always has both reflect + immune keys.
    assert "reflect" in data["payload"]
    assert "immune" in data["payload"]
    # Full mode's immune is the full run_immune payload (not skipped).
    assert data["payload"]["immune"].get("skipped") is not True


def test_cli_senesce_quick_mode(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, genesis_substrate: Path
) -> None:
    """``myco senesce --quick`` runs quick mode end-to-end via CLI.

    The SessionEnd hook invokes this exact shape — regression-protecting
    the CLI path keeps the hook binding stable across refactors.
    """
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _stderr = _run(["--json", "senesce", "--quick"])
    assert rc == 0
    import json

    data = json.loads(stdout)
    assert data["exit_code"] == 0
    assert data["payload"]["mode"] == "quick"
    # Quick mode skips immune — payload["immune"] is the skipped marker.
    assert data["payload"]["immune"]["skipped"] is True
    assert "reason" in data["payload"]["immune"]
    # Reflect still runs in quick mode.
    assert "reflect" in data["payload"]


def test_cli_session_end_alias_routes_to_senesce(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, genesis_substrate: Path
) -> None:
    """The v0.5.2 ``session-end`` alias must still invoke the senesce
    handler — checked at CLI level (not just manifest level).
    """
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _stderr = _run(["--json", "session-end"])
    assert rc == 0
    import json

    data = json.loads(stdout)
    # Alias resolution lands on the senesce handler, so mode is still set.
    assert data["payload"]["mode"] == "full"


def _run(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


def test_cli_genesis_creates_substrate(tmp_path: Path) -> None:
    target = tmp_path / "newsub"
    target.mkdir()
    rc, _stdout, stderr = _run(
        [
            "genesis",
            "--project-dir",
            str(target),
            "--substrate-id",
            "newsub",
        ]
    )
    assert rc == 0, stderr
    assert (target / "_canon.yaml").is_file()


def test_cli_eat_against_existing_substrate(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(genesis_substrate)
    rc, _, stderr = _run(["eat", "--content", "hello world"])
    assert rc == 0, stderr
    raw = list((genesis_substrate / "notes" / "raw").glob("*.md"))
    assert raw


def test_cli_missing_substrate_is_usage_error(tmp_path: Path) -> None:
    rc, _, stderr = _run(["--project-dir", str(tmp_path), "eat", "--content", "x"])
    assert rc >= 3
    assert "no Myco substrate" in stderr


def test_cli_json_output(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _ = _run(["--json", "eat", "--content", "x"])
    assert rc == 0
    import json

    parsed = json.loads(stdout)
    assert parsed["exit_code"] == 0
    assert "payload" in parsed


def test_cli_sense_runs(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(genesis_substrate)
    rc, _, stderr = _run(["sense", "--query", "test"])
    assert rc == 0, stderr


def test_cli_immune_runs(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.chdir(genesis_substrate)
    rc, _, _ = _run(["immune"])
    # exit code may be 0, 1, or 2 depending on findings; anything
    # below 3 is a finding-driven result (not a crash).
    assert rc < 3
