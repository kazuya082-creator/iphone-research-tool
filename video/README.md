# video — Remotion リールテンプレート

Instagram Reels / TikTok / YouTube Shorts 用の縦動画（1080×1920, 30fps）を
コードから書き出すための Remotion プロジェクト。

構成は `kazuya-script-creator` スキルの台本フォーマットに合わせてある。

```
フック → 転換（機能名）→ まず → しかも → さらに → つまり → CTA
```

## 使い方

```bash
cd video
npm install

# プレビュー（ブラウザでタイムラインを触りながら調整できる）
npm start

# 書き出し → out/reel.mp4
npm run render
```

このコンテナのようにシステムのChromeが無い環境では、既存のChromiumを指定する。

```bash
npx remotion render Reel out/reel.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

## 別ネタのリールを作るとき

基本的に `src/script.ts` の `SCENES` だけ書き換えればいい。
台本のテキスト・各シーンの尺（フレーム数）・iPhone画面の種類をここで指定する。

| フィールド | 意味 |
|---|---|
| `frames` | そのシーンの長さ（30 = 1秒） |
| `lines` | 画面上部の見出し。1行 = 1センテンス |
| `caption` | 下部の焼き込み字幕（音を出さずに見る人向け） |
| `screen` | ステップシーンで表示するiPhone画面（`settings` / `actions` / `assigned`） |

## ファイル構成

| パス | 役割 |
|---|---|
| `src/script.ts` | 台本データ。**ふだん触るのはここだけ** |
| `src/layout.ts` `src/theme.ts` | 安全領域・色・基準となる縦位置 |
| `src/Reel.tsx` | シーンを順番に並べる本体 |
| `src/scenes/Scenes.tsx` | フック / タイトル / ステップ / つまり / CTA の見た目 |
| `src/components/Phone.tsx` | iPhoneのモック。設定画面のドリルダウンやタップ波紋 |
| `src/components/Text.tsx` | 見出し・バッジ・字幕 |
| `src/components/Chrome.tsx` | 背景・進捗バー・アカウント名チップ |
| `public/notosansjp.css` `public/fonts/` | Noto Sans JP（ローカル同梱。オフラインでも文字化けしない） |

## レイアウトの前提

Reels は上下がUIに隠れるので、`src/layout.ts` の基準線に沿って
おおむね y=230〜1560 の範囲に文字と画面を収めている。

## 実写素材を混ぜる場合

画面収録を使うときは `public/` に mp4 を置いて `<OffthreadVideo>` に差し替える。
BGM も同様に `<Audio>` で重ねられる（このサンプルは音声なし）。
