"""OAuth helper for Instagram token generation"""

import webbrowser
import requests
from typing import Optional, Dict, Any
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from threading import Thread
import yaml
from pathlib import Path

from ..utils.logger import get_logger

logger = get_logger(__name__)


class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """HTTP handler to catch OAuth redirect"""
    
    def __init__(self, callback, *args, **kwargs):
        self.callback = callback
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        """Handle GET request from OAuth redirect"""
        parsed = urlparse(self.path)
        query_params = parse_qs(parsed.query)
        
        code = query_params.get("code", [None])[0]
        error = query_params.get("error", [None])[0]
        
        if code:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Success!</h1><p>You can close this window.</p></body></html>"
            )
            self.callback(code, None)
        elif error:
            error_description = query_params.get("error_description", [""])[0]
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(
                f"<html><body><h1>Error</h1><p>{error}: {error_description}</p></body></html>".encode()
            )
            self.callback(None, error)
        else:
            self.send_response(400)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body><h1>No code or error received</h1></body></html>")
            self.callback(None, "No code or error received")
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


class OAuthHelper:
    """Helper class for Instagram OAuth token generation"""
    
    INSTAGRAM_SCOPES = [
        "instagram_basic",
        "pages_read_engagement",
        "instagram_content_publish",
        "pages_show_list",
    ]
    
    def __init__(
        self,
        app_id: str,
        app_secret: str,
        redirect_uri: str = "http://localhost:8080/",
        api_version: str = "v18.0",
    ):
        self.app_id = app_id
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.api_version = api_version
        self.base_url = f"https://graph.facebook.com/{api_version}"
        self.oauth_url = f"https://www.facebook.com/{api_version}/dialog/oauth"
    
    def generate_authorization_url(self, scopes: Optional[list] = None) -> str:
        """
        Generate OAuth authorization URL
        
        Args:
            scopes: List of permission scopes (defaults to Instagram scopes)
            
        Returns:
            Authorization URL
        """
        if scopes is None:
            scopes = self.INSTAGRAM_SCOPES
        
        scope_string = ",".join(scopes)
        
        params = {
            "client_id": self.app_id,
            "redirect_uri": self.redirect_uri,
            "scope": scope_string,
            "response_type": "code",
        }
        
        query_string = "&".join([f"{k}={v}" for k, v in params.items()])
        return f"{self.oauth_url}?{query_string}"
    
    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token
        
        Args:
            code: Authorization code from OAuth redirect
            
        Returns:
            Token response with access_token and expires_in
        """
        url = f"{self.base_url}/oauth/access_token"
        
        params = {
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "redirect_uri": self.redirect_uri,
            "code": code,
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Token exchange failed: {result['error']}")
        
        return result
    
    def exchange_for_long_lived_token(
        self, short_lived_token: str
    ) -> Dict[str, Any]:
        """
        Exchange short-lived token for long-lived token (60 days)
        
        Args:
            short_lived_token: Short-lived access token
            
        Returns:
            Token response with access_token and expires_in
        """
        url = f"{self.base_url}/oauth/access_token"
        
        params = {
            "grant_type": "fb_exchange_token",
            "client_id": self.app_id,
            "client_secret": self.app_secret,
            "fb_exchange_token": short_lived_token,
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Long-lived token exchange failed: {result['error']}")
        
        return result
    
    def exchange_for_instagram_long_lived_token(
        self, short_lived_token: str
    ) -> Dict[str, Any]:
        """
        Exchange short-lived Instagram token for long-lived token (60 days)
        Uses Instagram-specific endpoint
        
        Args:
            short_lived_token: Short-lived Instagram access token
            
        Returns:
            Token response with access_token and expires_in
        """
        url = "https://graph.instagram.com/access_token"
        
        params = {
            "grant_type": "ig_exchange_token",
            "client_secret": self.app_secret,
            "access_token": short_lived_token,
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Instagram long-lived token exchange failed: {result['error']}")
        
        return result
    
    def get_page_access_token(
        self, user_access_token: str, page_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get page access token (required for Instagram API)
        
        Args:
            user_access_token: User access token
            page_id: Optional page ID, otherwise gets first page
            
        Returns:
            Page access token and related info
        """
        # First, get pages
        url = f"{self.base_url}/me/accounts"
        params = {
            "access_token": user_access_token,
            "fields": "id,name,access_token,instagram_business_account",
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Failed to get pages: {result['error']}")
        
        pages = result.get("data", [])
        if not pages:
            raise Exception("No Facebook pages found. Connect a page to your Instagram account first.")
        
        # Find page with Instagram connection or use specified page
        target_page = None
        if page_id:
            target_page = next((p for p in pages if p["id"] == page_id), None)
        else:
            # Try to find page with Instagram connection
            target_page = next(
                (p for p in pages if p.get("instagram_business_account")), None
            )
            if not target_page:
                target_page = pages[0]  # Use first page if no Instagram connection found
        
        if not target_page:
            raise Exception(f"Page {page_id} not found" if page_id else "No pages available")
        
        return {
            "page_id": target_page["id"],
            "page_name": target_page["name"],
            "page_access_token": target_page["access_token"],
            "instagram_account_id": target_page.get("instagram_business_account", {}).get("id"),
        }
    
    def verify_instagram_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify an Instagram access token
        
        Args:
            access_token: Instagram access token
            
        Returns:
            Account information
        """
        url = "https://graph.instagram.com/me"
        params = {
            "access_token": access_token,
            "fields": "id,username,account_type",
        }
        
        response = requests.get(url, params=params)
        result = response.json()
        
        if "error" in result:
            raise Exception(f"Token verification failed: {result['error']}")
        
        return result


def generate_token_interactive(
    app_id: str,
    app_secret: str,
    redirect_uri: str = "http://localhost:8080/",
    save_to_config: bool = True,
) -> Dict[str, Any]:
    """
    Interactive function to generate Instagram access token
    
    This function:
    1. Opens browser for OAuth authorization
    2. Catches the redirect
    3. Exchanges code for token
    4. Gets page access token (for Instagram)
    5. Optionally exchanges for long-lived token
    6. Optionally saves to config
    
    Args:
        app_id: Facebook App ID
        app_secret: Facebook App Secret
        redirect_uri: OAuth redirect URI (must match app settings)
        save_to_config: Whether to save token to accounts.yaml
        
    Returns:
        Dictionary with access_token, instagram_account_id, username, etc.
    """
    helper = OAuthHelper(app_id, app_secret, redirect_uri)
    
    print("\n" + "="*60)
    print("Instagram Token Generator")
    print("="*60 + "\n")
    
    # Step 1: Generate authorization URL
    auth_url = helper.generate_authorization_url()
    print("Step 1: Opening browser for authorization...")
    print(f"URL: {auth_url}\n")
    
    # Start HTTP server to catch redirect
    code_received = [None]
    error_received = [None]
    
    def handle_callback(code, error):
        code_received[0] = code
        error_received[0] = error
    
    def make_handler(callback):
        class Handler(OAuthCallbackHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(callback, *args, **kwargs)
        return Handler
    
    # Parse redirect URI to get port
    parsed_uri = urlparse(redirect_uri)
    port = parsed_uri.port or 8080
    
    server = HTTPServer(
        ("localhost", port),
        make_handler(handle_callback),
    )
    
    server_thread = Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    
    # Open browser
    webbrowser.open(auth_url)
    
    print("Waiting for authorization...")
    print("(Complete the OAuth flow in your browser)\n")
    
    # Wait for callback
    while code_received[0] is None and error_received[0] is None:
        import time
        time.sleep(0.5)
    
    server.shutdown()
    server.server_close()
    
    if error_received[0]:
        raise Exception(f"OAuth error: {error_received[0]}")
    
    if not code_received[0]:
        raise Exception("No authorization code received")
    
    # Step 2: Exchange code for token
    print("Step 2: Exchanging code for access token...")
    token_response = helper.exchange_code_for_token(code_received[0])
    short_lived_token = token_response["access_token"]
    print(f"   [OK] Received short-lived token (expires in {token_response.get('expires_in', 'unknown')} seconds)\n")
    
    # Step 3: Get page access token (required for Instagram)
    print("Step 3: Getting page access token...")
    page_info = helper.get_page_access_token(short_lived_token)
    page_token = page_info["page_access_token"]
    instagram_account_id = page_info.get("instagram_account_id")
    
    print(f"   [OK] Page: {page_info['page_name']} (ID: {page_info['page_id']})")
    if instagram_account_id:
        print(f"   [OK] Instagram Account ID: {instagram_account_id}")
    else:
        print("   [WARNING] No Instagram account connected to this page")
    print()
    
    # Step 4: Verify Instagram token
    print("Step 4: Verifying Instagram token...")
    try:
        instagram_info = helper.verify_instagram_token(page_token)
        username = instagram_info.get("username", "unknown")
        print(f"   [OK] Instagram Username: {username}")
        print(f"   [OK] Instagram ID: {instagram_info.get('id')}")
        print(f"   [OK] Account Type: {instagram_info.get('account_type')}\n")
    except Exception as e:
        print(f"   [WARNING] Could not verify Instagram token: {e}")
        print("   The token might still work, but verification failed.\n")
        username = "unknown"
    
    # Step 5: Exchange for long-lived token
    print("Step 5: Exchanging for long-lived token (60 days)...")
    try:
        long_lived_response = helper.exchange_for_instagram_long_lived_token(page_token)
        final_token = long_lived_response["access_token"]
        expires_in = long_lived_response.get("expires_in", "unknown")
        print(f"   [OK] Long-lived token (expires in {expires_in} seconds ≈ {expires_in // 86400} days)\n")
    except Exception as e:
        print(f"   [WARNING] Could not exchange for long-lived token: {e}")
        print("   Using short-lived token instead.\n")
        final_token = page_token
        expires_in = "unknown"
    
    # Step 6: Save to config if requested
    result = {
        "access_token": final_token,
        "instagram_account_id": instagram_account_id,
        "username": username,
        "page_id": page_info["page_id"],
        "page_name": page_info["page_name"],
        "expires_in": expires_in,
    }
    
    if save_to_config:
        print("Step 6: Saving to config/accounts.yaml...")
        try:
            accounts_path = Path("config/accounts.yaml")
            if accounts_path.exists():
                with open(accounts_path, "r") as f:
                    accounts_data = yaml.safe_load(f) or {"accounts": []}
            else:
                accounts_data = {"accounts": []}
            
            # Check if account already exists (by username or create new)
            account_id = f"account_{username}" if username != "unknown" else f"account_{len(accounts_data['accounts']) + 1}"
            
            new_account = {
                "account_id": account_id,
                "username": username,
                "access_token": final_token,
                "proxy": {"enabled": False},
                "warming": {
                    "enabled": True,
                    "daily_actions": 10,
                    "action_types": ["like", "comment", "follow", "story_view"],
                },
            }
            
            # Add or update account
            existing_index = next(
                (i for i, acc in enumerate(accounts_data["accounts"]) if acc.get("username") == username),
                None
            )
            
            if existing_index is not None:
                accounts_data["accounts"][existing_index] = new_account
                print(f"   [OK] Updated existing account: {account_id}")
            else:
                accounts_data["accounts"].append(new_account)
                print(f"   [OK] Added new account: {account_id}")
            
            with open(accounts_path, "w") as f:
                yaml.dump(accounts_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            
            print("   [OK] Configuration saved!\n")
        except Exception as e:
            print(f"   [WARNING] Could not save to config: {e}\n")
    
    print("="*60)
    print("[SUCCESS] Token generation complete!")
    print("="*60 + "\n")
    
    return result