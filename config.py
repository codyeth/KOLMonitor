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
import os

# Đọc từ biến môi trường (Railway) hoặc fallback sang secrets.py (local)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))

if not TELEGRAM_TOKEN:
    try:
        import secrets as _secrets
        TELEGRAM_TOKEN = getattr(_secrets, "TELEGRAM_TOKEN", "")
        if TELEGRAM_ADMIN_ID == 0:
            TELEGRAM_ADMIN_ID = getattr(_secrets, "TELEGRAM_ADMIN_ID", 0)
    except ImportError:
        TELEGRAM_TOKEN = ""

# Danh sách user ID được phép dùng bot (thêm bằng /adduser hoặc sửa trực tiếp)
TELEGRAM_ALLOWED_IDS: list[int] = []
