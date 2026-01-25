"""Persistent tracking of sent DMs to prevent duplicates"""

import json
from pathlib import Path
from typing import Dict, Set, Tuple
from datetime import datetime, timedelta
from ...utils.logger import get_logger

logger = get_logger(__name__)


class DMTracking:
    """Persistent tracking of sent DMs to prevent duplicates"""
    
    def __init__(self, tracking_file: str = "data/dm_tracking.json"):
        self.tracking_file = Path(tracking_file)
        self.tracking_file.parent.mkdir(parents=True, exist_ok=True)
        self._tracking: Dict[str, Dict[str, Set[str]]] = self._load_tracking()
        # Format: account_id -> {date -> {comment_id, comment_id, ...}}
    
    def _load_tracking(self) -> Dict[str, Dict[str, Set[str]]]:
        """Load tracking data from file"""
        if not self.tracking_file.exists():
            return {}
        
        try:
            with open(self.tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Convert lists back to sets
                result = {}
                for account_id, dates in data.items():
                    result[account_id] = {
                        date: set(comment_ids) for date, comment_ids in dates.items()
                    }
                return result
        except Exception as e:
            logger.error("Failed to load DM tracking", error=str(e))
            return {}
    
    def _save_tracking(self):
        """Save tracking data to file"""
        try:
            # Convert sets to lists for JSON serialization
            data = {
                account_id: {
                    date: list(comment_ids) for date, comment_ids in dates.items()
                }
                for account_id, dates in self._tracking.items()
            }
            with open(self.tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error("Failed to save DM tracking", error=str(e))
    
    def is_comment_processed(self, account_id: str, comment_id: str) -> bool:
        """Check if a comment has already been processed (DM sent or fallback replied)"""
        today = datetime.utcnow().date().isoformat()
        
        if account_id not in self._tracking:
            return False
        
        if today not in self._tracking[account_id]:
            return False
        
        return comment_id in self._tracking[account_id][today]
    
    def mark_comment_processed(self, account_id: str, comment_id: str):
        """Mark a comment as processed (DM sent or fallback replied)"""
        today = datetime.utcnow().date().isoformat()
        
        if account_id not in self._tracking:
            self._tracking[account_id] = {}
        
        if today not in self._tracking[account_id]:
            self._tracking[account_id][today] = set()
        
        self._tracking[account_id][today].add(comment_id)
        
        # Clean old entries (keep last 7 days)
        cutoff_date = (datetime.utcnow() - timedelta(days=7)).date().isoformat()
        self._tracking[account_id] = {
            date: comment_ids
            for date, comment_ids in self._tracking[account_id].items()
            if date >= cutoff_date
        }
        
        self._save_tracking()
        
        logger.debug(
            "Comment marked as processed",
            account_id=account_id,
            comment_id=comment_id,
            date=today,
        )
    
    def get_processed_count_today(self, account_id: str) -> int:
        """Get count of processed comments today"""
        today = datetime.utcnow().date().isoformat()
        if account_id not in self._tracking:
            return 0
        if today not in self._tracking[account_id]:
            return 0
        return len(self._tracking[account_id][today])
