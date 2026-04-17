"""Shared pytest fixtures for the Myco v0.4.0 rewrite."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def tmp_substrate_root(tmp_path: Path) -> Path:
    """An empty directory that can stand in for a substrate root."""
    return tmp_path


@pytest.fixture
def minimal_canon_text() -> str:
    """A minimum-valid ``_canon.yaml`` as text.

    Contains exactly the required top-level keys plus a non-empty
    ``identity``, ``system``, and ``subsystems``.
    """
    return textwrap.dedent(
        """\
        schema_version: "1"
        contract_version: "v0.4.0-alpha.1"
        identity:
          substrate_id: "test-substrate"
          tags: ["test"]
          entry_point: "MYCO.md"
        system:
          hard_contract:
            rule_count: 7
        subsystems:
          genesis:
            doc: "docs/architecture/L2_DOCTRINE/genesis.md"
        """
    )


@pytest.fixture
def seeded_substrate(tmp_substrate_root: Path, minimal_canon_text: str) -> Path:
    """A substrate root with a valid ``_canon.yaml`` written in place."""
    (tmp_substrate_root / "_canon.yaml").write_text(
        minimal_canon_text, encoding="utf-8"
    )
    (tmp_substrate_root / "notes").mkdir()
    (tmp_substrate_root / "docs").mkdir()
    return tmp_substrate_root


@pytest.fixture
def genesis_substrate(tmp_path: Path) -> Path:
    """A substrate produced by ``myco.genesis.bootstrap``.

    Useful when tests need a realistic substrate, including the entry-
    point file and ``.myco_state/autoseeded.txt`` marker.
    """
    from myco.genesis import bootstrap

    bootstrap(project_dir=tmp_path, substrate_id="test-substrate")
    return tmp_path
