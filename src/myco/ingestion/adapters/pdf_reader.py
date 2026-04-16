"""Adapter for local PDF files.

Requires ``pypdf`` (part of the ``[adapters]`` extras).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .protocol import Adapter, IngestResult

from pypdf import PdfReader as _PR  # ImportError if not installed


class PdfReader(Adapter):
    @property
    def name(self) -> str:
        return "pdf"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".pdf"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        return p.is_file() and p.suffix.lower() == ".pdf"

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        reader = _PR(str(p))
        pages = [page.extract_text() or "" for page in reader.pages]
        body = "\n\n---\n\n".join(
            f"[Page {i+1}]\n{text}" for i, text in enumerate(pages) if text.strip()
        )
        return [IngestResult(
            title=p.stem,
            body=body or "(no extractable text)",
            tags=["pdf", "file"],
            source=str(p.resolve()),
            metadata={
                "path": str(p),
                "page_count": len(reader.pages),
            },
        )]
