# AI Comment Reply Feature

## ✅ What's New

When someone comments on a post with `ai_enabled: true`, they now get **BOTH**:

1. **Auto DM** (existing feature) - Direct message sent to their inbox
2. **Auto Comment Reply** (NEW!) - Public comment reply mentioning them with AI-generated text

## 🎯 How It Works

### Flow:
1. User comments on a post with `ai_enabled: true`
2. System detects the comment
3. **DM is sent** with AI-generated message
4. **Comment reply is posted** with format: `@username {AI-generated text}`
5. User gets notified of both the DM and the comment mention

### Example:
- **Comment**: "Bhejde bhai"
- **DM sent**: "Bhejde bhai! Check out this cute little furball 🐱. You can find more here: https://example.com/file.pdf"
- **Comment reply**: "@username Bhejde bhai! Check out this cute little furball 🐱. You can find more here: https://example.com/file.pdf"

## 🔧 Technical Details

### New Method: `_reply_to_comment_with_ai()`
- Located in: `src/features/comments/comment_to_dm_service.py`
- Called after successful DM sends
- Only triggers when:
  - `ai_enabled: true` in post config
  - DM was sent successfully
  - Comment username is available

### Features:
- **Reuses AI message** from DM (if available) to keep consistency
- **Generates new AI reply** if needed (shorter, more casual for comments)
- **Mentions user** with `@username` format
- **Includes link** if configured in post
- **Falls back gracefully** if AI fails (uses friendly default message)

## 📋 Configuration

No new configuration needed! It automatically works when:
- Post has `ai_enabled: true` in `data/post_dm_config.json`
- Comment-to-DM is enabled for the account
- DM is successfully sent

## 🚀 Benefits

1. **Double Engagement**: Users get both DM and public comment reply
2. **Visibility**: Comment replies are visible to other users, increasing engagement
3. **Notifications**: Users get notified twice (DM + comment mention)
4. **Consistency**: Uses same AI-generated text for both DM and comment

## 📝 Logging

All comment replies are logged with:
- `event`: "Comment reply posted with AI text"
- `mentioned_user`: Username mentioned
- `reply_preview`: First 100 chars of reply

## ⚠️ Notes

- Comment replies only happen **after successful DM sends**
- If DM fails (e.g., 24h window), the existing fallback comment reply still works
- Comment replies use the same AI service as DMs
- Mentions are only added if username is available
