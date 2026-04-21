"""Adapter for any UTF-8 readable text file.

This is the fallback adapter: it handles any file extension that no
more-specific adapter claims, as long as the file is decodable as
UTF-8. Code files (.py, .js, .ts, .go, .rs, .rb, .sh, .c, .cpp,
.java, .kt, .swift, .lua, .r, .sql, .tf, .toml, .ini, .cfg,
.dockerfile, makefile, etc.) all land here.

v0.5.8 security fixes (Lens 6 P0-SEC-4):
* Removed ``.env`` from the recognised-extension list. User-run
  ``myco eat --path ~/project`` used to suck the project's ``.env``
  (AWS keys, OpenAI keys, DB passwords) into plaintext raw notes.
  Now ``.env`` is treated as non-text by the extension check and
  additionally filename-banned below.
* Added a filename/glob denylist for credential-bearing files
  (``.env*``, ``id_rsa*``, ``*.pem``, ``*.key``, ``.npmrc``,
  ``.netrc``, ``.pypirc``, ``credentials*``, ``secrets*``,
  ``*.p12``, ``*.pfx``). ``can_handle`` returns False for any match.
* Added a size cap (``DEFAULT_MAX_INGEST_BYTES = 10 MB``) so a 5 GB
  file cannot OOM the process via ``read_text``. Files over the cap
  are reported as skipped rather than ingested.
"""

from __future__ import annotations

import fnmatch
from collections.abc import Sequence
from pathlib import Path

from myco.core.io_atomic import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult

#: Size ceiling for a single file to pass through this adapter.
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
        except OSError:
            return []
        if size > DEFAULT_MAX_INGEST_BYTES:
            return []
        if _is_credential_file(p.name):
            return []
        try:
            body = p.read_text(encoding="utf-8", errors="strict")
        except UnicodeDecodeError:
            return []
        lang = p.suffix.lstrip(".") or "text"
        # v0.5.8: normalise source path to POSIX separators (even on
        # Windows, where `str(p.resolve())` yields backslashes). The
        # rest of the graph/traverse machinery assumes POSIX separator
        # contract per graph.py::_rel.
        source = str(p.resolve()).replace("\\", "/")
        return [
            IngestResult(
                title=p.name,
                body=body,
                tags=[lang, "file"],
                source=source,
                metadata={"path": str(p), "size_bytes": size},
            )
        ]
