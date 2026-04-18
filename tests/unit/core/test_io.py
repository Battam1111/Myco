"""Tests for ``myco.core.io``."""

from __future__ import annotations

import io
import sys

import pytest

from myco.core.io import ensure_utf8_stdio


def test_reconfigures_stdout_and_stderr_to_utf8(monkeypatch) -> None:
    class FakeStream:
        def __init__(self, encoding: str) -> None:
            self.encoding = encoding
            self.errors = "strict"

        def reconfigure(self, *, encoding: str, errors: str) -> None:
            self.encoding = encoding
            self.errors = errors

    fake_out = FakeStream(encoding="cp936")
    fake_err = FakeStream(encoding="cp936")
    monkeypatch.setattr(sys, "stdout", fake_out)
    monkeypatch.setattr(sys, "stderr", fake_err)

    ensure_utf8_stdio()

    assert fake_out.encoding == "utf-8"
    assert fake_out.errors == "replace"
    assert fake_err.encoding == "utf-8"
    assert fake_err.errors == "replace"


def test_silent_on_streams_without_reconfigure(monkeypatch) -> None:
    class NoReconfigure:
        encoding = "cp936"

    monkeypatch.setattr(sys, "stdout", NoReconfigure())
    monkeypatch.setattr(sys, "stderr", NoReconfigure())

    # Must not raise.
    ensure_utf8_stdio()


def test_swallows_reconfigure_failure(monkeypatch) -> None:
    class Flaky:
        encoding = "cp936"
        errors = "strict"

        def reconfigure(self, *, encoding: str, errors: str) -> None:
            raise ValueError("stream detached")

    monkeypatch.setattr(sys, "stdout", Flaky())
    monkeypatch.setattr(sys, "stderr", Flaky())

    # Must not raise; the CLI should keep running even if the guard fails.
    ensure_utf8_stdio()


def test_is_idempotent(monkeypatch) -> None:
    calls: list[tuple[str, str]] = []

    class FakeStream:
        encoding = "utf-8"
        errors = "replace"

        def reconfigure(self, *, encoding: str, errors: str) -> None:
            calls.append((encoding, errors))

    monkeypatch.setattr(sys, "stdout", FakeStream())
    monkeypatch.setattr(sys, "stderr", FakeStream())

    ensure_utf8_stdio()
    ensure_utf8_stdio()

    assert all(call == ("utf-8", "replace") for call in calls)


def test_non_ascii_print_survives_after_call(capsys, monkeypatch) -> None:
    """Regression: ensure_utf8_stdio lets us print box-drawing/CJK
    content without the cp936/gbk UnicodeEncodeError the install
    dry-run hit on Chinese Windows."""
    # capsys gives us UTF-8 text streams already, so this is an integration
    # check that the function runs on them without error and the write
    # still succeeds.
    ensure_utf8_stdio()
    print("\u2591\u2592\u2593\u2588 \u4e2d\u6587")
    captured = capsys.readouterr()
    assert "中文" in captured.out
