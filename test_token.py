"""Quick script to test Instagram access token"""

import requests
import sys

def test_token(token):
    """Test if an Instagram access token is valid"""
    print(f"Testing token: {token[:20]}...{token[-20:]}")
    print(f"Token length: {len(token)} characters")
    print()
    
    # Try to get account info using the token
    url = "https://graph.instagram.com/v18.0/me"
    params = {
        "fields": "id,username,account_type",
        "access_token": token
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        result = response.json()
        
        if response.status_code == 200:
            if "error" in result:
                error = result["error"]
                error_code = error.get("code")
                error_message = error.get("message", "Unknown error")
                error_type = error.get("type", "Unknown")
                
                print(f"[X] TOKEN INVALID")
                print(f"Error Type: {error_type}")
                print(f"Error Code: {error_code}")
                print(f"Error Message: {error_message}")
                
                if error_code == 190:
                    print("\nThis error usually means:")
                    print("- Token is expired or invalid")
                    print("- Token format is corrupted (check for URL encoding issues)")
                    print("- Token is not a valid Instagram Graph API token")
                
                return False
            else:
                print(f"[OK] TOKEN VALID!")
                print(f"Instagram ID: {result.get('id')}")
                print(f"Username: {result.get('username')}")
                print(f"Account Type: {result.get('account_type')}")
                return True
        else:
            print(f"[X] HTTP ERROR: {response.status_code}")
            print(f"Response: {result}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"[X] REQUEST FAILED: {str(e)}")
        return False

if __name__ == "__main__":
    # Get token from command line or use the one from accounts.yaml
    if len(sys.argv) > 1:
        token = sys.argv[1]
    else:
        # Read from accounts.yaml
        import yaml
        with open("config/accounts.yaml", "r") as f:
            config = yaml.safe_load(f)
            token = config["accounts"][0]["access_token"]
    
    success = test_token(token)
    sys.exit(0 if success else 1)
