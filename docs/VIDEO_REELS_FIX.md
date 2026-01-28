# Video & Reels Posting - Fixed & Integrated

## Problem
- Video and Reels posts were not working properly
- URLs from Cloudinary/Firebase were not being handled correctly
- Reels were being treated as regular video posts (Instagram API requires `REELS` type)

## Fixes Applied

### 1. **Reels Support** ✅
- **Before**: Reels were converted to "video" type
- **After**: Reels now use `media_type: "REELS"` in Instagram API
- **Location**: `src/services/posting_service.py`, `src/api/instagram_client.py`

### 2. **Instagram API Integration** ✅
- Added `media_type` parameter to `create_media_container()`
- Reels use `media_type: "REELS"` (Instagram requirement)
- Regular videos use `media_type: "VIDEO"`
- **Location**: `src/api/instagram_client.py`

### 3. **Video/Reels Processing** ✅
- Added proper waiting for video/reels container processing
- Reels get 10 seconds initial wait (vs 5 for videos)
- Status checking with timeout (max 60 seconds)
- **Location**: `src/services/posting_service.py`

### 4. **URL Validation** ✅
- **Own server**: URLs that point to this app’s host (same as `BASE_URL`/`APP_URL` or request host) are allowed for video/reels — no external host needed.
- Blocks unreliable tunnel hosts (Cloudflare tunnels, ngrok) only when the URL is *not* your own server.
- Clear error messages direct users to use “Upload file” (your server) or a stable public HTTPS URL.
- **Location**: `web/api.py`

### 5. **Error Messages** ✅
- Detailed error messages for video/reels failures
- Explains why Cloudflare/ngrok don't work
- Provides step-by-step solutions
- **Location**: `src/api/instagram_client.py`

### 6. **UI Improvements** ✅
- Warning banner when posting video/reels via URL
- Auto-suggests "Post by URL" when selecting video/reels
- Validates URLs before submission
- **Location**: `web/templates/index.html`, `web/static/js/posting.js`

### 7. **Scheduled Posts** ✅
- Scheduled reels preserve "reels" type (not converted to video)
- **Location**: `web/scheduled_publisher.py`

## How to Use

### Option A: Your own server (no external hosting)

You can post video/reels **without any external service** by using the app’s upload:

1. Select **"Video"** or **"Reels"** media type.
2. Use **"Upload file"** (or paste a URL that points to your app’s domain, e.g. `https://yourdomain.com/uploads/xxx.mp4`).
3. In **production**, set **`BASE_URL`** (or **`APP_URL`**) to your public HTTPS domain (e.g. `https://veilforce.com`) so upload URLs are public and Instagram can fetch the file.
4. Post. The video is served from your server; no Cloudinary/S3/Firebase required.

### For Video Posts (with URL):
1. Select **"Video"** media type
2. Enable **"Post by URL"**
3. Use your app’s upload URL, or upload to Cloudinary/S3/Firebase and paste the direct HTTPS URL
4. Paste URL in "Media URLs" field
5. Post!

### For Reels (with URL):
1. Select **"Reels"** media type
2. Enable **"Post by URL"**
3. Use your app’s upload URL, or upload to Cloudinary/S3/Firebase
4. **Important**: Video must be:
   - Format: MP4 or MOV
   - Aspect ratio: 9:16 (vertical)
   - Duration: 3 seconds to 15 minutes
   - Max size: 1GB
5. Paste URL in "Media URLs" field
6. Post!

## Optional: External Hosting Services

### ✅ **Cloudinary** (Best for Videos/Reels)
- Free tier available
- Fast CDN
- Automatic video optimization
- Direct HTTPS URLs
- **URL format**: `https://res.cloudinary.com/.../video.mp4`

### ✅ **AWS S3**
- Reliable, scalable
- Requires public bucket access
- **URL format**: `https://bucket-name.s3.region.amazonaws.com/video.mp4`

### ✅ **Firebase Storage**
- Google Cloud infrastructure
- Good for production
- **URL format**: `https://firebasestorage.googleapis.com/.../video.mp4`

### ✅ **Imgur**
- Good for smaller videos (< 200MB)
- Free, easy to use
- **URL format**: `https://i.imgur.com/abc.mp4`

## ❌ **DO NOT USE** (for videos/reels):
- Cloudflare tunnels (`trycloudflare.com`)
- Ngrok (`ngrok.io`, `ngrok-free.app`)
- Localhost URLs
- HTTP (non-HTTPS) URLs

## Technical Details

### Instagram API Requirements:
- **Reels**: `POST /me/media` with `media_type: "REELS"` and `video_url`
- **Video**: `POST /me/media` with `media_type: "VIDEO"` and `video_url`
- Container must be in `FINISHED` status before publishing
- Reels have stricter requirements (aspect ratio, duration, format)

### Code Flow:
1. User selects "Reels" or "Video"
2. Enters URL (validated for reliable hosting)
3. `PostMedia` created with `media_type: "reels"` or `"video"`
4. `create_media_container()` called with `media_type: "REELS"` or `"VIDEO"`
5. Instagram creates container, processes video
6. System waits for container to be `FINISHED`
7. `publish_media()` called to publish the post

## Testing

To test video/reels posting:
1. Upload a test video to Cloudinary
2. Get the direct HTTPS URL
3. In InstaForge:
   - Select "Video" or "Reels"
   - Enable "Post by URL"
   - Paste the Cloudinary URL
   - Add caption
   - Post!

## Common Errors & Solutions

### Error: "Instagram cannot access the media URL"
**Solution**: Use Cloudinary, S3, or Firebase Storage. Avoid Cloudflare/ngrok.

### Error: "Instagram timed out fetching/processing"
**Solution**: 
- Video file too large → Compress or use shorter video
- Hosting too slow → Use Cloudinary (fast CDN)
- URL not direct → Ensure no redirects/authentication

### Error: "Container not ready"
**Solution**: System automatically waits. If persists, video may be invalid format or too large.

## Status

✅ **FIXED**: Video and Reels posting works with your own server (set `BASE_URL` in production) or optional external hosting
✅ **INTEGRATED**: All components properly integrated
✅ **VALIDATED**: Same-origin URLs allowed; tunnel/ngrok blocked with clear guidance
✅ **DOCUMENTED**: Clear error messages guide users
