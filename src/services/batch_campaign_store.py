"""Persist and manage batch content campaigns for 30-day scheduling."""

import json
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..utils.logger import get_logger

logger = get_logger(__name__)

DATA_DIR = Path("data")
BATCH_CAMPAIGNS_FILE = DATA_DIR / "batch_campaigns.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True, parents=True)


def load_campaigns() -> List[Dict[str, Any]]:
    """Load all batch campaigns from disk."""
    _ensure_data_dir()
    if not BATCH_CAMPAIGNS_FILE.exists():
        return []
    try:
        with open(BATCH_CAMPAIGNS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("campaigns", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
    except Exception as e:
        logger.warning("Failed to load batch campaigns", error=str(e))
        return []


def save_campaigns(campaigns: List[Dict[str, Any]]) -> None:
    """Overwrite batch campaigns on disk."""
    _ensure_data_dir()
    with open(BATCH_CAMPAIGNS_FILE, "w", encoding="utf-8") as f:
        json.dump({"campaigns": campaigns}, f, indent=2)


def create_campaign(
    account_id: str,
    start_date: datetime,
    caption: str = "",
    hashtags: Optional[List[str]] = None,
    file_count: int = 0,
    end_date: Optional[datetime] = None,
) -> str:
    """Create a new batch campaign and return its ID."""
    campaigns = load_campaigns()
    campaign_id = str(uuid.uuid4())
    campaign = {
        "campaign_id": campaign_id,
        "account_id": account_id,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat() if end_date else None,
        "caption": caption or "",
        "hashtags": hashtags or [],
        "file_count": file_count,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "scheduled_posts": [],
        "errors": [],
    }
    campaigns.append(campaign)
    save_campaigns(campaigns)
    logger.info(
        "Batch campaign created",
        campaign_id=campaign_id,
        account_id=account_id,
        file_count=file_count,
        start_date=start_date.isoformat(),
    )
    return campaign_id


def get_campaign(campaign_id: str) -> Optional[Dict[str, Any]]:
    """Get a campaign by ID."""
    campaigns = load_campaigns()
    return next((c for c in campaigns if c.get("campaign_id") == campaign_id), None)


def update_campaign(campaign_id: str, updates: Dict[str, Any]) -> bool:
    """Update a campaign with new data."""
    campaigns = load_campaigns()
    for i, campaign in enumerate(campaigns):
        if campaign.get("campaign_id") == campaign_id:
            campaigns[i].update(updates)
            save_campaigns(campaigns)
            logger.info("Batch campaign updated", campaign_id=campaign_id, updates=list(updates.keys()))
            return True
    return False


def add_scheduled_post_to_campaign(campaign_id: str, post_id: str) -> bool:
    """Add a scheduled post ID to a campaign."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        return False
    
    if "scheduled_posts" not in campaign:
        campaign["scheduled_posts"] = []
    
    if post_id not in campaign["scheduled_posts"]:
        campaign["scheduled_posts"].append(post_id)
        return update_campaign(campaign_id, {"scheduled_posts": campaign["scheduled_posts"]})
    return True


def add_error_to_campaign(campaign_id: str, error: str) -> bool:
    """Add an error to a campaign's error list."""
    campaign = get_campaign(campaign_id)
    if not campaign:
        return False
    
    if "errors" not in campaign:
        campaign["errors"] = []
    
    campaign["errors"].append({
        "error": error,
        "timestamp": datetime.utcnow().isoformat(),
    })
    return update_campaign(campaign_id, {"errors": campaign["errors"]})


def mark_campaign_complete(campaign_id: str) -> bool:
    """Mark a campaign as complete."""
    return update_campaign(campaign_id, {"status": "complete"})


def mark_campaign_failed(campaign_id: str, reason: str) -> bool:
    """Mark a campaign as failed."""
    add_error_to_campaign(campaign_id, reason)
    return update_campaign(campaign_id, {"status": "failed"})


def get_all_campaigns(account_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Get all campaigns, optionally filtered by account_id."""
    campaigns = load_campaigns()
    if account_id:
        return [c for c in campaigns if c.get("account_id") == account_id]
    return campaigns
