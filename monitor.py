"""
KOL Monitor - Twitter/X KOL tracking tool using twikit
Usage:
  python monitor.py                                     # run with defaults (72h)
  python monitor.py --mode daily                        # filter last 24h
  python monitor.py --discover                          # also find new KOLs
  python monitor.py --usernames "user1,user2"           # chi check cac KOL nay
  python monitor.py --output-name KOL_Shan              # dat ten file output
  python monitor.py --all-posts                         # lay tat ca, khong loc keyword
  python monitor.py --dry-run                           # check config, no real run
"""

import asyncio
import json
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from config import CONFIG
from fetcher import TwitterFetcher
from filter import TweetFilter
from reporter import print_results, print_done
import exporter

DATA_DIR = Path(__file__).parent / "data"
OUTPUT_DIR = DATA_DIR / "output"
KOLS_FILE = DATA_DIR / "kols.json"
SEEN_FILE = DATA_DIR / "seen_tweets.json"


def parse_args():
    parser = argparse.ArgumentParser(description="KOL Monitor for X/Twitter")
    parser.add_argument("--mode", choices=["daily", "on-demand"], default="on-demand",
                        help="daily = last 24h | on-demand = all recent (default)")
    parser.add_argument("--keywords", type=str, default=None,
                        help="Comma-separated keywords (overrides config)")
    parser.add_argument("--min-views", type=int, default=None,
                        help="Minimum view count (overrides config)")
    parser.add_argument("--discover", action="store_true",
                        help="Also search for new KOLs posting about the project")
    parser.add_argument("--max-tweets", type=int, default=50,
                        help="Max tweets to fetch per KOL (default: 50)")
    parser.add_argument("--usernames", type=str, default=None,
                        help="Chi kiem tra cac username nay (cach nhau bang dau phay)")
    parser.add_argument("--output-name", type=str, default=None,
                        help="Ten file output khong co duoi, vd: KOL_Shan")
    parser.add_argument("--all-posts", action="store_true",
                        help="Lay tat ca bai viet, khong loc theo tu khoa")
    parser.add_argument("--csv-only", action="store_true",
                        help="Chi tao file CSV, khong tao Excel")
    parser.add_argument("--slim", action="store_true",
                        help="CSV chi co 2 cot: link_bai_viet va link_x")
    parser.add_argument("--append", action="store_true",
                        help="Ghi them vao file CSV co san (khong ghi de)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print config and exit without running")
    return parser.parse_args()


def load_kols() -> list[dict]:
    if not KOLS_FILE.exists():
        print(f"Khong tim thay danh sach KOL tai {KOLS_FILE}")
        sample = [
            {"username": "CryptoKOL1", "name": "Crypto KOL 1", "tags": ["gaming", "web3"]},
        ]
        KOLS_FILE.parent.mkdir(parents=True, exist_ok=True)
        KOLS_FILE.write_text(json.dumps(sample, indent=2, ensure_ascii=False))
    return json.loads(KOLS_FILE.read_text(encoding="utf-8"))


def load_seen_tweets() -> set:
    if not SEEN_FILE.exists():
        return set()
    data = json.loads(SEEN_FILE.read_text())
    return set(data.get("ids", []))


def save_seen_tweets(seen: set):
    ids = list(seen)[-5000:]
    SEEN_FILE.write_text(json.dumps({"ids": ids}, indent=2))


