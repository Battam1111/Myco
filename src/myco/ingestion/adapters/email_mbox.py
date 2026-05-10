"""Adapter for RFC 2822 emails (``.eml``) and Unix mailbox (``.mbox``).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬): an email export from any
mail client (Apple Mail, Thunderbird, mutt, ``mbsync``) is exactly
the kind of "personal correspondence fragment" the ingestion seam
is meant to absorb. Prior to this adapter, a user pointing
``myco eat --path Inbox.mbox`` at a 500-message archive got either
silent rejection (no extension match) or a single opaque blob via
the text-file fallback (no per-message granularity, no headers
exposed). One :class:`IngestResult` per message is the right shape:
downstream digestion can score, quote, or branch on a single
message rather than the whole archive.

Two on-disk formats are handled:

1. **``.eml``** — a single RFC 2822 message in a file. Common
   single-message export from Outlook / Apple Mail / Thunderbird.
   Parsed via :class:`email.parser.Parser`. Emits exactly one
   :class:`IngestResult`.

2. **``.mbox``** — a Unix mailbox (concatenated messages separated
   by ``From `` envelopes). Common bulk export from mutt / Mail.app
   / Gmail Takeout. Iterated via :class:`mailbox.mbox`. Emits one
   :class:`IngestResult` per message, capped at
   :data:`MAX_MBOX_MESSAGES` (500) so a 50k-message archive does
   not blow up the raw-notes directory in a single ``eat`` call.

Body extraction follows MIME walk-order:

* Multipart messages: pick the first ``text/plain`` part. If none,
  fall back to the first ``text/html`` part with HTML stripped via
  the stdlib :mod:`html.parser` (no BeautifulSoup dependency).
* Attachment parts (``Content-Disposition: attachment`` or any part
  with a ``filename=`` directive) are skipped. We never recover or
  surface attachment payloads — Myco substrates do not store binary
  blobs, and an attached ``id_rsa`` or ``.env`` would otherwise leak
  into a raw note.
* HTML is text-extracted, never executed: we strip ``<script>`` and
  ``<style>`` content alongside other tags. This is defense-in-depth
  even though Myco never renders the body in a browser — third-party
  tools (Cowork preview, Obsidian) might.

Security posture:

* **No execution.** HTML/JS in ``text/html`` parts is treated as
  text only.
* **Attachments dropped.** ``Content-Disposition: attachment`` parts
  are skipped entirely, by design (see above).
* **BCC scrubbed.** The ``Bcc`` / ``Resent-Bcc`` headers are stripped
  before we read anything else from the message. They sometimes
  survive in saved drafts and self-sent archives; emitting them into
  a raw note (which may be shared, replicated, or shown in
  ``brief``) is an accidental privacy disclosure waiting to happen.
* **Credential-glob denial.** A user who saves a credential dump as
  ``.email_credentials.eml`` triggers
  :data:`text_file._is_credential_file` and gets refused.
* **Size cap.** Files over :data:`DEFAULT_MAX_INGEST_BYTES` (10 MB)
  are rejected by ``can_handle``; a 5 GB archive cannot OOM us.

On every former silent-skip path (oversize, missing file, malformed
RFC 2822, corrupt mbox, encoding errors, empty mbox, credential
filename) returns a single failed-stub :class:`IngestResult` per
the v0.7.3 AD1-closure protocol — never ``[]``.
"""

from __future__ import annotations

import email
import mailbox
from collections.abc import Sequence
from email import policy
from email.message import Message
from email.parser import Parser
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult
from .text_file import _is_credential_file

#: Size ceiling for a single email / mbox file (10 MB). Mirrors the
#: cross-adapter cap; oversized archives get a failed-stub.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES

#: Substrings that mark an email-shaped file as credential-bearing
#: in a way the cross-adapter ``text_file._CREDENTIAL_DENY_GLOBS``
#: list doesn't cover. Email exports often pick up names like
#: ``.email_credentials.eml`` (Apple Mail "save as" of an IMAP
#: login dump) or ``smtp_credentials.eml`` — the leading ``.`` and
#: the embedded subword keep ``fnmatch`` from claiming them, so the
#: adapter applies a substring sweep on top of the shared denylist.
#: Lower-case comparison; matches anywhere in the basename.
_EMAIL_CREDENTIAL_SUBSTRINGS: tuple[str, ...] = (
    "credential",
    "password",
    "secret",
    "token",
)


