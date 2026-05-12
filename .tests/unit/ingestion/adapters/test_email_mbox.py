"""Tests for the email/mbox adapter (``.eml`` + ``.mbox``).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) — "personal correspondence
fragment" is ingestible material, so a 50-message ``.mbox`` must
produce 50 raw notes (not 1 opaque blob), and one ``.eml`` produces
one note with subject/from/to/date/message-id surfaced.

These tests pin the v0.7.4 email/mbox contract:

* ``can_handle`` — extension fast-path + credential-glob denial +
  size cap.
* ``ingest`` — one IngestResult for ``.eml``, one per message for
  ``.mbox``; failed-stub on every former silent-skip path
  (corrupt, empty, oversize, malformed RFC 2822, credential-named).
* MIME walk — multipart prefers ``text/plain``, falls back to
  ``text/html`` with HTML stripped via stdlib ``html.parser``.
* Security — attachments dropped, BCC scrubbed, HTML never executed.
* mbox cap — message #501 onwards becomes a single trailing
  failed-stub naming the truncation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime
from pathlib import Path

from myco.ingestion.adapters.email_mbox import EmailMboxAdapter

# ---------------------------------------------------------------------------
# Fixture helpers — build an .eml or .mbox on the fly without mock libs.
# ---------------------------------------------------------------------------


def _write_eml(path: Path, *, subject: str = "hello", body: str = "world") -> None:
    """Write a minimal but conformant single-part RFC 2822 ``.eml``."""
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.com"
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc))
    msg["Message-Id"] = "<msg-1@example.com>"
    msg.set_content(body)
    path.write_bytes(bytes(msg))


def _mbox_envelope(
    *,
    sender: str = "alice@example.com",
    timestamp: str = "Mon Jun  1 12:00:00 2024",
) -> str:
    """Return the ``From `` envelope line that delimits mbox messages."""
    return f"From {sender} {timestamp}\n"


def _write_mbox(path: Path, messages: list[bytes]) -> None:
    """Write *messages* (each one a serialised EmailMessage as bytes)
    to *path* as a Unix mbox, separated by ``From `` envelopes.

    Done by hand rather than via ``mailbox.mbox.add()`` so the test
    fixture mirrors what an Apple Mail / Thunderbird export actually
    produces on disk, and so we don't need write semantics on a
    Windows-locked mbox.
    """
    parts: list[bytes] = []
    for raw in messages:
        parts.append(_mbox_envelope().encode("ascii"))
        parts.append(raw)
        if not raw.endswith(b"\n"):
            parts.append(b"\n")
        parts.append(b"\n")
    path.write_bytes(b"".join(parts))


def _build_message(
    *,
    subject: str = "hi",
    body: str = "test body",
    sender: str = "alice@example.com",
) -> bytes:
    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = "bob@example.com"
    msg["Subject"] = subject
    msg["Date"] = format_datetime(datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc))
    msg["Message-Id"] = f"<{subject.replace(' ', '-')}@example.com>"
    msg.set_content(body)
    return bytes(msg)


# ---------------------------------------------------------------------------
# can_handle: extension fast-path + denials
# ---------------------------------------------------------------------------


def test_can_handle_eml_extension(tmp_path: Path) -> None:
    """``.eml`` is recognised via the extension fast-path."""
    p = tmp_path / "letter.eml"
    _write_eml(p)
    assert EmailMboxAdapter().can_handle(str(p)) is True


def test_can_handle_mbox_extension(tmp_path: Path) -> None:
    """``.mbox`` is recognised via the extension fast-path."""
    p = tmp_path / "inbox.mbox"
    _write_mbox(p, [_build_message()])
    assert EmailMboxAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_other(tmp_path: Path) -> None:
    """Non-email extensions (``.txt``, ``.md``, no extension) are not
    claimed by this adapter — they fall through to text-file."""
    adapter = EmailMboxAdapter()
    txt = tmp_path / "letter.txt"
    txt.write_text(
        "From: a@b\nSubject: looks like an email\n\nbut isn't", encoding="utf-8"
    )
    assert adapter.can_handle(str(txt)) is False
    md = tmp_path / "notes.md"
    md.write_text("# notes", encoding="utf-8")
    assert adapter.can_handle(str(md)) is False
    bare = tmp_path / "noext"
    bare.write_text("anything", encoding="utf-8")
    assert adapter.can_handle(str(bare)) is False


# ---------------------------------------------------------------------------
# ingest: .eml — single message → one IngestResult with full headers
# ---------------------------------------------------------------------------


def test_ingest_eml_extracts_headers_and_body(tmp_path: Path) -> None:
    """An ``.eml`` produces ONE IngestResult with subject / from / to /
    date (ISO 8601) / message-id / body all surfaced in metadata."""
    p = tmp_path / "letter.eml"
    _write_eml(p, subject="Project status", body="All systems green.")
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    assert r.metadata["kind"] == "email"
    assert r.metadata["subject"] == "Project status"
    assert r.metadata["from"] == "alice@example.com"
    assert r.metadata["to"] == "bob@example.com"
    assert r.metadata["message_id"] == "<msg-1@example.com>"
    # Date round-trips to ISO 8601 with timezone offset preserved.
    assert r.metadata["date"].startswith("2024-06-01T12:00:00")
    # Body is the plain-text payload (set_content adds a trailing \n).
    assert "All systems green." in r.body
    assert "email" in r.tags


def test_ingest_eml_multipart_prefers_text_plain(tmp_path: Path) -> None:
    """A multipart message with both text/plain and text/html parts
    surfaces the text/plain version — we never strip-and-emit the
    HTML if a plaintext alternative exists."""
    p = tmp_path / "multi.eml"
    msg = EmailMessage()
    msg["From"] = "a@b"
    msg["To"] = "c@d"
    msg["Subject"] = "multipart"
    msg["Date"] = format_datetime(datetime(2024, 6, 1, tzinfo=timezone.utc))
    msg["Message-Id"] = "<mp-1@x>"
    msg.set_content("PLAIN TEXT VERSION")
    msg.add_alternative("<html><body><p>HTML VERSION</p></body></html>", subtype="html")
    p.write_bytes(bytes(msg))
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    assert "PLAIN TEXT VERSION" in r.body
    assert "HTML VERSION" not in r.body  # html branch was not taken


def test_ingest_eml_falls_back_to_text_html_with_html_stripped(
    tmp_path: Path,
) -> None:
    """An HTML-only multipart (no text/plain alternative) surfaces
    the text content extracted via stdlib html.parser. Tags must be
    elided; <script> *content* must be dropped (not just the tag)."""
    p = tmp_path / "html_only.eml"
    msg = EmailMessage()
    msg["From"] = "a@b"
    msg["To"] = "c@d"
    msg["Subject"] = "html only"
    msg["Date"] = format_datetime(datetime(2024, 6, 1, tzinfo=timezone.utc))
    msg["Message-Id"] = "<ho-1@x>"
    # set_content with a content-type forces a non-text/plain leaf,
    # so the multipart walker will only find text/html.
    msg.set_content(
        "<html><body>"
        "<p>Visible paragraph.</p>"
        "<script>alert('do not run');</script>"
        "<style>.x { color: red; }</style>"
        "<p>Second paragraph.</p>"
        "</body></html>",
        subtype="html",
    )
    p.write_bytes(bytes(msg))
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    assert "Visible paragraph." in r.body
    assert "Second paragraph." in r.body
    # Defense-in-depth: script and style content must NOT bleed into
    # the body as text. The extractor drops both tag and content.
    assert "alert" not in r.body
    assert "do not run" not in r.body
    assert "color: red" not in r.body
    # Tags themselves are also gone.
    assert "<p>" not in r.body
    assert "<html>" not in r.body


# ---------------------------------------------------------------------------
# ingest: .mbox — one IngestResult per message + truncation cap
# ---------------------------------------------------------------------------


def test_ingest_mbox_emits_one_result_per_message(tmp_path: Path) -> None:
    """A 4-message mbox → 4 IngestResults with sequential indices and
    distinct subjects surfaced in metadata."""
    p = tmp_path / "four.mbox"
    msgs = [_build_message(subject=f"Message {i}", body=f"body {i}") for i in range(4)]
    _write_mbox(p, msgs)
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 4
    assert all(r.status == "ok" for r in results)
    assert [r.metadata["message_index"] for r in results] == [0, 1, 2, 3]
    assert [r.metadata["subject"] for r in results] == [
        "Message 0",
        "Message 1",
        "Message 2",
        "Message 3",
    ]
    assert all(r.metadata["kind"] == "email" for r in results)
    assert all(r.metadata["source_file"].endswith("four.mbox") for r in results)
    # Bodies survive the round-trip.
    assert "body 0" in results[0].body
    assert "body 3" in results[3].body


def test_ingest_mbox_truncates_at_500_messages(tmp_path: Path, monkeypatch) -> None:
    """A mbox over the cap → cap valid IngestResults followed by ONE
    failed-stub naming the truncation. We patch the cap down to 5
    so the test stays fast — the contract is the same.

    Validates:
    * Exactly cap+1 results (5 ok + 1 failed-stub).
    * The trailing stub carries ``failure_reason`` mentioning the
      truncation and the actual message count.
    """
    monkeypatch.setattr("myco.ingestion.adapters.email_mbox.MAX_MBOX_MESSAGES", 5)
    p = tmp_path / "many.mbox"
    msgs = [_build_message(subject=f"M{i}") for i in range(8)]
    _write_mbox(p, msgs)
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 6  # 5 ok + 1 truncation stub
    assert all(r.status == "ok" for r in results[:5])
    assert results[5].status == "failed"
    assert "truncated" in results[5].failure_reason
    assert "5" in results[5].failure_reason  # the cap
    assert "8" in results[5].failure_reason  # the actual count


# ---------------------------------------------------------------------------
# Security: attachments / BCC / credentials
# ---------------------------------------------------------------------------


def test_ingest_eml_skips_attachments(tmp_path: Path) -> None:
    """Attachment parts (``Content-Disposition: attachment``) are
    skipped entirely. The body of the IngestResult must contain ONLY
    the plain-text inline part — never any byte of the attachment.

    We craft a message with a text/plain inline body plus a
    text/plain *attachment* (so a naive walker that only checks
    Content-Type would surface both). The adapter must use the
    Content-Disposition signal, not just MIME type."""
    p = tmp_path / "with_attachment.eml"
    msg = EmailMessage()
    msg["From"] = "a@b"
    msg["To"] = "c@d"
    msg["Subject"] = "with attachment"
    msg["Date"] = format_datetime(datetime(2024, 6, 1, tzinfo=timezone.utc))
    msg["Message-Id"] = "<att-1@x>"
    msg.set_content("INLINE BODY")
    # Attach a file with text/plain content type — same MIME as the
    # body, distinguished only by Content-Disposition: attachment.
    msg.add_attachment(
        b"SECRET ATTACHMENT BODY",
        maintype="text",
        subtype="plain",
        filename="secret.txt",
    )
    p.write_bytes(bytes(msg))
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    assert "INLINE BODY" in r.body
    # The attachment payload must not appear in the body at all.
    assert "SECRET ATTACHMENT BODY" not in r.body
    assert "secret.txt" not in r.body


def test_ingest_strips_bcc_header(tmp_path: Path) -> None:
    """The ``Bcc`` header is private-recipient data; it must be
    scrubbed before metadata is captured. The IngestResult must
    contain no trace of the BCC recipients in metadata, body, or
    title — even when the source ``.eml`` has a Bcc header set."""
    p = tmp_path / "bcc.eml"
    msg = EmailMessage()
    msg["From"] = "alice@example.com"
    msg["To"] = "bob@example.com"
    msg["Cc"] = "carol@example.com"
    msg["Bcc"] = "secret-recipient@hidden.com"
    msg["Subject"] = "with bcc"
    msg["Date"] = format_datetime(datetime(2024, 6, 1, tzinfo=timezone.utc))
    msg["Message-Id"] = "<bcc-1@x>"
    msg.set_content("body without bcc surfacing")
    p.write_bytes(bytes(msg))
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    r = results[0]
    assert r.status == "ok"
    # No metadata field exposes the BCC recipient.
    assert "secret-recipient@hidden.com" not in str(r.metadata)
    # Belt-and-suspenders: no body / title leak either.
    assert "secret-recipient" not in r.body
    assert "secret-recipient" not in r.title
    # Cc is allowed to be present (it's already public among the
    # explicit recipients); confirm the adapter at least kept it
    # so we know we filtered Bcc specifically rather than wiping
    # all recipient headers.
    assert r.metadata["cc"] == "carol@example.com"


def test_ingest_corrupt_eml_returns_failed_stub(tmp_path: Path) -> None:
    """A non-RFC-2822 ``.eml`` (no headers, no body, just garbage)
    returns a single failed-stub naming what was wrong. Empty files
    also return a failed-stub. Both are former silent-skip paths
    closed by v0.7.3 AD1.

    We test two corrupt shapes:
    * Empty file — produces an "empty .eml" failed-stub.
    * Pure-binary garbage — produces a failed-stub naming missing
      headers/body."""
    # Empty .eml.
    empty = tmp_path / "empty.eml"
    empty.write_bytes(b"")
    results_empty = list(EmailMboxAdapter().ingest(str(empty)))
    assert len(results_empty) == 1
    assert results_empty[0].status == "failed"
    assert "empty" in results_empty[0].failure_reason.lower()

    # Garbage that looks like nothing — no colons, no headers, no body
    # structure. The Parser will accept it (it's permissive) but the
    # post-parse heuristic should reject it as not-an-email.
    garbage = tmp_path / "garbage.eml"
    garbage.write_bytes(b"\x00\x01\x02 not an email at all \x03\x04")
    results_garbage = list(EmailMboxAdapter().ingest(str(garbage)))
    assert len(results_garbage) == 1
    assert results_garbage[0].status == "failed"
    # Failure reason cites either a parse error or no-header heuristic.
    reason = results_garbage[0].failure_reason.lower()
    assert "rfc 2822" in reason or "no recognisable" in reason or "headers" in reason


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``.email_credentials.eml`` (matches credential glob) → can_handle
    False, ingest returns a failed-stub. Mirrors text-file's defense.

    The brief specifies ``.email_credentials.eml`` as the canonical
    test name — it matches the ``credentials.*`` glob in
    :data:`stdlib_simple_cluster._CREDENTIAL_DENY_GLOBS`."""
    p = tmp_path / ".email_credentials.eml"
    _write_eml(p, body="EMAIL_PASSWORD=hunter2\nIMAP_TOKEN=abc123")
    adapter = EmailMboxAdapter()
    assert adapter.can_handle(str(p)) is False
    # Direct ingest call must also refuse with a failed-stub
    # (defense-in-depth: ``can_handle`` may have been bypassed).
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


# ---------------------------------------------------------------------------
# Registry: the adapter registers in the right priority slot
# ---------------------------------------------------------------------------


def test_email_mbox_adapter_registered_before_text_file() -> None:
    """The email-mbox adapter must register before text-file in the
    registry. Otherwise text-file's UTF-8 sniff would claim a tiny
    ``.eml`` as one opaque blob, losing per-message structure (L0
    P2 "personal correspondence fragment" intent)."""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.email_mbox import (
        EmailMboxAdapter as EM,
    )
    from myco.ingestion.adapters.stdlib_simple_cluster import TextFileAdapter as TF

    adapters = list(all_adapters())
    em_idx = next((i for i, a in enumerate(adapters) if isinstance(a, EM)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert em_idx >= 0, "EmailMboxAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert em_idx < tf_idx, (
        f"EmailMboxAdapter (idx {em_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )


def test_oversize_eml_returns_failed_stub(tmp_path: Path, monkeypatch) -> None:
    """A .eml over the size cap → single failed-stub naming the cap.
    Bonus regression test parallel to chat-log's oversize coverage."""
    p = tmp_path / "huge.eml"
    _write_eml(p, body="x")
    monkeypatch.setattr(
        "myco.ingestion.adapters.email_mbox.DEFAULT_MAX_INGEST_BYTES", 8
    )
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_empty_mbox_returns_failed_stub(tmp_path: Path) -> None:
    """An empty (zero-message) mbox file returns a failed-stub
    naming the condition. ``mailbox.mbox`` is happy to open an empty
    file as a 0-message container — we explicitly catch that."""
    p = tmp_path / "empty.mbox"
    p.write_bytes(b"")
    results = list(EmailMboxAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "empty" in results[0].failure_reason.lower()
