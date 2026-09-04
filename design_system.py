"""
デザインシステム定義

方針:
  - 色 / タイポグラフィ / フォーム / アクセシビリティ
        → デジタル庁デザインシステム (https://design.digital.go.jp/)
          日本語UIの可読性・アクセシビリティ要件に沿った土台として採用。
  - 影 / シェイプ / ステートレイヤー / モーション
        → Material Design 3 (https://m3.material.io/)
          カード・チップ・操作フィードバックのレイヤーとして採用。

このモジュールはデザイントークンと、それをCSSカスタムプロパティとして
注入する処理、UIコンポーネントをまとめている。
色を変えるときはこのファイルの COLORS と .streamlit/config.toml の2箇所を直す。
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
    "border": "#DCDCE0",
    "border-strong": "#B4B4B7",
    "surface": "#FFFFFF",
    "surface-alt": "#F7F7F8",
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
    "2": "0 2px 4px rgba(26,26,28,.10), 0 4px 10px 2px rgba(26,26,28,.08)",
    "3": "0 4px 8px 3px rgba(26,26,28,.09), 0 1px 3px rgba(26,26,28,.10)",
}

# 日本語本文は行間170%（デジタル庁の推奨）
FONT_STACK = (
    '"Noto Sans JP", "Hiragino Sans", "Hiragino Kaku Gothic ProN", '
    'Meiryo, system-ui, -apple-system, sans-serif'
)

# プラットフォーム名 → 表示用の短いラベルとバリアント
PLATFORMS = {
    "YouTube": ("YouTube", "youtube"),
    "TikTok": ("TikTok", "tiktok"),
    "Instagram": ("Reels", "instagram"),
}


def _variant(platform: str):
    for key, (label, variant) in PLATFORMS.items():
        if key in platform:
            return label, variant
    return platform, "instagram"


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
    /* Streamlit のアイコンはリガチャフォントなので上書きしない
       （上書きすると "visibility" などの文字列がそのまま表示される） */
    [data-testid="stIconMaterial"],
    [class*="material-symbols"],
    [class*="material-icons"] {
        font-family: "Material Symbols Rounded", "Material Icons" !important;
    }
    .stApp {
        background: var(--ds-color-surface);
        color: var(--ds-color-text);
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
        display: flex;
        align-items: center;
        gap: var(--ds-space-4);
        border-bottom: 1px solid var(--ds-color-border);
        padding-bottom: var(--ds-space-4);
        margin-bottom: var(--ds-space-6);
    }
    .ds-header__mark {
        flex: none;
        width: 44px;
        height: 44px;
        border-radius: var(--ds-radius-lg);
        background: var(--ds-color-primary);
        color: var(--ds-color-on-primary);
        display: grid;
        place-items: center;
        font-size: 22px;
        font-weight: 700;
    }
    .ds-header h1 {
        font-size: 26px;
        font-weight: 700;
        line-height: 1.4;
        letter-spacing: .01em;
        margin: 0;
        color: var(--ds-color-text);
    }
    .ds-header p {
        font-size: 13px;
        line-height: 1.6;
        margin: 2px 0 0 0;
        color: var(--ds-color-text-secondary);
    }

    /* ── セクション見出し ─────────────────────────── */
    .ds-section {
        display: flex;
        align-items: baseline;
        gap: var(--ds-space-3);
        margin: var(--ds-space-8) 0 var(--ds-space-4) 0;
    }
    .ds-section__title {
        font-size: 18px;
        font-weight: 700;
        line-height: 1.5;
        color: var(--ds-color-text);
    }
    .ds-section__note {
        font-size: 12px;
        color: var(--ds-color-text-tertiary);
    }

    /* ── 集計タイル ────────────────────────────── */
    .ds-stats {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        gap: var(--ds-space-3);
        margin-bottom: var(--ds-space-4);
    }
    .ds-stat {
        background: var(--ds-color-surface-alt);
        border-radius: var(--ds-radius-lg);
        padding: var(--ds-space-3) var(--ds-space-4);
    }
    .ds-stat__label {
        display: flex;
        align-items: center;
        gap: var(--ds-space-2);
        font-size: 12px;
        font-weight: 500;
        color: var(--ds-color-text-secondary);
        margin-bottom: 2px;
    }
    .ds-stat__dot {
        width: 8px;
        height: 8px;
        border-radius: var(--ds-radius-full);
        flex: none;
    }
    .ds-stat__dot--total     { background: var(--ds-color-primary); }
    .ds-stat__dot--youtube   { background: var(--ds-color-youtube); }
    .ds-stat__dot--tiktok    { background: var(--ds-color-tiktok); }
    .ds-stat__dot--instagram { background: var(--ds-color-instagram); }
    .ds-stat__value {
        font-size: 26px;
        font-weight: 700;
        line-height: 1.2;
        color: var(--ds-color-text);
        font-feature-settings: "tnum";
    }
    .ds-stat__unit {
        font-size: 12px;
        font-weight: 500;
        color: var(--ds-color-text-secondary);
        margin-left: 3px;
    }

    /* ── 動画カードのグリッド ───────────────────────── */
    .ds-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: var(--ds-space-4);
        margin-top: var(--ds-space-2);
    }
    .ds-vcard {
        display: flex;
        flex-direction: column;
        background: var(--ds-color-surface);
        border: 1px solid var(--ds-color-border);
        border-radius: var(--ds-radius-xl);
        overflow: hidden;
        text-decoration: none !important;
        color: inherit;
        transition: box-shadow .2s cubic-bezier(.2,0,0,1),
                    transform .2s cubic-bezier(.2,0,0,1),
                    border-color .2s cubic-bezier(.2,0,0,1);
    }
    .ds-vcard:hover {
        box-shadow: var(--ds-elevation-2);
        border-color: transparent;
        transform: translateY(-2px);
    }
    .ds-vcard__media {
        position: relative;
        aspect-ratio: 4 / 3;
        background: var(--ds-color-surface-sunken);
        overflow: hidden;
    }
    .ds-vcard__media img {
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
        transition: transform .3s cubic-bezier(.2,0,0,1);
    }
    .ds-vcard:hover .ds-vcard__media img {
        transform: scale(1.04);
    }
    .ds-vcard__chip {
        position: absolute;
        top: var(--ds-space-2);
        left: var(--ds-space-2);
        display: inline-flex;
        align-items: center;
        height: 22px;
        padding: 0 10px;
        border-radius: var(--ds-radius-full);
        font-size: 11px;
        font-weight: 700;
        letter-spacing: .02em;
        color: #FFFFFF;
    }
    .ds-vcard__chip--youtube   { background: var(--ds-color-youtube); }
    .ds-vcard__chip--tiktok    { background: var(--ds-color-tiktok); }
    .ds-vcard__chip--instagram { background: var(--ds-color-instagram); }
    .ds-vcard__dur {
        position: absolute;
        right: var(--ds-space-2);
        bottom: var(--ds-space-2);
        padding: 1px 6px;
        border-radius: var(--ds-radius-sm);
        background: rgba(26,26,28,.82);
        color: #FFFFFF;
        font-size: 11px;
        font-weight: 500;
        font-feature-settings: "tnum";
    }
    .ds-vcard__body {
        padding: var(--ds-space-3) var(--ds-space-4) var(--ds-space-4);
        display: flex;
        flex-direction: column;
        gap: var(--ds-space-2);
        flex: 1;
    }
    .ds-vcard__title {
        font-size: 14px;
        font-weight: 700;
        line-height: 1.6;
        margin: 0;
        color: var(--ds-color-text);
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
        overflow: hidden;
        min-height: calc(1.6em * 2);      /* 2行分を確保してカード間の位置を揃える */
    }
    .ds-vcard__views {
        margin: auto 0 0 0;
        font-size: 20px;
        font-weight: 700;
        line-height: 1.2;
        color: var(--ds-color-primary);
        font-feature-settings: "tnum";
    }
    .ds-vcard__views span {
        font-size: 11px;
        font-weight: 500;
        color: var(--ds-color-text-secondary);
        margin-left: 3px;
    }
    .ds-vcard__sub {
        margin: 0;
        font-size: 11px;
        line-height: 1.5;
        color: var(--ds-color-text-tertiary);
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* ── ボタン（MD3 filled / ステートレイヤー付き）──── */
    .stButton > button,
    .stDownloadButton > button {
        font-family: var(--ds-font);
        font-weight: 700;
        font-size: 15px;
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
        background: var(--ds-color-surface);
        color: var(--ds-color-primary);
        border: 1px solid var(--ds-color-border-strong);
        font-size: 13px;
        min-height: 38px;
    }
    .stDownloadButton > button:hover {
        background: var(--ds-color-primary-container);
        color: var(--ds-color-on-primary-container);
        border-color: transparent;
    }

    /* ── 絞り込み（MD3 segmented button 風のラジオ）───── */
    div[data-testid="stRadio"] > label { display: none; }
    div[data-testid="stRadio"] div[role="radiogroup"] {
        flex-direction: row;
        flex-wrap: wrap;
        gap: var(--ds-space-2);
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        background: var(--ds-color-surface);
        border: 1px solid var(--ds-color-border-strong);
        border-radius: var(--ds-radius-full);
        padding: 6px 14px;
        margin: 0;
        min-height: 34px;
        align-items: center;
        transition: background-color .15s, border-color .15s;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background: var(--ds-color-surface-alt);
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) {
        background: var(--ds-color-primary-container);
        border-color: var(--ds-color-primary);
    }
    /* ラジオの丸を消してチップに見せる（構造は label > div > div > div:first-child）*/
    div[data-testid="stRadio"] div[role="radiogroup"] > label > div > div > div:first-child {
        display: none;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        cursor: pointer;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label p {
        font-size: 13px !important;
        font-weight: 500;
        color: var(--ds-color-text) !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:has(input:checked) p {
        color: var(--ds-color-on-primary-container) !important;
        font-weight: 700;
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
        font-size: 13px !important;
        font-weight: 500;
        color: var(--ds-color-text) !important;
    }

    /* ── サイドバー ────────────────────────────── */
    section[data-testid="stSidebar"] {
        background: var(--ds-color-surface-alt);
        border-right: 1px solid var(--ds-color-border);
    }
    section[data-testid="stSidebar"] h2 {
        font-size: 16px;
        font-weight: 700;
    }
    section[data-testid="stSidebar"] h3 {
        font-size: 12px;
        font-weight: 700;
        color: var(--ds-color-text-secondary);
        letter-spacing: .06em;
    }

    /* ── エキスパンダー ──────────────────────────── */
    div[data-testid="stExpander"] details {
        border: 1px solid var(--ds-color-border);
        border-radius: var(--ds-radius-lg);
        background: var(--ds-color-surface);
    }
    div[data-testid="stExpander"] summary {
        font-weight: 500;
        font-size: 13px;
    }

    /* ── 通知（info / warning / error）───────────── */
    div[data-testid="stAlert"] {
        border-radius: var(--ds-radius-md);
        border-left: 4px solid var(--ds-color-primary);
        font-size: 13px;
    }

    /* ── プログレスバー ─────────────────────────── */
    .stProgress > div > div > div > div {
        background: var(--ds-color-primary);
    }

    hr { border-color: var(--ds-color-border); }
</style>
"""


