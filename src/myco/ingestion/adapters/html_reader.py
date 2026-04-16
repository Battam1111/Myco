"""Adapter for local HTML files.

Requires ``beautifulsoup4`` (part of the ``[adapters]`` extras).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .protocol import Adapter, IngestResult

from bs4 import BeautifulSoup  # ImportError if not installed


class HtmlReader(Adapter):
    @property
    def name(self) -> str:
        return "html"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".html", ".htm"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        return p.is_file() and p.suffix.lower() in (".html", ".htm")

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        raw = p.read_text(encoding="utf-8", errors="replace")
        soup = BeautifulSoup(raw, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else p.stem
        body = soup.get_text(separator="\n", strip=True)
        return [IngestResult(
            title=title[:120],
            body=body,
            tags=["html", "file"],
            source=str(p.resolve()),
            metadata={"path": str(p)},
        )]
