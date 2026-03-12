"""
Chạy MỘT LẦN để xác thực Telegram và lưu session:
    python scripts/telegram_auth.py

Sau khi chạy, file .session sẽ được tạo và dùng lại tự động.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv không bắt buộc — có thể set env var thủ công

from telethon import TelegramClient


async def auth():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session = os.getenv("TELEGRAM_SESSION_NAME", "tg_monitor_session")

    if not api_id or not api_hash:
        print("❌ Cần set TELEGRAM_API_ID và TELEGRAM_API_HASH trước.")
        print("   Lấy tại: https://my.telegram.org/apps")
        return

    client = TelegramClient(session, int(api_id), api_hash)
    await client.start()
    me = await client.get_me()
    print(f"✅ Đã xác thực: {me.username} ({me.first_name})")
    print(f"✅ Session lưu tại: {session}.session")
    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(auth())
