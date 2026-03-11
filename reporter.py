"""
reporter.py — In báo cáo tóm tắt ra terminal
"""

from pathlib import Path


def fmt_num(n: int) -> str:
    return f"{n:,}"


def print_results(kol_hits: list[dict], discovered: list[dict]):
    print("\n" + "━" * 50)
    print("  KẾT QUẢ")
    print("━" * 50)

    all_tweets = kol_hits + discovered
    if not all_tweets:
        print("  ℹ️  Không có bài đăng nào khớp tiêu chí")
    else:
        for t in all_tweets:
            tag = " (mới)" if t.get("source") == "discovered" else ""
            text = t["text"][:50].replace("\n", " ")
            views_str = fmt_num(t.get("views", 0))
            print(f"  @{t['username']}{tag:<6}  {views_str:>10} views   \"{text}...\"")

    print("━" * 50)


def print_done(xlsx_path: Path, csv_path: Path, kol_hits: list[dict], discovered: list[dict]):
    total = len(kol_hits) + len(discovered)
    total_views = sum(t.get("views", 0) for t in kol_hits + discovered)

    print(f"\n✅ Hoàn tất!")
    if xlsx_path:
        print(f"   📊 Excel : {xlsx_path}")
    print(f"   📄 CSV   : {csv_path}")
    print(f"   🔗 Tổng  : {total} bài viết | {fmt_num(total_views)} lượt xem tổng cộng")
