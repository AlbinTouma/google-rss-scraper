from contextlib import contextmanager

from src.googlerss.ingestfeed import IngestFeed 
from src.googlerss.utils import fetch_with_browser, parse_article


class BrokenBrowser:
    def new_page(self):
        raise RuntimeError("page creation failed")


def test_fetch_with_browser_handles_browser_page_creation_failure():
    browser = BrokenBrowser()

    result = fetch_with_browser("https://example.com", browser)

    assert result is None


def test_parse_article_handles_missing_content():
    assert parse_article(None) is None
    assert parse_article("") is None


def test_google_rss_fetch_all_returns_only_valid_articles(monkeypatch):
    rss = GoogleRSS("https://example.com/rss")

    class DummyResponse:
        content = b"<rss></rss>"

        def raise_for_status(self):
            return None

    class DummyClient:
        def get(self, url):
            return DummyResponse()

    class DummyBrowser:
        pass

    @contextmanager
    def dummy_session():
        yield DummyBrowser(), DummyClient()

    monkeypatch.setattr(rss, "managed_session", dummy_session)
    monkeypatch.setattr("src.googlerss.clients.google_rss.parse_rss_feed", lambda response: ["a", "b", "c"])
    monkeypatch.setattr("src.googlerss.clients.google_rss.decode_rss_links", lambda value: value)
    monkeypatch.setattr("src.googlerss.clients.google_rss.fetch_article", lambda url, client, browser: {"a": "A", "b": "B"}.get(url))
    monkeypatch.setattr("src.googlerss.clients.google_rss.parse_article", lambda value: {"ok": value} if value else None)

    assert rss.fetch_all() == [{"ok": "A"}, {"ok": "B"}]
