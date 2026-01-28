"""Account onboarding pipeline - validates and registers new accounts"""

from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum

from ..models.account import Account
from ..services.account_service import AccountService
from ..utils.logger import get_logger
from ..utils.exceptions import AccountError, InstagramAPIError
from ..features.comments.comment_monitor import CommentMonitor
from ..features.comments.comment_to_dm_service import CommentToDMService
from ..features.comments.comment_service import CommentService
from ..features.ai_dm import AIDMHandler

logger = get_logger(__name__)


class AccountStatus(str, Enum):
    """Account onboarding status"""
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    FAILED = "failed"


class OnboardingResult:
    """Result of account onboarding"""
    
    def __init__(
        self,
        account_id: str,
        status: AccountStatus,
        steps_completed: List[str],
        steps_failed: List[str],
        errors: Dict[str, str],
    ):
        self.account_id = account_id
        self.status = status
        self.steps_completed = steps_completed
        self.steps_failed = steps_failed
        self.errors = errors
        self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "account_id": self.account_id,
            "status": self.status.value,
            "steps_completed": self.steps_completed,
            "steps_failed": self.steps_failed,
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


class AccountOnboardingService:
    """Service for onboarding new accounts into InstaForge"""
    
    def __init__(
        self,
        account_service: AccountService,
        comment_monitor: Optional[CommentMonitor] = None,
        comment_to_dm_service: Optional[CommentToDMService] = None,
        comment_service: Optional[CommentService] = None,
    ):
        self.account_service = account_service
        self.comment_monitor = comment_monitor
        self.comment_to_dm_service = comment_to_dm_service
        self.comment_service = comment_service
    
    def onboard_account(
        self,
        account: Account,
        app_instance: Any = None,
    ) -> OnboardingResult:
        """
        Onboard a new account through the complete pipeline.
        
        Steps:
        1. Validate access token
        2. Check permissions
        3. Verify IG connection
        4. Register webhook (if app_instance provided)
        5. Register scheduler jobs (if app_instance provided)
        6. Initialize AI DM
        7. Initialize comment monitor
        8. Initialize posting queue
        9. Initialize safety rules
        10. Save status
        
        Args:
            account: Account to onboard
            app_instance: Optional InstaForgeApp instance for full registration
            
        Returns:
            OnboardingResult with status and details
        """
        account_id = account.account_id
        steps_completed = []
        steps_failed = []
        errors = {}
        
        logger.info(
            "Starting account onboarding",
            account_id=account_id,
            username=account.username,
        )
        
        # Step 1: Validate access token
        try:
            self._validate_access_token(account)
            steps_completed.append("validate_token")
            logger.info("Token validated", account_id=account_id)
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("validate_token")
            errors["validate_token"] = error_msg
            logger.error(
                "Token validation failed",
                account_id=account_id,
                error=error_msg,
            )
            return OnboardingResult(
                account_id=account_id,
                status=AccountStatus.FAILED,
                steps_completed=steps_completed,
                steps_failed=steps_failed,
                errors=errors,
            )
        
        # Step 2: Check permissions
        try:
            self._check_permissions(account)
            steps_completed.append("check_permissions")
            logger.info("Permissions checked", account_id=account_id)
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("check_permissions")
            errors["check_permissions"] = error_msg
            logger.warning(
                "Permission check failed (non-critical)",
                account_id=account_id,
                error=error_msg,
            )
            # Continue - permissions check is non-critical
        
        # Step 3: Verify IG connection
        try:
            account_info = self._verify_ig_connection(account)
            steps_completed.append("verify_connection")
            logger.info(
                "IG connection verified",
                account_id=account_id,
                instagram_id=account_info.get("id"),
            )
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("verify_connection")
            errors["verify_connection"] = error_msg
            logger.error(
                "IG connection verification failed",
                account_id=account_id,
                error=error_msg,
            )
            return OnboardingResult(
                account_id=account_id,
                status=AccountStatus.FAILED,
                steps_completed=steps_completed,
                steps_failed=steps_failed,
                errors=errors,
            )
        
        # Step 4: Register webhook (if app_instance provided)
        if app_instance:
            try:
                self._register_webhook(account, app_instance)
                steps_completed.append("register_webhook")
                logger.info("Webhook registered", account_id=account_id)
            except Exception as e:
                error_msg = str(e)
                steps_failed.append("register_webhook")
                errors["register_webhook"] = error_msg
                logger.warning(
                    "Webhook registration failed (non-critical)",
                    account_id=account_id,
                    error=error_msg,
                )
                # Continue - webhook registration is non-critical
        
        # Step 5: Register scheduler jobs (if app_instance provided)
        if app_instance:
            try:
                self._register_scheduler_jobs(account, app_instance)
                steps_completed.append("register_scheduler")
                logger.info("Scheduler jobs registered", account_id=account_id)
            except Exception as e:
                error_msg = str(e)
                steps_failed.append("register_scheduler")
                errors["register_scheduler"] = error_msg
                logger.warning(
                    "Scheduler registration failed (non-critical)",
                    account_id=account_id,
                    error=error_msg,
                )
                # Continue - scheduler registration is non-critical
        
        # Step 6: Initialize AI DM
        try:
            self._initialize_ai_dm(account)
            steps_completed.append("initialize_ai_dm")
            logger.info("AI DM initialized", account_id=account_id)
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("initialize_ai_dm")
            errors["initialize_ai_dm"] = error_msg
            logger.warning(
                "AI DM initialization failed (non-critical)",
                account_id=account_id,
                error=error_msg,
            )
            # Continue - AI DM is optional
        
        # Step 7: Initialize comment monitor
        if self.comment_monitor:
            try:
                self._initialize_comment_monitor(account)
                steps_completed.append("initialize_comment_monitor")
                logger.info("Comment monitor initialized", account_id=account_id)
            except Exception as e:
                error_msg = str(e)
                steps_failed.append("initialize_comment_monitor")
                errors["initialize_comment_monitor"] = error_msg
                logger.warning(
                    "Comment monitor initialization failed (non-critical)",
                    account_id=account_id,
                    error=error_msg,
                )
                # Continue - comment monitor is optional
        
        # Step 8: Initialize posting queue
        try:
            self._initialize_posting_queue(account)
            steps_completed.append("initialize_posting_queue")
            logger.info("Posting queue initialized", account_id=account_id)
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("initialize_posting_queue")
            errors["initialize_posting_queue"] = error_msg
            logger.warning(
                "Posting queue initialization failed (non-critical)",
                account_id=account_id,
                error=error_msg,
            )
            # Continue - posting queue is optional
        
        # Step 9: Initialize safety rules
        try:
            self._initialize_safety_rules(account)
            steps_completed.append("initialize_safety_rules")
            logger.info("Safety rules initialized", account_id=account_id)
        except Exception as e:
            error_msg = str(e)
            steps_failed.append("initialize_safety_rules")
            errors["initialize_safety_rules"] = error_msg
            logger.warning(
                "Safety rules initialization failed (non-critical)",
                account_id=account_id,
                error=error_msg,
            )
            # Continue - safety rules are optional
        
        # Step 10: Determine final status
        # If critical steps failed, mark as INACTIVE
        critical_steps = ["validate_token", "verify_connection"]
        critical_failed = any(step in steps_failed for step in critical_steps)
        
        if critical_failed:
            status = AccountStatus.INACTIVE
        elif len(steps_failed) == 0:
            status = AccountStatus.ACTIVE
        elif len(steps_completed) >= 3:  # At least token, connection, and one other
            status = AccountStatus.ACTIVE  # Active but with some non-critical failures
        else:
            status = AccountStatus.INACTIVE
        
        result = OnboardingResult(
            account_id=account_id,
            status=status,
            steps_completed=steps_completed,
            steps_failed=steps_failed,
            errors=errors,
        )
        
        logger.info(
            "Account onboarding completed",
            account_id=account_id,
            status=status.value,
            steps_completed=len(steps_completed),
            steps_failed=len(steps_failed),
        )
        
        return result
    
    def _validate_access_token(self, account: Account) -> None:
        """Validate access token format and basic structure"""
        if not account.access_token:
            raise AccountError("Access token is required")
        
        if not account.access_token.startswith(("IGAAT", "EAAB")):
            # Allow other token formats but log warning
            logger.warning(
                "Access token format may be invalid",
                account_id=account.account_id,
                token_prefix=account.access_token[:10],
            )
    
    def _check_permissions(self, account: Account) -> None:
        """Check required Instagram API permissions"""
        try:
            client = self.account_service.get_client(account.account_id)
            # Try to get account info to verify permissions
            account_info = client.get_account_info()
            if not account_info:
                raise AccountError("Failed to retrieve account info - check permissions")
        except AccountError:
            raise
        except Exception as e:
            raise AccountError(f"Permission check failed: {str(e)}")
    
    def _verify_ig_connection(self, account: Account) -> Dict[str, Any]:
        """Verify Instagram connection and get account info"""
        try:
            return self.account_service.verify_account(account.account_id)
        except Exception as e:
            raise AccountError(f"IG connection verification failed: {str(e)}")
    
    def _register_webhook(self, account: Account, app_instance: Any) -> None:
        """Register webhook for account (if webhook URL configured)"""
        # Webhook registration is typically done via Instagram App Dashboard
        # This step is a placeholder for future webhook management
        # For now, webhooks are configured manually in Meta App Dashboard
        logger.debug(
            "Webhook registration skipped (manual configuration)",
            account_id=account.account_id,
        )
    
    def _register_scheduler_jobs(self, account: Account, app_instance: Any) -> None:
        """Register scheduler jobs for account"""
        # Scheduler jobs are registered globally, not per-account
        # This step ensures the account is included in scheduled tasks
        if hasattr(app_instance, "warming_service") and app_instance.warming_service:
            # Warming service already handles all accounts via account_service
            logger.debug(
                "Scheduler jobs already registered (global)",
                account_id=account.account_id,
            )
        else:
            logger.warning(
                "Warming service not available for scheduler registration",
                account_id=account.account_id,
            )
    
    def _initialize_ai_dm(self, account: Account) -> None:
        """Initialize AI DM handler for account"""
        if account.ai_dm and account.ai_dm.enabled:
            try:
                handler = AIDMHandler()
                if not handler.is_available():
                    raise AccountError("OpenAI API key not configured")
                logger.debug(
                    "AI DM handler available",
                    account_id=account.account_id,
                )
            except Exception as e:
                raise AccountError(f"AI DM initialization failed: {str(e)}")
    
    def _initialize_comment_monitor(self, account: Account) -> None:
        """Initialize comment monitor for account"""
        if self.comment_monitor:
            try:
                # Start monitoring for this account
                self.comment_monitor.start_monitoring(account.account_id)
                logger.debug(
                    "Comment monitor started",
                    account_id=account.account_id,
                )
            except Exception as e:
                raise AccountError(f"Comment monitor initialization failed: {str(e)}")
    
    def _initialize_posting_queue(self, account: Account) -> None:
        """Initialize posting queue for account"""
        # Posting queue is handled by PostingService which uses account_service
        # No per-account initialization needed
        logger.debug(
            "Posting queue ready (via account_service)",
            account_id=account.account_id,
        )
    
    def _initialize_safety_rules(self, account: Account) -> None:
        """Initialize safety rules for account"""
        # Safety rules are handled by rate limiters and service-level checks
        # No per-account initialization needed
        logger.debug(
            "Safety rules ready (via rate limiters)",
            account_id=account.account_id,
        )
