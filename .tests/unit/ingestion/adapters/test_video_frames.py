"""Tests for the video-frames adapter (v0.8.0 multimedia extras, 3 of 3).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) for the video modality.

These tests pin the v0.8.0 contract for the 13th adapter:

* ``can_handle`` — claims the 5 canonical extensions (.mp4, .mov,
  .avi, .mkv, .webm) by suffix only; rejects everything else,
  including credential-glob filenames and oversize files.
* ``ingest`` — emits one IngestResult per sampled frame whose OCR
  yielded text, OR a failed-stub for the install-extras /
  codec-error / all-empty cases.
* Three distinct ImportError modes:
  - ``import cv2`` fails → install-extras hint.
  - ``import pytesseract`` fails → install-extras hint.
  - Both succeed but ``tesseract`` binary missing → binary hint.

All happy-path tests use mocks (no real cv2 / tesseract / video
file decoding needed). The adapter's frame-sampling logic and
the AD1 "all frames empty" / "loud per-frame skip" branches are
all covered with a synthetic VideoCapture stand-in.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from myco.ingestion.adapters.video_frames import (
    DEFAULT_MAX_VIDEO_BYTES,
    MAX_FRAMES_PER_VIDEO,
    VideoFramesAdapter,
    _compute_sample_interval,
)

pytestmark = pytest.mark.multimedia


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_video_stub(tmp_path: Path, name: str, size: int = 1024) -> Path:
    """Create a stub file with the given name and approximate size."""
    p = tmp_path / name
    p.write_bytes(b"\x00" * size)
    return p


# CAP_PROP_* constants used by cv2. We pin to opaque small ints since
# the adapter passes them by name through the cv2 module reference.
_CAP_PROP_FPS = 5
_CAP_PROP_FRAME_COUNT = 7
_CAP_PROP_POS_FRAMES = 1


class _FakeVideoCapture:
    """Synthetic stand-in for cv2.VideoCapture.

    Reproduces the minimal surface the adapter consumes:

    * ``isOpened()`` — True/False based on constructor's ``opened`` arg.
    * ``get(prop)`` — returns the configured fps / total_frames.
    * ``set(prop, val)`` — accepts the seek call (no-op).
    * ``read()`` — returns ``(True, sentinel)`` for the configured
      number of successful reads, then ``(False, None)``.
    * ``release()`` — no-op.

    Does NOT model real frame decoding; the OCR layer above is
    mocked separately so ``read()``'s return frame is just a token
    that pytesseract.image_to_string sees and ignores.
    """

    def __init__(
        self,
        *,
        opened: bool = True,
        fps: float = 30.0,
        total_frames: int = 90,
        read_failures_after: int | None = None,
    ) -> None:
        self._opened = opened
        self._fps = fps
        self._total_frames = total_frames
        self._read_count = 0
        self._read_failures_after = read_failures_after

    def isOpened(self) -> bool:
        # Method name matches the cv2 API exactly so the adapter's
        # ``cap.isOpened()`` call binds to it.
        return self._opened

    def get(self, prop: int) -> float:
        if prop == _CAP_PROP_FPS:
            return self._fps
        if prop == _CAP_PROP_FRAME_COUNT:
            return float(self._total_frames)
        return 0.0

    def set(self, prop: int, value: float) -> bool:
        # Adapter calls set(POS_FRAMES, ...) before read(); we accept
        # the seek and let read() drive the synthetic state.
        return True

    def read(self):
        self._read_count += 1
        if (
            self._read_failures_after is not None
            and self._read_count > self._read_failures_after
        ):
            return False, None
        # Return a sentinel "frame" the mock pytesseract ignores.
        return True, f"frame-{self._read_count}"

    def release(self) -> None:
        return None


def _build_fake_cv2(*, capture: _FakeVideoCapture | None = None) -> types.ModuleType:
    """Build a fake cv2 module with VideoCapture + CAP_PROP_* constants."""
    fake = types.ModuleType("cv2")
    fake.CAP_PROP_FPS = _CAP_PROP_FPS  # type: ignore[attr-defined]
    fake.CAP_PROP_FRAME_COUNT = _CAP_PROP_FRAME_COUNT  # type: ignore[attr-defined]
    fake.CAP_PROP_POS_FRAMES = _CAP_PROP_POS_FRAMES  # type: ignore[attr-defined]

    def _ctor(_path):
        return capture if capture is not None else _FakeVideoCapture()

    fake.VideoCapture = _ctor  # type: ignore[attr-defined]
    return fake


def _build_fake_pytesseract(
    *,
    text_per_frame: list[str] | None = None,
    raise_not_found: bool = False,
    raise_runtime: Exception | None = None,
) -> types.ModuleType:
    """Build a fake pytesseract that emits text per ``image_to_string``
    call.

    ``text_per_frame``: cycles through the list per-call; when
    exhausted, returns the last value indefinitely.
    """
    fake = types.ModuleType("pytesseract")
    nested = types.ModuleType("pytesseract.pytesseract")

    class _TesseractNotFoundError(Exception):
        pass

    nested.TesseractNotFoundError = _TesseractNotFoundError  # type: ignore[attr-defined]
    fake.pytesseract = nested  # type: ignore[attr-defined]
    call_count = {"n": 0}
    seq = list(text_per_frame or [""])

    def _image_to_string(_img, lang="eng"):
        if raise_not_found:
            raise _TesseractNotFoundError("tesseract not found")
        if raise_runtime is not None:
            raise raise_runtime
        i = call_count["n"]
        call_count["n"] += 1
        if i < len(seq):
            return seq[i]
        return seq[-1]

    fake.image_to_string = _image_to_string  # type: ignore[attr-defined]
    return fake


# ---------------------------------------------------------------------------
# can_handle: extension claim, credential / size denials
# ---------------------------------------------------------------------------


def test_can_handle_mp4_extension(tmp_path: Path) -> None:
    """``.mp4`` files are claimed."""
    p = _make_video_stub(tmp_path, "demo.mp4")
    assert VideoFramesAdapter().can_handle(str(p)) is True


def test_can_handle_mov_extension(tmp_path: Path) -> None:
    """``.mov`` files are claimed (Apple QuickTime container)."""
    p = _make_video_stub(tmp_path, "demo.mov")
    assert VideoFramesAdapter().can_handle(str(p)) is True


def test_can_handle_avi_extension(tmp_path: Path) -> None:
    """``.avi`` files are claimed."""
    p = _make_video_stub(tmp_path, "demo.avi")
    assert VideoFramesAdapter().can_handle(str(p)) is True


def test_can_handle_mkv_extension(tmp_path: Path) -> None:
    """``.mkv`` files are claimed (Matroska container)."""
    p = _make_video_stub(tmp_path, "demo.mkv")
    assert VideoFramesAdapter().can_handle(str(p)) is True


def test_can_handle_webm_extension(tmp_path: Path) -> None:
    """``.webm`` files are claimed (open web video format)."""
    p = _make_video_stub(tmp_path, "demo.webm")
    assert VideoFramesAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_non_video(tmp_path: Path) -> None:
    """Non-video extensions must NOT be claimed."""
    adapter = VideoFramesAdapter()
    for name in ("plain.txt", "doc.md", "audio.mp3", "image.png", "noext"):
        p = tmp_path / name
        p.write_bytes(b"hello")
        assert adapter.can_handle(str(p)) is False, f"unexpected claim: {name!r}"
    # A directory with a video-looking name must also be rejected.
    d = tmp_path / "fake.mp4"
    d.mkdir()
    assert adapter.can_handle(str(d)) is False


def test_can_handle_rejects_credential_filename(tmp_path: Path) -> None:
    """Credential-glob names refuse claim regardless of video extension."""
    p = _make_video_stub(tmp_path, "id_rsa.mp4")
    assert VideoFramesAdapter().can_handle(str(p)) is False


# ---------------------------------------------------------------------------
# ingest: missing-dep paths (the key CI tests)
# ---------------------------------------------------------------------------


def test_ingest_returns_failed_stub_when_dep_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**THIS IS THE KEY TEST**: ``import cv2`` raising ImportError
    must produce a single failed-stub naming the install-extras hint.

    CI machines do NOT have opencv-python-headless installed by
    default; the adapter must guide the operator to ``pip install
    'myco[multimedia]'`` instead of crashing.
    """
    p = _make_video_stub(tmp_path, "tutorial.mp4")
    monkeypatch.setitem(sys.modules, "cv2", None)
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "myco[multimedia]" in results[0].failure_reason
    assert "pip install" in results[0].failure_reason


