# InstaForge Terminal Dashboard

Python-only terminal-based dashboard for controlling the InstaForge Instagram automation system.

## Features

✅ **Main Dashboard** - View system status, account info, warming status  
✅ **Trending Images Fetcher** - Fetch images from Reddit, Unsplash, or Pexels  
✅ **Daily Posting Control** - Create and publish posts with captions and hashtags  
✅ **Warming Control** - Manage warming actions (enable/disable, manual trigger)  
✅ **Activity Log Viewer** - View recent activity logs with color-coded levels  

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure your InstaForge application is configured (config/accounts.yaml, etc.)

## Usage

Run the dashboard:
```bash
python ui/dashboard.py
```

## Navigation

- Use number keys to select menu options
- Follow on-screen prompts for input
- Press Enter to continue between screens
- Type 'q' or 'Q' to quit

## Features Detail

### Main Dashboard
- Shows app status (running/stopped)
- Connected Instagram account username
- Warming status (enabled/disabled)
- Warming schedule time
- Daily action count and types

### Trending Images Fetcher
- Fetch images from:
  - **Reddit**: Popular image subreddits (r/pics, etc.) - No API key needed
  - **Unsplash**: Free stock photos (requires API key)
  - **Pexels**: Free stock photos (requires API key)
- Save images for posting later
- Preview images with metadata

### Daily Posting Control
- Input caption and hashtags via terminal
- Post immediately or schedule for later
- Uses existing PostingService internally
- Supports saved images from fetcher

### Warming Control
- View warming status and statistics
- Manual trigger: Run warming actions now
- View daily action counts and types
- Toggle warming (requires config file edit)

### Activity Log Viewer
- Scrollable log viewer
- Color-coded log levels (INFO, WARNING, ERROR)
- Reads from logs/instaforge.log
- Refresh option to reload logs

## Architecture

- **Python-only**: Uses `rich` library for terminal UI
- **No frontend**: Pure terminal interface
- **Modular**: UI layer calls backend services
- **Headless compatible**: Backend runs without UI

## Requirements

- Python 3.8+
- `rich` library (terminal UI)
- Existing InstaForge backend setup

## Notes

- Images must meet Instagram's aspect ratio requirements (see main README)
- Reddit image fetcher works without API keys
- Unsplash/Pexels require API keys (optional, set via environment variables)
- All changes persist through existing config system
