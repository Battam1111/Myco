"""Canonical directory-skip list for every filesystem walker in Myco.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/circulation.md``
(Circulation § "Scope" — the graph walker's skip rules live here).
Also consumed by ``docs/architecture/L2_DOCTRINE/ingestion.md`` §
"Forage" and by MP1/MP2 dimensions.

v0.5.8 consolidated three previously-divergent ``_SKIP_DIRS`` lists
(``circulation/graph_src.py``, ``ingestion/adapters/code_repo.py``, and
an inline predicate in ``homeostasis/dimensions/mp1_no_provider_imports.py``)
into this single module so every walker sees the same set.

The list covers:

* **Python tooling caches**: ``__pycache__``, ``.pytest_cache``,
  ``.mypy_cache``, ``.ruff_cache``, ``.tox``, ``*.egg-info``.
* **VCS**: ``.git``, ``.hg``, ``.svn``.
* **Python virtualenvs**: ``.venv``, ``venv``, ``env``.
* **Node ecosystem**: ``node_modules``.
* **Build output**: ``build``, ``dist``.
* **Editor local caches**: ``.vscode``, ``.idea``, ``.DS_Store`` (file, but
  a reasonable include).
* **Myco's own runtime state**: ``.myco_state`` (derivable; must not
  be ingested or graphed).
* **Legacy quarantine**: ``legacy_v0_3`` (v0.4 greenfield rewrite
  preserved the pre-rewrite source under this dir; it is not part of
  the live substrate).

Callers can opt in to test trees (``tests`` is NOT in the default
skip set so graph-walkers cover test-doc refs correctly; pass
``include_tests=False`` to exclude).
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Final

__all__ = [
    "DEFAULT_SKIP_DIRS",
    "TEST_DIRS",
    "should_skip_dir",
    "should_skip_path",
]


#: The canonical skip set. Matches against directory *basenames*; path
#: components deeper in the tree are allowed (e.g. a directory literally
#: named ``.git`` is always skipped, but ``docs/.git-setup.md`` is NOT
#: affected because we never match against basename of a file).
DEFAULT_SKIP_DIRS: Final[frozenset[str]] = frozenset(
    {
        # Python tooling
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        # VCS
        ".git",
        ".hg",
        ".svn",
        # Virtualenvs
        ".venv",
        "venv",
        "env",
        # Node
        "node_modules",
        # Build output
        "build",
        "dist",
        # Editor + misc
        ".vscode",
        ".idea",
        # Myco runtime state
        ".myco_state",
        # Legacy quarantine
        "legacy_v0_3",
    }
)

#: Directories containing tests. Graph walkers include these by
#: default so test-doc cross-refs are visible, but ingestion adapters
#: (which may want to skip tests when forage'ing a project root) can
#: use this set to augment ``DEFAULT_SKIP_DIRS``.
TEST_DIRS: Final[frozenset[str]] = frozenset({"tests", "test"})


def should_skip_dir(
    name: str,
    *,
    include_tests: bool = True,
    extra: Iterable[str] | None = None,
) -> bool:
    """Return True if a directory with the given basename should be
    skipped by a walker.

    Args:
        name: basename of the directory (not a full path).
        include_tests: if True (default), ``tests/`` is walked. Pass
            False when forage'ing a downstream project and test trees
            are typically noise.
        extra: caller-supplied additions to the skip set (e.g. a
            substrate-local ``canon.system.walker_skip_dirs`` field).

    Also skips any directory whose basename matches the ``*.egg-info``
    glob (covers ``myco.egg-info``, ``pip.egg-info``, etc.) and any
    dot-prefixed directory not explicitly listed (heuristic for ".*"
    private dirs like ``.next``, ``.cache``; callers that legitimately
    want to walk such dirs pass ``extra`` and filter the result).
    """
    skip_set = set(DEFAULT_SKIP_DIRS)
    if not include_tests:
        skip_set |= TEST_DIRS
    if extra:
        skip_set |= set(extra)

    if name in skip_set:
        return True
    return name.endswith(".egg-info")


def should_skip_path(
    path: Path,
    *,
    root: Path | None = None,
    include_tests: bool = True,
    extra: Iterable[str] | None = None,
) -> bool:
    """Return True if any component of ``path`` (relative to ``root``
    if supplied, otherwise all parts) triggers the skip predicate.

    This is the common predicate walkers use when iterating deep
    trees: a nested match at any level prunes the entire subtree.
    """
    if root is not None:
        try:
            rel = path.relative_to(root)
        except ValueError:
            rel = path
        parts = rel.parts
    else:
        parts = path.parts

    for part in parts:
        if should_skip_dir(part, include_tests=include_tests, extra=extra):
            return True
    return False
