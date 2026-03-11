"""
telegram_bot.py — Telegram bot interface cho KOL Monitor

Commands:
  /start         — Chào mừng + hướng dẫn
  /help          — Hướng dẫn sử dụng
  /myid          — Hiển thị Telegram user ID của bạn
  /adduser <id>  — Thêm user (admin only)
  /removeuser <id> — Xoá user (admin only)
  /listusers     — Danh sách user được phép (admin only)

Gửi danh sách KOL (URL hoặc username, mỗi dòng 1 tài khoản):
  https://x.com/user1
  https://x.com/user2
  @user3
  user4
"""

import json
import logging
import re
from pathlib import Path

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN, TELEGRAM_ADMIN_ID, TELEGRAM_ALLOWED_IDS
from monitor_core import run_monitor

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# File lưu danh sách allowed IDs (để persist qua restart)
ALLOWED_IDS_FILE = Path(__file__).parent / "data" / "allowed_users.json"


# ── Quản lý allowed users ────────────────────────────────────────────────────

def _load_allowed_ids() -> set[int]:
    ids = set(TELEGRAM_ALLOWED_IDS)
    if TELEGRAM_ADMIN_ID:
        ids.add(TELEGRAM_ADMIN_ID)
    if ALLOWED_IDS_FILE.exists():
        try:
            ids.update(json.loads(ALLOWED_IDS_FILE.read_text()))
        except Exception:
            pass
    return ids


def _save_allowed_ids(ids: set[int]):
    ALLOWED_IDS_FILE.parent.mkdir(parents=True, exist_ok=True)
    ALLOWED_IDS_FILE.write_text(json.dumps(sorted(ids)))


allowed_ids: set[int] = _load_allowed_ids()


def is_allowed(user_id: int) -> bool:
    return user_id in allowed_ids


def is_admin(user_id: int) -> bool:
    return user_id == TELEGRAM_ADMIN_ID


# ── Parse usernames từ message ───────────────────────────────────────────────

def parse_usernames(text: str) -> list[str]:
    """
    Nhận text chứa URLs, @mentions hoặc usernames thuần.
    Trả về list username (không có @, không trùng, giữ thứ tự).
    """
    usernames = []
    seen = set()

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue

        # x.com/username hoặc twitter.com/username
        m = re.search(r"(?:x\.com|twitter\.com)/([A-Za-z0-9_]{1,50})", line)
        if m:
            username = m.group(1)
        elif line.startswith("@"):
            username = line.lstrip("@")
        elif re.fullmatch(r"[A-Za-z0-9_]{1,50}", line):
            username = line
        else:
            continue

        lower = username.lower()
        if lower not in seen:
            seen.add(lower)
            usernames.append(username)

    return usernames


# ── Handlers ─────────────────────────────────────────────────────────────────

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_allowed(user_id):
        await update.message.reply_text(
            f"⛔ Bạn chưa được cấp quyền.\n\nID của bạn: `{user_id}`\nGửi ID này cho admin để được thêm vào.",
            parse_mode="Markdown",
        )
        return

    await update.message.reply_text(
        "👋 *KOL Monitor Bot*\n\n"
        "Gửi danh sách tài khoản Twitter/X (mỗi dòng 1 link hoặc username), "
        "bot sẽ kiểm tra và trả về file CSV chứa các bài viết có từ khoá "
        "*NEXI / Nexira / DAEP / $NEXI* trong 72 giờ gần nhất.\n\n"
        "Dùng /help để xem hướng dẫn chi tiết.",
        parse_mode="Markdown",
    )


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_allowed(update.effective_user.id):
        return

    await update.message.reply_text(
        "📖 *Hướng dẫn sử dụng*\n\n"
        "Gửi danh sách KOL theo định dạng bất kỳ:\n"
        "```\n"
        "https://x.com/user1\n"
        "https://x.com/user2\n"
        "@user3\n"
        "user4\n"
        "```\n\n"
        "Bot sẽ:\n"
        "1. Kiểm tra từng tài khoản\n"
        "2. Lọc bài có chứa NEXI/Nexira/DAEP/$NEXI\n"
        "3. Gửi lại file CSV kết quả\n\n"
        "⏱ Khoảng 5-10 phút cho 30 tài khoản (do giới hạn API Twitter)\n\n"
        "*Lệnh khác:*\n"
        "/myid — Xem Telegram ID của bạn",
        parse_mode="Markdown",
    )


