"""
monitors/tg_fetcher.py — Lấy tin nhắn lịch sử từ Telegram channel/group

Yêu cầu env vars:
  TELEGRAM_API_ID      — từ https://my.telegram.org/apps
  TELEGRAM_API_HASH    — từ https://my.telegram.org/apps
  TELEGRAM_SESSION_STRING — chạy scripts/gen_session_string.py để lấy

Dùng StringSession để tránh lưu file .session (phù hợp Railway).
"""

import os
from datetime import datetime, timezone, timedelta

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import Channel, Chat, User


def _get_client() -> TelegramClient:
    api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
    api_hash = os.getenv("TELEGRAM_API_HASH", "")
    session_string = os.getenv("TELEGRAM_SESSION_STRING", "")

    if not api_id or not api_hash:
        raise RuntimeError(
            "Thiếu TELEGRAM_API_ID hoặc TELEGRAM_API_HASH.\n"
            "Lấy tại: https://my.telegram.org/apps"
        )
    if not session_string:
        raise RuntimeError(
            "Thiếu TELEGRAM_SESSION_STRING.\n"
            "Chạy: python scripts/gen_session_string.py để lấy."
        )

    return TelegramClient(StringSession(session_string), api_id, api_hash)


async def fetch_tg_channels(
    channel_usernames: list[str],
    keywords: list[str],
    hours: int = 24,
) -> list[dict]:
    """
    Quét danh sách channel/group Telegram, lấy tin nhắn trong `hours` giờ gần nhất.
    Lọc theo keywords (nếu không có keywords → lấy tất cả).
    Trả về list[dict] tương thích với CSV schema.
    """
    since = datetime.now(timezone.utc) - timedelta(hours=hours)
    results: list[dict] = []
    errors: list[str] = []

    client = _get_client()
    await client.connect()

    try:
        for username in channel_usernames:
            try:
                entity = await client.get_entity(username)
                name = getattr(entity, "title", username)
                followers = getattr(entity, "participants_count", 0) or 0

                async for msg in client.iter_messages(entity, limit=500):
                    if not msg.date:
                        continue

                    msg_dt = msg.date
                    if msg_dt.tzinfo is None:
                        msg_dt = msg_dt.replace(tzinfo=timezone.utc)

                    if msg_dt < since:
                        break  # iter_messages trả về mới → cũ, có thể break sớm

                    text = msg.text or msg.message or ""
                    if not text.strip():
                        continue

                    # Lọc keywords
                    if keywords:
                        text_lower = text.lower()
                        matched = [kw for kw in keywords if kw.lower() in text_lower]
                        if not matched:
                            continue
                    else:
                        matched = ["ALL"]

                    # Đếm reactions
                    likes = 0
                    if hasattr(msg, "reactions") and msg.reactions:
                        try:
                            likes = sum(r.count for r in msg.reactions.results)
                        except Exception:
                            likes = 0

                    replies_count = 0
                    if hasattr(msg, "replies") and msg.replies:
                        replies_count = msg.replies.replies or 0

                    results.append({
                        "id": str(msg.id),
                        "username": username.lstrip("@"),
                        "name": name,
                        "followers": followers,
                        "text": text[:150],
                        "created_at": msg_dt.strftime("%a %b %d %H:%M:%S %z %Y"),
                        "views": getattr(msg, "views", 0) or 0,
                        "likes": likes,
                        "forwards": getattr(msg, "forwards", 0) or 0,
                        "replies": replies_count,
                        "url": f"https://t.me/{username.lstrip('@')}/{msg.id}",
                        "matched_keywords": ", ".join(matched),
                        "platform": "telegram",
                    })

            except Exception as e:
                errors.append(f"@{username}: {e}")

    finally:
        await client.disconnect()

    return results, errors
