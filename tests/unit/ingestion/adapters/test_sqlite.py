"""Tests for the SQLite adapter (``.sqlite`` / ``.sqlite3`` / ``.db``).

Governing doctrine: ``docs/architecture/L2_DOCTRINE/ingestion.md``
§ "Adapters", and L0 P2 (永恒吞噬) — a SQLite database is structured
record-storage, so a 50-row table must produce 50 raw notes, not 1
opaque binary blob (or, worse, a silent skip).

These tests pin the contract for the v0.7.4 SQLite adapter (the 8th
built-in adapter):

* ``can_handle`` — extension claim (``.sqlite`` / ``.sqlite3`` /
  ``.db``) + credential-glob denial + size cap.
* ``ingest`` — one IngestResult per row of the largest user table,
  excluding ``sqlite_*`` system tables and ``alembic_version``
  migration markers; failed-stub on every former silent-skip path
  (oversize, empty DB, no user tables, corrupt DB, credential
  filename, row-count overflow).
* Defensive validation — table names that don't match the safe-
  identifier regex are filtered before any SQL interpolation.
* Read-only mode — the connection URI is ``?mode=ro`` so even a
  bug in the adapter cannot mutate the user's DB.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

from myco.ingestion.adapters.sqlite import SqliteAdapter

# ---------------------------------------------------------------------------
# can_handle: extension fast-path + credential / size denials
# ---------------------------------------------------------------------------


def _make_db(path: Path, sql: str) -> Path:
    """Create a SQLite DB at ``path``, run ``sql``, and return the path."""
    conn = sqlite3.connect(str(path))
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
    return path


def test_can_handle_sqlite_extension(tmp_path: Path) -> None:
    """All three canonical extensions are recognised."""
    adapter = SqliteAdapter()
    for ext in (".sqlite", ".sqlite3", ".db"):
        p = _make_db(
            tmp_path / f"sample{ext}",
            "CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT); "
            "INSERT INTO t (v) VALUES ('a');",
        )
        assert adapter.can_handle(str(p)) is True, f"failed for ext {ext!r}"


def test_can_handle_rejects_non_sqlite(tmp_path: Path) -> None:
    """A regular ``.txt`` / ``.md`` / ``.csv`` must NOT be claimed."""
    adapter = SqliteAdapter()
    for name in ("plain.txt", "doc.md", "data.csv", "noext"):
        p = tmp_path / name
        p.write_text("hello world", encoding="utf-8")
        assert adapter.can_handle(str(p)) is False, f"unexpected claim: {name!r}"
    # A directory with a sqlite-looking name must also be rejected.
    d = tmp_path / "fake.sqlite"
    d.mkdir()
    assert adapter.can_handle(str(d)) is False


# ---------------------------------------------------------------------------
# ingest: one IngestResult per row of the primary table
# ---------------------------------------------------------------------------


def test_ingest_simple_2col_table_emits_one_result_per_row(tmp_path: Path) -> None:
    """A 3-row 2-column table → 3 IngestResults with row_index 0..2."""
    p = _make_db(
        tmp_path / "simple.sqlite",
        """
        CREATE TABLE notes (id INTEGER PRIMARY KEY, body TEXT);
        INSERT INTO notes (body) VALUES ('first');
        INSERT INTO notes (body) VALUES ('second');
        INSERT INTO notes (body) VALUES ('third');
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 3
    assert all(r.status == "ok" for r in results)
    assert all(r.metadata["kind"] == "sqlite-row" for r in results)
    assert all(r.metadata["table"] == "notes" for r in results)
    assert [r.metadata["row_index"] for r in results] == [0, 1, 2]
    # Bodies are pretty-printed JSON containing column→value mapping
    # for the user-visible columns (rowid is not in the body).
    assert "first" in results[0].body
    assert "second" in results[1].body
    assert "third" in results[2].body
    assert "rowid" not in results[0].body  # rowid stays in metadata only


