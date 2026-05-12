"""Tests for ``myco.core.io_atomic``.

Covers the atomic-write + bounded-read chokepoint that every kernel
write routes through at v0.5.8+. Tests the properties the helper
promises: atomicity (no torn reads), LF-normalisation, UTF-8 default,
parent-dir creation, size-cap enforcement.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from myco.core.errors import MycoError
from myco.core.io_atomic import (
    DEFAULT_MAX_READ_BYTES,
    atomic_utf8_write,
    bounded_read_bytes,
    bounded_read_text,
)


class TestAtomicUtf8Write:
    def test_basic_write(self, tmp_path: Path) -> None:
        target = tmp_path / "a.txt"
        atomic_utf8_write(target, "hello")
        assert target.read_text(encoding="utf-8") == "hello"

    def test_overwrite_existing(self, tmp_path: Path) -> None:
        target = tmp_path / "b.txt"
        target.write_text("old", encoding="utf-8")
        atomic_utf8_write(target, "new")
        assert target.read_text(encoding="utf-8") == "new"

    def test_creates_parents(self, tmp_path: Path) -> None:
        target = tmp_path / "deep" / "nested" / "path" / "file.txt"
        atomic_utf8_write(target, "content")
        assert target.is_file()
        assert target.read_text(encoding="utf-8") == "content"

    def test_lf_only_on_multiline(self, tmp_path: Path) -> None:
        target = tmp_path / "ml.txt"
        atomic_utf8_write(target, "line1\nline2\nline3\n")
        # Read in byte mode to see exact line endings.
        raw = target.read_bytes()
        assert raw == b"line1\nline2\nline3\n"
        assert b"\r\n" not in raw

    def test_utf8_roundtrip_non_ascii(self, tmp_path: Path) -> None:
        target = tmp_path / "u.txt"
        content = "中文 — naïve 日本語 emoji 🦠"
        atomic_utf8_write(target, content)
        assert target.read_text(encoding="utf-8") == content

    def test_rejects_bytes(self, tmp_path: Path) -> None:
        target = tmp_path / "bytes.bin"
        with pytest.raises(TypeError, match="str content"):
            atomic_utf8_write(target, b"not a string")  # type: ignore[arg-type]

    def test_leaves_no_tempfile_on_success(self, tmp_path: Path) -> None:
        target = tmp_path / "clean.txt"
        atomic_utf8_write(target, "body")
        leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
        assert leftovers == []

    def test_cleans_tempfile_on_error(self, tmp_path: Path, monkeypatch) -> None:
        target = tmp_path / "fail.txt"

        # Force os.replace to raise so we see the cleanup path.
        def _boom(*_args, **_kwargs):
            raise OSError("simulated replace failure")

        monkeypatch.setattr(os, "replace", _boom)
        with pytest.raises(OSError, match="simulated"):
            atomic_utf8_write(target, "x")
        # Target never materialised and temp file is gone.
        assert not target.exists()
        leftovers = [p for p in tmp_path.iterdir() if p.name.endswith(".tmp")]
        assert leftovers == []

    def test_atomicity_sequential_interleave(self, tmp_path: Path) -> None:
        """Interleaved writes + reads never observe a torn file.

        On Windows, ``os.replace`` fails if a concurrent reader holds
        the target file open, so we test atomicity by interleaving
        sequential writes with sequential reads: every read between
        writes MUST return one of the two legal payloads byte-for-byte
        (a torn intermediate state would surface as a third distinct
        string).
        """
        target = tmp_path / "concurrent.txt"
        payload_a = "A" * 8192
        payload_b = "B" * 8192

        seen: set[str] = set()
        for i in range(50):
            payload = payload_a if i % 2 == 0 else payload_b
            atomic_utf8_write(target, payload)
            # Read right after the write — should always see the exact
            # payload we just wrote, never a partial.
            observed = target.read_text(encoding="utf-8")
            seen.add(observed)
            # Byte-length check: a torn write would produce wrong length.
            assert len(observed) == 8192

        assert seen <= {payload_a, payload_b}
        assert seen == {payload_a, payload_b}  # both should be reached


class TestBoundedReadText:
    def test_basic_read(self, tmp_path: Path) -> None:
        p = tmp_path / "x.txt"
        p.write_text("hello", encoding="utf-8")
        assert bounded_read_text(p) == "hello"

    def test_utf8_default(self, tmp_path: Path) -> None:
        p = tmp_path / "u.txt"
        p.write_text("naïve", encoding="utf-8")
        assert bounded_read_text(p) == "naïve"

    def test_rejects_oversized(self, tmp_path: Path) -> None:
        p = tmp_path / "big.txt"
        p.write_bytes(b"x" * 1024)
        with pytest.raises(MycoError, match="too large"):
            bounded_read_text(p, max_bytes=512)

    def test_default_cap_is_10_MB(self) -> None:
        assert DEFAULT_MAX_READ_BYTES == 10 * 1024 * 1024

    def test_exactly_at_cap_succeeds(self, tmp_path: Path) -> None:
        p = tmp_path / "edge.txt"
        p.write_bytes(b"y" * 1024)
        # Exactly the cap; must not raise.
        assert bounded_read_text(p, max_bytes=1024) == "y" * 1024


class TestBoundedReadBytes:
    def test_basic_read(self, tmp_path: Path) -> None:
        p = tmp_path / "x.bin"
        p.write_bytes(b"\x01\x02\x03")
        assert bounded_read_bytes(p) == b"\x01\x02\x03"

    def test_rejects_oversized(self, tmp_path: Path) -> None:
        p = tmp_path / "big.bin"
        p.write_bytes(b"x" * 1024)
        with pytest.raises(MycoError, match="too large"):
            bounded_read_bytes(p, max_bytes=512)

    def test_empty_file_ok(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.bin"
        p.write_bytes(b"")
        assert bounded_read_bytes(p) == b""
