"""
設定ファイル - 各プラットフォームの検索条件
"""

# 検索キーワード (iPhone便利機能関連)
SEARCH_KEYWORDS = [
    "iPhone 便利機能",
    "iPhone 裏技",
    "iPhone 使い方",
    "iPhone 知らない機能",
    "iPhone tips",
    "iPhone tricks",
    "iphone便利",
    "アイフォン便利",
]

# 検索ハッシュタグ
SEARCH_HASHTAGS = [
    "iphone便利機能",
    "iphone裏技",
    "iphoneの使い方",
    "iphone便利",
    "iphoneтрюки",
    "iphonehacks",
    "iphonetips",
    "iphonetricks",
]

# フィルター条件
MIN_VIEWS = 500_000          # 最低再生数 (50万回)
MIN_DURATION_SECONDS = 60    # 最低動画時間 (1分)
MAX_DURATION_SECONDS = 300   # 最大動画時間 (5分 - ショーツ想定)

# 取得件数
MAX_RESULTS_PER_KEYWORD = 50

# 出力設定
OUTPUT_DIR = "results"
OUTPUT_FORMAT = "csv"  # "csv" or "json"

# YouTube API設定
YOUTUBE_API_KEY = ""  # Google Cloud Console で取得
YOUTUBE_MAX_RESULTS = 50
YOUTUBE_PUBLISHED_AFTER_DAYS = 365  # 何日前まで遡るか

# TikTok設定
TIKTOK_SESSION_ID = ""  # TikTokのsessionid (Cookieから取得)

# Instagram設定
INSTAGRAM_USERNAME = ""  # Instagramユーザー名 (未ログインでも動作するが制限あり)
INSTAGRAM_PASSWORD = ""  # Instagramパスワード (オプション)
