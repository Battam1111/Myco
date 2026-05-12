"""Multimedia ingestion adapter cluster (v0.8.8 merge).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters".

Merged home of two of the three v0.8.0 multimedia adapters that
previously lived in their own per-class files (``audio.py``,
``image_ocr.py``). The third multimedia adapter (``video_frames.py``,
505 LOC alone) stays a singleton because adding it would breach the
PA2 megafile cap. Cluster-merge follows the v0.8.8 substrate-wide
consolidation policy. Section markers ``# === <AdapterName> — ...``
preserve per-class review boundaries; git history holds the original
per-file state.

Adapters in this cluster:

* :class:`AudioAdapter` — ``.wav``/``.mp3``/``.flac``/``.m4a``/``.ogg``
  via OpenAI Whisper; one ``IngestResult`` per detected segment.
* :class:`ImageOcrAdapter` — ``.png``/``.jpg``/``.jpeg``/``.tiff``/
  ``.bmp``/``.webp`` via pytesseract; one ``IngestResult`` per image.

Both follow the v0.7.10 lazy-import architecture: module imports
stay stdlib-only so a default ``pip install myco`` install keeps the
adapter registry shape; the heavy deps (whisper / PyTorch /
pytesseract / Pillow) lazy-import inside ``ingest()``, returning a
single failed-stub on missing-dep paths per the v0.7.3 AD1 contract.

Security posture preserved verbatim:

* **Credential-glob denial.** Reuses
  :func:`stdlib_simple_cluster._is_credential_file`.
* **Size caps.** ``DEFAULT_MAX_AUDIO_BYTES`` = 100 MB,
  ``DEFAULT_MAX_IMAGE_BYTES`` = 50 MB (per-modality, larger than the
  cross-adapter 10 MB cap because lossy audio / multi-page TIFFs
  reach 30+ MB legitimately).
* **Failed-stub on every former silent-skip path** — pixel decode
  error, codec error, model load failure, OCR empty, tesseract not
  on PATH all produce a single failed-stub instead of an empty list.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .protocol import Adapter, IngestResult
from .stdlib_simple_cluster import _is_credential_file

# =========================================================================
# Shared module-level helpers
# =========================================================================


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

    Centralised so every failure path emits the identical shape; AD1
    watches for the empty-list-return anti-pattern in adapter code,
    and concentrating the stub construction here keeps the per-failure
    call sites uniform.
    """
    return IngestResult(
        title=title,
        body="",
        source=source,
        status="failed",
        failure_reason=reason,
        metadata=metadata or {},
    )


# =========================================================================
# === AudioAdapter — formerly audio.py (351 LOC)
# =========================================================================

#: Size ceiling for a single audio file (100 MB). Larger than the
#: cross-adapter 10 MB cap because lossy audio of meaningful length
#: easily exceeds 10 MB; smaller than video (500 MB) to keep the
#: decode + model-warm-up bounded.
DEFAULT_MAX_AUDIO_BYTES: int = 100 * 1024 * 1024

#: File extensions claimed by the audio adapter. Aligned with the
#: formats ``ffmpeg`` (Whisper's transitive decoder) handles natively.
_AUDIO_EXTS: frozenset[str] = frozenset({".wav", ".mp3", ".flac", ".m4a", ".ogg"})

#: Default Whisper model name. ``base`` is the right balance of
#: accuracy and download size (~140 MB) for first-time users.
_DEFAULT_WHISPER_MODEL: str = "base"

#: Default speaker label. Whisper does not perform speaker
#: diarization out of the box (that needs pyannote-audio).
_DEFAULT_SPEAKER_LABEL: str = "speaker"

#: Reason text fragment for missing whisper. The exact phrasing is
#: pinned in tests so the operator-facing guidance stays stable.
_AUDIO_INSTALL_HINT: str = (
    "myco[multimedia] not installed; run "
    "`pip install 'myco[multimedia]'` to enable audio ingestion."
)

# v0.8.8: legacy alias preserved for any test that imported the
# generic ``_INSTALL_EXTRAS_HINT`` symbol from audio.py.
_INSTALL_EXTRAS_HINT = _AUDIO_INSTALL_HINT


