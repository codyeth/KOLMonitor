# KOL Monitor Bot — UX Architecture & Build Prompt

## Tổng quan
Telegram bot theo dõi KOL đang đăng về dự án Web3 trên **X/Twitter** và **Telegram**.
Hỗ trợ cả button inline và gõ lệnh trực tiếp.

---

## Sơ đồ UX Flow

```
/start
└── Menu tổng
    ├── 📋 Monitor
    │   ├── 🐦 Monitor X
    │   │   └── User gửi danh sách username/link X
    │   │       └── ⏳ Đang kiểm tra...
    │   │           └── ✅ Kết quả + file CSV
    │   │
    │   └── 💬 Monitor TG
    │       └── User gửi danh sách link channel/group Telegram
    │           └── ⏳ Đang quét...
    │               └── ✅ Kết quả + file CSV
    │
    ├── 🔍 Scan
    │   └── ⏳ Đang quét X (24h, view > 1k)...
    │       └── ✅ Message tóm tắt + file Excel
    │
    └── ❓ Help
        └── Hướng dẫn tổng quan tất cả tính năng
```

---

## Chi tiết từng màn hình

### Màn hình 1 — `/start` (Menu tổng)

```
👋 Chào mừng đến với KOL Monitor Bot!

Bot giúp theo dõi KOL đang đăng về dự án
trên X/Twitter và Telegram.

━━━━━━━━━━━━━━━━━━━━

[ 📋 Monitor ]  [ 🔍 Scan ]  [ ❓ Help ]
```

**callback_data:**
- `menu_monitor`
- `cmd_scan`
- `menu_help`

---

### Màn hình 2A — Nhấn `📋 Monitor`

```
📋 Chọn nền tảng muốn theo dõi:

[ 🐦 Monitor X ]  [ 💬 Monitor TG ]

[ 🔙 Quay lại ]
```

**callback_data:**
- `cmd_monitor_x`
- `cmd_monitor_tg`
- `menu_main`

---

### Màn hình 2B — Nhấn `🐦 Monitor X`

```
🐦 Monitor X/Twitter

Gửi danh sách KOL cần kiểm tra
(mỗi dòng 1 tài khoản):

  https://x.com/user1
  @user2
  user3

⚙️ Lọc: 72h gần nhất · Từ khóa dự án
📤 Kết quả: file CSV
```

→ Bot set `context.user_data["mode"] = "monitor_x"`
→ User gửi danh sách → bot nhận qua `handle_message()` → xử lý → trả CSV

---

### Màn hình 2C — Nhấn `💬 Monitor TG`

```
💬 Monitor Telegram

Gửi danh sách channel/group cần quét
(mỗi dòng 1 link):

  https://t.me/channel1
  https://t.me/group2
  @channelname

⚙️ Lọc: 24h gần nhất · Từ khóa dự án
📤 Kết quả: file CSV
```

→ Bot set `context.user_data["mode"] = "monitor_tg"`
→ User gửi danh sách → bot nhận qua `handle_message()` → xử lý → trả CSV

---

### Màn hình 3 — Nhấn `🔍 Scan`

```
⏳ Đang quét X/Twitter...
Keywords: NEXI, Nexira, DAEP
Vui lòng chờ ~30 giây
```

→ Xong:

```
🔍 Kết quả Scan KOL
━━━━━━━━━━━━━━━━━━━━
✅ Tìm thấy 5 bài viết
📅 24h gần nhất · 👁 Min 1,000 views

1. @CryptoWhale
   👁 15,420 views · ❤️ 832 · 🔁 214
   📝 "Vừa xem $NEXI tokenomics..."
   🔗 https://x.com/...

2. @BlockchainGuru
   👁 8,300 views · ❤️ 401 · 🔁 98
   📝 "DAEP cross-game layer..."
   🔗 https://x.com/...

📎 File Excel đính kèm gồm tất cả X bài
```

---

### Màn hình 4 — Nhấn `❓ Help`

```
❓ Hướng dẫn sử dụng KOL Monitor Bot

━━━━━━━━━━━━━━━━━━━━
📋 MONITOR X
━━━━━━━━━━━━━━━━━━━━
Theo dõi danh sách KOL trên X/Twitter.
Gửi username hoặc link → bot kiểm tra
bài đăng 72h gần nhất có từ khóa dự án.

Lệnh: /monitor
Gửi trực tiếp: https://x.com/username

━━━━━━━━━━━━━━━━━━━━
💬 MONITOR TG
━━━━━━━━━━━━━━━━━━━━
Quét channel/group Telegram tìm bài
đăng có từ khóa dự án trong 24h qua.

Lệnh: /monitortg
Gửi trực tiếp: https://t.me/channel

━━━━━━━━━━━━━━━━━━━━
🔍 SCAN X
━━━━━━━━━━━━━━━━━━━━
Tìm KOL mới đang đăng về dự án.
Không cần danh sách — bot tự tìm.

Lệnh: /scan
Tùy chỉnh: /scan NEXI Nexira

⚙️ Điều kiện: 24h · view > 1,000
⏱ Tự động: 9:00 sáng mỗi ngày

━━━━━━━━━━━━━━━━━━━━
📤 Output: CSV (Monitor) · Excel (Scan)
```

---

## Mapping lệnh