def inject(st) -> None:
    """デザインシステムのCSSをページに注入する。ページ先頭で1回だけ呼ぶ。"""
    st.markdown(_STYLES.replace("__VARS__", _css_variables()), unsafe_allow_html=True)


def format_views(views: int) -> str:
    """再生数を日本語の桁で読みやすくする。1,234,567 → 123.5万"""
    if views >= 100_000_000:
        return f"{views / 100_000_000:.1f}".rstrip("0").rstrip(".") + "億"
    if views >= 10_000:
        return f"{views / 10_000:.1f}".rstrip("0").rstrip(".") + "万"
    return f"{views:,}"


# ─────────────────────────────────────────────
# コンポーネント（HTMLを返す。外部由来の値は必ずエスケープする）
# ─────────────────────────────────────────────
def header(title: str, description: str, mark: str = "▶") -> str:
    return (
        '<div class="ds-header">'
        f'<div class="ds-header__mark">{html.escape(mark)}</div>'
        "<div>"
        f"<h1>{html.escape(title)}</h1>"
        f"<p>{html.escape(description)}</p>"
        "</div>"
        "</div>"
    )


def section(title: str, note: str = "") -> str:
    note_html = f'<span class="ds-section__note">{html.escape(note)}</span>' if note else ""
    return (
        '<div class="ds-section">'
        f'<span class="ds-section__title">{html.escape(title)}</span>'
        f"{note_html}</div>"
    )


