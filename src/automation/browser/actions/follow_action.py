"""Browser-based follow action for Instagram profiles."""

import random
import time
from typing import Dict, Any

from ....utils.logger import get_logger

logger = get_logger(__name__)

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None


class BrowserFollowAction:
    """Follow a user via browser by profile URL or by post/reel URL."""

    def __init__(self, page: Page):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright is required")
        self.page = page

    async def follow_by_post_or_reel_url(self, post_or_reel_url: str) -> Dict[str, Any]:
        """Open a post or reel, find the creator's profile link, then follow them."""
        try:
            logger.info("Follow from post/reel", post_or_reel_url=post_or_reel_url)
            await self.page.goto(
                post_or_reel_url.rstrip("/"),
                wait_until="domcontentloaded",
                timeout=60000,
            )
            await self.page.wait_for_timeout(2000)
            # Find creator profile link: href like /username/ (exclude /reel/, /p/, /explore/, etc.)
            js = """
            () => {
                const links = document.querySelectorAll('a[href^="/"]');
                for (const a of links) {
                    const h = (a.getAttribute('href') || '').split('?')[0].replace(/\\/$/, '');
                    if (/^\\/[a-zA-Z0-9._]+$/.test(h) && !h.includes('/reel/') && !h.includes('/p/')
                        && h !== '/explore' && h !== '/reels' && h.length > 1) {
                        return 'https://www.instagram.com' + h + '/';
                    }
                }
                return null;
            }
            """
            profile_url = await self.page.evaluate(js)
            if not profile_url:
                return {
                    "action": "follow",
                    "post_or_reel_url": post_or_reel_url,
                    "status": "failed",
                    "error": "Could not find creator profile link on page",
                    "timestamp": time.time(),
                }
            return await self.follow_by_profile_url(profile_url)
        except Exception as e:
            logger.error(
                "Follow from post/reel failed",
                post_or_reel_url=post_or_reel_url,
                error=str(e),
            )
            return {
                "action": "follow",
                "post_or_reel_url": post_or_reel_url,
                "status": "failed",
                "error": str(e),
                "timestamp": time.time(),
            }

    async def follow_by_profile_url(self, profile_url: str) -> Dict[str, Any]:
        """Follow a user by their profile URL."""
        try:
            logger.info("Following via browser", profile_url=profile_url)
            url = profile_url.rstrip("/")
            # Do not try to extract username from /reel/ or /p/ URL (wrong index); use follow_by_post_or_reel_url instead
            if "/reel/" in url or "/p/" in url:
                return await self.follow_by_post_or_reel_url(profile_url)
            if not url.startswith("http"):
                url = f"https://www.instagram.com/{url.lstrip('/')}/"
            await self.page.goto(url, wait_until="domcontentloaded", timeout=60000)
            await self.page.wait_for_timeout(2000)

            follow_selectors = [
                'button:has-text("Follow")',
                'div[role="button"]:has-text("Follow")',
                'span:has-text("Follow")',
                '[aria-label="Follow"]',
            ]
            for sel in follow_selectors:
                try:
                    btn = await self.page.wait_for_selector(sel, timeout=5000)
                    if btn:
                        text = await btn.text_content()
                        if text and "Following" in text:
                            return {"action": "follow", "profile_url": url, "status": "already_following"}
                        await btn.click()
                        await self.page.wait_for_timeout(random.randint(800, 1500))
                        return {"action": "follow", "profile_url": url, "status": "completed"}
                except Exception:
                    continue
            return {"action": "follow", "profile_url": url, "status": "failed", "error": "Follow button not found"}
        except Exception as e:
            logger.error("Follow failed", profile_url=profile_url, error=str(e))
            return {"action": "follow", "profile_url": profile_url, "status": "failed", "error": str(e)}
