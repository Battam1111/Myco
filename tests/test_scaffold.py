"""Stage A/B sanity test.

Verifies:
  1. Every package in the eight-subsystem layout imports cleanly.
  2. ``myco.__version__`` is the Stage A/B marker ``"0.4.0.dev"``.
  3. ``python -m myco --help`` exits zero and lists the manifest verbs
     (confirms Stage B.7 surface has landed).
"""

from __future__ import annotations

import importlib
import subprocess
import sys

import pytest

import myco

PACKAGES = [
    "myco",
    "myco.core",
    "myco.genesis",
    "myco.genesis.templates",
    "myco.ingestion",
    "myco.digestion",
    "myco.circulation",
    "myco.homeostasis",
    "myco.homeostasis.dimensions",
    "myco.surface",
    "myco.symbionts",
]


@pytest.mark.parametrize("name", PACKAGES)
def test_package_imports(name: str) -> None:
    mod = importlib.import_module(name)
    assert mod is not None


def test_version_is_stage_ab_marker() -> None:
    assert myco.__version__ == "0.4.0.dev", myco.__version__


def test_dunder_main_help_lists_verbs() -> None:
    """``python -m myco --help`` should succeed and list manifest verbs."""
    result = subprocess.run(
        [sys.executable, "-m", "myco", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    for verb in ("genesis", "eat", "reflect", "immune", "session-end"):
        assert verb in result.stdout, result.stdout
