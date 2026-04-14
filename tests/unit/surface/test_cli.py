"""Tests for ``myco.surface.cli``."""

from __future__ import annotations

import io
import os
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from myco.surface.cli import build_parser, main


def test_build_parser_lists_all_verbs() -> None:
    parser = build_parser()
    help_text = parser.format_help()
    for verb in (
        "genesis", "hunger", "eat", "sense", "forage",
        "reflect", "digest", "distill",
        "perfuse", "propagate",
        "immune", "session-end",
    ):
        assert verb in help_text


def test_cli_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--help"])
    assert excinfo.value.code == 0


def _run(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


def test_cli_genesis_creates_substrate(tmp_path: Path) -> None:
    target = tmp_path / "newsub"
    target.mkdir()
    rc, stdout, stderr = _run(
        [
            "genesis",
            "--project-dir", str(target),
            "--substrate-id", "newsub",
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
    rc, _, stderr = _run(
        ["--project-dir", str(tmp_path), "eat", "--content", "x"]
    )
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
