"""
monitors/telegram_monitor.py — Theo dõi Telegram channel/group, xuất CSV
cùng schema với X monitor.

Chạy: python run_telegram_monitor.py
Auth lần đầu: python scripts/telegram_auth.py
"""

import asyncio
import csv
import logging
import os
from datetime import datetime, timezone
from pathlib import Path

import yaml
from telethon import TelegramClient, events
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.types import Channel, Chat

# ── Logging ────────────────────────────────────────────────────────────────────

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(LOG_DIR / "telegram_monitor.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger("telegram_monitor")

# ── CSV schema (identical to X monitor) ───────────────────────────────────────

CSV_FIELDNAMES = [
    "stt", "ngay_dang", "username", "ten_kol", "followers",
    "luot_xem", "likes", "retweets", "replies",
    "noi_dung_150ky", "link_bai_viet", "link_x", "loai", "tu_khoa_khop",
]


def _fmt_date(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%d/%m/%Y %H:%M")


class TelegramMonitor:
    def __init__(self):
        self.api_id = int(os.getenv("TELEGRAM_API_ID", "0"))
        self.api_hash = os.getenv("TELEGRAM_API_HASH", "")
        self.session_name = os.getenv("TELEGRAM_SESSION_NAME", "tg_monitor_session")
        self.output_dir = Path(os.getenv("TELEGRAM_OUTPUT_DIR", "output/telegram"))

        if not self.api_id or not self.api_hash:
            raise RuntimeError(
                "TELEGRAM_API_ID và TELEGRAM_API_HASH chưa được set.\n"
                "Lấy tại: https://my.telegram.org/apps"
            )

        self.sources = self._load_sources()
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self._row_counter = 0
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_sources(self) -> list[dict]:
        config_path = Path(__file__).parent.parent / "config" / "telegram_sources.yaml"
        if not config_path.exists():
            logger.warning(f"Không tìm thấy {config_path} — không có source nào.")
            return []
        with open(config_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("sources", [])

    def _get_csv_path(self) -> Path:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.output_dir / f"telegram_{today}.csv"

    def _get_csv_writer(self, path: Path):
        file_exists = path.exists()
        f = open(path, "a", newline="", encoding="utf-8-sig")
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
        if not file_exists:
            writer.writeheader()
        return f, writer

    def _match_keywords(self, text: str, keywords) -> list[str]:
        if not keywords:
            return ["ALL"]
        text_lower = text.lower()
        return [kw for kw in keywords if kw.lower() in text_lower]

    def _normalize_row(self, event, source: dict, matched: list[str], stt: int) -> dict:
        msg = event.message
        sender = getattr(event, "chat", None)

        username = source.get("username", "")
        ten_kol = getattr(sender, "title", username) if sender else username
        followers = getattr(sender, "participants_count", 0) or 0
        views = getattr(msg, "views", 0) or 0
        forwards = getattr(msg, "forwards", 0) or 0
        replies_count = 0
        if hasattr(msg, "replies") and msg.replies:
            replies_count = msg.replies.replies or 0

        # reactions tổng
        likes = 0
        if hasattr(msg, "reactions") and msg.reactions:
            try:
                likes = sum(r.count for r in msg.reactions.results)
            except Exception:
                likes = 0

        text = (msg.text or msg.message or "")[:150]
        link = f"https://t.me/{username}/{msg.id}"
        profile = f"https://t.me/{username}"

        return {
            "stt": stt,
            "ngay_dang": _fmt_date(msg.date),
            "username": username,
            "ten_kol": ten_kol,
            "followers": followers,
            "luot_xem": views,
            "likes": likes,
            "retweets": forwards,
            "replies": replies_count,
            "noi_dung_150ky": text,
            "link_bai_viet": link,
            "link_x": profile,
            "loai": "Telegram",
            "tu_khoa_khop": ", ".join(matched),
        }

    def _write_row(self, row: dict):
        path = self._get_csv_path()
        f, writer = self._get_csv_writer(path)
        try:
            writer.writerow(row)
            f.flush()
        finally:
            f.close()

    async def _try_join(self, username: str):
        try:
            entity = await self.client.get_entity(username)
            if isinstance(entity, (Channel, Chat)):
                await self.client(JoinChannelRequest(entity))
                logger.info(f"Đã join: @{username}")
        except Exception as e:
            logger.warning(f"Không thể join @{username}: {e}")

    async def start(self):
        await self.client.start()
        me = await self.client.get_me()
        logger.info(f"Đã đăng nhập: {me.username} ({me.first_name})")
        logger.info(f"Đang theo dõi {len(self.sources)} source(s)")

        source_map: dict[str, dict] = {}

        for source in self.sources:
            username = source.get("username", "")
            if not username:
                continue
            await self._try_join(username)
            try:
                entity = await self.client.get_entity(username)
                source_map[entity.id] = source
            except Exception as e:
                logger.error(f"Không lấy được entity @{username}: {e}")

        @self.client.on(events.NewMessage(chats=list(source_map.keys())))
        async def handler(event):
            chat_id = event.chat_id
            source = source_map.get(chat_id)
            if not source:
                return

            text = event.message.text or event.message.message or ""
            keywords = source.get("keywords")
            matched = self._match_keywords(text, keywords)

            if not matched:
                return

            self._row_counter += 1
            row = self._normalize_row(event, source, matched, self._row_counter)
            self._write_row(row)
            logger.info(
                f"[{source['username']}] Lưu tin #{row['stt']} — "
                f"khớp: {row['tu_khoa_khop']}"
            )

        logger.info("Bot Telegram đang lắng nghe tin nhắn mới... (Ctrl+C để dừng)")
        await self.client.run_until_disconnected()

    async def stop(self):
        await self.client.disconnect()
        logger.info("Đã dừng Telegram Monitor.")


def main():
    monitor = TelegramMonitor()
    try:
        asyncio.run(monitor.start())
    except KeyboardInterrupt:
        logger.info("Nhận KeyboardInterrupt — dừng.")


if __name__ == "__main__":
    main()
