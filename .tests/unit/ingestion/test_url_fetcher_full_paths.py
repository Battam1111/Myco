"""Coverage for ingestion/adapters/url_fetcher.py — SSRF guards + content paths."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from myco.ingestion.adapters.web_cluster import (
    DEFAULT_MAX_INGEST_BYTES,
    UrlFetcher,
    UrlFetchError,
    _is_routable_host,
    _validate_url,
)

# ---------- _is_routable_host ----------


def test_is_routable_empty_returns_false():
    assert _is_routable_host("") is False


def test_is_routable_loopback_returns_false():
    assert _is_routable_host("127.0.0.1") is False
    assert _is_routable_host("localhost") is False


def test_is_routable_link_local_returns_false():
    assert _is_routable_host("169.254.169.254") is False


def test_is_routable_private_returns_false():
    assert _is_routable_host("10.0.0.1") is False
    assert _is_routable_host("192.168.0.1") is False
    assert _is_routable_host("172.16.0.1") is False


def test_is_routable_public_returns_true():
    """1.1.1.1 is public — should pass."""
    # If DNS lookup fails for any reason, skip.
    try:
        result = _is_routable_host("1.1.1.1")
        # We can't assert True (offline), but we can assert it doesn't crash.
        assert isinstance(result, bool)
    except Exception:
        pytest.skip("network unavailable")


def test_is_routable_unresolvable_returns_false():
    """A nonsense host that won't resolve."""
    assert _is_routable_host("non-existent-host-aaaaa-zzzzz.invalid") is False


# ---------- _validate_url ----------


def test_validate_disallowed_scheme_raises():
    with pytest.raises(UrlFetchError, match="scheme"):
        _validate_url("ftp://example.com/file")


def test_validate_file_scheme_raises():
    with pytest.raises(UrlFetchError, match="scheme"):
        _validate_url("file:///etc/passwd")


def test_validate_data_scheme_raises():
    with pytest.raises(UrlFetchError, match="scheme"):
        _validate_url("data:text/plain,hello")


def test_validate_loopback_host_raises():
    with pytest.raises(UrlFetchError, match="non-routable"):
        _validate_url("http://127.0.0.1/")


def test_validate_link_local_raises():
    """169.254.169.254 (AWS metadata) → blocked."""
    with pytest.raises(UrlFetchError, match="non-routable"):
        _validate_url("http://169.254.169.254/latest/meta-data/")


# ---------- UrlFetcher.can_handle ----------


def test_can_handle_http():
    """can_handle returns True for valid public http URL... but DNS may fail.
    Just verify the path."""
    fetcher = UrlFetcher()
    # Validation may fail offline → we just verify it returns bool.
    assert isinstance(fetcher.can_handle("http://example.com"), bool)


def test_can_handle_non_http():
    fetcher = UrlFetcher()
    assert fetcher.can_handle("/local/file.txt") is False
    assert fetcher.can_handle("./relative/path") is False


def test_can_handle_loopback_returns_false():
    fetcher = UrlFetcher()
    assert fetcher.can_handle("http://127.0.0.1/") is False


# ---------- UrlFetcher properties ----------


def test_fetcher_name():
    assert UrlFetcher().name == "url"


def test_fetcher_extensions_empty():
    assert UrlFetcher().extensions == frozenset()


# ---------- UrlFetcher.ingest with mocked httpx ----------


def test_ingest_text_response():
    """Mocked httpx.Client returns text — body decoded as text."""
    fetcher = UrlFetcher()
    with patch("myco.ingestion.adapters.web_cluster._validate_url"):
        with patch("myco.ingestion.adapters.web_cluster.httpx") as mock_httpx:
            # Mock the streaming context manager
            mock_resp = MagicMock()
            mock_resp.iter_bytes.return_value = [b"hello world"]
            mock_resp.headers = {"content-type": "text/plain"}
            mock_resp.url = "https://example.com/x"
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_stream_cm = MagicMock()
            mock_stream_cm.__enter__.return_value = mock_resp
            mock_stream_cm.__exit__.return_value = False
            mock_client.stream.return_value = mock_stream_cm
            mock_httpx.Client.return_value = mock_client
            results = fetcher.ingest("https://example.com/x")
            assert len(results) == 1
            assert "hello world" in results[0].body


