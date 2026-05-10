"""Adapter for conversation / chat-log files (markdown + JSONL).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬): "conversation fragment" is
explicitly named as ingestible material, but the prior 6 adapters
(html_reader, pdf_reader, tabular, text_file, url_fetcher,
code_repo) treated a transcript as one opaque blob. The chat-log
adapter recognises turn boundaries and emits one
:class:`IngestResult` per turn, so downstream digestion can score,
quote, or branch on a single utterance rather than a whole dialog.

Two on-disk formats are supported:

1. **Markdown chat-log** — a ``.md`` file with ``## user:`` /
   ``## assistant:`` / ``## system:`` headers between sections.
   Common in Claude / ChatGPT exports and hand-typed transcripts.
   Bold variants (``**user:**``, ``## **user:**``) are also
   accepted. Role match is case-insensitive.

2. **JSONL chat-log** — one JSON object per line with at least
   ``{"role": "user" | "assistant" | "system", "content": "..."}``
   fields. Anthropic API export format and many other tools.

Detection is two-tier:

* Extension fast-path: ``.chat.md``, ``.chatlog.md``,
  ``.conversation.md`` → markdown; ``.chatlog.jsonl``,
  ``.chat.jsonl``, ``.conversation.jsonl`` → JSONL.
* Content-sniff fallback for ``.md`` / ``.jsonl`` files without the
  chat-suffix: if the first ~200 chars of a ``.md`` contain ≥ 2
  role headers, treat as markdown chat. If the first parsable line
  of a ``.jsonl`` has both ``role`` and ``content`` keys, treat as
  JSONL chat. This lets users who didn't rename their export still
  get turn-level ingestion.

Security posture mirrors :mod:`text_file`:

* Reuses :data:`_CREDENTIAL_DENY_GLOBS` from
  :mod:`myco.ingestion.adapters.text_file` (an attacker who dumps
  ``.aws_credentials`` into a chat could otherwise exfiltrate via
  ``myco eat --path``).
* Refuses files over :data:`DEFAULT_MAX_INGEST_BYTES` (10 MB) at
  ``can_handle`` so a 5 GB log cannot OOM the parser.
* On every former silent-skip path (oversize, missing file, decode
  error, no recognisable structure, unparseable JSONL, missing
  role/content fields) returns a single failed-stub
  :class:`IngestResult` per the v0.7.3 AD1-closure protocol.
"""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from pathlib import Path

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult
from .text_file import _is_credential_file

#: Size ceiling for a single chat-log file (10 MB). Mirrors
#: :data:`myco.core.io_atomic.DEFAULT_MAX_READ_BYTES` and the cap on
#: every other adapter, so attacker-planted multi-GB transcripts
#: cannot be used as an OOM oracle on the parser.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES

#: Compound extensions that unambiguously declare a chat-log.
#: Ordered longest-first so ``.chatlog.md`` matches before ``.md``.
_MD_CHAT_SUFFIXES: tuple[str, ...] = (
    ".chat.md",
    ".chatlog.md",
    ".conversation.md",
)
_JSONL_CHAT_SUFFIXES: tuple[str, ...] = (
    ".chatlog.jsonl",
    ".chat.jsonl",
    ".conversation.jsonl",
)

#: Roles recognised in a turn header / JSONL entry. The protocol
#: matches the OpenAI / Anthropic chat-completion vocabulary; any
#: other role string is rejected at parse time.
_ALLOWED_ROLES: frozenset[str] = frozenset({"user", "assistant", "system"})

#: Regex for a markdown chat-log section header. Permits:
#: * ``## user``, ``## user:``, ``## USER``, ``## User:``
#: * ``## **user:**``, ``## **User:**`` (bold inside heading)
#: * ``**user:**``, ``**assistant:**`` (standalone bold line)
#:
#: Two branches separated by ``|``: branch A requires ``##`` (with
#: optional bold asterisks), branch B requires ``**`` (the standalone
#: bold form). Either way the role is captured in group 1, an
#: optional colon and trailing ``**`` follow. A bare un-decorated
#: ``user:`` line does NOT match — the brief specifies only the
#: ``##`` and ``**`` forms, so we stay strict to avoid claiming
#: prose that happens to contain ``user:`` on its own line.
#:
#: The pattern is anchored ``^`` / ``$`` in multiline mode so inline
#: mentions of ``user:`` mid-sentence do not trigger a turn break.
_HEADER_RE = re.compile(
    r"^\s*(?:##\s*\*{0,2}\s*|\*{2}\s*)(user|assistant|system)"
    r"\s*:?\s*\*{0,2}\s*$",
    re.IGNORECASE | re.MULTILINE,
)

#: How many bytes of a candidate ``.md`` to sniff for header density.
_SNIFF_BYTES: int = 256

#: Minimum role-header count in the sniff window for a content-sniff
#: claim. Two is the minimum for a "conversation" (one turn could be
#: a heading in regular prose; two argues structure).
_SNIFF_MIN_HEADERS: int = 2


