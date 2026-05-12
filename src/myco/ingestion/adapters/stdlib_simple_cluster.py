"""Stdlib-simple ingestion adapter cluster (v0.8.8 merge).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters".

This module is the merged home of three pure-stdlib adapters that
previously lived in their own per-class files (``text_file.py``,
``code_repo.py``, ``tabular.py``). Cluster-merge follows the v0.8.8
substrate-wide consolidation policy (per L1 protocol.md, §R2 "one
module per dim" is an L3 organization choice — overrideable without a
molt). Section markers ``# === <AdapterName> — ...`` preserve
per-class review boundaries; git history holds the original per-file
state.

Adapters in this cluster:

* :class:`TextFileAdapter` — fallback for any UTF-8-decodable text
  file. Refuses credential-bearing names and files over the size cap.
* :class:`CodeRepoAdapter` — directory-scope walker that delegates to
  :class:`TextFileAdapter`. Honors ``.gitignore`` via ``pathspec``.
* :class:`TabularReader` — CSV / TSV / JSON / JSONL summarizer.

Shared module-level helpers (``_is_credential_file``,
``_CREDENTIAL_DENY_GLOBS``, ``_CODE_EXTS``, ``DEFAULT_MAX_INGEST_BYTES``,
``_posix``) are re-exported here because six sibling adapters
(``chat_log``, ``audio``, ``email_mbox``, ``image_ocr``,
``video_frames``, ``sqlite``) import ``_is_credential_file`` from this
module's surface.

v0.5.8 security floor (Lens 6 P0-SEC-4) is preserved verbatim:

* ``.env`` removed from recognised-extension list; credential-bearing
  filenames are denied regardless of extension or content.
* Size cap (``DEFAULT_MAX_INGEST_BYTES = 10 MB``) prevents OOM via
  ``read_text`` on attacker-planted large files.
* POSIX-normalised source paths so Windows backslash separators do
  not leak into the graph contract.
"""

from __future__ import annotations

import csv
import fnmatch
import io
import json
from collections.abc import Sequence
from pathlib import Path

from myco.core.io_cluster import DEFAULT_MAX_READ_BYTES, should_skip_dir

from .protocol import Adapter, IngestResult

# =========================================================================
# Shared module-level helpers (formerly text_file + tabular module-globals)
# =========================================================================

#: Size ceiling for a single file to pass through stdlib-simple adapters.
#: Mirrors :data:`myco.core.io_atomic.DEFAULT_MAX_READ_BYTES` (10 MB).
#: Files over this size are rejected by ``can_handle`` so ingestion
#: cannot be used as an OOM oracle on attacker-planted large files.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES

#: Filename patterns that are never ingested regardless of extension
#: or content-sniff. These are well-known credential-bearing files
#: that showed up in user ``.env``-in-repo scenarios.
_CREDENTIAL_DENY_GLOBS: frozenset[str] = frozenset(
    {
        ".env",
        ".env.*",
        "*.env",
        "id_rsa",
        "id_rsa.*",
        "id_dsa",
        "id_dsa.*",
        "id_ecdsa",
        "id_ecdsa.*",
        "id_ed25519",
        "id_ed25519.*",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
        ".npmrc",
        ".netrc",
        ".pypirc",
        "credentials",
        "credentials.*",
        ".aws_credentials",
        ".aws_credentials.*",
        "secrets",
        "secrets.*",
        ".secrets",
        ".secret",
    }
)


def _is_credential_file(name: str) -> bool:
    """Return True if ``name`` (basename only) matches any credential-
    bearing glob in :data:`_CREDENTIAL_DENY_GLOBS`.

    Matching is case-insensitive to catch ``.ENV`` etc. ``fnmatch``
    semantics: ``*`` matches any characters, ``?`` matches one.
    """
    lower = name.lower()
    return any(fnmatch.fnmatch(lower, glob) for glob in _CREDENTIAL_DENY_GLOBS)


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


# Common extensions that are almost certainly UTF-8 text.
# The adapter also tries any unlisted extension via a decode attempt.
# v0.5.8: ``.env`` removed per P0-SEC-4 (credential exfil via eat).
_CODE_EXTS = frozenset(
    {
        ".py",
        ".pyi",
        ".pyx",
        ".js",
        ".jsx",
        ".ts",
        ".tsx",
        ".mjs",
        ".cjs",
        ".go",
        ".rs",
        ".rb",
        ".sh",
        ".bash",
        ".zsh",
        ".fish",
        ".c",
        ".h",
        ".cpp",
        ".hpp",
        ".cc",
        ".cxx",
        ".java",
        ".kt",
        ".kts",
        ".scala",
        ".clj",
        ".cljs",
        ".swift",
        ".m",
        ".mm",
        ".lua",
        ".r",
        ".jl",
        ".zig",
        ".nim",
        ".v",
        ".d",
        ".sql",
        ".graphql",
        ".gql",
        ".tf",
        ".hcl",
        ".toml",
        ".ini",
        ".cfg",
        ".properties",
        ".xml",
        ".xsl",
        ".xsd",
        ".svg",
        ".css",
        ".scss",
        ".sass",
        ".less",
        ".md",
        ".markdown",
        ".txt",
        ".rst",
        ".adoc",
        ".org",
        ".yaml",
        ".yml",
        ".json",
        ".json5",
        ".jsonc",
        ".jsonl",
        ".log",
        ".conf",
        ".diff",
        ".patch",
        ".dockerfile",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".makefile",
    }
)


