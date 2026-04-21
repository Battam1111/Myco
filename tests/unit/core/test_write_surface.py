"""Tests for ``myco.core.write_surface``.

Covers :func:`is_path_allowed`, :func:`guarded_write`, and the
``MYCO_ALLOW_UNSAFE_WRITE`` bypass env-var. These are the R6-enforcement
chokepoints — a bug here means the write-surface contract is
silently bypassed.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from myco.core.context import MycoContext
from myco.core.write_surface import (
    UNSAFE_WRITE_ENV,
    WriteSurfaceViolation,
    check_write_allowed,
    guarded_write,
    is_path_allowed,
    unsafe_bypass_enabled,
)


def _set_surface(ctx: MycoContext, patterns: list[str]) -> None:
    """Patch the canon's write surface via ``object.__setattr__``
    (``Canon`` is frozen)."""
    object.__setattr__(
        ctx.substrate.canon,
        "system",
        {"write_surface": {"allowed": patterns}},
    )


class TestIsPathAllowed:
    def test_match_exact(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["_canon.yaml"])
        allowed, rel = is_path_allowed(seeded_substrate / "_canon.yaml", ctx)
        assert allowed
        assert rel == "_canon.yaml"

    def test_match_glob(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        raw = seeded_substrate / "notes" / "raw"
        raw.mkdir(parents=True, exist_ok=True)
        target = raw / "n.md"
        allowed, rel = is_path_allowed(target, ctx)
        assert allowed
        assert rel == "notes/raw/n.md"

    def test_reject_outside_surface(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        allowed, rel = is_path_allowed(seeded_substrate / "src" / "leak.py", ctx)
        assert not allowed
        assert rel == "src/leak.py"

    def test_reject_escapes_substrate(
        self, seeded_substrate: Path, tmp_path_factory
    ) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["**/*"])
        # A path in a completely separate tmp dir (``tmp_path_factory``
        # gives a different base than the one ``seeded_substrate`` uses),
        # so the path genuinely escapes the substrate root.
        outside_base = tmp_path_factory.mktemp("outside_substrate")
        outside = outside_base / "not-mine.txt"
        outside.write_text("x", encoding="utf-8")
        allowed, rel = is_path_allowed(outside, ctx)
        assert not allowed
        assert rel is None

    def test_reject_empty_surface(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, [])
        allowed, _ = is_path_allowed(seeded_substrate / "_canon.yaml", ctx)
        assert not allowed

    def test_reject_missing_surface(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        object.__setattr__(ctx.substrate.canon, "system", {})
        allowed, _ = is_path_allowed(seeded_substrate / "_canon.yaml", ctx)
        assert not allowed

    def test_case_sensitive_match(self, seeded_substrate: Path) -> None:
        """v0.5.8 uses ``fnmatchcase`` so the surface is case-sensitive
        (matching POSIX filesystem reality)."""
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["NOTES/**"])
        notes_dir = seeded_substrate / "notes"
        notes_dir.mkdir(exist_ok=True)
        target = notes_dir / "n.md"
        allowed, _ = is_path_allowed(target, ctx)
        assert not allowed  # 'notes' != 'NOTES' under fnmatchcase


class TestGuardedWrite:
    def test_write_in_surface_succeeds(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "notes" / "hello.md"
        rel = guarded_write(ctx, target, "hello")
        assert rel == "notes/hello.md"
        assert target.read_text(encoding="utf-8") == "hello"

    def test_write_outside_surface_raises(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "src" / "leak.py"
        with pytest.raises(WriteSurfaceViolation, match="outside allowed"):
            guarded_write(ctx, target, "pwned")
        assert not target.exists()

    def test_unsafe_bypass_env_allows_write(
        self, seeded_substrate: Path, monkeypatch
    ) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "bypass" / "x.txt"
        monkeypatch.setenv(UNSAFE_WRITE_ENV, "1")
        rel = guarded_write(ctx, target, "allowed via env")
        assert rel == "bypass/x.txt"
        assert target.read_text(encoding="utf-8") == "allowed via env"

    def test_unsafe_bypass_false_values_do_not_enable(
        self, seeded_substrate: Path, monkeypatch
    ) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "src" / "leak.py"
        # Empty string, "0", "false", "no" — none enable the bypass.
        for value in ("", "0", "false", "no", "off"):
            monkeypatch.setenv(UNSAFE_WRITE_ENV, value)
            with pytest.raises(WriteSurfaceViolation):
                guarded_write(ctx, target, "x")

    def test_write_is_atomic_lf(self, seeded_substrate: Path) -> None:
        """``guarded_write`` delegates to ``atomic_utf8_write`` for the
        actual bytes, so LF + UTF-8 + atomicity carry through."""
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "notes" / "multi.md"
        guarded_write(ctx, target, "line1\nline2\n")
        raw = target.read_bytes()
        assert raw == b"line1\nline2\n"
        assert b"\r\n" not in raw


class TestWriteSurfaceViolationIsMycoError:
    def test_is_myco_error(self) -> None:
        from myco.core.errors import MycoError

        assert issubclass(WriteSurfaceViolation, MycoError)

    def test_exit_code_three(self) -> None:
        assert WriteSurfaceViolation.exit_code == 3


class TestCheckWriteAllowed:
    """``check_write_allowed`` is the public bypass-aware guard used
    by verbs that do their own file I/O (eat's O_EXCL loop etc.) but
    still want the full write_surface + env-bypass semantics."""

    def test_allowed_path_is_silent(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "notes" / "hello.md"
        # Does not raise.
        check_write_allowed(ctx, target, verb="test")

    def test_disallowed_path_raises(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "src" / "leak.py"
        with pytest.raises(WriteSurfaceViolation, match="test:"):
            check_write_allowed(ctx, target, verb="test")

    def test_verb_name_surfaces_in_message(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, [])
        target = seeded_substrate / "any.md"
        with pytest.raises(WriteSurfaceViolation) as exc_info:
            check_write_allowed(ctx, target, verb="my-verb-name")
        assert "my-verb-name:" in str(exc_info.value)

    def test_bypass_env_suppresses_raise(
        self, seeded_substrate: Path, monkeypatch
    ) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["notes/**"])
        target = seeded_substrate / "src" / "leak.py"
        monkeypatch.setenv(UNSAFE_WRITE_ENV, "1")
        # Does not raise despite being outside surface.
        check_write_allowed(ctx, target, verb="test")

    def test_violation_lists_allowed_patterns(self, seeded_substrate: Path) -> None:
        ctx = MycoContext.for_testing(root=seeded_substrate)
        _set_surface(ctx, ["a/**", "b/**"])
        target = seeded_substrate / "c" / "x.md"
        with pytest.raises(WriteSurfaceViolation) as exc_info:
            check_write_allowed(ctx, target, verb="test")
        msg = str(exc_info.value)
        assert "a/**" in msg
        assert "b/**" in msg


class TestUnsafeBypassEnabled:
    def test_unset_is_false(self, monkeypatch) -> None:
        monkeypatch.delenv(UNSAFE_WRITE_ENV, raising=False)
        assert not unsafe_bypass_enabled()

    def test_truthy_values(self, monkeypatch) -> None:
        for value in ("1", "true", "TRUE", "yes", "YES", "on", "ON"):
            monkeypatch.setenv(UNSAFE_WRITE_ENV, value)
            assert unsafe_bypass_enabled(), f"expected truthy on {value!r}"

    def test_falsy_values(self, monkeypatch) -> None:
        for value in ("", "0", "false", "FALSE", "no", "NO", "off", "random"):
            monkeypatch.setenv(UNSAFE_WRITE_ENV, value)
            assert not unsafe_bypass_enabled(), f"expected falsy on {value!r}"

    def test_whitespace_trimmed(self, monkeypatch) -> None:
        monkeypatch.setenv(UNSAFE_WRITE_ENV, "  1  ")
        assert unsafe_bypass_enabled()
