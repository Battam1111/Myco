"""Adapter protocol for ingestion.

An adapter converts one external artifact (a file, URL, or directory)
into one or more ``IngestResult`` objects that ``eat`` writes as raw
notes. The protocol is deliberately thin: adapters do format
conversion, not judgment. L0 principle 2 says "no filter on what
enters"; adapters honor that by accepting anything they can decode,
without scoring or ranking.

Third-party adapters can subclass ``Adapter`` and call
``myco.ingestion.adapters.register()`` at import time.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Sequence


@dataclass
class IngestResult:
    """One unit of ingested content, ready to become a raw note.

    ``eat`` maps each IngestResult to one ``notes/raw/*.md`` file:
    title becomes the note slug, body becomes the note body, tags and
    source flow into frontmatter fields.
    """
    title: str
    body: str
    tags: list[str] = field(default_factory=list)
    source: str = ""
    metadata: dict = field(default_factory=dict)


class Adapter(ABC):
    """Base class for ingestion adapters."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable adapter name (e.g. ``"pdf"``, ``"code-repo"``)."""

    @property
    @abstractmethod
    def extensions(self) -> frozenset[str]:
        """File extensions this adapter handles (e.g. ``{".py", ".js"}``).

        Return an empty frozenset if the adapter uses non-extension
        dispatch (e.g. URL prefix, directory detection).
        """

    @abstractmethod
    def can_handle(self, target: str) -> bool:
        """Return True if this adapter can process *target*."""

    @abstractmethod
    def ingest(self, target: str) -> Sequence[IngestResult]:
        """Convert *target* into one or more ``IngestResult`` objects."""
