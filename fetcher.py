"""
fetcher.py — Handles all Twitter/X data fetching via twikit
"""

import asyncio
import json
from pathlib import Path

COOKIES_FILE = Path(__file__).parent / "data" / "cookies.json"


class TwitterFetcher:
    def __init__(self):
        self.client = None

    async def login(self):
        """Load session from cookies file. Does NOT login with password."""
        from twikit import Client

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

        self.client = Client("en-US")

        # Cookie-Editor exports a list of objects — convert to {name: value} dict
        raw = json.loads(COOKIES_FILE.read_text())
        if isinstance(raw, list):
            cookies = {c["name"]: c["value"] for c in raw}
        else:
            cookies = raw
        self.client.set_cookies(cookies)

    def _tweet_to_dict(self, tweet) -> dict:
        """Normalize a twikit Tweet object to a plain dict."""
        try:
            views = int(tweet.view_count) if tweet.view_count else 0
        except (ValueError, TypeError):
            views = 0

        return {
            "id": str(tweet.id),
            "username": tweet.user.screen_name if tweet.user else "unknown",
            "name": tweet.user.name if tweet.user else "unknown",
            "followers": tweet.user.followers_count if tweet.user else 0,
            "text": tweet.text or "",
            "created_at": str(tweet.created_at),
            "views": views,
            "likes": tweet.favorite_count or 0,
            "retweets": tweet.retweet_count or 0,
            "replies": tweet.reply_count or 0,
            "quotes": tweet.quote_count or 0,
            "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}" if tweet.user else "",
            "profile_url": f"https://x.com/{tweet.user.screen_name}" if tweet.user else "",
            "lang": tweet.lang or "und",
            "source": "",  # set by caller: "known_kol" or "discovered"
        }

    async def _with_rate_limit_retry(self, coro_fn, label: str):
        """Run coro_fn(), retry once after 90s if rate-limited (429)."""
        for attempt in range(2):
            try:
                return await coro_fn()
            except Exception as e:
                msg = str(e)
                if "429" in msg or "Rate limit" in msg or "rate limit" in msg:
                    if attempt == 0:
                        print(f"\n   ⏳ Rate limit — chờ 90 giây rồi thử lại...", flush=True)
                        await asyncio.sleep(90)
                        continue
                raise RuntimeError(f"{label}: {e}")
        raise RuntimeError(f"{label}: vẫn bị rate limit sau khi chờ")

    async def get_user_tweets(self, username: str, limit: int = 20) -> list[dict]:
        """Fetch recent tweets from a specific user."""
        async def _fetch():
            user = await self.client.get_user_by_screen_name(username)
            tweets = await user.get_tweets("Tweets", count=limit)
            return [self._tweet_to_dict(t) for t in tweets]
        return await self._with_rate_limit_retry(_fetch, f"@{username}")

    async def search_tweets(self, query: str, limit: int = 30) -> list[dict]:
        """Search tweets by keyword — used for KOL discovery."""
        async def _fetch():
            results = await self.client.search_tweet(query, "Latest", count=limit)
            return [self._tweet_to_dict(t) for t in results]
        return await self._with_rate_limit_retry(_fetch, f"search:{query}")
