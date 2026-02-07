# InstaForge - Instagram Automation Platform

Production-grade Instagram automation system with web dashboard, comment automation, comment-to-DM funnels, and advanced safety features.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

## Key Features

### Smart Posting
- **Multi-Format Support**: Images, Videos, and Carousels (2-10 items)
- **Auto-Validation**: Frontend and backend checks for media requirements
- **Retry Logic**: Automatic retries with exponential backoff
- **Scheduling**: Plan posts for future publication

### Comment-to-DM Automation
- **Auto-DM Funnel**: Automatically send a DM when someone comments on your post
- **Smart Triggers**: Trigger on any comment or specific keywords
- **File Delivery**: Send PDFs, links, or checkout pages via DM
- **Safety**: One DM per user per post per day, configurable limits and cooldowns

### Multi-User and Role-Based Access
- **Admin and User roles**: Separate permissions for admin and regular users
- **Account ownership**: Each user sees only their own accounts; admins manage all
- **Admin-only pages**: Users, Settings, Webhook Test (admin only)

### Safety Layer
- Rate limiting and quota protection
- Health monitoring and proxy support

### Web Dashboard
- Tabbed navigation (Content, Automation, Accounts, Tools, Admin)
- Live logs, config management, media upload
- Red and black theme

---

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` to `.env` and set required variables (see Deployment section).

### 3. Start the Server

**Development** (with auto-reload):
```bash
python web_server.py
```

**Production** (uvicorn):
```bash
python main.py
```
Or with multiple workers:
```bash
python app.py
```

### 4. Access Dashboard
- **URL**: [http://localhost:8000](http://localhost:8000)
- **Default login**: `admin` / `admin` (or value of `WEB_PASSWORD` env var)

---

## Project Structure

```
insta_autopost/
├── config/              # Configuration
│   ├── app_credentials.yaml
│   └── (accounts.yaml in data/)
├── data/                # Runtime data (accounts, users, scheduled posts, etc.)
├── deploy/              # Nginx, Apache configs for VPS
├── src/                 # Core Source Code
│   ├── api/             # Instagram Graph API Client
│   ├── auth/            # User auth, Meta OAuth
│   ├── services/        # Business Logic
│   ├── features/        # Comment-to-DM, AI DM, Warmup
│   └── safety/          # Rate Limiting, Safety Engines
├── web/                 # FastAPI Web Dashboard
│   ├── templates/       # HTML Frontend
│   └── static/          # CSS/JS Assets
├── web_server.py        # Dev entry point (Cloudflare tunnel)
├── main.py              # Production entry point
├── app.py               # Production with uvicorn workers
└── requirements.txt
```

---

## Deployment

### Environment Variables
| Variable | Description |
|----------|-------------|
| `BASE_URL` | Public URL (e.g. https://yourdomain.com) |
| `WEB_PASSWORD` | Default admin password on first run |
| `META_APP_ID` | Meta/Facebook App ID for OAuth |
| `META_APP_SECRET` | Meta App Secret |
| `OPENAI_API_KEY` | For AI DM features |
| `WEBHOOK_VERIFY_TOKEN` | Token for Instagram webhook verification |
| `RAZORPAY_KEY_ID` | Razorpay key for payments |
| `RAZORPAY_KEY_SECRET` | Razorpay secret |
| `RAZORPAY_WEBHOOK_SECRET` | For Razorpay webhook verification |
| `ENVIRONMENT` | `development` or `production` |

### Render
Uses `render.yaml` and `Procfile`. Set env vars in Render dashboard.

### VPS (Nginx + Systemd)
1. Copy `deploy/nginx-veilforce.conf` to `/etc/nginx/sites-available/` and enable
2. Copy `deploy/instaforge.service` to `/etc/systemd/system/`, edit WorkingDirectory and paths, then `systemctl enable instaforge && systemctl start instaforge`
3. Use Let's Encrypt for SSL; ensure `data/` and `uploads/` are persistent

---

## Configuration

### Posting Mode (Recommended for Start)
```yaml
warming:
  enabled: false
comment_to_dm:
  enabled: false
```

### Auto-DM Mode
```yaml
comment_to_dm:
  enabled: true
  trigger_keyword: "AUTO"
  link_to_send: "https://your-link.com/file.pdf"
```

---

## Support

- Check logs via Dashboard > Logs
- Health check: `GET /api/health`