def _is_email_credential_file(name: str) -> bool:
    """Return True if *name* looks credential-bearing for an email
    archive (substring sweep on top of the shared glob denylist).

    Reuses :func:`text_file._is_credential_file` first; only widens
    when the shared list is silent.
    """
    if _is_credential_file(name):
        return True
    lower = name.lower()
    return any(sub in lower for sub in _EMAIL_CREDENTIAL_SUBSTRINGS)


#: Maximum number of messages emitted from a single ``.mbox`` file.
#: A user pointing ``myco eat`` at a 50k-message Gmail Takeout would
#: otherwise produce 50k raw notes in one shot, which is a
#: filesystem / homeostasis stress test we don't want to surface
#: silently. The 501st message produces a single failed-stub naming
#: the truncation; the operator can re-split the archive.
MAX_MBOX_MESSAGES: int = 500

#: Headers stripped from every parsed message before extraction.
#: ``Bcc`` and ``Resent-Bcc`` are private-recipient lists that often
#: survive in saved drafts and self-sent copies; surfacing them in a
#: raw note (which downstream tools may display, replicate, or
#: federate) is an accidental privacy disclosure.
_PRIVACY_HEADERS_TO_STRIP: tuple[str, ...] = ("Bcc", "Resent-Bcc")


class _HtmlToText(HTMLParser):
    """Minimal HTML-to-text extractor using stdlib only.

    Drops the *content* of ``<script>`` and ``<style>`` blocks (not
    just the tags) so we don't surface JS or CSS as "email body".
    Tags themselves are always elided; we keep only the text node
    payload, normalising consecutive whitespace.
    """

    _SKIP_TAGS = frozenset({"script", "style", "head"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._chunks: list[str] = []
        self._skip_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in self._SKIP_TAGS:
            self._skip_depth += 1
        # Translate <br> and block-level openers to newlines so the
        # extracted text retains some shape; otherwise an HTML email
        # collapses to a single line.
        if tag.lower() in {"br", "p", "div", "li", "tr", "h1", "h2", "h3"}:
            self._chunks.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._SKIP_TAGS and self._skip_depth > 0:
            self._skip_depth -= 1
        if tag.lower() in {"p", "div", "li", "tr"}:
            self._chunks.append("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth == 0:
            self._chunks.append(data)

    def get_text(self) -> str:
        # Collapse repeated blank lines and trim per-line whitespace
        # so an HTML body doesn't render as one indented soup.
        raw = "".join(self._chunks)
        lines = [ln.strip() for ln in raw.splitlines()]
        # Drop completely empty leading/trailing lines but preserve
        # paragraph breaks between content.
        out: list[str] = []
        prev_blank = True
        for ln in lines:
            if not ln:
                if prev_blank:
                    continue
                prev_blank = True
                out.append("")
            else:
                prev_blank = False
                out.append(ln)
        # Trim a trailing blank line if present.
        while out and not out[-1]:
            out.pop()
        return "\n".join(out)


def _strip_html(html: str) -> str:
    """Return text content of *html* as a single string (no tags)."""
    parser = _HtmlToText()
    try:
        parser.feed(html)
        parser.close()
    except Exception:  # pragma: no cover — HTMLParser is permissive
        # The stdlib parser tolerates malformed HTML, but we still
        # belt-and-suspenders the failure: a parser bomb gets us back
        # whatever was extracted so far rather than crashing.
        pass
    return parser.get_text()


def _is_attachment_part(part: Message) -> bool:
    """Return True if *part* is an attachment we should skip.

    Two signals matter:
    * Explicit ``Content-Disposition: attachment``.
    * Any disposition with a ``filename=`` directive (some mailers
      use ``inline; filename="…"`` for embedded images we still
      shouldn't ingest as text).
    """
    disposition = part.get("Content-Disposition", "")
    if not disposition:
        return False
    lower = disposition.lower()
    if "attachment" in lower:
        return True
    return "filename" in lower


def _decode_part_payload(part: Message) -> str:
    """Return *part*'s decoded text payload, preferring the declared
    charset and falling back to UTF-8 with replacement on failure.

    Returns an empty string for parts whose payload cannot be
    decoded as bytes (e.g. multipart containers).
    """
    payload = part.get_payload(decode=True)
    if payload is None:
        # Either a multipart container or a non-binary payload
        # (some malformed messages). Try the str payload directly.
        raw = part.get_payload()
        if isinstance(raw, str):
            return raw
        return ""
    if not isinstance(payload, (bytes, bytearray)):
        return ""
    charset = part.get_content_charset() or "utf-8"
    try:
        return payload.decode(charset, errors="strict")
    except (UnicodeDecodeError, LookupError):
        return payload.decode("utf-8", errors="replace")


def _extract_body(msg: Message) -> str:
    """Return the best plain-text body for *msg*.

    Walk order:
    1. If multipart, prefer the first non-attachment ``text/plain``
       part. If none, fall back to the first non-attachment
       ``text/html`` part with HTML stripped.
    2. If single-part, use its decoded payload directly. HTML-only
       singletons are stripped via :func:`_strip_html`.
    3. If nothing is recoverable, return ``""``.
    """
    if msg.is_multipart():
        plain_text: str | None = None
        html_text: str | None = None
        for part in msg.walk():
            if part.is_multipart():
                continue
            if _is_attachment_part(part):
                continue
            ctype = part.get_content_type().lower()
            if ctype == "text/plain" and plain_text is None:
                plain_text = _decode_part_payload(part)
            elif ctype == "text/html" and html_text is None:
                html_text = _decode_part_payload(part)
        if plain_text is not None and plain_text.strip():
            return plain_text
        if html_text is not None and html_text.strip():
            return _strip_html(html_text)
        # Fall through to empty if both were missing/blank — the
        # caller decides whether to emit a body-less ok or a stub.
        return plain_text or (_strip_html(html_text) if html_text is not None else "")
    # Single-part message.
    if _is_attachment_part(msg):
        return ""
    body = _decode_part_payload(msg)
    if msg.get_content_type().lower() == "text/html":
        return _strip_html(body)
    return body


def _scrub_privacy_headers(msg: Message) -> None:
    """Delete BCC / Resent-Bcc headers in-place from *msg*.

    ``email.message.Message.__delitem__`` removes all instances of
    the named header (case-insensitive); we do not need to loop.
    """
    for hdr in _PRIVACY_HEADERS_TO_STRIP:
        del msg[hdr]


def _format_date_iso(raw_date: str | None) -> str:
    """Return ISO 8601 form of an RFC 2822 ``Date`` header.

    Unparseable / missing dates return an empty string rather than
    raising — a missing ``Date`` is common in drafts and shouldn't
    fail the ingest of an otherwise valid message.
    """
    if not raw_date:
        return ""
    try:
        dt = parsedate_to_datetime(raw_date)
    except (TypeError, ValueError):
        return ""
    if dt is None:
        return ""
    try:
        return dt.isoformat()
    except (ValueError, OverflowError):
        return ""


def _safe_header(msg: Message, name: str) -> str:
    """Return *msg*'s header value as a string, or ``""``.

    The stdlib parser sometimes returns ``Header`` objects for
    encoded headers; we coerce to ``str`` for safe metadata storage.
    Empty header values are normalised to ``""``.
    """
    val = msg.get(name)
    if val is None:
        return ""
    return str(val).strip()


def _result_from_message(
    *,
    msg: Message,
    path: Path,
    source: str,
    index: int,
    total: int,
) -> IngestResult:
    """Build one :class:`IngestResult` from a parsed message.

    ``index`` is 0-based per file; ``total`` is the count for the
    archive (1 for a ``.eml``, ≥1 for an ``.mbox``). Both flow into
    metadata so downstream consumers can reconstruct ordering.
    """
    _scrub_privacy_headers(msg)
    subject = _safe_header(msg, "Subject")
    from_addr = _safe_header(msg, "From")
    to_addr = _safe_header(msg, "To")
    cc_addr = _safe_header(msg, "Cc")
    message_id = _safe_header(msg, "Message-Id") or _safe_header(msg, "Message-ID")
    date_iso = _format_date_iso(_safe_header(msg, "Date"))
    body = _extract_body(msg)
    # Title format: subject (or fallback) + 0-padded index for stable
    # sort within an mbox. `` `` etc. in subjects survive into
    # the slug; ``eat`` does its own slugification on top.
    safe_subject = subject or "(no subject)"
    if total > 1:
        title = f"{path.stem}-msg-{index:03d}-{safe_subject}"
    else:
        title = f"{path.stem}-{safe_subject}"
    return IngestResult(
        title=title,
        body=body,
        tags=["email"],
        source=source,
        metadata={
            "kind": "email",
            "subject": subject,
            "from": from_addr,
            "to": to_addr,
            "cc": cc_addr,
            "date": date_iso,
            "message_id": message_id,
            "message_index": index,
            "message_count": total,
            "source_file": source,
        },
    )


class EmailMboxAdapter(Adapter):
    """Adapter for ``.eml`` (single message) and ``.mbox`` (mailbox).

    See module docstring for full security and extraction contract.

    ``.eml`` files emit exactly one :class:`IngestResult`; ``.mbox``
    files emit one per message, capped at :data:`MAX_MBOX_MESSAGES`
    with a trailing failed-stub if truncation occurred. Refuses
    credential-bearing filenames and oversized files at
    ``can_handle``; returns a failed-stub on every former
    silent-skip path at ``ingest`` per the v0.7.3 AD1-closure
    protocol.
    """

    @property
    def name(self) -> str:
        return "email-mbox"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".eml", ".mbox"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in self.extensions:
            return False
        # P0-SEC-4 parity with text_file: refuse credential-bearing
        # filenames regardless of extension. ``.email_credentials.eml``
        # would otherwise be claimed because the extension matches.
        # The local substring widener catches names the shared glob
        # list doesn't cover (e.g. ``.email_credentials.eml``).
        if _is_email_credential_file(p.name):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check size cap and credential name at
        # ingest. ``can_handle`` may have been bypassed by a third-
        # party orchestrator or test fixture calling ``ingest``
        # directly.
        try:
            size = p.stat().st_size
        except OSError as exc:
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=str(p),
                    status="failed",
                    failure_reason=f"stat() failed: {exc}",
                )
            ]
        if size > DEFAULT_MAX_INGEST_BYTES:
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=str(p),
                    status="failed",
                    failure_reason=(
                        f"email-mbox size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_INGEST_BYTES} bytes"
                    ),
                )
            ]
        if _is_email_credential_file(p.name):
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=str(p),
                    status="failed",
                    failure_reason=(
                        f"refused credential-bearing file by name: {p.name!r}"
                    ),
                )
            ]
        # Normalise to POSIX separators on Windows (graph.py contract).
        source = str(p.resolve()).replace("\\", "/")
        suffix = p.suffix.lower()
        if suffix == ".eml":
            return self._ingest_eml(path=p, source=source)
        if suffix == ".mbox":
            return self._ingest_mbox(path=p, source=source)
        # Defensive: extension was verified in can_handle, but a
        # direct-call path could pass through with an unexpected
        # extension.
        return [
            IngestResult(
                title=p.stem,
                body="",
                source=source,
                status="failed",
                failure_reason=(
                    f"unsupported extension for email-mbox adapter: {p.suffix!r}"
                ),
            )
        ]

    # ---- format-specific parsers -------------------------------------------

    @staticmethod
    def _ingest_eml(*, path: Path, source: str) -> Sequence[IngestResult]:
        """Parse a single ``.eml`` and return one :class:`IngestResult`.

        Decode failures, malformed RFC 2822, or empty payloads
        return a single failed-stub naming the cause.
        """
        try:
            raw_bytes = path.read_bytes()
        except OSError as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"read failed: {exc}",
                )
            ]
        if not raw_bytes:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"empty .eml file: {path.name!r}",
                )
            ]
        # Decode preserving the raw on-wire representation. ``email``
        # auto-handles per-part charsets via Content-Type; we only
        # need the outer envelope as text. ``replace`` keeps a
        # malformed-but-readable header from blowing up the parse.
        try:
            text = raw_bytes.decode("utf-8", errors="replace")
        except UnicodeDecodeError as exc:  # pragma: no cover — replace never raises
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"utf-8 decode failed: {exc}",
                )
            ]
        try:
            msg = Parser(policy=policy.default).parsestr(text)
        except (email.errors.MessageError, ValueError, IndexError) as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"malformed RFC 2822 message: {exc}",
                )
            ]
        # ``Parser`` is permissive — it'll happily build a Message
        # from pure binary garbage with zero headers, putting the
        # whole input in ``get_payload()``. RFC 2822 mandates a
        # header section, so the cleanest "is this actually an
        # email?" check is whether ANY of the canonical headers
        # parsed. If not, refuse rather than silently emit a
        # body-of-garbage IngestResult.
        has_headers = any(
            msg.get(h) for h in ("From", "To", "Subject", "Date", "Message-Id")
        )
        if not has_headers:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(f"no recognisable RFC 2822 headers: {path.name!r}"),
                )
            ]
        return [
            _result_from_message(msg=msg, path=path, source=source, index=0, total=1)
        ]

    @staticmethod
    def _ingest_mbox(*, path: Path, source: str) -> Sequence[IngestResult]:
        """Iterate ``.mbox`` and emit one IngestResult per message.

        Caps at :data:`MAX_MBOX_MESSAGES`; the (cap+1)th onwards are
        replaced by a single trailing failed-stub. Read-only —
        never mutates the mbox via ``add()`` / ``remove()``.

        On Windows ``mailbox.mbox`` uses dotlock-only locking (no
        ``flock``). We always pair the open with ``close()`` in a
        ``finally`` so a parse error doesn't leave a stray ``.lock``
        file or hold the underlying handle.
        """
        # ``mailbox.mbox`` is permissive about non-existent / non-mbox
        # input — it'll still construct an empty container if the
        # file is unreadable. Pre-check via a real open() so we can
        # produce a concrete failed-stub for "file vanished between
        # can_handle and ingest" / "permission denied".
        try:
            with path.open("rb"):
                pass
        except OSError as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"open failed: {exc}",
                )
            ]
        try:
            box = mailbox.mbox(str(path), create=False)
        except (OSError, mailbox.Error) as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"mbox open failed: {exc}",
                )
            ]
        results: list[IngestResult] = []
        try:
            try:
                total = len(box)
            except (OSError, mailbox.Error) as exc:
                return [
                    IngestResult(
                        title=path.stem,
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=f"corrupt mbox: {exc}",
                    )
                ]
            if total == 0:
                return [
                    IngestResult(
                        title=path.stem,
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=f"empty mbox: {path.name!r}",
                    )
                ]
            effective_total = min(total, MAX_MBOX_MESSAGES)
            for index, key in enumerate(box.keys()):
                if index >= MAX_MBOX_MESSAGES:
                    results.append(
                        IngestResult(
                            title=f"{path.stem}-msg-{index:03d}-truncated",
                            body="",
                            source=source,
                            status="failed",
                            failure_reason=(
                                f"mbox truncated at {MAX_MBOX_MESSAGES} "
                                f"messages (file has {total}); re-split the "
                                f"archive to ingest the remainder"
                            ),
                            metadata={
                                "kind": "email",
                                "message_index": index,
                                "message_count": total,
                                "source_file": source,
                            },
                        )
                    )
                    break
                try:
                    raw_msg = box.get_message(key)
                except (
                    OSError,
                    mailbox.Error,
                    email.errors.MessageError,
                    ValueError,
                ) as exc:
                    results.append(
                        IngestResult(
                            title=f"{path.stem}-msg-{index:03d}-malformed",
                            body="",
                            source=source,
                            status="failed",
                            failure_reason=(
                                f"mbox message {index} parse failed: {exc}"
                            ),
                            metadata={
                                "kind": "email",
                                "message_index": index,
                                "message_count": total,
                                "source_file": source,
                            },
                        )
                    )
                    continue
                results.append(
                    _result_from_message(
                        msg=raw_msg,
                        path=path,
                        source=source,
                        index=index,
                        total=effective_total,
                    )
                )
        finally:
            try:
                box.close()
            except OSError:  # pragma: no cover — close on Windows is best-effort
                pass
        if not results:
            # Defensive: should not be reachable (we cover empty,
            # truncated, and per-message-error above), but keep the
            # AD1 contract — never return ``[]``.
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"mbox produced no results: {path.name!r}",
                )
            ]
        return results