class AudioAdapter(Adapter):
    """Adapter for audio files via OpenAI Whisper.

    Emits one :class:`IngestResult` per Whisper-detected segment.
    Each result's ``metadata`` carries:

    * ``kind`` — always ``"audio-transcript-segment"``
    * ``start_sec`` — float; segment start time
    * ``end_sec`` — float; segment end time
    * ``speaker_label`` — string; default :data:`_DEFAULT_SPEAKER_LABEL`
      (Whisper itself does not diarize)
    * ``segment_index`` — 0-based ordinal within the file
    * ``source_file`` — POSIX-normalised absolute path

    Refuses files matched by credential globs and files over
    :data:`DEFAULT_MAX_AUDIO_BYTES` (100 MB) at ``can_handle``.
    Returns a single failed-stub on every former silent-skip path
    per the v0.7.3 AD1-closure protocol.
    """

    @property
    def name(self) -> str:
        return "audio"

    @property
    def extensions(self) -> frozenset[str]:
        return _AUDIO_EXTS

    def can_handle(self, target: str) -> bool:
        """Claim by extension only; never imports whisper."""
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in _AUDIO_EXTS:
            return False
        if _is_credential_file(p.name):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_AUDIO_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        try:
            size = p.stat().st_size
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem, source=str(p), reason=f"stat() failed: {exc}"
                )
            ]
        if size > DEFAULT_MAX_AUDIO_BYTES:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(
                        f"audio size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_AUDIO_BYTES} bytes"
                    ),
                )
            ]
        if _is_credential_file(p.name):
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=f"refused credential-bearing file by name: {p.name!r}",
                )
            ]
        # Lazy-import whisper inside ingest() so module import stays
        # stdlib-only on default installs.
        try:
            import whisper
        except ImportError:
            return [
                _failed_stub(title=p.stem, source=_posix(p), reason=_AUDIO_INSTALL_HINT)
            ]
        source = _posix(p)
        try:
            model = whisper.load_model(_DEFAULT_WHISPER_MODEL)
        except (OSError, RuntimeError, ValueError) as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"whisper model load failed ({_DEFAULT_WHISPER_MODEL!r}): {exc}",
                )
            ]
        try:
            transcription = model.transcribe(str(p))
        except (OSError, RuntimeError, ValueError) as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"whisper transcription failed: {exc}",
                )
            ]
        if not isinstance(transcription, dict):
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        f"whisper returned unexpected shape: "
                        f"{type(transcription).__name__}"
                    ),
                )
            ]
        segments = transcription.get("segments")
        if not isinstance(segments, list) or not segments:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        f"whisper produced no segments for {p.name!r} — "
                        "audio may be silent or below detection threshold"
                    ),
                )
            ]
        results: list[IngestResult] = []
        for seg_index, seg in enumerate(segments):
            if not isinstance(seg, dict):
                results.append(
                    _failed_stub(
                        title=f"{p.stem}-segment-{seg_index:04d}",
                        source=source,
                        reason=(
                            f"whisper segment {seg_index} malformed: "
                            f"{type(seg).__name__}"
                        ),
                        metadata={
                            "kind": "audio-transcript-segment",
                            "segment_index": seg_index,
                            "source_file": source,
                        },
                    )
                )
                continue
            text = str(seg.get("text") or "").strip()
            if not text:
                results.append(
                    _failed_stub(
                        title=f"{p.stem}-segment-{seg_index:04d}",
                        source=source,
                        reason=(
                            f"whisper segment {seg_index} produced "
                            f"empty transcript text"
                        ),
                        metadata={
                            "kind": "audio-transcript-segment-empty",
                            "segment_index": seg_index,
                            "source_file": source,
                        },
                    )
                )
                continue
            try:
                start_sec = float(seg.get("start", 0.0))
                end_sec = float(seg.get("end", 0.0))
            except (TypeError, ValueError):
                start_sec = 0.0
                end_sec = 0.0
            results.append(
                IngestResult(
                    title=f"{p.stem}-segment-{seg_index:04d}",
                    body=text,
                    tags=["audio", "audio-transcript", "transcript-segment"],
                    source=source,
                    metadata={
                        "kind": "audio-transcript-segment",
                        "start_sec": start_sec,
                        "end_sec": end_sec,
                        "speaker_label": _DEFAULT_SPEAKER_LABEL,
                        "segment_index": seg_index,
                        "source_file": source,
                    },
                )
            )
        return results


# =========================================================================
# === ImageOcrAdapter — formerly image_ocr.py (317 LOC)
# =========================================================================

#: Size ceiling for a single image file (50 MB). Larger than the
#: cross-adapter 10 MB cap because TIFFs/PNGs can legitimately reach
#: 30+ MB at print resolution; smaller than audio (100 MB) because
#: PIL's pixel-buffer expansion is roughly width*height*4 bytes.
DEFAULT_MAX_IMAGE_BYTES: int = 50 * 1024 * 1024

#: File extensions claimed by the image-OCR adapter.
_IMAGE_EXTS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
)

#: Default OCR language. ``eng`` is the only language tesseract ships
#: in its default install; users wanting CJK / cyrillic / arabic
#: configs can pass a different ``ocr_lang`` via a substrate-local
#: plugin override (out of scope for v0.8.0).
_DEFAULT_OCR_LANG: str = "eng"

#: Reason text fragment for missing pytesseract (the Python wrapper).
_IMAGE_INSTALL_HINT: str = (
    "myco[multimedia] not installed; run "
    "`pip install 'myco[multimedia]'` to enable image OCR."
)

#: Reason text fragment for missing tesseract binary on PATH.
_TESSERACT_BINARY_HINT: str = (
    "tesseract binary not on PATH; install via your platform's "
    "package manager (apt/brew/winget) for image OCR to work."
)


class ImageOcrAdapter(Adapter):
    """Adapter for image files via pytesseract OCR.

    Emits exactly one :class:`IngestResult` per image (or one
    failed-stub on any failure path). Each result's ``metadata``
    carries:

    * ``kind`` — always ``"image-ocr"``
    * ``image_size`` — 2-tuple ``(width, height)`` in pixels
    * ``ocr_lang`` — string; default :data:`_DEFAULT_OCR_LANG`
    * ``source_file`` — POSIX-normalised absolute path

    Refuses files matched by credential globs and files over
    :data:`DEFAULT_MAX_IMAGE_BYTES` (50 MB) at ``can_handle``.
    Returns a single failed-stub on every former silent-skip path.
    """

    @property
    def name(self) -> str:
        return "image-ocr"

    @property
    def extensions(self) -> frozenset[str]:
        return _IMAGE_EXTS

    def can_handle(self, target: str) -> bool:
        """Claim by extension only; never imports pytesseract."""
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in _IMAGE_EXTS:
            return False
        if _is_credential_file(p.name):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_IMAGE_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        try:
            size = p.stat().st_size
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem, source=str(p), reason=f"stat() failed: {exc}"
                )
            ]
        if size > DEFAULT_MAX_IMAGE_BYTES:
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=(
                        f"image size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_IMAGE_BYTES} bytes"
                    ),
                )
            ]
        if _is_credential_file(p.name):
            return [
                _failed_stub(
                    title=p.stem,
                    source=str(p),
                    reason=f"refused credential-bearing file by name: {p.name!r}",
                )
            ]
        # Lazy-import PIL.Image and pytesseract inside ingest() so
        # module-level import stays stdlib-only on default installs.
        try:
            from PIL import Image
        except ImportError:
            return [
                _failed_stub(title=p.stem, source=_posix(p), reason=_IMAGE_INSTALL_HINT)
            ]
        try:
            import pytesseract
        except ImportError:
            return [
                _failed_stub(title=p.stem, source=_posix(p), reason=_IMAGE_INSTALL_HINT)
            ]
        source = _posix(p)
        try:
            with Image.open(str(p)) as img:
                img.load()
                width, height = img.size
                rgb_img = img.convert("RGB")
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"image decode failed: {exc}",
                )
            ]
        try:
            text = pytesseract.image_to_string(rgb_img, lang=_DEFAULT_OCR_LANG)
        except pytesseract.pytesseract.TesseractNotFoundError:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=_TESSERACT_BINARY_HINT,
                )
            ]
        except (RuntimeError, OSError, ValueError) as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"OCR failed: {exc}",
                )
            ]
        text_stripped = (text or "").strip()
        if not text_stripped:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=(
                        "OCR yielded no text — image may be artwork, "
                        "blank, or low-contrast"
                    ),
                    metadata={
                        "kind": "image-ocr-empty",
                        "image_size": (width, height),
                        "ocr_lang": _DEFAULT_OCR_LANG,
                        "source_file": source,
                    },
                )
            ]
        return [
            IngestResult(
                title=p.stem,
                body=text_stripped,
                tags=["image", "ocr", "image-ocr"],
                source=source,
                metadata={
                    "kind": "image-ocr",
                    "image_size": (width, height),
                    "ocr_lang": _DEFAULT_OCR_LANG,
                    "source_file": source,
                },
            )
        ]
