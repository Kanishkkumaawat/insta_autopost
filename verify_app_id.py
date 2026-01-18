"""Verify App ID by trying different methods"""

import requests
import yaml
from pathlib import Path

def verify_app():
    """Verify App ID exists"""
    print("\n" + "="*60)
    print("App ID Verification")
    print("="*60 + "\n")
    
    # Load credentials
    with open("config/app_credentials.yaml", "r") as f:
        creds = yaml.safe_load(f)
    
    app_id = creds["instagram"]["app_id"]
    app_secret = creds["instagram"]["app_secret"]
    
    print(f"App ID: {app_id}")
    print(f"App Secret: {app_secret[:8]}...{app_secret[-4:]}\n")
    
    # Method 1: Try to get app info with app access token
    print("Method 1: Testing App Access Token...")
    app_token = f"{app_id}|{app_secret}"
    try:
        r = requests.get(
            f"https://graph.facebook.com/v18.0/{app_id}",
            params={"access_token": app_token, "fields": "id,name"},
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            print(f"  [SUCCESS] App found: {data.get('name')} (ID: {data.get('id')})")
        else:
            error = r.json().get("error", {})
            print(f"  [FAILED] {error.get('message')} (Code: {error.get('code')})")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Method 2: Try to get app info using just app_id (no auth)
    print("\nMethod 2: Testing App ID format...")
    if len(app_id) < 10 or len(app_id) > 20:
        print(f"  [WARNING] App ID length unusual: {len(app_id)} digits")
    elif not app_id.isdigit():
        print(f"  [ERROR] App ID must be numeric: {app_id}")
    else:
        print(f"  [OK] App ID format valid: {len(app_id)} digits")
    
    # Method 3: Try OAuth dialog URL
    print("\nMethod 3: Testing OAuth URL...")
    oauth_url = (
        f"https://www.facebook.com/v18.0/dialog/oauth?"
        f"client_id={app_id}&"
        f"redirect_uri=http://localhost:8080/&"
        f"scope=instagram_basic,pages_read_engagement&"
        f"response_type=code"
    )
    print(f"  OAuth URL: {oauth_url[:80]}...")
    print(f"\n  Try opening this URL in your browser:")
    print(f"  {oauth_url}")
    print(f"\n  If you get 'Invalid App ID', the App ID definitely doesn't exist")
    print(f"  or isn't accessible with your account.")
    
    # Method 4: Check if app exists by trying debug endpoint
    print("\nMethod 4: Testing with debug token...")
    try:
        # Try to debug the app token
        r = requests.get(
            "https://graph.facebook.com/v18.0/debug_token",
            params={
                "input_token": app_token,
                "access_token": app_token
            },
            timeout=10
        )
        if r.status_code == 200:
            data = r.json()
            token_info = data.get("data", {})
            print(f"  [SUCCESS] Token is valid")
            print(f"  App ID: {token_info.get('app_id')}")
            print(f"  Type: {token_info.get('type')}")
        else:
            error = r.json().get("error", {})
            print(f"  [FAILED] {error.get('message')} (Code: {error.get('code')})")
    except Exception as e:
        print(f"  [ERROR] {e}")
    
    # Summary
    print("\n" + "="*60)
    print("Troubleshooting Steps")
    print("="*60)
    print("\nIf all methods fail:")
    print("\n1. LOG INTO META DEVELOPERS:")
    print("   - Go to: https://developers.facebook.com/apps/")
    print("   - Log in with: kanishkkumawat.rex@gmail.com")
    print("   - Make sure you can see the app")
    print("\n2. VERIFY APP ID:")
    print("   - Click on your app")
    print("   - Go to Settings > Basic")
    print("   - Copy the App ID EXACTLY (including any spaces/characters)")
    print("   - Update config/app_credentials.yaml")
    print("\n3. VERIFY APP SECRET:")
    print("   - Same page, click 'Show' next to App Secret")
    print("   - Copy it EXACTLY")
    print("   - Make sure it matches what's in the file")
    print("\n4. CHECK APP STATUS:")
    print("   - Make sure the app isn't restricted or deleted")
    print("   - Check if you're logged in with the correct account")
    print("\n5. IF APP DOESN'T EXIST:")
    print("   - Create a new app at: https://developers.facebook.com/apps/")
    print("   - Choose 'Business' or 'Consumer' type")
    print("   - Add 'Instagram Graph API' product")
    print("   - Get the new App ID and Secret")
    print("="*60 + "\n")

if __name__ == "__main__":
    verify_app()