async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(f"🪪 Telegram ID của bạn: `{uid}`", parse_mode="Markdown")


async def cmd_adduser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Chỉ admin mới dùng được lệnh này.")
        return
    if not context.args:
        await update.message.reply_text("Cách dùng: /adduser <telegram_id>")
        return
    try:
        new_id = int(context.args[0])
        allowed_ids.add(new_id)
        _save_allowed_ids(allowed_ids)
        await update.message.reply_text(f"✅ Đã thêm user `{new_id}`.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ ID không hợp lệ.")


async def cmd_removeuser(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Chỉ admin mới dùng được lệnh này.")
        return
    if not context.args:
        await update.message.reply_text("Cách dùng: /removeuser <telegram_id>")
        return
    try:
        rem_id = int(context.args[0])
        allowed_ids.discard(rem_id)
        _save_allowed_ids(allowed_ids)
        await update.message.reply_text(f"✅ Đã xoá user `{rem_id}`.", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("❌ ID không hợp lệ.")


async def cmd_listusers(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Chỉ admin mới dùng được lệnh này.")
        return
    if not allowed_ids:
        await update.message.reply_text("Chưa có user nào.")
        return
    lines = [f"• `{uid}`{'  ← admin' if uid == TELEGRAM_ADMIN_ID else ''}" for uid in sorted(allowed_ids)]
    await update.message.reply_text(
        "👥 *Danh sách user được phép:*\n" + "\n".join(lines),
        parse_mode="Markdown",
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if not is_allowed(user_id):
        await update.message.reply_text(
            f"⛔ Bạn chưa được cấp quyền.\nID của bạn: `{user_id}`",
            parse_mode="Markdown",
        )
        return

    text = update.message.text or ""
    usernames = parse_usernames(text)

    if not usernames:
        await update.message.reply_text(
            "❓ Không nhận ra tài khoản nào.\n\n"
            "Gửi danh sách theo dạng:\n"
            "• https://x.com/username\n"
            "• @username\n"
            "• username"
        )
        return

    status_msg = await update.message.reply_text(
        f"⏳ Bắt đầu kiểm tra {len(usernames)} KOL...\n\n"
        + "\n".join(f"• @{u}" for u in usernames),
    )

    progress_lines: list[str] = []

    async def on_progress(msg: str):
        progress_lines.append(msg)
        # Cập nhật message mỗi 3 dòng để không spam API Telegram
        if len(progress_lines) % 3 == 0 or "✗" in msg:
            try:
                await status_msg.edit_text(
                    "⏳ Đang kiểm tra...\n\n" + "\n".join(progress_lines[-15:]),
                )
            except Exception:
                pass

    try:
        _, csv_path, kol_hits, _ = await run_monitor(
            usernames=usernames,
            on_progress=on_progress,
        )
    except Exception as e:
        await status_msg.edit_text(f"❌ Lỗi khi chạy monitor:\n`{e}`", parse_mode="Markdown")
        return

    if not kol_hits:
        await status_msg.edit_text(
            f"✅ Đã kiểm tra {len(usernames)} KOL\n\n"
            "ℹ️ Không có bài viết nào khớp từ khoá trong 72 giờ gần nhất."
        )
        return

    total_views = sum(t.get("views", 0) for t in kol_hits)
    await status_msg.edit_text(
        f"✅ Hoàn tất!\n\n"
        f"📊 {len(kol_hits)} bài viết khớp\n"
        f"👁 {total_views:,} lượt xem tổng\n\n"
        f"Đang gửi file CSV...",
    )

    with open(csv_path, "rb") as f:
        await update.message.reply_document(
            document=f,
            filename=csv_path.name,
            caption=f"📄 {len(kol_hits)} bài | {total_views:,} views | {len(usernames)} KOL",
        )


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("myid", cmd_myid))
    app.add_handler(CommandHandler("adduser", cmd_adduser))
    app.add_handler(CommandHandler("removeuser", cmd_removeuser))
    app.add_handler(CommandHandler("listusers", cmd_listusers))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Bot đang chạy...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
