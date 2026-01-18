"""Warming up action interfaces and implementations"""

import time
import random
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ..utils.logger import get_logger
from ..api.instagram_client import InstagramClient

logger = get_logger(__name__)


class WarmingAction(ABC):
    """Base interface for warming up actions"""
    
    def __init__(self, client: InstagramClient):
        self.client = client
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the warming action
        
        Returns:
            Action result dictionary
        """
        pass
    
    @abstractmethod
    def get_action_name(self) -> str:
        """Get the name of this action"""
        pass


class LikeAction(WarmingAction):
    """Like a post
    
    Note: Instagram Graph API does not support liking posts directly for Business accounts.
    This action logs the attempt but does not perform actual API calls.
    """
    
    def execute(self, media_id: str, **kwargs) -> Dict[str, Any]:
        """
        Like a post
        
        Args:
            media_id: Instagram media ID to like
            
        Returns:
            Action result
        """
        logger.info(
            "Warming action: Like",
            media_id=media_id,
        )
        
        # Note: Instagram Graph API doesn't support liking posts for Business accounts
        # This is a limitation of the API. We log the action for tracking purposes.
        # In a real implementation, you might need Instagram Basic Display API or other methods.
        logger.warning(
            "Like action not supported via Instagram Graph API for Business accounts",
            media_id=media_id,
        )
        
        # Simulate realistic delay
        time.sleep(random.uniform(0.5, 1.5))
        
        return {
            "action": "like",
            "media_id": media_id,
            "status": "simulated",
            "note": "Instagram Graph API doesn't support liking for Business accounts",
            "timestamp": time.time(),
        }
    
    def get_action_name(self) -> str:
        return "like"


class CommentAction(WarmingAction):
    """Comment on a post using Instagram Graph API"""
    
    def execute(self, media_id: str, comment_text: str, **kwargs) -> Dict[str, Any]:
        """
        Comment on a post
        
        Args:
            media_id: Instagram media ID to comment on
            comment_text: Comment text
            
        Returns:
            Action result
        """
        logger.info(
            "Warming action: Comment",
            media_id=media_id,
            comment_length=len(comment_text),
        )
        
        try:
            # Use Instagram Graph API to comment
            result = self.client.comment_on_media(media_id, comment_text)
            
            logger.info(
                "Comment posted successfully",
                media_id=media_id,
                comment_id=result.get("id"),
            )
            
            return {
                "action": "comment",
                "media_id": media_id,
                "comment_id": result.get("id"),
                "comment_text": comment_text,
                "status": "completed",
                "timestamp": time.time(),
            }
        except Exception as e:
            logger.error(
                "Failed to post comment",
                media_id=media_id,
                error=str(e),
            )
            return {
                "action": "comment",
                "media_id": media_id,
                "comment_text": comment_text,
                "status": "failed",
                "error": str(e),
                "timestamp": time.time(),
            }
    
    def get_action_name(self) -> str:
        return "comment"


class FollowAction(WarmingAction):
    """Follow a user
    
    Note: Instagram Graph API does not support following users directly.
    This action logs the attempt but does not perform actual API calls.
    """
    
    def execute(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        Follow a user
        
        Args:
            user_id: Instagram user ID to follow
            
        Returns:
            Action result
        """
        logger.info(
            "Warming action: Follow",
            user_id=user_id,
        )
        
        # Note: Instagram Graph API doesn't support following users
        # This is a limitation of the API. We log the action for tracking purposes.
        logger.warning(
            "Follow action not supported via Instagram Graph API",
            user_id=user_id,
        )
        
        # Simulate realistic delay
        time.sleep(random.uniform(0.8, 1.5))
        
        return {
            "action": "follow",
            "user_id": user_id,
            "status": "simulated",
            "note": "Instagram Graph API doesn't support following users",
            "timestamp": time.time(),
        }
    
    def get_action_name(self) -> str:
        return "follow"


class StoryViewAction(WarmingAction):
    """View a user's story
    
    Note: Instagram Graph API does not support viewing stories directly.
    This action logs the attempt but does not perform actual API calls.
    """
    
    def execute(self, user_id: str, **kwargs) -> Dict[str, Any]:
        """
        View a user's story
        
        Args:
            user_id: Instagram user ID whose story to view
            
        Returns:
            Action result
        """
        logger.info(
            "Warming action: Story View",
            user_id=user_id,
        )
        
        # Note: Instagram Graph API doesn't support viewing stories
        # This is a limitation of the API. We log the action for tracking purposes.
        logger.warning(
            "Story view action not supported via Instagram Graph API",
            user_id=user_id,
        )
        
        # Simulate realistic delay
        time.sleep(random.uniform(0.5, 1.0))
        
        return {
            "action": "story_view",
            "user_id": user_id,
            "status": "simulated",
            "note": "Instagram Graph API doesn't support viewing stories",
            "timestamp": time.time(),
        }
    
    def get_action_name(self) -> str:
        return "story_view"


class DMAction(WarmingAction):
    """Send a direct message (placeholder implementation)"""
    
    def execute(self, user_id: str, message_text: str, **kwargs) -> Dict[str, Any]:
        """
        Send a direct message
        
        Args:
            user_id: Instagram user ID to message
            message_text: Message text
            
        Returns:
            Action result
        """
        # TODO: Implement actual Instagram API call for DM
        logger.info(
            "Warming action: Direct Message",
            user_id=user_id,
            message_length=len(message_text),
        )
        
        time.sleep(random.uniform(1.0, 2.0))
        
        return {
            "action": "dm",
            "user_id": user_id,
            "message_text": message_text,
            "status": "completed",
            "timestamp": time.time(),
        }
    
    def get_action_name(self) -> str:
        return "dm"


def create_warming_action(action_type: str, client: InstagramClient) -> WarmingAction:
    """
    Factory function to create warming actions
    
    Args:
        action_type: Type of action (like, comment, follow, story_view, dm)
        client: Instagram API client
        
    Returns:
        WarmingAction instance
    """
    action_map = {
        "like": LikeAction,
        "comment": CommentAction,
        "follow": FollowAction,
        "story_view": StoryViewAction,
        "dm": DMAction,
    }
    
    action_class = action_map.get(action_type.lower())
    if not action_class:
        raise ValueError(f"Unknown warming action type: {action_type}")
    
    return action_class(client)
