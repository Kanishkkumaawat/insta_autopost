"""
Cron-style intervals and rate limits for background jobs.
Reduces API pressure on Instagram/Meta and avoids blocks from constant polling.
All intervals in seconds. Override via environment variables.
"""

import os


def _int_env(name: str, default: int) -> int:
    try:
        v = os.getenv(name, "").strip()
        return int(v) if v else default
    except ValueError:
        return default


# Comment monitor: run comment check (all accounts) every N seconds.
# Stagger between accounts so we don't burst Instagram API.
COMMENT_CHECK_INTERVAL_SECONDS = _int_env("COMMENT_CHECK_INTERVAL_SECONDS", 300)  # 5 min
COMMENT_STAGGER_BETWEEN_ACCOUNTS_SECONDS = _int_env("COMMENT_STAGGER_SECONDS", 45)  # 45s between accounts

# Scheduled publisher: check for due posts every N seconds.
SCHEDULED_PUBLISHER_INTERVAL_SECONDS = _int_env("SCHEDULED_PUBLISHER_INTERVAL_SECONDS", 90)  # 90s (cron-style)

# Token refresh: run once per day.
TOKEN_REFRESH_INTERVAL_SECONDS = _int_env("TOKEN_REFRESH_INTERVAL_SECONDS", 86400)  # 24h

# Account health: check every N seconds.
ACCOUNT_HEALTH_INTERVAL_SECONDS = _int_env("ACCOUNT_HEALTH_INTERVAL_SECONDS", 600)  # 10 min

# Frontend auto-refresh (inbox, schedule, accounts): recommend 60s+ to avoid rate limits.
# These are hints for the UI; actual timers are in JS.
INBOX_REFRESH_INTERVAL_SECONDS = _int_env("INBOX_REFRESH_INTERVAL_SECONDS", 60)
SCHEDULE_PAGE_REFRESH_INTERVAL_SECONDS = 60
ACCOUNTS_PAGE_REFRESH_INTERVAL_SECONDS = 60
