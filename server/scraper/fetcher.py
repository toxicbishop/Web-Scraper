import hashlib
import random
import time
import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

RATE_LIMIT_DELAY = float(os.getenv("RATE_LIMIT_DELAY", "1.5"))

# Rotate through a small pool of real desktop UAs instead of one static string —
# a single hardcoded UA is itself a fingerprint.
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
]

# Launch args that hide the automation flag Playwright/Selenium set by default.
# Sites that fingerprint navigator.webdriver or CDP artifacts check for exactly this.
STEALTH_ARGS = ["--disable-blink-features=AutomationControlled"]


def _jitter(low: float = 0.8, high: float = 2.2):
    """Randomized delay so request timing doesn't look machine-regular."""
    time.sleep(random.uniform(low, high))


def _random_ua() -> str:
    return random.choice(USER_AGENTS)


# ── Standard single-page fetch (Playwright, stealth-aware) ─────────────────────

def fetch_page(url: str) -> dict:
    time.sleep(RATE_LIMIT_DELAY)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=STEALTH_ARGS)
        context = browser.new_context(
            user_agent=_random_ua(),
            viewport={
                "width": random.randint(1600, 1920),
                "height": random.randint(900, 1080),
            },
        )
        page = context.new_page()

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            _jitter()
            html = page.content()
        finally:
            browser.close()

    return parse_html(url, html)


def fetch_page_static(url: str) -> dict:
    import requests

    time.sleep(RATE_LIMIT_DELAY)

    headers = {"User-Agent": _random_ua()}
    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    return parse_html(url, response.text)


# ── Scroll-to-load (infinite-scroll feeds) ──────────────────────────────────────

def fetch_infinite_scroll(
    url: str,
    feed_selector: str = "body",
    max_scrolls: int = 10,
    scroll_pixels: int = 2000,
) -> dict:
    """
    Repeatedly scrolls a feed container and waits for lazy-loaded content,
    stopping early once scroll height stops growing (nothing new loaded)
    or once max_scrolls is hit.
    """
    time.sleep(RATE_LIMIT_DELAY)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=STEALTH_ARGS)
        context = browser.new_context(user_agent=_random_ua())
        page = context.new_page()

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            _jitter()

            last_height = 0
            for _ in range(max_scrolls):
                page.evaluate(
                    f'document.querySelector("{feed_selector}")?.scrollBy(0, {scroll_pixels})'
                )
                _jitter(1.0, 2.0)

                new_height = page.evaluate(
                    f'document.querySelector("{feed_selector}")?.scrollHeight || 0'
                )
                if new_height == last_height:
                    break  # nothing new loaded, stop early
                last_height = new_height

            html = page.content()
        finally:
            browser.close()

    return parse_html(url, html)


# ── Click-through extraction (list view → detail panel) ────────────────────────

def fetch_with_click_through(
    url: str,
    item_selector: str,
    detail_wait_selector: str = "h1",
    max_items: int = 10,
) -> list[dict]:
    """
    For sites where the list/summary view doesn't carry full data:
    click each item matching `item_selector`, wait for `detail_wait_selector`
    to appear, then parse whatever's on screen at that point.

    Generic version of the pattern (site-agnostic selectors passed in by the
    caller) rather than hardcoded to one site's DOM.
    """
    time.sleep(RATE_LIMIT_DELAY)
    results: list[dict] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=STEALTH_ARGS)
        context = browser.new_context(user_agent=_random_ua())
        page = context.new_page()

        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            _jitter()

            items = page.query_selector_all(item_selector)
            for item in items[:max_items]:
                try:
                    item.click()
                    page.wait_for_selector(detail_wait_selector, timeout=8000)
                    _jitter(1.0, 2.5)

                    html = page.content()
                    parsed = parse_html(url, html)
                    if parsed:
                        results.append(parsed)
                except Exception:
                    continue  # skip items that fail to open/extract, keep going
        finally:
            browser.close()

    return results


def parse_html(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")

    title = soup.title.get_text(strip=True) if soup.title else ""

    for tag in soup(["script", "style", "nav", "footer"]):
        tag.decompose()

    content = soup.get_text(separator=" ", strip=True)
    content_hash = hashlib.sha256(content.encode()).hexdigest()

    return {
        "url": url,
        "title": title,
        "content": content[:50000],
        "content_hash": content_hash,
    }
