"""Rate limiting for Instagram API requests"""

import time
from collections import deque
from typing import Optional
from threading import Lock

from ..utils.logger import get_logger
from ..utils.exceptions import RateLimitError

logger = get_logger(__name__)


class RateLimiter:
    """Thread-safe rate limiter for API requests"""
    
    def __init__(
        self,
        requests_per_hour: int = 200,
        requests_per_minute: int = 20,
        retry_after_seconds: int = 60,
    ):
        self.requests_per_hour = requests_per_hour
        self.requests_per_minute = requests_per_minute
        self.retry_after_seconds = retry_after_seconds
        
        # Track request timestamps
        self.hourly_requests: deque = deque()
        self.minute_requests: deque = deque()
        self.lock = Lock()
    
    def _clean_old_requests(self):
        """Remove requests older than the time window"""
        current_time = time.time()
        
        # Remove requests older than 1 hour
        while self.hourly_requests and current_time - self.hourly_requests[0] > 3600:
            self.hourly_requests.popleft()
        
        # Remove requests older than 1 minute
        while self.minute_requests and current_time - self.minute_requests[0] > 60:
            self.minute_requests.popleft()
    
    def acquire(self, wait: bool = True) -> bool:
        """
        Acquire permission to make a request
        
        Args:
            wait: If True, wait until rate limit allows; if False, return immediately
            
        Returns:
            True if permission granted, False if rate limit exceeded and wait=False
        """
        with self.lock:
            self._clean_old_requests()
            
            # Check hourly limit
            if len(self.hourly_requests) >= self.requests_per_hour:
                if wait:
                    sleep_time = 3600 - (time.time() - self.hourly_requests[0])
                    if sleep_time > 0:
                        logger.warning(
                            "Hourly rate limit reached, waiting",
                            sleep_seconds=sleep_time,
                        )
                        time.sleep(sleep_time)
                        return self.acquire(wait=False)
                else:
                    raise RateLimitError(
                        f"Hourly rate limit exceeded: {self.requests_per_hour} requests/hour",
                        retry_after=int(3600 - (time.time() - self.hourly_requests[0])),
                    )
            
            # Check minute limit
            if len(self.minute_requests) >= self.requests_per_minute:
                if wait:
                    sleep_time = 60 - (time.time() - self.minute_requests[0])
                    if sleep_time > 0:
                        logger.warning(
                            "Minute rate limit reached, waiting",
                            sleep_seconds=sleep_time,
                        )
                        time.sleep(sleep_time)
                        return self.acquire(wait=False)
                else:
                    raise RateLimitError(
                        f"Minute rate limit exceeded: {self.requests_per_minute} requests/minute",
                        retry_after=int(60 - (time.time() - self.minute_requests[0])),
                    )
            
            # Record this request
            current_time = time.time()
            self.hourly_requests.append(current_time)
            self.minute_requests.append(current_time)
            
            return True
    
    def get_wait_time(self) -> float:
        """Get the time to wait before next request is allowed"""
        with self.lock:
            self._clean_old_requests()
            
            wait_times = []
            
            if len(self.hourly_requests) >= self.requests_per_hour:
                wait_times.append(3600 - (time.time() - self.hourly_requests[0]))
            
            if len(self.minute_requests) >= self.requests_per_minute:
                wait_times.append(60 - (time.time() - self.minute_requests[0]))
            
            return max(wait_times) if wait_times else 0.0