def test_ingest_picks_largest_table_when_multiple_present(tmp_path: Path) -> None:
    """When multiple user tables exist, the one with the most rows wins."""
    p = _make_db(
        tmp_path / "multi.sqlite",
        """
        CREATE TABLE small (id INTEGER PRIMARY KEY, v TEXT);
        INSERT INTO small (v) VALUES ('a');
        INSERT INTO small (v) VALUES ('b');
        CREATE TABLE big (id INTEGER PRIMARY KEY, v TEXT);
        INSERT INTO big (v) VALUES ('1');
        INSERT INTO big (v) VALUES ('2');
        INSERT INTO big (v) VALUES ('3');
        INSERT INTO big (v) VALUES ('4');
        INSERT INTO big (v) VALUES ('5');
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 5  # the larger table only
    assert all(r.metadata["table"] == "big" for r in results)


def test_ingest_empty_db_returns_failed_stub(tmp_path: Path) -> None:
    """A DB with no user tables (only schema, all empty) → failed-stub."""
    # Empty DB: just create the file with sqlite3 connection but no tables.
    p = tmp_path / "empty.sqlite"
    conn = sqlite3.connect(str(p))
    conn.close()
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "no user tables" in results[0].failure_reason


def test_ingest_corrupt_db_returns_failed_stub(tmp_path: Path) -> None:
    """A ``.sqlite`` file whose bytes are random garbage → failed-stub."""
    p = tmp_path / "corrupt.sqlite"
    # Write binary garbage that's NOT a valid SQLite header.
    p.write_bytes(b"\x00\xff\xfe\x00not a real sqlite db\x42\x42\x42" * 32)
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    # The driver may report "file is not a database" on open or on first
    # query; either way the failure_reason mentions sqlite.
    assert "sqlite" in results[0].failure_reason.lower()


def test_ingest_excludes_sqlite_master_tables(tmp_path: Path) -> None:
    """``sqlite_*`` system tables must not be picked as the primary table.

    Even if a user table has fewer rows than ``sqlite_sequence`` /
    ``sqlite_stat1``, the user table wins because the system tables
    are filtered before the count comparison."""
    p = _make_db(
        tmp_path / "with_sys.sqlite",
        # AUTOINCREMENT triggers sqlite_sequence creation; ANALYZE
        # populates sqlite_stat1 (best-effort — not all builds emit it).
        """
        CREATE TABLE userdata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT
        );
        INSERT INTO userdata (label) VALUES ('only-row');
        ANALYZE;
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "ok"
    assert results[0].metadata["table"] == "userdata"
    # No result should reference a sqlite_* system table.
    for r in results:
        assert not r.metadata.get("table", "").lower().startswith("sqlite_")