def _normalise_role(role: object) -> str | None:
    """Return the canonical lowercase role, or ``None`` if invalid.

    Accepts any case (``"USER"``, ``"User"``, ``"user"`` all → ``"user"``)
    and tolerates surrounding whitespace. Rejects roles not in
    :data:`_ALLOWED_ROLES` (e.g. OpenAI's ``"function"`` /
    ``"tool"``) — chat-log adapter is intentionally limited to the
    three-role conversational shape.
    """
    if not isinstance(role, str):
        return None
    norm = role.strip().lower()
    if norm in _ALLOWED_ROLES:
        return norm
    return None


def _has_md_chat_extension(name: str) -> bool:
    """Return True if ``name`` ends with a markdown chat-log suffix."""
    lower = name.lower()
    return any(lower.endswith(suf) for suf in _MD_CHAT_SUFFIXES)


def _has_jsonl_chat_extension(name: str) -> bool:
    """Return True if ``name`` ends with a JSONL chat-log suffix."""
    lower = name.lower()
    return any(lower.endswith(suf) for suf in _JSONL_CHAT_SUFFIXES)


def _md_content_sniff(path: Path) -> bool:
    """Return True if the first :data:`_SNIFF_BYTES` of ``path`` look
    like a markdown chat-log (≥ :data:`_SNIFF_MIN_HEADERS` role
    headers).

    Reads only a small chunk to keep ``can_handle`` cheap; a real
    chat-log will have at least two headers within the first few
    hundred bytes (the opening turn pair). Errors during read are
    swallowed — if we can't sniff, we don't claim.
    """
    try:
        sample = path.read_bytes()[:_SNIFF_BYTES]
        text = sample.decode("utf-8", errors="strict")
    except (UnicodeDecodeError, OSError):
        return False
    return len(_HEADER_RE.findall(text)) >= _SNIFF_MIN_HEADERS


def _jsonl_content_sniff(path: Path) -> bool:
    """Return True if ``path``'s first non-blank line parses as a
    JSON object with both ``role`` and ``content`` keys (and a valid
    role value).

    A single line is enough: if line 1 doesn't smell like a chat
    record, the whole file isn't ours. Errors fall through to
    False — we never raise out of ``can_handle``.
    """
    try:
        with path.open("r", encoding="utf-8", errors="strict") as fp:
            for raw in fp:
                line = raw.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    return False
                if not isinstance(obj, dict):
                    return False
                if "role" not in obj or "content" not in obj:
                    return False
                return _normalise_role(obj["role"]) is not None
    except (UnicodeDecodeError, OSError):
        return False
    return False


def _parse_markdown_turns(body: str) -> list[tuple[str, str]] | None:
    """Split a markdown chat-log body into ``(role, content)`` pairs.

    The split happens at every header line that matches
    :data:`_HEADER_RE`; the role is the captured group, the content
    is everything until the next header (or end-of-file), with
    surrounding whitespace stripped.

    Pre-header preamble (text before the first header) is discarded —
    it's typically an export tool's title block. If the body has no
    headers at all returns ``None``; the caller emits a failed-stub
    IngestResult per the v0.7.3 AD1 mechanical/HIGH discipline.
    """
    matches = list(_HEADER_RE.finditer(body))
    if not matches:
        return None
    turns: list[tuple[str, str]] = []
    for idx, m in enumerate(matches):
        role = m.group(1).lower()
        start = m.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        content = body[start:end].strip()
        turns.append((role, content))
    return turns


