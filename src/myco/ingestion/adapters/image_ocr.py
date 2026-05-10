"""Adapter for image files via pytesseract OCR.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬) for the **image-with-text
modality**: a screenshot, scanned document, or whiteboard photo
carries text the agent should be able to ingest. v0.7.10's gap
analysis flagged image OCR alongside audio and video as missing.

This is the v0.8.0 12th adapter (2nd of three multimedia adapters
gated behind the opt-in ``[multimedia]`` extras). One
:class:`IngestResult` per image — OCR yields a single text block
per image, so per-image granularity is the right grain (don't try
to segment per word; modern OCR returns line-broken paragraph
runs that downstream digestion handles fine).

Detection is extension-only:

* ``.png``, ``.jpg``, ``.jpeg``, ``.tiff``, ``.bmp``, ``.webp``
  are claimed.

Architecture — **import-on-demand**:

The Pillow + pytesseract pair is lighter than Whisper (no PyTorch),
but pytesseract still requires the system ``tesseract`` binary on
PATH. Two failure modes the operator must distinguish:

1. ``import pytesseract`` fails → ``[multimedia]`` extras not
   installed → install-extras failed-stub.
2. ``import pytesseract`` succeeds but ``tesseract`` binary not on
   PATH → ``pytesseract.pytesseract.TesseractNotFoundError`` at
   call time → "install tesseract binary" failed-stub.

Both paths emit a failed-stub naming the cause; the operator gets
concrete remediation guidance instead of a silent skip.

Security posture mirrors :mod:`text_file` and :mod:`audio`:

* **Credential-glob denial.** Reuses
  :func:`text_file._is_credential_file`. An attacker who renames
  ``id_rsa`` to ``id_rsa.png`` is refused.
* **Size cap.** Files over :data:`DEFAULT_MAX_IMAGE_BYTES` (50 MB)
  are rejected by ``can_handle``. PIL buffers decoded pixel data
  in memory, so a 5 GB attacker-planted PNG would OOM the decoder
  before OCR ever runs. 50 MB comfortably accommodates a 4K
  multi-page TIFF without exposing the OOM oracle.
* **Failed-stub on every former silent-skip path.** pytesseract
  missing, tesseract binary not on PATH, decode error, OCR
  returned empty — all produce a single failed-stub IngestResult.
  Never ``[]`` (AD1).
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .protocol import Adapter, IngestResult
from .text_file import _is_credential_file

#: Size ceiling for a single image file (50 MB). Larger than the
#: cross-adapter 10 MB cap because TIFFs/PNGs can legitimately
#: reach 30+ MB at print resolution; smaller than audio (100 MB)
#: because PIL's pixel-buffer expansion is roughly width*height*4
#: bytes — a 50 MB compressed PNG can decode to several hundred MB
#: in RAM, so we cap below the audio threshold.
DEFAULT_MAX_IMAGE_BYTES: int = 50 * 1024 * 1024

#: File extensions claimed by this adapter. Aligned with the formats
#: Pillow handles natively without extra plugins.
_IMAGE_EXTS: frozenset[str] = frozenset(
    {".png", ".jpg", ".jpeg", ".tiff", ".bmp", ".webp"}
)

#: Default OCR language. ``eng`` is the only language tesseract
#: ships in its default install; users wanting CJK / cyrillic /
#: arabic configs can pass a different ``ocr_lang`` via a substrate-
#: local plugin override (out of scope for v0.8.0; see the v0.7.10
#: examples-only IOU for the extension hook).
_DEFAULT_OCR_LANG: str = "eng"

#: Reason text fragment for missing pytesseract (the Python wrapper).
#: Pinned in tests so the operator-facing guidance stays stable.
_INSTALL_EXTRAS_HINT: str = (
    "myco[multimedia] not installed; run "
    "`pip install 'myco[multimedia]'` to enable image OCR."
)

#: Reason text fragment for missing tesseract binary on PATH. Distinct
#: from the install-extras hint because the remediation differs:
#: pytesseract is a Python pip package, but the underlying tesseract
#: binary is a system-level install (``apt-get install tesseract-ocr``,
#: ``brew install tesseract``, or the Windows installer).
_TESSERACT_BINARY_HINT: str = (
    "tesseract binary not on PATH; install via your platform's "
    "package manager (apt/brew/winget) for image OCR to work."
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
    keeps the per-failure call sites uniform and AD1-friendly.
    """
    return IngestResult(
        title=title,
        body="",
        source=source,
        status="failed",
        failure_reason=reason,
        metadata=metadata or {},
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

    Refuses files matched by
    :data:`text_file._CREDENTIAL_DENY_GLOBS` and files over
    :data:`DEFAULT_MAX_IMAGE_BYTES` (50 MB) at ``can_handle``.
    Returns a single failed-stub on every former silent-skip path
    (pytesseract not installed, tesseract binary not on PATH,
    decode error, OCR returned empty) per the v0.7.3 AD1-closure
    protocol.
    """

    @property
    def name(self) -> str:
        return "image-ocr"

    @property
    def extensions(self) -> frozenset[str]:
        return _IMAGE_EXTS

    def can_handle(self, target: str) -> bool:
        """Claim by extension only; never imports pytesseract.

        The lazy-import architecture means ``can_handle`` must work
        without the heavy deps. We claim by extension, then
        ``ingest`` either OCRs or emits the install-extras failed-
        stub. Routes the file to this adapter even on a default
        install so the operator gets clear remediation guidance.
        """
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
                    reason=(f"refused credential-bearing file by name: {p.name!r}"),
                )
            ]
        # Lazy-import PIL.Image and pytesseract inside ingest() so
        # module-level import stays stdlib-only on default installs.
        # Two distinct ImportError modes covered:
        # 1. ``pytesseract`` missing → install-extras hint.
        # 2. ``Pillow`` missing → install-extras hint (Pillow is
        #    bundled in the same extras row, so the same hint
        #    applies; the operator runs one install command).
        try:
            from PIL import Image
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
        # PIL.Image.open is lazy; size + format inspection forces the
        # header read so a corrupt image fails here rather than mid-
        # OCR. ``UnidentifiedImageError`` is a subclass of OSError on
        # modern Pillow; we catch the broader OSError to stay
        # compatible across versions.
        try:
            with Image.open(str(p)) as img:
                # Force the lazy load so format errors surface here.
                img.load()
                width, height = img.size
                # Convert to RGB before OCR — tesseract handles RGB
                # better than e.g. RGBA / palette modes, and the
                # conversion is cheap.
                rgb_img = img.convert("RGB")
        except OSError as exc:
            return [
                _failed_stub(
                    title=p.stem,
                    source=source,
                    reason=f"image decode failed: {exc}",
                )
            ]
        # Run OCR. ``TesseractNotFoundError`` fires when the binary
        # isn't on PATH; we map it to the binary-install hint so the
        # operator knows pip alone won't solve it.
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
            # Catch-all for tesseract subprocess failures (corrupt
            # image, unsupported language pack, malformed config).
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
