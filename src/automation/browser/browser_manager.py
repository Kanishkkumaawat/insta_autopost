"""Browser manager for Playwright instances"""

import asyncio
from typing import Optional, Dict, Any
from pathlib import Path
from urllib.parse import urlparse

from ...utils.logger import get_logger

logger = get_logger(__name__)


def _parse_proxy_url(proxy_url: str) -> Dict[str, Any]:
    """
    Parse proxy URL into Playwright format.
    Supports http://host:port and http://user:pass@host:port.
    Returns dict with server (required), username and password (optional).
    """
    if not proxy_url or not proxy_url.strip():
        return {}
    url = proxy_url.strip()
    if not url.startswith(("http://", "https://")):
        url = "http://" + url
    parsed = urlparse(url)
    netloc = parsed.netloc or ""
    server = f"{parsed.scheme or 'http'}://{netloc}"
    username = None
    password = None
    if "@" in netloc:
        userinfo, hostport = netloc.rsplit("@", 1)
        server = f"{parsed.scheme or 'http'}://{hostport}"
        if ":" in userinfo:
            username, _, password = userinfo.partition(":")
        else:
            username = userinfo
    return {"server": server, "username": username or None, "password": password or None}

# Try to import Playwright
try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Browser = None
    BrowserContext = None
    Page = None


class BrowserManager:
    """
    Manages Playwright browser instances for Instagram automation.
    
    Features:
    - Per-account browser isolation
    - Session persistence
    - Proxy support
    - Fingerprint management
    """
    
    def __init__(self, headless: bool = True, user_data_dir: Optional[str] = None):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is not installed. Install it with: "
                "pip install playwright && playwright install chromium"
            )
        
        self.headless = headless
        self.user_data_dir = Path(user_data_dir) if user_data_dir else Path("data/sessions")
        self.user_data_dir.mkdir(parents=True, exist_ok=True)
        
        self.playwright = None
        self.browsers: Dict[str, Browser] = {}
        self.contexts: Dict[str, BrowserContext] = {}
        self.pages: Dict[str, Page] = {}
        self._playwright_instance = None
    
    async def _initialize_playwright(self):
        """Initialize Playwright instance"""
        if self._playwright_instance is None:
            self._playwright_instance = await async_playwright().start()
            self.playwright = self._playwright_instance
            logger.debug("Playwright initialized")
    
    async def get_browser_for_account(
        self,
        account_id: str,
        proxy_url: Optional[str] = None,
    ) -> Browser:
        """
        Get or create a browser instance for an account
        
        Args:
            account_id: Account identifier
            proxy_url: Optional proxy URL
            
        Returns:
            Browser instance
        """
        if account_id not in self.browsers:
            await self._initialize_playwright()
            
            # Browser launch options; reduce automation detection (Instagram often blocks headless)
            launch_options = {
                "headless": self.headless,
                "channel": "chromium",
                "args": [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-infobars",
                    "--window-size=1920,1080",
                ],
            }
            # Add proxy if provided (Playwright wants server + optional username/password)
            if proxy_url:
                proxy_dict = _parse_proxy_url(proxy_url)
                if proxy_dict:
                    launch_options["proxy"] = {k: v for k, v in proxy_dict.items() if v is not None}
            
            browser = await self.playwright.chromium.launch(**launch_options)
            self.browsers[account_id] = browser
            
            logger.info(
                "Browser launched for account",
                account_id=account_id,
                headless=self.headless,
                has_proxy=bool(proxy_url),
            )
        
        return self.browsers[account_id]
    
    async def get_context_for_account(
        self,
        account_id: str,
        proxy_url: Optional[str] = None,
    ) -> BrowserContext:
        """
        Get or create a browser context for an account
        
        Args:
            account_id: Account identifier
            proxy_url: Optional proxy URL
            
        Returns:
            BrowserContext instance
        """
        if account_id not in self.contexts:
            browser = await self.get_browser_for_account(account_id, proxy_url)
            
            # Create context with account-specific user data directory
            user_data_path = self.user_data_dir / account_id
            user_data_path.mkdir(parents=True, exist_ok=True)
            
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
                ),
                "locale": "en-US",
                "timezone_id": "America/New_York",
                "extra_http_headers": {
                    "Accept-Language": "en-US,en;q=0.9",
                },
            }
            
            context = await browser.new_context(**context_options)
            self.contexts[account_id] = context
            
            logger.debug(
                "Browser context created",
                account_id=account_id,
            )
        
        return self.contexts[account_id]
    
    async def get_page_for_account(
        self,
        account_id: str,
        proxy_url: Optional[str] = None,
    ) -> Page:
        """
        Get or create a page for an account
        
        Args:
            account_id: Account identifier
            proxy_url: Optional proxy URL
            
        Returns:
            Page instance
        """
        if account_id not in self.pages:
            context = await self.get_context_for_account(account_id, proxy_url)
            page = await context.new_page()
            self.pages[account_id] = page
            
            logger.debug(
                "Browser page created",
                account_id=account_id,
            )
        
        return self.pages[account_id]
    
    async def close_account_browser(self, account_id: str):
        """Close browser for a specific account"""
        if account_id in self.pages:
            await self.pages[account_id].close()
            del self.pages[account_id]
        
        if account_id in self.contexts:
            await self.contexts[account_id].close()
            del self.contexts[account_id]
        
        if account_id in self.browsers:
            await self.browsers[account_id].close()
            del self.browsers[account_id]
        
        logger.info("Browser closed for account", account_id=account_id)
    
    async def close_all(self):
        """Close all browsers and cleanup"""
        for account_id in list(self.pages.keys()):
            await self.close_account_browser(account_id)
        
        if self._playwright_instance:
            await self._playwright_instance.stop()
            self._playwright_instance = None
        
        logger.info("All browsers closed")