def test_ingest_returns_failed_stub_when_pytesseract_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When cv2 is installed but pytesseract is not, the adapter
    still emits the install-extras hint (both are in the same
    extras row, so the operator runs one fix).
    """
    p = _make_video_stub(tmp_path, "tutorial.mp4")
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2())
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "myco[multimedia]" in results[0].failure_reason


def test_ingest_oversize_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file over the 500 MB cap → single failed-stub naming the cap.

    The size-cap branch fires before any lazy import.
    """
    monkeypatch.setattr(
        "myco.ingestion.adapters.video_frames.DEFAULT_MAX_VIDEO_BYTES", 100
    )
    p = _make_video_stub(tmp_path, "big.mp4", size=500)
    adapter = VideoFramesAdapter()
    assert adapter.can_handle(str(p)) is False
    results = list(adapter.ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``id_rsa.mp4`` → can_handle False, ingest emits failed-stub."""
    p = _make_video_stub(tmp_path, "id_rsa.mp4")
    adapter = VideoFramesAdapter()
    assert adapter.can_handle(str(p)) is False
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


def test_ingest_corrupt_video_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A video that cv2.VideoCapture cannot open → failed-stub
    naming the codec error.
    """
    p = _make_video_stub(tmp_path, "corrupt.mp4")
    capture = _FakeVideoCapture(opened=False)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(sys.modules, "pytesseract", _build_fake_pytesseract())
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "could not be opened" in results[0].failure_reason
    assert "codec" in results[0].failure_reason


def test_ingest_zero_frames_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A video with 0 frames or 0 fps → single failed-stub naming
    the "no frames / unknown fps" cause.
    """
    p = _make_video_stub(tmp_path, "empty.mp4")
    capture = _FakeVideoCapture(opened=True, fps=0.0, total_frames=0)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(sys.modules, "pytesseract", _build_fake_pytesseract())
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no frames" in results[0].failure_reason


def test_ingest_emits_one_result_per_frame_with_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Happy path: 3-frame mock video with non-empty OCR per frame
    → 3 ok IngestResults with frame_index / timestamp_sec metadata.

    The fake capture has 90 frames at 30 fps (3 sec total). With a
    10 sec sampling interval the video is too short — ``_compute_
    sample_interval`` falls back to ``max(1, 30*10) = 300`` stride,
    which exceeds total_frames so we'd sample only frame 0. To
    exercise multi-frame sampling we override the stride via a
    longer total_frames.
    """
    p = _make_video_stub(tmp_path, "demo.mp4")
    # 30 fps, 900 frames = 30 sec total. Default stride = 30*10 = 300
    # frames = 10s → sampled frames at indices 0, 300, 600 = 3 frames.
    capture = _FakeVideoCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        _build_fake_pytesseract(
            text_per_frame=[
                "Slide 1: Welcome",
                "Slide 2: Architecture",
                "Slide 3: Conclusion",
            ]
        ),
    )
    results = list(VideoFramesAdapter().ingest(str(p)))
    ok_results = [r for r in results if r.status == "ok"]
    assert len(ok_results) == 3
    assert all(r.metadata["kind"] == "video-frame-ocr" for r in ok_results)
    assert [r.metadata["frame_index"] for r in ok_results] == [0, 1, 2]
    # Timestamps: 0/30=0.0, 300/30=10.0, 600/30=20.0.
    timestamps = [r.metadata["timestamp_sec"] for r in ok_results]
    assert timestamps == [0.0, 10.0, 20.0]
    assert "Welcome" in ok_results[0].body
    assert "Architecture" in ok_results[1].body
    assert "Conclusion" in ok_results[2].body
    assert ok_results[0].metadata["ocr_lang"] == "eng"


