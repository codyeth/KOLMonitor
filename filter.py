"""
filter.py — Keyword matching and view count filtering
"""

from datetime import datetime, timezone


class TweetFilter:
    def __init__(self, keywords: list[str], min_views: int, since: datetime):
        self.keywords = [k.lower() for k in keywords]
        self.min_views = min_views
        self.since = since

    def matched_keywords(self, text: str) -> list[str]:
        text_lower = text.lower()
        return [kw for kw in self.keywords if kw in text_lower]

    def matches_keyword(self, text: str) -> bool:
        if not self.keywords:   # no keyword filter — accept all
            return True
        return bool(self.matched_keywords(text))

    def is_recent(self, created_at_str: str) -> bool:
        try:
            # twikit returns strings like "Mon Jan 01 00:00:00 +0000 2024"
            dt = datetime.strptime(created_at_str, "%a %b %d %H:%M:%S %z %Y")
            return dt >= self.since
        except Exception:
            return True  # include if we can't parse

    def filter(self, tweets: list[dict], exclude_ids: set = None) -> list[dict]:
        results = []
        exclude_ids = exclude_ids or set()

        for t in tweets:
            # Skip already seen
            if t["id"] in exclude_ids:
                continue
            # Must match at least one keyword
            if not self.matches_keyword(t["text"]):
                continue
            # Must meet minimum views
            if t["views"] < self.min_views:
                continue
            # Must be within time window
            if not self.is_recent(t["created_at"]):
                continue

            t = dict(t)
            t["matched_keywords"] = ", ".join(self.matched_keywords(t["text"]))
            results.append(t)

        # Sort by views descending
        results.sort(key=lambda x: x["views"], reverse=True)
        return results
