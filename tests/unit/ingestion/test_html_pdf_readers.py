"""Coverage for HtmlReader + PdfReader adapters."""

from __future__ import annotations

import io
from pathlib import Path
from unittest.mock import patch

from myco.ingestion.adapters.html_reader import (
    DEFAULT_MAX_INGEST_BYTES,
    HtmlReader,
)
from myco.ingestion.adapters.pdf_reader import PdfReader


# ---------- HtmlReader ----------


def test_html_reader_name_and_ext():
    a = HtmlReader()
    assert a.name == "html"
    assert ".html" in a.extensions
    assert ".htm" in a.extensions


def test_html_can_handle_html_file(tmp_path: Path):
    p = tmp_path / "x.html"
    p.write_text("<html><body>x</body></html>", encoding="utf-8")
    assert HtmlReader().can_handle(str(p)) is True


def test_html_can_handle_htm_file(tmp_path: Path):
    p = tmp_path / "x.htm"
    p.write_text("<html><body>x</body></html>", encoding="utf-8")
    assert HtmlReader().can_handle(str(p)) is True


def test_html_can_handle_other_ext_returns_false(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("text", encoding="utf-8")
    assert HtmlReader().can_handle(str(p)) is False


def test_html_can_handle_missing_file_returns_false(tmp_path: Path):
    assert HtmlReader().can_handle(str(tmp_path / "nope.html")) is False


def test_html_can_handle_oversized_returns_false(tmp_path: Path, monkeypatch):
    p = tmp_path / "big.html"
    p.write_text("<html></html>", encoding="utf-8")
    # Patch DEFAULT_MAX_INGEST_BYTES below the actual size to trigger reject.
    monkeypatch.setattr(
        "myco.ingestion.adapters.html_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    assert HtmlReader().can_handle(str(p)) is False


def test_html_ingest_extracts_text(tmp_path: Path):
    p = tmp_path / "x.html"
    p.write_text(
        "<html><head><title>Doc Title</title></head>"
        "<body><p>Hello world</p>"
        "<script>js</script><style>css</style>"
        "<nav>nav</nav><footer>foot</footer><header>head</header>"
        "</body></html>",
        encoding="utf-8",
    )
    results = HtmlReader().ingest(str(p))
    assert len(results) == 1
    r = results[0]
    assert r.title == "Doc Title"
    assert "Hello world" in r.body
    # script/style/nav/footer/header all stripped.
    assert "js" not in r.body
    assert "css" not in r.body
    assert "nav" not in r.body
    assert "foot" not in r.body
    assert "head" not in r.body


def test_html_ingest_uses_filename_when_no_title(tmp_path: Path):
    p = tmp_path / "myfile.html"
    p.write_text("<html><body><p>content</p></body></html>", encoding="utf-8")
    results = HtmlReader().ingest(str(p))
    assert results[0].title == "myfile"


def test_html_ingest_oversized_returns_empty(tmp_path: Path, monkeypatch):
    p = tmp_path / "big.html"
    p.write_text("<html><body>x</body></html>", encoding="utf-8")
    monkeypatch.setattr(
        "myco.ingestion.adapters.html_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    results = HtmlReader().ingest(str(p))
    assert results == []


def test_html_ingest_missing_file_returns_empty(tmp_path: Path):
    """ingest on a non-existent file → empty list (not exception)."""
    results = HtmlReader().ingest(str(tmp_path / "missing.html"))
    assert results == []


# ---------- PdfReader ----------


def test_pdf_reader_name_and_ext():
    a = PdfReader()
    assert a.name == "pdf"
    assert ".pdf" in a.extensions


def test_pdf_can_handle_non_pdf_returns_false(tmp_path: Path):
    p = tmp_path / "x.txt"
    p.write_text("hi", encoding="utf-8")
    assert PdfReader().can_handle(str(p)) is False


def test_pdf_can_handle_missing_returns_false(tmp_path: Path):
    assert PdfReader().can_handle(str(tmp_path / "nope.pdf")) is False


def test_pdf_can_handle_oversized_returns_false(tmp_path: Path, monkeypatch):
    p = tmp_path / "big.pdf"
    # Mock signature so it parses as PDF (we don't actually parse; we patch can_handle path)
    p.write_text("not a real pdf", encoding="utf-8")
    monkeypatch.setattr(
        "myco.ingestion.adapters.pdf_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    assert PdfReader().can_handle(str(p)) is False


def test_pdf_ingest_oversized_returns_empty(tmp_path: Path, monkeypatch):
    p = tmp_path / "big.pdf"
    p.write_text("not a real pdf", encoding="utf-8")
    monkeypatch.setattr(
        "myco.ingestion.adapters.pdf_reader.DEFAULT_MAX_INGEST_BYTES", 2
    )
    results = PdfReader().ingest(str(p))
    assert results == []


def test_pdf_ingest_extracts_text():
    """Mock pypdf to return text — confirm body contains [Page 1]."""

    class FakePage:
        def __init__(self, text: str) -> None:
            self._text = text

        def extract_text(self) -> str:
            return self._text

    class FakeReader:
        def __init__(self, *a, **kw) -> None:
            self.pages = [FakePage("hello"), FakePage("")]

    with patch(
        "myco.ingestion.adapters.pdf_reader._PR", FakeReader
    ):
        # Need a real file so stat() works.
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-fake")
            tmp = f.name
        try:
            results = PdfReader().ingest(tmp)
            assert len(results) == 1
            assert "[Page 1]" in results[0].body
            assert "hello" in results[0].body
        finally:
            os.unlink(tmp)


def test_pdf_ingest_no_text_returns_placeholder():
    """When no page has extractable text, body says (no extractable text)."""

    class FakePage:
        def extract_text(self) -> str:
            return ""

    class FakeReader:
        def __init__(self, *a, **kw) -> None:
            self.pages = [FakePage(), FakePage()]

    with patch(
        "myco.ingestion.adapters.pdf_reader._PR", FakeReader
    ):
        import tempfile, os

        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-fake")
            tmp = f.name
        try:
            results = PdfReader().ingest(tmp)
            assert "no extractable text" in results[0].body
        finally:
            os.unlink(tmp)


def test_pdf_ingest_missing_file_returns_empty(tmp_path: Path):
    results = PdfReader().ingest(str(tmp_path / "missing.pdf"))
    assert results == []
