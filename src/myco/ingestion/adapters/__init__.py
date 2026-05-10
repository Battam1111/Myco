"""Ingestion adapter registry.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters" — the extension seam that lets ``myco eat --path`` /
``myco eat --url`` dispatch to format-specific readers without
baking their list into the core.

Built-in adapters are registered at import time. External adapters
can call :func:`register` to add themselves.

Import ordering matters: more specific adapters (PDF, HTML, URL)
are registered before the generic text-file adapter so
``find_adapter`` resolves the most specific handler first.
"""

from __future__ import annotations

from collections.abc import Sequence

from .protocol import Adapter, IngestResult

__all__ = [
    "Adapter",
    "IngestResult",
    "register",
    "find_adapter",
    "all_adapters",
    "handled_extensions",
]

_REGISTRY: list[Adapter] = []


def register(adapter: Adapter) -> None:
    """Add an adapter to the global registry."""
    _REGISTRY.append(adapter)


def find_adapter(target: str) -> Adapter | None:
    """Return the first registered adapter that can handle *target*,
    or ``None`` if none matches.
    """
    for a in _REGISTRY:
        if a.can_handle(target):
            return a
    return None


def all_adapters() -> Sequence[Adapter]:
    """Return the registered adapter list in registration order."""
    return list(_REGISTRY)


def handled_extensions() -> frozenset[str]:
    """Union of all registered adapter extensions. Used by ``forage``
    to decide which files to list.
    """
    exts: set[str] = set()
    for a in _REGISTRY:
        exts.update(a.extensions)
    return frozenset(exts)


# --- Auto-register built-in adapters (most-specific first) --------


def _try_register(cls_path: str) -> None:
    """Import *cls_path* (dot-separated), instantiate, register.
    Silently skip if optional deps are missing.
    """
    module_path, cls_name = cls_path.rsplit(".", 1)
    try:
        import importlib

        mod = importlib.import_module(module_path)
        cls = getattr(mod, cls_name)
        register(cls())
    except (ImportError, AttributeError):
        pass  # optional dep missing; adapter not available


_try_register("myco.ingestion.adapters.url_fetcher.UrlFetcher")
_try_register("myco.ingestion.adapters.pdf_reader.PdfReader")
_try_register("myco.ingestion.adapters.html_reader.HtmlReader")
_try_register("myco.ingestion.adapters.tabular.TabularReader")
# Chat-log must register before text-file: a ``.chat.md`` would
# otherwise match TextFileAdapter's broad ``.md`` claim and be
# ingested as a single opaque blob, losing turn structure (L0 P2
# "conversation fragment" intent).
_try_register("myco.ingestion.adapters.chat_log.ChatLogAdapter")
# Sqlite must register before text-file: a ``.db`` is binary and
# would be rejected by text-file's NUL-byte heuristic anyway, but
# being explicit avoids relying on that. ``.sqlite`` / ``.sqlite3``
# fall outside text-file's extension claim, so order is mostly a
# documentation aid for future maintainers — kept ahead so the
# specificity ladder reads top-down.
_try_register("myco.ingestion.adapters.sqlite.SqliteAdapter")
# Email/mbox must register before text-file: ``.eml`` and ``.mbox``
# are RFC 2822 / Unix-mailbox formats that the UTF-8 sniff in
# text-file would happily claim as one opaque blob, losing per-
# message granularity (L0 P2 "personal correspondence fragment"
# intent). Each ``.mbox`` message becomes one IngestResult, capped
# at MAX_MBOX_MESSAGES (500) per file. Stdlib-only (``email`` +
# ``mailbox`` + ``html.parser``) — no optional dep gate.
_try_register("myco.ingestion.adapters.email_mbox.EmailMboxAdapter")
# git-history must register before code_repo: when the user opts in
# via a working-tree marker file (``.git-history``), the path passed
# to ``find_adapter`` is the working tree itself — which code_repo
# would otherwise claim via its broad ``Path(target).is_dir()`` check.
# When the user passes ``.../.git`` directly, code_repo would also
# claim it (it's a directory) and emit hundreds of useless raw notes
# from the object store. Registering git-history first wins both.
_try_register("myco.ingestion.adapters.git_history.GitHistoryAdapter")
# v0.8.0 multimedia adapters (audio / image-OCR / video-frame). Each
# is gated behind the ``[multimedia]`` extras: module import stays
# stdlib-only (heavy deps lazy-imported inside ``ingest()``), so these
# always register successfully even when the extras aren't installed.
# Order ahead of code_repo + text_file: their extension claims
# (``.mp3``, ``.png``, ``.mp4``, etc.) are more specific than the
# generic text-file fallback, and code_repo is directory-scope so
# wouldn't claim individual media files anyway. Among themselves:
# audio → image_ocr → video_frames per the v0.8.0 craft, matching the
# size-cap ladder (100 MB → 50 MB → 500 MB) and the modality-
# decisiveness ladder (audio is mono-segment-rich, OCR is single-
# block, video is frame-sampled).
_try_register("myco.ingestion.adapters.audio.AudioAdapter")
_try_register("myco.ingestion.adapters.image_ocr.ImageOcrAdapter")
_try_register("myco.ingestion.adapters.video_frames.VideoFramesAdapter")
_try_register("myco.ingestion.adapters.code_repo.CodeRepoAdapter")
_try_register("myco.ingestion.adapters.text_file.TextFileAdapter")
