"""Regression tests for v0.5.4 dogfood bug fixes.

Every test here pins a specific behavior that the v0.5.3 dogfood
session identified as broken. Keep one test per bug so a future
regression can point straight at which one is violated.
"""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

import pytest

from myco.surface.cli import build_parser, main


def _run(argv: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        rc = main(argv)
    return rc, out.getvalue(), err.getvalue()


# ---------------------------------------------------------------------------
# Bug #1: `myco --version` prints the version and exits 0
# ---------------------------------------------------------------------------


def test_version_flag_prints_and_exits_zero() -> None:
    import myco

    # argparse ``action='version'`` calls sys.exit(0) after printing.
    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        with pytest.raises(SystemExit) as excinfo:
            main(["--version"])
    assert excinfo.value.code == 0
    combined = out.getvalue() + err.getvalue()
    assert myco.__version__ in combined
    assert "myco" in combined


def test_short_version_flag() -> None:
    import myco

    out = io.StringIO()
    err = io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        with pytest.raises(SystemExit) as excinfo:
            main(["-V"])
    assert excinfo.value.code == 0
    assert myco.__version__ in (out.getvalue() + err.getvalue())


# ---------------------------------------------------------------------------
# Bug #3: `--tags a b c` natural-form multi-value parses correctly
# ---------------------------------------------------------------------------


def test_list_flag_accepts_natural_multi_value(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``--tags a b c`` must parse as ``["a", "b", "c"]``. Before
    v0.5.4 only the repeated form (``--tags a --tags b``) worked;
    the natural form errored with 'unrecognized arguments'."""
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, stderr = _run(
        ["--json", "eat", "--content", "x", "--tags", "a", "b", "c"]
    )
    assert rc == 0, stderr
    data = json.loads(stdout)
    assert data["payload"]["tags"] == ["a", "b", "c"]


def test_list_flag_still_accepts_repeated_form(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Legacy ``--tags a --tags b`` form still works (extend semantics)."""
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _ = _run(
        ["--json", "eat", "--content", "y", "--tags", "a", "--tags", "b"]
    )
    assert rc == 0
    assert json.loads(stdout)["payload"]["tags"] == ["a", "b"]


# ---------------------------------------------------------------------------
# Bug #6: subparser dest collision with manifest arg named "verb"
# ---------------------------------------------------------------------------


def test_subparser_dest_does_not_collide_with_verb_arg() -> None:
    """Before v0.5.4 the subparsers' ``dest='verb'`` stored the
    subcommand name on ``ns.verb``, but ``ramify`` has a flag
    ``--verb`` whose default None overwrote that same attribute. The
    dispatcher then looked up the command as ``None`` and raised
    'unknown command'."""
    parser = build_parser()
    ns = parser.parse_args(
        ["ramify", "--dimension", "D1", "--category", "mechanical", "--severity", "medium"]
    )
    subcmd = getattr(ns, "_subcmd", None)
    assert subcmd == "ramify"
    # The --verb arg still works when explicitly set.
    ns2 = parser.parse_args(["ramify", "--verb", "some_verb"])
    assert getattr(ns2, "_subcmd") == "ramify"
    assert ns2.verb == "some_verb"


def test_ramify_dimension_mode_no_verb_flag(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """End-to-end reproduction: ramify --dimension without --verb
    must succeed. Before v0.5.4 it errored with 'unknown command: None'."""
    # seeded_substrate's canon declares substrate_id "test-substrate"
    # which isn't "myco-self", so --substrate-local auto-on.
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, stderr = _run(
        ["--json", "ramify", "--dimension", "X1",
         "--category", "mechanical", "--severity", "low"]
    )
    assert rc == 0, stderr
    data = json.loads(stdout)
    assert data["payload"]["mode"] == "dimension"
    assert data["payload"]["dimension"] == "X1"
    assert data["payload"]["written"] is True


# ---------------------------------------------------------------------------
# Bug #5: `--json` includes findings list
# ---------------------------------------------------------------------------


def test_json_output_includes_findings_key(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Every ``--json`` response carries a ``findings`` field (empty
    list when the handler produces none). Before v0.5.4, findings
    were silently dropped from the JSON output."""
    monkeypatch.chdir(genesis_substrate)
    rc, stdout, _ = _run(["--json", "immune"])
    assert rc < 3
    data = json.loads(stdout)
    assert "findings" in data
    assert isinstance(data["findings"], list)


def test_json_findings_render_dimension_id_and_severity(
    genesis_substrate: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When immune fires a finding, the JSON output exposes the
    finding's dimension_id + category + severity for the agent."""
    # genesis_substrate lacks an entry-point file; M2 fires HIGH.
    monkeypatch.chdir(genesis_substrate)
    (genesis_substrate / "MYCO.md").unlink(missing_ok=True)
    rc, stdout, _ = _run(["--json", "--exit-on", "high", "immune"])
    data = json.loads(stdout)
    findings = data["findings"]
    assert findings, "expected at least one finding"
    assert all("dimension_id" in f for f in findings)
    assert all("severity" in f for f in findings)
    assert any(f["dimension_id"] == "M2" for f in findings)
