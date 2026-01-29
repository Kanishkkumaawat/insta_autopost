"""API request/response models for web dashboard"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, field_validator


def _parse_scheduled_time(v):
    """Parse datetime from API/frontend. Accepts YYYY-MM-DDTHH:mm or YYYY-MM-DDTHH:mm:ss (naive, server-local)."""
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.replace(tzinfo=None) if v.tzinfo else v
    if not isinstance(v, str) or not v.strip():
        return None
    s = v.strip().replace("Z", "").split("+")[0].strip()
    if "." in s:
        s = s.split(".")[0]
    if not s:
        return None
    if len(s) == 16 and s[10] == "T":  # YYYY-MM-DDTHH:mm
        s = s + ":00"
    try:
        dt = datetime.fromisoformat(s)
        return dt.replace(tzinfo=None) if dt.tzinfo else dt
    except Exception as e:
        raise ValueError(f"Invalid scheduled_time format: use YYYY-MM-DDTHH:mm or YYYY-MM-DDTHH:mm:ss") from e


class CreatePostRequest(BaseModel):
    """Request model for creating a post"""
    media_type: str = Field(..., description="Type: image, video, carousel, reels")
    urls: List[str] = Field(..., description="List of media URLs")
    caption: str = ""
    hashtags: List[str] = Field(default_factory=list)
    account_id: str
    scheduled_time: Optional[datetime] = None

    @field_validator("scheduled_time", mode="before")
    @classmethod
    def parse_scheduled_time(cls, v):
        return _parse_scheduled_time(v)
    # Auto-DM settings (for scheduled posts, these are stored and applied after publishing)
    auto_dm_enabled: Optional[bool] = False
    auto_dm_link: Optional[str] = Field(None, description="Link/file URL to send via DM")
    auto_dm_mode: Optional[str] = Field("AUTO", description="AUTO or KEYWORD")
    auto_dm_trigger: Optional[str] = Field(None, description="Trigger keyword if mode is KEYWORD")
    auto_dm_ai_enabled: Optional[bool] = Field(False, description="Use AI for reply text; stored in post DM config as ai_enabled")


class PostResponse(BaseModel):
    """Response model for post information"""
    post_id: Optional[str] = None
    account_id: str
    media_type: str
    caption: str
    hashtags: List[str]
    status: str
    instagram_media_id: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None


class LogEntry(BaseModel):
    """Log entry model"""
    timestamp: str
    level: str
    event: str
    message: str
    data: Dict[str, Any] = Field(default_factory=dict)


class ConfigAccountResponse(BaseModel):
    """Account configuration response"""
    account_id: str
    username: str
    warming_enabled: bool
    daily_actions: int
    action_types: List[str]


class ConfigSettingsResponse(BaseModel):
    """App settings response"""
    warming_schedule_time: str
    rate_limit_per_hour: int
    rate_limit_per_minute: int
    posting_max_retries: int
    posting_retry_delay: int


class StatusResponse(BaseModel):
    """System status response"""
    app_status: str
    accounts: List[Dict[str, Any]]
    warming_enabled: bool
    warming_schedule: str


class PublishedPostResponse(BaseModel):
    """Published post from Instagram API"""
    id: str
    media_type: Optional[str] = None
    caption: Optional[str] = None
    permalink: Optional[str] = None
    timestamp: Optional[str] = None
