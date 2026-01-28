# Multi-Account System Documentation

## Overview

InstaForge's multi-account system ensures that all features work seamlessly across all connected accounts without manual intervention. The system automatically handles account onboarding, health monitoring, service registration, and recovery.

## Key Features

- **Automatic Onboarding**: New accounts are automatically validated and registered
- **Health Monitoring**: Continuous health checks every 10 minutes
- **Dynamic Reload**: Accounts can be reloaded without server restart
- **Service Auto-Registration**: All services automatically include new accounts
- **Fail-Safe Mode**: Broken accounts are automatically disabled
- **Status Dashboard**: Real-time account health visibility

## Architecture

### Components

1. **Account Onboarding Service** (`src/services/account_onboarding.py`)
   - Validates new accounts
   - Registers accounts in all services
   - Initializes features per account

2. **Account Health Service** (`src/services/account_health.py`)
   - Monitors account health every 10 minutes
   - Checks token validity, permissions, API connectivity
   - Tracks health status per account

3. **Account Service** (`src/services/account_service.py`)
   - Manages account lifecycle
   - Provides dynamic add/remove/update methods
   - Handles client initialization

4. **InstaForgeApp** (`src/app.py`)
   - Orchestrates all services
   - Provides `reload_accounts()` method
   - Manages service lifecycle

## Onboarding Flow

When a new account is added:

1. **Validate Access Token**
   - Checks token format and structure
   - Verifies token is not empty

2. **Check Permissions**
   - Verifies required Instagram API permissions
   - Tests account info retrieval

3. **Verify IG Connection**
   - Connects to Instagram Graph API
   - Retrieves account information
   - Confirms account is accessible

4. **Register Webhook** (if applicable)
   - Webhooks are configured manually in Meta App Dashboard
   - This step is a placeholder for future automation

5. **Register Scheduler Jobs**
   - Warming service automatically includes all accounts
   - No per-account registration needed

6. **Initialize AI DM**
   - Checks if AI DM is enabled
   - Verifies OpenAI API key is configured

7. **Initialize Comment Monitor**
   - Starts comment monitoring for the account
   - Registers account in monitoring service

8. **Initialize Posting Queue**
   - Posting service uses account_service
   - No per-account initialization needed

9. **Initialize Safety Rules**
   - Rate limiters are shared across accounts
   - Safety rules are service-level

10. **Save Status**
    - Account marked as ACTIVE, INACTIVE, or FAILED
    - Status saved for health monitoring

### Onboarding Result Status

- **ACTIVE**: Account is fully operational
- **INACTIVE**: Critical steps failed, account disabled
- **FAILED**: Onboarding failed completely

## Health Monitoring

### Health Checks

The system performs comprehensive health checks every 10 minutes:

1. **Token Validity**
   - Verifies access token is valid
   - Tests token with API call
   - Checks for token expiration

2. **Permission Status**
   - Verifies required permissions are granted
   - Tests account info retrieval

3. **API Connectivity**
   - Tests connection to Instagram Graph API
   - Measures response time
   - Checks for API errors

4. **Webhook Status** (placeholder)
   - Webhooks require manual verification
   - Status is marked as "unknown"

5. **Scheduler Status**
   - Verifies account is included in scheduled tasks
   - Checks scheduler is running

### Health Status Levels

- **HEALTHY**: All critical checks pass
- **WARNING**: Some non-critical checks failed
- **CRITICAL**: Critical checks failed
- **UNKNOWN**: Unable to determine status

## Service Reloader

The `reload_accounts()` method in `InstaForgeApp`:

1. Reloads accounts from config
2. Updates account_service with new accounts
3. Updates proxy_manager
4. Re-registers accounts in comment monitor
5. Re-schedules warming (if needed)

### When to Reload

- New account added to config
- Account token updated
- Account permissions changed
- Account removed from config

### Reload Process

```python
# In InstaForgeApp
results = app.reload_accounts()

# Returns:
{
    "accounts_loaded": 5,
    "accounts_added": ["account_3"],
    "accounts_removed": ["account_1"],
    "accounts_updated": ["account_2"],
    "errors": []
}
```

## Dynamic Account Management

### Adding Accounts

```python
# Via AccountService
account = Account(
    account_id="new_account",
    username="new_user",
    access_token="IGAAT...",
    # ... other fields
)

account_service.add_account(account)

# Via Onboarding Service (recommended)
result = onboarding_service.onboard_account(account, app_instance=app)
```

### Removing Accounts

```python
account_service.remove_account(account_id)
```

### Updating Accounts

```python
# Update account
account.access_token = "new_token"
account_service.update_account(account)
```

## API Endpoints

### Get All Account Status

```
GET /api/accounts/status
```

Returns health status for all accounts.

**Response:**
```json
{
    "status": "success",
    "accounts": [
        {
            "account_id": "account_1",
            "username": "user1",
            "status": "healthy",
            "checks": {
                "token": {"status": "ok", ...},
                "permissions": {"status": "ok", ...},
                "api_connectivity": {"status": "ok", ...}
            },
            "timestamp": "2026-01-27T10:00:00"
        }
    ],
    "total": 1
}
```

### Get Single Account Status

```
GET /api/accounts/{account_id}/status
```

Returns health status for a specific account.

### Onboard Account

```
POST /api/accounts/{account_id}/onboard
```

