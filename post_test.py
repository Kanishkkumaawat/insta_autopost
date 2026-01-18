"""Test script for posting to Instagram"""

import sys
from pathlib import Path
from pydantic import HttpUrl

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.app import InstaForgeApp
from src.models.post import PostMedia
from src.utils.logger import get_logger

logger = get_logger(__name__)


def test_post_image():
    """Test posting an image to Instagram"""
    
    print("=" * 60)
    print("Instagram Posting Test")
    print("=" * 60)
    
    # Initialize the app
    print("\n[1/4] Initializing InstaForge application...")
    app = InstaForgeApp()
    app.initialize()
    print("  [OK] Application initialized")
    
    # Get the first account
    accounts = app.account_service.list_accounts()
    if not accounts:
        print("\n[ERROR] No accounts configured!")
        print("  Please add accounts to config/accounts.yaml")
        sys.exit(1)
    
    account = accounts[0]
    account_id = account.account_id
    
    print(f"\n[2/4] Using account: {account.username} ({account_id})")
    
    # Create a test media object
    # IMPORTANT: Image URL must be publicly accessible via HTTPS
    print("\n" + "=" * 60)
    print("IMAGE URL REQUIREMENTS:")
    print("  - Must be publicly accessible (no login required)")
    print("  - Must use HTTPS (not HTTP)")
    print("  - Must be a valid image file (JPG, PNG)")
    print("  - Image must be accessible when Instagram fetches it")
    print("\nINSTAGRAM ASPECT RATIO REQUIREMENTS:")
    print("  ✓ Square (1:1) - RECOMMENDED: 1080x1080 pixels")
    print("  ✓ Portrait (4:5): 1080x1350 pixels")
    print("  ✓ Landscape (16:9): 1080x608 pixels")
    print("  ✗ Very wide or very tall images are NOT supported")
    print("\nRecommended: Use square images (1080x1080) for best compatibility")
    print("\nUpload your image to:")
    print("  * imgur.com")
    print("  * cloudinary.com")
    print("  * Your own web server")
    print("=" * 60)
    
    test_image_url = input("\nEnter image URL to post: ").strip()
    
    if not test_image_url:
        print("\n[ERROR] Image URL is required!")
        print("\nInstagram API requires a valid, publicly accessible image URL.")
        print("The placeholder image service is not compatible with Instagram's API.")
        print("\nPlease provide a real image URL and try again.")
        sys.exit(1)
    
    # Validate URL format
    if not test_image_url.startswith("https://"):
        print("\n[ERROR] Image URL must use HTTPS!")
        print(f"  Provided: {test_image_url[:50]}...")
        print("  Instagram requires HTTPS for security reasons.")
        sys.exit(1)
    
    print(f"\n[3/4] Creating post with image: {test_image_url[:50]}...")
    
    try:
        # Create media object
        media = PostMedia(
            media_type="image",
            url=HttpUrl(test_image_url),
        )
        
        # Create post
        caption = "Test post from InstaForge automation system! 🚀 #instaforge #automation"
        
        post = app.posting_service.create_post(
            account_id=account_id,
            media=media,
            caption=caption,
        )
        
        print(f"  [OK] Post created: {post.post_id}")
        print(f"       Status: {post.status}")
        
        # Confirm before posting
        print(f"\n[4/4] Ready to publish post to {account.username}")
        confirm = input("  Publish this post? (yes/no): ").strip().lower()
        
        if confirm in ['yes', 'y']:
            print("\n  Publishing post...")
            
            # Publish with retry
            published_post = app.posting_service.publish_post_with_retry(post)
            
            print(f"\n  [SUCCESS] Post published!")
            print(f"    Instagram Media ID: {published_post.instagram_media_id}")
            print(f"    Published at: {published_post.published_at}")
            print(f"    Status: {published_post.status}")
            
            if published_post.instagram_media_id:
                # Try to construct a permalink (this may not always work)
                print(f"\n  View your post on Instagram!")
                print(f"    (Check your Instagram account for the new post)")
            
            print("\n" + "=" * 60)
            print("Posting test completed successfully!")
            print("=" * 60)
        else:
            print("\n  Post creation cancelled. Post was created but not published.")
            print(f"    Post ID: {post.post_id}")
            print(f"    Status: {post.status}")
    
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Posting failed: {error_msg}")
        
        # Provide specific guidance based on error
        if "36003" in error_msg or "aspect ratio" in error_msg.lower():
            print("\n" + "=" * 60)
            print("ERROR: Unsupported Aspect Ratio (Code 36003)")
            print("=" * 60)
            print("\nInstagram has strict aspect ratio requirements for feed posts:")
            print("\nSUPPORTED ASPECT RATIOS:")
            print("  1. Square (1:1) - RECOMMENDED")
            print("     Example: 1080x1080, 1200x1200 pixels")
            print("  2. Portrait (4:5) - Vertical images")
            print("     Example: 1080x1350 pixels (4:5 ratio)")
            print("     Maximum: Up to 8:5 portrait")
            print("  3. Landscape (16:9) - Horizontal images")
            print("     Example: 1080x608 pixels (16:9 ratio)")
            print("     Note: Instagram prefers vertical/square content")
            print("\nNOT SUPPORTED:")
            print("  - Very wide images (wider than 16:9)")
            print("  - Very tall images (taller than 8:5)")
            print("  - Extreme aspect ratios")
            print("\nRECOMMENDED DIMENSIONS:")
            print("  - Square: 1080x1080 pixels (best for engagement)")
            print("  - Portrait: 1080x1350 pixels")
            print("  - Landscape: 1080x608 pixels")
            print("\nSOLUTION:")
            print("  1. Resize your image to meet Instagram's requirements")
            print("  2. Use image editing tools (Photoshop, GIMP, online editors)")
            print("  3. Crop to square (1:1) for best compatibility")
            print("  4. Re-upload the correctly sized image")
            print("\nYour image URL is valid, but the dimensions need adjustment.")
            print("=" * 60)
        elif "9004" in error_msg or "media type" in error_msg.lower():
            print("\n" + "=" * 60)
            print("ERROR: Invalid Image Format (Code 9004)")
            print("=" * 60)
            print("\nThis error means Instagram rejected your image URL.")
            print("\nCommon causes:")
            print("  1. Image URL is not publicly accessible")
            print("     - Instagram's servers must be able to fetch the image")
            print("     - Test: Try opening the URL in an incognito browser")
            print("  2. Image format not supported")
            print("     - Use JPG or PNG format")
            print("     - Avoid GIF, WebP, or other formats")
            print("  3. Image URL redirects or requires authentication")
            print("     - URL must directly serve the image file")
            print("     - No login, cookies, or redirects allowed")
            print("  4. Image dimensions")
            print("     - Minimum: 320x320 pixels")
            print("     - Recommended: 1080x1080 pixels or larger")
            print("\nSolution:")
            print("  - Upload your image to a reliable hosting service")
            print("  - Use imgur.com or similar service for testing")
            print("  - Ensure the direct image URL ends with .jpg or .png")
            print("=" * 60)
        elif "190" in error_msg or "OAuth" in error_msg:
            print("\nToken or permission issue. Check your access token.")
        else:
            print("\nCommon issues:")
            print("  1. Image URL must be publicly accessible via HTTPS")
            print("  2. Image must be in a supported format (JPG, PNG)")
            print("  3. Image must meet Instagram's size requirements")
            print("  4. Access token must have posting permissions")
        
        print(f"\nFull error details: {error_msg}")
        sys.exit(1)


