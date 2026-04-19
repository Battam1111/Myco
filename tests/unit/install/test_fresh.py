"""Tests for ``myco.install.fresh`` (v0.5.2 MAJOR 11).

These tests do NOT actually ``git clone`` or ``pip install`` — they
drive ``run_fresh`` with ``--dry-run`` (which skips every subprocess)
and with ``git_cmd=...`` overrides to validate the CLI plumbing, or
they patch ``subprocess.run`` to simulate results. End-to-end
behavior (a real clone + pip install) is validated manually at
release time, not per-test-run.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from myco.install import main as install_main
from myco.install.clients import MycoInstallError
from myco.install.fresh import DEFAULT_REPO, run_fresh


def test_fresh_dry_run_prints_plan_without_side_effects(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "myco-clone"
    rc = run_fresh(
        target=target,
        repo=DEFAULT_REPO,
        branch=None,
        depth=None,
        configure=(),
        global_=False,
        force=False,
        dry_run=True,
        yes=False,
        extras="mcp",
        # bypass git lookup in test environments that may not have it
        git="/fake/git",
        python="/fake/python",
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "[dry-run]" in captured.out
    assert "git" in captured.out and "clone" in captured.out
    assert DEFAULT_REPO in captured.out
    assert str(target) in captured.out
    assert "-m pip install -e" in captured.out
    # No files were created.
    assert not target.exists()


def test_fresh_refuses_nonempty_target_without_force(
    tmp_path: Path,
) -> None:
    target = tmp_path / "existing"
    target.mkdir()
    (target / "leftover.txt").write_text("hi", encoding="utf-8")

    with pytest.raises(MycoInstallError, match="not empty"):
        run_fresh(
            target=target,
            repo=DEFAULT_REPO,
            branch=None,
            depth=None,
            configure=(),
            global_=False,
            force=False,
            dry_run=True,
            yes=False,
            extras="mcp",
            git="/fake/git",
            python="/fake/python",
        )


def test_fresh_accepts_empty_target(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "empty-dir"
    target.mkdir()  # exists but empty
    rc = run_fresh(
        target=target,
        repo=DEFAULT_REPO,
        branch=None,
        depth=None,
        configure=(),
        global_=False,
        force=False,
        dry_run=True,
        yes=False,
        extras="mcp",
        git="/fake/git",
        python="/fake/python",
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "[dry-run]" in captured.out


def test_fresh_rejects_non_directory_target(tmp_path: Path) -> None:
    target = tmp_path / "a-file.txt"
    target.write_text("", encoding="utf-8")
    with pytest.raises(MycoInstallError, match="not a directory"):
        run_fresh(
            target=target,
            repo=DEFAULT_REPO,
            branch=None,
            depth=None,
            configure=(),
            global_=False,
            force=False,
            dry_run=True,
            yes=False,
            extras="mcp",
            git="/fake/git",
            python="/fake/python",
        )


def test_fresh_dry_run_with_configure_lists_hosts(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "c-clone"
    rc = run_fresh(
        target=target,
        repo=DEFAULT_REPO,
        branch=None,
        depth=None,
        configure=("claude-code", "cursor"),
        global_=False,
        force=False,
        dry_run=True,
        yes=False,
        extras="mcp",
        git="/fake/git",
        python="/fake/python",
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "would configure host: claude-code" in captured.out
    assert "would configure host: cursor" in captured.out


def test_fresh_rejects_unknown_configure_client(tmp_path: Path) -> None:
    target = tmp_path / "c-clone"
    with pytest.raises(MycoInstallError, match="unknown --configure"):
        run_fresh(
            target=target,
            repo=DEFAULT_REPO,
            branch=None,
            depth=None,
            configure=("totally-not-a-client",),
            global_=False,
            force=False,
            dry_run=False,
            yes=False,
            extras="mcp",
            git="/fake/git",
            python="/fake/python",
        )


def test_fresh_branch_and_depth_flags_render_correctly(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    target = tmp_path / "branch-clone"
    rc = run_fresh(
        target=target,
        repo="https://example.com/myco.git",
        branch="v0.5.1",
        depth=1,
        configure=(),
        global_=False,
        force=False,
        dry_run=True,
        yes=False,
        extras="mcp",
        git="/fake/git",
        python="/fake/python",
    )
    captured = capsys.readouterr()
    assert rc == 0
    assert "--branch v0.5.1" in captured.out
    assert "--depth 1" in captured.out
    assert "https://example.com/myco.git" in captured.out


def test_fresh_without_git_on_path_raises_clean_error(tmp_path: Path) -> None:
    target = tmp_path / "no-git-clone"
    # Force git lookup to fail.
    with patch("myco.install.fresh.shutil.which", return_value=None):
        with pytest.raises(MycoInstallError, match="git is not on PATH"):
            run_fresh(
                target=target,
                repo=DEFAULT_REPO,
                branch=None,
                depth=None,
                configure=(),
                global_=False,
                force=False,
                dry_run=True,
                yes=False,
                extras="mcp",
                # deliberately omit git override to exercise the lookup
            )


def test_cli_fresh_subcommand_dry_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch,
) -> None:
    """`myco-install fresh --dry-run <target>` works from the CLI."""
    # Stub git so the dry-run check passes without needing git.
    monkeypatch.setattr("myco.install.fresh.shutil.which", lambda cmd: "/fake/git")
    target = tmp_path / "cli-clone"
    rc = install_main(["fresh", "--dry-run", str(target)])
    assert rc == 0
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out


def test_cli_host_subcommand_dry_run(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """`myco-install host cursor --dry-run` is the explicit form."""
    rc = install_main(["host", "cursor", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out


def test_cli_legacy_positional_routes_to_host(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Legacy `myco-install cursor --dry-run` (v0.4/v0.5 shape) keeps
    working by auto-routing to `host cursor`."""
    rc = install_main(["cursor", "--dry-run"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "[dry-run]" in captured.out


def test_cli_no_subcommand_prints_help_and_exits_nonzero(
    capsys: pytest.CaptureFixture[str],
) -> None:
    rc = install_main([])
    assert rc == 2


def test_default_target_is_home_myco() -> None:
    """The documented default target is ~/myco (stable contract)."""
    from myco.install.fresh import _default_target

    assert _default_target() == Path.home() / "myco"
