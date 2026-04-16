"""Adapter for tabular data files (CSV, JSON, JSONL).

Uses only the Python standard library (``csv``, ``json``), so no
optional deps are needed. Produces a summary note: column names,
row count, first few rows.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
from typing import Sequence

from .protocol import Adapter, IngestResult

_MAX_PREVIEW_ROWS = 10


class TabularReader(Adapter):
    @property
    def name(self) -> str:
        return "tabular"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset({".csv", ".tsv", ".json", ".jsonl"})

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        return p.is_file() and p.suffix.lower() in self.extensions

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
        return [IngestResult(
            title=p.name,
            body="\n".join(lines),
            tags=["tabular", suffix.lstrip(".")],
            source=str(p.resolve()),
            metadata={"columns": cols, "row_count": len(rows)},
        )]

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
        return [IngestResult(
            title=p.name,
            body="\n".join(lines),
            tags=["tabular", "jsonl"],
            source=str(p.resolve()),
            metadata={"record_count": len(objects)},
        )]

    def _ingest_json(self, p: Path) -> list[IngestResult]:
        text = p.read_text(encoding="utf-8", errors="replace")
        try:
            data = json.loads(text)
        except json.JSONDecodeError:
            return [IngestResult(
                title=p.name,
                body=text[:2000],
                tags=["json", "file"],
                source=str(p.resolve()),
            )]
        body = json.dumps(data, indent=2, ensure_ascii=False)
        if len(body) > 5000:
            body = body[:5000] + "\n... (truncated)"
        return [IngestResult(
            title=p.name,
            body=body,
            tags=["json", "file"],
            source=str(p.resolve()),
            metadata={"type": type(data).__name__},
        )]