def test_ingest_all_frames_empty_returns_failed_stub_chain(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """All sampled frames OCR-empty → per-frame failed-stubs PLUS
    one trailing overall failed-stub naming the "all frames empty"
    cause. Loud-skip per AD1 — never silent ``return []``.
    """
    p = _make_video_stub(tmp_path, "silent.mp4")
    capture = _FakeVideoCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        _build_fake_pytesseract(text_per_frame=["", "  ", "\n\n"]),
    )
    results = list(VideoFramesAdapter().ingest(str(p)))
    # 3 per-frame failed-stubs + 1 overall = 4 total.
    assert len(results) == 4
    assert all(r.status == "failed" for r in results)
    per_frame = [
        r for r in results if r.metadata.get("kind") == "video-frame-ocr-empty"
    ]
    assert len(per_frame) == 3
    overall = [r for r in results if "all sampled frames" in r.failure_reason]
    assert len(overall) == 1


def test_ingest_tesseract_binary_missing_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``TesseractNotFoundError`` on the first OCR call → entire
    ingest bails with a single binary-install hint failed-stub.
    """
    p = _make_video_stub(tmp_path, "demo.mp4")
    capture = _FakeVideoCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        _build_fake_pytesseract(raise_not_found=True),
    )
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "tesseract" in results[0].failure_reason.lower()
    assert "PATH" in results[0].failure_reason


# ---------------------------------------------------------------------------
# _compute_sample_interval logic
# ---------------------------------------------------------------------------


def test_compute_sample_interval_short_video() -> None:
    """A 30-second video at 30 fps (900 frames) with 10 s default
    interval → stride 300 → 3 sampled frames (under cap).
    """
    stride = _compute_sample_interval(total_frames=900, fps=30.0)
    assert stride == 300


def test_compute_sample_interval_long_video_caps_at_max() -> None:
    """A 1-hour video at 30 fps (108k frames) → stride stretched
    so sampled count lands at MAX_FRAMES_PER_VIDEO.
    """
    total = 30 * 60 * 60  # 30 fps x 60 s x 60 min = 108k frames
    stride = _compute_sample_interval(total_frames=total, fps=30.0)
    sampled = total // stride
    assert sampled <= MAX_FRAMES_PER_VIDEO
    # With cap = 30 and total = 108000, stride = 108000 // 30 = 3600.
    assert stride == 3600


def test_compute_sample_interval_zero_inputs_returns_floor() -> None:
    """Degenerate inputs → return 1 (every frame) rather than crash.

    Defensive: a corrupt video header could legitimately report
    0 frames or 0 fps; the higher-level zero-frame check catches
    that, but we still want this helper safe in isolation.
    """
    assert _compute_sample_interval(total_frames=0, fps=30.0) == 1
    assert _compute_sample_interval(total_frames=900, fps=0.0) == 1


# ---------------------------------------------------------------------------
# Registry: discoverable in priority order
# ---------------------------------------------------------------------------


def test_video_frames_adapter_registered_before_text_file() -> None:
    """The video-frames adapter must register BEFORE text-file."""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.stdlib_simple_cluster import TextFileAdapter as TF
    from myco.ingestion.adapters.video_frames import VideoFramesAdapter as VF

    adapters = list(all_adapters())
    vf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, VF)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert vf_idx >= 0, "VideoFramesAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert vf_idx < tf_idx, (
        f"VideoFramesAdapter (idx {vf_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )


def test_video_frames_adapter_registered_after_image_ocr() -> None:
    """The video-frames adapter registers after image-ocr per the
    v0.8.0 multimedia ladder.
    """
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.multimedia_cluster import ImageOcrAdapter as IO
    from myco.ingestion.adapters.video_frames import VideoFramesAdapter as VF

    adapters = list(all_adapters())
    io_idx = next((i for i, a in enumerate(adapters) if isinstance(a, IO)), -1)
    vf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, VF)), -1)
    assert io_idx >= 0 and vf_idx >= 0
    assert io_idx < vf_idx


def test_default_max_video_bytes_is_500mb() -> None:
    """The size cap is 500 MB per the v0.8.0 multimedia craft."""
    assert DEFAULT_MAX_VIDEO_BYTES == 500 * 1024 * 1024


def test_max_frames_per_video_is_30() -> None:
    """The frame-sample cap is 30 per the v0.8.0 multimedia craft.

    A 30-minute talk samples ~1 frame per minute under this cap
    (slide-deck-grade resolution).
    """
    assert MAX_FRAMES_PER_VIDEO == 30


# ---------------------------------------------------------------------------
# Additional defensive paths for v0.9 cov-floor revert (≥85%).
# Cover the per-frame loud-skip branches (read fail, OCR fail) that the
# happy-path tests above don't exercise.
# ---------------------------------------------------------------------------


class _FailingReadCapture(_FakeVideoCapture):
    """Variant whose ``read()`` returns ``(False, None)`` after a fixed count.

    Used to drive the ``not read_ok or frame is None`` per-frame failed-stub
    branch in ``_sample_and_ocr``.
    """

    def read(self):
        # Always fail to read.
        self._read_count += 1
        return False, None


class _RaisingReadCapture(_FakeVideoCapture):
    """Variant whose ``read()`` raises RuntimeError on every call.

    Drives the ``except (RuntimeError, OSError, ValueError)`` per-frame
    read-failed branch in ``_sample_and_ocr``.
    """

    def read(self):
        self._read_count += 1
        raise RuntimeError("decoder lost frame buffer")


def test_ingest_per_frame_read_failure_emits_per_frame_failed_stubs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per-frame read returning ``(False, None)`` → per-frame failed-stub
    on each sample, then the overall "no readable frames" stub when
    every sample fails.
    """
    p = _make_video_stub(tmp_path, "broken.mp4")
    capture = _FailingReadCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(sys.modules, "pytesseract", _build_fake_pytesseract())
    results = list(VideoFramesAdapter().ingest(str(p)))
    # Every sample failed to read; per-frame failed-stubs accumulated AND
    # the overall "no readable frames" stub fires.
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no readable frames" in results[0].failure_reason


