"""
iPhone便利機能 バイラル動画リサーチ - Webアプリ版
Streamlit を使用。Chrome で開いて使える。
"""

import csv
import io
import logging
import os
import sys
import time
from datetime import datetime

import streamlit as st

import design_system as ds

# ロガー設定
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# ページ設定
st.set_page_config(
    page_title="iPhone動画リサーチツール",
    page_icon="📱",
    layout="wide",
)

# ─────────────────────────────────────────────
# デザインシステム（デジタル庁 + Material Design 3）
# ─────────────────────────────────────────────
ds.inject(st)

# ─────────────────────────────────────────────
# ヘッダー
# ─────────────────────────────────────────────
st.markdown(
    ds.header(
        "iPhone便利機能 バイラル動画リサーチ",
        "YouTube Shorts / TikTok / Instagram Reels から、"
        "再生数と動画時間の条件に合う動画を横断検索します。",
    ),
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────
# サイドバー: API設定
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("設定")

    st.subheader("APIキー")

    # 環境変数から自動取得（Streamlit Cloud の Secrets に設定している場合）
    default_yt_key = os.environ.get("YOUTUBE_API_KEY", "")
    default_tiktok_session = os.environ.get("TIKTOK_SESSION_ID", "")
    default_ig_user = os.environ.get("INSTAGRAM_USERNAME", "")
    default_ig_pass = os.environ.get("INSTAGRAM_PASSWORD", "")

    youtube_api_key = st.text_input(
        "YouTube API Key",
        value=default_yt_key,
        type="password",
        help="Google Cloud Console で YouTube Data API v3 を有効化して取得",
    )

    tiktok_session_id = st.text_input(
        "TikTok Session ID（任意）",
        value=default_tiktok_session,
        type="password",
        help="TikTokにChrome でログイン → F12 → Application → Cookies → sessionid",
    )

    ig_username = st.text_input(
        "Instagram ユーザー名（任意）",
        value=default_ig_user,
    )

    ig_password = st.text_input(
        "Instagram パスワード（任意）",
        value=default_ig_pass,
        type="password",
    )

    st.divider()

    st.subheader("検索条件")

    min_views = st.number_input(
        "最低再生数",
        min_value=10_000,
        max_value=10_000_000,
        value=500_000,
        step=50_000,
        format="%d",
    )

    min_duration = st.slider(
        "最低動画時間（秒）",
        min_value=30,
        max_value=180,
        value=60,
        step=5,
        help="1分 = 60秒",
    )

    max_duration = st.slider(
        "最大動画時間（秒）",
        min_value=60,
        max_value=600,
        value=300,
        step=10,
    )

    days_back = st.slider(
        "何日前まで遡る",
        min_value=7,
        max_value=365,
        value=180,
        step=7,
    )

    st.divider()

    st.subheader("対象プラットフォーム")
    use_youtube = st.checkbox("YouTube Shorts", value=True)
    use_tiktok = st.checkbox("TikTok", value=True)
    use_instagram = st.checkbox("Instagram Reels", value=True)

    st.divider()

    st.subheader("検索キーワード")
    custom_keywords = st.text_area(
        "キーワード（1行1つ）",
        value="\n".join([
            "iPhone 便利機能",
            "iPhone 裏技",
            "iPhone 使い方",
            "iPhone 知らない機能",
            "iPhone tips",
            "iPhone tricks",
        ]),
        height=150,
    )

# ─────────────────────────────────────────────
# メイン: 実行ボタン
# ─────────────────────────────────────────────
col_run, _ = st.columns([1, 2])
if col_run.button("リサーチ開始", type="primary", use_container_width=True):
    if not youtube_api_key and use_youtube:
        st.error("YouTube API Keyが入力されていません。サイドバーで設定してください。")
        st.stop()

    # config を動的に更新
    import config
    config.YOUTUBE_API_KEY = youtube_api_key
    config.TIKTOK_SESSION_ID = tiktok_session_id
    config.INSTAGRAM_USERNAME = ig_username
    config.INSTAGRAM_PASSWORD = ig_password
    config.MIN_VIEWS = min_views
    config.MIN_DURATION_SECONDS = min_duration
    config.MAX_DURATION_SECONDS = max_duration
    config.YOUTUBE_PUBLISHED_AFTER_DAYS = days_back
    config.SEARCH_KEYWORDS = [k.strip() for k in custom_keywords.strip().splitlines() if k.strip()]

    platforms = []
    if use_youtube:
        platforms.append("youtube")
    if use_tiktok:
        platforms.append("tiktok")
    if use_instagram:
        platforms.append("instagram")

    if not platforms:
        st.warning("プラットフォームを1つ以上選択してください。")
        st.stop()

    all_results = []
    progress = st.progress(0, text="リサーチ中...")
    status = st.empty()

    total = len(platforms)

    # YouTube
    if "youtube" in platforms:
        status.info("YouTube Shorts を検索中...")
        from youtube_scraper import search_youtube_shorts
        youtube_results = search_youtube_shorts(youtube_api_key)
        all_results.extend(youtube_results)
        progress.progress(1 / total, text=f"YouTube: {len(youtube_results)} 件取得")
        time.sleep(0.3)

    # TikTok
    if "tiktok" in platforms:
        status.info("TikTok を検索中...")
        from tiktok_scraper import search_tiktok
        tiktok_results = search_tiktok(tiktok_session_id)
        all_results.extend(tiktok_results)
        progress.progress(
            platforms.index("tiktok") / total + 1 / total,
            text=f"TikTok: {len(tiktok_results)} 件取得"
        )
        time.sleep(0.3)

    # Instagram
    if "instagram" in platforms:
        status.info("Instagram Reels を検索中...")
        from instagram_scraper import search_instagram_reels
        instagram_results = search_instagram_reels(ig_username, ig_password)
        all_results.extend(instagram_results)
        progress.progress(1.0, text=f"Instagram: {len(instagram_results)} 件取得")
        time.sleep(0.3)

    progress.empty()
    status.empty()

    # 結果をセッションに保存
    all_results.sort(key=lambda x: x["views"], reverse=True)
    st.session_state["results"] = all_results
    st.session_state["search_time"] = datetime.now().strftime("%Y-%m-%d %H:%M")

# ─────────────────────────────────────────────
# 結果表示
# ─────────────────────────────────────────────
if "results" in st.session_state:
    results = st.session_state["results"]
    search_time = st.session_state.get("search_time", "")

    st.markdown(
        ds.section("検索結果", f"検索日時 {search_time}"),
        unsafe_allow_html=True,
    )

    if not results:
        st.warning("条件に合う動画が見つかりませんでした。検索条件を緩めてみてください。")
    else:
        # サマリー
        platform_counts = {}
        for r in results:
            platform_counts[r["platform"]] = platform_counts.get(r["platform"], 0) + 1

        st.markdown(
            ds.stat_tiles(len(results), platform_counts),
            unsafe_allow_html=True,
        )

        # 絞り込み（チップ）とCSVダウンロードを横並びに
        col_filter, col_csv = st.columns([3, 1])

        with col_filter:
            filter_platform = st.radio(
                "プラットフォームで絞り込み",
                options=["全て"] + list(platform_counts.keys()),
                horizontal=True,
                label_visibility="collapsed",
            )

        filtered = results if filter_platform == "全て" else [
            r for r in results if r["platform"] == filter_platform
        ]

        with col_csv:
            csv_buffer = io.StringIO()
            fieldnames = ["platform", "title", "url", "views", "duration_str",
                          "channel", "published_at"]
            writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames,
                                    extrasaction="ignore")
            writer.writeheader()
            writer.writerows(filtered)

            st.download_button(
                label="CSVでダウンロード",
                data=csv_buffer.getvalue().encode("utf-8-sig"),
                file_name=f"iphone_research_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # 結果カードのグリッド
        st.markdown(ds.result_grid(filtered), unsafe_allow_html=True)

# ─────────────────────────────────────────────
# フッター: APIキー取得ガイド
# ─────────────────────────────────────────────
with st.expander("YouTube API Key の取得方法"):
    st.markdown("""
1. [Google Cloud Console](https://console.cloud.google.com) にアクセス
2. 新しいプロジェクトを作成
3. 「APIとサービス」→「ライブラリ」→「YouTube Data API v3」を有効化
4. 「認証情報」→「APIキーを作成」
5. 作成されたAPIキーをコピーしてサイドバーに貼り付ける

**無料枠**: 1日10,000ユニット（通常のリサーチなら十分）
""")

with st.expander("TikTok Session ID の取得方法"):
    st.markdown("""
1. Chrome で [TikTok](https://www.tiktok.com) にログイン
2. F12 キーで開発者ツールを開く
3. 「Application」タブ → 「Cookies」→ `https://www.tiktok.com`
4. `sessionid` の Value をコピー
5. サイドバーに貼り付ける

※ 未入力でも動作しますが、取得できる件数が少なくなります
""")
