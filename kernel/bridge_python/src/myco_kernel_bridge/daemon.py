"""Bridge daemon main loop — read frames from stdin, dispatch, write to stdout.

## Lifecycle

1. Read first frame; expect a ``hello`` message keyed by :data:`BOOTSTRAP_KEY`.
2. Verify HMAC, extract session_secret, send ``hello_ack``.
3. Loop: read frame keyed by session_secret → dispatch → write response.
4. On ``shutdown``: write ``shutdown_ack``, then exit cleanly.
5. On any error: write ``error`` envelope echoing the failed request_id.
6. On stdin EOF without prior shutdown: exit (parent process died).

## Stdio binary mode

The daemon uses ``sys.stdin.buffer`` and ``sys.stdout.buffer`` to bypass
Python's text-mode line-ending mangling. On Windows this is critical
(binary mode prevents CRLF translation).

## Error policy

- Protocol errors (malformed frame, bad version, unknown type) → write
  an ``error`` envelope on the corresponding request_id and continue
  the loop (the controller can retry or shutdown).
- HMAC mismatch → write an ``error`` envelope keyed with the current
  session_secret if it exists, else exit (controller is hostile or
  protocol is desync'd beyond recovery).
- Stream errors (EOF mid-frame) → exit immediately; the controller will
  detect the subprocess died via wait()/poll().
"""

from __future__ import annotations

import sys
from typing import BinaryIO

from myco_kernel_bridge.dispatcher import (
    DispatcherState,
    build_error_response,
    dispatch,
)
from myco_kernel_bridge.framing import (
    EndOfStreamError,
    TruncatedFrameError,
    read_frame,
    write_frame,
)
from myco_kernel_bridge.protocol import (
    BOOTSTRAP_KEY,
    BridgeProtocolError,
    HmacMismatchError,
    Message,
    MessageType,
    decode_message,
    encode_message,
)


def _write_error(
    stream: BinaryIO,
    *,
    in_response_to: int,
    code: str,
    message: str,
    key: bytes,
) -> None:
    """Write an error envelope keyed by ``key`` (which may be BOOTSTRAP_KEY
    if no session yet, or session_secret if handshake completed)."""
    err = build_error_response(in_response_to, code, message)
    frame = encode_message(err, key)
    write_frame(stream, frame)


def run_loop(stdin: BinaryIO, stdout: BinaryIO) -> int:
    """Run the bridge daemon main loop until exit.

    Returns:
        OS exit code (0 = clean shutdown; 1 = stream / fatal error;
        2 = handshake failed before completion).
    """
    state = DispatcherState()
    while True:
        # Determine key for the next frame: BOOTSTRAP_KEY pre-handshake,
        # session_secret post-handshake.
        expected_key = (
            state.session_secret
            if state.handshake_complete and state.session_secret is not None
            else BOOTSTRAP_KEY
        )

        try:
            frame_body = read_frame(stdin)
        except EndOfStreamError:
            return 0 if state.handshake_complete else 2
        except TruncatedFrameError:
            return 1

        try:
            request = decode_message(frame_body, expected_key)
        except HmacMismatchError as e:
            # If we have a session key, we can write an error using it. If
            # we don't (pre-handshake), the controller is broken — exit.
            if state.handshake_complete and state.session_secret is not None:
                _write_error(
                    stdout,
                    in_response_to=0,
                    code="hmac_mismatch",
                    message=str(e),
                    key=state.session_secret,
                )
                continue
            return 2
        except BridgeProtocolError as e:
            # Same logic: write error if we have a session key, else exit.
            if state.handshake_complete and state.session_secret is not None:
                _write_error(
                    stdout,
                    in_response_to=0,
                    code="protocol_error",
                    message=str(e),
                    key=state.session_secret,
                )
                continue
            return 2

        # Dispatch.
        try:
            response = dispatch(state, request)
        except BridgeProtocolError as e:
            response_key = (
                state.session_secret
                if state.handshake_complete and state.session_secret is not None
                else BOOTSTRAP_KEY
            )
            _write_error(
                stdout,
                in_response_to=request.request_id,
                code="dispatcher_error",
                message=str(e),
                key=response_key,
            )
            continue

        if response is None:
            return 0

        # Write response. Keying: HELLO_ACK uses session_secret (which was
        # just transported by the HELLO request); everything else uses the
        # established session_secret.
        if state.session_secret is None:
            # Should never happen post-dispatch except for malformed flows.
            return 2
        response_frame = encode_message(response, state.session_secret)
        write_frame(stdout, response_frame)

        if request.type is MessageType.SHUTDOWN:
            return 0


def main() -> int:
    """Entry point for the ``myco-kernel-bridge-daemon`` script."""
    return run_loop(sys.stdin.buffer, sys.stdout.buffer)