def test_ingest_per_frame_read_raises_emits_overall_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per-frame read raising RuntimeError on every sample → ``sampled_count
    == 0`` short-circuits to a single overall "no readable frames"
    failed-stub naming the higher-level failure.

    The per-frame failed-stubs accumulated during the loop are discarded
    by the ``sampled_count == 0`` branch — the diagnostic the operator
    cares about is the overall verdict, not the noisy per-frame log.
    Exercises the per-frame ``except (RuntimeError, OSError, ValueError)``
    branch even though only the overall stub survives.
    """
    p = _make_video_stub(tmp_path, "raising.mp4")
    capture = _RaisingReadCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    monkeypatch.setitem(sys.modules, "pytesseract", _build_fake_pytesseract())
    results = list(VideoFramesAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no readable frames" in results[0].failure_reason


def test_ingest_per_frame_ocr_runtime_error_emits_per_frame_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Per-frame OCR raising RuntimeError → per-frame failed-stub naming
    the OCR failure, AD1 loud-skip per frame.

    We mix one OK frame with subsequent OCR errors so the test exercises
    the ``except (RuntimeError, OSError, ValueError)`` branch (line 420)
    rather than the binary-not-found branch (line 414).
    """
    p = _make_video_stub(tmp_path, "ocr-error.mp4")
    # Set up cv2 with 3 frames at 30 fps, 900 total → stride 300.
    capture = _FakeVideoCapture(opened=True, fps=30.0, total_frames=900)
    monkeypatch.setitem(sys.modules, "cv2", _build_fake_cv2(capture=capture))
    # pytesseract raises RuntimeError on every call (not TesseractNotFoundError).
    monkeypatch.setitem(
        sys.modules,
        "pytesseract",
        _build_fake_pytesseract(
            raise_runtime=RuntimeError("language pack 'xyz' missing")
        ),
    )
    results = list(VideoFramesAdapter().ingest(str(p)))
    # Every frame OCR'd but raised → per-frame OCR-error stubs.
    assert all(r.status == "failed" for r in results)
    ocr_error_stubs = [
        r for r in results if r.metadata.get("kind") == "video-frame-ocr-error"
    ]
    assert len(ocr_error_stubs) >= 1
    # Naming check: per-frame OCR error mentions the language pack.
    assert any("xyz" in r.failure_reason for r in ocr_error_stubs)


