"""
monitor_core.py — Core logic có thể gọi trực tiếp từ bot hoặc CLI
"""

import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Callable, Awaitable

from config import CONFIG
from fetcher import TwitterFetcher
from filter import TweetFilter
import exporter

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "output"


async def run_monitor(
    usernames: list[str],
    output_name: str = None,
    since_hours: int = None,
    max_tweets: int = 50,
    on_progress: Callable[[str], Awaitable[None]] = None,
) -> tuple[Path | None, Path | None, list[dict], list[dict]]:
    """
    Chạy KOL Monitor cho danh sách usernames.

    Args:
        usernames:    Danh sách username (không cần @)
        output_name:  Tên file output (không có đuôi), mặc định = tự động
        since_hours:  Số giờ nhìn lại, mặc định lấy từ config
        max_tweets:   Số tweet tối đa mỗi KOL
        on_progress:  Async callback(message: str) để gửi tiến độ realtime

    Returns:
        (xlsx_path, csv_path, kol_hits, discovered)
        xlsx_path = None vì chỉ xuất CSV
    """
    since_hours = since_hours or CONFIG.get("since_hours", 72)
    keywords = CONFIG["keywords"]
    min_views = CONFIG["min_views"]

    since_dt = datetime.now(timezone.utc) - timedelta(hours=since_hours)
    fetcher = TwitterFetcher()
    tweet_filter = TweetFilter(keywords=keywords, min_views=min_views, since=since_dt)

    await fetcher.login()

    kol_hits: list[dict] = []

    for username in usernames:
        if on_progress:
            await on_progress(f"🔍 Đang kiểm tra @{username}...")
        try:
            tweets = await fetcher.get_user_tweets(username, limit=max_tweets)
            for t in tweets:
                t["source"] = "known_kol"
            hits = tweet_filter.filter(tweets)
            kol_hits.extend(hits)
            if on_progress:
                await on_progress(
                    f"   @{username} — {len(hits)} bài khớp / {len(tweets)} bài tổng"
                )
        except Exception as e:
            if on_progress:
                await on_progress(f"   @{username} — ✗ Lỗi: {e}")
        await asyncio.sleep(5)

    if not kol_hits:
        return None, None, [], []

    _, csv_path = exporter.export(
        kol_hits=kol_hits,
        discovered=[],
        keywords=keywords,
        mode="on-demand",
        since_hours=since_hours,
        min_views=min_views,
        output_dir=OUTPUT_DIR,
        output_name=output_name,
        csv_only=True,
        slim=False,
    )

    return None, csv_path, kol_hits, []
