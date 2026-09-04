# デザインシステムについて

このアプリのUIは、2つの公開デザインシステムを組み合わせて構成している。

| 領域 | 参照元 | 理由 |
|---|---|---|
| 色 / タイポグラフィ / フォーム / アクセシビリティ | [デジタル庁デザインシステム](https://design.digital.go.jp/) | 日本語UIの可読性・アクセシビリティ要件に沿っている |
| 影 / シェイプ / ステートレイヤー / モーション | [Material Design 3](https://m3.material.io/) | 操作フィードバックと階層表現がWebアプリに向く |

## 実装場所

- `design_system.py` … トークン定義（色・余白・角丸・影・フォント）とCSS注入、UIコンポーネント
- `.streamlit/config.toml` … Streamlit組み込みテーマ。`design_system.py` の `COLORS` と値を揃えること
- `app.py` … `ds.inject(st)` を1回呼び、`ds.header()` / `ds.section_title()` / `ds.result_card()` を使う

色を変えるときは `design_system.py` の `COLORS` と `.streamlit/config.toml` の2箇所だけを直す。

## 採用したルール

- **本文の行間 170%** … 日本語の可読性確保（デジタル庁の推奨値）
- **タップターゲット最小 44px** … ボタンの `min-height`
- **フォーカスリング** … `:focus-visible` に 2px のアウトライン＋2pxオフセット。キーボード操作でも現在位置が分かる
- **4pxグリッド** … 余白は `SPACING` の値のみを使う
- **エレベーション** … MD3のレベル1〜3。カードは通常レベル1、ホバーでレベル2
- **シェイプ** … ボタンはpill（MD3）、カード・入力欄は8〜12px
- **フォント** … Noto Sans JP（Google Fonts）。Streamlitのアイコンフォント（Material Symbols）は
  `[data-testid="stIconMaterial"]` で除外している。ここを外すとアイコンが `visibility` などの文字列で表示される

## 注意点

- 色の16進値は両デザインシステムの公開値をもとにしているが、この作業環境から
  design.digital.go.jp への通信が遮断されていて公式サイトと突き合わせられていない。
  厳密にブランド準拠させる場合は公式のカラートークンと照合して `COLORS` を更新すること。
- 検索結果のタイトル・チャンネル名は外部サイトから取得した値なので、
  `design_system.py` 側で必ず `html.escape()` してから埋め込んでいる。
  カードのHTMLを編集するときはエスケープを外さないこと。
- Streamlit内部のCSSクラス名（`st-emotion-cache-*`）は更新で変わるため使っていない。
  `data-testid` 属性のみを選択子にしている。
