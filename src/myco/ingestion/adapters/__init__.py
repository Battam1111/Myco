"""Ingestion adapter registry.

Built-in adapters are registered at import time. External adapters
can call :func:`register` to add themselves.

Import ordering matters: more specific adapters (PDF, HTML, URL)
are registered before the generic text-file adapter so
``find_adapter`` resolves the most specific handler first.
"""
from __future__ import annotations

from typing import Sequence

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
_try_register("myco.ingestion.adapters.code_repo.CodeRepoAdapter")
_try_register("myco.ingestion.adapters.text_file.TextFileAdapter")
