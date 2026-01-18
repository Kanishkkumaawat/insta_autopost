"""Check if token generation completed successfully"""

import yaml
from pathlib import Path

print("\n" + "="*60)
print("Token Generation Status Check")
print("="*60 + "\n")

# Check accounts.yaml
accounts_path = Path("config/accounts.yaml")
if accounts_path.exists():
    with open(accounts_path, "r") as f:
        accounts_data = yaml.safe_load(f)
    
    accounts = accounts_data.get("accounts", [])
    print(f"Found {len(accounts)} account(s) in config:\n")
    
    for i, acc in enumerate(accounts, 1):
        print(f"Account {i}:")
        print(f"  account_id: {acc.get('account_id')}")
        print(f"  username: {acc.get('username')}")
        token = acc.get('access_token', '')
        if token:
            print(f"  access_token: {token[:30]}...{token[-10:]} (length: {len(token)})")
        else:
            print(f"  access_token: (MISSING)")
        print()
else:
    print("[ERROR] config/accounts.yaml not found")

print("="*60)
print("\nIf the token generation completed successfully, you should see:")
print("- A new account entry with your Instagram username")
print("- A new access_token (long string, 200+ characters)")
print("\nIf you still see the old token, the generation may not have completed.")
print("Check the terminal where you ran 'python generate_token.py' for any errors.")
print("="*60 + "\n")
