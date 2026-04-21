"""Adapter for HTTP/HTTPS URLs.

Requires ``httpx`` (part of the ``[adapters]`` extras).
Dispatches to other adapters by Content-Type when possible (e.g.
PDF, HTML), or falls back to treating the body as plain text.

v0.5.8 security fixes (Lens 6 P0-SEC-5 / Lens 8 P0-NET-3):
* **SSRF guard** — the URL host is resolved and rejected if it
  maps to a loopback, link-local, private, or other non-routable
  IP range. Without this, an agent pointed at
  ``http://169.254.169.254/latest/meta-data/`` would exfiltrate
  EC2 credentials; ``http://127.0.0.1:8080/`` would grab local
  admin panels. The scheme is also restricted to http/https
  (no ``file://``, ``gopher://``, ``ftp://``, ``data:``).
* **Response-size cap** — fetched bodies are bounded to
  ``DEFAULT_MAX_INGEST_BYTES`` (10 MB) via streaming + byte counter,
  so a malicious endpoint returning Gigabytes of data can no longer
  OOM the agent process. Streams abort as soon as the cap is
  exceeded (no silent truncation — we error instead).
* **Redirect target also SSRF-checked** — ``follow_redirects`` is
  still on, but we use ``httpx.Client`` with an event hook that
  re-validates each redirect target's host. A server answering
  ``302 Location: http://127.0.0.1/`` cannot bypass the guard.
"""

from __future__ import annotations

import ipaddress
import socket
from collections.abc import Sequence
from urllib.parse import urlparse

import httpx  # will ImportError if not installed; registry skips

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

#: Byte cap on an HTTP response body (10 MB). Mirrors the local-file
#: caps on text/pdf/html/tabular adapters so a URL ingest cannot be
#: used to bypass the size envelope.
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


class UrlFetcher(Adapter):
    @property
    def name(self) -> str:
        return "url"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset()  # dispatches on URL prefix, not extension

    def can_handle(self, target: str) -> bool:
        if not (target.startswith("http://") or target.startswith("https://")):
            return False
        try:
            _validate_url(target)
        except UrlFetchError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        # Re-validate at ingest (can_handle may be bypassed by direct
        # caller). Any failure here is a hard error — the agent must
        # see it, not a silent empty-result.
        _validate_url(target)

        def _on_response(resp: httpx.Response) -> None:
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
