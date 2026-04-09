"""
YouTube Shorts リサーチモジュール
YouTube Data API v3 を使用
"""

import os
import re
import logging
from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import config

logger = logging.getLogger(__name__)


def parse_iso8601_duration(duration: str) -> int:
    """ISO 8601 duration (PT1M30S) を秒に変換"""
    pattern = r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?"
    match = re.match(pattern, duration)
    if not match:
        return 0
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    return hours * 3600 + minutes * 60 + seconds


def search_youtube_shorts(api_key: str) -> list[dict]:
    """
    YouTube Shortsを検索してiPhone便利機能動画を取得

    Returns:
        list of dict with keys: platform, title, url, views, duration_sec,
                                channel, published_at, thumbnail
    """
    if not api_key:
        logger.warning("YouTube API Key が設定されていません。config.py の YOUTUBE_API_KEY を設定してください。")
        return []

    youtube = build("youtube", "v3", developerKey=api_key)
    results = []
    seen_video_ids = set()

    published_after = (
        datetime.now(timezone.utc) - timedelta(days=config.YOUTUBE_PUBLISHED_AFTER_DAYS)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")

    for keyword in config.SEARCH_KEYWORDS:
        # Shortsはハッシュタグ #shorts を付けて検索
        query = f"{keyword} #shorts"
        logger.info(f"YouTube 検索中: {query}")

        try:
            search_response = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=config.YOUTUBE_MAX_RESULTS,
                publishedAfter=published_after,
                relevanceLanguage="ja",
                order="viewCount",
            ).execute()

            video_ids = [
                item["id"]["videoId"]
                for item in search_response.get("items", [])
                if item["id"]["videoId"] not in seen_video_ids
            ]

            if not video_ids:
                continue

            seen_video_ids.update(video_ids)

            # 動画の詳細情報（再生数・時間）を取得
            videos_response = youtube.videos().list(
                part="contentDetails,statistics,snippet",
                id=",".join(video_ids),
            ).execute()

            for item in videos_response.get("items", []):
                duration_sec = parse_iso8601_duration(
                    item["contentDetails"]["duration"]
                )
                views = int(item["statistics"].get("viewCount", 0))
                video_id = item["id"]

                if (
                    duration_sec >= config.MIN_DURATION_SECONDS
                    and duration_sec <= config.MAX_DURATION_SECONDS
                    and views >= config.MIN_VIEWS
                ):
                    results.append({
                        "platform": "YouTube Shorts",
                        "title": item["snippet"]["title"],
                        "url": f"https://www.youtube.com/shorts/{video_id}",
                        "views": views,
                        "duration_sec": duration_sec,
                        "duration_str": f"{duration_sec // 60}分{duration_sec % 60}秒",
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"][:10],
                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    })

        except HttpError as e:
            logger.error(f"YouTube API エラー ({keyword}): {e}")
            if "quotaExceeded" in str(e):
                logger.error("YouTube API クォータを超えました。明日以降に再実行してください。")
                break

    # ハッシュタグ検索も追加
    for hashtag in config.SEARCH_HASHTAGS[:3]:  # API節約のため上位3件のみ
        query = f"#{hashtag} #shorts"
        logger.info(f"YouTube ハッシュタグ検索中: {query}")

        try:
            search_response = youtube.search().list(
                q=query,
                part="id,snippet",
                type="video",
                maxResults=20,
                publishedAfter=published_after,
                order="viewCount",
            ).execute()

            video_ids = [
                item["id"]["videoId"]
                for item in search_response.get("items", [])
                if item["id"]["videoId"] not in seen_video_ids
            ]

            if not video_ids:
                continue

            seen_video_ids.update(video_ids)

            videos_response = youtube.videos().list(
                part="contentDetails,statistics,snippet",
                id=",".join(video_ids),
            ).execute()

            for item in videos_response.get("items", []):
                duration_sec = parse_iso8601_duration(
                    item["contentDetails"]["duration"]
                )
                views = int(item["statistics"].get("viewCount", 0))
                video_id = item["id"]

                if (
                    duration_sec >= config.MIN_DURATION_SECONDS
                    and duration_sec <= config.MAX_DURATION_SECONDS
                    and views >= config.MIN_VIEWS
                ):
                    results.append({
                        "platform": "YouTube Shorts",
                        "title": item["snippet"]["title"],
                        "url": f"https://www.youtube.com/shorts/{video_id}",
                        "views": views,
                        "duration_sec": duration_sec,
                        "duration_str": f"{duration_sec // 60}分{duration_sec % 60}秒",
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"][:10],
                        "thumbnail": item["snippet"]["thumbnails"].get("high", {}).get("url", ""),
                    })

        except HttpError as e:
            logger.error(f"YouTube API エラー ({hashtag}): {e}")

    logger.info(f"YouTube: {len(results)} 件の動画を取得")
    return results
