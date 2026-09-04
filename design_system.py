"""
デザインシステム定義

方針:
  - 色 / タイポグラフィ / フォーム / アクセシビリティ
        → デジタル庁デザインシステム (https://design.digital.go.jp/)
          日本語UIの可読性・アクセシビリティ要件に沿った土台として採用。
  - 影 / シェイプ / ステートレイヤー / モーション
        → Material Design 3 (https://m3.material.io/)
          操作フィードバックと階層表現のレイヤーとして採用。

このモジュールは Streamlit アプリ全体で使うデザイントークンと、
それをCSSカスタムプロパティとして注入する処理をまとめている。
色の変更はここ1箇所だけ直せば全体に反映される。
"""

import html

# ─────────────────────────────────────────────
# デザイントークン
# ─────────────────────────────────────────────
COLORS = {
    # プライマリ（デジタル庁のブルー系）
    "primary": "#0017C1",
    "primary-hover": "#001299",
    "primary-pressed": "#000C7A",
    "primary-container": "#EEF1FD",   # MD3 の tonal container 相当
    "on-primary": "#FFFFFF",
    "on-primary-container": "#000C7A",

    # ニュートラル
    "text": "#1A1A1C",
    "text-secondary": "#626264",
    "text-tertiary": "#949497",
    "border": "#D8D8DB",
    "border-strong": "#B4B4B7",
    "surface": "#FFFFFF",
    "surface-alt": "#F5F5F6",
    "surface-sunken": "#ECECEE",

    # セマンティック
    "error": "#EC0000",
    "warning": "#B26C00",
    "success": "#197A4B",

    # プラットフォームのブランド色
    "youtube": "#FF0000",
    "tiktok": "#161823",
    "instagram": "#C13584",
}

# 4pxグリッド
SPACING = {
    "1": "4px", "2": "8px", "3": "12px", "4": "16px",
    "5": "20px", "6": "24px", "8": "32px", "10": "40px",
}

# MD3 のシェイプスケール
RADIUS = {
    "sm": "4px", "md": "8px", "lg": "12px", "xl": "16px", "full": "999px",
}

# MD3 のエレベーション
ELEVATION = {
    "1": "0 1px 2px rgba(26,26,28,.08), 0 1px 3px 1px rgba(26,26,28,.06)",
    "2": "0 1px 2px rgba(26,26,28,.10), 0 2px 6px 2px rgba(26,26,28,.07)",
    "3": "0 4px 8px 3px rgba(26,26,28,.08), 0 1px 3px rgba(26,26,28,.10)",
}

# 日本語本文は行間170%（デジタル庁の推奨）
FONT_STACK = (
    '"Noto Sans JP", "Hiragino Sans", "Hiragino Kaku Gothic ProN", '
    'Meiryo, system-ui, -apple-system, sans-serif'
)


def _css_variables() -> str:
    """トークンをCSSカスタムプロパティ宣言に変換する。"""
    lines = []
    for name, value in COLORS.items():
        lines.append(f"--ds-color-{name}: {value};")
    for name, value in SPACING.items():
        lines.append(f"--ds-space-{name}: {value};")
    for name, value in RADIUS.items():
        lines.append(f"--ds-radius-{name}: {value};")
    for name, value in ELEVATION.items():
        lines.append(f"--ds-elevation-{name}: {value};")
    lines.append(f"--ds-font: {FONT_STACK};")
    return "\n        ".join(lines)


