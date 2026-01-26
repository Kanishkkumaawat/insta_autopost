"""Per-post comment-to-DM configuration storage"""

import json
from pathlib import Path
from typing import Dict, Optional, Any
from ...utils.logger import get_logger

logger = get_logger(__name__)


class PostDMConfig:
    """Manages per-post comment-to-DM file/link assignments"""

    def __init__(self, config_file: str = "data/post_dm_config.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self._config: Dict[str, Dict[str, Any]] = self._load_config()

    def _load_config(self) -> Dict[str, Dict[str, Any]]:
        """Load configuration from file"""
        if not self.config_file.exists():
            return {}

        try:
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error("Failed to load post DM config", error=str(e))
            return {}

    def _save_config(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save post DM config", error=str(e))

    def set_post_dm_file(
        self,
        account_id: str,
        media_id: str,
        file_path: Optional[str] = None,
        file_url: Optional[str] = None,
        trigger_mode: Optional[str] = "AUTO",
        trigger_word: Optional[str] = None,
        ai_enabled: Optional[bool] = None,
    ):
        """
        Set file/link to send when someone comments on a specific post.

        Args:
            account_id: Account identifier
            media_id: Instagram media ID (post ID)
            file_path: Local file path (will be converted to URL if needed)
            file_url: Direct URL to file/PDF
            trigger_mode: "AUTO" (any comment) or "KEYWORD"
            trigger_word: Specific word to trigger DM (if mode is KEYWORD)
            ai_enabled: Use AI to generate reply text (default False). Stored with post config.
        """
        key = f"{account_id}:{media_id}"

        if file_path and not file_url:
            file_url = f"file:///{file_path.replace(chr(92), '/')}"

        if not file_url and not trigger_mode:
            if key in self._config:
                del self._config[key]
                self._save_config()
            return

        existing = self._config.get(key, {})
        ai_val = ai_enabled if ai_enabled is not None else existing.get("ai_enabled", False)

        existing.update({
            "account_id": account_id,
            "media_id": media_id,
            "file_url": file_url or existing.get("file_url"),
            "file_path": file_path or existing.get("file_path"),
            "trigger_mode": trigger_mode or existing.get("trigger_mode", "AUTO"),
            "trigger_word": trigger_word if trigger_word is not None else existing.get("trigger_word"),
            "ai_enabled": ai_val,
        })
        self._config[key] = existing
        self._save_config()

        logger.info(
            "Post DM config updated",
            account_id=account_id,
            media_id=media_id,
            file_url=file_url,
            trigger_mode=trigger_mode,
            trigger_word=trigger_word,
            ai_enabled=ai_val,
        )

    def get_post_dm_config(self, account_id: str, media_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full configuration for a specific post.
        Returns dict with ai_enabled defaulting to False for older entries (backward compatible).
        """
        key = f"{account_id}:{media_id}"
        c = self._config.get(key)
        if not c:
            return None
        return {**c, "ai_enabled": c.get("ai_enabled", False)}

    def get_post_dm_file(self, account_id: str, media_id: str) -> Optional[str]:
        """
        Get file/link configured for a specific post
        
        Args:
            account_id: Account identifier
            media_id: Instagram media ID
            
        Returns:
            File URL if configured, None otherwise
        """
        config = self.get_post_dm_config(account_id, media_id)
        if config:
            return config.get("file_url")
        return None
    
    def remove_post_dm_file(self, account_id: str, media_id: str):
        """Remove file configuration for a post"""
        key = f"{account_id}:{media_id}"
        if key in self._config:
            del self._config[key]
            self._save_config()
            logger.info(
                "Post DM file removed",
                account_id=account_id,
                media_id=media_id,
            )
    
    def get_all_posts(self, account_id: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get all configured posts, optionally filtered by account"""
        if account_id:
            return {
                k: v for k, v in self._config.items()
                if v.get("account_id") == account_id
            }
        return self._config.copy()
