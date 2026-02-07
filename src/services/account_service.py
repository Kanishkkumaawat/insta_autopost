"""Account management service with isolation"""

from typing import Dict, List, Optional
from threading import Lock
from tenacity import RetryError

from ..models.account import Account
from ..api.instagram_client import InstagramClient
from ..api.rate_limiter import RateLimiter
from ..utils.logger import get_logger
from ..utils.exceptions import AccountError, InstagramAPIError
from ..proxies.proxy_manager import ProxyManager

logger = get_logger(__name__)


class AccountService:
    """Service for managing Instagram accounts with isolation"""
    
    def __init__(
        self,
        accounts: List[Account],
        rate_limiter: Optional[RateLimiter] = None,
        rate_limiter_posting: Optional[RateLimiter] = None,
        proxy_manager: Optional[ProxyManager] = None,
        image_upload_timeout: int = 90,
        video_upload_timeout: int = 180,
    ):
        self.accounts = {acc.account_id: acc for acc in accounts}
        self.clients: Dict[str, InstagramClient] = {}
        self.posting_clients: Dict[str, InstagramClient] = {}
        self.lock = Lock()
        self.rate_limiter = rate_limiter
        self.rate_limiter_posting = rate_limiter_posting or rate_limiter
        self.proxy_manager = proxy_manager
        self.image_upload_timeout = image_upload_timeout
        self.video_upload_timeout = video_upload_timeout
        
        # Initialize clients for each account
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize Instagram clients for all accounts"""
        for account_id, account in self.accounts.items():
            try:
                # Instagram Graph API does NOT use proxy - proxy is only for warm-up browser.
                # Using proxy for API causes BadStatusLine / connection errors.
                proxy_url = None
                
                # Create client for monitoring (comment / media fetch)
                client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.clients[account_id] = client
                
                # Create posting-only client with dedicated rate limiter (avoids starvation)
                posting_client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter_posting,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.posting_clients[account_id] = posting_client
                
                logger.info(
                    "Initialized account client",
                    account_id=account_id,
                    username=account.username,
                    has_proxy=bool(proxy_url),
                )
            
            except Exception as e:
                logger.error(
                    "Failed to initialize account client",
                    account_id=account_id,
                    error=str(e),
                )
                raise AccountError(f"Failed to initialize client for {account_id}: {str(e)}")
    
    def get_client(self, account_id: str) -> InstagramClient:
        """
        Get Instagram client for an account
        
        Args:
            account_id: Account identifier
            
        Returns:
            InstagramClient instance
            
        Raises:
            AccountError: If account not found
        """
        if account_id not in self.clients:
            raise AccountError(f"Account not found: {account_id}")
        
        return self.clients[account_id]
    
    def get_posting_client(self, account_id: str) -> InstagramClient:
        """
        Get Instagram client for posting (uses dedicated rate limiter).
        
        Args:
            account_id: Account identifier
            
        Returns:
            InstagramClient instance
            
        Raises:
            AccountError: If account not found
        """
        if account_id not in self.posting_clients:
            raise AccountError(f"Account not found: {account_id}")
        
        return self.posting_clients[account_id]
    
    def get_account(self, account_id: str) -> Account:
        """
        Get account configuration
        
        Args:
            account_id: Account identifier
            
        Returns:
            Account instance
            
        Raises:
            AccountError: If account not found
        """
        if account_id not in self.accounts:
            raise AccountError(f"Account not found: {account_id}")
        
        return self.accounts[account_id]
    
    def list_accounts(self) -> List[Account]:
        """List all configured accounts"""
        return list(self.accounts.values())

    def update_accounts(self, accounts: List[Account]) -> None:
        """Replace accounts and re-initialize clients (e.g. after add/update/delete or OAuth persist)."""
        self.accounts = {acc.account_id: acc for acc in accounts}
        self.clients.clear()
        self.posting_clients.clear()
        self._initialize_clients()
    
    def verify_account(self, account_id: str, instagram_account_id: Optional[str] = None) -> Dict[str, any]:
        """
        Verify account credentials and get account info
        
        Args:
            account_id: Account identifier
            instagram_account_id: Optional Instagram Business Account ID to use
            
        Returns:
            Account information from Instagram API
        """
        client = self.get_client(account_id)
        
        try:
            account_info = client.get_account_info(instagram_account_id)
            
            logger.info(
                "Account verified",
                account_id=account_id,
                instagram_id=account_info.get("id"),
                username=account_info.get("username"),
            )
            
            return account_info
        
        except RetryError as e:
            # Extract the underlying exception from RetryError
            error_msg = str(e)
            
            # Try to extract the actual exception from RetryError
            if hasattr(e, 'last_attempt') and e.last_attempt is not None:
                try:
                    underlying_error = e.last_attempt.exception()
                    error_msg = str(underlying_error)
                    
                    # If the underlying error has more details, use those
                    if isinstance(underlying_error, InstagramAPIError):
                        error_code = getattr(underlying_error, 'error_code', None)
                        error_subcode = getattr(underlying_error, 'error_subcode', None)
                        if error_code:
                            error_msg = f"{error_msg} (code: {error_code}, subcode: {error_subcode})"
                except Exception:
                    # If we can't extract the exception, use the RetryError message
                    pass
            
            logger.error(
                "Account verification failed",
                account_id=account_id,
                error=error_msg,
                retry_error=True,
            )
            raise AccountError(f"Account verification failed: {error_msg}")
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Account verification failed",
                account_id=account_id,
                error=error_msg,
            )
            raise AccountError(f"Account verification failed: {error_msg}")
    
    def verify_all_accounts(self) -> Dict[str, Dict[str, any]]:
        """Verify all accounts and return status"""
        results = {}
        
        for account_id in self.accounts.keys():
            try:
                results[account_id] = {
                    "status": "verified",
                    "info": self.verify_account(account_id),
                }
            except RetryError as e:
                # Extract the underlying exception from RetryError
                error_msg = str(e)
                
                # Try to extract the actual exception from RetryError
                if hasattr(e, 'last_attempt') and e.last_attempt is not None:
                    try:
                        underlying_error = e.last_attempt.exception()
                        error_msg = str(underlying_error)
                        
                        # If the underlying error has more details, use those
                        if isinstance(underlying_error, InstagramAPIError):
                            error_code = getattr(underlying_error, 'error_code', None)
                            if error_code:
                                error_msg = f"{error_msg} (code: {error_code})"
                    except Exception:
                        # If we can't extract the exception, use the RetryError message
                        pass
                
                results[account_id] = {
                    "status": "failed",
                    "error": error_msg,
                }
            except Exception as e:
                results[account_id] = {
                    "status": "failed",
                    "error": str(e),
                }
        
        return results
    
    def add_account(self, account: Account) -> None:
        """
        Add a new account dynamically.
        
        Args:
            account: Account to add
            
        Raises:
            AccountError: If account already exists or initialization fails
        """
        with self.lock:
            if account.account_id in self.accounts:
                raise AccountError(f"Account already exists: {account.account_id}")
            
            # Add to accounts dict
            self.accounts[account.account_id] = account
            
            # Initialize client for this account
            try:
                # Instagram API does not use proxy (proxy is for warm-up browser only)
                proxy_url = None
                
                # Create client for monitoring
                client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.clients[account.account_id] = client
                
                # Create posting client
                posting_client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter_posting,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.posting_clients[account.account_id] = posting_client
                
                logger.info(
                    "Account added successfully",
                    account_id=account.account_id,
                    username=account.username,
                )
            
            except Exception as e:
                # Rollback: remove from accounts dict
                self.accounts.pop(account.account_id, None)
                logger.error(
                    "Failed to add account",
                    account_id=account.account_id,
                    error=str(e),
                )
                raise AccountError(f"Failed to add account {account.account_id}: {str(e)}")
    
    def remove_account(self, account_id: str) -> None:
        """
        Remove an account dynamically.
        
        Args:
            account_id: Account identifier to remove
            
        Raises:
            AccountError: If account not found
        """
        with self.lock:
            if account_id not in self.accounts:
                raise AccountError(f"Account not found: {account_id}")
            
            # Remove from accounts dict
            self.accounts.pop(account_id, None)
            
            # Remove clients
            self.clients.pop(account_id, None)
            self.posting_clients.pop(account_id, None)
            
            logger.info("Account removed", account_id=account_id)
    
    def update_account(self, account: Account) -> None:
        """
        Update an existing account dynamically.
        
        Args:
            account: Updated account
            
        Raises:
            AccountError: If account not found or update fails
        """
        with self.lock:
            if account.account_id not in self.accounts:
                raise AccountError(f"Account not found: {account.account_id}")
            
            # Update account
            self.accounts[account.account_id] = account
            
            # Re-initialize clients for this account
            try:
                # Remove old clients
                self.clients.pop(account.account_id, None)
                self.posting_clients.pop(account.account_id, None)
                
                # Instagram API does not use proxy (proxy is for warm-up browser only)
                proxy_url = None
                
                # Create new client for monitoring
                client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.clients[account.account_id] = client
                
                # Create new posting client
                posting_client = InstagramClient(
                    access_token=account.access_token,
                    rate_limiter=self.rate_limiter_posting,
                    proxy_url=proxy_url,
                    image_upload_timeout=self.image_upload_timeout,
                    video_upload_timeout=self.video_upload_timeout,
                )
                self.posting_clients[account.account_id] = posting_client
                
                logger.info(
                    "Account updated successfully",
                    account_id=account.account_id,
                    username=account.username,
                )
            except Exception as e:
                logger.error(
                    "Failed to update account",
                    account_id=account.account_id,
                    error=str(e),
                )
                raise AccountError(f"Failed to update account {account.account_id}: {str(e)}")