Runs onboarding pipeline for an account.

**Response:**
```json
{
    "status": "success",
    "onboarding_result": {
        "account_id": "account_1",
        "status": "active",
        "steps_completed": ["validate_token", "verify_connection", ...],
        "steps_failed": [],
        "errors": {},
        "timestamp": "2026-01-27T10:00:00"
    }
}
```

### Reload Accounts

```
POST /api/accounts/reload
```

Reloads accounts from config and re-registers in all services.

**Response:**
```json
{
    "status": "success",
    "results": {
        "accounts_loaded": 5,
        "accounts_added": ["account_3"],
        "accounts_removed": ["account_1"],
        "accounts_updated": [],
        "errors": []
    }
}
```

## UI Dashboard

### Account Status Page

Access via: `/accounts`

Features:
- Real-time account health status
- Color-coded status indicators
- Detailed health check results
- Auto-refresh every 60 seconds
- Manual refresh button
- Reload accounts button

### Status Indicators

- **Green (Healthy)**: All checks passing
- **Yellow (Warning)**: Some non-critical checks failed
- **Red (Critical)**: Critical checks failed
- **Gray (Unknown)**: Status cannot be determined

## Fail-Safe Mode

When an account is detected as broken:

1. **Automatic Disable**
   - Automation features disabled
   - Posting stopped
   - DMs stopped
   - Comment monitoring stopped

2. **Notification**
   - Error logged with account_id
   - Status updated in dashboard
   - Health check continues monitoring

3. **Recovery**
   - Health checks continue
   - When account recovers, features re-enabled
   - Manual onboarding can be triggered

## Common Issues

### Account Not Appearing in Services

**Problem**: Account added but not working in features.

**Solution**:
1. Check account status: `GET /api/accounts/{account_id}/status`
2. Run onboarding: `POST /api/accounts/{account_id}/onboard`
3. Reload accounts: `POST /api/accounts/reload`

### Token Expired

**Problem**: Health check shows token as failed.

**Solution**:
1. Update token in config
2. Reload accounts: `POST /api/accounts/reload`
3. Or update account: `PUT /api/config/accounts/{account_id}`

### Permission Errors

**Problem**: Permission check fails.

**Solution**:
1. Verify required permissions in Meta App Dashboard
2. Re-authorize account if needed
3. Check token has correct scopes

### Scheduler Not Running

**Problem**: Warming actions not scheduled for new account.

**Solution**:
1. Warming service is global and includes all accounts automatically
2. Verify account exists: `GET /api/accounts/status`
3. Check warming config in settings

### Comment Monitor Not Working

**Problem**: Comment monitoring not active for account.

**Solution**:
1. Check comment monitor status
2. Reload accounts: `POST /api/accounts/reload`
3. Verify account has comment_to_dm enabled in config

## Testing

### Test Scenarios

1. **Single Account**
   - Add one account
   - Verify all services include it
   - Check health status

2. **Multiple Accounts**
   - Add 5 accounts
   - Verify all services include all accounts
   - Check health status for each

3. **Account Addition**
   - Add account while system running
   - Reload accounts
   - Verify new account appears in all services

4. **Account Removal**
   - Remove account from config
   - Reload accounts
   - Verify account removed from all services

5. **Account Update**
   - Update account token
   - Reload accounts
   - Verify new token is used

### Verification Checklist

- [ ] All accounts appear in status dashboard
- [ ] Health checks running for all accounts
- [ ] Comment monitor includes all accounts
- [ ] Warming service includes all accounts
- [ ] Posting service includes all accounts
- [ ] AI DM works for all accounts (if enabled)
- [ ] Account reload works without errors
- [ ] Onboarding completes successfully

## Logging

All account operations are logged with structured logging:

```python
logger.info(
    "Account onboarding completed",
    account_id=account_id,
    status=status.value,
    steps_completed=len(steps_completed),
    steps_failed=len(steps_failed),
)
```

### Log Fields

- `account_id`: Account identifier
- `service`: Service name (onboarding, health, etc.)
- `status`: Operation status
- `error_code`: Error code if failed
- `auto_fix_attempted`: Whether auto-fix was attempted

## Best Practices

1. **Always Use Onboarding Service**
   - Don't add accounts directly
   - Use onboarding service for proper initialization

2. **Monitor Health Status**
   - Check status dashboard regularly
   - Set up alerts for critical failures

3. **Reload After Config Changes**
   - Always reload after adding/removing accounts
   - Reload after token updates

4. **Handle Failures Gracefully**
   - Don't let one broken account break the system
   - Use fail-safe mode for broken accounts

5. **Test Before Production**
   - Test with multiple accounts
   - Verify all services work
   - Check health monitoring

## Future Enhancements

- Automatic webhook registration
- Auto-fix for common issues
- Email/SMS notifications for failures
- Account usage analytics
- Performance metrics per account
- Automated token refresh

## Support

For issues or questions:
1. Check logs: `logs/instaforge.log`
2. Review account status dashboard
3. Check health check results
4. Review onboarding results

## Related Documentation

- [Account Configuration](ACCOUNT_CONFIG.md)
- [Token Generation](TOKEN_GENERATION_GUIDE.md)
- [Service Architecture](ARCHITECTURE.md)
- [Troubleshooting](TROUBLESHOOTING.md)
