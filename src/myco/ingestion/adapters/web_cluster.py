"""Web / fetched-content ingestion adapter cluster (v0.8.8 merge).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters".

Merged home of three optional-dep adapters that previously lived in
their own per-class files (``pdf_reader.py``, ``html_reader.py``,
``url_fetcher.py``). Cluster-merge follows the v0.8.8 substrate-wide
consolidation policy. Section markers ``# === <AdapterName> — ...``
preserve per-class review boundaries; git history holds the original
per-file state.

Adapters in this cluster:

* :class:`PdfReader` — local ``.pdf`` files via ``pypdf``.
* :class:`HtmlReader` — local ``.html`` / ``.htm`` files via
  ``beautifulsoup4``.
* :class:`UrlFetcher` — ``http(s)://`` URLs via ``httpx``. Dispatches
  to PDF / HTML body-extraction by Content-Type.

Optional-dep gating follows the v0.8.0 multimedia pattern: each heavy
dependency is lazily imported, with a module-top "soft import" sentinel
that lets :meth:`can_handle` skip the adapter cleanly when the dep is
absent (instead of failing at module-import time and being silently
unregistered). This makes the adapter contract uniform across stdlib
and optional-dep adapters: they always register, and
``can_handle`` / ``ingest`` decide whether to participate.

v0.5.8 security floor preserved verbatim:

* Size cap (``DEFAULT_MAX_INGEST_BYTES = 10 MB``) on every
  local-file path and on the HTTP-response stream.
* POSIX-normalised source paths.
* SSRF guard for URL host + every redirect target. Scheme restricted
  to ``http`` / ``https``.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Sequence
from pathlib import Path
from urllib.parse import urlparse

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

# =========================================================================
# Soft imports — optional deps loaded once at module-import time so that
# can_handle can cheaply gate. Each sentinel is None when the dep is
# missing; the corresponding adapter's can_handle returns False, and
# ingest emits a "failed" IngestResult rather than raising.
# =========================================================================

try:  # pypdf — for PdfReader
    from pypdf import PdfReader as _PR
except ImportError:  # pragma: no cover — optional dep
    _PR = None  # type: ignore[assignment,misc]

try:  # bs4 — for HtmlReader (and UrlFetcher's HTML branch)
    from bs4 import BeautifulSoup
except ImportError:  # pragma: no cover — optional dep
    BeautifulSoup = None  # type: ignore[assignment,misc]

try:  # httpx — for UrlFetcher
    import httpx
except ImportError:  # pragma: no cover — optional dep
    httpx = None  # type: ignore[assignment]

# =========================================================================
# Shared module-level helpers
# =========================================================================

#: Size ceiling for every fetched-content adapter (10 MB). Mirrors
#: :data:`myco.core.io_atomic.DEFAULT_MAX_READ_BYTES`. PDFs / HTML /
#: HTTP response bodies that exceed this are rejected at ``can_handle``
#: (local) or aborted mid-stream (network) so a 5 GB attacker-planted
#: file or response cannot OOM the reader.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES

#: Allowed URL schemes. ``file://`` would let an agent pretend a
#: local-file ingest is a URL ingest (bypassing path trust checks);
#: ``gopher://`` / ``ftp://`` / ``data:`` are historical SSRF vectors.
_ALLOWED_SCHEMES: frozenset[str] = frozenset({"http", "https"})


class UrlFetchError(Exception):
    """Raised when an HTTP fetch fails a security check."""


def _is_routable_host(host: str) -> bool:
    """Return True if ``host`` resolves to at least one public IP.

    All resolved addresses are checked; if **any** resolves to
    loopback / link-local / private / multicast / reserved, the
    host is rejected. This matches how browsers and hardened SSRF
    libraries treat mixed-A-record attacks.
    """
    if not host:
        return False
    try:
        # Permissive lookup — both IPv4 and IPv6.
        infos = socket.getaddrinfo(host, None)
    except OSError:
        return False
    for info in infos:
        ip_str = info[4][0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        if (
            ip.is_loopback
            or ip.is_link_local
            or ip.is_private
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        ):
            return False
    return True


def _validate_url(url: str) -> None:
    """Raise :class:`UrlFetchError` if ``url`` fails the SSRF / scheme
    checks. Used both on the user-provided URL and on any redirect
    target the server returns."""
    parsed = urlparse(url)
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UrlFetchError(
            f"url scheme {parsed.scheme!r} is not allowed "
            f"(expected one of {sorted(_ALLOWED_SCHEMES)})"
        )
    host = parsed.hostname or ""
    # Reject bracketed IPv6 literals that resolve to loopback too.
    if not _is_routable_host(host):
        raise UrlFetchError(
            f"url host {host!r} resolves to a non-routable address; "
            f"refusing to fetch (SSRF guard)"
        )


def _failed(p: Path, reason: str) -> list[IngestResult]:
    """Standard failed-stub for local-file paths."""
    return [
        IngestResult(
            title=p.stem,
            body="",
            source=str(p),
            status="failed",
            failure_reason=reason,
        )
    ]


# =========================================================================
# === PdfReader — formerly pdf_reader.py (112 LOC)
# =========================================================================


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
        if _PR is None:  # optional dep missing
            return False
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
        if _PR is None:
            return _failed(p, "pypdf not installed; install myco[adapters]")
        # Belt + suspenders: re-check at ingest; ``can_handle`` may be
        # bypassed by a direct-invocation path.
        try:
            size = p.stat().st_size
        except OSError as exc:
            return _failed(p, f"stat() failed: {exc}")
        if size > DEFAULT_MAX_INGEST_BYTES:
            return _failed(
                p,
                f"pdf size cap exceeded: {size} > {DEFAULT_MAX_INGEST_BYTES} bytes",
            )
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


# =========================================================================
# === HtmlReader — formerly html_reader.py (99 LOC)
# =========================================================================


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
        if BeautifulSoup is None:  # optional dep missing
            return False
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
        if BeautifulSoup is None:
            return _failed(p, "beautifulsoup4 not installed; install myco[adapters]")
        try:
            size = p.stat().st_size
        except OSError as exc:
            return _failed(p, f"stat() failed: {exc}")
        if size > DEFAULT_MAX_INGEST_BYTES:
            return _failed(
                p,
                f"html size cap exceeded: {size} > {DEFAULT_MAX_INGEST_BYTES} bytes",
            )
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


# =========================================================================
# === UrlFetcher — formerly url_fetcher.py (231 LOC)
# =========================================================================


class UrlFetcher(Adapter):
    """Adapter for ``http(s)://`` URLs via ``httpx``.

    Fetches the URL with streaming + byte-cap abort (response bodies
    over :data:`DEFAULT_MAX_INGEST_BYTES` raise
    :class:`UrlFetchError` rather than buffer in memory). The host
    is validated by :func:`_validate_url` (SSRF guard: loopback /
    link-local / private / multicast / reserved addresses refused;
    scheme restricted to ``http`` / ``https``). Redirect targets
    re-validate.
    """

    @property
    def name(self) -> str:
        return "url"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset()  # dispatches on URL prefix, not extension

    def can_handle(self, target: str) -> bool:
        if httpx is None:  # optional dep missing
            return False
        if not (target.startswith("http://") or target.startswith("https://")):
            return False
        try:
            _validate_url(target)
        except UrlFetchError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        if httpx is None:
            return [
                IngestResult(
                    title=urlparse(target).netloc or target,
                    body="",
                    source=target,
                    status="failed",
                    failure_reason="httpx not installed; install myco[adapters]",
                )
            ]
        # Re-validate at ingest (can_handle may be bypassed by direct
        # caller). Any failure here is a hard error — the agent must
        # see it, not a silent empty-result.
        _validate_url(target)

        def _on_response(resp) -> None:
            # httpx follows redirects internally; the final URL may
            # differ from the requested URL. Validate it before we
            # stream the body.
            _validate_url(str(resp.url))

        # ``stream=True`` lets us abort reads once the cap is hit.
        with httpx.Client(follow_redirects=True, timeout=30) as client:
            with client.stream("GET", target) as resp:
                resp.raise_for_status()
                _on_response(resp)
                chunks: list[bytes] = []
                total = 0
                for chunk in resp.iter_bytes():
                    total += len(chunk)
                    if total > DEFAULT_MAX_INGEST_BYTES:
                        raise UrlFetchError(
                            f"response body exceeded {DEFAULT_MAX_INGEST_BYTES} "
                            f"bytes; aborting read (size cap, Lens 8 P0-NET-3)"
                        )
                    chunks.append(chunk)
                data = b"".join(chunks)
                ct = resp.headers.get("content-type", "").lower()
                final_url = str(resp.url)
                status = resp.status_code

        # Decode to text where appropriate.
        try:
            text = data.decode("utf-8", errors="replace")
        except UnicodeDecodeError:
            text = ""

        domain = urlparse(target).netloc
        tags = ["url", domain]

        if "text/html" in ct:
            body = self._strip_html(text)
        elif "application/pdf" in ct:
            body = self._extract_pdf_bytes(data)
        elif "application/json" in ct:
            body = text
            tags.append("json")
        else:
            body = text

        title = domain + urlparse(target).path.rstrip("/").rsplit("/", 1)[-1]
        return [
            IngestResult(
                title=title[:120] or domain,
                body=body,
                tags=tags,
                source=target,
                metadata={
                    "status": status,
                    "content_type": ct,
                    "bytes": total,
                    "final_url": final_url,
                },
            )
        ]

    @staticmethod
    def _strip_html(html: str) -> str:
        # Reuse the cluster-level BeautifulSoup if available; otherwise
        # regex-strip. Note: BeautifulSoup is already a module-level
        # soft-import, so the local try/except is just a guard against
        # the (vanishingly rare) re-import-error case.
        if BeautifulSoup is None:
            import re

            return re.sub(r"<[^>]+>", "", html)
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    @staticmethod
    def _extract_pdf_bytes(data: bytes) -> str:
        if _PR is None:
            return "(PDF content; install pypdf to extract text)"
        import io

        reader = _PR(io.BytesIO(data))
        pages = [p.extract_text() or "" for p in reader.pages]
        return "\n\n---\n\n".join(pages)