| Button | Lệnh tương đương | Ghi chú |
|--------|-----------------|---------|
| 📋 → 🐦 Monitor X | `/monitor` + danh sách | Gửi username/link X |
| 📋 → 💬 Monitor TG | `/monitortg` + danh sách | Gửi link channel/group |
| 🔍 Scan | `/scan` hoặc `/scan NEXI` | Tự động mỗi 9:00 sáng |
| ❓ Help | `/help` | Hướng dẫn tổng quan |

---

## Prompt build cho Cursor / VS Code

Paste đoạn sau vào AI chat kèm file `telegram_bot.py` hiện tại:

---

```
@telegram_bot.py

Hãy cập nhật telegram_bot.py theo UX mới sau. KHÔNG xóa các tính năng cũ,
chỉ thêm/sửa các phần được chỉ định.

## 1. Import thêm

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

## 2. Sửa cmd_start — hiển thị menu tổng với 3 button

async def cmd_start(update, context):
    # Kiểm tra quyền như cũ
    # Hiển thị message + 3 button inline:
    # [ 📋 Monitor ] [ 🔍 Scan ] [ ❓ Help ]
    # callback_data: "menu_monitor", "cmd_scan", "menu_help"

## 3. Thêm hàm cmd_button — xử lý toàn bộ callback từ button

async def cmd_button(update, context):
    query = update.callback_query
    await query.answer()

    # "menu_main" → edit message về menu tổng (3 button)

    # "menu_monitor" → edit message hiển thị 2 button:
    #   [ 🐦 Monitor X ] [ 💬 Monitor TG ]
    #   [ 🔙 Quay lại ]
    #   callback_data: "cmd_monitor_x", "cmd_monitor_tg", "menu_main"

    # "cmd_monitor_x" → edit message hướng dẫn gửi danh sách X
    #   set context.user_data["mode"] = "monitor_x"

    # "cmd_monitor_tg" → edit message hướng dẫn gửi danh sách TG
    #   set context.user_data["mode"] = "monitor_tg"

    # "cmd_scan" → gọi thẳng logic scan như /scan hiện tại
    #   (dùng lại hàm _scan_kol_tweets và _send_scan_results)

    # "menu_help" → edit message hiển thị nội dung help đầy đủ

## 4. Thêm lệnh /monitortg

async def cmd_monitor_tg(update, context):
    # Hiển thị hướng dẫn gửi danh sách channel/group Telegram
    # set context.user_data["mode"] = "monitor_tg"
    # Nội dung:
    # "💬 Monitor Telegram
    #  Gửi danh sách channel/group cần quét..."

## 5. Sửa handle_message — kiểm tra mode trước khi xử lý

async def handle_message(update, context):
    mode = context.user_data.get("mode", "monitor_x")

    if mode == "monitor_tg":
        # parse link telegram từ message
        # gọi hàm scan_telegram_channels() (xem spec bên dưới)
        # reset context.user_data["mode"] về None sau khi xử lý
    else:
        # giữ nguyên logic monitor X hiện tại

## 6. Thêm hàm scan_telegram_channels (Monitor TG)

async def scan_telegram_channels(channels: list[str], keywords: list[str]) -> list[dict]:
    """
    Quét danh sách channel/group Telegram tìm bài có từ khóa trong 24h gần nhất.

    Cách implement:
    - Dùng thư viện telethon (pip install telethon)
    - Kết nối bằng Telegram API (TELEGRAM_API_ID, TELEGRAM_API_HASH từ env)
    - Với mỗi channel: lấy messages trong 24h, filter theo keywords
    - Trả về list dict cùng format với tweet dict để tái dùng exporter

    Format dict trả về:
    {
        "id": str,
        "username": str,           # channel username
        "name": str,               # channel title
        "followers": int,          # subscriber count
        "text": str,
        "created_at": str,
        "views": int,              # message views
        "url": str,                # link to message
        "platform": "telegram"
    }
    """

## 7. Sửa cmd_help — nội dung hướng dẫn đầy đủ

Nội dung help phải bao gồm đủ 3 tính năng:
- Monitor X: giải thích + cách dùng + ví dụ
- Monitor TG: giải thích + cách dùng + ví dụ
- Scan X: giải thích + cách dùng + ví dụ + lịch tự động

## 8. Đăng ký handler trong main()

app.add_handler(CommandHandler("monitortg", cmd_monitor_tg))
app.add_handler(CallbackQueryHandler(cmd_button))

## Lưu ý quan trọng
- KHÔNG xóa các handler cũ: /monitor, /scan, /myid, /adduser, /removeuser, /listusers
- Giữ nguyên is_allowed() check ở tất cả handlers
- Giữ nguyên auto_scan_job scheduler
- Monitor TG cần thêm vào requirements.txt: telethon>=1.34.0
- Thêm vào Railway Variables: TELEGRAM_API_ID, TELEGRAM_API_HASH
  (lấy từ https://my.telegram.org/apps)
```

---

## Railway Variables cần thêm cho Monitor TG

```
TELEGRAM_API_ID   = lấy từ https://my.telegram.org/apps
TELEGRAM_API_HASH = lấy từ https://my.telegram.org/apps
```

## requirements.txt cần thêm

```
telethon>=1.34.0
```

---

## Thứ tự build gợi ý

1. Sửa `cmd_start` + `cmd_button` + `cmd_help` trước → test button flow
2. Thêm `cmd_monitor_tg` + `handle_message` mode check
3. Build `scan_telegram_channels()` với telethon
4. Test end-to-end → push GitHub → Railway redeploy