def stat_tiles(total: int, platform_counts: dict) -> str:
    """件数の集計タイル。プラットフォームごとに色ドットを付ける。"""
    tiles = [("total", "合計", total, "件")]
    for name in ("YouTube Shorts", "TikTok", "Instagram Reels"):
        _, variant = _variant(name)
        tiles.append((variant, name, platform_counts.get(name, 0), "件"))

    cells = []
    for variant, label, value, unit in tiles:
        cells.append(
            '<div class="ds-stat">'
            f'<div class="ds-stat__label">'
            f'<span class="ds-stat__dot ds-stat__dot--{variant}"></span>{html.escape(label)}</div>'
            f'<div><span class="ds-stat__value">{value:,}</span>'
            f'<span class="ds-stat__unit">{unit}</span></div>'
            "</div>"
        )
    return f'<div class="ds-stats">{"".join(cells)}</div>'


def _video_card(r: dict) -> str:
    label, variant = _variant(r["platform"])
    url = html.escape(str(r["url"]), quote=True)
    title = html.escape(str(r["title"]))
    thumb = r.get("thumbnail")

    if thumb:
        media = f'<img src="{html.escape(str(thumb), quote=True)}" alt="" loading="lazy">'
    else:
        media = ""

    return (
        f'<a class="ds-vcard" href="{url}" target="_blank" rel="noopener noreferrer" '
        f'title="{title}">'
        f'<div class="ds-vcard__media">{media}'
        f'<span class="ds-vcard__chip ds-vcard__chip--{variant}">{html.escape(label)}</span>'
        f'<span class="ds-vcard__dur">{html.escape(str(r["duration_str"]))}</span>'
        "</div>"
        '<div class="ds-vcard__body">'
        f'<p class="ds-vcard__title">{title}</p>'
        f'<p class="ds-vcard__views">{format_views(r["views"])}<span>回再生</span></p>'
        f'<p class="ds-vcard__sub">{html.escape(str(r["channel"]))}'
        f' ・ {html.escape(str(r["published_at"]))}</p>'
        "</div></a>"
    )


def result_grid(results: list) -> str:
    """検索結果をカードのグリッドとして1つのHTMLにまとめて返す。"""
    return f'<div class="ds-grid">{"".join(_video_card(r) for r in results)}</div>'
