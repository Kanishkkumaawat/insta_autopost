"""Check if Facebook App is properly configured for Instagram"""

import requests
import yaml
from pathlib import Path

def check_app_setup():
    """Check app configuration"""
    print("\n" + "="*60)
    print("Facebook App Setup Checker")
    print("="*60 + "\n")
    
    # Load credentials
    creds_path = Path("config/app_credentials.yaml")
    if not creds_path.exists():
        print("[ERROR] config/app_credentials.yaml not found")
        return
    
    with open(creds_path, "r") as f:
        creds = yaml.safe_load(f)
    
    app_id = creds.get("instagram", {}).get("app_id")
    app_secret = creds.get("instagram", {}).get("app_secret")
    
    if not app_id or not app_secret:
        print("[ERROR] app_id or app_secret missing")
        return
    
    print(f"App ID: {app_id}")
    print(f"App Secret: {'*' * (len(app_secret) - 4)}{app_secret[-4:]}\n")
    
    # Check 1: Validate App ID format
    print("1. Checking App ID format...")
    if not app_id.isdigit():
        print(f"   [ERROR] App ID must be numeric: {app_id}")
        print("   Get your App ID from: https://developers.facebook.com/apps/{app_id}/settings/basic/")
    elif len(app_id) < 10 or len(app_id) > 20:
        print(f"   [WARNING] App ID length looks unusual: {len(app_id)} digits")
    else:
        print(f"   [OK] App ID format looks correct ({len(app_id)} digits)")
    
    # Check 2: Test app access token
    print("\n2. Testing App Access Token...")
    app_access_token = f"{app_id}|{app_secret}"
    
    try:
        # Try to get app info
        url = f"https://graph.facebook.com/v18.0/{app_id}"
        params = {
            "access_token": app_access_token,
            "fields": "id,name,category"
        }
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        if "error" in result:
            error = result["error"]
            print(f"   [ERROR] Cannot access app: {error.get('message')}")
            print(f"   Error Code: {error.get('code')}")
            
            if error.get("code") == 803:
                print("\n   This means the App ID doesn't exist or is incorrect!")
                print("   Steps to fix:")
                print("   1. Go to: https://developers.facebook.com/apps/")
                print("   2. Make sure you're logged in with the correct account")
                print("   3. Find your app or create a new one")
                print("   4. Go to Settings > Basic")
                print("   5. Copy the 'App ID' - it should be a long number")
                print("   6. Update config/app_credentials.yaml")
            elif error.get("code") == 101:
                print("\n   This means the App Secret is incorrect!")
                print("   Steps to fix:")
                print("   1. Go to: https://developers.facebook.com/apps/{}/settings/basic/".format(app_id))
                print("   2. Click 'Show' next to App Secret")
                print("   3. Copy the App Secret (you may need to enter password)")
                print("   4. Update config/app_credentials.yaml")
        else:
            print(f"   [OK] App found: {result.get('name')} (ID: {result.get('id')})")
            print(f"   Category: {result.get('category', 'N/A')}")
    except Exception as e:
        print(f"   [ERROR] Failed to test app: {e}")
    
    # Check 3: OAuth URL test
    print("\n3. Testing OAuth URL generation...")
    try:
        redirect_uri = "http://localhost:8080/"
        oauth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={app_id}&"
            f"redirect_uri={redirect_uri}&"
            f"scope=instagram_basic,pages_read_engagement,instagram_content_publish&"
            f"response_type=code"
        )
        print(f"   [OK] OAuth URL generated")
        print(f"   URL: {oauth_url[:80]}...")
        print("\n   Try opening this URL in your browser to see if you get the same error")
        print("   If you get 'Invalid App ID', the App ID is definitely wrong")
    except Exception as e:
        print(f"   [ERROR] Failed to generate OAuth URL: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Summary & Next Steps")
    print("="*60)
    print("\nIf you're getting 'Invalid App ID' error:")
    print("\n1. VERIFY YOUR APP ID:")
    print("   - Go to: https://developers.facebook.com/apps/")
    print("   - Select your app")
    print("   - Go to Settings > Basic")
    print("   - Copy the 'App ID' (must be numeric, 15-16 digits)")
    print("   - Update config/app_credentials.yaml")
    print("\n2. VERIFY YOUR APP SECRET:")
    print("   - Same page as above")
    print("   - Click 'Show' next to App Secret")
    print("   - Copy it and update config/app_credentials.yaml")
    print("\n3. ADD INSTAGRAM PRODUCT:")
    print("   - Go to your app dashboard")
    print("   - Click 'Add Product'")
    print("   - Find 'Instagram Graph API'")
    print("   - Click 'Set Up'")
    print("\n4. SET OAUTH REDIRECT URI:")
    print("   - Go to: Products > Facebook Login > Settings")
    print("   - Add 'Valid OAuth Redirect URIs':")
    print("     - http://localhost:8080/")
    print("     - http://localhost:8080")
    print("\n5. MAKE SURE YOUR INSTAGRAM ACCOUNT:")
    print("   - Is a Business or Creator account (not Personal)")
    print("   - Is connected to a Facebook Page")
    print("="*60 + "\n")

if __name__ == "__main__":
    check_app_setup()
