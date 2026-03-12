# Prompt cho Claude Code — KOL Monitor (Tiếng Việt)

## Bài toán cần giải quyết

Tôi cần một công cụ CLI bằng Python để **theo dõi các bài đăng trên X/Twitter từ KOL (Key Opinion Leader)** về dự án Web3 của tôi.

Công cụ cần làm được:
1. Nhận danh sách KOL tôi cung cấp → tổng hợp bài đăng mới nhất của họ
2. Lọc bài đăng theo từ khóa tôi đưa vào
3. Chỉ lấy bài có **trên 2.000 lượt xem** (để đảm bảo là KOL có ảnh hưởng)
4. Tìm kiếm thêm **KOL mới** đang đăng bài về dự án (chưa có trong danh sách)
5. Xuất toàn bộ link bài viết + thông tin ra file **Excel (.xlsx) và CSV**

---

## Tech Stack

- **Ngôn ngữ:** Python 3.8+
- **Thư viện fetch data:** `twikit` — miễn phí, không cần API key, dùng X internal API
- **Thư viện xuất Excel:** `openpyxl` — tạo file .xlsx có định dạng đẹp
- **Xác thực:** Load cookies từ `data/cookies.json` (export thủ công từ browser bằng Cookie-Editor extension — **KHÔNG** dùng login bằng password)

---

## Cấu trúc file cần tạo

```
kol-monitor/
├── monitor.py          # Điểm vào CLI chính
├── config.py           # Cài đặt: từ khóa, min_views, ngưỡng follower
├── fetcher.py          # Wrapper twikit: login cookies, lấy tweet, tìm kiếm
├── filter.py           # Lọc tweet theo từ khóa + lượt xem + thời gian
├── exporter.py         # Xuất kết quả ra .xlsx và .csv
├── reporter.py         # In báo cáo tóm tắt ra terminal
├── requirements.txt    # twikit, openpyxl, pandas
├── .gitignore
└── data/
    ├── kols.json           # Danh sách KOL (người dùng tự chỉnh)
    ├── cookies.json        # Tự tạo sau lần login đầu (không chỉnh)
    ├── seen_tweets.json    # Tự tạo — theo dõi tweet đã xử lý
    └── output/             # File Excel và CSV xuất ra đây
```

---

## config.py

```python
CONFIG = {
    # Từ khóa lọc — tweet phải chứa ít nhất 1 từ (không phân biệt hoa thường)
    "keywords": ["NEXI", "Nexira", "DAEP", "$NEXI"],

    # Lượt xem tối thiểu
    "min_views": 2000,

    # Khoảng thời gian nhìn lại (giờ) — on-demand mode
    "since_hours": 72,

    # Số follower tối thiểu để tài khoản mới được coi là KOL tiềm năng
    "discover_min_followers": 5000,
}
```

---

## data/kols.json — Định dạng danh sách KOL

```json
[
  {
    "username": "username_khong_co_@",
    "name": "Tên hiển thị",
    "tags": ["gaming", "web3"]
  },
  {
    "username": "CryptoInfluencer2",
    "name": "Crypto Influencer 2",
    "tags": ["defi", "nft"]
  }
]
```

---

## Giao diện CLI

```bash
# Chạy cơ bản — lấy 72h gần nhất
python3 monitor.py

# Chế độ daily — chỉ lấy 24h gần nhất
python3 monitor.py --mode daily

# Bật chế độ tìm KOL mới
python3 monitor.py --discover

# Tùy chỉnh từ khóa
python3 monitor.py --keywords "NEXI,Nexira,DAEP"

# Tùy chỉnh ngưỡng lượt xem
python3 monitor.py --min-views 5000

# Kết hợp đầy đủ
python3 monitor.py --mode daily --discover --min-views 2000

# Kiểm tra config không chạy thật
python3 monitor.py --dry-run
```

---

## fetcher.py — Hành vi bắt buộc

```python
# QUAN TRỌNG: Chỉ load cookies, KHÔNG đăng nhập bằng mật khẩu
async def login(self):
    if not COOKIES_FILE.exists():
        raise FileNotFoundError(
            "❌ Không tìm thấy data/cookies.json\n\n"
            "Cách lấy cookies:\n"
            "  1. Đăng nhập x.com thủ công trên Chrome/Firefox\n"
            "  2. Cài extension 'Cookie-Editor'\n"
            "  3. Vào x.com → mở Cookie-Editor → Export (JSON)\n"
            "  4. Lưu file vào: data/cookies.json\n"
            "  5. Chạy lại lệnh này"
        )
    self.client.load_cookies(str(COOKIES_FILE))

# Lấy tweet của 1 user cụ thể
async def get_user_tweets(username: str, limit: int = 20) -> list[dict]

# Tìm tweet theo từ khóa (dùng cho discover mode)
async def search_tweets(query: str, limit: int = 30) -> list[dict]
```

