"""AI-powered Instagram-style reply generation using OpenAI."""

import os
from typing import Optional

from dotenv import load_dotenv

from ..utils.logger import get_logger

load_dotenv()

logger = get_logger(__name__)

# Default timeout for OpenAI API calls (seconds)
DEFAULT_TIMEOUT = 15.0
# Fallback reply when API fails or is unavailable
FALLBACK_REPLY = "Thanks for your comment! 💙"


class AIReplyService:
    """
    Generates friendly, short Instagram-style replies using OpenAI chat completions.
    Production-safe: timeout, error handling, no secrets in logs.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: float = DEFAULT_TIMEOUT,
        model: str = "gpt-4o-mini",
    ):
        self._api_key = (api_key or os.getenv("OPENAI_API_KEY") or "").strip()
        self._timeout = max(1.0, float(timeout))
        self._model = model
        self._client = None
        if self._api_key:
            try:
                from openai import OpenAI, AuthenticationError

                self._client = OpenAI(api_key=self._api_key)
                self._AuthError = AuthenticationError
                logger.info(
                    "AI_REPLY",
                    action="service_initialized",
                    has_api_key=True,
                    key_prefix=self._api_key[:10] + "..." if len(self._api_key) > 10 else "***",
                )
            except Exception as e:
                logger.warning("OpenAI client init failed", error=str(e))
                self._AuthError = None
        else:
            logger.warning(
                "AI_REPLY",
                action="service_initialized",
                has_api_key=False,
                error="OPENAI_API_KEY not found in environment",
            )

    def is_available(self) -> bool:
        """Return True if the service is configured and ready."""
        return bool(self._api_key and self._client)

    def generate_reply(
        self,
        user_message: str,
        post_context: str,
        account_username: str,
        link: Optional[str] = None,
    ) -> str:
        """
        Generate a friendly, short Instagram-style reply.

        Args:
            user_message: The comment or message to reply to.
            post_context: Brief context about the post (e.g. caption, topic).
            account_username: The Instagram account username replying.
            link: Optional URL to include in the reply.

        Returns:
            Plain-text reply. Falls back to FALLBACK_REPLY on errors.
        """
        if not user_message or not isinstance(user_message, str):
            user_message = ""
        user_message = user_message.strip()
        post_context = (post_context or "").strip()
        account_username = (account_username or "").strip() or "we"
        link = (link or "").strip() or None

        if not self.is_available():
            logger.warning(
                "AI_REPLY",
                action="failure",
                reason="unavailable",
                error="OPENAI_API_KEY not set or client unavailable",
            )
            return FALLBACK_REPLY

        _ctx = post_context or "(none)"
        logger.info(
            "AI_REPLY",
            action="called",
            user_message=user_message[:200] + ("..." if len(user_message) > 200 else ""),
            post_context=_ctx[:200] + ("..." if len(_ctx) > 200 else ""),
            account_username=account_username,
            has_link=bool(link),
        )

        system = (
            "You are helping generate short, friendly Instagram comment/DM replies. "
            "Keep replies concise (1–2 sentences), casual, and on-brand. "
            "No hashtags unless the user used them. Use emoji sparingly. "
            "Reply in the same language as the user's message when possible."
        )
        user_parts = [
            f"Comment to reply to: {user_message}",
            f"Post context: {post_context or '(none)'}",
            f"Reply as account: {account_username}",
        ]
        if link:
            user_parts.append(f"Include this link in the reply: {link}")
        user_parts.append("Output only the reply text, nothing else.")
        prompt = "\n".join(user_parts)

        logger.info(
            "AI_REPLY",
            action="prompt_sent",
            prompt=prompt[:1000] + ("..." if len(prompt) > 1000 else ""),
        )

        try:
            response = self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
                temperature=0.7,
                timeout=self._timeout,
            )
            choice = response.choices[0] if response.choices else None
            if not choice or not getattr(choice.message, "content", None):
                logger.warning(
                    "AI_REPLY",
                    action="failure",
                    reason="empty_completion",
                    error="No content in API response",
                )
                return FALLBACK_REPLY
            reply = (choice.message.content or "").strip()
            if not reply:
                logger.warning(
                    "AI_REPLY",
                    action="failure",
                    reason="empty_reply",
                    error="Reply content empty after strip",
                )
                return FALLBACK_REPLY
            logger.info(
                "AI_REPLY",
                action="response_received",
                response=reply[:1000] + ("..." if len(reply) > 1000 else ""),
            )
            return reply
        except Exception as e:
            auth_fail = getattr(self, "_AuthError", None) and isinstance(e, self._AuthError)
            err_str = str(e).lower()
            quota_fail = "quota" in err_str or "429" in err_str or "insufficient_quota" in err_str
            if auth_fail:
                reason = "invalid_api_key"
                err_msg = f"{e}. Check OPENAI_API_KEY in .env; get a key at https://platform.openai.com/api-keys"
            elif quota_fail:
                reason = "quota_exceeded"
                err_msg = f"{e}. Add billing at https://platform.openai.com/account/billing"
            else:
                reason = "exception"
                err_msg = str(e)
            logger.warning(
                "AI_REPLY",
                action="failure",
                reason=reason,
                error=err_msg,
                error_type=type(e).__name__,
            )
            return FALLBACK_REPLY
