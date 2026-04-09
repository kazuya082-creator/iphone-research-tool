"""
Instagram Reels リサーチモジュール
instaloader を使用
※ レート制限あり。ログイン推奨
"""

import logging
import time

import config

logger = logging.getLogger(__name__)


def search_instagram_reels(username: str = "", password: str = "") -> list[dict]:
    """
    InstagramのハッシュタグからiPhone便利機能のReelsを取得

    Returns:
        list of dict
    """
    try:
        import instaloader
    except ImportError:
        logger.error("instaloader がインストールされていません。`pip install instaloader` を実行してください。")
        return []

    L = instaloader.Instaloader(
        download_videos=False,
        download_video_thumbnails=False,
        download_geotags=False,
        download_comments=False,
        save_metadata=False,
        quiet=True,
    )

    # ログイン（任意だが推奨）
    if username and password:
        try:
            L.login(username, password)
            logger.info(f"Instagram ログイン成功: {username}")
        except Exception as e:
            logger.warning(f"Instagram ログイン失敗: {e}。未ログインで続行します。")

    results = []
    seen_ids = set()

    for hashtag_name in config.SEARCH_HASHTAGS[:5]:  # レート制限のため上位5件
        logger.info(f"Instagram ハッシュタグ検索中: #{hashtag_name}")
        try:
            hashtag = instaloader.Hashtag.from_name(L.context, hashtag_name)
            count = 0

            for post in hashtag.get_posts():
                if count >= 30:
                    break

                post_id = post.shortcode
                if post_id in seen_ids:
                    continue
                seen_ids.add(post_id)

                # 動画投稿のみ
                if not post.is_video:
                    count += 1
                    continue

                views = post.video_view_count or 0
                duration = post.video_duration or 0

                if views >= config.MIN_VIEWS and duration >= config.MIN_DURATION_SECONDS:
                    results.append({
                        "platform": "Instagram Reels",
                        "title": (post.caption or "")[:100].replace("\n", " "),
                        "url": f"https://www.instagram.com/reel/{post_id}/",
                        "views": views,
                        "duration_sec": int(duration),
                        "duration_str": f"{int(duration) // 60}分{int(duration) % 60}秒",
                        "channel": f"@{post.owner_username}",
                        "published_at": post.date_local.strftime("%Y-%m-%d"),
                        "thumbnail": post.url,
                    })

                count += 1
                time.sleep(1)  # レート制限対策

        except Exception as e:
            logger.warning(f"Instagram ハッシュタグ {hashtag_name} の取得エラー: {e}")
            if "429" in str(e) or "rate" in str(e).lower():
                logger.warning("レート制限に達しました。しばらく待ってから再実行してください。")
                break
            time.sleep(5)

    logger.info(f"Instagram: {len(results)} 件の動画を取得")
    return results
