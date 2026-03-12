# 📋 CLAUDE CODE CLI — TELEGRAM MONITOR DEPLOY GUIDE
> Dành cho: Hệ thống Python X Monitor đã có sẵn  
> Mục tiêu: Thêm Telegram channel/group monitor, output CSV tương tự Twitter  
> Nguyên tắc: **KHÔNG thay đổi bất kỳ file/logic cũ nào**

---

## BƯỚC 1 — Khảo sát hệ thống hiện tại

Mở terminal tại thư mục project, chạy Claude Code CLI:

```
claude
```

Paste prompt sau:

---

### 🔍 PROMPT 1: Scan cấu trúc project

```
Please scan and describe the current project structure. I need to understand:
1. List all Python files and their purpose (one-line summary each)
2. Find the X/Twitter monitor file — show me the CSV output columns it produces
3. Find requirements.txt or pyproject.toml — list current dependencies
4. Find any config files (yaml, json, .env.example)
5. Identify the main entry point (how is the X monitor triggered/run)

DO NOT modify any files. Read only.
Output a clear summary tree.
```

---

## BƯỚC 2 — Xác nhận CSV schema của Twitter

Sau khi có kết quả Prompt 1, paste tiếp:

---

### 🔍 PROMPT 2: Extract CSV schema

```
Based on the X/Twitter monitor file you found, show me:
1. The exact CSV columns being written (header row)
2. The exact code block that writes to CSV
3. The output file naming convention (e.g. tweets_2024-01-01.csv)

DO NOT modify anything. Read only.
I will use this to make the Telegram monitor produce identical CSV format.
```

> ⏸️ **DỪNG LẠI** — Ghi lại CSV columns bạn thấy. Ví dụ điển hình:
> `timestamp, source, author, content, url, matched_keywords`

---

## BƯỚC 3 — Cài thư viện mới (không đụng cũ)

---

### ⚙️ PROMPT 3: Add dependency

```
I need to add Telethon to the project for a NEW Telegram monitor module.
Do the following:
1. Add `telethon>=1.34.0` to requirements.txt (append only, do not change existing lines)
2. If there is a pyproject.toml instead, add it there under [project.dependencies]
3. Show me the diff of what you changed

Then run: pip install telethon
```

---

## BƯỚC 4 — Tạo config file cho Telegram sources

---

### ⚙️ PROMPT 4: Create Telegram sources config

```
Create a new file: config/telegram_sources.yaml

This file lists Telegram public channels/groups to monitor.
Use this exact structure:

```yaml
# Telegram Monitor Sources
# Add public channel/group usernames below
# type: "channel" or "group"
# keywords: list of strings to filter (null = monitor all messages)

sources:
  - id: "example_crypto_channel"
    username: "example_channel"
    type: "channel"
    keywords:
      - "listing"
      - "partnership"
      - "airdrop"
    priority: "high"

  - id: "example_vn_group"
    username: "example_group"
    type: "group"
    keywords:
      - "$TOKEN"
      - "alpha"
    priority: "medium"
```

Also create: config/telegram_sources.example.yaml as a copy for documentation.
DO NOT modify any existing config files.
```

---

## BƯỚC 5 — Tạo .env variables mới

---

### ⚙️ PROMPT 5: Add env variables

```
I need to add Telegram API credentials to the environment config.
Do the following:

1. If .env.example exists: APPEND these lines (do not change existing lines):
```
# --- Telegram Monitor (NEW) ---
TELEGRAM_API_ID=your_api_id_here
TELEGRAM_API_HASH=your_api_hash_here
TELEGRAM_SESSION_NAME=tg_monitor_session
TELEGRAM_OUTPUT_DIR=output/telegram
```

2. If .env.example does NOT exist: create it with only the lines above.

3. If there is a .env file (real credentials): also APPEND the same lines with placeholder values.

Show me exactly what was changed/added.
```

> 📌 **Lấy API credentials tại:** https://my.telegram.org/apps  
> Đăng nhập → App configuration → Tạo app → Copy `api_id` và `api_hash`

---

## BƯỚC 6 — Build Telegram Monitor module

Đây là prompt quan trọng nhất. Paste **nguyên văn**, thay `[PASTE_CSV_COLUMNS_HERE]` bằng columns bạn thấy ở Bước 2:

---

### 🏗️ PROMPT 6: Build the Telegram monitor module

```
Create a NEW file: monitors/telegram_monitor.py

Requirements:
- This is a standalone module. DO NOT import from or modify existing monitor files.
- Use Telethon (MTProto) for Telegram access
- Read sources from config/telegram_sources.yaml
- Output CSV with IDENTICAL columns to the existing X monitor: [PASTE_CSV_COLUMNS_HERE]
- CSV output path: read from env var TELEGRAM_OUTPUT_DIR (default: "output/telegram")
- CSV filename format: telegram_YYYY-MM-DD.csv (one file per day, append mode)
- Filter messages by keywords if defined in config; if keywords is null, capture all
- Handle both channels and groups
- On startup: attempt to join all sources in config (skip if already joined or private)
- Log errors to logs/telegram_monitor.log (create logs/ dir if not exists)
- Graceful shutdown on KeyboardInterrupt

Class structure:
```python
class TelegramMonitor:
    def __init__(self)         # load env, load yaml config
    def _load_sources(self)    # parse telegram_sources.yaml
    def _get_csv_writer(self)  # return csv.writer with correct columns, append mode
    def _match_keywords(self, text, keywords) -> bool
    def _normalize_row(self, event, source) -> dict  # map to CSV schema
    def _write_row(self, row: dict)
    async def start(self)      # join channels, register event listener, run
    async def stop(self)

