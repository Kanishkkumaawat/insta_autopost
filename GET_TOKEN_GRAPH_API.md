# Get Instagram Token via Graph API Explorer

## Step-by-Step Instructions

### Step 1: Generate Access Token with Permissions

1. **In Graph API Explorer**, click the **"Generate Access Token"** button (blue button, top right)

2. **A popup will appear** - Select these permissions:
   - ✅ `pages_show_list`
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`
   - ✅ `pages_read_engagement`

3. Click **"Generate Access Token"** in the popup

4. **You'll be redirected** to Facebook login - authorize the app

5. **You'll be redirected back** - the new token will appear in the "Access Token" field

### Step 2: Get Your Pages

1. In Graph API Explorer, use this query:
   ```
   GET /me/accounts
   ```

2. Or with specific fields:
   ```
   GET /me/accounts?fields=id,name,access_token,instagram_business_account
   ```

3. Click **"Submit"**

4. **You should see** a response like:
   ```json
   {
     "data": [
       {
         "id": "123456789",
         "name": "Your Page Name",
         "access_token": "PAGE_ACCESS_TOKEN_HERE",
         "instagram_business_account": {
           "id": "17841444586838008"
         }
       }
     ]
   }
   ```

### Step 3: Get Instagram Token (Two Methods)

#### Method A: Use Page Access Token Directly

The `access_token` from the page response **IS** your Instagram access token!

1. Copy the `access_token` from the page that has `instagram_business_account`
2. Use this token directly in `config/accounts.yaml`

#### Method B: Get Instagram Account Info

1. Use the `instagram_business_account.id` from the response above
2. Query:
   ```
   GET /{instagram_account_id}?fields=id,username,account_type
   ```
   (Replace `{instagram_account_id}` with the ID from step above)

3. Use the **Page Access Token** from Step 2 for authentication

### Step 4: Update Your Config

Update `config/accounts.yaml`:

```yaml
accounts:
  - account_id: "your_instagram_account_id"  # From instagram_business_account.id
    username: "your_instagram_username"      # From Instagram query
    access_token: "PAGE_ACCESS_TOKEN_HERE"   # From pages query (this works as Instagram token!)
    proxy:
      enabled: false
    warming:
      enabled: true
      daily_actions: 10
      action_types:
        - "like"
        - "comment"
        - "follow"
        - "story_view"
```

### Step 5: Verify It Works

```bash
python test_account_setup.py
```

## Important Notes

- **Page Access Token = Instagram Access Token** - The access token from your Facebook Page works directly with Instagram API
- If `data` array is empty, you either:
  - Don't have any Facebook Pages
  - Your Instagram isn't connected to a Page
  - Your token doesn't have the right permissions (need to regenerate)
- If you see permissions with red X, you need to generate a new token with those permissions

## Troubleshooting

**Empty data array:**
- Make sure you have a Facebook Page
- Make sure your Instagram Business account is connected to that Page
- Make sure your token has `pages_read_engagement` permission

**No instagram_business_account in response:**
- Your Instagram account must be Business or Creator (not Personal)
- It must be connected to a Facebook Page
- Check: Instagram app → Settings → Business or Creator account → Page connection
