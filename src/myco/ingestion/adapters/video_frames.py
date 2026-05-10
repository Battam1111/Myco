"""Adapter for video files via OpenCV frame sampling + per-frame OCR.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬) for the **video-with-text
modality**: a screen-recorded tutorial, demo capture, or slide
recording carries text on each visible slide. v0.7.10's gap
analysis flagged video alongside audio and image OCR as missing
modalities.

This is the v0.8.0 13th adapter (3rd of three multimedia adapters
gated behind the opt-in ``[multimedia]`` extras). Strategy:

1. Sample frames at 1 fps (or every Nth frame to keep total ≤
   :data:`MAX_FRAMES_PER_VIDEO` (30) — whichever is sparser).
2. Run pytesseract OCR on each sampled frame.
3. Emit one :class:`IngestResult` per frame whose OCR yielded
   non-empty text. Frames with empty OCR are logged as per-frame
   failed-stubs so the operator can see what was skipped (AD1).

Trade-offs explored across three rounds of craft:

* **Round 1 — every frame** is too dense (a 1-hour video at 30 fps
  = 108k frames; OCR cost is prohibitive and downstream notes
  flooding kills the substrate). Refuted.
* **Round 2 — first frame only** misses the actual content (slide
  decks change every minute or two). Refuted.
* **Round 3 — adaptive sampling** caps at 30 frames per file
  (slide-deck-grade resolution: a 30-minute talk samples ~1 frame
  per minute). 1 fps minimum so a short clip still gets dense
  coverage. Concluded; this is the implementation.

Detection is extension-only:

* ``.mp4``, ``.mov``, ``.avi``, ``.mkv``, ``.webm`` are claimed.

Architecture — **import-on-demand**:

OpenCV (``cv2``) is a ~80 MB transitive closure with system
binary deps; pytesseract requires the system tesseract binary on
PATH. Module-level imports stay stdlib-only so the adapter loads
on default installs. Two distinct ImportError modes:

1. ``import cv2`` fails → ``[multimedia]`` extras not installed.
2. ``import pytesseract`` fails → same hint (both in extras).

Both → install-extras failed-stub.

Security posture mirrors :mod:`audio` and :mod:`image_ocr`:

* **Credential-glob denial.** Reuses
  :func:`text_file._is_credential_file`.
* **Size cap.** Files over :data:`DEFAULT_MAX_VIDEO_BYTES` (500 MB)
  are rejected by ``can_handle``. Larger than audio/image because
  video is naturally larger; OpenCV streams frames so peak RAM
  doesn't track file size, but we still cap to bound the OCR
  loop's wall-clock cost.
* **Frame-level loud-skip.** Every empty-OCR frame produces a
  per-frame failed-stub IngestResult with a metadata-only marker
  rather than emitting the empty list for the whole batch. AD1-friendly.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .protocol import Adapter, IngestResult
from .text_file import _is_credential_file

#: Size ceiling for a single video file (500 MB). Larger than audio
#: (100 MB) and image (50 MB) caps because video is naturally larger
#: by orders of magnitude. OpenCV streams frames, so peak RAM doesn't
#: track file size — the cap exists to bound the OCR loop's wall-
#: clock cost on a hostile/giant video, not to prevent OOM.
DEFAULT_MAX_VIDEO_BYTES: int = 500 * 1024 * 1024

#: File extensions claimed by this adapter. Aligned with the formats
#: OpenCV's VideoCapture handles natively (depends on the underlying
#: ffmpeg / GStreamer build, but these five are universal).
_VIDEO_EXTS: frozenset[str] = frozenset({".mp4", ".mov", ".avi", ".mkv", ".webm"})

#: Maximum frames OCR'd per video. A 30-minute tutorial sampled at
#: 1 fps would produce 1800 frames; 30 keeps the per-file ingest
#: bounded and matches slide-deck cadence (a slide change every
#: ~1 minute on a 30-minute deck).
MAX_FRAMES_PER_VIDEO: int = 30

#: Target sampling interval (seconds) when the video is short enough
#: that ``MAX_FRAMES_PER_VIDEO`` isn't the binding constraint. A 5-
#: minute clip at 10 s spacing produces 30 frames — exactly at the
#: cap. Longer videos increase the spacing to stay at the cap.
DEFAULT_FRAME_INTERVAL_SEC: float = 10.0

#: Default OCR language (mirrors :mod:`image_ocr`). Pinned for the
#: same reason: tesseract's default install ships only ``eng``.
_DEFAULT_OCR_LANG: str = "eng"

#: Reason text fragment for missing extras (cv2 or pytesseract).
#: Pinned in tests so the operator-facing guidance stays stable.
_INSTALL_EXTRAS_HINT: str = (
    "myco[multimedia] not installed; run "
    "`pip install 'myco[multimedia]'` to enable video frame OCR."
)

#: Reason text fragment for missing tesseract binary on PATH.
#: Distinct from the install-extras hint because the remediation is
#: a system-level package, not pip.
_TESSERACT_BINARY_HINT: str = (
    "tesseract binary not on PATH; install via your platform's "
    "package manager (apt/brew/winget) for video frame OCR to work."
)


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


def _failed_stub(
    *,
    title: str,
    source: str,
    reason: str,
    metadata: dict[str, Any] | None = None,
) -> IngestResult:
    """Construct a v0.7.3 AD1-closure failed-stub IngestResult.

    Centralised so every failure path emits the identical shape;
    keeps per-failure call sites uniform and AD1-friendly.
    """
    return IngestResult(
        title=title,
        body="",
        source=source,
        status="failed",
        failure_reason=reason,
        metadata=metadata or {},
    )


def _compute_sample_interval(
    *,
    total_frames: int,
    fps: float,
) -> int:
    """Return the per-frame stride (in source frames) so the sampled
    count stays at or below :data:`MAX_FRAMES_PER_VIDEO`.

    Two regimes:

    1. **Short video** — ``total_frames / (fps * DEFAULT_FRAME_INTERVAL_SEC)
       ≤ MAX_FRAMES_PER_VIDEO``. Sample every
       ``fps * DEFAULT_FRAME_INTERVAL_SEC`` frames (one frame per
       :data:`DEFAULT_FRAME_INTERVAL_SEC` seconds).
    2. **Long video** — sampling at the default interval would
       exceed the cap. Stretch the interval so the sampled count
       lands exactly at :data:`MAX_FRAMES_PER_VIDEO`.

    Returns ``1`` (every frame) as a degenerate floor — covers the
    "tiny clip with very few total frames" case where any larger
    stride would skip the entire video.
    """
    if total_frames <= 0 or fps <= 0:
        return 1
    default_stride = max(1, round(fps * DEFAULT_FRAME_INTERVAL_SEC))
    sampled_at_default = max(1, total_frames // default_stride)
    if sampled_at_default <= MAX_FRAMES_PER_VIDEO:
        return default_stride
    # Long video: stretch the stride so we get exactly the cap.
    cap_stride = max(default_stride, total_frames // MAX_FRAMES_PER_VIDEO)
    return cap_stride


class VideoFramesAdapter(Adapter):
    """Adapter for video files via OpenCV frame sampling + OCR.

    Emits one :class:`IngestResult` per sampled frame with non-empty
    OCR text. Each result's ``metadata`` carries:

    * ``kind`` — ``"video-frame-ocr"`` (or ``"video-frame-ocr-empty"``
      / ``"video-frame-ocr-error"`` for per-frame failed-stubs)
    * ``frame_index`` — 0-based ordinal of the sampled frame within
      the file (NOT the source frame number; this is the sampled-
      sequence position)
    * ``timestamp_sec`` — wall-clock position of the frame in seconds
    * ``source_file`` — POSIX-normalised absolute path
    * ``ocr_lang`` — string; default :data:`_DEFAULT_OCR_LANG`

    Refuses files matched by
    :data:`text_file._CREDENTIAL_DENY_GLOBS` and files over
    :data:`DEFAULT_MAX_VIDEO_BYTES` (500 MB). Returns a single
    failed-stub on every former silent-skip path (cv2 not installed,
    pytesseract not installed, video can't be opened, all frames
    OCR-empty) per the v0.7.3 AD1-closure protocol.
    """

    @property
    def name(self) -> str:
        return "video-frames"

    @property
    def extensions(self) -> frozenset[str]:
        return _VIDEO_EXTS

    def can_handle(self, target: str) -> bool:
        """Claim by extension only; never imports cv2 or pytesseract.

        Lazy-import architecture: claim by extension, then ``ingest``
        either OCRs frames or emits the install-extras failed-stub.
        """
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in _VIDEO_EXTS:
            return False
        if _is_credential_file(p.name):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_VIDEO_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check size cap and credential name at
        # ingest. ``can_handle`` may be bypassed by a third-party
        # orchestrator or test fixture calling ``ingest`` directly.
        try:
            size = p.stat().st_size
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=f"stat() failed: {exc}",
                )
            ]
        if size > DEFAULT_MAX_VIDEO_BYTES:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(
                        f"video size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_VIDEO_BYTES} bytes"
                    ),
                )
            ]
        if _is_credential_file(p.name):
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(f"refused credential-bearing file by name: {p.name!r}"),
                )
            ]
        # Lazy-import cv2 and pytesseract inside ingest() so module-
        # level import stays stdlib-only on default installs.
        try:
            import cv2
        except ImportError:
            return [
                _failed_stub(
                    title=p.stem,
                    source=_posix(p),
                    reason=_INSTALL_EXTRAS_HINT,
                )
            ]
        try:
            import pytesseract
        except ImportError:
            return [
                _failed_stub(
                    title=p.stem,
                    source=_posix(p),
                    reason=_INSTALL_EXTRAS_HINT,
                )
            ]
        source = _posix(p)
        # OpenCV's VideoCapture is permissive about non-existent /
        # corrupt files — it returns an opened-but-invalid handle
        # rather than raising. ``isOpened()`` is the right gate.
        cap = cv2.VideoCapture(str(p))
        try:
            if not cap.isOpened():
                return [
                    _failed_stub(
                        title=p.stem,
                        source=source,
                        reason=(
                            f"video could not be opened (codec error or "
                            f"unsupported format): {p.name!r}"
                        ),
                    )
                ]
            try:
                fps = float(cap.get(cv2.CAP_PROP_FPS) or 0.0)
                total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
            except (ValueError, TypeError, AttributeError):
                fps, total_frames = 0.0, 0
            if total_frames <= 0 or fps <= 0:
                return [
                    _failed_stub(
                        title=p.stem,
                        source=source,
                        reason=(
                            f"video has no frames or unknown fps "
                            f"(fps={fps}, total_frames={total_frames}): "
                            f"{p.name!r}"
                        ),
                    )
                ]
            stride = _compute_sample_interval(total_frames=total_frames, fps=fps)
            results = self._sample_and_ocr(
                cap=cap,
                cv2_mod=cv2,
                pytesseract_mod=pytesseract,
                stride=stride,
                fps=fps,
                total_frames=total_frames,
                source=source,
                stem=p.stem,
                name=p.name,
            )
            return results
        finally:
            try:
                cap.release()
            except Exception:  # pragma: no cover — best-effort release
                pass

    # ---- internal helpers --------------------------------------------------

    def _sample_and_ocr(
        self,
        *,
        cap: Any,
        cv2_mod: Any,
        pytesseract_mod: Any,
        stride: int,
        fps: float,
        total_frames: int,
        source: str,
        stem: str,
        name: str,
    ) -> list[IngestResult]:
        """Iterate sampled frames, OCR each, build the result list.

        Returns a non-empty list:

        * ≥ 1 ok IngestResult per frame with non-empty OCR text.
        * Per-frame failed-stub for frames whose OCR yielded empty
          text or whose OCR call raised (loud per-frame skip).
        * Single overall failed-stub if every sampled frame produced
          empty text (the AD1 "all frames empty" branch).

        Per the AD1 protocol, never returns ``[]``: the all-empty
        branch builds a one-entry list with the overall failed-stub.
        """
        results: list[IngestResult] = []
        sampled_count = 0
        any_ok = False
        had_tesseract_binary_error = False
        for sample_idx in range(MAX_FRAMES_PER_VIDEO):
            source_frame = sample_idx * stride
            if source_frame >= total_frames:
                break
            try:
                cap.set(cv2_mod.CAP_PROP_POS_FRAMES, source_frame)
                read_ok, frame = cap.read()
            except (RuntimeError, OSError, ValueError) as exc:
                results.append(
                    _failed_stub(
                        title=f"{stem}-frame-{sample_idx:04d}",
                        source=source,
                        reason=(f"video frame {sample_idx} read failed: {exc}"),
                        metadata={
                            "kind": "video-frame-ocr-error",
                            "frame_index": sample_idx,
                            "source_file": source,
                        },
                    )
                )
                continue
            if not read_ok or frame is None:
                results.append(
                    _failed_stub(
                        title=f"{stem}-frame-{sample_idx:04d}",
                        source=source,
                        reason=(
                            f"video frame {sample_idx} could not be "
                            f"decoded (frame {source_frame} of {total_frames})"
                        ),
                        metadata={
                            "kind": "video-frame-ocr-error",
                            "frame_index": sample_idx,
                            "source_file": source,
                        },
                    )
                )
                continue
            timestamp_sec = source_frame / fps if fps > 0 else 0.0
            sampled_count += 1
            try:
                # OpenCV frames are BGR ndarrays; pytesseract.image_to_string
                # accepts a numpy array directly via PIL conversion under
                # the hood. The conversion is implicit when we pass the
                # array; pytesseract handles BGR→RGB internally for the
                # OCR pipeline.
                text = pytesseract_mod.image_to_string(frame, lang=_DEFAULT_OCR_LANG)
            except pytesseract_mod.pytesseract.TesseractNotFoundError:
                # Bail the whole loop: tesseract binary missing means
                # every subsequent frame would fail identically. Emit
                # a single failed-stub naming the binary remediation.
                had_tesseract_binary_error = True
                break
            except (RuntimeError, OSError, ValueError) as exc:
                results.append(
                    _failed_stub(
                        title=f"{stem}-frame-{sample_idx:04d}",
                        source=source,
                        reason=(f"video frame {sample_idx} OCR failed: {exc}"),
                        metadata={
                            "kind": "video-frame-ocr-error",
                            "frame_index": sample_idx,
                            "source_file": source,
                            "timestamp_sec": timestamp_sec,
                        },
                    )
                )
                continue
            text_stripped = (text or "").strip()
            if not text_stripped:
                results.append(
                    _failed_stub(
                        title=f"{stem}-frame-{sample_idx:04d}",
                        source=source,
                        reason=(f"video frame {sample_idx} produced empty OCR text"),
                        metadata={
                            "kind": "video-frame-ocr-empty",
                            "frame_index": sample_idx,
                            "source_file": source,
                            "timestamp_sec": timestamp_sec,
                        },
                    )
                )
                continue
            any_ok = True
            results.append(
                IngestResult(
                    title=f"{stem}-frame-{sample_idx:04d}",
                    body=text_stripped,
                    tags=["video", "video-frame", "ocr"],
                    source=source,
                    metadata={
                        "kind": "video-frame-ocr",
                        "frame_index": sample_idx,
                        "timestamp_sec": timestamp_sec,
                        "ocr_lang": _DEFAULT_OCR_LANG,
                        "source_file": source,
                    },
                )
            )
        if had_tesseract_binary_error:
            return [
                _failed_stub(
                    title=stem,
                    source=source,
                    reason=_TESSERACT_BINARY_HINT,
                )
            ]
        if sampled_count == 0:
            # No frames were even read — every iteration broke out.
            # The per-frame stubs above cover the diagnostic; we add
            # an overall stub explaining the higher-level failure.
            return [
                _failed_stub(
                    title=stem,
                    source=source,
                    reason=(
                        f"video {name!r} produced no readable frames "
                        f"(see per-frame failed-stubs for details)"
                    ),
                )
            ]
        if not any_ok:
            # Frames were read but every OCR returned empty. Emit the
            # overall "all frames OCR-empty" stub on top of the per-
            # frame stubs already in ``results`` so the operator sees
            # both the global verdict and the per-frame trail.
            results.append(
                _failed_stub(
                    title=stem,
                    source=source,
                    reason=(
                        f"video {name!r}: all sampled frames produced "
                        f"empty OCR text — video may be silent/animated "
                        f"or text contrast too low"
                    ),
                )
            )
        return results
