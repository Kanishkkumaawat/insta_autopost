"""Browser-based Explore/hashtag discovery - collect post URLs for warm-up."""

import asyncio
import re
from typing import List

from ....utils.logger import get_logger

logger = get_logger(__name__)

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None

POST_URL_PATTERN = re.compile(r"https?://(?:www\.)?instagram\.com/p/([A-Za-z0-9_-]+)/?")
REEL_URL_PATTERN = re.compile(r"https?://(?:www\.)?instagram\.com/reel/([A-Za-z0-9_-]+)/?")

# Wait up to 15s for at least one post/reel link to appear (grid loaded)
WAIT_FOR_LINKS_TIMEOUT_MS = 15000
# After scroll, wait before re-collecting
SCROLL_WAIT_MS = 1500


def _extract_urls_from_links(links: List[str], limit: int, seen: set) -> List[str]:
    """Dedupe and validate links; return up to limit new URLs."""
    urls = []
    for href in links or []:
        if len(urls) >= limit:
            break
        m = POST_URL_PATTERN.search(href) or REEL_URL_PATTERN.search(href)
        if m and href not in seen:
            seen.add(href)
            urls.append(href)
    return urls


async def _collect_post_links(page: Page, limit: int, seen: set) -> List[str]:
    """Collect post/reel links using primary and fallback selectors."""
    js_primary = """() => [...document.querySelectorAll('a[href*="/p/"], a[href*="/reel/"]')].map(a => a.href)"""
    js_fallback = """() => [...document.querySelectorAll('a[href*="instagram.com/p/"], a[href*="instagram.com/reel/"]')].map(a => a.href)"""
    links = await page.evaluate(js_primary)
    urls = _extract_urls_from_links(links, limit, seen)
    if not urls:
        links = await page.evaluate(js_fallback)
        urls = _extract_urls_from_links(links, limit, seen)
    return urls


class BrowserExploreAction:
    """Discover post URLs from Explore or hashtag page."""

    def __init__(self, page: Page):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required")
        self.page = page

    async def get_post_urls_from_hashtag(self, hashtag: str, limit: int = 15) -> List[str]:
        """Navigate to hashtag explore page and collect post URLs."""
        urls = []
        seen = set()
        try:
            tag = hashtag.replace("#", "").strip()
            if not tag:
                return []
            url = f"https://www.instagram.com/explore/tags/{tag}/"
            logger.info("Discovering posts from hashtag", hashtag=tag)
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            # Wait for at least one post/reel link (grid loaded)
            try:
                await self.page.wait_for_selector(
                    'a[href*="/p/"], a[href*="/reel/"]',
                    timeout=WAIT_FOR_LINKS_TIMEOUT_MS,
                )
            except Exception:
                pass
            await self.page.wait_for_timeout(1000)
            urls = await _collect_post_links(self.page, limit, seen)
            # Optional scroll to trigger lazy-load, then collect again
            if len(urls) < limit:
                await self.page.evaluate("window.scrollBy(0, 500)")
                await self.page.wait_for_timeout(SCROLL_WAIT_MS)
                more = await _collect_post_links(self.page, limit - len(urls), seen)
                urls.extend(more)
            logger.info("Found post URLs", count=len(urls), hashtag=tag)
        except Exception as e:
            logger.warning("Hashtag discovery failed", hashtag=hashtag, error=str(e))
        return urls[:limit]

    async def get_post_urls_from_explore(self, limit: int = 15) -> List[str]:
        """Navigate to Explore and collect post URLs."""
        urls = []
        seen = set()
        try:
            await self.page.goto("https://www.instagram.com/explore/", wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)
            try:
                await self.page.wait_for_selector(
                    'a[href*="/p/"], a[href*="/reel/"]',
                    timeout=WAIT_FOR_LINKS_TIMEOUT_MS,
                )
            except Exception:
                pass
            urls = await _collect_post_links(self.page, limit, seen)
            for _ in range(3):
                if len(urls) >= limit:
                    break
                await self.page.evaluate("window.scrollBy(0, 500)")
                await self.page.wait_for_timeout(SCROLL_WAIT_MS)
                more = await _collect_post_links(self.page, limit - len(urls), seen)
                urls.extend(more)
            logger.info("Found post URLs from Explore", count=len(urls))
        except Exception as e:
            logger.warning("Explore discovery failed", error=str(e))
        return urls[:limit]

    async def get_post_urls_from_reels(self, limit: int = 15) -> List[str]:
        """Navigate to Reels tab and collect reel URLs.
        Tries DOM links (including relative /reel/xxx); scrolls to load more; optionally advances feed.
        """
        urls: List[str] = []
        seen: set = set()
        max_advance = 25
        base = "https://www.instagram.com"
        try:
            await self.page.goto(
                f"{base}/reels/",
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await self.page.wait_for_timeout(3000)
            try:
                await self.page.wait_for_selector(
                    'a[href*="/reel/"], a[href*="/p/"]',
                    timeout=WAIT_FOR_LINKS_TIMEOUT_MS,
                )
            except Exception:
                pass
            # A) Collect full URLs from DOM
            urls = await _collect_post_links(self.page, limit, seen)
            # A2) Also collect relative hrefs like /reel/ABC123 and normalize to full URL
            js_rel = """() => {
                const out = [];
                document.querySelectorAll('a[href*="/reel/"], a[href*="/p/"]').forEach(a => {
                    let h = (a.getAttribute('href') || '').split('?')[0];
                    if (h.startsWith('/')) h = 'https://www.instagram.com' + h;
                    if (h && (h.includes('/reel/') || h.includes('/p/'))) out.push(h);
                });
                return [...new Set(out)];
            }"""
            try:
                links = await self.page.evaluate(js_rel)
                for href in links or []:
                    if len(urls) >= limit:
                        break
                    m = POST_URL_PATTERN.search(href) or REEL_URL_PATTERN.search(href)
                    if m and href not in seen:
                        seen.add(href)
                        urls.append(href)
            except Exception:
                pass
            # B) Scroll to trigger lazy-load, then collect again
            for _ in range(3):
                if len(urls) >= limit:
                    break
                await self.page.evaluate("window.scrollBy(0, 400)")
                await self.page.wait_for_timeout(SCROLL_WAIT_MS)
                more = await _collect_post_links(self.page, limit - len(urls), seen)
                urls.extend(more)
            # C) If feed is one-reel-at-a-time, advance and read current URL
            if len(urls) < limit:
                for _ in range(max_advance):
                    if len(urls) >= limit:
                        break
                    current = self.page.url
                    if REEL_URL_PATTERN.search(current) or POST_URL_PATTERN.search(current):
                        norm = current.split("?")[0].rstrip("/") + "/"
                        if norm not in seen:
                            seen.add(norm)
                            urls.append(norm)
                    await self.page.keyboard.press("ArrowDown")
                    await self.page.wait_for_timeout(1200)
                urls = list(dict.fromkeys(urls))[:limit]
            logger.info("Found reel URLs from Reels tab", count=len(urls))
        except Exception as e:
            logger.warning("Reels discovery failed", error=str(e))
        return urls[:limit]
