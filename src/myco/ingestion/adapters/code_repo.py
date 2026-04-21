"""Adapter for a directory containing code (a repo or a subtree).

Walks the directory, delegates each ingestible file to
:class:`TextFileAdapter`, and returns one ``IngestResult`` per file.
Respects ``.gitignore`` patterns if the ``pathspec`` library is
installed; otherwise falls back to a short hardcoded skip-list.

v0.5.8: the always-skip directory list now delegates to
``myco.core.skip_dirs`` so every walker in Myco (graph, forage,
sense, MP1) shares the same set. Previously three overlapping lists
diverged; adding a new cache dir required 3 PRs.

.gitignore matching now uses ``rel.as_posix()`` so Windows users
(with backslash rel paths) get the same semantics as POSIX users.
Previously ``spec.match_file("notes\\temp\\x.md")`` returned False
for rule ``notes/temp/``, silently ingesting files the user's
.gitignore excluded.
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from myco.core.skip_dirs import should_skip_dir

from .protocol import Adapter, IngestResult
from .text_file import TextFileAdapter

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
        # v0.5.8: delegate to the canonical skip-dirs module so every
        # walker in Myco sees the same set (graph_src, forage, sense,
        # MP1, this adapter — previously four divergent lists).
        for part in rel.parts:
            if should_skip_dir(part):
                return True
        # pathspec match (if available). v0.5.8 P1-B fix: pass the
        # POSIX form of the relative path. pathspec's gitwildmatch
        # semantics expect forward slashes; a Windows backslash path
        # silently fails to match rules like ``notes/temp/``, which
        # caused the repo's own .gitignore to be ignored on Windows
        # (credential files slipped through).
        if spec is not None:
            try:
                if spec.match_file(rel.as_posix()):
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
