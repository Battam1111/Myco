"""Bridge stdio framing — read/write length-prefixed frames.

## Frame format

::

    [u32 BE length, 4 bytes] [frame body, length bytes]

Where the frame body is the HMAC + canonical-bytes body
(see :mod:`myco_kernel_bridge.protocol`).

## I/O contract

- Reads block until a complete frame is received or EOF.
- Writes flush after each frame.
- Both sides use binary stdio (``sys.stdin.buffer`` / ``sys.stdout.buffer``).
- Length is a strict u32 big-endian (0 to 4_294_967_295).
- Frames larger than :data:`MAX_FRAME_BODY_SIZE` are rejected.

## Errors

- :class:`EndOfStreamError` — peer closed the stream cleanly between frames.
- :class:`TruncatedFrameError` — partial read mid-frame; peer crashed or
  pipe broke.
- :class:`FrameTooLargeError` — incoming length prefix exceeds the cap.
"""

from __future__ import annotations

import struct
from typing import BinaryIO

from myco_kernel_bridge.protocol import (
    FrameTooLargeError,
    MAX_FRAME_BODY_SIZE,
)


class EndOfStreamError(Exception):
    """The peer closed the stream cleanly between frames."""


class TruncatedFrameError(Exception):
    """Partial read mid-frame — peer crashed or pipe broke."""


def read_exact(stream: BinaryIO, n: int) -> bytes:
    """Read exactly ``n`` bytes from ``stream`` or raise.

    Raises:
        EndOfStreamError: if no bytes available at all (clean EOF).
        TruncatedFrameError: if EOF mid-read (peer crashed).
    """
    if n == 0:
        return b""
    buf = bytearray()
    while len(buf) < n:
        chunk = stream.read(n - len(buf))
        if not chunk:
            if len(buf) == 0:
                raise EndOfStreamError()
            raise TruncatedFrameError(
                f"truncated read: got {len(buf)} of {n} bytes before EOF"
            )
        buf.extend(chunk)
    return bytes(buf)


def read_frame(stream: BinaryIO) -> bytes:
    """Read one length-prefixed frame from ``stream`` and return the frame body.

    The returned bytes are the **frame body** (HMAC + canonical-bytes body) —
    NOT including the u32 length prefix.

    Raises:
        EndOfStreamError: on clean EOF between frames.
        TruncatedFrameError: on mid-frame EOF.
        FrameTooLargeError: if the length exceeds :data:`MAX_FRAME_BODY_SIZE`.
    """
    length_bytes = read_exact(stream, 4)
    (length,) = struct.unpack(">I", length_bytes)
    if length > MAX_FRAME_BODY_SIZE:
        raise FrameTooLargeError(
            f"incoming frame size {length} exceeds cap {MAX_FRAME_BODY_SIZE}"
        )
    return read_exact(stream, length)


def write_frame(stream: BinaryIO, frame_body: bytes) -> None:
    """Write one length-prefixed frame to ``stream`` and flush.

    Args:
        stream: binary write stream.
        frame_body: HMAC + canonical-bytes body bytes (no length prefix).

    Raises:
        FrameTooLargeError: if ``frame_body`` exceeds :data:`MAX_FRAME_BODY_SIZE`.
    """
    if len(frame_body) > MAX_FRAME_BODY_SIZE:
        raise FrameTooLargeError(
            f"outgoing frame size {len(frame_body)} exceeds cap {MAX_FRAME_BODY_SIZE}"
        )
    length_bytes = struct.pack(">I", len(frame_body))
    stream.write(length_bytes)
    stream.write(frame_body)
    stream.flush()
