"""Top-level sanity test.

Verifies:

  1. **Every package under ``src/myco/`` imports cleanly.** v0.5+
     auto-discovers the package set via ``pkgutil.walk_packages``
     instead of maintaining a hardcoded list — adding a new subsystem
     no longer requires an edit here (MAJOR 7 fix).

  2. ``myco.__version__`` is a well-formed PEP 440 release or ``.dev``
     marker (e.g. ``"0.4.0"`` or ``"0.4.1.dev"``). The exact string
     changes per release, so the test checks the shape, not the value.

  3. ``python -m myco --help`` exits zero and lists the manifest verbs
     (confirms the surface layer is wired). The verb sample covers one
     verb per subsystem plus the v0.5 governance verbs.
"""

from __future__ import annotations

import importlib
import pkgutil
import re
import subprocess
import sys

import pytest

import myco


def _discover_packages() -> list[str]:
    """Every package and subpackage under ``myco``.

    Includes ``myco`` itself plus every sub-*package* (directories
    with ``__init__.py``) and every sub-*module* (standalone ``.py``
    files). Matches what the v0.4-era hardcoded ``PACKAGES`` list
    enumerated by hand, but stays green as subsystems are added or
    split.
    """
    names: list[str] = ["myco"]
    for info in pkgutil.walk_packages(myco.__path__, prefix="myco."):
        names.append(info.name)
    return sorted(set(names))


PACKAGES = _discover_packages()


@pytest.mark.parametrize("name", PACKAGES)
def test_package_imports(name: str) -> None:
    mod = importlib.import_module(name)
    assert mod is not None


def test_every_subsystem_has_a_matching_package() -> None:
    """Every entry in ``canon.subsystems`` that declares a ``package:``
    path points to a directory that actually exists. This is the
    dynamic equivalent of the MF1 dimension and acts as a belt-and-
    suspenders check for the scaffold-level invariant (MAJOR 7)."""
    import yaml
    from pathlib import Path

    canon_path = Path(__file__).resolve().parent.parent / "_canon.yaml"
    data = yaml.safe_load(canon_path.read_text(encoding="utf-8"))
    subsystems = data.get("subsystems") or {}
    for name, spec in subsystems.items():
        if not isinstance(spec, dict):
            continue
        pkg = spec.get("package")
        if pkg is None:
            continue
        pkg_path = canon_path.parent / pkg
        assert pkg_path.is_dir(), f"canon.subsystems.{name}.package missing: {pkg}"


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
    # v0.5 expanded the verb set. Sample one per subsystem plus the
    # governance verbs so the test stays stable across additions.
    for verb in (
        "genesis", "eat", "reflect", "immune", "session-end",
        "craft", "bump", "evolve", "scaffold",
    ):
        assert verb in result.stdout, result.stdout
