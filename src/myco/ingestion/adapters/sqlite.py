"""Adapter for SQLite database files (``.sqlite``, ``.sqlite3``, ``.db``).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters". Realises L0 P2 (永恒吞噬): a SQLite DB is structured
record-storage, and the prior 7 adapters (text_file, html_reader,
pdf_reader, tabular, url_fetcher, code_repo, chat_log) treated a
``.db`` as either an opaque binary (rejected) or as text (rejected
on the NUL-byte heuristic). The SQLite adapter recognises row
boundaries and emits one :class:`IngestResult` per row of the
"primary table" (the table with the most rows that isn't a SQLite
system or migration table), so downstream digestion can score,
quote, or branch on a single record rather than the whole DB.

Detection is extension-only:

* ``.sqlite``, ``.sqlite3``, ``.db`` are claimed.
* Bare files without extension that *happen* to start with the
  SQLite magic header are NOT claimed — the v0.5.8 size + credential
  posture means we never sniff binary content.

Security posture mirrors :mod:`text_file` and :mod:`chat_log`:

* Reuses :data:`stdlib_simple_cluster._CREDENTIAL_DENY_GLOBS` (e.g. an attacker
  who renamed their AWS credentials to ``.aws_credentials.sqlite``
  cannot exfiltrate via ``myco eat --path``).
* Refuses files over :data:`DEFAULT_MAX_INGEST_BYTES` (10 MB) at
  ``can_handle`` so a 5 GB analytics DB cannot be used as an OOM
  oracle on the parser.
* Opens the DB in ``mode=ro`` URI mode so a malicious adapter call
  cannot ever write back to the user's database.
* Validates every table name against ``^[A-Za-z_][A-Za-z0-9_]*$``
  before interpolating it into a ``SELECT * FROM <name>`` — the
  stdlib ``sqlite3`` driver does not parameterise identifiers, so
  this regex is the only line of defence against an attacker-crafted
  schema with a malicious quoted-identifier table name.
* Caps emitted rows at :data:`_MAX_ROWS_PER_DB` (1000) so a DB with
  10M analytics rows degrades to "first 1000 + truncation flag",
  not OOM.
* On every former silent-skip path (oversize, missing file, decode
  error, no user tables, corrupt DB, sqlite ``DatabaseError``)
  returns a single failed-stub :class:`IngestResult` per the v0.7.3
  AD1-closure protocol.
"""

from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Sequence
from pathlib import Path

from myco.core.io_cluster import DEFAULT_MAX_READ_BYTES

from .protocol import Adapter, IngestResult
from .stdlib_simple_cluster import _is_credential_file

#: Size ceiling for a single SQLite file (10 MB). Mirrors
#: :data:`myco.core.io_atomic.DEFAULT_MAX_READ_BYTES` and the cap on
#: every other adapter, so attacker-planted multi-GB DBs cannot be
#: used as an OOM oracle on the parser.
DEFAULT_MAX_INGEST_BYTES: int = DEFAULT_MAX_READ_BYTES

#: Per-DB row cap. A 10M-row analytics DB ingested as 10M raw notes
#: would melt the substrate; we emit the first 1000 plus a final
#: failed-stub flagging the truncation so the operator can see what
#: was lost. The cap matches the spirit of
#: :data:`code_repo._MAX_FILES = 500` — a per-source ceiling that
#: keeps any single ingestion call bounded.
_MAX_ROWS_PER_DB: int = 1000

#: File extensions claimed by this adapter.
_SQLITE_EXTS: frozenset[str] = frozenset({".sqlite", ".sqlite3", ".db"})

#: Whitelist regex for table identifiers. Stdlib ``sqlite3`` does not
#: parameterise identifiers (only values), so any table name that
#: gets interpolated into ``SELECT * FROM <name>`` must first survive
#: this validator. Attacker-controlled DBs can carry tables named
#: ``"x; DROP TABLE users"`` (legal SQLite via quoted identifiers);
#: this regex rejects every such name before it reaches the cursor.
_SAFE_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

#: Tables we never enumerate. ``sqlite_*`` is the SQLite system
#: namespace (master schema, sequences, stats); ``alembic_version``
#: is a per-deployment migration cursor that's noise to ingest.
_EXCLUDED_TABLE_PREFIXES: tuple[str, ...] = ("sqlite_",)
_EXCLUDED_TABLE_NAMES: frozenset[str] = frozenset(
    {
        "alembic_version",
    }
)


def _posix(p: Path) -> str:
    """Normalise ``p.resolve()`` to POSIX separators (Lens 10 P1-C)."""
    return str(p.resolve()).replace("\\", "/")


def _is_excluded_table(name: str) -> bool:
    """Return True if ``name`` is a SQLite system or migration table.

    Excludes:

    * Anything starting with ``sqlite_`` (master schema, sequences,
      autoindex, stat tables).
    * The well-known migration tables (currently just
      ``alembic_version``; expand as new migration tools surface).
    """
    lower = name.lower()
    if any(lower.startswith(p) for p in _EXCLUDED_TABLE_PREFIXES):
        return True
    return lower in _EXCLUDED_TABLE_NAMES


