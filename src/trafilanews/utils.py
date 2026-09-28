import feedparser
from googlenewsdecoder import gnewsdecoder
from io import BytesIO
from typing import List
from trafilatura import extract 
from collections.abc import Generator, Iterator 


def fetch_with_browser(url, browser) -> str | None:
    """Fetches the article content from the given URL using Playwright.
    params:
        url: str - The URL of the article to fetch       
        browser: playwright.sync_api.Browser - The Playwright browser instance
    returns:
        str - The HTML content of the article
    """
    page = None
    try:
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        return page.content()
    except Exception:
        return None
    finally:
        if page is not None:
            page.close()

def fetch_article(url, client, browser) -> str | None:
    """Fetches the article content from the given URL using either httpx or Playwright.
    If the httpx request fails, it will attempt to fetch the content using Playwright unless Playwright is unavailable."""
    try:
        response = client.get(url)
        if response.status_code == 200:
            return response.text
        elif browser:
            return fetch_with_browser(url, browser)
        return None 
    except Exception as e:
        pass


def decode_rss_links(url) -> str:
        """Decodes urls from Google RSS feed. Returns decoded url if successful, otherwise returns the original url.
        params:
            url: str - The url to decode
        returns:
            str - The decoded url or the original url if decoding fails
        """
        decoded = gnewsdecoder(url)
        if decoded['decoded_url']:
            return decoded['decoded_url']

        return url

def parse_rss_feed(response) -> Generator[str, None, None]:
        """
                Parses the RSS feed and yields the links of the articles.
                params:
                    response: httpx.Response - The response object from the RSS feed request
                yields:
                    str - The link of each article in the RSS feed
        """
        try:
            feed= feedparser.parse(BytesIO(response.content))
            for item in feed['entries']:
                yield item['link']

        except Exception as e:
            raise Exception("Error", e)

def parse_article(html_content: str) -> str | None:
        """
        Parses the HTML content of an article and returns the extracted text in JSON format.
        params:
            html_content: str - The HTML content of the article
        returns:
            str - The extracted text in JSON format
        """
        if not html_content:
            return None

        return extract(html_content, output_format="json", with_metadata=True)


