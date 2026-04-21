"""Adapter for tabular data files (CSV, JSON, JSONL).

Uses only the Python standard library (``csv``, ``json``), so no
optional deps are needed. Produces a summary note: column names,
row count, first few rows.

v0.5.8: size cap + POSIX source normalization. Tabular corpora
from data-science workflows routinely hit multi-GB sizes; without
a cap, ``p.read_text`` would OOM before the preview-truncation
logic even runs.
"""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Sequence
from pathlib import Path

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

_MAX_PREVIEW_ROWS = 10

#: Size ceiling for a single tabular file (10 MB). Oversized files
#: are rejected by ``can_handle`` so ingestion cannot OOM the process.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


class TabularReader(Adapter):
    @property
    def name(self) -> str:
        return "tabular"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".csv", ".tsv", ".json", ".jsonl"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not (p.is_file() and p.suffix.lower() in self.extensions):
            return False
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        suffix = p.suffix.lower()
        if suffix in (".csv", ".tsv"):
            return self._ingest_csv(p, suffix)
        if suffix == ".jsonl":
            return self._ingest_jsonl(p)
        if suffix == ".json":
            return self._ingest_json(p)
        return []

    def _ingest_csv(self, p: Path, suffix: str) -> list[IngestResult]:
        delimiter = "\t" if suffix == ".tsv" else ","
        text = p.read_text(encoding="utf-8", errors="replace")
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)
        rows = list(reader)
        cols = reader.fieldnames or []
        preview = rows[:_MAX_PREVIEW_ROWS]
        lines = [
            f"Columns ({len(cols)}): {', '.join(cols)}",
            f"Rows: {len(rows)}",
            "",
            "Preview:",
        ]
        for row in preview:
            lines.append("  " + json.dumps(row, ensure_ascii=False))
        return [
            IngestResult(
                title=p.name,
                body="\n".join(lines),
                tags=["tabular", suffix.lstrip(".")],
                source=_posix(p),
                metadata={"columns": cols, "row_count": len(rows)},
            )
        ]

    def _ingest_jsonl(self, p: Path) -> list[IngestResult]:
        text = p.read_text(encoding="utf-8", errors="replace")
        objects = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                objects.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        preview = objects[:_MAX_PREVIEW_ROWS]
        lines = [
            f"Records: {len(objects)}",
            "",
            "Preview:",
        ]
        for obj in preview:
            lines.append("  " + json.dumps(obj, ensure_ascii=False))
        return [
            IngestResult(
                title=p.name,
                body="\n".join(lines),
                tags=["tabular", "jsonl"],
                source=_posix(p),
                metadata={"record_count": len(objects)},
            )
        ]

    def _ingest_json(self, p: Path) -> list[IngestResult]:
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [
                IngestResult(
                    title=p.name,
                    body=text[:2000],
                    tags=["json", "file"],
                    source=_posix(p),
                )
            ]
        body = json.dumps(data, indent=2, ensure_ascii=False)
        if len(body) > 5000:
            body = body[:5000] + "\n... (truncated)"
        return [
            IngestResult(
                title=p.name,
                body=body,
                tags=["json", "file"],
                source=_posix(p),
                metadata={"type": type(data).__name__},
            )
        ]
