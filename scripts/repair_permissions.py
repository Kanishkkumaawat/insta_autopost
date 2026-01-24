import sys
import os
import json
import shutil
import logging
import requests
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.utils.config import config_manager

# Setup logging
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "permission_repair.log")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, mode='w'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("permission_repair")

class PermissionRepairTool:
    GRAPH_API_URL = "https://graph.facebook.com/v18.0"
    BASIC_API_URL = "https://graph.instagram.com/v18.0"
    
    REQUIRED_SCOPES = [
        "instagram_basic",
        "instagram_manage_comments",
        "instagram_manage_messages",
        "instagram_content_publish",
        "pages_show_list",
        "pages_read_engagement"
    ]

    def __init__(self):
        try:
            self.accounts = config_manager.load_accounts()
        except Exception as e:
            logger.error(f"Failed to load accounts: {e}")
            self.accounts = []
        
        self.report = []

    def log(self, msg: str, level: str = "INFO"):
        """Log helper that also adds to internal report"""
        if level == "INFO":
            logger.info(msg)
        elif level == "WARNING":
            logger.warning(msg)
        elif level == "ERROR":
            logger.error(msg)
        elif level == "SUCCESS":
            logger.info(f"✅ {msg}")
        
        self.report.append(f"[{level}] {msg}")

    def detect_token_type(self, token: str) -> str:
        """Detect token type based on prefix and length"""
        if token.startswith("IGAAT"):
            return "INSTAGRAM_BASIC_DISPLAY_TOKEN" # Short-lived or Long-lived Basic Display
        elif token.startswith("EAAB"):
            return "FACEBOOK_PAGE_TOKEN" # Graph API Token (Page/User)
        elif token.startswith("IGQ"):
            return "INSTAGRAM_LEGACY_TOKEN"
        else:
            return "UNKNOWN_FORMAT"

    def validate_token_permissions(self, token: str) -> Dict[str, Any]:
        """
        Validate permissions using the debug_token endpoint or me/permissions.
        Note: debug_token requires an app access token usually, but we try self-inspection via me/permissions.
        """
        # Try Graph API first (for EAAB tokens)
        url = f"{self.GRAPH_API_URL}/me/permissions"
        params = {"access_token": token}
        
        try:
            resp = requests.get(url, params=params)
            data = resp.json()
            
            if "data" in data:
                return {"api": "GRAPH", "permissions": data["data"]}
            
            # If Graph API failed, try Basic Display API (for IGAAT tokens)
            if "error" in data:
                url_basic = f"{self.BASIC_API_URL}/me/permissions" # Basic display doesn't fully support this standardly
                resp_basic = requests.get(url_basic, params=params)
                data_basic = resp_basic.json()
                
                if "data" in data_basic:
                    return {"api": "BASIC", "permissions": data_basic["data"]}
                
                return {"api": "ERROR", "error": data.get("error", {}).get("message")}
                
        except Exception as e:
            return {"api": "EXCEPTION", "error": str(e)}
            
        return {"api": "UNKNOWN", "permissions": []}

    def check_page_mapping(self, token: str, expected_account_id: str) -> Dict[str, Any]:
        """
        Check if the token is linked to a Facebook Page that is connected to the expected Instagram Account.
        This is critical for Graph API comments.
        """
        # 1. Check if token belongs to a Page or User
        url_me = f"{self.GRAPH_API_URL}/me"
        params = {"access_token": token, "fields": "id,name,accounts{id,name,instagram_business_account}"}
        
        try:
            resp = requests.get(url_me, params=params)
            data = resp.json()
            
            if "error" in data:
                return {"status": "ERROR", "message": data["error"]["message"]}
            
            # If "accounts" is present, this is likely a User Token with Page access
            if "accounts" in data:
                pages = data["accounts"].get("data", [])
                for page in pages:
                    ig_account = page.get("instagram_business_account")
                    if ig_account and ig_account.get("id") == expected_account_id:
                        return {
                            "status": "MAPPED_VIA_USER", 
                            "page_id": page.get("id"),
                            "page_name": page.get("name"),
                            "ig_id": ig_account.get("id")
                        }
                return {"status": "NOT_MAPPED", "pages_found": len(pages)}
            
            # If we queried /me and got a page directly (if token is page token)
            # Check for instagram_business_account field directly
            url_page = f"{self.GRAPH_API_URL}/me"
            params_page = {"access_token": token, "fields": "id,name,instagram_business_account"}
            resp_page = requests.get(url_page, params=params_page)
            data_page = resp_page.json()
            
            if "instagram_business_account" in data_page:
                ig_id = data_page["instagram_business_account"].get("id")
                if ig_id == expected_account_id:
                    return {
                        "status": "DIRECT_PAGE_TOKEN",
                        "page_id": data_page.get("id"),
                        "page_name": data_page.get("name"),
                        "ig_id": ig_id
                    }
                else:
                    return {"status": "WRONG_MAPPING", "found_ig_id": ig_id, "expected": expected_account_id}
            
            return {"status": "NO_IG_LINKED", "page_name": data_page.get("name")}

        except Exception as e:
            return {"status": "EXCEPTION", "message": str(e)}

    def test_live_access(self, token: str, account_id: str):
        """Test actual API calls to verify access"""
        # Test 1: Fetch Media
        self.log("  > Testing Media Fetch...")
        url = f"{self.GRAPH_API_URL}/{account_id}/media"
        params = {"access_token": token, "limit": 1}
        resp = requests.get(url, params=params)
        data = resp.json()
        
        if "error" in data:
            self.log(f"    FAILED: {data['error']['message']}", "ERROR")
            return None
        
        media_list = data.get("data", [])
        if not media_list:
            self.log("    SUCCESS: Media access OK (but no media found)", "SUCCESS")
            return None
            
        media_id = media_list[0]['id']
        self.log(f"    SUCCESS: Media access OK (ID: {media_id})", "SUCCESS")
        
        # Test 2: Fetch Comments
        self.log(f"  > Testing Comments Fetch for Media {media_id}...")
        url_comments = f"{self.GRAPH_API_URL}/{media_id}/comments"
        resp_c = requests.get(url_comments, params=params)
        data_c = resp_c.json()
        
        if "error" in data_c:
            self.log(f"    FAILED: {data_c['error']['message']}", "ERROR")
            self.log("    ROOT CAUSE: Token likely lacks 'instagram_manage_comments' or is Basic Display.", "ERROR")
        else:
            self.log("    SUCCESS: Comment access OK", "SUCCESS")

    def run(self):
        self.log("==================================================")
        self.log("INSTAGRAM PERMISSION REPAIR TOOL")
        self.log("==================================================")
        
        if not self.accounts:
            self.log("No accounts found in data/accounts.yaml", "ERROR")
            return

        for acc in self.accounts:
            self.log(f"\nAnalyzing Account: {acc.username} (ID: {acc.account_id})")
            token = acc.access_token
            
            # 1. Token Type
            token_type = self.detect_token_type(token)
            self.log(f"Token Type: {token_type}")
            
            if token_type == "INSTAGRAM_BASIC_DISPLAY_TOKEN":
                self.log("CRITICAL ERROR: You are using a Basic Display Token (IGAAT...).", "ERROR")
                self.log("Basic Display Tokens CANNOT read comments or send DMs.", "ERROR")
                self.log("FIX: You must generate a Graph API Token (starts with EAAB...).", "WARNING")
                self.log("ACTION: Please re-authenticate using Facebook Login for Business.", "WARNING")
                continue # Cannot repair a basic token into a graph token
                
            if token_type == "UNKNOWN_FORMAT":
                self.log("WARNING: Token format unrecognized. Proceeding with checks anyway.", "WARNING")

            # 2. Page Mapping
            self.log("Checking Facebook Page <-> Instagram Mapping...")
            mapping = self.check_page_mapping(token, acc.account_id)
            self.log(f"Mapping Status: {mapping['status']}")
            
            if mapping['status'] == "ERROR":
                self.log(f"API Error: {mapping.get('message')}", "ERROR")
            elif mapping['status'] == "NO_IG_LINKED":
                self.log("The Page associated with this token does NOT have an Instagram account connected.", "ERROR")
                self.log("FIX: Go to Facebook Page Settings > Linked Accounts > Instagram and connect.", "WARNING")
            elif mapping['status'] == "WRONG_MAPPING":
                self.log(f"Token is linked to IG ID {mapping.get('found_ig_id')}, but config expects {acc.account_id}", "ERROR")
            elif mapping['status'] in ["DIRECT_PAGE_TOKEN", "MAPPED_VIA_USER"]:
                self.log(f"Confirmed Link: Page '{mapping.get('page_name')}' -> IG '{acc.account_id}'", "SUCCESS")

            # 3. Permissions
            self.log("Verifying Permissions...")
            perm_data = self.validate_token_permissions(token)
            
            if perm_data['api'] == "GRAPH":
                perms = perm_data['permissions']
                granted = [p['permission'] for p in perms if p['status'] == 'granted']
                
                missing = []
                for req in self.REQUIRED_SCOPES:
                    if req not in granted:
                        missing.append(req)
                
                if missing:
                    self.log(f"MISSING PERMISSIONS: {', '.join(missing)}", "ERROR")
                    self.log("FIX: Re-generate token and select ALL required pages and permissions.", "WARNING")
                else:
                    self.log("All required permissions are GRANTED.", "SUCCESS")
                    
                # 4. Live Test
                self.test_live_access(token, acc.account_id)
            else:
                self.log(f"Could not validate permissions via Graph API. Error: {perm_data.get('error')}", "ERROR")

        self.log("\n==================================================")
        self.log(f"Report saved to {LOG_FILE}")

if __name__ == "__main__":
    tool = PermissionRepairTool()
    tool.run()
