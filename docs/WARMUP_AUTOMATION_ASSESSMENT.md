# Warm-Up Automation – Full Assessment

## What Works (Fully Automated)

| Task | Days | Status |
|------|------|--------|
| Like posts | 1, 2, 3, 4 | ✅ Automated via browser |
| Comment on posts | 1, 2, 3, 4 | ✅ Automated via browser |
| Save posts | 1, 2, 3, 4 | ✅ Automated via browser |

These run at scheduled hours (9, 14, 18) or via the **Run automation now** button.

---

## What Stays Manual

| Task | Reason |
|------|--------|
| Bio update, profile pic | No API; user must do it |
| Follow accounts | Browser support exists but not wired for warm-up automation |
| Watch reels | No reliable automation; must be done manually |
| Reply to stories, story DMs | Complex; no automation implemented |
| Post story / reel | Requires user decisions and content |

---

## Requirements for Automation to Work

1. **Playwright** – `pip install playwright && playwright install chromium`
2. **Account password** – Stored in account config; needed for browser login
3. **Automation enabled** – Toggle in warm-up UI + Save
4. **Target hashtags** – Optional; Explore page is tried first, then hashtags. Use e.g. `love`, `photo`, `travel` if you set any.
5. **Discovery is browser-only** – No Meta app callback URL or permission is used for finding posts. If you run the app on a server (e.g. cloud), use a **residential proxy** (Config → Accounts → Edit → Proxy) or run from a home network; otherwise Instagram may block the browser and you'll see "no posts".

---

## Known Issues (Fixed)

1. **Scheduler timing** – `now.minute > 10` could skip runs; fixed by running whenever the hour matches.
2. **Run now blocking** – Long browser actions were blocking the API; fixed by using a thread pool.

---

## How to Verify

1. Start warm-up for an account.
2. Enable automation and set hashtags.
3. Add account password in config (Accounts → edit).
4. Click **Run automation now** and check logs; tasks should complete.
5. For scheduled runs, ensure the server is running during 9, 14, or 18 o’clock.
