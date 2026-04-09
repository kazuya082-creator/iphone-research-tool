#!/bin/bash
# セットアップスクリプト

echo "=== iPhone便利機能リサーチツール セットアップ ==="

# Python仮想環境作成
python3 -m venv venv
source venv/bin/activate

# 依存パッケージインストール
pip install -r requirements.txt

# TikTokApi用ブラウザドライバー
python3 -m playwright install chromium

echo ""
echo "=== セットアップ完了 ==="
echo ""
echo "次のステップ:"
echo "1. config.py を開いて以下を設定してください:"
echo "   - YOUTUBE_API_KEY: Google Cloud Console で取得"
echo "   - TIKTOK_SESSION_ID: TikTokのブラウザCookieから取得 (任意)"
echo "   - INSTAGRAM_USERNAME/PASSWORD: Instagramアカウント (任意)"
echo ""
echo "2. 実行コマンド:"
echo "   source venv/bin/activate"
echo "   python main.py                          # 単発実行 (全プラットフォーム)"
echo "   python main.py --platforms youtube      # YouTubeのみ"
echo "   python main.py --schedule daily         # 毎日09:00に自動実行"
echo "   python main.py --schedule daily --schedule-time 08:00  # 時刻変更"
echo "   python main.py --schedule weekly        # 毎週月曜に自動実行"
echo "   python main.py --format json            # JSON形式で出力"
