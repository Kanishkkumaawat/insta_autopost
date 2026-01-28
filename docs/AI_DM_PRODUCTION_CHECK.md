# AI DM Auto Reply – Production Check

Use this checklist to confirm AI DM auto-reply is working on production.

---

## 1. Pre-flight checks

### Config

- [ ] **OPENAI_API_KEY** is set in production `.env`
- [ ] In **data/accounts.yaml**, the account has:
  ```yaml
  ai_dm:
    enabled: true
  ```
- [ ] Account has **instagram_business_id** set (or you only have one account)

### Webhook

- [ ] Meta App Dashboard → Webhooks → **messages** field is subscribed (Instagram Messaging and/or Graph API)
- [ ] Callback URL is your production URL, e.g. `https://veilforce.com/webhooks/instagram`
- [ ] Webhook verification (GET) works (Meta can reach the URL)
- **Note:** Instagram can send DMs in two formats: `entry[].messaging[]` (Messenger Platform) or `entry[].changes[]` with `field: "messages"` (Graph API). The app supports both.

---

## 2. Test via API (no Instagram needed)

From your server or any machine that can reach production:

```bash
# Replace with your production URL
BASE="https://veilforce.com"

# 1. Check AI DM status (OpenAI + config)
curl -s "$BASE/api/test/ai-dm-status" | python -m json.tool

# 2. Test AI reply generation (no DM sent)
curl -s -X POST "$BASE/api/test/ai-reply" \
  -d "message=Hello! What are your prices?" \
  -d "account_id=YOUR_ACCOUNT_ID" \
  | python -m json.tool
```

**What to look for:**

- **ai-dm-status**: `openai_configured: true`, and your account has `ai_dm_enabled: true`
- **test/ai-reply**: `"status": "success"` and a non-empty `"reply"` (the AI reply text)

If these pass, OpenAI and config are fine. Remaining checks are webhook + Instagram.

---

## 3. Test with a real DM

1. From another Instagram account (or a test account), send a **text** DM to the account that has `ai_dm.enabled: true`.
2. Wait **about 5–15 seconds** (3–6 s delay + OpenAI + send).
3. You should get one automated reply.

**If you get a reply:**  
Auto DM reply is working end-to-end.

**If you don’t:**  
Go to step 4 (logs) and 5 (troubleshooting).

---

## 4. Check production logs

When someone sends a DM, you should see lines like these (exact wording may vary):

```text
Instagram webhook payload received
Instagram webhook messages event
AI_DM_WEBHOOK  action=processing_start
AI_DM_WEBHOOK  action=config_check  ai_dm_enabled=True
AI_DM_WEBHOOK  action=extracted_data  has_user_id=True  has_message_text=True
AI_DM_REPLY  action=generating
AI_DM_REPLY  action=generated
AI_DM_WEBHOOK  action=reply_sent
```

**If you see:**

- `action=reply_sent` → Reply was sent to Instagram successfully.
- `action=skipped` and `reason=...` → See “Common issues” below.
- No “Instagram webhook messages event” at all → Webhook not receiving message events (subscription or URL).

---

## 5. Common issues

| Symptom | What to check |
|--------|----------------|
| No webhook logs for messages | Subscribed to **messages** in Meta App; callback URL is correct and reachable. |
| `account_not_found` / no account_id | Set **instagram_business_id** in `data/accounts.yaml` for that account, or use a single account (fallback). |
| `ai_dm_disabled` | In `data/accounts.yaml`: `ai_dm: enabled: true` for that account. |
| `rate_limited` | User already got 10 replies today; wait or check `data/ai_dm_tracking.json`. |
| `reply_failed` or send error | Token permissions (e.g. `instagram_manage_messages`), 24h messaging window (user must have messaged you first). |
| OpenAI errors in logs | Check OPENAI_API_KEY and billing. |

---

## 6. Quick “is it on?” summary

1. **API:**  
   `GET .../api/test/ai-dm-status` → `openai_configured: true`, `ai_dm_enabled: true`.
2. **AI:**  
   `POST .../api/test/ai-reply` with a message → `status: success` and a reply.
3. **Live:**  
   Send a real DM → get one reply within ~5–15 s.
4. **Logs:**  
   See `AI_DM_WEBHOOK` and `action=reply_sent` when the DM is sent.

If 1–3 pass and 4 shows `reply_sent`, auto DM reply is working in production.
