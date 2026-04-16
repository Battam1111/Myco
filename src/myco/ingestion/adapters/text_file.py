"""Adapter for any UTF-8 readable text file.

This is the fallback adapter: it handles any file extension that no
more-specific adapter claims, as long as the file is decodable as
UTF-8. Code files (.py, .js, .ts, .go, .rs, .rb, .sh, .c, .cpp,
.java, .kt, .swift, .lua, .r, .sql, .tf, .toml, .ini, .cfg, .env,
.dockerfile, makefile, etc.) all land here.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .protocol import Adapter, IngestResult

# Common extensions that are almost certainly UTF-8 text.
# The adapter also tries any unlisted extension via a decode attempt.
_CODE_EXTS = frozenset({
    ".py", ".pyi", ".pyx",
    ".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs",
    ".go", ".rs", ".rb", ".sh", ".bash", ".zsh", ".fish",
    ".c", ".h", ".cpp", ".hpp", ".cc", ".cxx",
    ".java", ".kt", ".kts", ".scala", ".clj", ".cljs",
    ".swift", ".m", ".mm",
    ".lua", ".r", ".jl", ".zig", ".nim", ".v", ".d",
    ".sql", ".graphql", ".gql",
    ".tf", ".hcl",
    ".toml", ".ini", ".cfg", ".env", ".properties",
    ".xml", ".xsl", ".xsd", ".svg",
    ".css", ".scss", ".sass", ".less",
    ".md", ".markdown", ".txt", ".rst", ".adoc", ".org",
    ".yaml", ".yml", ".json", ".json5", ".jsonc", ".jsonl",
    ".log", ".conf", ".diff", ".patch",
    ".dockerfile",
    ".gitignore", ".gitattributes", ".editorconfig",
    ".makefile",
})


class TextFileAdapter(Adapter):
    @property
    def name(self) -> str:
        return "text-file"

    @property
    def extensions(self) -> frozenset[str]:
        return _CODE_EXTS

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() in _CODE_EXTS:
            return True
        if p.name.lower() in {
            "makefile", "dockerfile", "vagrantfile", "procfile",
            "gemfile", "rakefile", "cmakelists.txt", "license",
            "readme", "contributing", "changelog",
        }:
            return True
        # Last resort: read a small chunk, reject if it contains null
        # bytes (classic binary-detection heuristic) or fails UTF-8.
        try:
            sample = p.read_bytes()[:512]
            if b"\x00" in sample:
                return False
            sample.decode("utf-8", errors="strict")
            return True
        except (UnicodeDecodeError, OSError):
            return False

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        try:
            body = p.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            return []
        lang = p.suffix.lstrip(".") or "text"
        return [IngestResult(
            title=p.name,
            body=body,
            tags=[lang, "file"],
            source=str(p.resolve()),
            metadata={"path": str(p), "size_bytes": p.stat().st_size},
        )]
