# InstaForge - Instagram Automation Platform

Production-grade Instagram automation system with web dashboard, comment automation, comment-to-DM funnels, and advanced safety features.

![Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.8+-blue)
![License](https://img.shields.io/badge/License-Proprietary-red)

## 🚀 Key Features

### 📸 Smart Posting
- **Multi-Format Support**: Images, Videos, and **Carousels** (2-10 items).
- **Auto-Validation**: Frontend and backend checks for media requirements.
- **Retry Logic**: Automatic retries with exponential backoff for reliability.
- **Scheduling**: Plan posts for future publication (backend ready).

### 💬 Comment-to-DM Automation (New!)
- **Auto-DM Funnel**: Automatically send a DM when someone comments on your post.
- **Smart Triggers**: Trigger on **any comment** or specific keywords (e.g., "PDF", "LINK").
- **File Delivery**: Automatically send PDFs, links, or checkout pages via DM.
- **Safety First**:
  - One DM per user per post per day (prevents spam).
  - Configurable daily limits and cooldowns.
  - "Last Processed" tracking to avoid duplicates.

### 🛡️ Advanced Safety Layer
- **Rate Limiting**: Intelligent API quota management (prevents 429 errors).
- **Quota Protection**: Feature-gating ensures Posting has priority over Monitoring.
- **Health Monitoring**: Real-time system status checks.
- **Proxy Support**: Individual proxy routing per account.

### 💻 Modern Web Dashboard
- **Clean UI**: Beautiful, responsive interface for managing your accounts.
- **Live Logs**: Real-time system logs viewer.
- **Config Management**: Update settings directly from the UI.
- **Media Upload**: Direct file upload or URL support.

---

## 🛠️ Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Account
Edit `config/accounts.yaml` with your Instagram credentials:
```yaml
accounts:
  - account_id: "your_id"
    access_token: "IGAAT..."  # Your Instagram Graph API Token
    # Enable features as needed
    comment_to_dm:
      enabled: true
      trigger_keyword: "AUTO"
```
> See [`docs/TOKEN_GENERATION_GUIDE.md`](docs/TOKEN_GENERATION_GUIDE.md) for getting your token.

### 3. Start the Server
```bash
python web_server.py
```

### 4. Access Dashboard
- **URL**: [http://localhost:8000](http://localhost:8000)
- **Login**: `admin` / `admin` (Default)

---

## 📂 Project Structure

```
InstaForge/
├── config/              # Configuration (YAML)
│   ├── accounts.yaml    # Account credentials & feature flags
│   └── settings.yaml    # Global app settings
├── src/                 # Core Source Code
│   ├── api/             # Instagram Graph API Client
│   ├── services/        # Business Logic (Posting, Comments, Accounts)
│   ├── features/        # Feature Modules (Comment-to-DM, Auto-Reply)
│   └── safety/          # Rate Limiting & Safety Engines
├── web/                 # FastAPI Web Dashboard
│   ├── templates/       # HTML Frontend
│   └── static/          # CSS/JS Assets
├── scripts/             # Utility Scripts
│   ├── stop_server.ps1  # Force stop server
│   └── ...              # Token & Testing scripts
└── docs/                # Comprehensive Documentation
```

---

## 📚 Documentation

- **[Features Overview](docs/FEATURES.md)** - Detailed capabilities list.
- **[Setup Guide](docs/SETUP.md)** - Full installation instructions.
- **[Token Generation](docs/TOKEN_GENERATION_GUIDE.md)** - How to get your `IGAAT` token.
- **[Comment-to-DM Setup](docs/COMMENT_TO_DM_SETUP.md)** - Configuring the auto-DM funnel.
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Solutions for common errors.
- **[System Architecture](docs/ARCHITECTURE.md)** - Technical design overview.

---

## 🔧 Configuration Guide

### Posting Mode (Recommended for Start)
To prioritize posting and avoid rate limits, disable background monitoring in `config/accounts.yaml`:
```yaml
warming:
  enabled: false
comment_to_dm:
  enabled: false
```

### Auto-DM Mode
To enable the Comment-to-DM funnel:
```yaml
comment_to_dm:
  enabled: true
  trigger_keyword: "AUTO"  # Or specific word like "SEND"
  link_to_send: "https://your-link.com/file.pdf"
```

---

## 🆘 Support

- Check logs: `logs/instaforge.log` or via Dashboard > Logs.
- Run diagnostics: `python scripts/check_token_detailed.py`.
- Force stop server: `.\scripts\stop_server.ps1`.
