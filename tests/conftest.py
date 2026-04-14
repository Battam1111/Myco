"""Shared pytest fixtures for the Myco v0.4.0 rewrite.

Stage A only needs a minimal placeholder; Stage B steps will add
fixtures for temporary substrate roots, fake canons, etc.
"""

from __future__ import annotations

from pathlib import Path

import pytest


@pytest.fixture
def tmp_substrate_root(tmp_path: Path) -> Path:
    """An empty directory that can stand in for a substrate root.

    Stage B fixtures will build on top of this by seeding ``_canon.yaml``
    and ``notes/`` from ``myco.genesis.templates``.
    """
    return tmp_path
