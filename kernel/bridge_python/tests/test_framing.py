"""Tests for kernel/bridge_python framing — in-process via BytesIO."""

from __future__ import annotations

import io
import struct

import pytest

from myco_kernel_bridge.framing import (
    EndOfStreamError,
    TruncatedFrameError,
    read_exact,
    read_frame,
    write_frame,
)
from myco_kernel_bridge.protocol import FrameTooLargeError, MAX_FRAME_BODY_SIZE


def test_read_exact_zero() -> None:
    stream = io.BytesIO(b"hello")
    assert read_exact(stream, 0) == b""


def test_read_exact_short() -> None:
    stream = io.BytesIO(b"hello world")
    assert read_exact(stream, 5) == b"hello"
    assert read_exact(stream, 6) == b" world"


def test_read_exact_eof() -> None:
    stream = io.BytesIO(b"")
    with pytest.raises(EndOfStreamError):
        read_exact(stream, 4)


def test_read_exact_truncated() -> None:
    stream = io.BytesIO(b"abc")
    with pytest.raises(TruncatedFrameError):
        read_exact(stream, 5)


def test_write_then_read_frame_roundtrip() -> None:
    stream = io.BytesIO()
    body = b"\x01\x02\x03"
    write_frame(stream, body)
    stream.seek(0)
    got = read_frame(stream)
    assert got == body


def test_write_frame_length_prefix() -> None:
    stream = io.BytesIO()
    body = b"abcd"
    write_frame(stream, body)
    raw = stream.getvalue()
    expected_prefix = struct.pack(">I", 4)
    assert raw[:4] == expected_prefix
    assert raw[4:] == body


def test_read_frame_eof_clean() -> None:
    stream = io.BytesIO(b"")
    with pytest.raises(EndOfStreamError):
        read_frame(stream)


def test_read_frame_partial_length_prefix() -> None:
    stream = io.BytesIO(b"\x00\x00")  # only 2 of 4 length bytes
    with pytest.raises(TruncatedFrameError):
        read_frame(stream)


def test_read_frame_partial_body() -> None:
    # Length prefix says 10 bytes, but only 3 available.
    stream = io.BytesIO(struct.pack(">I", 10) + b"abc")
    with pytest.raises(TruncatedFrameError):
        read_frame(stream)


def test_read_frame_too_large_rejected() -> None:
    # Length prefix says 1 MiB + 1.
    huge_length = MAX_FRAME_BODY_SIZE + 1
    stream = io.BytesIO(struct.pack(">I", huge_length))
    with pytest.raises(FrameTooLargeError):
        read_frame(stream)


def test_write_frame_too_large_rejected() -> None:
    stream = io.BytesIO()
    huge_body = b"x" * (MAX_FRAME_BODY_SIZE + 1)
    with pytest.raises(FrameTooLargeError):
        write_frame(stream, huge_body)


def test_read_two_frames_in_sequence() -> None:
    stream = io.BytesIO()
    write_frame(stream, b"first")
    write_frame(stream, b"second-frame")
    stream.seek(0)
    assert read_frame(stream) == b"first"
    assert read_frame(stream) == b"second-frame"


def test_read_frame_then_eof() -> None:
    stream = io.BytesIO()
    write_frame(stream, b"data")
    stream.seek(0)
    assert read_frame(stream) == b"data"
    with pytest.raises(EndOfStreamError):
        read_frame(stream)