def test_post_to_multiple_accounts():
    """Test posting to multiple accounts simultaneously"""
    
    print("=" * 60)
    print("Multi-Account Posting Test")
    print("=" * 60)
    
    # Initialize the app
    print("\n[1/3] Initializing InstaForge application...")
    app = InstaForgeApp()
    app.initialize()
    print("  [OK] Application initialized")
    
    # Get all accounts
    accounts = app.account_service.list_accounts()
    if len(accounts) < 2:
        print(f"\n[INFO] Only {len(accounts)} account(s) configured.")
        print("  Multi-account posting requires at least 2 accounts.")
        print("  Run test_post_image() for single account posting.")
        return
    
    print(f"\n[2/3] Found {len(accounts)} accounts")
    account_ids = [acc.account_id for acc in accounts]
    
    # Create media
    test_image_url = input("\nEnter image URL to post (or press Enter to cancel): ").strip()
    
    if not test_image_url:
        print("  Cancelled.")
        return
    
    print(f"\n[3/3] Posting to {len(account_ids)} accounts...")
    
    try:
        media = PostMedia(
            media_type="image",
            url=HttpUrl(test_image_url),
        )
        
        caption = "Multi-account test post from InstaForge! 🚀"
        
        posts = app.posting_service.publish_to_multiple_accounts(
            account_ids=account_ids,
            media=media,
            caption=caption,
        )
        
        print(f"\n  [SUCCESS] Posted to {len(posts)} account(s)!")
        for post in posts:
            print(f"    - Account: {post.account_id}, Media ID: {post.instagram_media_id}")
    
    except Exception as e:
        print(f"\n[ERROR] Multi-account posting failed: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    print("\nInstaForge Posting Test Script")
    print("Choose an option:")
    print("  1. Post to single account (default)")
    print("  2. Post to multiple accounts")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "2":
        test_post_to_multiple_accounts()
    else:
        test_post_image()
