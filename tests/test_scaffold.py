"""Stage A sanity test.

Verifies:
  1. Every package in the eight-subsystem layout imports cleanly.
  2. ``myco.__version__`` is the Stage A/B marker ``"0.4.0.dev"``.
  3. ``python -m myco`` raises the deliberate ``NotImplementedError``
     (documents that the CLI surface is intentionally absent until B.7).

If any of these fail, the Stage A commit is not ready.
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


def test_dunder_main_is_deliberately_unimplemented() -> None:
    """``python -m myco`` should raise NotImplementedError until Stage B.7."""
    result = subprocess.run(
        [sys.executable, "-m", "myco"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0, result.stdout
    assert "NotImplementedError" in result.stderr, result.stderr
    assert "Stage B.7" in result.stderr, result.stderr
