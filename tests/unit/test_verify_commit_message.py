"""Tests for scripts/verify_commit_message.py (Wave 58 Wave 3 — release loop)."""

import subprocess
import sys
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "verify_commit_message.py"


def run(msg: str):
    return subprocess.run(
        [sys.executable, str(SCRIPT), msg],
        capture_output=True, text=True,
    )


def test_feat_valid():
    r = run("feat: add new MCP tool")
    assert r.returncode == 0


def test_feat_bang_valid():
    r = run("feat!: breaking API change")
    assert r.returncode == 0


def test_fix_with_scope():
    r = run("fix(cli): handle missing project_dir")
    assert r.returncode == 0


def test_chore_release_valid():
    r = run("chore(release): v0.6.0")
    assert r.returncode == 0


def test_minor_prefix_valid():
    r = run("minor: user-facing feature that warrants 0.x bump")
    assert r.returncode == 0


def test_non_conventional_rejected():
    r = run("update stuff")
    assert r.returncode == 1
    assert "non-conventional" in r.stderr.lower()


def test_empty_rejected():
    r = run("")
    assert r.returncode == 1


def test_merge_commit_allowed():
    r = run("Merge branch 'main' into feature")
    assert r.returncode == 0
