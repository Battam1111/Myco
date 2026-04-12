"""Shared pytest fixtures for the Myco test suite.

Wave 25 (v0.24.0) — test infrastructure seed. Landed by
``docs/primordia/hermes_absorption_craft_2026-04-12.md`` §4.2 items 1-3.

Discipline inheritance: ``_isolate_myco_project`` is the Myco analog of
hermes's ``tests/conftest.py::_isolate_hermes_home`` autouse isolation
fixture (hermes_agent repo, under MIT license, referenced in
``notes/n_20260412T013044_5546.md`` catalog C1). Myco's substrate shape
differs — hermes isolates a user home directory, Myco isolates a
project directory — but the pattern is the same: every test gets a
private, tmp_path-backed workspace so tests can never accidentally
mutate the developer's live Myco project.

Why autouse: if isolation is opt-in, the first test that forgets the
opt-in leaks across the suite and the next wave discovers it the hard
way. Wave 20's silent-fail doctrine applies here too — a sensor system
that returns "isolated" when it isn't is worse than a crash.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest


# Ensure the editable package is importable regardless of how pytest is
# invoked. This mirrors the ``PYTHONPATH=src`` pattern used by the CLI
# entry point during development and keeps tests decoupled from whether
# the user has run ``pip install -e .``.
_REPO_ROOT = Path(__file__).resolve().parent.parent
_SRC = _REPO_ROOT / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))


# Minimal canon fixture for tests that need a walkable project root.
# This is the smallest _canon.yaml that satisfies ``_project_root``'s
# walk-up check without triggering ``MycoProjectNotFound``. Tests that
# exercise lint dimensions will need to extend this — that's expected
# and should happen inside those specific tests, not globally.
_MIN_CANON = """\
system:
  principles_count: 13
  principles_label: "十三原則"
  entry_point: MYCO.md
  contract_version: "v0.24.0"
  synced_contract_version: "v0.24.0"
architecture:
  layers: 4
  wiki_pages: 0
project:
  name: TestProject
"""


@pytest.fixture(autouse=True)
def _isolate_myco_project(tmp_path, monkeypatch):
    """Redirect every test into a private tmp_path-backed Myco project.

    Provides:
      - ``tmp_path/project/_canon.yaml``  (minimal, walkable)
      - ``tmp_path/project/notes/``       (empty digestive dir)
      - ``tmp_path/project/docs/primordia/`` (craft surface, empty)
      - ``tmp_path/project/log.md``       (empty append-only log)

    Env vars cleared so no stray kernel pointers leak in:
      - ``MYCO_ALLOW_NO_PROJECT`` (strict-mode escape hatch) is unset
      - ``MYCO_PROJECT_DIR`` (future C8 env var) is unset

    Yields the project root :class:`~pathlib.Path` so tests can build
    on it without repeating scaffolding. No manual cleanup: pytest
    auto-removes ``tmp_path`` at teardown.
    """
    project = tmp_path / "project"
    project.mkdir()
    (project / "_canon.yaml").write_text(_MIN_CANON, encoding="utf-8")
    (project / "notes").mkdir()
    (project / "docs").mkdir()
    (project / "docs" / "primordia").mkdir()
    (project / "log.md").write_text("", encoding="utf-8")

    monkeypatch.delenv("MYCO_ALLOW_NO_PROJECT", raising=False)
    monkeypatch.delenv("MYCO_PROJECT_DIR", raising=False)

    # Change cwd into the isolated project so _project_root()'s walk-up
    # and any bare ``Path.cwd()`` reads land inside the fixture.
    monkeypatch.chdir(project)

    yield project
