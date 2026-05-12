"""Tests for the image-OCR adapter (v0.8.0 multimedia extras, 2 of 3).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) for the image-with-text modality.

These tests pin the v0.8.0 contract for the 12th adapter:

* ``can_handle`` — claims the 6 canonical extensions (.png, .jpg,
  .jpeg, .tiff, .bmp, .webp) by suffix only; rejects everything
  else, including credential-glob filenames and oversize files.
* ``ingest`` — emits one IngestResult per image when the extras +
  tesseract binary are both available, OR a single failed-stub
  naming the install hint when either is missing.
* **Two distinct ImportError modes**:
  - ``import pytesseract`` fails → install-extras hint.
  - ``import pytesseract`` succeeds but ``tesseract`` binary not on
    PATH → ``TesseractNotFoundError`` at call time → binary hint.

All happy-path tests use mocks (no real tesseract binary needed).
PIL is a Pillow transitive dep already in the dev environment, so
we use real PIL to construct fixture images and mock only the
pytesseract layer. CI machines without tesseract installed get
the failed-stub branch covered explicitly.
"""

from __future__ import annotations

import sys
import types
from pathlib import Path

import pytest

from myco.ingestion.adapters.multimedia_cluster import (
    DEFAULT_MAX_IMAGE_BYTES,
    ImageOcrAdapter,
)

# v0.8.2 hotfix: CI machines don't ship Pillow; skip the whole test
# module when PIL is unavailable so the multimedia opt-in extras
# pattern (default install lean) is honored. Local dev machines that
# have ``pip install 'myco[multimedia]'`` still run all tests.
PIL = pytest.importorskip(
    "PIL",
    reason=(
        "test_image_ocr.py uses real PIL to construct fixture images; "
        "skip on CI environments without 'myco[multimedia]' extras "
        "installed. The adapter's failed-stub-when-dep-missing path "
        "is verified separately at runtime via mock-import tests."
    ),
)

pytestmark = pytest.mark.multimedia


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


def _make_image_stub(tmp_path: Path, name: str, size: int = 1024) -> Path:
    """Create a stub file with the given name and approximate size.

    The file's bytes don't matter for ``can_handle`` (only the path /
    extension / stat is inspected). For OCR-path tests we use a real
    PIL image (see :func:`_make_real_image`).
    """
    p = tmp_path / name
    p.write_bytes(b"\x00" * size)
    return p


def _make_real_image(tmp_path: Path, name: str = "real.png") -> Path:
    """Create a real PIL image so the decoder branch can exercise.

    PIL is a Pillow transitive dep already in the dev environment; we
    use a tiny 4x4 RGB image so encoding/decoding is fast and
    deterministic. Returns the file path.
    """
    from PIL import Image

    p = tmp_path / name
    img = Image.new("RGB", (4, 4), color=(255, 255, 255))
    img.save(str(p))
    return p


def _build_fake_pytesseract(
    *,
    text: str | None = None,
    raise_not_found: bool = False,
    raise_runtime: Exception | None = None,
) -> types.ModuleType:
    """Build a fake pytesseract module shaped like the real one.

    The real module exposes ``image_to_string`` at the top level and
    ``pytesseract.TesseractNotFoundError`` as a nested attribute. We
    replicate both shapes so the adapter's exception-handler line
    ``except pytesseract.pytesseract.TesseractNotFoundError`` still
    binds correctly.
    """
    fake = types.ModuleType("pytesseract")
    nested = types.ModuleType("pytesseract.pytesseract")

    class _TesseractNotFoundError(Exception):
        pass

    nested.TesseractNotFoundError = _TesseractNotFoundError  # type: ignore[attr-defined]
    fake.pytesseract = nested  # type: ignore[attr-defined]

    def _image_to_string(_img, lang="eng"):
        if raise_not_found:
            raise _TesseractNotFoundError("tesseract not found")
        if raise_runtime is not None:
            raise raise_runtime
        return text or ""

    fake.image_to_string = _image_to_string  # type: ignore[attr-defined]
    return fake


# ---------------------------------------------------------------------------
# can_handle: extension claim, credential / size denials
# ---------------------------------------------------------------------------


