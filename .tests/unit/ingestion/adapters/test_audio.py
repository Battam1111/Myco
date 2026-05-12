"""Tests for the audio adapter (v0.8.0 multimedia extras, 1 of 3).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) for the audio modality.

These tests pin the v0.8.0 contract for the 11th adapter:

* ``can_handle`` — claims the 5 canonical extensions (.wav, .mp3,
  .flac, .m4a, .ogg) by suffix only; rejects everything else,
  including credential-glob filenames and oversize files.
* ``ingest`` — emits one IngestResult per Whisper segment when the
  extras are installed, OR a single failed-stub naming the
  ``[multimedia]`` install hint when whisper is absent.
* **The key test** is the ImportError mock: CI machines do NOT have
  whisper installed, and the adapter MUST emit the install-extras
  failed-stub rather than crashing when ``import whisper`` raises.

All happy-path tests use mocks (no real whisper / PyTorch needed).
This is essential because:

1. The whisper transitive closure is ~500 MB — installing it on
   every CI run is wasteful.
2. The default install (``pip install myco``) does NOT pull
   whisper. The adapter's whole point is the lazy-import +
   failed-stub pattern, which mocks exercise correctly.
3. Real Whisper happy-path coverage belongs to the integration
   suite (gated on ``MYCO_RUN_MULTIMEDIA_E2E=1``), out of scope
   for v0.8.0 — see the v0.7.10 examples-only IOU footnote.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from myco.ingestion.adapters.multimedia_cluster import (
    DEFAULT_MAX_AUDIO_BYTES,
    AudioAdapter,
)

pytestmark = pytest.mark.multimedia


# ---------------------------------------------------------------------------
# can_handle: extension claim, credential / size denials
# ---------------------------------------------------------------------------


def _make_audio_stub(tmp_path: Path, name: str, size: int = 1024) -> Path:
    """Create a stub file with the given name and approximate size.

    The file's bytes don't matter for ``can_handle`` (it only inspects
    the path/extension/stat) — we just need a real file on disk.
    """
    p = tmp_path / name
    p.write_bytes(b"\x00" * size)
    return p


def test_can_handle_wav_extension(tmp_path: Path) -> None:
    """``.wav`` files are claimed by the audio adapter."""
    p = _make_audio_stub(tmp_path, "lecture.wav")
    assert AudioAdapter().can_handle(str(p)) is True


def test_can_handle_mp3_extension(tmp_path: Path) -> None:
    """``.mp3`` files are claimed."""
    p = _make_audio_stub(tmp_path, "podcast.mp3")
    assert AudioAdapter().can_handle(str(p)) is True


def test_can_handle_flac_extension(tmp_path: Path) -> None:
    """``.flac`` files are claimed (lossless audio)."""
    p = _make_audio_stub(tmp_path, "music.flac")
    assert AudioAdapter().can_handle(str(p)) is True


def test_can_handle_m4a_extension(tmp_path: Path) -> None:
    """``.m4a`` files are claimed (Apple's MPEG-4 audio container)."""
    p = _make_audio_stub(tmp_path, "voice-note.m4a")
    assert AudioAdapter().can_handle(str(p)) is True


def test_can_handle_ogg_extension(tmp_path: Path) -> None:
    """``.ogg`` files are claimed (Vorbis container)."""
    p = _make_audio_stub(tmp_path, "open.ogg")
    assert AudioAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_non_audio(tmp_path: Path) -> None:
    """Non-audio extensions must NOT be claimed.

    The audio adapter is the gatekeeper for these five suffixes; a
    ``.txt`` or ``.png`` claim would short-circuit text-file or
    image-OCR routing.
    """
    adapter = AudioAdapter()
    for name in ("plain.txt", "doc.md", "data.csv", "image.png", "noext"):
        p = tmp_path / name
        p.write_bytes(b"hello")
        assert adapter.can_handle(str(p)) is False, f"unexpected claim: {name!r}"
    # A directory with an audio-looking name must also be rejected.
    d = tmp_path / "fake.mp3"
    d.mkdir()
    assert adapter.can_handle(str(d)) is False


def test_can_handle_rejects_credential_filename(tmp_path: Path) -> None:
    """Credential-glob names refuse claim regardless of audio extension.

    Mirrors text_file's defense: ``id_rsa.wav`` (contrived but the
    pattern is uniform) cannot exfiltrate via ``myco eat --path``.
    """
    p = _make_audio_stub(tmp_path, "id_rsa.wav")
    assert AudioAdapter().can_handle(str(p)) is False


def test_can_handle_rejects_oversize(tmp_path: Path, monkeypatch) -> None:
    """Files over the 100 MB cap are rejected at can_handle.

    We monkeypatch the cap down to 1 KB so the test runs without
    actually creating a 100 MB file — the cap mechanic itself is
    independent of the constant value.
    """
    monkeypatch.setattr(
        "myco.ingestion.adapters.multimedia_cluster.DEFAULT_MAX_AUDIO_BYTES", 100
    )
    p = _make_audio_stub(tmp_path, "big.wav", size=200)
    assert AudioAdapter().can_handle(str(p)) is False


# ---------------------------------------------------------------------------
# ingest: missing-dep path (the key CI test)
# ---------------------------------------------------------------------------


def test_ingest_returns_failed_stub_when_dep_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**THIS IS THE KEY TEST**: ``import whisper`` raising ImportError
    must produce a single failed-stub naming the install-extras hint.

    CI machines do NOT have whisper installed. Without this contract,
    every audio file forage encounters in CI would either crash the
    eat() call or silently skip — both unacceptable. We mock the
    import by stashing ``None`` into ``sys.modules['whisper']`` so the
    adapter's lazy ``import whisper`` line raises ImportError.
    """
    p = _make_audio_stub(tmp_path, "talk.mp3")
    # Force ``import whisper`` to raise ImportError. Setting a key to
    # None in sys.modules triggers ImportError on subsequent imports.
    monkeypatch.setitem(sys.modules, "whisper", None)
    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "myco[multimedia]" in results[0].failure_reason
    assert "pip install" in results[0].failure_reason


def test_ingest_oversize_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file over the size cap → single failed-stub naming the cap.

    Even with whisper available, the size-cap branch fires before
    the lazy import so we don't need to mock whisper here.
    """
    monkeypatch.setattr(
        "myco.ingestion.adapters.multimedia_cluster.DEFAULT_MAX_AUDIO_BYTES", 100
    )
    p = _make_audio_stub(tmp_path, "big.mp3", size=500)
    adapter = AudioAdapter()
    # can_handle rejects BEFORE any import attempt.
    assert adapter.can_handle(str(p)) is False
    # Direct ingest call must also refuse with a failed-stub.
    results = list(adapter.ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``id_rsa.wav`` → can_handle False, ingest emits failed-stub if
    called directly. Defense-in-depth per the chat_log v0.7.5
    precedent.
    """
    p = _make_audio_stub(tmp_path, "id_rsa.wav")
    adapter = AudioAdapter()
    assert adapter.can_handle(str(p)) is False
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


def test_ingest_corrupt_audio_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A whisper transcription RuntimeError → single failed-stub.

    We inject a fake whisper module whose ``load_model`` returns a
    fake model whose ``transcribe`` raises RuntimeError (simulating
    corrupt audio / sample-rate mismatch / missing ffmpeg).
    """
    p = _make_audio_stub(tmp_path, "corrupt.wav")

    class _FakeModel:
        def transcribe(self, _path):
            raise RuntimeError("ffmpeg failed to decode audio")

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "transcription failed" in results[0].failure_reason
    assert "ffmpeg" in results[0].failure_reason


def test_ingest_model_load_failure_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``whisper.load_model`` raising → single failed-stub naming the
    model and the cause. Disk-full / network-unreachable scenario.
    """
    p = _make_audio_stub(tmp_path, "talk.mp3")

    fake_whisper = types.ModuleType("whisper")

    def _bad_load(_name):
        raise OSError("no space left on device")

    fake_whisper.load_model = _bad_load  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "model load failed" in results[0].failure_reason
    assert "no space" in results[0].failure_reason


def test_ingest_emits_one_result_per_segment(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Happy path with a fake whisper: 3 segments → 3 ok IngestResults
    with start_sec / end_sec / segment_index metadata.
    """
    p = _make_audio_stub(tmp_path, "talk.mp3")

    fake_segments = [
        {"start": 0.0, "end": 5.0, "text": "Hello and welcome."},
        {"start": 5.0, "end": 12.5, "text": "Today's topic is mycelium."},
        {"start": 12.5, "end": 20.0, "text": "Three rounds of craft follow."},
    ]

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": fake_segments, "text": "joined text"}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    assert all(r.metadata["kind"] == "audio-transcript-segment" for r in results)
    assert [r.metadata["segment_index"] for r in results] == [0, 1, 2]
    assert results[0].metadata["start_sec"] == 0.0
    assert results[0].metadata["end_sec"] == 5.0
    assert results[0].metadata["speaker_label"] == "speaker"
    assert "Hello and welcome." in results[0].body
    assert "Today's topic" in results[1].body
    assert results[0].metadata["source_file"].endswith("talk.mp3")


def test_ingest_no_segments_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whisper returning ``segments=[]`` → single failed-stub naming
    the silence/below-threshold cause. Belt-and-suspenders for
    the "audio is silent" branch.
    """
    p = _make_audio_stub(tmp_path, "silence.wav")

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": [], "text": ""}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no segments" in results[0].failure_reason


def test_ingest_empty_text_segment_emits_per_segment_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A whisper segment with empty text → per-segment failed-stub
    rather than silent drop. Loud-skip per AD1.
    """
    p = _make_audio_stub(tmp_path, "mixed.wav")

    fake_segments = [
        {"start": 0.0, "end": 3.0, "text": "Real content here."},
        {"start": 3.0, "end": 5.0, "text": "   "},  # whitespace-only
        {"start": 5.0, "end": 9.0, "text": "More content after."},
    ]

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": fake_segments}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 3
    statuses = [r.status for r in results]
    assert statuses == ["ok", "failed", "ok"]
    assert "empty transcript" in results[1].failure_reason


# ---------------------------------------------------------------------------
# Registry: discoverable in priority order
# ---------------------------------------------------------------------------


def test_audio_adapter_registered_before_text_file() -> None:
    """The audio adapter must register BEFORE text-file in the registry.

    The brief specifies multimedia adapters land before text-file so
    their more-specific extension claims (``.wav``, ``.mp3``, etc.)
    win the routing race. (Practically, text-file's NUL-byte heuristic
    would reject a binary audio file anyway, but the failed-stub on
    a missing-dep direct call is louder than a silent skip.)
    """
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.multimedia_cluster import AudioAdapter as AA
    from myco.ingestion.adapters.stdlib_simple_cluster import TextFileAdapter as TF

    adapters = list(all_adapters())
    aa_idx = next((i for i, a in enumerate(adapters) if isinstance(a, AA)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert aa_idx >= 0, "AudioAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert aa_idx < tf_idx, (
        f"AudioAdapter (idx {aa_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )


def test_default_max_audio_bytes_is_100mb() -> None:
    """The size cap is 100 MB per the v0.8.0 multimedia craft.

    Documented separately from the runtime branch tests so a future
    cap-ratchet (e.g. raising to 200 MB for hi-fi recordings) shows
    up as a single test to update with explicit intent.
    """
    assert DEFAULT_MAX_AUDIO_BYTES == 100 * 1024 * 1024


# ---------------------------------------------------------------------------
# Additional defensive paths for v0.9 cov-floor revert (≥85%).
# These cover branches the v0.8 happy-path tests didn't reach.
# ---------------------------------------------------------------------------


def test_ingest_unexpected_transcription_shape_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Whisper returning a non-dict (e.g. list) → single failed-stub naming
    the unexpected-shape cause. Defensive against future Whisper API
    changes or wrapper bugs.
    """
    p = _make_audio_stub(tmp_path, "shape-error.wav")

    class _FakeModel:
        def transcribe(self, _path):
            return ["not", "a", "dict"]  # shape contract violation

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "unexpected shape" in results[0].failure_reason
    assert "list" in results[0].failure_reason


def test_ingest_segments_not_a_list_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``segments`` field present but not a list → no-segments failed-stub.

    Defensive: a malformed Whisper response with ``segments=None`` /
    ``segments={}`` must not crash the iteration loop.
    """
    p = _make_audio_stub(tmp_path, "bad-segments.wav")

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": "not a list", "text": ""}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no segments" in results[0].failure_reason


def test_ingest_malformed_segment_emits_per_segment_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-dict segment in the segments list → per-segment failed-stub
    naming the malformed shape. AD1 loud-skip per segment.
    """
    p = _make_audio_stub(tmp_path, "mixed-malformed.wav")

    fake_segments = [
        {"start": 0.0, "end": 3.0, "text": "Real content here."},
        "not a dict — broken",  # malformed
        {"start": 5.0, "end": 9.0, "text": "After the malformed entry."},
    ]

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": fake_segments}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 3
    statuses = [r.status for r in results]
    assert statuses == ["ok", "failed", "ok"]
    assert "malformed" in results[1].failure_reason
    assert "str" in results[1].failure_reason


def test_ingest_segment_with_invalid_start_end_falls_back_to_zero(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A segment whose start/end aren't numeric (TypeError/ValueError on
    ``float()``) → segment is still emitted as ok with start=end=0.0
    (defensive zero rather than per-segment failed-stub).
    """
    p = _make_audio_stub(tmp_path, "bad-times.wav")

    fake_segments = [
        {"start": "not a number", "end": [1, 2], "text": "Has text but bad times."},
    ]

    class _FakeModel:
        def transcribe(self, _path):
            return {"segments": fake_segments}

    fake_whisper = types.ModuleType("whisper")
    fake_whisper.load_model = lambda _name: _FakeModel()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "whisper", fake_whisper)

    results = list(AudioAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].metadata["start_sec"] == 0.0
    assert results[0].metadata["end_sec"] == 0.0
    assert "Has text" in results[0].body
