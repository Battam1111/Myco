"""Adapter for local HTML files.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters".

Requires ``beautifulsoup4`` (part of the ``[adapters]`` extras).

v0.5.8: size cap + POSIX source normalization. See ``pdf_reader``
and ``text_file`` for the rationale — a 1 GB offline HTML dump
from a web crawl would otherwise OOM BeautifulSoup's tree.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from bs4 import BeautifulSoup  # ImportError if not installed

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

#: Size ceiling for a single HTML file (10 MB).
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES


class HtmlReader(Adapter):
    """Adapter for ``.html`` / ``.htm`` files using BeautifulSoup.

    Extracts text via ``soup.get_text``, stripping ``<script>``,
    ``<style>``, ``<nav>``, ``<header>``, ``<footer>`` first. Refuses
    files over :data:`DEFAULT_MAX_INGEST_BYTES` (10 MB) at
    ``can_handle`` so oversized web dumps can't OOM BeautifulSoup.
    """

    @property
    def name(self) -> str:
        return "html"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".html", ".htm"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not (p.is_file() and p.suffix.lower() in (".html", ".htm")):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        try:
            size = p.stat().st_size
        except OSError:
            return []
        if size > DEFAULT_MAX_INGEST_BYTES:
            return []
        raw = p.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else p.stem
        body = soup.get_text(separator="\n", strip=True)
        source = str(p.resolve()).replace("\\", "/")
        return [
            IngestResult(
                title=title[:120],
                body=body,
                tags=["html", "file"],
                source=source,
                metadata={"path": str(p), "size_bytes": size},
            )
        ]
