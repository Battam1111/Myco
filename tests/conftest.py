"""Shared pytest fixtures for the Myco v0.4.0 rewrite."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


@pytest.fixture(autouse=True)
def _isolate_global_registry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Disable ``~/.myco/substrates.yaml`` writes across every test.

    v0.5.16 hooked ``myco.germination.bootstrap`` to call
    ``register_substrate`` on success, which means any test that
    germinates — there are a lot of them — would pollute the real
    operator's registry with pytest tmp-dir paths. The
    ``MYCO_REGISTRY_DISABLED`` env var (honoured by
    ``register_substrate``) short-circuits the write; this fixture
    sets it for the full test session.

    Tests that specifically exercise the registry code path either
    (a) pass ``home=`` explicitly — those bypass this fixture because
    ``_registry_disabled`` is checked first — so they need an
    explicit ``monkeypatch.delenv`` or (b) call the lower-level
    functions directly with an explicit ``home`` kwarg. See
    ``tests/unit/core/test_registry.py`` for the pattern.
    """
    monkeypatch.setenv("MYCO_REGISTRY_DISABLED", "1")


@pytest.fixture
def tmp_substrate_root(tmp_path: Path) -> Path:
    """An empty directory that can stand in for a substrate root."""
    return tmp_path


@pytest.fixture
def minimal_canon_text() -> str:
    """A minimum-valid ``_canon.yaml`` as text.

    Contains exactly the required top-level keys plus a non-empty
    ``identity``, ``system``, and ``subsystems``.

    v0.5.8: now includes a permissive ``system.write_surface.allowed``
    so the shared ``seeded_substrate`` fixture works with
    ``write_surface``-enforcing verbs (eat, sporulate, fruit, molt,
    ramify, etc.). Tests that specifically exercise write-surface
    violation paths create their own canon with a narrower surface.
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
          write_surface:
            allowed:
              - "_canon.yaml"
              - "MYCO.md"
              - "notes/**"
              - "docs/**"
              - "src/**"
              - ".myco/**"
              - ".myco_state/**"
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
    """A substrate produced by ``myco.germination.bootstrap``.

    Useful when tests need a realistic substrate, including the entry-
    point file and ``.myco_state/autoseeded.txt`` marker.

    v0.5.7: canonical import path is ``myco.germination`` (the v0.5.3
    rename); the ``myco.genesis`` shim still resolves through v1.0.0
    but our own test harness uses the canonical path to avoid
    emitting self-inflicted DeprecationWarnings on every test run.
    Fixture name stays ``genesis_substrate`` for test-readability
    continuity.
    """
    from myco.germination import bootstrap

    bootstrap(project_dir=tmp_path, substrate_id="test-substrate")
    return tmp_path
