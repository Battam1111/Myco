"""Top-level sanity test.

Verifies:
  1. Every package in the eight-subsystem layout imports cleanly.
  2. ``myco.__version__`` is a well-formed PEP 440 release or ``.dev``
     marker (e.g. ``"0.4.0"`` or ``"0.4.1.dev"``). The exact string
     changes per release, so the test checks the shape, not the value.
  3. ``python -m myco --help`` exits zero and lists the manifest verbs
     (confirms the surface layer is wired).
"""

from __future__ import annotations

import importlib
import re
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


def test_version_is_well_formed() -> None:
    """Package version matches the L1 versioning grammar: ``N.N.N`` or
    ``N.N.N.devN?``. Kept version-agnostic so release bumps do not
    force a test edit.
    """
    assert re.match(r"^\d+\.\d+\.\d+(\.dev\d*)?$", myco.__version__), myco.__version__


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
