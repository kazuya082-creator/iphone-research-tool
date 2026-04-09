"""
iPhone便利機能 バイラル動画リサーチツール
対象: Instagram Reels / TikTok / YouTube Shorts
条件: 1分以上 / 再生数50万以上
"""

import argparse
import csv
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import schedule
import time

import config
from youtube_scraper import search_youtube_shorts
from tiktok_scraper import search_tiktok
from instagram_scraper import search_instagram_reels

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("research.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def run_research(platforms: list[str] | None = None) -> list[dict]:
    """
    全プラットフォームのリサーチを実行

    Args:
        platforms: 対象プラットフォーム。None の場合は全て実行
                   ["youtube", "tiktok", "instagram"] から選択

    Returns:
        フィルタ済みの動画リスト
    """
    if platforms is None:
        platforms = ["youtube", "tiktok", "instagram"]

    all_results = []

    if "youtube" in platforms:
        logger.info("=== YouTube Shorts リサーチ開始 ===")
        youtube_results = search_youtube_shorts(config.YOUTUBE_API_KEY)
        all_results.extend(youtube_results)
        logger.info(f"YouTube: {len(youtube_results)} 件")

    if "tiktok" in platforms:
        logger.info("=== TikTok リサーチ開始 ===")
        tiktok_results = search_tiktok(config.TIKTOK_SESSION_ID)
        all_results.extend(tiktok_results)
        logger.info(f"TikTok: {len(tiktok_results)} 件")

    if "instagram" in platforms:
        logger.info("=== Instagram Reels リサーチ開始 ===")
        instagram_results = search_instagram_reels(
            config.INSTAGRAM_USERNAME, config.INSTAGRAM_PASSWORD
        )
        all_results.extend(instagram_results)
        logger.info(f"Instagram: {len(instagram_results)} 件")

    # 再生数でソート（降順）
    all_results.sort(key=lambda x: x["views"], reverse=True)

    logger.info(f"=== 合計 {len(all_results)} 件取得 ===")
    return all_results


def save_results(results: list[dict], output_format: str = "csv") -> str:
    """結果をファイルに保存"""
    output_dir = Path(config.OUTPUT_DIR)
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    if output_format == "json":
        filepath = output_dir / f"research_{timestamp}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    else:
        filepath = output_dir / f"research_{timestamp}.csv"
        if results:
            fieldnames = ["platform", "title", "url", "views", "duration_str",
                          "channel", "published_at", "thumbnail"]
            with open(filepath, "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
                writer.writeheader()
                writer.writerows(results)

    logger.info(f"結果を保存しました: {filepath}")
    return str(filepath)


def print_summary(results: list[dict]) -> None:
    """コンソールにサマリーを表示"""
    if not results:
        print("\n条件に合う動画は見つかりませんでした。")
        return

    print(f"\n{'='*60}")
    print(f"リサーチ結果 - {len(results)} 件 (再生数50万以上, 1分以上)")
    print(f"{'='*60}")

    platform_counts = {}
    for r in results:
        platform_counts[r["platform"]] = platform_counts.get(r["platform"], 0) + 1

    for platform, count in platform_counts.items():
        print(f"  {platform}: {count} 件")

    print(f"\n--- TOP 10 ---")
    for i, r in enumerate(results[:10], 1):
        views_str = f"{r['views']:,}"
        print(f"{i:2}. [{r['platform']}] {r['title'][:40]}")
        print(f"    再生数: {views_str} | 時間: {r['duration_str']} | {r['channel']}")
        print(f"    URL: {r['url']}")
        print()


def job(platforms: list[str] | None = None) -> None:
    """スケジュール実行用ジョブ"""
    logger.info(f"定期リサーチ開始: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        results = run_research(platforms)
        print_summary(results)
        if results:
            save_results(results, config.OUTPUT_FORMAT)
    except Exception as e:
        logger.error(f"リサーチ中にエラーが発生しました: {e}", exc_info=True)


def main():
    parser = argparse.ArgumentParser(
        description="iPhone便利機能 バイラル動画リサーチツール"
    )
    parser.add_argument(
        "--platforms",
        nargs="+",
        choices=["youtube", "tiktok", "instagram"],
        default=None,
        help="対象プラットフォーム (デフォルト: 全て)",
    )
    parser.add_argument(
        "--schedule",
        choices=["hourly", "daily", "weekly"],
        default=None,
        help="定期実行の間隔",
    )
    parser.add_argument(
        "--schedule-time",
        default="09:00",
        help="daily/weekly の実行時刻 (例: 09:00)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json"],
        default="csv",
        help="出力フォーマット",
    )

    args = parser.parse_args()
    config.OUTPUT_FORMAT = args.format

    if args.schedule:
        logger.info(f"定期実行モード: {args.schedule} ({args.schedule_time})")

        if args.schedule == "hourly":
            schedule.every().hour.do(job, platforms=args.platforms)
        elif args.schedule == "daily":
            schedule.every().day.at(args.schedule_time).do(job, platforms=args.platforms)
        elif args.schedule == "weekly":
            schedule.every().monday.at(args.schedule_time).do(job, platforms=args.platforms)

        # 初回は即時実行
        job(args.platforms)

        logger.info(f"次回実行: {schedule.next_run()}")
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        # 単発実行
        results = run_research(args.platforms)
        print_summary(results)
        if results:
            save_results(results, config.OUTPUT_FORMAT)


if __name__ == "__main__":
    main()
