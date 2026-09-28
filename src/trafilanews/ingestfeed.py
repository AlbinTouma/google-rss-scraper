from operator import contains
from src.trafilanews.utils import decode_rss_links, parse_rss_feed, parse_article, fetch_article 
import httpx
from collections.abc import Generator, Iterator
import contextlib

class trafilanews():

    def __init__(
            self,
            url: str,
            proxy: str | None = None,
            timeout: float | None = 10.0,
            user_agent: str | None = None,
            use_playwright: bool = False,
            ):

            self.proxy = proxy
            self.timeout = timeout
            self.headers = {"User-Agent": user_agent} if user_agent else None
            self.rss_url = url
            self.use_playwright = use_playwright

    @contextlib.contextmanager
    def _manage_browser(self):
        if not self.use_playwright:
            yield None
            return
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as e:
            raise ImportError("This feature requires Playwright. Install it with pip install trafilanews[playwright]")

        with sync_playwright() as p:
            browser = p.chromium.launch()
        try:
            yield browser
        finally:
            browser.close()

    @contextlib.contextmanager
    def _manage_client(self):
        with httpx.Client(
                proxy=self.proxy,
                follow_redirects=True,
                timeout=self.timeout,
                http2=True,
                headers=self.headers,
                ) as client:
            yield client

    @contextlib.contextmanager
    def managed_session(self):
        with self._manage_browser() as browser, self._manage_client() as client:
            yield browser, client

    def fetch_article(self, url: str) -> str | None:
        with self.managed_session() as (browser, client):
            if "news.google.com/rss" in url:
                decoded_url = decode_rss_links(url)
            else:
                decoded_url = url
            article = fetch_article(decoded_url, client, browser)
            return article

    def stream_articles(self) -> Generator[str, None, None]:
        with self.managed_session() as (browser, client):
            response = client.get(self.rss_url)
            response.raise_for_status()
            rss_feed = parse_rss_feed(response)

            for url in rss_feed:
                if contains(self.rss_url, "news.google.com/rss"):
                    url = decode_rss_links(url)

                article = fetch_article(url, client, browser)
                if not article:
                    continue

                content_json = parse_article(article)
                if content_json is None:
                    continue

                yield content_json

    def fetch_all(self) -> list[str]:
        return list(self.stream_articles())


if __name__ =="__main__":

    google_rss_url ="https://news.google.com/rss/search?hl=en-US&gl=US&ceid=US:en&q=Iran"
    bbc_rss_url = "https://feeds.bbci.co.uk/news/rss.xml"

    rss = trafilanews(google_rss_url, use_playwright=True)
    feed = rss.stream_articles()
    for i in feed:
        print(i)
