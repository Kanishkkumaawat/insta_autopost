"""Meta OAuth configuration for Facebook/Instagram authentication"""

import os
from typing import Optional
from urllib.parse import urlencode
from dotenv import load_dotenv

from ..utils.logger import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

# Constants loaded from environment variables
META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
META_REDIRECT_URI = os.getenv("META_REDIRECT_URI") or "http://localhost:8000/auth/meta/callback"

# OAuth scopes required for Instagram operations
META_OAUTH_SCOPES = [
    "instagram_basic",
    "instagram_manage_comments",
    "instagram_manage_messages",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
]


def get_meta_login_url(redirect_uri: Optional[str] = None) -> str:
    """
    Generate Facebook OAuth URL for Meta authentication.

    Args:
        redirect_uri: Override redirect URI (e.g. tunnel or custom domain).
                      If None, uses META_REDIRECT_URI from env or localhost default.

    Returns:
        OAuth authorization URL with required scopes.

    Raises:
        ValueError: If META_APP_ID is not set in environment variables.
    """
    if not META_APP_ID:
        error_msg = "META_APP_ID environment variable is not set"
        logger.error(error_msg)
        raise ValueError(error_msg)

    if not META_APP_SECRET:
        logger.warning("META_APP_SECRET environment variable is not set")

    uri = (redirect_uri or META_REDIRECT_URI).strip()

    api_version = "v18.0"
    oauth_base_url = f"https://www.facebook.com/{api_version}/dialog/oauth"

    params = {
        "client_id": META_APP_ID,
        "redirect_uri": uri,
        "scope": ",".join(META_OAUTH_SCOPES),
        "response_type": "code",
    }

    query_string = urlencode(params)
    auth_url = f"{oauth_base_url}?{query_string}"

    logger.info(
        "Generated Meta OAuth URL",
        app_id=META_APP_ID,
        redirect_uri=uri,
        scopes=META_OAUTH_SCOPES,
    )

    return auth_url