def test_can_handle_png_extension(tmp_path: Path) -> None:
    """``.png`` files are claimed by the image-OCR adapter."""
    p = _make_image_stub(tmp_path, "screenshot.png")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_jpg_extension(tmp_path: Path) -> None:
    """``.jpg`` files are claimed."""
    p = _make_image_stub(tmp_path, "photo.jpg")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_jpeg_extension(tmp_path: Path) -> None:
    """``.jpeg`` (long-form) files are claimed."""
    p = _make_image_stub(tmp_path, "photo.jpeg")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_tiff_extension(tmp_path: Path) -> None:
    """``.tiff`` files are claimed (scanner output)."""
    p = _make_image_stub(tmp_path, "scan.tiff")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_bmp_extension(tmp_path: Path) -> None:
    """``.bmp`` files are claimed (Windows screenshot format)."""
    p = _make_image_stub(tmp_path, "win.bmp")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_webp_extension(tmp_path: Path) -> None:
    """``.webp`` files are claimed (modern web image format)."""
    p = _make_image_stub(tmp_path, "modern.webp")
    assert ImageOcrAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_non_image(tmp_path: Path) -> None:
    """Non-image extensions must NOT be claimed."""
    adapter = ImageOcrAdapter()
    for name in ("plain.txt", "doc.md", "audio.mp3", "video.mp4", "noext"):
        p = tmp_path / name
        p.write_bytes(b"hello")
        assert adapter.can_handle(str(p)) is False, f"unexpected claim: {name!r}"
    # A directory with an image-looking name must also be rejected.
    d = tmp_path / "fake.png"
    d.mkdir()
    assert adapter.can_handle(str(d)) is False


def test_can_handle_rejects_credential_filename(tmp_path: Path) -> None:
    """Credential-glob names refuse claim regardless of image extension.

    Mirrors text_file's defense: ``id_rsa.png`` cannot exfiltrate.
    """
    p = _make_image_stub(tmp_path, "id_rsa.png")
    assert ImageOcrAdapter().can_handle(str(p)) is False


# ---------------------------------------------------------------------------
# ingest: missing-dep paths (the key CI tests)
# ---------------------------------------------------------------------------


def test_ingest_returns_failed_stub_when_dep_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """**THIS IS THE KEY TEST**: ``import pytesseract`` raising
    ImportError must produce a single failed-stub naming the
    install-extras hint.

    CI machines do NOT have pytesseract installed by default; without
    this contract the adapter would crash on every image. We mock by
    stashing ``None`` into ``sys.modules['pytesseract']``.
    """
    p = _make_real_image(tmp_path, "screenshot.png")
    # PIL is transitively present (Pillow), so the PIL ImportError
    # branch needs a separate test. Here we exercise the pytesseract
    # branch.
    monkeypatch.setitem(sys.modules, "pytesseract", None)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "myco[multimedia]" in results[0].failure_reason
    assert "pip install" in results[0].failure_reason


def test_ingest_returns_failed_stub_when_pil_missing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When ``from PIL import Image`` fails, the adapter must emit
    the install-extras hint just like the pytesseract branch.

    This proves the second ImportError mode — the ``Pillow`` half of
    the multimedia extras row — also produces the install hint
    (single ``pip install 'myco[multimedia]'`` fixes both gaps).
    """
    p = _make_image_stub(tmp_path, "screenshot.png")
    # Force PIL.Image import to fail. Setting both ``PIL`` and
    # ``PIL.Image`` to None covers ``from PIL import Image`` (which
    # imports PIL first, then looks up Image) and also ``import
    # PIL.Image`` paths.
    monkeypatch.setitem(sys.modules, "PIL", None)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "myco[multimedia]" in results[0].failure_reason


def test_ingest_oversize_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A file over the 50 MB cap → single failed-stub naming the cap.

    The size-cap branch fires before the lazy import so we don't
    need to mock the deps.
    """
    monkeypatch.setattr(
        "myco.ingestion.adapters.multimedia_cluster.DEFAULT_MAX_IMAGE_BYTES", 100
    )
    p = _make_image_stub(tmp_path, "big.png", size=500)
    adapter = ImageOcrAdapter()
    assert adapter.can_handle(str(p)) is False
    results = list(adapter.ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``id_rsa.png`` → can_handle False, ingest emits failed-stub."""
    p = _make_image_stub(tmp_path, "id_rsa.png")
    adapter = ImageOcrAdapter()
    assert adapter.can_handle(str(p)) is False
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


def test_ingest_corrupt_image_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A non-image file with ``.png`` extension → single failed-stub
    when PIL fails to decode it.
    """
    # Write garbage bytes that don't form a valid PNG.
    p = tmp_path / "fake.png"
    p.write_bytes(b"this is not a real PNG file" * 32)
    # Mock pytesseract in case the test environment lacks it; the
    # decode-error branch fires before pytesseract.image_to_string,
    # but the import still happens, so we provide a fake to keep
    # the test deterministic.
    fake = _build_fake_pytesseract(text="ignored")
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "decode failed" in results[0].failure_reason


def test_ingest_tesseract_binary_missing_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``TesseractNotFoundError`` at OCR call time → binary-install
    hint failed-stub (distinct from the install-extras hint).
    """
    p = _make_real_image(tmp_path, "screenshot.png")
    fake = _build_fake_pytesseract(raise_not_found=True)
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "tesseract" in results[0].failure_reason.lower()
    assert "PATH" in results[0].failure_reason


def test_ingest_emits_one_result_per_image(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Happy path with a fake pytesseract: one IngestResult per image
    with the expected metadata shape.
    """
    p = _make_real_image(tmp_path, "screenshot.png")
    fake = _build_fake_pytesseract(text="Hello World\nLine 2\n")
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].metadata["kind"] == "image-ocr"
    assert results[0].metadata["ocr_lang"] == "eng"
    assert results[0].metadata["image_size"] == (4, 4)
    assert "Hello World" in results[0].body
    assert "Line 2" in results[0].body
    assert results[0].metadata["source_file"].endswith("screenshot.png")
    assert "image" in results[0].tags
    assert "ocr" in results[0].tags


