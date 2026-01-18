# Fix Cloudinary Invalid Signature Error

The error "Invalid Signature" means your **API Secret** is incorrect.

## How to Fix:

### Step 1: Get Your Correct Cloudinary Credentials

1. Go to: https://cloudinary.com/console
2. Log in to your account
3. Click on **Dashboard**
4. Find the **Account Details** section
5. You'll see:
   - **Cloud name**: `dtgesg0ps` (this is correct)
   - **API Key**: `858581386324189` (verify this)
   - **API Secret**: Click "Reveal" to show it

### Step 2: Update Your .env File

Your current `.env` file has an incorrect API Secret. Update it:

1. Open `.env` file in `D:\InstaForge`
2. Update the API Secret with the correct one from Cloudinary dashboard:

```
CLOUDINARY_CLOUD_NAME=dtgesg0ps
CLOUDINARY_API_KEY=858581386324189
CLOUDINARY_API_SECRET=YOUR_CORRECT_API_SECRET_HERE
```

**Important:**
- Copy the EXACT API Secret from Cloudinary (it's case-sensitive)
- Don't add quotes or spaces
- Make sure you copied the entire secret

### Step 3: Restart Your Server

After updating the `.env` file:

```powershell
# Stop the server (Ctrl+C)
# Then restart:
python web_server.py
```

### Step 4: Test Again

Try uploading an image through the web interface. You should see:
```
DEBUG: Successfully uploaded to Cloudinary: https://res.cloudinary.com/...
```

Instead of Cloudflare URLs!

## Common Mistakes:

1. **Copying the wrong secret** - Make sure you're copying the API Secret, not the API Key
2. **Adding spaces** - Don't add spaces before or after the secret
3. **Using quotes** - Don't wrap the secret in quotes in the .env file
4. **Old secret** - If you regenerated your secret, make sure you're using the NEW one

## If You Regenerated Your API Secret:

If you clicked "Regenerate" on your API Secret, you MUST update your .env file with the NEW secret. Old secrets won't work.
