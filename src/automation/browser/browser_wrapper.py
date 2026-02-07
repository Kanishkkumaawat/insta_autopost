"""Synchronous wrapper for async browser operations"""

import asyncio
import threading
from typing import Optional, Dict, Any, Coroutine

from .browser_service import BrowserService
from ...utils.logger import get_logger

logger = get_logger(__name__)

_thread_local = threading.local()


def _get_thread_loop():
    """Get or create a dedicated event loop for this thread. Avoids conflicts with FastAPI/uvicorn."""
    if not hasattr(_thread_local, "loop") or _thread_local.loop is None or _thread_local.loop.is_closed():
        _thread_local.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_thread_local.loop)
    return _thread_local.loop


def _run_async_in_thread(coro: Coroutine[Any, Any, Any]) -> Any:
    """Run coroutine on this thread's dedicated loop (used when called from run_in_threadpool)."""
    loop = _get_thread_loop()
    return loop.run_until_complete(coro)


def _close_thread_loop():
    """Close and clear this thread's loop. Call after automation run to avoid pending task warnings."""
    if hasattr(_thread_local, "loop") and _thread_local.loop and not _thread_local.loop.is_closed():
        try:
            pending = asyncio.all_tasks(_thread_local.loop)
            for task in pending:
                task.cancel()
            if pending:
                _thread_local.loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
        except Exception:
            pass
        _thread_local.loop.close()
        _thread_local.loop = None
    asyncio.set_event_loop(None)


class BrowserWrapper:
    """
    Synchronous wrapper for browser automation service.
    
    This allows browser automation to be used from synchronous code.
    Uses a thread-local event loop per call to avoid conflicts with FastAPI.
    """
    
    def __init__(self, headless: bool = True):
        self.browser_service = BrowserService(headless=headless)
    
    def like_post_sync(
        self,
        account_id: str,
        post_url: str,
        username: str,
        password: Optional[str] = None,
        proxy_url: Optional[str] = None,
    ) -> Dict:
        """
        Like a post synchronously
        
        Args:
            account_id: Account identifier
            post_url: Instagram post URL
            username: Instagram username
            password: Instagram password (optional)
            proxy_url: Optional proxy URL
            
        Returns:
            Action result dictionary
        """
        return _run_async_in_thread(
            self.browser_service.like_post(
                account_id=account_id,
                post_url=post_url,
                username=username,
                password=password,
                proxy_url=proxy_url,
            )
        )
    
    def close_account(self, account_id: str):
        """Close browser for an account"""
        _run_async_in_thread(self.browser_service.close_account(account_id))
    
    def close_all(self):
        """Close all browsers"""
        try:
            _run_async_in_thread(self.browser_service.close_all())
        except RuntimeError:
            pass

    def save_post_sync(self, account_id: str, post_url: str, username: str, password=None, proxy_url=None) -> Dict:
        """Save a post (sync wrapper)."""
        return _run_async_in_thread(
            self.browser_service.save_post(account_id, post_url, username, password, proxy_url)
        )

    def follow_profile_sync(self, account_id: str, profile_url: str, username: str, password=None, proxy_url=None) -> Dict:
        """Follow a profile (sync wrapper)."""
        return _run_async_in_thread(
            self.browser_service.follow_profile(account_id, profile_url, username, password, proxy_url)
        )

    def follow_by_post_or_reel_sync(
        self,
        account_id: str,
        post_or_reel_url: str,
        username: str,
        password=None,
        proxy_url=None,
    ) -> Dict:
        """Follow the creator of a post/reel (sync wrapper)."""
        return _run_async_in_thread(
            self.browser_service.follow_by_post_or_reel_url(
                account_id, post_or_reel_url, username, password, proxy_url
            )
        )

    def comment_on_post_sync(self, account_id: str, post_url: str, text: str, username: str, password=None, proxy_url=None) -> Dict:
        """Comment on a post (sync wrapper)."""
        return _run_async_in_thread(
            self.browser_service.comment_on_post(account_id, post_url, text, username, password, proxy_url)
        )

    def discover_post_urls_sync(self, account_id: str, hashtags: list, limit_per_hashtag: int = 5, username: str = "", password=None, proxy_url=None) -> list:
        """Discover post URLs (sync wrapper)."""
        return _run_async_in_thread(
            self.browser_service.discover_post_urls(account_id, hashtags, limit_per_hashtag, username, password, proxy_url)
        )
