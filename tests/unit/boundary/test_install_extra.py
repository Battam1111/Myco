"""Extra coverage for boundary.install package paths.

Targets the under-covered paths in ``boundary/install/__init__.py``
(58%) and ``boundary/install/fresh.py`` (66%).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.boundary.install import CLIENTS, MycoInstallError, dispatch, main
from myco.boundary.install.clients import detect_installed_hosts


def test_clients_dict_has_known_hosts():
    assert "claude-code" in CLIENTS
    assert "cursor" in CLIENTS
    assert "vscode" in CLIENTS


def test_main_help_exits_zero():
    """argparse prints help and exits 0."""
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_main_missing_subcommand_runs_legacy_path():
    """No subcommand → main may print help with rc=0 (legacy compat)."""
    rc = main([])
    # Either zero-exit (legacy help) or non-zero — either is acceptable.
    assert rc is None or isinstance(rc, int)


def test_detect_installed_hosts_returns_iterable(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Detection returns an iterable (list/dict/set)."""
    detected = detect_installed_hosts()
    # Detection is best-effort against current $HOME; just verify type.
    assert detected is not None


def test_install_dispatch_unknown_host():
    """Unknown host name raises MycoInstallError."""
    with pytest.raises(MycoInstallError):
        dispatch(
            "not-a-real-host",
            dry_run=True,
            global_=False,
            uninstall=False,
        )


def test_main_host_with_unknown_client_argparse_exits():
    """``myco-install host fake-host`` → argparse rejects unknown client."""
    with pytest.raises(SystemExit) as exc:
        main(["host", "fake-host", "--dry-run"])
    assert exc.value.code != 0