def _open_readonly(path: Path) -> sqlite3.Connection:
    """Open ``path`` as a read-only SQLite connection.

    Uses the ``file:`` URI form with ``?mode=ro`` so any accidental
    DDL/DML in this adapter (or in a future maintainer's edit) is
    rejected by the driver rather than scribbling on the user's DB.
    POSIX-normalised so Windows backslash paths don't break the URI.
    """
    uri = f"file:{_posix(path)}?mode=ro"
    return sqlite3.connect(uri, uri=True)


def _list_user_tables(conn: sqlite3.Connection) -> list[str]:
    """Return the unsorted list of user table names.

    Filters ``sqlite_*`` and migration tables (see
    :func:`_is_excluded_table`) and rejects any table name that
    fails :data:`_SAFE_IDENT_RE` — an attacker-controlled DB can
    legally carry tables with quoted identifiers containing
    semicolons, spaces, or DDL keywords; we refuse to enumerate
    those because we cannot safely interpolate them into the
    later ``SELECT *`` query.
    """
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
    names: list[str] = []
    for (name,) in cursor.fetchall():
        if not isinstance(name, str):
            continue
        if _is_excluded_table(name):
            continue
        if not _SAFE_IDENT_RE.match(name):
            # Attacker-planted exotic name; refuse silently. The
            # ingest path may still emit a failed-stub if zero
            # tables survive this filter.
            continue
        names.append(name)
    return names


def _row_count(conn: sqlite3.Connection, table: str) -> int:
    """Return ``COUNT(*)`` for ``table``.

    Caller MUST have validated ``table`` against
    :data:`_SAFE_IDENT_RE` before invoking; this function trusts
    that contract and inserts the name directly into the query
    text. Any deviation from that contract is a programming error,
    not user input — so we do not re-validate here.
    """
    # Guard against caller breaking the contract. Belt + suspenders:
    # if a future refactor lets a non-validated name reach this
    # function, the regex check stops it before SQL execution.
    if not _SAFE_IDENT_RE.match(table):
        raise ValueError(f"unsafe table identifier: {table!r}")
    (count,) = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()
    return int(count)


def _detect_primary_key_column(conn: sqlite3.Connection, table: str) -> str | None:
    """Return the name of ``table``'s primary-key column, or ``None``.

    Uses ``PRAGMA table_info`` rather than the schema parser so we
    don't have to crack the user's CREATE TABLE syntax. Returns the
    first column flagged ``pk > 0`` (composite PKs collapse to the
    first part for our purposes — the synthetic ``rowid`` fallback
    in :meth:`SqliteAdapter._ingest_table` covers tables with no
    explicit PK).
    """
    if not _SAFE_IDENT_RE.match(table):
        return None
    rows = conn.execute(f'PRAGMA table_info("{table}")').fetchall()
    # PRAGMA table_info columns: (cid, name, type, notnull, dflt_value, pk)
    pk_columns = [r for r in rows if r[5] and r[5] > 0]
    if not pk_columns:
        return None
    pk_columns.sort(key=lambda r: r[5])  # composite-PK order = pk index
    return str(pk_columns[0][1])