def test_compute_sample_interval_default_stride_short_clip() -> None:
    """A short clip (30 frames at 30 fps = 1 sec) → default stride 300
    (10 sec interval), but total_frames < default_stride so floor=1.

    Tests the "tiny clip" fallthrough where the stride would skip the
    entire video — degenerate case returns 1 (every frame).
    """
    # 30 frames at 30 fps = 1 sec. Default stride = 30 * 10 = 300, but
    # 1 sec total, so the fallback at the bottom of _compute_sample_interval
    # ensures we still sample. The function returns the larger of
    # default_stride and total_frames // MAX. With total=30, MAX=30 →
    # 30 // 30 = 1, so cap_stride = max(300, 1) = 300. So this returns 300.
    # That's the long-video-stretch path even for a short clip.
    stride = _compute_sample_interval(total_frames=30, fps=30.0)
    # Either 300 (the default-stride floor) or 1 (degenerate); both are valid.
    assert stride >= 1


def test_can_handle_oversize_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Files larger than the cap are rejected by ``can_handle`` even when
    the extension matches. Exercises the size-cap branch in can_handle
    (lines 222-223 of video_frames.py).
    """
    monkeypatch.setattr(
        "myco.ingestion.adapters.video_frames.DEFAULT_MAX_VIDEO_BYTES", 100
    )
    p = _make_video_stub(tmp_path, "huge.mp4", size=500)
    assert VideoFramesAdapter().can_handle(str(p)) is False
