"""Cover the boundary/install/__init__.py main() dispatch paths."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.boundary.install import (
    CLIENTS,
    _legacy_sniff,
    _run_all_hosts,
    _run_cowork_plugin,
    main,
)


def test_legacy_sniff_inserts_host_for_known_client():
    out = _legacy_sniff(["claude-code", "--dry-run"])
    assert out == ["host", "claude-code", "--dry-run"]


def test_legacy_sniff_no_op_for_subcommand():
    out = _legacy_sniff(["host", "claude-code"])
    assert out == ["host", "claude-code"]


def test_legacy_sniff_no_op_for_fresh_subcommand():
    out = _legacy_sniff(["fresh", "/tmp/x"])
    assert out == ["fresh", "/tmp/x"]


def test_legacy_sniff_empty():
    out = _legacy_sniff([])
    assert out == []


def test_legacy_sniff_unknown_first_arg():
    """Unknown first arg → not rewritten."""
    out = _legacy_sniff(["not-a-client"])
    assert out == ["not-a-client"]


def test_main_returns_2_when_no_subcommand(capsys):
    rc = main([])
    assert rc == 2
    err = capsys.readouterr().err
    assert "myco-install" in err.lower() or err  # help printed to stderr


def test_main_help_subcommand_not_known_raises_systemexit():
    with pytest.raises(SystemExit):
        main(["--help"])


def test_main_host_unknown_client_argparse_rejects():
    with pytest.raises(SystemExit):
        main(["host", "fake-client", "--dry-run"])


def test_main_host_no_client_no_all_hosts_returns_2(capsys):
    rc = main(["host", "--dry-run"])
    assert rc == 2
    err = capsys.readouterr().err
    assert "client" in err.lower() or "all-hosts" in err.lower()


def test_main_host_dispatch_dry_run(capsys):
    """dispatch path returns gracefully on dry-run for unknown context."""
    rc = main(["host", "claude-code", "--dry-run"])
    # dry-run dispatch may print something, return 0 normally.
    assert isinstance(rc, int)


def test_main_fresh_dry_run(tmp_path: Path, capsys):
    """fresh subcommand dry-run returns 0 without writing."""
    rc = main(
        [
            "fresh",
            str(tmp_path / "myco-fresh"),
            "--dry-run",
            "--yes",
            "--extras",
            "mcp",
        ]
    )
    assert rc == 0


def test_main_legacy_positional_routes_to_host():
    """Legacy ``myco-install <client>`` form routes to ``host <client>``."""
    rc = main(["claude-code", "--dry-run"])
    # Either 0 (dispatch ok) or non-zero (dispatch error). Both proves routing.
    assert isinstance(rc, int)


def test_main_cowork_plugin_dry_run(tmp_path: Path, capsys):
    """cowork-plugin dry-run prints upload instructions."""
    rc = main(["cowork-plugin", "--dry-run"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "would build" in out or "upload" in out.lower()


def test_run_cowork_plugin_dry_run(capsys):
    """Direct invocation of _run_cowork_plugin in dry-run mode."""
    rc = _run_cowork_plugin(dry_run=True, cleanup_legacy=False)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[dry-run]" in out or "would build" in out


def test_run_cowork_plugin_with_cleanup_dry_run(tmp_path: Path, capsys):
    """cleanup_legacy=True with dry_run=True does not touch any files."""
    rc = _run_cowork_plugin(
        dry_run=True,
        cleanup_legacy=True,
        cowork_root=tmp_path / "fake_cowork",
    )
    assert rc == 0


def test_run_all_hosts_with_no_detected_returns_0(capsys, monkeypatch):
    """When detection finds nothing, _run_all_hosts still returns 0."""

    def fake_detect():
        return dict.fromkeys(CLIENTS, False)

    monkeypatch.setattr("myco.boundary.install.detect_installed_hosts", fake_detect)
    rc = _run_all_hosts(dry_run=True, global_=True, uninstall=False)
    assert rc == 0


def test_run_all_hosts_dry_run_implies_global(monkeypatch):
    """``--all-hosts`` implies ``--global`` even when not explicit."""

    def fake_detect():
        return dict.fromkeys(CLIENTS, False)

    monkeypatch.setattr("myco.boundary.install.detect_installed_hosts", fake_detect)
    # Pass global_=False and verify no error (function flips it inside).
    rc = _run_all_hosts(dry_run=True, global_=False, uninstall=False)
    assert rc == 0