### Định dạng tweet dict (chuẩn hóa đầu ra):

```python
{
    "id": str,
    "username": str,
    "name": str,
    "followers": int,
    "text": str,
    "created_at": str,      # chuỗi gốc từ twikit
    "views": int,           # mặc định 0 nếu None
    "likes": int,
    "retweets": int,
    "replies": int,
    "quotes": int,
    "url": str,             # https://x.com/{username}/status/{id}
    "lang": str,
    "source": str,          # "known_kol" hoặc "discovered"
}
```

---

## filter.py — Logic lọc

```python
class TweetFilter:
    def filter(self, tweets: list[dict], exclude_ids: set) -> list[dict]:
        # 1. Bỏ qua nếu id đã có trong exclude_ids (đã báo cáo lần trước)
        # 2. Bỏ qua nếu không chứa từ khóa (case-insensitive)
        # 3. Bỏ qua nếu views < min_views
        # 4. Bỏ qua nếu tweet cũ hơn khoảng thời gian cho phép
        # Trả về list sắp xếp theo views giảm dần
```

---

## exporter.py — Xuất Excel và CSV ⭐

Đây là phần quan trọng nhất. Tạo 2 file output mỗi lần chạy:

### File Excel (.xlsx)
Dùng `openpyxl` để tạo file có **2 sheet**:

**Sheet 1: "Bài Đăng KOL"** — toàn bộ kết quả lọc được

| Cột | Nội dung | Ghi chú |
|-----|----------|---------|
| A | STT | Số thứ tự |
| B | Ngày đăng | Định dạng DD/MM/YYYY HH:MM |
| C | Username | @username |
| D | Tên KOL | Tên hiển thị |
| E | Followers | Số follower (định dạng có dấu phẩy) |
| F | Lượt xem | Views (định dạng có dấu phẩy) |
| G | Likes | |
| H | Retweets | |
| I | Replies | |
| J | Nội dung | 150 ký tự đầu của tweet |
| K | Link bài viết | Hyperlink có thể click |
| L | Loại | "KOL đã theo dõi" hoặc "KOL mới phát hiện" |
| M | Từ khóa khớp | Từ khóa nào trong tweet này |