class SqliteAdapter(Adapter):
    """Adapter for SQLite database files.

    Emits one :class:`IngestResult` per row of the database's
    "primary table" — the user table (excluding ``sqlite_*`` system
    tables and ``alembic_version`` migration markers) with the
    largest row count. Each result's ``metadata`` carries:

    * ``kind`` — always ``"sqlite-row"``
    * ``table`` — the primary-table name
    * ``row_index`` — 0-based ordinal of the row within the table
      (matches SELECT order; SQLite gives no guaranteed ordering
      without ORDER BY, so this is the cursor's natural-iteration
      position, sufficient for "Nth row of dump")
    * ``primary_key`` — value of the table's PRIMARY KEY column if
      one exists, otherwise the SQLite ``rowid`` (always present
      and unique within a table, even for tables with no explicit
      PK or for ``WITHOUT ROWID`` tables we don't claim — guarded
      by the regex check)
    * ``source_file`` — POSIX-normalised absolute path to the DB

    Refuses files matched by
    :data:`stdlib_simple_cluster._CREDENTIAL_DENY_GLOBS` (e.g.
    ``.aws_credentials.sqlite``) and files over
    :data:`DEFAULT_MAX_INGEST_BYTES`. Caps emitted rows per DB at
    :data:`_MAX_ROWS_PER_DB`; on overflow emits the first 1000 plus a
    final failed-stub flagging the truncation so the operator can
    see what was lost. Returns a single failed-stub on every former
    silent-skip path per the v0.7.3 AD1-closure protocol.
    """

    @property
    def name(self) -> str:
        return "sqlite"

    @property
    def extensions(self) -> frozenset[str]:
        return _SQLITE_EXTS

    def can_handle(self, target: str) -> bool:
        p = Path(target)
        if not p.is_file():
            return False
        if p.suffix.lower() not in _SQLITE_EXTS:
            return False
        # P0-SEC-4 parity with text_file: refuse credential-bearing
        # filenames regardless of extension. ``.aws_credentials.sqlite``
        # exists because users dump their boto3 cred cache as SQLite.
        if _is_credential_file(p.name):
            return False
        # Size cap before any content read.
        try:
            if p.stat().st_size > DEFAULT_MAX_INGEST_BYTES:
                return False
        except OSError:
            return False
        return True

    def ingest(self, target: str) -> Sequence[IngestResult]:
        p = Path(target)
        # Belt + suspenders: re-check the size cap and credential
        # name at ingest. ``can_handle`` may have been bypassed by a
        # direct-call path (third-party orchestrator, test fixture).
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
                        f"sqlite size cap exceeded: {size} > "
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
        # Normalise to POSIX separators on Windows (graph.py contract).
        source = _posix(p)
        try:
            conn = _open_readonly(p)
        except sqlite3.DatabaseError as exc:
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"sqlite open failed: {exc}",
                )
            ]
        try:
            return self._ingest_with_conn(conn=conn, path=p, source=source)
        except sqlite3.DatabaseError as exc:
            return [
                IngestResult(
                    title=p.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"sqlite read failed: {exc}",
                )
            ]
        finally:
            try:
                conn.close()
            except sqlite3.Error:
                pass

    # ---- internal helpers --------------------------------------------------

    def _ingest_with_conn(
        self, *, conn: sqlite3.Connection, path: Path, source: str
    ) -> list[IngestResult]:
        try:
            tables = _list_user_tables(conn)
        except sqlite3.DatabaseError as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"sqlite_master read failed: {exc}",
                )
            ]
        if not tables:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(
                        "sqlite db has no user tables "
                        f"(only system / migration tables): {path.name!r}"
                    ),
                )
            ]
        # Pick the table with the most rows. Stable tiebreak on name
        # so two tables with equal counts give a deterministic pick
        # (avoids flaky tests on a 2-table fixture with identical
        # row counts).
        try:
            counted = [(name, _row_count(conn, name)) for name in tables]
        except sqlite3.DatabaseError as exc:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=f"COUNT(*) failed: {exc}",
                )
            ]
        counted.sort(key=lambda nc: (-nc[1], nc[0]))
        primary_table, primary_count = counted[0]
        if primary_count == 0:
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(
                        f"sqlite db has user tables but all are empty: {path.name!r}"
                    ),
                )
            ]
        return self._ingest_table(
            conn=conn,
            table=primary_table,
            path=path,
            source=source,
        )

    def _ingest_table(
        self,
        *,
        conn: sqlite3.Connection,
        table: str,
        path: Path,
        source: str,
    ) -> list[IngestResult]:
        # Re-validate before SQL interpolation (defence in depth even
        # though the caller already filtered through _list_user_tables).
        if not _SAFE_IDENT_RE.match(table):
            return [
                IngestResult(
                    title=path.stem,
                    body="",
                    source=source,
                    status="failed",
                    failure_reason=(
                        f"unsafe table identifier reached ingest: {table!r}"
                    ),
                )
            ]
        pk_col = _detect_primary_key_column(conn, table)
        # ``rowid`` is always present unless the table is
        # ``WITHOUT ROWID``. SQLite quietly aliases an explicit
        # INTEGER PRIMARY KEY column to rowid, so selecting both in
        # the same query just gives us the same number twice — that's
        # fine and saves a branch.
        cursor = conn.execute(f'SELECT rowid, * FROM "{table}"')
        col_names = [d[0] for d in cursor.description]
        # description[0] is ``rowid`` we asked for; the rest are the
        # table's actual columns. Slice off the rowid name so the
        # body JSON shows only the user-visible columns.
        user_col_names = col_names[1:]
        results: list[IngestResult] = []
        for row_index, row in enumerate(cursor):
            if row_index >= _MAX_ROWS_PER_DB:
                results.append(
                    IngestResult(
                        title=f"{path.stem}-{table}-truncated",
                        body="",
                        source=source,
                        status="failed",
                        failure_reason=(
                            f"sqlite row cap exceeded: emitted first "
                            f"{_MAX_ROWS_PER_DB} rows of table {table!r}; "
                            "remaining rows skipped"
                        ),
                        metadata={
                            "kind": "sqlite-row-truncation",
                            "table": table,
                            "row_cap": _MAX_ROWS_PER_DB,
                            "source_file": source,
                        },
                    )
                )
                break
            rowid = row[0]
            user_values = row[1:]
            row_dict = dict(zip(user_col_names, user_values, strict=False))
            pk_value = row_dict.get(pk_col) if pk_col else rowid
            body = json.dumps(row_dict, indent=2, ensure_ascii=False, default=str)
            results.append(
                IngestResult(
                    title=f"{path.stem}-{table}-row-{row_index:04d}",
                    body=body,
                    tags=["sqlite", "sqlite-row", table],
                    source=source,
                    metadata={
                        "kind": "sqlite-row",
                        "table": table,
                        "row_index": row_index,
                        "primary_key": pk_value,
                        "source_file": source,
                    },
                )
            )
        return results
