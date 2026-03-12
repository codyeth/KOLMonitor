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
        import importlib.util, pathlib
        _spec = importlib.util.spec_from_file_location(
            "_local_secrets",
            pathlib.Path(__file__).parent / "secrets.py",
        )
        _mod = importlib.util.module_from_spec(_spec)
        _spec.loader.exec_module(_mod)
        TELEGRAM_TOKEN = getattr(_mod, "TELEGRAM_TOKEN", "")
        if TELEGRAM_ADMIN_ID == 0:
            TELEGRAM_ADMIN_ID = getattr(_mod, "TELEGRAM_ADMIN_ID", 0)
    except (FileNotFoundError, AttributeError, Exception):
        TELEGRAM_TOKEN = ""

if not TELEGRAM_TOKEN:
    raise RuntimeError(
        "TELEGRAM_TOKEN chưa được set. "
        "Trên Railway: thêm biến môi trường TELEGRAM_TOKEN. "
        "Chạy local: tạo file secrets.py với TELEGRAM_TOKEN = '...' "
    )

# Danh sách user ID được phép dùng bot (thêm bằng /adduser hoặc sửa trực tiếp)
_allowed = os.getenv("TELEGRAM_ALLOWED_IDS", "")
TELEGRAM_ALLOWED_IDS: list[int] = [
    int(x.strip()) for x in _allowed.split(",") if x.strip()
]