def test_ingest_empty_ocr_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """OCR returning an empty/whitespace string → single failed-stub
    naming the artwork/blank/low-contrast cause.

    Pinned exact phrasing matches the brief: "OCR yielded no text —
    image may be artwork, blank, or low-contrast".
    """
    p = _make_real_image(tmp_path, "blank.png")
    fake = _build_fake_pytesseract(text="   \n  \n")  # whitespace only
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no text" in results[0].failure_reason
    assert "artwork" in results[0].failure_reason
    assert results[0].metadata["kind"] == "image-ocr-empty"


def test_ingest_ocr_runtime_error_returns_failed_stub(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A pytesseract subprocess RuntimeError → failed-stub naming
    the OCR failure (catch-all for unexpected tesseract issues).
    """
    p = _make_real_image(tmp_path, "weird.png")
    fake = _build_fake_pytesseract(
        raise_runtime=RuntimeError("language pack 'xyz' not found")
    )
    monkeypatch.setitem(sys.modules, "pytesseract", fake)
    results = list(ImageOcrAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "OCR failed" in results[0].failure_reason
    assert "xyz" in results[0].failure_reason


# ---------------------------------------------------------------------------
# Registry: discoverable in priority order
# ---------------------------------------------------------------------------


def test_image_ocr_adapter_registered_before_text_file() -> None:
    """The image-OCR adapter must register BEFORE text-file."""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.multimedia_cluster import ImageOcrAdapter as IO
    from myco.ingestion.adapters.stdlib_simple_cluster import TextFileAdapter as TF

    adapters = list(all_adapters())
    io_idx = next((i for i, a in enumerate(adapters) if isinstance(a, IO)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert io_idx >= 0, "ImageOcrAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert io_idx < tf_idx, (
        f"ImageOcrAdapter (idx {io_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )


def test_image_ocr_adapter_registered_after_audio() -> None:
    """The image-OCR adapter registers after audio per the v0.8.0
    multimedia ladder. Documented in the registry.
    """
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.multimedia_cluster import (
        AudioAdapter as AA,
    )
    from myco.ingestion.adapters.multimedia_cluster import (
        ImageOcrAdapter as IO,
    )

    adapters = list(all_adapters())
    aa_idx = next((i for i, a in enumerate(adapters) if isinstance(a, AA)), -1)
    io_idx = next((i for i, a in enumerate(adapters) if isinstance(a, IO)), -1)
    assert aa_idx >= 0 and io_idx >= 0
    assert aa_idx < io_idx


def test_default_max_image_bytes_is_50mb() -> None:
    """The size cap is 50 MB per the v0.8.0 multimedia craft."""
    assert DEFAULT_MAX_IMAGE_BYTES == 50 * 1024 * 1024