# =========================================================================
# === TextFileAdapter — formerly text_file.py (304 LOC)
# =========================================================================


class TextFileAdapter(Adapter):
    """Fallback adapter for UTF-8-decodable text files.

    Accepts any file whose extension appears in :data:`_CODE_EXTS` or
    whose first 512 bytes look like UTF-8 with no NUL byte. Refuses
    files matched by :data:`_CREDENTIAL_DENY_GLOBS` regardless of
    content, and refuses files over :data:`DEFAULT_MAX_INGEST_BYTES`
    regardless of extension.
    """

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
        # v0.5.8 P0-SEC-4: refuse credential-bearing files by name
        # regardless of extension or content. The last-resort
        # UTF-8-sniffer below would otherwise happily accept a
        # .env file as "text" and ingest OPENAI_API_KEY into a note.
        if _is_credential_file(p.name):
            return False
        # v0.5.8 P1-05 (Lens 16): refuse files over the ingest-size
        # cap so a multi-GB input cannot OOM the reader. `stat` is
        # a single syscall — cheaper than reading, so check first.
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        if p.suffix.lower() in _CODE_EXTS:
            return True
        if p.name.lower() in {
            "makefile",
            "dockerfile",
            "vagrantfile",
            "procfile",
            "gemfile",
            "rakefile",
            "cmakelists.txt",
            "license",
            "readme",
            "contributing",
            "changelog",
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
        # Belt + suspenders: re-check size cap at ingest (can_handle
        # may have been bypassed by a direct-call path).
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
                        f"text-file size cap exceeded: {size} > "
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
        lang = p.suffix.lstrip(".") or "text"
        # v0.5.8: normalise source path to POSIX separators (even on
        # Windows, where `str(p.resolve())` yields backslashes). The
        # rest of the graph/traverse machinery assumes POSIX separator
        # contract per graph.py::_rel.
        source = _posix(p)
        return [
            IngestResult(
                title=p.name,
                body=body,
                tags=[lang, "file"],
                source=source,
                metadata={"path": str(p), "size_bytes": size},
            )
        ]


# =========================================================================
# === CodeRepoAdapter — formerly code_repo.py (120 LOC)
# =========================================================================

_MAX_FILES = 500


class CodeRepoAdapter(Adapter):
    """Directory-scope adapter for a repo subtree.

    Walks ``target`` (a directory), delegates each ingestible file to
    :class:`TextFileAdapter`, and returns one :class:`IngestResult`
    per file. Honors ``.gitignore`` via ``pathspec`` when installed,
    falls back to a hardcoded skip list from
    :mod:`myco.core.skip_dirs` otherwise. Caps the result at
    :data:`_MAX_FILES`.
    """

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
                # v0.8.6 — POSIX-normalize the relative path so
                # ingested sources read identically on Windows (where
                # `Path.relative_to(...)` renders backslashes by default).
                r.source = f"{root.name}/{path.relative_to(root).as_posix()}"
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

            from myco.core.io_cluster import bounded_read_text

            return pathspec.PathSpec.from_lines(
                "gitwildmatch", bounded_read_text(gi).splitlines()
            )
        except ImportError:
            return None


# =========================================================================
# === TabularReader — formerly tabular.py (168 LOC)
# =========================================================================

_MAX_PREVIEW_ROWS = 10


class TabularReader(Adapter):
    """Adapter for CSV / TSV / JSON / JSONL data files.

    Emits one :class:`IngestResult` per file containing a summary
    (column names, row count) plus a preview of the first
    :data:`_MAX_PREVIEW_ROWS` rows. Refuses files over
    :data:`DEFAULT_MAX_INGEST_BYTES` at ``can_handle``.
    """

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
        return [
            IngestResult(
                title=p.stem,
                body="",
                source=_posix(p),
                status="failed",
                failure_reason=(
                    f"tabular adapter received unsupported suffix {suffix!r}; "
                    "expected .csv, .tsv, .json, or .jsonl"
                ),
            )
        ]

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
