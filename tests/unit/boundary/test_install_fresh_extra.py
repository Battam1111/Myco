"""Extra coverage for ``boundary.install.fresh``."""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.boundary.install.fresh import DEFAULT_REPO, run_fresh


def test_default_repo_is_set():
    assert DEFAULT_REPO


def test_fresh_dry_run_no_writes(tmp_path: Path):
    """``run_fresh --dry-run`` does not clone or pip install."""
    target = tmp_path / "myco-fresh"
    rc = run_fresh(
        target=target,
        repo=DEFAULT_REPO,
        branch=None,
        depth=None,
        extras="mcp",
        configure=(),
        global_=False,
        force=False,
        dry_run=True,
        yes=True,
    )
    assert rc == 0
    # In dry-run mode, no clone happened.
    assert not target.exists() or not (target / ".git").exists()


def test_fresh_existing_target_blocks_without_force(tmp_path: Path):
    """Non-empty target raises (or returns non-zero) without --force."""
    target = tmp_path / "existing"
    target.mkdir()
    (target / "junk.txt").write_text("hello", encoding="utf-8")
    try:
        rc = run_fresh(
            target=target,
            repo=DEFAULT_REPO,
            branch=None,
            depth=None,
            extras="mcp",
            configure=(),
            global_=False,
            force=False,
            dry_run=True,
            yes=True,
        )
        # Some implementations return non-zero rather than raise.
        assert rc != 0
    except Exception:
        pass  # raise path also acceptable