async def main():
    args = parse_args()

    if args.all_posts:
        keywords = []
    elif args.keywords:
        keywords = [k.strip() for k in args.keywords.split(",")]
    else:
        keywords = CONFIG["keywords"]

    min_views = args.min_views if args.min_views is not None else CONFIG["min_views"]
    since_hours = 24 if args.mode == "daily" else CONFIG.get("since_hours", 72)
    mode_label = "daily (24h)" if args.mode == "daily" else f"on-demand ({since_hours}h)"
    kw_display = ", ".join(keywords) if keywords else "Tat ca (khong loc)"

    print(f"""
╔══════════════════════════════════════════════╗
║         KOL Monitor — Dang chay...          ║
╠══════════════════════════════════════════════╣
║  Che do    : {mode_label:<32}║
║  Tu khoa   : {kw_display:<32}║
║  Min Views : {min_views:<32,}║
║  Max tweets: {args.max_tweets:<32}║
║  Discover  : {'Co' if args.discover else 'Khong':<32}║
╚══════════════════════════════════════════════╝
""")

    if args.dry_run:
        print("Dry run — thoat.")
        return

    all_kols = load_kols()

    if args.usernames:
        filter_names = {u.strip().lower().lstrip("@") for u in args.usernames.split(",")}
        kols = [k for k in all_kols if k["username"].lower() in filter_names]
        existing = {k["username"].lower() for k in kols}
        for name in filter_names:
            if name not in existing:
                kols.append({"username": name, "name": name, "tags": []})
        print(f"Chi kiem tra {len(kols)} KOL: {', '.join('@'+k['username'] for k in kols)}\n")
    else:
        kols = all_kols

    seen_ids = load_seen_tweets()
    since_dt = datetime.now(timezone.utc) - timedelta(hours=since_hours)

    fetcher = TwitterFetcher()
    tweet_filter = TweetFilter(keywords=keywords, min_views=min_views, since=since_dt)

    print("Dang load cookies...")
    try:
        await fetcher.login()
    except FileNotFoundError as e:
        print(e)
        return
    print("Dang nhap thanh cong\n")

    print(f"Dang kiem tra {len(kols)} KOL (moi KOL lay toi da {args.max_tweets} tweets)...")
    kol_hits = []

    for kol in kols:
        username = kol["username"]
        print(f"   @{username} ", end="", flush=True)
        try:
            tweets = await fetcher.get_user_tweets(username, limit=args.max_tweets)
            for t in tweets:
                t["source"] = "known_kol"
            hits = tweet_filter.filter(tweets, exclude_ids=seen_ids)
            for t in hits:
                seen_ids.add(t["id"])
            kol_hits.extend(hits)
            print(f"✓ {len(hits)} bai khop / {len(tweets)} bai tong")
        except Exception as e:
            print(f"✗ {e}")
        await asyncio.sleep(5)

    discovered = []
    if args.discover:
        print(f"\nDang tim KOL moi...")
        known_usernames = {k["username"].lower() for k in kols}
        search_keywords = keywords if keywords else CONFIG["keywords"]
        try:
            for keyword in search_keywords[:2]:
                print(f"   Tim kiem: \"{keyword}\" ", end="", flush=True)
                tweets = await fetcher.search_tweets(keyword, limit=30)
                for t in tweets:
                    t["source"] = "discovered"
                hits = tweet_filter.filter(tweets, exclude_ids=seen_ids)
                new_hits = []
                for t in hits:
                    if t["username"].lower() not in known_usernames:
                        new_hits.append(t)
                        known_usernames.add(t["username"].lower())
                        seen_ids.add(t["id"])
                discovered.extend(new_hits)
                print(f"✓ {len(new_hits)} bai lien quan")
                await asyncio.sleep(4)
        except Exception as e:
            print(f"✗ Loi tim kiem: {e}")

    print_results(kol_hits, discovered)
    save_seen_tweets(seen_ids)

    if kol_hits or discovered:
        xlsx_path, csv_path = exporter.export(
            kol_hits=kol_hits,
            discovered=discovered,
            keywords=keywords,
            mode=args.mode,
            since_hours=since_hours,
            min_views=min_views,
            output_dir=OUTPUT_DIR,
            output_name=args.output_name,
            csv_only=args.csv_only,
            slim=args.slim,
            append=args.append,
        )
        print_done(xlsx_path, csv_path, kol_hits, discovered)
    else:
        print("\nKhong co ket qua — khong tao file output.")


if __name__ == "__main__":
    asyncio.run(main())
