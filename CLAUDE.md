# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run CLI monitor (requires data/cookies.json)
python monitor.py
python monitor.py --mode daily
python monitor.py --usernames "user1,user2"
python monitor.py --discover
python monitor.py --dry-run

# Run Telegram bot locally (requires secrets.py)
python telegram_bot.py
```

## Architecture

Two entry points share the same core:

- **`monitor.py`** — CLI tool. Reads KOL list from `data/kols.json`, runs full pipeline, saves results to `data/output/`.
- **`telegram_bot.py`** — Telegram bot. Accepts usernames via chat message, calls `monitor_core.run_monitor()`, replies with CSV.

Core pipeline:
1. `fetcher.py` (`TwitterFetcher`) — authenticates via cookies, fetches tweets with rate-limit retry
2. `filter.py` (`TweetFilter`) — filters by keyword, view count, and time window
3. `exporter.py` — writes CSV (and optionally XLSX) to `data/output/`
4. `monitor_core.py` — thin async wrapper around the above, used by the bot

## Configuration

**`config.py`** — keywords, min_views, since_hours. All Telegram credentials are read from env vars:
- `TELEGRAM_TOKEN` — required
- `TELEGRAM_ADMIN_ID` — integer
- `TELEGRAM_ALLOWED_IDS` — comma-separated integers
- `TWITTER_COOKIES` — JSON string of X.com cookies (Railway/production)

Local development uses `secrets.py` (gitignored) as fallback for `TELEGRAM_TOKEN` / `TELEGRAM_ADMIN_ID`.
Twitter cookies are read from `TWITTER_COOKIES` env var first, then fallback to `data/cookies.json`.

**`data/kols.json`** — list of `{username, name, tags}` objects for CLI mode.

## Secrets / gitignored files

- `secrets.py` — local Telegram credentials
- `data/cookies.json` — X.com browser cookies (export via Cookie-Editor extension)
- `data/allowed_users.json` — persisted allowed Telegram user IDs (written by `/adduser`)
- `data/output/` — generated CSV/XLSX files

## Deployment (Railway)

Set these environment variables on Railway:
- `TELEGRAM_TOKEN`
- `TELEGRAM_ADMIN_ID`
- `TWITTER_COOKIES` (minified JSON from `data/cookies.json`)
- `TELEGRAM_ALLOWED_IDS` (optional, comma-separated)

Start command: `python telegram_bot.py`