_STYLES = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;700&display=swap" rel="stylesheet">
<style>
    :root {
        __VARS__
    }

    /* ── 基本タイポグラフィ ────────────────────────── */
    html, body, [class*="st-"], button, input, textarea, select {
        font-family: var(--ds-font);
    }
    .stApp {
        background: var(--ds-color-surface);
        color: var(--ds-color-text);
    }
    /* Streamlit のアイコンはリガチャフォントなので上書きしない
       （上書きすると "visibility" などの文字列がそのまま表示される） */
    [data-testid="stIconMaterial"],
    [class*="material-symbols"],
    [class*="material-icons"] {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }

    /* 日本語本文の可読性：行間170% */
    .stMarkdown p, .stMarkdown li {
        line-height: 1.7;
        color: var(--ds-color-text);
    }

    /* ── アクセシビリティ：フォーカスリング ───────────── */
    *:focus-visible {
        outline: 2px solid var(--ds-color-primary);
        outline-offset: 2px;
        border-radius: var(--ds-radius-sm);
    }

    /* ── ヘッダー ──────────────────────────────── */
    .ds-header {
        border-bottom: 1px solid var(--ds-color-border);
        padding-bottom: var(--ds-space-4);
        margin-bottom: var(--ds-space-6);
    }
    .ds-header h1 {
        font-size: 32px;
        font-weight: 700;
        line-height: 1.4;
        letter-spacing: .02em;
        margin: 0 0 var(--ds-space-2) 0;
        color: var(--ds-color-text);
    }
    .ds-header p {
        font-size: 14px;
        line-height: 1.7;
        margin: 0;
        color: var(--ds-color-text-secondary);
    }

    /* ── セクション見出し ─────────────────────────── */
    .ds-section-title {
        font-size: 20px;
        font-weight: 700;
        line-height: 1.5;
        margin: var(--ds-space-8) 0 var(--ds-space-4) 0;
        padding-left: var(--ds-space-3);
        border-left: 4px solid var(--ds-color-primary);
        color: var(--ds-color-text);
    }

    /* ── ボタン（MD3 filled / ステートレイヤー付き）──── */
    .stButton > button,
    .stDownloadButton > button {
        font-family: var(--ds-font);
        font-weight: 700;
        font-size: 16px;
        min-height: 44px;                 /* タップターゲット最小44px */
        border-radius: var(--ds-radius-full);
        transition: background-color .2s cubic-bezier(.2,0,0,1),
                    box-shadow .2s cubic-bezier(.2,0,0,1);
    }
    .stButton > button[kind="primary"] {
        background: var(--ds-color-primary);
        color: var(--ds-color-on-primary);
        border: none;
        box-shadow: var(--ds-elevation-1);
    }
    .stButton > button[kind="primary"]:hover {
        background: var(--ds-color-primary-hover);
        box-shadow: var(--ds-elevation-2);
    }
    .stButton > button[kind="primary"]:active {
        background: var(--ds-color-primary-pressed);
        box-shadow: var(--ds-elevation-1);
    }
    .stDownloadButton > button {
        background: var(--ds-color-primary-container);
        color: var(--ds-color-on-primary-container);
        border: 1px solid transparent;
    }
    .stDownloadButton > button:hover {
        background: #E2E7FB;
        color: var(--ds-color-on-primary-container);
        border-color: transparent;
    }

    /* ── フォーム部品 ─────────────────────────────── */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    .stSelectbox div[data-baseweb="select"] > div {
        border-radius: var(--ds-radius-md);
        border-color: var(--ds-color-border-strong);
        font-size: 14px;
    }
    .stTextInput input:focus,
    .stNumberInput input:focus,
    .stTextArea textarea:focus {
        border-color: var(--ds-color-primary);
        box-shadow: 0 0 0 1px var(--ds-color-primary);
    }
    label, .stCheckbox label p {
        font-size: 14px !important;
        font-weight: 500;
        color: var(--ds-color-text) !important;
    }

    /* ── サイドバー ────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--ds-color-surface-alt);
        border-right: 1px solid var(--ds-color-border);
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 18px;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 14px;
        font-weight: 700;
        color: var(--ds-color-text-secondary);
        letter-spacing: .04em;
    }

    /* ── 指標カード ────────────────────────────── */
    div[data-testid="stMetric"] {
        background: var(--ds-color-surface);
        border: 1px solid var(--ds-color-border);
        border-radius: var(--ds-radius-lg);
        padding: var(--ds-space-4);
        box-shadow: var(--ds-elevation-1);
    }
    div[data-testid="stMetricLabel"] p {
        font-size: 13px;
        font-weight: 500;
        color: var(--ds-color-text-secondary);
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: var(--ds-color-primary);
    }

    /* ── 結果カード ────────────────────────────── */
    .ds-card {
        background: var(--ds-color-surface);
        border: 1px solid var(--ds-color-border);
        border-radius: var(--ds-radius-lg);
        padding: var(--ds-space-4);
        box-shadow: var(--ds-elevation-1);
        transition: box-shadow .2s cubic-bezier(.2,0,0,1);
    }
    .ds-card:hover {
        box-shadow: var(--ds-elevation-2);
    }
    .ds-card__title {
        font-size: 16px;
        font-weight: 700;
        line-height: 1.6;
        margin: var(--ds-space-2) 0;
        color: var(--ds-color-text);
    }
    .ds-card__meta {
        display: flex;
        flex-wrap: wrap;
        gap: var(--ds-space-1) var(--ds-space-4);
        font-size: 13px;
        line-height: 1.7;
        color: var(--ds-color-text-secondary);
        margin-bottom: var(--ds-space-2);
    }
    .ds-card__meta strong {
        color: var(--ds-color-text);
        font-weight: 700;
    }
    .ds-card__link {
        display: inline-flex;
        align-items: center;
        gap: var(--ds-space-1);
        font-size: 14px;
        font-weight: 500;
        color: var(--ds-color-primary);
        text-decoration: underline;
        text-underline-offset: 3px;
        min-height: 24px;
    }
    .ds-card__link:hover {
        color: var(--ds-color-primary-hover);
    }

    /* ── バッジ（MD3 chip）──────────────────────── */
    .ds-badge {
        display: inline-flex;
        align-items: center;
        height: 24px;
        padding: 0 var(--ds-space-3);
        border-radius: var(--ds-radius-full);
        font-size: 12px;
        font-weight: 700;
        letter-spacing: .02em;
        color: #FFFFFF;
    }
    .ds-badge--youtube   { background: var(--ds-color-youtube); }
    .ds-badge--tiktok    { background: var(--ds-color-tiktok); }
    .ds-badge--instagram { background: var(--ds-color-instagram); }

    /* ── エキスパンダー ──────────────────────────── */
    div[data-testid="stExpander"] details {
        border: 1px solid var(--ds-color-border);
        border-radius: var(--ds-radius-lg);
        background: var(--ds-color-surface);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 500;
        font-size: 14px;
    }

    /* ── 通知（info / warning / error）───────────── */
    div[data-testid="stAlert"] {
        border-radius: var(--ds-radius-md);
        border-left: 4px solid var(--ds-color-primary);
        font-size: 14px;
    }

    /* ── プログレスバー ─────────────────────────── */
    .stProgress > div > div > div > div {
        background: var(--ds-color-primary);
    }

    /* ── 区切り線 ──────────────────────────────── */
    hr {
        border-color: var(--ds-color-border);
    }
