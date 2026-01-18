# Quick Fix for "Invalid App ID" Error

## The Problem
Error Code 190 means your App ID and App Secret don't match, or the app configuration is wrong.

## Step-by-Step Fix

### 1. Get Your Real App ID and Secret

1. Go to: **https://developers.facebook.com/apps/904357532549094/settings/basic/**
   - (Replace `904357532549094` with your actual app ID if different)

2. **Copy the App ID:**
   - It should be a 15-digit number
   - Copy it exactly as shown (no spaces, no quotes)

3. **Copy the App Secret:**
   - Click "Show" next to "App Secret"
   - Enter your Facebook password if prompted
   - Copy the secret exactly (no spaces, no quotes)

4. **Update `config/app_credentials.yaml`:**
   ```yaml
   instagram:
     app_id: "PASTE_YOUR_APP_ID_HERE"
     app_secret: "PASTE_YOUR_APP_SECRET_HERE"
   ```
   - Make sure there are quotes around the values
   - No extra spaces or characters

### 2. Add Instagram Product

1. Go to your app dashboard: **https://developers.facebook.com/apps/904357532549094/**
2. Click "Add Product" in the left sidebar
3. Find "Instagram Graph API"
4. Click "Set Up"

### 3. Configure OAuth Redirect URI

1. In your app dashboard, go to: **Products > Facebook Login > Settings**
2. Under "Valid OAuth Redirect URIs", add:
   - `http://localhost:8080/`
   - `http://localhost:8080`
3. Click "Save Changes"

### 4. Verify Your Instagram Account

- Your Instagram account must be **Business** or **Creator** (not Personal)
- It must be connected to a Facebook Page
- To check: Instagram app > Settings > Account type and tools > Business or Creator account

## Test Again

After fixing the credentials:

```bash
python check_app_setup.py
```

Then try:

```bash
python generate_token.py
```

## Common Issues

- **App ID looks correct but still fails**: The App Secret is probably wrong
- **Can't see App Secret**: Make sure you're logged into the account that created the app
- **App not found**: You might have the wrong App ID, or the app was deleted