class ChatLogAdapter(Adapter):
    """Adapter for markdown / JSONL chat-log files.

    Emits one :class:`IngestResult` per turn. Each result's
    ``metadata`` carries:

    * ``kind`` — always ``"chat-turn"``
    * ``role`` — ``"user"`` | ``"assistant"`` | ``"system"``
    * ``turn_index`` — 0-based index of the turn within the file
    * ``source_file`` — POSIX-normalised absolute path to the source

    Refuses files matched by :data:`text_file._CREDENTIAL_DENY_GLOBS`
    (e.g. ``.aws_credentials.chat.md``) and files over
    :data:`DEFAULT_MAX_INGEST_BYTES`. Returns a single failed-stub
    on every former silent-skip path per the v0.7.3 AD1-closure
    protocol.
    """

    @property
    def name(self) -> str:
        return "chat-log"

    @property
    def extensions(self) -> frozenset[str]:
        # The compound suffixes (e.g. ``.chat.md``) aren't a single
        # ``Path.suffix`` — ``Path("x.chat.md").suffix == ".md"``. We
        # surface the leaf extensions here so :func:`forage` lists
        # candidate files; ``can_handle`` does the precise matching.
        return frozenset({".md", ".jsonl"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not p.is_file():
            return False
        # P0-SEC-4 parity with text_file: refuse credential-bearing
        # filenames regardless of extension. A user who pastes their
        # ``.aws_credentials`` into a markdown chat dump and names the
        # file ``.aws_credentials.chat.md`` would otherwise exfiltrate
        # one IngestResult per "turn" of credential.
        if _is_credential_file(p.name):
            return False
        # Size cap before any content read.
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        name = p.name
        # Fast path: explicit chat-log extension.
        if _has_md_chat_extension(name) or _has_jsonl_chat_extension(name):
            return True
        # Sniff path: a generic ``.md`` with chat structure, or a
        # generic ``.jsonl`` whose first line is a chat record.
        suffix = p.suffix.lower()
        if suffix == ".md":
            return _md_content_sniff(p)
        if suffix == ".jsonl":
            return _jsonl_content_sniff(p)
        return False

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check the size cap and credential
        # name at ingest. ``can_handle`` may have been bypassed by a
        # direct-call path (third-party orchestrator, test fixture).
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
                        f"chat-log size cap exceeded: {size} > "
                        f"{DEFAULT_MAX_INGEST_BYTES} bytes"
                    ),
                )
            ]
        if _is_credential_file(p.name):
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
        try:
            body = p.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=str(p),
                    status="failed",
                    failure_reason=f"utf-8 decode failed: {exc}",
                )
            ]
        # Normalise to POSIX separators on Windows (graph.py contract).
        source = str(p.resolve()).replace("\\", "/")
        # Dispatch on declared/sniffed format.
        if _has_jsonl_chat_extension(p.name) or (
            p.suffix.lower() == ".jsonl" and _jsonl_content_sniff(p)
        ):
            return self._ingest_jsonl(body=body, path=p, source=source)
        return self._ingest_markdown(body=body, path=p, source=source)

    # ---- format-specific parsers -------------------------------------------

    @staticmethod
    def _ingest_markdown(
        *, body: str, path: Path, source: str
    ) -> Sequence[IngestResult]:
        turns = _parse_markdown_turns(body)
        if turns is None or not turns:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(
                        "no recognisable role headers in markdown chat-log "
                        f"(expected '## user:' / '## assistant:' / "
                        f"'## system:' or '**user:**' lines): {path.name!r}"
                    ),
                )
            ]
        results: list[IngestResult] = []
        for idx, (role, content) in enumerate(turns):
            results.append(
                IngestResult(
                    title=f"{path.stem}-turn-{idx:03d}-{role}",
                    body=content,
                    tags=["chat-log", "chat-turn", role],
                    source=source,
                    metadata={
                        "kind": "chat-turn",
                        "role": role,
                        "turn_index": idx,
                        "source_file": source,
                    },
                )
            )
        return results

    @staticmethod
    def _ingest_jsonl(*, body: str, path: Path, source: str) -> Sequence[IngestResult]:
        results: list[IngestResult] = []
        # ``turn_index`` advances per logical entry (whether ok or
        # failed). Blank lines do NOT advance the index — they're
        # transport noise, not turns.
        turn_index = 0
        for line_no, raw in enumerate(body.splitlines(), start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                results.append(
                    IngestResult(
                        title=f"{path.stem}-turn-{turn_index:03d}-malformed",
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=(
                            f"jsonl decode failed at line {line_no}: {exc}"
                        ),
                        metadata={
                            "kind": "chat-turn",
                            "turn_index": turn_index,
                            "source_file": source,
                            "line_number": line_no,
                        },
                    )
                )
                turn_index += 1
                continue
            if not isinstance(obj, dict):
                results.append(
                    IngestResult(
                        title=f"{path.stem}-turn-{turn_index:03d}-malformed",
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=(
                            f"jsonl line {line_no} is not a JSON object "
                            f"(got {type(obj).__name__})"
                        ),
                        metadata={
                            "kind": "chat-turn",
                            "turn_index": turn_index,
                            "source_file": source,
                            "line_number": line_no,
                        },
                    )
                )
                turn_index += 1
                continue
            role = _normalise_role(obj.get("role"))
            content = obj.get("content")
            if role is None or not isinstance(content, str):
                missing: list[str] = []
                if role is None:
                    missing.append("role")
                if not isinstance(content, str):
                    missing.append("content")
                results.append(
                    IngestResult(
                        title=f"{path.stem}-turn-{turn_index:03d}-malformed",
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=(
                            f"jsonl line {line_no} missing/invalid fields: "
                            f"{', '.join(missing)}"
                        ),
                        metadata={
                            "kind": "chat-turn",
                            "turn_index": turn_index,
                            "source_file": source,
                            "line_number": line_no,
                        },
                    )
                )
                turn_index += 1
                continue
            results.append(
                IngestResult(
                    title=f"{path.stem}-turn-{turn_index:03d}-{role}",
                    body=content,
                    tags=["chat-log", "chat-turn", role],
                    source=source,
                    metadata={
                        "kind": "chat-turn",
                        "role": role,
                        "turn_index": turn_index,
                        "source_file": source,
                        "line_number": line_no,
                    },
                )
            )
            turn_index += 1
        if not results:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(
                        f"jsonl chat-log has no parseable lines: {path.name!r}"
                    ),
                )
            ]
        return results
