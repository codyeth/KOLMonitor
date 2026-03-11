"""
config.py — Edit this file to configure your KOL Monitor
"""

CONFIG = {
    # ─── Project Keywords ───────────────────────────────────────────────────
    # Tweets must contain at least one of these to be included
    "keywords": [
        "NEXI",
        "Nexira",
        "DAEP",
        "$NEXI",
    ],

    # ─── View Filter ────────────────────────────────────────────────────────
    # Minimum view count for a tweet to be included
    "min_views": 0,

    # ─── Time Window ────────────────────────────────────────────────────────
    # Default hours to look back (used in on-demand mode)
    "since_hours": 72,
}

# ─── Telegram Bot ───────────────────────────────────────────────────────────
# Token và Admin ID được load từ secrets.py (không commit lên git)
try:
    from secrets import TELEGRAM_TOKEN, TELEGRAM_ADMIN_ID
except ImportError:
    TELEGRAM_TOKEN = ""
    TELEGRAM_ADMIN_ID = 0

# Danh sách user ID được phép dùng bot (thêm bằng /adduser hoặc sửa trực tiếp)
TELEGRAM_ALLOWED_IDS: list[int] = []
