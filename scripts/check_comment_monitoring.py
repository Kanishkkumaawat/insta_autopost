"""Check if comment monitoring is working properly."""

import os
import sys
from pathlib import Path

# Load from project root
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from src.app import InstaForgeApp
from src.utils.logger import setup_logger, get_logger

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

# Setup logging
setup_logger(log_level="INFO", log_format="console")
logger = get_logger(__name__)

def check_comment_monitoring():
    """Check comment monitoring status and recent activity."""
    print("=" * 60)
    print("Comment Monitoring Diagnostic")
    print("=" * 60)
    
    try:
        app = InstaForgeApp()
        app.initialize()
        
        # Check accounts
        accounts = app.account_service.list_accounts()
        if not accounts:
            print("❌ No accounts configured")
            return
        
        print(f"\n✓ Found {len(accounts)} account(s)")
        
        for account in accounts:
            account_id = account.account_id
            username = account.username or account.account_id
            
            print(f"\n--- Account: {username} ({account_id}) ---")
            
            # Check comment-to-DM enabled
            dm_enabled = account.comment_to_dm and account.comment_to_dm.enabled if account.comment_to_dm else False
            print(f"  Comment-to-DM enabled: {dm_enabled}")
            
            if dm_enabled:
                dm_config = app.comment_to_dm_service._get_dm_config(account_id)
                if dm_config:
                    print(f"  Trigger keyword: {dm_config.get('trigger_keyword', 'AUTO')}")
                    print(f"  Has link: {bool(dm_config.get('link_to_send'))}")
            
            # Check if monitoring is active
            is_monitoring = app.comment_monitor.monitoring.get(account_id, False)
            print(f"  Monitoring active: {is_monitoring}")
            
            # Get recent posts
            try:
                client = app.account_service.get_client(account_id)
                media_list = client.get_recent_media(limit=3)
                print(f"  Recent posts: {len(media_list)}")
                
                for media in media_list[:3]:
                    media_id = media.get("id")
                    comments_count = media.get("comments_count", 0)
                    
                    # Get post DM config
                    post_config = app.comment_to_dm_service.post_dm_config.get_post_dm_config(account_id, media_id)
                    ai_enabled = post_config.get("ai_enabled", False) if post_config else False
                    has_link = bool(post_config.get("file_url")) if post_config else False
                    
                    print(f"    Post {media_id[:15]}...: {comments_count} comments, AI={ai_enabled}, Link={has_link}")
                    
            except Exception as e:
                print(f"  ⚠ Error checking posts: {e}")
        
        # Check AI service
        print(f"\n--- AI Reply Service ---")
        ai_available = app.comment_to_dm_service.ai_reply_service.is_available()
        print(f"  AI available: {ai_available}")
        
        if not ai_available:
            print("  ⚠ OPENAI_API_KEY not set or invalid")
            print("  Run: py scripts/check_openai_key.py")
        
        print("\n" + "=" * 60)
        print("✓ Diagnostic complete")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    check_comment_monitoring()
