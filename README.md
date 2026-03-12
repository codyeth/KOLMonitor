# KOL Monitor 🔍

Track KOL posts about your project on X/Twitter — free, no API key required.

## Features
- ✅ Monitor a list of known KOLs for new posts
- 🔍 Discover new accounts posting about your project
- 👁 Filter by minimum view count (e.g. 2000+)
- 🕐 Filter by time window (daily or custom)
- 📄 Markdown + JSON report output
- 🔄 Deduplication — never report the same tweet twice

## Quick Start

### 1. Install
```bash
pip install -r requirements.txt
```

### 2. Configure

Edit `config.py`:
```python
CONFIG = {
    "keywords": ["NEXI", "Nexira", "DAEP", "$NEXI"],
    "min_views": 2000,
    "since_hours": 72,
    "x_username": "your_x_handle",
    "x_email": "your@email.com",
    "x_password": "yourpassword",
}
```

> ⚠️ **Security tip:** Create a dedicated X account for monitoring. Do NOT use your main account.

### 3. Add your KOL list

Edit `data/kols.json`:
```json
[
  { "username": "CryptoKOL1", "name": "Crypto KOL 1", "tags": ["gaming"] },
  { "username": "Web3Influencer", "name": "Web3 Influencer", "tags": ["defi"] }
]
```

### 4. Run

```bash
# On-demand (last 72h by default)
python monitor.py

# Daily mode (last 24h only)
python monitor.py --mode daily

# Custom keywords + view threshold
python monitor.py --keywords "NEXI,Nexira" --min-views 5000

# Also discover new KOLs
python monitor.py --discover

# Full combo
python monitor.py --mode daily --discover --min-views 2000
```

## Output

Each run generates two files in `data/output/`:
- `kol_report_YYYY-MM-DD_HHMM.md` — human-readable markdown report
- `kol_data_YYYY-MM-DD_HHMM.json` — raw data for programmatic use

### Sample Report Output
```
## ✅ Hits from Known KOLs (3 posts)

### 1. @CryptoWhale_X (125.3K followers)
- 👁 15.4K views · ❤️ 832 · 🔁 214 · 💬 67
- 🕐 Mon Mar 11 08:23:11 +0000 2024
- 📝 "Just looked at $NEXI tokenomics — the DAEP cross-game interoperability is..."
- 🔗 https://x.com/CryptoWhale_X/status/...
```

## Automation (Optional)

### Run daily at 9am (Linux/Mac cron)
```bash
0 9 * * * cd /path/to/kol-monitor && python monitor.py --mode daily >> logs/daily.log 2>&1
```

### Windows Task Scheduler
Create a task running:
```
python C:\path\to\kol-monitor\monitor.py --mode daily
```

## Rate Limits & Safety

- The script adds 2s delay between each KOL lookup
- Login cookies are saved — no re-login needed unless session expires
- Run max 2-3x per day to avoid account flagging
- Keep KOL list reasonable (< 50 accounts per run)

## Upgrading to Paid (when ready)

When you outgrow the free tier, the `fetcher.py` abstraction makes it easy to swap in:
- **Twitterapi.io** — $10/mo, more reliable, higher rate limits
- **Apify** — $30/mo, cloud-based, no local account needed
- **X API Basic** — $100/mo, official, most stable

Just replace the methods in `fetcher.py` — everything else stays the same.