def test_ingest_excludes_alembic_version_table(tmp_path: Path) -> None:
    """``alembic_version`` is a migration cursor and must be excluded
    even if it has more rows than the real user table."""
    p = _make_db(
        tmp_path / "with_alembic.sqlite",
        """
        CREATE TABLE alembic_version (version_num VARCHAR(32) NOT NULL);
        INSERT INTO alembic_version (version_num) VALUES ('a1');
        INSERT INTO alembic_version (version_num) VALUES ('a2');
        INSERT INTO alembic_version (version_num) VALUES ('a3');
        CREATE TABLE app_data (id INTEGER PRIMARY KEY, name TEXT);
        INSERT INTO app_data (name) VALUES ('x');
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 1
    assert results[0].metadata["table"] == "app_data"
    for r in results:
        assert r.metadata.get("table") != "alembic_version"


def test_ingest_truncates_at_1000_rows_emits_final_failed_stub(
    tmp_path: Path, monkeypatch
) -> None:
    """A DB with > _MAX_ROWS_PER_DB rows emits cap rows + 1 failed-stub.

    We monkeypatch the cap down to 5 so the test runs fast — the
    truncation logic itself is independent of the constant value."""
    monkeypatch.setattr("myco.ingestion.adapters.sqlite._MAX_ROWS_PER_DB", 5)
    # Insert 12 rows; cap is 5 → expect 5 ok + 1 failed-stub.
    inserts = "\n".join(f"INSERT INTO big (v) VALUES ('row{i}');" for i in range(12))
    p = _make_db(
        tmp_path / "huge.sqlite",
        f"""
        CREATE TABLE big (id INTEGER PRIMARY KEY, v TEXT);
        {inserts}
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 6
    ok_results = [r for r in results if r.status == "ok"]
    failed_results = [r for r in results if r.status == "failed"]
    assert len(ok_results) == 5
    assert len(failed_results) == 1
    assert "row cap" in failed_results[0].failure_reason
    assert "5" in failed_results[0].failure_reason
    # The truncation stub keeps the table name in metadata so an
    # operator scanning stderr can locate the source.
    assert failed_results[0].metadata.get("table") == "big"


def test_ingest_credential_file_blocked(tmp_path: Path) -> None:
    """``.aws_credentials.sqlite`` → can_handle False, ingest emits a
    failed-stub if called directly. Mirrors text-file's defense."""
    p = _make_db(
        tmp_path / ".aws_credentials.sqlite",
        """
        CREATE TABLE creds (id INTEGER PRIMARY KEY, key TEXT, secret TEXT);
        INSERT INTO creds (key, secret) VALUES ('AKIA...', 'XXXX');
        """,
    )
    adapter = SqliteAdapter()
    assert adapter.can_handle(str(p)) is False
    # Direct ingest call must also refuse with a failed-stub
    # (defense-in-depth: ``can_handle`` may have been bypassed).
    direct = list(adapter.ingest(str(p)))
    assert len(direct) == 1
    assert direct[0].status == "failed"
    assert "credential" in direct[0].failure_reason


def test_ingest_oversize_returns_failed_stub(tmp_path: Path, monkeypatch) -> None:
    """A DB over the size cap → single failed-stub naming the cap."""
    p = _make_db(
        tmp_path / "small.sqlite",
        "CREATE TABLE t (id INTEGER PRIMARY KEY, v TEXT); "
        "INSERT INTO t (v) VALUES ('hi');",
    )
    # Force the cap below the file's actual size so even a tiny DB
    # trips the oversize path. SQLite always allocates ≥ 4 KiB.
    monkeypatch.setattr("myco.ingestion.adapters.sqlite.DEFAULT_MAX_INGEST_BYTES", 4)
    adapter = SqliteAdapter()
    # can_handle must reject before any open attempt.
    assert adapter.can_handle(str(p)) is False
    # Direct ingest call must also refuse with a failed-stub.
    results = list(adapter.ingest(str(p)))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_ingest_primary_key_in_frontmatter(tmp_path: Path) -> None:
    """A table with an explicit named PRIMARY KEY column → each
    IngestResult's metadata.primary_key holds the row's PK value
    (not the rowid alias) so downstream consumers can dedupe."""
    p = _make_db(
        tmp_path / "pk.sqlite",
        """
        CREATE TABLE users (
            user_id INTEGER PRIMARY KEY,
            email TEXT NOT NULL
        );
        INSERT INTO users (user_id, email) VALUES (101, 'a@example.com');
        INSERT INTO users (user_id, email) VALUES (202, 'b@example.com');
        INSERT INTO users (user_id, email) VALUES (303, 'c@example.com');
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 3
    pks = [r.metadata["primary_key"] for r in results]
    assert pks == [101, 202, 303]
    # Confirm the JSON body also has the PK value (round-trip check).
    assert "101" in results[0].body
    assert "a@example.com" in results[0].body


def test_ingest_table_without_pk_uses_rowid(tmp_path: Path) -> None:
    """A table with no explicit PRIMARY KEY → metadata.primary_key
    falls back to the SQLite ``rowid`` (always populated, always
    unique within the table). Without this fallback, downstream
    consumers couldn't dedupe rows from PK-less tables."""
    p = _make_db(
        tmp_path / "nopk.sqlite",
        """
        CREATE TABLE log (msg TEXT, level TEXT);
        INSERT INTO log (msg, level) VALUES ('hi', 'info');
        INSERT INTO log (msg, level) VALUES ('bye', 'info');
        """,
    )
    results = list(SqliteAdapter().ingest(str(p)))
    assert len(results) == 2
    # rowid is 1-indexed in SQLite, monotonically increasing.
    pks = [r.metadata["primary_key"] for r in results]
    assert pks == [1, 2]


# ---------------------------------------------------------------------------
# Registry: the adapter is discoverable in priority order
# ---------------------------------------------------------------------------


def test_sqlite_adapter_registered_before_text_file() -> None:
    """The SQLite adapter must run before text-file in the registry.

    The brief specifies "extension match is more specific" — keeping
    the specificity ladder readable top-down lets a future maintainer
    see at a glance that ``.sqlite`` / ``.sqlite3`` / ``.db`` are
    handled by the dedicated adapter. (Practically, text-file's
    NUL-byte heuristic would reject a binary SQLite file anyway, so
    a wrong order would degrade to a silent skip rather than a
    corrupt note — but the failed-stub on a corrupt-DB direct call
    is louder than a silent skip, which is exactly the L0 P2 posture
    that v0.7.3 closed AD1 against.)"""
    from myco.ingestion.adapters import all_adapters
    from myco.ingestion.adapters.sqlite import SqliteAdapter as SA
    from myco.ingestion.adapters.text_file import TextFileAdapter as TF

    adapters = list(all_adapters())
    sa_idx = next((i for i, a in enumerate(adapters) if isinstance(a, SA)), -1)
    tf_idx = next((i for i, a in enumerate(adapters) if isinstance(a, TF)), -1)
    assert sa_idx >= 0, "SqliteAdapter not registered"
    assert tf_idx >= 0, "TextFileAdapter not registered"
    assert sa_idx < tf_idx, (
        f"SqliteAdapter (idx {sa_idx}) must register before "
        f"TextFileAdapter (idx {tf_idx})"
    )