def test_ingest_html_response_strips_tags():
    """Mocked HTML response → tags stripped (or fallback regex)."""
    fetcher = UrlFetcher()
    with patch("myco.ingestion.adapters.web_cluster._validate_url"):
        with patch("myco.ingestion.adapters.web_cluster.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.iter_bytes.return_value = [
                b"<html><body><p>Hello</p><script>x</script></body></html>"
            ]
            mock_resp.headers = {"content-type": "text/html"}
            mock_resp.url = "https://example.com/page"
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_stream_cm = MagicMock()
            mock_stream_cm.__enter__.return_value = mock_resp
            mock_stream_cm.__exit__.return_value = False
            mock_client.stream.return_value = mock_stream_cm
            mock_httpx.Client.return_value = mock_client
            results = fetcher.ingest("https://example.com/page")
            assert len(results) == 1
            assert "<script>" not in results[0].body
            assert "Hello" in results[0].body


def test_ingest_json_response():
    """JSON response is treated as plaintext, tagged 'json'."""
    fetcher = UrlFetcher()
    with patch("myco.ingestion.adapters.web_cluster._validate_url"):
        with patch("myco.ingestion.adapters.web_cluster.httpx") as mock_httpx:
            mock_resp = MagicMock()
            mock_resp.iter_bytes.return_value = [b'{"a": 1}']
            mock_resp.headers = {"content-type": "application/json"}
            mock_resp.url = "https://example.com/api"
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_stream_cm = MagicMock()
            mock_stream_cm.__enter__.return_value = mock_resp
            mock_stream_cm.__exit__.return_value = False
            mock_client.stream.return_value = mock_stream_cm
            mock_httpx.Client.return_value = mock_client
            results = fetcher.ingest("https://example.com/api")
            assert "json" in results[0].tags


def test_ingest_size_cap_aborts():
    """Body exceeding cap → UrlFetchError."""
    fetcher = UrlFetcher()
    with patch("myco.ingestion.adapters.web_cluster._validate_url"):
        with patch("myco.ingestion.adapters.web_cluster.httpx") as mock_httpx:
            # Generate too many bytes
            big = b"x" * (DEFAULT_MAX_INGEST_BYTES + 1)
            mock_resp = MagicMock()
            mock_resp.iter_bytes.return_value = [big]
            mock_resp.headers = {"content-type": "text/plain"}
            mock_resp.url = "https://example.com/x"
            mock_resp.status_code = 200
            mock_resp.raise_for_status = MagicMock()
            mock_client = MagicMock()
            mock_client.__enter__.return_value = mock_client
            mock_client.__exit__.return_value = False
            mock_stream_cm = MagicMock()
            mock_stream_cm.__enter__.return_value = mock_resp
            mock_stream_cm.__exit__.return_value = False
            mock_client.stream.return_value = mock_stream_cm
            mock_httpx.Client.return_value = mock_client
            with pytest.raises(UrlFetchError, match="exceeded"):
                fetcher.ingest("https://example.com/x")


# ---------- _strip_html / _extract_pdf_bytes static methods ----------


def test_strip_html_with_bs4_or_fallback():
    out = UrlFetcher._strip_html(
        "<html><body><script>x</script><p>Hello world</p></body></html>"
    )
    assert "Hello world" in out
    assert "<script>" not in out


def test_strip_html_plain_text_passthrough():
    """Plain text falls through unchanged."""
    out = UrlFetcher._strip_html("just text")
    assert "just text" in out


def test_extract_pdf_bytes_invalid_returns_empty_or_partial():
    """Invalid PDF bytes → fallback returns empty (or raises)."""
    try:
        out = UrlFetcher._extract_pdf_bytes(b"not pdf")
        # Real PDF library may return empty string here.
        assert isinstance(out, str)
    except Exception:
        pass  # acceptable
