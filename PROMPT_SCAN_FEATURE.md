# Prompt mở rộng Telegram Bot — Tính năng Scan KOL theo từ khóa

## Bối cảnh
Bot Telegram hiện tại đã hoạt động với file `telegram_bot.py` và `config.py`.
Cần thêm **1 tính năng mới** vào bot hiện tại, KHÔNG viết lại từ đầu.

---

## Tính năng cần thêm: `/scan` — Quét KOL theo từ khóa

### Mô tả
Tìm kiếm các bài đăng trên X/Twitter trong **24h gần nhất** chứa từ khóa của dự án.
Lọc các bài có **view > 1000** (không cần quan tâm followers).
Trả kết quả về Telegram dưới dạng **message tóm tắt + file Excel đính kèm**.

---

## Cách dùng trong Telegram

### Gọi thủ công
```
/scan                  → dùng keywords mặc định từ config
/scan NEXI             → scan từ khóa NEXI
/scan NEXI Nexira DAEP → scan nhiều từ khóa cùng lúc
```

### Tự động 24h
- Bot tự động chạy scan mỗi **24 giờ một lần**
- Gửi kết quả vào **chat của TELEGRAM_ADMIN_ID**
- Chạy lúc **9:00 sáng giờ UTC+7** mỗi ngày

---

## Luồng xử lý

```
User gõ /scan (hoặc scheduler trigger)
        ↓
Bot reply: "⏳ Đang quét X/Twitter, vui lòng chờ..."
        ↓
Gọi twikit search_tweet() với từng keyword
        ↓
Lọc: views > 1000 VÀ trong 24h gần nhất
        ↓
Loại trùng (cùng tweet_id)
        ↓
Sắp xếp theo views giảm dần
        ↓
Gửi message tóm tắt vào Telegram
        ↓
Tạo file Excel + gửi đính kèm
        ↓
Xóa file Excel tạm sau khi gửi xong
```

---

## Format message Telegram trả về

```
🔍 Kết quả Scan KOL
━━━━━━━━━━━━━━━━━━━━
📅 24h gần nhất
🔑 Keywords: NEXI, Nexira, DAEP
👁 Min views: 1,000
━━━━━━━━━━━━━━━━━━━━
✅ Tìm thấy 5 bài viết

1. @CryptoWhale_X
   👁 15,420 views · ❤️ 832 · 🔁 214
   📝 "Vừa xem $NEXI tokenomics..."
   🔗 https://x.com/CryptoWhale_X/status/xxx

2. @BlockchainGuru
   👁 8,300 views · ❤️ 401 · 🔁 98
   📝 "DAEP cross-game layer is..."
   🔗 https://x.com/BlockchainGuru/status/xxx

... (tối đa 10 bài trong message)

📎 File Excel đính kèm gồm tất cả X bài
```

Nếu không tìm thấy bài nào:
```
🔍 Kết quả Scan KOL
━━━━━━━━━━━━━━━━━━━━
❌ Không tìm thấy bài viết nào khớp tiêu chí trong 24h qua.
Keywords: NEXI, Nexira, DAEP
```

---

## File Excel đính kèm

Tạo bằng `openpyxl`, gửi qua `bot.send_document()`, xóa file sau khi gửi.

### Tên file
```
scan_NEXI_2024-03-11.xlsx
```

### Cấu trúc — 1 sheet tên "Kết quả Scan"

| Cột | Nội dung |
|-----|----------|
| A | STT |
| B | Thời gian đăng (DD/MM/YYYY HH:MM) |
| C | @Username |
| D | Tên KOL |
| E | Followers |
| F | Lượt xem |
| G | Likes |
| H | Retweets |
| I | Replies |
| J | Nội dung tweet (150 ký tự) |
| K | Link bài viết (hyperlink) |
| L | Từ khóa khớp |

### Định dạng Excel
- Header: nền `#1DA1F2` (màu Twitter), chữ trắng, in đậm
- Xen kẽ màu hàng: trắng và `#F0F8FF`
- Cột K: hyperlink thật có thể click
- Freeze hàng tiêu đề
- Auto-fit độ rộng cột
- Số có dấu phẩy: `1,234,567`

---

## Code cần thêm vào telegram_bot.py

### 1. Import thêm ở đầu file
```python
import asyncio
from datetime import datetime, timezone, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter
import tempfile
import os
```

### 2. Hàm scan core
```python
async def scan_kol_tweets(keywords: list[str], min_views: int = 1000) -> list[dict]:
    """
    Tìm tweet trong 24h gần nhất chứa keyword và có view > min_views.
    Trả về list tweet dict sắp xếp theo views giảm dần.
    """
```

### 3. Hàm tạo Excel
```python
def create_scan_excel(tweets: list[dict], keywords: list[str]) -> str:
    """
    Tạo file Excel từ danh sách tweet.
    Trả về đường dẫn file tạm.
    """
```

### 4. Handler lệnh /scan
```python
async def scan_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Xử lý lệnh /scan từ Telegram.
    - Parse keywords từ args (nếu có), fallback về config
    - Gửi "đang xử lý..."
    - Chạy scan
    - Gửi message tóm tắt
    - Gửi file Excel
    - Xóa file tạm
    """
```

### 5. Hàm auto scan (scheduler)
```python
async def auto_scan_job(bot):
    """
    Chạy tự động mỗi 24h, gửi kết quả vào TELEGRAM_ADMIN_ID.
    """
```

### 6. Khởi động scheduler trong main()
```python
scheduler = AsyncIOScheduler(timezone="Asia/Ho_Chi_Minh")
scheduler.add_job(
    auto_scan_job,
    trigger="cron",
    hour=9,
    minute=0,
    args=[application.bot]
)
scheduler.start()
```

### 7. Đăng ký handler trong main()
```python
application.add_handler(CommandHandler("scan", scan_command))
```

---

## Config cần thêm vào config.py

```python
# ─── Scan Settings ──────────────────────────────────────────────────────────
SCAN_MIN_VIEWS = int(os.getenv("SCAN_MIN_VIEWS", "1000"))
SCAN_HOURS = int(os.getenv("SCAN_HOURS", "24"))
SCAN_MAX_RESULTS = int(os.getenv("SCAN_MAX_RESULTS", "50"))  # tối đa 50 kết quả
```

---

## requirements.txt cần thêm

```
apscheduler>=3.10.0
openpyxl>=3.1.0
```

---

## Railway Variables cần thêm

```
SCAN_MIN_VIEWS = 1000
SCAN_HOURS = 24
```

---

## Xử lý lỗi

| Tình huống | Xử lý |
|-----------|-------|
| Không có cookies.json | Gửi message: "❌ Bot chưa được cấu hình X/Twitter cookies" |
| Rate limit twikit | Chờ 30s, thử lại 1 lần |
| Không có kết quả | Gửi message thông báo, không gửi Excel |
| Lỗi tạo Excel | Log lỗi, chỉ gửi message text |
| User không có quyền | Bỏ qua silently |

---

## Lưu ý quan trọng

1. **KHÔNG viết lại** các handler/tính năng đã có trong bot
2. **Chỉ thêm** scan_command, auto_scan_job và scheduler vào file hiện tại
3. Twikit client phải được **khởi tạo 1 lần** và tái sử dụng, không login lại mỗi lần scan
4. File Excel tạm lưu vào `tempfile.gettempdir()`, **xóa ngay** sau khi `send_document()` xong
5. Message Telegram dùng `parse_mode="HTML"` để format đẹp
6. Tất cả twikit calls phải là `async/await`
7. Giới hạn message Telegram tối đa **10 bài**, còn lại xem trong Excel