Yêu cầu định dạng Excel:
- Hàng tiêu đề: nền xanh đậm (#1DA1F2 — màu X/Twitter), chữ trắng, in đậm
- Cột K (Link): là hyperlink thật, có thể click vào mở tweet
- Xen kẽ màu nền hàng: trắng và xám nhạt (#F8F9FA) cho dễ đọc
- Cố định hàng tiêu đề (freeze panes)
- Tự động điều chỉnh độ rộng cột (auto-fit)
- Số lượt xem và follower: định dạng có dấu phẩy (1,234,567)

**Sheet 2: "Tóm Tắt"** — thống kê tổng quan

| Thông tin | Giá trị |
|-----------|---------|
| Thời gian chạy | DD/MM/YYYY HH:MM |
| Chế độ | daily / on-demand |
| Khoảng thời gian | 24h / 72h |
| Từ khóa | NEXI, Nexira, DAEP |
| Lượt xem tối thiểu | 2,000 |
| Tổng bài từ KOL đã theo dõi | N |
| Tổng bài từ KOL mới phát hiện | N |
| Tổng cộng | N |
| Tổng lượt xem | N |
| Bài xem nhiều nhất | @username — N views |

### File CSV (.csv)
- Encoding: UTF-8-BOM (để Excel mở đúng tiếng Việt)
- Các cột: stt, ngay_dang, username, ten_kol, followers, luot_xem, likes, retweets, replies, noi_dung_150ky, link, loai, tu_khoa_khop
- Dấu phân cách: dấu phẩy

### Tên file output:
```
data/output/kol_report_2024-03-11_0900.xlsx
data/output/kol_report_2024-03-11_0900.csv
```

---

## reporter.py — In ra terminal

```
╔══════════════════════════════════════════════╗
║         KOL Monitor — Đang chạy...          ║
╠══════════════════════════════════════════════╣
║  Chế độ    : daily (24h gần nhất)           ║
║  Từ khóa   : NEXI, Nexira, DAEP, $NEXI      ║
║  Min Views : 2,000                          ║
║  Discover  : Có                             ║
╚══════════════════════════════════════════════╝

🔐 Đang load cookies...
✅ Đăng nhập thành công

📋 Đang kiểm tra 5 KOL đã theo dõi...
   @KOL_username_1 .............. ✓ 2 bài khớp
   @KOL_username_2 .............. ✓ 0 bài khớp
   @KOL_username_3 .............. ✗ Không tìm thấy tài khoản (bỏ qua)

🔍 Đang tìm KOL mới...
   Tìm kiếm: "NEXI" ............. ✓ 3 bài liên quan
   Tìm kiếm: "Nexira" ........... ✓ 1 bài liên quan

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  KẾT QUẢ
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  @CryptoWhale_X      15,420 views   "Vừa xem $NEXI tokenomics..."
  @BlockchainGuru     8,300 views    "DAEP cross-game layer..."
  @NewKOL (mới)       5,100 views    "Nexira đang build..."
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Hoàn tất!
   📊 Excel : data/output/kol_report_2024-03-11_0900.xlsx
   📄 CSV   : data/output/kol_report_2024-03-11_0900.csv
   🔗 Tổng  : 3 bài viết | 28,820 lượt xem tổng cộng
```

---

## Xử lý lỗi — Thông báo tiếng Việt

| Tình huống | Thông báo |
|-----------|-----------|
| Thiếu `cookies.json` | Hướng dẫn chi tiết cách export cookies |
| Thiếu `kols.json` | Tự tạo file mẫu, yêu cầu người dùng điền |
| Không tìm thấy @username | ⚠️ Cảnh báo, bỏ qua, tiếp tục |
| Rate limit | ⏳ Chờ 60 giây rồi thử lại... |
| Tweet không có view count | Mặc định 0, tự động bị lọc |
| Không có kết quả nào | ℹ️ Không có bài đăng nào khớp tiêu chí |

---

## Rate Limiting

```python
# Giữa mỗi lần fetch user tweets
await asyncio.sleep(2)

# Giữa mỗi search query
await asyncio.sleep(3)

# Khi bị rate limit
except TooManyRequests:
    print("⏳ Bị rate limit, chờ 60 giây...")
    await asyncio.sleep(60)
    # Thử lại 1 lần
```

---

## Xử lý seen_tweets.json

```python
# Load khi bắt đầu
seen_ids: set = load_seen_tweets()  # set of tweet ID strings

# Sau khi filter, thêm ID mới vào
for tweet in results:
    seen_ids.add(tweet["id"])

# Lưu lại — giữ tối đa 5000 ID gần nhất
save_seen_tweets(seen_ids)
```

---

## .gitignore

```
data/cookies.json
data/seen_tweets.json
data/output/
__pycache__/
*.pyc
.env
```

---

## requirements.txt

```
twikit>=2.3.0
openpyxl>=3.1.0
pandas>=2.0.0
```

---

## Lưu ý khi implement

1. Tất cả twikit calls phải là `async/await`, dùng `asyncio.run(main())` làm entry point
2. Parse `created_at` với format: `"%a %b %d %H:%M:%S %z %Y"`
3. Format số lớn: `15400` → `"15,400"` | `1250000` → `"1,250,000"`
4. Cột Link trong Excel phải là **hyperlink thật** dùng `openpyxl`:
   ```python
   from openpyxl.styles import Font
   cell.value = url
   cell.hyperlink = url
   cell.font = Font(color="1DA1F2", underline="single")
   ```
5. CSV dùng encoding `utf-8-sig` để Excel Windows mở đúng tiếng Việt
6. Tạo thư mục `data/output/` tự động nếu chưa có
7. **KHÔNG** implement login bằng username/password
8. **KHÔNG** dùng database — chỉ dùng JSON files
9. **KHÔNG** tạo web UI — chỉ CLI

---

## Ví dụ output Excel mong muốn

| STT | Ngày đăng | Username | Tên KOL | Followers | Lượt xem | Likes | Retweets | Replies | Nội dung | Link | Loại | Từ khóa |
|-----|-----------|----------|---------|-----------|----------|-------|----------|---------|----------|------|------|---------|
| 1 | 11/03/2024 09:23 | @CryptoWhale_X | Crypto Whale | 125,300 | 15,420 | 832 | 214 | 67 | Vừa xem $NEXI tokenomics... | [click] | KOL đã theo dõi | $NEXI, NEXI |
| 2 | 11/03/2024 07:15 | @NewGamingKOL | New Gaming KOL | 45,200 | 5,100 | 203 | 87 | 34 | Nexira đang build... | [click] | KOL mới phát hiện | Nexira |
