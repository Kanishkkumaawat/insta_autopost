"""Test if the account setup is working"""

from src.utils.config_loader import ConfigLoader
from src.services.account_service import AccountService
from src.api.rate_limiter import RateLimiter
from src.proxies.proxy_manager import ProxyManager

print("\n" + "="*60)
print("Testing Account Setup")
print("="*60 + "\n")

try:
    # Load configuration
    print("1. Loading configuration...")
    loader = ConfigLoader()
    config = loader.load_settings()
    accounts = loader.load_accounts()
    
    print(f"   [OK] Loaded {len(accounts)} account(s)")
    for acc in accounts:
        print(f"      - {acc.account_id}: {acc.username}")
    
    # Initialize services
    print("\n2. Initializing services...")
    rate_limiter = RateLimiter(
        requests_per_hour=config.instagram.rate_limit["requests_per_hour"],
        requests_per_minute=config.instagram.rate_limit["requests_per_minute"],
    )
    
    accounts_dict = {acc.account_id: acc for acc in accounts}
    proxy_manager = ProxyManager(
        accounts=accounts_dict,
        connection_timeout=config.proxies.connection_timeout,
    )
    
    account_service = AccountService(
        accounts=accounts,
        rate_limiter=rate_limiter,
        proxy_manager=proxy_manager,
    )
    print("   [OK] Services initialized")
    
    # Verify account
    print("\n3. Verifying Instagram account...")
    account_id = accounts[0].account_id
    account_info = account_service.verify_account(account_id)
    
    print("\n   [SUCCESS] Account verified!")
    print(f"   - Instagram ID: {account_info.get('id')}")
    print(f"   - Username: {account_info.get('username')}")
    print(f"   - Account Type: {account_info.get('account_type')}")
    
    print("\n" + "="*60)
    print("[SUCCESS] Everything is working! Your account is ready to use.")
    print("="*60 + "\n")
    
    print("Next Steps:")
    print("1. Run the main application: python main.py")
    print("2. The app will automatically handle warming actions")
    print("3. You can post to Instagram using the posting service")
    print("\nYour token has been saved to config/accounts.yaml")
    
except Exception as e:
    print(f"\n[ERROR] {str(e)}")
    print("\nCommon issues:")
    print("- Token may be expired or invalid")
    print("- Token may not have required permissions")
    print("- Instagram account may not be connected properly")
    import traceback
    traceback.print_exc()
