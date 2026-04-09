"""
TikTok リサーチモジュール
TikTokApi (非公式) を使用
※ 動作にはTikTokのsessionidが必要な場合があります
"""

import asyncio
import logging

import config

logger = logging.getLogger(__name__)


async def _search_tiktok_async(session_id: str) -> list[dict]:
    """TikTok非同期検索"""
    try:
        from TikTokApi import TikTokApi
    except ImportError:
        logger.error("TikTokApi がインストールされていません。`pip install TikTokApi` を実行してください。")
        return []

    results = []
    ms_token = None  # 必要に応じてブラウザのCookieから取得

    try:
        async with TikTokApi() as api:
            if session_id:
                await api.create_sessions(
                    ms_tokens=[ms_token] if ms_token else None,
                    num_sessions=1,
                    sleep_after=3,
                    cookies=[{"name": "sessionid", "value": session_id}],
                )
            else:
                await api.create_sessions(num_sessions=1, sleep_after=3)

            seen_ids = set()

            # ハッシュタグ検索
            for hashtag_name in config.SEARCH_HASHTAGS:
                logger.info(f"TikTok ハッシュタグ検索中: #{hashtag_name}")
                try:
                    hashtag = api.hashtag(name=hashtag_name)
                    async for video in hashtag.videos(count=30):
                        video_id = video.id
                        if video_id in seen_ids:
                            continue
                        seen_ids.add(video_id)

                        stats = video.stats or {}
                        play_count = stats.get("playCount", 0) or 0
                        duration = video.as_dict.get("video", {}).get("duration", 0) or 0

                        if play_count >= config.MIN_VIEWS and duration >= config.MIN_DURATION_SECONDS:
                            author = video.author
                            results.append({
                                "platform": "TikTok",
                                "title": video.desc or "(タイトルなし)",
                                "url": f"https://www.tiktok.com/@{author.username}/video/{video_id}",
                                "views": play_count,
                                "duration_sec": duration,
                                "duration_str": f"{duration // 60}分{duration % 60}秒",
                                "channel": f"@{author.username}",
                                "published_at": str(video.create_time.date()) if video.create_time else "",
                                "thumbnail": video.as_dict.get("video", {}).get("cover", ""),
                            })
                except Exception as e:
                    logger.warning(f"TikTok ハッシュタグ {hashtag_name} の取得エラー: {e}")

    except Exception as e:
        logger.error(f"TikTok セッション作成エラー: {e}")
        logger.info("ヒント: TikTokのブラウザCookieから sessionid を取得して config.py に設定してください")

    logger.info(f"TikTok: {len(results)} 件の動画を取得")
    return results


def search_tiktok(session_id: str = "") -> list[dict]:
    """TikTok検索 (同期ラッパー)"""
    try:
        return asyncio.run(_search_tiktok_async(session_id))
    except Exception as e:
        logger.error(f"TikTok 検索エラー: {e}")
        return []
