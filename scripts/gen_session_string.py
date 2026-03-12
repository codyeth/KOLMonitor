"""
Chạy MỘT LẦN để tạo Telegram session string:
    python scripts/gen_session_string.py

Copy giá trị in ra → thêm vào Railway Variables với tên TELEGRAM_SESSION_STRING
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telethon import TelegramClient
from telethon.sessions import StringSession


async def main():
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("❌ Cần set TELEGRAM_API_ID và TELEGRAM_API_HASH trước.")
        print("   Lấy tại: https://my.telegram.org/apps")
        return

    phone = os.getenv("TELEGRAM_PHONE") or input("📱 Nhập số điện thoại (VD: +84912345678): ").strip()
    print(f"\n📲 Đang gửi OTP đến {phone}...\n")

    client = TelegramClient(StringSession(), int(api_id), api_hash)
    await client.start(phone=phone)

    session_string = client.session.save()
    me = await client.get_me()

    print(f"\n✅ Đã xác thực: {me.first_name} (@{me.username})")
    print("\n" + "="*60)
    print("TELEGRAM_SESSION_STRING =")
    print(session_string)
    print("="*60)
    print("\n👆 Copy giá trị trên → thêm vào Railway Variables")
    print("   Tên biến: TELEGRAM_SESSION_STRING")

    await client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
