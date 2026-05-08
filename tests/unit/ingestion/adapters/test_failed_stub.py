"""Tests for the v0.7.3 AD1-closure failed-stub adapter protocol.

Governing doctrine: L0 P2 (永恒吞噬). Pre-v0.7.3 adapters silent-skipped
on failure (size cap, parse error, OSError) by returning ``[]``. AD1 has
flagged this since v0.6.0 because the user couldn't tell whether a 7MB
PDF was successfully ingested-as-empty or silently lost. v0.7.3 closes
the loop:

* :class:`IngestResult` gains ``status`` + ``failure_reason`` fields,
  defaulting to ``"ok"`` / ``""`` for backward compat.
* All four built-in adapters (html, pdf, tabular, text-file) replace
  ``return []`` failure paths with a single failed-stub result that
  carries the concrete reason.
* ``myco eat`` consumes the new fields: a failed-stub triggers a
  ``[adapter-skip]`` line on stderr but does NOT produce a
  ``notes/raw/*.md`` file.

These tests pin every leg of that contract.
"""

from __future__ import annotations

from pathlib import Path

from myco.core.context import MycoContext
from myco.ingestion.adapters.html_reader import HtmlReader
from myco.ingestion.adapters.pdf_reader import PdfReader
from myco.ingestion.adapters.protocol import IngestResult
from myco.ingestion.adapters.text_file import TextFileAdapter
from myco.ingestion.eat import run

# ---------------------------------------------------------------------------
# Protocol: IngestResult is constructable with status + failure_reason
# ---------------------------------------------------------------------------


def test_ingest_result_failed_stub_constructable() -> None:
    """The new failed-stub shape must be constructable directly."""
    r = IngestResult(
        title="x",
        body="",
        source="y",
        status="failed",
        failure_reason="z",
    )
    assert r.status == "failed"
    assert r.failure_reason == "z"
    assert r.body == ""


def test_ingest_result_defaults_status_ok() -> None:
    """Backward compat: pre-v0.7.3 callers that don't pass status get 'ok'."""
    r = IngestResult(title="x", body="hello", source="y")
    assert r.status == "ok"
    assert r.failure_reason == ""


# ---------------------------------------------------------------------------
# Adapters: each returns a failed-stub at every former silent-skip site
# ---------------------------------------------------------------------------


def test_html_oversized_returns_failed_stub(
    tmp_path: Path,
    monkeypatch,
) -> None:
    p = tmp_path / "big.html"
    p.write_text("<html><body>x</body></html>", encoding="utf-8")
    monkeypatch.setattr(
        "myco.ingestion.adapters.html_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    results = HtmlReader().ingest(str(p))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason
    assert results[0].body == ""


def test_html_missing_file_returns_failed_stub(tmp_path: Path) -> None:
    results = HtmlReader().ingest(str(tmp_path / "absent.html"))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "stat" in results[0].failure_reason


def test_pdf_oversized_returns_failed_stub(
    tmp_path: Path,
    monkeypatch,
) -> None:
    p = tmp_path / "big.pdf"
    p.write_text("not a real pdf", encoding="utf-8")
    monkeypatch.setattr(
        "myco.ingestion.adapters.pdf_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    results = PdfReader().ingest(str(p))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_pdf_missing_file_returns_failed_stub(tmp_path: Path) -> None:
    results = PdfReader().ingest(str(tmp_path / "absent.pdf"))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "stat" in results[0].failure_reason


def test_text_file_oversized_returns_failed_stub(
    tmp_path: Path,
    monkeypatch,
) -> None:
    p = tmp_path / "big.py"
    p.write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr("myco.ingestion.adapters.text_file.DEFAULT_MAX_INGEST_BYTES", 1)
    results = TextFileAdapter().ingest(str(p))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "size cap" in results[0].failure_reason


def test_text_file_credential_name_returns_failed_stub(tmp_path: Path) -> None:
    """A direct-call to ingest() on a credential-bearing filename must
    return a failed-stub (not silent skip)."""
    p = tmp_path / ".env"
    p.write_text("OPENAI_API_KEY=sk-x\n", encoding="utf-8")
    results = TextFileAdapter().ingest(str(p))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "credential" in results[0].failure_reason


def test_text_file_missing_returns_failed_stub(tmp_path: Path) -> None:
    results = TextFileAdapter().ingest(str(tmp_path / "absent.py"))
    assert len(results) == 1
    assert results[0].status == "failed"
    assert "stat" in results[0].failure_reason


# ---------------------------------------------------------------------------
# Consumer: ``myco eat`` skips failed-stubs without writing raw notes
# ---------------------------------------------------------------------------


def test_eat_skips_failed_stub_no_raw_note(
    genesis_substrate: Path,
    monkeypatch,
    capsys,
) -> None:
    """``eat`` consuming a failed-stub must NOT write a raw note, MUST
    log a ``[adapter-skip]`` line on stderr, and MUST report the skip
    in the result payload.

    We inject a stub adapter via the registry rather than relying on
    a real adapter's failure path; this isolates the consumer-side
    contract from the adapter selection logic (which prefers the
    text-file fallback for tiny .html files when the html size cap
    is patched below their size).
    """
    from myco.ingestion.adapters.protocol import Adapter

    class _FailingAdapter(Adapter):
        @property
        def name(self) -> str:
            return "failing-stub"

        @property
        def extensions(self) -> frozenset[str]:
            return frozenset({".failing"})

        def can_handle(self, target: str) -> bool:
            return target.endswith(".failing")

        def ingest(self, target: str):
            return [
                IngestResult(
                    title=Path(target).stem,
                    body="",
                    source=target,
                    status="failed",
                    failure_reason="size cap exceeded (test-injected)",
                )
            ]

    import myco.ingestion.adapters as registry_mod

    monkeypatch.setattr(
        registry_mod,
        "_REGISTRY",
        [_FailingAdapter(), *registry_mod._REGISTRY],
    )

    ext = genesis_substrate / "ext"
    ext.mkdir()
    target = ext / "boom.failing"
    target.write_text("anything", encoding="utf-8")

    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = run({"path": str(target)}, ctx=ctx)

    # No raw note file should have been written.
    raw_dir = genesis_substrate / "notes" / "raw"
    notes = list(raw_dir.glob("*.md")) if raw_dir.is_dir() else []
    assert notes == [], f"failed-stub leaked a raw note: {notes}"

    # Result payload reports notes_created=0 and lists the skip.
    assert result.exit_code == 0
    assert result.payload["notes_created"] == 0
    assert len(result.payload["skipped"]) == 1
    assert "size cap" in result.payload["skipped"][0]["failure_reason"]

    # Stderr carries the [adapter-skip] line with the concrete reason.
    captured = capsys.readouterr()
    assert "[adapter-skip]" in captured.err
    assert "size cap" in captured.err


def test_eat_writes_note_for_ok_result(
    genesis_substrate: Path,
) -> None:
    """Sanity check: a normal ok result still produces a raw note."""
    ext = genesis_substrate / "ext"
    ext.mkdir()
    f = ext / "hello.py"
    f.write_text("print('hi')\n", encoding="utf-8")

    ctx = MycoContext.for_testing(root=genesis_substrate)
    result = run({"path": str(f)}, ctx=ctx)

    assert result.exit_code == 0
    assert result.payload["notes_created"] == 1
    assert result.payload["skipped"] == []
    raw_dir = genesis_substrate / "notes" / "raw"
    assert len(list(raw_dir.glob("*.md"))) == 1
