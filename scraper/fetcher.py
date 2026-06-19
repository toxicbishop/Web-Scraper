import hashlib
import time
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.5"))


def fetch_page(url: str) -> dict:
    """
    Fetch a URL using Playwright (handles JS-rendered pages).
    Returns: { url, title, content, content_hash }
    """
    time.sleep(RATE_LIMIT_DELAY)  # polite rate limiting

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (compatible; PortfolioScraper/1.0)"
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            html = page.content()
        finally:
            browser.close()

    return parse_html(url, html)


def fetch_page_static(url: str) -> dict:
    """
    Fetch a static HTML page using requests (faster, no JS support).
    """
    import requests

    time.sleep(RATE_LIMIT_DELAY)

    headers = {"User-Agent": "Mozilla/5.0 (compatible; PortfolioScraper/1.0)"}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    return parse_html(url, response.text)


def parse_html(url: str, html: str) -> dict:
    """
    Parse HTML with BeautifulSoup and extract key fields.
    Returns structured dict ready for DB insert.
    """
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.get_text(strip=True) if soup.title else ""

    # Remove scripts/styles before extracting text
    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    content = soup.get_text(separator=" ", strip=True)

    # Deduplification hash based on content
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    return {
        "url": url,
        "title": title,
        "content": content[:50000],  # cap at 50k chars
        "content_hash": content_hash,
    }
