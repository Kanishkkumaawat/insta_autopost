"""Browser session manager for Instagram login persistence"""

import asyncio
import json
from typing import Optional
from pathlib import Path

from ...utils.logger import get_logger

logger = get_logger(__name__)

# Use domcontentloaded instead of networkidle - Instagram has continuous background
# requests and networkidle often times out or triggers ERR_HTTP_RESPONSE_CODE_FAILURE
INSTAGRAM_WAIT_UNTIL = "domcontentloaded"
INSTAGRAM_NAV_TIMEOUT = 60000

try:
    from playwright.async_api import Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    Page = None


class BrowserSessionManager:
    """
    Manages Instagram login sessions using browser cookies.
    
    Features:
    - Save/load cookies for session persistence
    - Automatic login detection
    - Session validation
    """
    
    def __init__(self, sessions_dir: str = "data/sessions"):
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
    
    def get_session_file(self, account_id: str) -> Path:
        """Get session file path for an account"""
        return self.sessions_dir / f"{account_id}_cookies.json"
    
    async def save_session(self, account_id: str, page: Page):
        """
        Save current session cookies
        
        Args:
            account_id: Account identifier
            page: Playwright Page instance
        """
        if not PLAYWRIGHT_AVAILABLE:
            return
        
        try:
            cookies = await page.context.cookies()
            session_file = self.get_session_file(account_id)
            
            with open(session_file, "w") as f:
                json.dump(cookies, f, indent=2)
            
            logger.info(
                "Session saved",
                account_id=account_id,
                cookie_count=len(cookies),
            )
        except Exception as e:
            logger.error(
                "Failed to save session",
                account_id=account_id,
                error=str(e),
            )
    
    async def load_session(self, account_id: str, page: Page) -> bool:
        """
        Load saved session cookies
        
        Args:
            account_id: Account identifier
            page: Playwright Page instance
            
        Returns:
            True if session was loaded, False otherwise
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        session_file = self.get_session_file(account_id)
        
        if not session_file.exists():
            logger.debug("No saved session found", account_id=account_id)
            return False
        
        try:
            with open(session_file, "r") as f:
                cookies = json.load(f)
            
            await page.context.add_cookies(cookies)
            
            logger.info(
                "Session loaded",
                account_id=account_id,
                cookie_count=len(cookies),
            )
            
            return True
        except Exception as e:
            logger.error(
                "Failed to load session",
                account_id=account_id,
                error=str(e),
            )
            return False
    
    async def is_logged_in(self, page: Page) -> bool:
        """
        Check if user is logged into Instagram
        
        Args:
            page: Playwright Page instance
            
        Returns:
            True if logged in, False otherwise
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            # Navigate to Instagram home (domcontentloaded avoids networkidle timeout on Instagram)
            await page.goto(
                "https://www.instagram.com/",
                wait_until=INSTAGRAM_WAIT_UNTIL,
                timeout=INSTAGRAM_NAV_TIMEOUT,
            )
            
            # Check for login indicators
            # If we see certain elements, we're logged in
            logged_in_indicators = [
                'a[href*="/direct/"]',  # DM icon
                'a[href="/"]',  # Home icon
            ]
            
            for selector in logged_in_indicators:
                try:
                    element = await page.wait_for_selector(selector, timeout=5000)
                    if element:
                        logger.debug("Logged in detected", indicator=selector)
                        return True
                except Exception:
                    continue
            
            # Check for login page indicators
            login_indicators = [
                'input[name="username"]',
                'button[type="submit"]',
            ]
            
            for selector in login_indicators:
                try:
                    element = await page.wait_for_selector(selector, timeout=3000)
                    if element:
                        logger.debug("Not logged in - login page detected")
                        return False
                except Exception:
                    continue
            
            # Default to not logged in if we can't determine
            return False
            
        except Exception as e:
            logger.error("Error checking login status", error=str(e))
            return False
    
    async def login(
        self,
        page: Page,
        username: str,
        password: str,
        account_id: Optional[str] = None,
    ) -> bool:
        """
        Login to Instagram
        
        Args:
            page: Playwright Page instance
            username: Instagram username
            password: Instagram password
            account_id: Account identifier (for saving session)
            
        Returns:
            True if login successful, False otherwise
        """
        if not PLAYWRIGHT_AVAILABLE:
            return False
        
        try:
            # Navigate to Instagram login page - use domcontentloaded and retry on failure
            # (networkidle fails on Instagram due to continuous background requests)
            login_url = "https://www.instagram.com/accounts/login/"
            last_err = None
            for attempt in range(3):
                try:
                    await page.goto(
                        login_url,
                        wait_until=INSTAGRAM_WAIT_UNTIL,
                        timeout=INSTAGRAM_NAV_TIMEOUT,
                    )
                    break
                except Exception as e:
                    last_err = e
                    if attempt < 2:
                        logger.warning(
                            "Login page nav failed, retrying",
                            attempt=attempt + 1,
                            error=str(e)[:100],
                        )
                        await asyncio.sleep(3)
            else:
                raise last_err

            # Wait for login form
            await page.wait_for_selector('input[name="username"]', timeout=10000)
            
            # Fill in credentials
            await page.fill('input[name="username"]', username)
            await page.fill('input[name="password"]', password)
            
            # Click login button
            await page.click('button[type="submit"]')
            
            # Wait for navigation (either to home or error)
            await page.wait_for_load_state(INSTAGRAM_WAIT_UNTIL, timeout=20000)
            
            # Check if login was successful
            if await self.is_logged_in(page):
                logger.info("Login successful", username=username)
                
                # Save session if account_id provided
                if account_id:
                    await self.save_session(account_id, page)
                
                return True
            else:
                logger.warning("Login failed or still on login page", username=username)
                return False
                
        except Exception as e:
            logger.error("Login error", username=username, error=str(e))
            return False