</style>
"""


def inject(st) -> None:
    """デザインシステムのCSSをページに注入する。ページ先頭で1回だけ呼ぶ。"""
    st.markdown(_STYLES.replace("__VARS__", _css_variables()), unsafe_allow_html=True)


# ─────────────────────────────────────────────
# コンポーネント（HTMLを返す。値は必ずエスケープする）
# ─────────────────────────────────────────────
def header(title: str, description: str) -> str:
    return (
        '<div class="ds-header">'
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(description)}</p>"
        "</div>"
    )


def section_title(text: str) -> str:
    return f'<div class="ds-section-title">{html.escape(text)}</div>'


def badge(platform: str) -> str:
    if "YouTube" in platform:
        variant = "youtube"
    elif "TikTok" in platform:
        variant = "tiktok"
    else:
        variant = "instagram"
    return f'<span class="ds-badge ds-badge--{variant}">{html.escape(platform)}</span>'


def result_card(platform: str, title: str, views: int, duration: str,
                channel: str, published_at: str, url: str) -> str:
    """検索結果1件分のカード。スクレイピング由来の値を含むので全てエスケープする。"""
    safe_url = html.escape(url, quote=True)
    return (
        '<div class="ds-card">'
        f"{badge(platform)}"
        f'<div class="ds-card__title">{html.escape(title)}</div>'
        '<div class="ds-card__meta">'
        f"<span>👁️ <strong>{views:,}回</strong></span>"
        f"<span>⏱️ {html.escape(duration)}</span>"
        f"<span>📺 {html.escape(channel)}</span>"
        f"<span>📅 {html.escape(str(published_at))}</span>"
        "</div>"
        f'<a class="ds-card__link" href="{safe_url}" target="_blank" '
        f'rel="noopener noreferrer">動画を開く ↗</a>'
        "</div>"
    )
