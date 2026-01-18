# How to Get Instagram Access Token

## Quick Method (Recommended)

1. **Run the token generator:**
   ```bash
   python generate_token.py
   ```

2. **The script will:**
   - Open your browser automatically
   - Ask you to authorize the app
   - Automatically complete the OAuth flow
   - Save the token to `config/accounts.yaml`

3. **Watch the terminal output** - You should see:
   - Step 1: Opening browser for authorization
   - Step 2: Exchanging code for access token
   - Step 3: Getting page access token
   - Step 4: Verifying Instagram token
   - Step 5: Exchanging for long-lived token
   - Step 6: Saving to config/accounts.yaml
   - **[SUCCESS] Token generation complete!**

4. **After completion, verify it worked:**
   ```bash
   python test_account_setup.py
   ```

## If generate_token.py doesn't work

### Manual Method via Graph API Explorer

1. Go to: https://developers.facebook.com/tools/explorer/

2. Select your app: `1903716743593562` (from dropdown at top)

3. Click "Get Token" → "Get User Access Token"

4. Select these permissions:
   - `instagram_basic`
   - `pages_read_engagement`
   - `instagram_content_publish`
   - `pages_show_list`

5. Click "Generate Access Token"

6. **IMPORTANT:** You'll get a short-lived token. You need to:
   - Use this token to get your Facebook Page's access token
   - Then use that Page token as your Instagram access token

7. To get Page token:
   - In Graph API Explorer, use: `GET /me/accounts?fields=id,name,access_token,instagram_business_account`
   - Find the page with `instagram_business_account`
   - Copy the `access_token` from that page
   - This is your Instagram access token!

8. **Update `config/accounts.yaml`:**
   ```yaml
   accounts:
     - account_id: "your_instagram_account_id"
       username: "your_instagram_username"
       access_token: "PASTE_YOUR_PAGE_ACCESS_TOKEN_HERE"
   ```

## Token Types Explained

- **Short-lived token:** Expires in 1 hour
- **Long-lived token:** Expires in 60 days (better for automation)
- **Page Access Token:** This is what you need for Instagram API (works like Instagram token)

## Troubleshooting

**Error: "Invalid OAuth access token"**
- The token expired (short-lived tokens last 1 hour)
- The token format is wrong
- Run `generate_token.py` again to get a fresh token

**Error: "Invalid App ID"**
- Make sure `config/app_credentials.yaml` has correct App ID: `1903716743593562`
- Check: https://developers.facebook.com/apps/1903716743593562/settings/basic/

**Token not saving:**
- Make sure the `generate_token.py` script completes fully
- Check terminal output for any errors
- Verify `config/accounts.yaml` is writable
