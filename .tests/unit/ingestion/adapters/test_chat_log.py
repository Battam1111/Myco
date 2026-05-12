"""Tests for the chat-log adapter (markdown + JSONL).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) — "conversation fragment" is
ingestible material, so a 5-turn export must produce 5 raw notes,
not 1 opaque blob.

These tests pin the contract for v0.7.4 chat-log support:

* ``can_handle`` — extension fast-path + content-sniff fallback +
  credential-glob denial + size cap.
* ``ingest`` — one IngestResult per turn (markdown + JSONL),
  failed-stub on every former silent-skip path (oversize, no
  headers, malformed JSON line, missing role/content fields,
  credential-bearing filename).
* Role normalisation — ``"USER"`` / ``"User"`` / ``"user"`` all
  normalise to ``"user"`` in the metadata frontmatter.
"""

from __future__ import annotations

import json
from pathlib import Path

from myco.ingestion.adapters.chat_log import ChatLogAdapter

# ---------------------------------------------------------------------------
# can_handle: extension fast-path + content-sniff + denials
# ---------------------------------------------------------------------------


def test_can_handle_markdown_chat_extension(tmp_path: Path) -> None:
    """``.chat.md`` is recognised via the extension fast-path."""
    p = tmp_path / "session.chat.md"
    p.write_text("## user:\nhi\n\n## assistant:\nhello\n", encoding="utf-8")
    assert ChatLogAdapter().can_handle(str(p)) is True


def test_can_handle_jsonl_chat_extension(tmp_path: Path) -> None:
    """``.chatlog.jsonl`` is recognised via the extension fast-path."""
    p = tmp_path / "session.chatlog.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "hi"}) + "\n",
        encoding="utf-8",
    )
    assert ChatLogAdapter().can_handle(str(p)) is True


def test_can_handle_md_content_sniff(tmp_path: Path) -> None:
    """A bare ``.md`` whose first 256 bytes contain ≥ 2 role headers
    is recognised via the content-sniff path. The user didn't have
    to rename the file to ``.chat.md`` — Myco picks up structure."""
    p = tmp_path / "transcript.md"
    p.write_text(
        "# Some Title\n\n"
        "## user:\nhello\n\n"
        "## assistant:\nhi back\n\n"
        "## user:\nthanks\n",
        encoding="utf-8",
    )
    assert ChatLogAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_plain_markdown(tmp_path: Path) -> None:
    """A regular ``.md`` (no chat structure in first 256 bytes) is
    NOT claimed — text-file falls through to handle it as one note."""
    p = tmp_path / "readme.md"
    p.write_text(
        "# Project Title\n\n"
        "Some prose explaining the project. No chat headers here.\n"
        "Another paragraph of regular markdown content.\n",
        encoding="utf-8",
    )
    assert ChatLogAdapter().can_handle(str(p)) is False


def test_can_handle_jsonl_content_sniff(tmp_path: Path) -> None:
    """A bare ``.jsonl`` whose first line has role+content is claimed."""
    p = tmp_path / "anthropic_export.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "ping"})
        + "\n"
        + json.dumps({"role": "assistant", "content": "pong"})
        + "\n",
        encoding="utf-8",
    )
    assert ChatLogAdapter().can_handle(str(p)) is True


def test_can_handle_rejects_non_chat_jsonl(tmp_path: Path) -> None:
    """A ``.jsonl`` whose first line is just data (no role/content
    keys) falls through to text-file."""
    p = tmp_path / "metrics.jsonl"
    p.write_text(
        json.dumps({"timestamp": 1234, "value": 42}) + "\n",
        encoding="utf-8",
    )
    assert ChatLogAdapter().can_handle(str(p)) is False


# ---------------------------------------------------------------------------
# ingest: one IngestResult per turn
# ---------------------------------------------------------------------------


