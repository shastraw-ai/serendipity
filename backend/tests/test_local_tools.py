"""Local tool tests. No real network: httpx.get and ddgs.DDGS are monkeypatched out."""
from __future__ import annotations

import httpx

from app.tools.local_tools import _fetch_url, _web_search


class FakeResponse:
    def __init__(self, text: str, url: str = "http://example.com/final"):
        self.text = text
        self.url = url

    def raise_for_status(self) -> None:
        pass


def test_fetch_url_rejects_non_http_scheme():
    result = _fetch_url({"url": "ftp://example.com/file"})
    assert result == {"error": "url must start with http:// or https://"}


def test_fetch_url_strips_html_and_truncates(monkeypatch):
    html = "<p>Hello   world</p>"
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(html, url="http://x.test/page"))
    result = _fetch_url({"url": "http://x.test/page", "max_chars": 5})
    assert result == {"url": "http://x.test/page", "text": "Hello"}


def test_fetch_url_returns_full_text_under_the_cap(monkeypatch):
    html = "<p>Hello world</p>"
    monkeypatch.setattr(httpx, "get", lambda *a, **k: FakeResponse(html, url="http://x.test/page"))
    result = _fetch_url({"url": "http://x.test/page"})
    assert result == {"url": "http://x.test/page", "text": "Hello world"}


def test_fetch_url_surfaces_errors_as_dict(monkeypatch):
    def raise_error(*a, **k):
        raise RuntimeError("network down")

    monkeypatch.setattr(httpx, "get", raise_error)
    result = _fetch_url({"url": "http://x.test/page"})
    assert result == {"error": "fetch failed: network down"}


class FakeDDGS:
    def __init__(self, *a, **k):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def text(self, query, max_results=6):
        return [{"title": "T1", "href": "http://a.test", "body": "snippet1"}]


def test_web_search_requires_query():
    assert _web_search({"query": ""}) == {"error": "query is required"}


def test_web_search_maps_ddgs_hits_to_tool_shape(monkeypatch):
    monkeypatch.setattr("ddgs.DDGS", FakeDDGS)
    result = _web_search({"query": "test", "max_results": 3})
    assert result == [{"title": "T1", "url": "http://a.test", "snippet": "snippet1"}]
