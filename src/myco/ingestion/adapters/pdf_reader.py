"""Adapter for local PDF files.

Requires ``pypdf`` (part of the ``[adapters]`` extras).

v0.5.8: adopts the same safety envelope as the text adapter.
* Size cap (``DEFAULT_MAX_INGEST_BYTES`` = 10 MB) — a multi-GB PDF
  can OOM pypdf before any extraction happens, so ``can_handle``
  rejects it up front.
* Source path normalised to POSIX separators (Lens 10 P1-C) so
  downstream graph/traverse machinery stays cross-platform
  consistent.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pypdf import PdfReader as _PR  # ImportError if not installed

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

#: Size ceiling for a single PDF to pass through this adapter (10 MB).
#: Mirrors :data:`myco.ingestion.adapters.text_file.DEFAULT_MAX_INGEST_BYTES`.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES


class PdfReader(Adapter):
    """Adapter for ``.pdf`` files via the ``pypdf`` library.

    Extracts per-page text and concatenates with page markers
    (``[Page N]``). Refuses files over
    :data:`DEFAULT_MAX_INGEST_BYTES` (10 MB) at ``can_handle``;
    pypdf buffers pages in memory so oversized PDFs can OOM the
    reader before extraction finishes.
    """

    @property
    def name(self) -> str:
        return "pdf"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".pdf"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not (p.is_file() and p.suffix.lower() == ".pdf"):
            return False
        # v0.5.8 P1-05 (Lens 16): reject outsized PDFs up front.
        # pypdf buffers page content in memory; a 5 GB attacker-planted
        # PDF would exhaust RAM before extraction finished.
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check at ingest; ``can_handle`` may be
        # bypassed by a direct-invocation path.
        try:
            size = p.stat().st_size
        except OSError:
            return []
        if size > DEFAULT_MAX_INGEST_BYTES:
            return []
        reader = _PR(str(p))
        pages = [page.extract_text() or "" for page in reader.pages]
        body = "\n\n---\n\n".join(
            f"[Page {i + 1}]\n{text}" for i, text in enumerate(pages) if text.strip()
        )
        source = str(p.resolve()).replace("\\", "/")
        return [
            IngestResult(
                title=p.stem,
                body=body or "(no extractable text)",
                tags=["pdf", "file"],
                source=source,
                metadata={
                    "path": str(p),
                    "page_count": len(reader.pages),
                    "size_bytes": size,
                },
            )
        ]