def test_ingest_markdown_emits_one_result_per_turn(tmp_path: Path) -> None:
    """A 3-turn markdown chat → 3 IngestResults with role + turn_index."""
    p = tmp_path / "three.chat.md"
    p.write_text(
        "## user:\nfirst question\n\n"
        "## assistant:\nfirst answer\n\n"
        "## user:\nfollow up\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    assert [r.metadata["role"] for r in results] == ["user", "assistant", "user"]
    assert [r.metadata["turn_index"] for r in results] == [0, 1, 2]
    assert all(r.metadata["kind"] == "chat-turn" for r in results)
    assert all(r.metadata["source_file"].endswith("three.chat.md") for r in results)
    # Bodies are stripped of header + surrounding whitespace.
    assert results[0].body == "first question"
    assert results[1].body == "first answer"
    assert results[2].body == "follow up"


def test_ingest_jsonl_emits_one_result_per_line(tmp_path: Path) -> None:
    """A 5-line JSONL chat → 5 IngestResults."""
    p = tmp_path / "five.chatlog.jsonl"
    lines = [
        json.dumps({"role": "system", "content": "You are helpful."}),
        json.dumps({"role": "user", "content": "Q1"}),
        json.dumps({"role": "assistant", "content": "A1"}),
        json.dumps({"role": "user", "content": "Q2"}),
        json.dumps({"role": "assistant", "content": "A2"}),
    ]
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 5
    assert all(r.status == "ok" for r in results)
    assert [r.metadata["role"] for r in results] == [
        "system",
        "user",
        "assistant",
        "user",
        "assistant",
    ]
    assert [r.metadata["turn_index"] for r in results] == [0, 1, 2, 3, 4]
    assert results[0].body == "You are helpful."
    assert results[4].body == "A2"


def test_ingest_jsonl_skips_malformed_line_returns_failed_stub(
    tmp_path: Path,
) -> None:
    """1 valid + 1 malformed JSON line → 1 ok + 1 failed-stub.

    The failed-stub carries a concrete ``failure_reason`` referencing
    the line number so the operator can locate the bad row in the
    source. ``status="ok"`` results are not contaminated."""
    p = tmp_path / "mixed.chatlog.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "valid"}) + "\n" + "{this is not json\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 2
    assert results[0].status == "ok"
    assert results[0].body == "valid"
    assert results[1].status == "failed"
    assert "decode failed" in results[1].failure_reason
    assert "line 2" in results[1].failure_reason


def test_ingest_jsonl_missing_role_returns_failed_stub(tmp_path: Path) -> None:
    """A line that's valid JSON but missing the ``role`` key produces
    a failed-stub naming the missing field."""
    p = tmp_path / "no_role.chatlog.jsonl"
    p.write_text(
        json.dumps({"role": "user", "content": "good"})
        + "\n"
        + json.dumps({"content": "orphan"})
        + "\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 2
    assert results[0].status == "ok"
    assert results[1].status == "failed"
    assert "role" in results[1].failure_reason


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``.aws_credentials.chat.md`` → can_handle False, ingest emits
    a failed-stub if called directly. Mirrors text-file's defense."""
    p = tmp_path / ".aws_credentials.chat.md"
    p.write_text(
        "## user:\nAWS_SECRET_ACCESS_KEY=AKIA...\n",
        encoding="utf-8",
    )
    adapter = ChatLogAdapter()
    assert adapter.can_handle(str(p)) is False
    # Direct ingest call must also refuse with a failed-stub
    # (defense-in-depth: ``can_handle`` may have been bypassed).
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


def test_ingest_oversize_returns_failed(tmp_path: Path, monkeypatch) -> None:
    """A file over the size cap → single failed-stub naming the cap."""
    p = tmp_path / "huge.chat.md"
    p.write_text("## user:\nhi\n\n## assistant:\nyo\n", encoding="utf-8")
    monkeypatch.setattr("myco.ingestion.adapters.chat_log.DEFAULT_MAX_INGEST_BYTES", 4)
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_ingest_no_headers_returns_failed_stub(tmp_path: Path) -> None:
    """A ``.chat.md`` whose body has no recognisable headers (the
    user's export tool used some other format) → failed-stub
    explaining what shape was expected."""
    p = tmp_path / "no_headers.chat.md"
    p.write_text(
        "Some preamble.\nNo headers anywhere.\nJust prose.\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no recognisable role headers" in results[0].failure_reason


def test_role_normalization(tmp_path: Path) -> None:
    """``"USER"`` / ``"User"`` / ``"user"`` all normalise to ``"user"``
    in the IngestResult metadata. Same for assistant and system."""
    p = tmp_path / "casey.chatlog.jsonl"
    p.write_text(
        json.dumps({"role": "USER", "content": "yelling"})
        + "\n"
        + json.dumps({"role": "User", "content": "title-case"})
        + "\n"
        + json.dumps({"role": "user", "content": "lower"})
        + "\n"
        + json.dumps({"role": "ASSISTANT", "content": "loud bot"})
        + "\n"
        + json.dumps({"role": "System", "content": "mixed"})
        + "\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 5
    assert [r.metadata["role"] for r in results] == [
        "user",
        "user",
        "user",
        "assistant",
        "system",
    ]
    assert all(r.status == "ok" for r in results)


def test_role_normalization_markdown_bold_variant(tmp_path: Path) -> None:
    """The bold variant ``**user:**`` (no ``##`` prefix) is also a
    valid header, and case-insensitive role matching still applies."""
    p = tmp_path / "bold.chat.md"
    p.write_text(
        "**USER:**\nshouted prompt\n\n**Assistant:**\ncalm reply\n",
        encoding="utf-8",
    )
    results = list(ChatLogAdapter().ingest(str(p)))
    assert len(results) == 2
    assert [r.metadata["role"] for r in results] == ["user", "assistant"]
    assert results[0].body == "shouted prompt"
    assert results[1].body == "calm reply"


# ---------------------------------------------------------------------------
# Registry: the adapter is discoverable in priority order
# ---------------------------------------------------------------------------


def test_chat_log_adapter_registered_before_text_file() -> None:
    """The chat-log adapter must run before text-file in the registry,
    otherwise a ``.chat.md`` would be claimed by text-file's broad
    ``.md`` extension and ingested as a single opaque blob."""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.chat_log import ChatLogAdapter as CL
    from myco.ingestion.adapters.stdlib_simple_cluster import TextFileAdapter as TF

    adapters = list(all_adapters())
    cl_idx = next((i for i, a in enumerate(adapters) if isinstance(a, CL)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert cl_idx >= 0, "ChatLogAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert cl_idx < tf_idx, (
        f"ChatLogAdapter (idx {cl_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )
