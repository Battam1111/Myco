"""Adapter for HTTP/HTTPS URLs.

Requires ``httpx`` (part of the ``[adapters]`` extras).
Dispatches to other adapters by Content-Type when possible (e.g.
PDF, HTML), or falls back to treating the body as plain text.
"""

from __future__ import annotations

from collections.abc import Sequence
from urllib.parse import urlparse

import httpx  # will ImportError if not installed; registry skips

from .protocol import Adapter, IngestResult


class UrlFetcher(Adapter):
    @property
    def name(self) -> str:
        return "url"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset()  # dispatches on URL prefix, not extension

    def can_handle(self, target: str) -> bool:
        return target.startswith("http://") or target.startswith("https://")

    def ingest(self, target: str) -> Sequence[IngestResult]:
        resp = httpx.get(target, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        ct = resp.headers.get("content-type", "").lower()
        domain = urlparse(target).netloc
        tags = ["url", domain]

        if "text/html" in ct:
            body = self._strip_html(resp.text)
        elif "application/pdf" in ct:
            body = self._extract_pdf_bytes(resp.content)
        elif "application/json" in ct:
            body = resp.text
            tags.append("json")
        else:
            body = resp.text

        title = domain + urlparse(target).path.rstrip("/").rsplit("/", 1)[-1]
        return [
            IngestResult(
                title=title[:120] or domain,
                body=body,
                tags=tags,
                source=target,
                metadata={"status": resp.status_code, "content_type": ct},
            )
        ]

    @staticmethod
    def _strip_html(html: str) -> str:
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header"]):
                tag.decompose()
            return soup.get_text(separator="\n", strip=True)
        except ImportError:
            # Rough fallback: strip tags with regex
            import re

            return re.sub(r"<[^>]+>", "", html)

    @staticmethod
    def _extract_pdf_bytes(data: bytes) -> str:
        try:
            import io

            from pypdf import PdfReader as _PR

            reader = _PR(io.BytesIO(data))
            pages = [p.extract_text() or "" for p in reader.pages]
            return "\n\n---\n\n".join(pages)
        except ImportError:
            return "(PDF content; install pypdf to extract text)"
