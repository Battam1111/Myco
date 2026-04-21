"""Tests for ``myco.core.skip_dirs``.

Covers :data:`DEFAULT_SKIP_DIRS`, :func:`should_skip_dir`, and
:func:`should_skip_path`. These predicates unify the previously-
divergent skip lists that lived in ``graph_src``, ``code_repo``,
``mp1``, and inline in ``forage`` — a bug here ripples to every
walker in Myco.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.skip_dirs import (
    DEFAULT_SKIP_DIRS,
    TEST_DIRS,
    should_skip_dir,
    should_skip_path,
)


class TestDefaultSkipDirs:
    def test_contains_git(self) -> None:
        assert ".git" in DEFAULT_SKIP_DIRS

    def test_contains_venvs(self) -> None:
        assert ".venv" in DEFAULT_SKIP_DIRS
        assert "venv" in DEFAULT_SKIP_DIRS
        assert "env" in DEFAULT_SKIP_DIRS

    def test_contains_build_outputs(self) -> None:
        assert "build" in DEFAULT_SKIP_DIRS
        assert "dist" in DEFAULT_SKIP_DIRS

    def test_contains_node_modules(self) -> None:
        assert "node_modules" in DEFAULT_SKIP_DIRS

    def test_contains_myco_state(self) -> None:
        assert ".myco_state" in DEFAULT_SKIP_DIRS

    def test_does_not_contain_tests_by_default(self) -> None:
        # Graph walkers include tests by default.
        assert "tests" not in DEFAULT_SKIP_DIRS
        assert "test" not in DEFAULT_SKIP_DIRS

    def test_test_dirs_tracked_separately(self) -> None:
        assert frozenset({"tests", "test"}) == TEST_DIRS


class TestShouldSkipDir:
    def test_git_skipped(self) -> None:
        assert should_skip_dir(".git")

    def test_venv_skipped(self) -> None:
        assert should_skip_dir(".venv")

    def test_node_modules_skipped(self) -> None:
        assert should_skip_dir("node_modules")

    def test_regular_dir_not_skipped(self) -> None:
        assert not should_skip_dir("src")
        assert not should_skip_dir("notes")
        assert not should_skip_dir("docs")

    def test_tests_default_not_skipped(self) -> None:
        assert not should_skip_dir("tests")
        assert not should_skip_dir("test")

    def test_tests_opt_in_skipped(self) -> None:
        assert should_skip_dir("tests", include_tests=False)
        assert should_skip_dir("test", include_tests=False)

    def test_egg_info_glob(self) -> None:
        assert should_skip_dir("myco.egg-info")
        assert should_skip_dir("pip.egg-info")
        assert should_skip_dir("some-package.egg-info")

    def test_extra_dirs_skipped(self) -> None:
        assert should_skip_dir("custom", extra=["custom"])

    def test_extra_combines_with_defaults(self) -> None:
        # Both DEFAULT_SKIP_DIRS and extra fire.
        assert should_skip_dir(".git", extra=["custom"])
        assert should_skip_dir("custom", extra=["custom"])

    def test_no_false_positives(self) -> None:
        # Ensure unrelated directory names don't trigger.
        for name in ("myco", "src", "lib", "foo", "bar"):
            assert not should_skip_dir(name), f"false positive on {name}"


class TestShouldSkipPath:
    def test_nested_skip_propagates(self, tmp_path: Path) -> None:
        p = tmp_path / ".git" / "objects" / "a.pack"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"")
        assert should_skip_path(p)

    def test_with_root_uses_relative(self, tmp_path: Path) -> None:
        p = tmp_path / "src" / "myco" / "core.py"
        p.parent.mkdir(parents=True)
        p.write_text("x", encoding="utf-8")
        # Path inside root with no skip-dir components — should pass.
        assert not should_skip_path(p, root=tmp_path)

    def test_venv_prunes_subtree(self, tmp_path: Path) -> None:
        p = tmp_path / ".venv" / "lib" / "python3.13" / "site-packages" / "any.py"
        p.parent.mkdir(parents=True)
        p.write_text("x", encoding="utf-8")
        assert should_skip_path(p, root=tmp_path)

    def test_tests_honored_via_opt_in(self, tmp_path: Path) -> None:
        p = tmp_path / "tests" / "unit" / "test_x.py"
        p.parent.mkdir(parents=True)
        p.write_text("x", encoding="utf-8")
        # Default (include_tests=True): tests/ not skipped.
        assert not should_skip_path(p, root=tmp_path)
        # Opt-in: skipped.
        assert should_skip_path(p, root=tmp_path, include_tests=False)

    def test_path_outside_root_uses_full_parts(self, tmp_path: Path) -> None:
        # When path escapes root, should_skip_path uses full parts.
        p = Path("/.venv/something")
        assert should_skip_path(p, root=tmp_path)
