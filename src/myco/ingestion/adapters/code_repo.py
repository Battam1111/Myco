"""Adapter for a directory containing code (a repo or a subtree).

Walks the directory, delegates each ingestible file to
:class:`TextFileAdapter`, and returns one ``IngestResult`` per file.
Respects ``.gitignore`` patterns if the ``pathspec`` library is
installed; otherwise falls back to a short hardcoded skip-list.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from .protocol import Adapter, IngestResult
from .text_file import TextFileAdapter

_ALWAYS_SKIP = {
    ".git", "__pycache__", "node_modules", ".venv", "venv",
    ".tox", ".mypy_cache", ".ruff_cache", ".pytest_cache",
    "dist", "build", ".eggs", "*.egg-info",
}

_MAX_FILES = 500


class CodeRepoAdapter(Adapter):
    def __init__(self) -> None:
        self._text = TextFileAdapter()

    @property
    def name(self) -> str:
        return "code-repo"

    @property
    def extensions(self) -> frozenset[str]:
        return frozenset()  # dispatches on directory, not extension

    def can_handle(self, target: str) -> bool:
        return Path(target).is_dir()

    def ingest(self, target: str) -> Sequence[IngestResult]:
        root = Path(target)
        gitignore_spec = self._load_gitignore(root)
        results: list[IngestResult] = []
        for path in sorted(root.rglob("*")):
            if len(results) >= _MAX_FILES:
                break
            if not path.is_file():
                continue
            if self._should_skip(path, root, gitignore_spec):
                continue
            if not self._text.can_handle(str(path)):
                continue
            for r in self._text.ingest(str(path)):
                r.tags.append("repo")
                r.source = f"{root.name}/{path.relative_to(root)}"
                results.append(r)
        return results

    @staticmethod
    def _should_skip(path: Path, root: Path, spec) -> bool:
        rel = path.relative_to(root)
        # Always-skip dirs
        for part in rel.parts:
            if part in _ALWAYS_SKIP or part.endswith(".egg-info"):
                return True
        # pathspec match (if available)
        if spec is not None:
            try:
                if spec.match_file(str(rel)):
                    return True
            except Exception:
                pass
        return False

    @staticmethod
    def _load_gitignore(root: Path):
        gi = root / ".gitignore"
        if not gi.exists():
            return None
        try:
            import pathspec
            return pathspec.PathSpec.from_lines(
                "gitwildmatch", gi.read_text(encoding="utf-8").splitlines()
            )
        except ImportError:
            return None