def main():
    monitor = TelegramMonitor()
    asyncio.run(monitor.start())

if __name__ == "__main__":
    main()
```

CSV row mapping (match X monitor columns exactly):
- timestamp → message.date ISO format
- source → "telegram"
- author → channel username from config
- content → message.text (truncate at 1000 chars)
- url → https://t.me/{username}/{message_id}
- matched_keywords → comma-separated list of matched keywords (or "ALL" if keywords=null)

[If the X monitor has additional columns not listed above, add them with empty string "" as default value]

Show me the complete file after creation.
```

---

## BƯỚC 7 — Tạo runner script độc lập

---

### ⚙️ PROMPT 7: Create standalone runner

```
Create a NEW file: run_telegram_monitor.py at the project root.

Content:
```python
"""
Telegram Monitor — Standalone Runner
Run with: python run_telegram_monitor.py

This script is independent of the X monitor runner.
Do not modify the existing run script.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from monitors.telegram_monitor import main

if __name__ == "__main__":
    main()
```

Also update README.md if it exists:
- APPEND a new section at the bottom called "## Telegram Monitor"
- Add: how to configure sources, how to run, required env vars
- DO NOT modify any existing README content
```

---

## BƯỚC 8 — First-time auth (chạy 1 lần duy nhất)

---

### ⚙️ PROMPT 8: Create auth helper

```
Create a NEW file: scripts/telegram_auth.py

This is a one-time setup script to authenticate with Telegram and save the session file.

```python
"""
Run ONCE to authenticate:
    python scripts/telegram_auth.py

This creates a .session file. After this, run_telegram_monitor.py
will use the saved session without re-authenticating.
"""
import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient

load_dotenv()

async def auth():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session = os.getenv("TELEGRAM_SESSION_NAME", "tg_monitor_session")
    
    client = TelegramClient(session, api_id, api_hash)
    await client.start()
    me = await client.get_me()
    print(f"✅ Authenticated as: {me.username} ({me.first_name})")
    print(f"✅ Session saved to: {session}.session")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(auth())
```

Also add `*.session` to .gitignore (append only, do not modify existing lines).
```

---

## BƯỚC 9 — Verify không có conflict

---

### ✅ PROMPT 9: Conflict check

```
Please do a final review:

1. List ALL files that were newly created (should be only new files)
2. List ALL files that were modified (should be ONLY: requirements.txt, .env.example, .gitignore, README.md)
3. Confirm that the existing X monitor file(s) were NOT touched
4. Run a quick syntax check on monitors/telegram_monitor.py:
   python -m py_compile monitors/telegram_monitor.py
5. Show the final project structure tree highlighting new files

If any existing monitor logic was accidentally modified, revert it now.
```

---

## BƯỚC 10 — Test run

---

### ✅ PROMPT 10: Test flow

```
Let's test the Telegram monitor step by step:

Step 1 - Auth (run once):
    python scripts/telegram_auth.py

Step 2 - Verify config:
    python -c "import yaml; print(yaml.safe_load(open('config/telegram_sources.yaml')))"

Step 3 - Dry run (start monitor, wait 10 seconds, stop):
    timeout 10 python run_telegram_monitor.py || true

Step 4 - Check output:
    ls -la output/telegram/
    head -5 output/telegram/telegram_$(date +%Y-%m-%d).csv

Step 5 - Compare CSV headers with X monitor output:
    head -1 output/telegram/telegram_$(date +%Y-%m-%d).csv
    head -1 output/[EXISTING_TWITTER_OUTPUT_DIR]/

Confirm both CSV headers are identical.
```

---

## 📁 File structure sau khi deploy

```
project/
├── monitors/
│   ├── x_monitor.py          ← KHÔNG THAY ĐỔI
│   └── telegram_monitor.py   ← MỚI ✨
├── config/
│   ├── [existing configs]    ← KHÔNG THAY ĐỔI  
│   ├── telegram_sources.yaml ← MỚI ✨
│   └── telegram_sources.example.yaml ← MỚI ✨
├── scripts/
│   └── telegram_auth.py      ← MỚI ✨ (chạy 1 lần)
├── output/
│   ├── twitter/              ← KHÔNG THAY ĐỔI
│   └── telegram/             ← MỚI ✨
├── logs/
│   └── telegram_monitor.log  ← MỚI ✨ (auto-created)
├── run_telegram_monitor.py   ← MỚI ✨
├── requirements.txt          ← chỉ append telethon
├── .env.example              ← chỉ append TG vars
└── .gitignore                ← chỉ append *.session
```

---

## ⚠️ Lưu ý quan trọng

| Vấn đề | Giải pháp |
|---|---|
| Telegram yêu cầu phone number khi auth lần đầu | Chạy `telegram_auth.py` interactive trên máy local |
| `.session` file rất nhạy cảm | Đã add vào `.gitignore`, KHÔNG commit lên git |
| Channel private không join được | Bỏ qua, monitor sẽ log lỗi và tiếp tục |
| Rate limit từ Telegram | Telethon tự handle, không cần config thêm |
| Deploy lên server | Copy `.session` file lên server cùng với code |

---

## 🚀 Chạy song song cả 2 monitor

```bash
# Terminal 1 — X Monitor (giữ nguyên cách cũ)
python run_x_monitor.py

# Terminal 2 — Telegram Monitor (mới)  
python run_telegram_monitor.py
```

Hoặc dùng `screen` / `tmux` / `supervisor` để chạy background trên server.
