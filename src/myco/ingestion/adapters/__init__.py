"""Ingestion adapter registry.

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters" — the extension seam that lets ``myco eat --path``
dispatch to format-specific readers without baking their list into
the core.

v0.8.8 max-aggressive: per owner directive "只保留最核心最逻辑部分",
the specialized adapters (chat_log, email_mbox, git_history, sqlite,
video_frames, pdf, html, url, audio, image_ocr) were excreted. Only
the stdlib-simple cluster (text-file + code-repo + tabular) ships in
core. Downstream substrates re-add specialty adapters by calling
``register()`` from a ``.myco/plugins/adapters/`` module.

Built-in adapters are registered at import time. External adapters
can call :func:`register` to add themselves.
"""

from __future__ import annotations

from collections.abc import Sequence

from .protocol import Adapter, IngestResult
from .stdlib_simple_cluster import (
    CodeRepoAdapter,
    TabularReader,
    TextFileAdapter,
)

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


# --- Auto-register built-in stdlib-simple adapters ----------------
# Specificity order: tabular (.csv/.json/.jsonl) before code_repo
# (directory) before text_file (UTF-8 fallback).
register(TabularReader())
register(CodeRepoAdapter())
register(TextFileAdapter())
