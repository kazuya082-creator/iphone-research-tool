#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
iPhone 通常カメラ素材用ルックLUT (.cube) ジェネレータ

目的:
  Blackmagic Cam の Apple Log 2 素材に当てている完パケグレード
  （AppleLog2_to_Rec709 の後段 `eq` + `colorbalance`）と
  同じ「絵」を、iPhone 標準カメラアプリで撮った素材にも当てられるようにする。

入力の2系統:
  rec709 : SDR / Rec.709 タグの素材（HDRビデオOFF、または既に709化済み）
  hlg    : 標準カメラの HDR 素材（BT.2020 primaries + arib-std-b67）
           → LUT の中で HLG → 表示リニア → トーンマップ → Rec.709 まで畳み込む。
             ffmpeg 側に zscale/tonemap を書かなくても 1 本の lut3d で完結する。

ルック（--look）:
  neutral : ルック無し（トーンマップのみ。hlg 入力専用。rec709 では素通しになる）
  cine    : Log パイプラインの「②控えめシネマティック」と同一のグレード
            eq=contrast=1.05:saturation=0.92 →
            colorbalance=rs=-0.03:bs=0.05:rh=0.03:bh=-0.03
  match   : cine に加えて、標準カメラ特有の「濃い・締まりすぎ」を寝かせて
            Log グレード素材と同じカットに混ぜやすくした版
            （黒を持ち上げ／ハイライトを丸め／コントラスト・彩度をわずかに落とす）

`eq` と `colorbalance` は ffmpeg の実装（libavfilter/vf_eq.c, vf_colorbalance.c）を
そのまま数式で再現している。rec709 入力の cine LUT は verify_lut.py で
実チェーンとの差分を検証済み。

使い方:
  python3 make_lut.py --all                       # 既定の5本を luts/ に生成
  python3 make_lut.py --input hlg --look cine --size 65 -o out.cube
"""

import argparse
import os
import sys

import numpy as np

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

# BT.709 luma 係数
KR_709, KG_709, KB_709 = 0.2126, 0.7152, 0.0722
# BT.2020 luma 係数
KR_2020, KG_2020, KB_2020 = 0.2627, 0.6780, 0.0593

# HLG inverse OETF (ARIB STD-B67)
HLG_A = 0.17883277
HLG_B = 1.0 - 4.0 * HLG_A          # 0.28466892
HLG_C = 0.5 - HLG_A * np.log(4.0 * HLG_A)   # 0.55991073

# HLG の OOTF システムガンマ（peak 1000nit 基準）
HLG_SYSTEM_GAMMA = 1.2

# 表示リニア（拡散白 = 1.0 に正規化後）でハイライトを丸め始める点
HLG_TONEMAP_KNEE = 0.70

# BT.2020 linear -> BT.709 linear
M_2020_TO_709 = np.array([
    [1.660491, -0.587641, -0.072850],
    [-0.124550, 1.132900, -0.008349],
    [-0.018151, -0.100579, 1.118730],
], dtype=np.float64)


# ルック定義（数値はすべてここに集約。現場で振りたくなったらここを触る）
LOOKS = {
    "neutral": {
        "lift": 0.0,
        "contrast": 1.0,
        "saturation": 1.0,
        "shoulder": None,
        "colorbalance": None,
    },
    # Log パイプラインの「②控えめシネマティック」と同一
    "cine": {
        "lift": 0.0,
        "contrast": 1.05,
        "saturation": 0.92,
        "shoulder": None,
        "colorbalance": {
            "rs": -0.03, "gs": 0.0, "bs": 0.05,
            "rm": 0.0, "gm": 0.0, "bm": 0.0,
            "rh": 0.03, "gh": 0.0, "bh": -0.03,
        },
    },
    # cine + 標準カメラの絵を Log グレードに寄せる補正
    "match": {
        "lift": 0.012,          # 黒の持ち上げ（Log 由来の絵は黒が沈みきらない）
        "contrast": 0.99,       # 標準カメラは元々コントラストが強いので少し戻す
        "saturation": 0.90,     # 同上（cine の 0.92 よりさらに控えめ）
        "shoulder": (0.78, 0.55),  # (開始点, 強さ) ハイライトを丸めて白飛びの硬さを取る
        "colorbalance": {
            "rs": -0.03, "gs": 0.0, "bs": 0.05,
            "rm": 0.0, "gm": 0.0, "bm": 0.0,
            "rh": 0.03, "gh": 0.0, "bh": -0.03,
        },
    },
}


# ---------------------------------------------------------------------------
# 色変換ユーティリティ（すべて float64 / shape (N, 3)）
# ---------------------------------------------------------------------------

def rgb_to_ycbcr_limited(rgb, kr=KR_709, kg=KG_709, kb=KB_709):
    """フルレンジ RGB [0,1] -> 8bit リミテッドレンジ Y'CbCr を 0..1 に正規化した値。

    ffmpeg の `eq` は 8bit プレーンの生のコード値に対して動くので、
    LUT 側でも「コード値 / 255」の座標系に合わせる必要がある。
    """
    r, g, b = rgb[:, 0], rgb[:, 1], rgb[:, 2]
    y = kr * r + kg * g + kb * b
    cb = (b - y) / (2.0 * (1.0 - kb))
    cr = (r - y) / (2.0 * (1.0 - kr))
    yc = (16.0 + 219.0 * y) / 255.0
    cbc = (128.0 + 224.0 * cb) / 255.0
    crc = (128.0 + 224.0 * cr) / 255.0
    return np.stack([yc, cbc, crc], axis=-1)


def ycbcr_limited_to_rgb(ycc, kr=KR_709, kg=KG_709, kb=KB_709):
    """rgb_to_ycbcr_limited の逆変換。"""
    y = (ycc[:, 0] * 255.0 - 16.0) / 219.0
    cb = (ycc[:, 1] * 255.0 - 128.0) / 224.0
    cr = (ycc[:, 2] * 255.0 - 128.0) / 224.0
    r = y + 2.0 * (1.0 - kr) * cr
    b = y + 2.0 * (1.0 - kb) * cb
    g = (y - kr * r - kb * b) / kg
    return np.stack([r, g, b], axis=-1)


def hlg_inverse_oetf(e_prime):
    """HLG 信号値 [0,1] -> シーンリニア [0,1]（ARIB STD-B67）。"""
    e_prime = np.clip(e_prime, 0.0, 1.0)
    lo = (e_prime ** 2) / 3.0
    hi = (np.exp((np.clip(e_prime, 0.5, None) - HLG_C) / HLG_A) + HLG_B) / 12.0
    return np.where(e_prime <= 0.5, lo, hi)


def hlg_to_display_linear(rgb_hlg, system_gamma=HLG_SYSTEM_GAMMA):
    """HLG 符号化 RGB(BT.2020) -> 表示リニア（ピーク 1.0 正規化・BT.2020 原色）。

    OOTF: D = Ys^(gamma-1) * E   （Ys = シーンリニアの BT.2020 輝度）
    """
    e = hlg_inverse_oetf(rgb_hlg)
    ys = KR_2020 * e[:, 0] + KG_2020 * e[:, 1] + KB_2020 * e[:, 2]
    gain = np.power(np.maximum(ys, 1e-8), system_gamma - 1.0)
    return e * gain[:, None]


def hlg_diffuse_white_level(system_gamma=HLG_SYSTEM_GAMMA):
    """HLG の拡散白（信号 0.75）が表示リニアで占める割合。peak1000nit で ≈0.203。"""
    e = float(hlg_inverse_oetf(np.array([0.75])) [0])
    return float(e ** system_gamma)


def _shoulder_strength(knee, peak):
    """ショルダーの傾きが knee 点で 1 になる（＝折れ目が見えない）強さを解く。"""
    q = (peak - knee) / max(1.0 - knee, 1e-6)
    s = 0.5
    for _ in range(200):                      # s = tanh(q * s) の不動点反復
        s = float(np.tanh(q * s))
        if s <= 1e-6:
            return 1e-6
    return s


def tonemap_shoulder(rgb, peak, knee=HLG_TONEMAP_KNEE):
    """拡散白（=1.0）付近をそのまま残し、その上だけを 1.0 に丸め込むトーンマップ。

    Hable や Reinhard を peak で正規化すると中間調ごと暗くなり
    （拡散白が 62 IRE まで落ちる）、標準カメラの絵としては眠くなる。
    ここでは knee までリニアに素通しし、knee 以上を tanh で 1.0 に漸近させる。
    knee 点で傾き 1 に合わせてあるので折れ目は出ない。
    """
    rgb = np.maximum(rgb, 0.0)
    s = _shoulder_strength(knee, peak)
    span = 1.0 - knee
    denom = float(np.tanh(s * (peak - knee) / span))
    over = (rgb - knee) / span
    rolled = knee + span * np.tanh(s * over) / denom
    return np.where(rgb <= knee, rgb, np.minimum(rolled, 1.0))


def bt709_oetf(linear):
    """リニア -> BT.709 符号値。"""
    linear = np.clip(linear, 0.0, 1.0)
    lo = linear * 4.5
    hi = 1.099 * np.power(np.maximum(linear, 0.018), 0.45) - 0.099
    return np.where(linear < 0.018, lo, hi)


# ---------------------------------------------------------------------------
# ffmpeg フィルタの再現
# ---------------------------------------------------------------------------

def apply_eq(rgb, contrast=1.0, saturation=1.0, brightness=0.0):
    """ffmpeg `eq` フィルタ（libavfilter/vf_eq.c）の再現。

    eq は YUV プレーン上で動く:
      luma  : v = contrast * (v - 0.5) + 0.5 + brightness
      chroma: v = saturation * (v - 0.5) + 0.5
    ピボットが 128/255 ではなく 0.5 なのは ffmpeg の実装そのまま（意図的に合わせている）。
    """
    if contrast == 1.0 and saturation == 1.0 and brightness == 0.0:
        return rgb
    ycc = rgb_to_ycbcr_limited(rgb)
    y = contrast * (ycc[:, 0] - 0.5) + 0.5 + brightness
    cb = saturation * (ycc[:, 1] - 0.5) + 0.5
    cr = saturation * (ycc[:, 2] - 0.5) + 0.5
    # ffmpeg は 8bit LUT なのでここで 0..1（=0..255）にクリップされる
    ycc2 = np.clip(np.stack([y, cb, cr], axis=-1), 0.0, 1.0)
    return ycbcr_limited_to_rgb(ycc2)


def apply_colorbalance(rgb, cb):
    """ffmpeg `colorbalance` フィルタ（libavfilter/vf_colorbalance.c）の再現。

        l = max(r,g,b) + min(r,g,b)
        s *= clip((b - l) * a + 0.5) * scale
        m *= clip((l - b) * a + 0.5) * clip((1 - l - b) * a + 0.5) * scale
        h *= clip((l - 1 + b) * a + 0.5) * scale
        v  = clip(v + s + m + h)
      （a = 4, b = 0.333, scale = 0.7, pl=false）

    l は「明度の2倍」（max+min を 0.5 倍しない）。ffmpeg 6.1 の実測から確定した
    定義で、これを間違えるとシャドウ/ハイライトの効き始める明るさが丸ごとズレる。
    verify_lut.py が実チェーンとの一致を毎回チェックする。
    """
    if cb is None:
        return rgb
    a, bb, scale = 4.0, 0.333, 0.7
    l = rgb.max(axis=1) + rgb.min(axis=1)
    fs = np.clip((bb - l) * a + 0.5, 0.0, 1.0) * scale
    fm = (np.clip((l - bb) * a + 0.5, 0.0, 1.0)
          * np.clip((1.0 - l - bb) * a + 0.5, 0.0, 1.0) * scale)
    fh = np.clip((l - 1.0 + bb) * a + 0.5, 0.0, 1.0) * scale
    out = np.empty_like(rgb)
    for i, ch in enumerate("rgb"):
        s = cb.get(ch + "s", 0.0)
        m = cb.get(ch + "m", 0.0)
        h = cb.get(ch + "h", 0.0)
        out[:, i] = rgb[:, i] + s * fs + m * fm + h * fh
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------------------
# ルック
# ---------------------------------------------------------------------------

def apply_shoulder(rgb, start, strength):
    """start より上を丸めるハイライトショルダー（連続・単調）。"""
    if not start:
        return rgb
    x = rgb
    over = np.maximum(x - start, 0.0)
    span = max(1.0 - start, 1e-6)
    # 0..1 に正規化した超過分を soft knee で圧縮
    t = over / span
    compressed = (1.0 - np.exp(-strength * t * 2.0)) / (1.0 - np.exp(-strength * 2.0))
    return np.where(x <= start, x, start + compressed * span)


def apply_look(rgb, look):
    """Rec.709 符号値空間でルックを適用する。"""
    cfg = LOOKS[look]
    out = rgb
    if cfg["lift"]:
        out = out * (1.0 - cfg["lift"]) + cfg["lift"]
    if cfg["shoulder"]:
        out = apply_shoulder(out, cfg["shoulder"][0], cfg["shoulder"][1])
    out = apply_eq(out, contrast=cfg["contrast"], saturation=cfg["saturation"])
    out = apply_colorbalance(out, cfg["colorbalance"])
    return np.clip(out, 0.0, 1.0)


# ---------------------------------------------------------------------------
# LUT 生成
# ---------------------------------------------------------------------------

def transform(rgb, input_kind, look, peak_scale=None):
    """LUT 1点分の変換。rgb は (N,3) の入力符号値。"""
    if input_kind == "hlg":
        lin2020 = hlg_to_display_linear(rgb)
        white = hlg_diffuse_white_level()
        # 拡散白が SDR の 1.0 に来るよう正規化（ハイライトは 1.0 超えのまま残す）
        lin2020 = lin2020 / white
        peak = peak_scale if peak_scale else (1.0 / white)
        lin2020 = tonemap_shoulder(lin2020, peak)
        lin709 = lin2020 @ M_2020_TO_709.T
        lin709 = np.clip(lin709, 0.0, 1.0)
        rgb = bt709_oetf(lin709)
    return apply_look(rgb, look)


def build_lut(size, input_kind, look):
    axis = np.linspace(0.0, 1.0, size)
    # .cube は red が最速で回る
    b, g, r = np.meshgrid(axis, axis, axis, indexing="ij")
    grid = np.stack([r.ravel(), g.ravel(), b.ravel()], axis=-1)
    return transform(grid, input_kind, look)


def write_cube(path, data, size, title):
    with open(path, "w") as f:
        f.write('TITLE "%s"\n' % title)
        f.write("LUT_3D_SIZE %d\n" % size)
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        for row in data:
            f.write("%.6f %.6f %.6f\n" % (row[0], row[1], row[2]))


PRESETS = [
    # (input_kind, look, size, filename, title)
    ("rec709", "cine", 33, "iPhoneCam_Rec709_Cinematic_33.cube",
     "iPhone standard camera (Rec.709) - cinematic (matches Apple Log 2 pipeline)"),
    ("rec709", "match", 33, "iPhoneCam_Rec709_LogMatch_33.cube",
     "iPhone standard camera (Rec.709) - cinematic + Apple Log 2 look match"),
    ("hlg", "neutral", 33, "iPhoneCam_HLG_to_Rec709_Neutral_33.cube",
     "iPhone standard camera HDR (HLG/BT.2020) to Rec.709 - neutral"),
    ("hlg", "cine", 33, "iPhoneCam_HLG_to_Rec709_Cinematic_33.cube",
     "iPhone standard camera HDR (HLG/BT.2020) to Rec.709 - cinematic"),
    ("hlg", "match", 33, "iPhoneCam_HLG_to_Rec709_LogMatch_33.cube",
     "iPhone standard camera HDR (HLG/BT.2020) to Rec.709 - cinematic + Log look match"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--all", action="store_true", help="既定の5本を luts/ に生成する")
    ap.add_argument("--input", choices=["rec709", "hlg"], default="rec709")
    ap.add_argument("--look", choices=list(LOOKS), default="cine")
    ap.add_argument("--size", type=int, default=33, help="グリッドサイズ（33 / 65）")
    ap.add_argument("-o", "--out", help="出力 .cube パス")
    ap.add_argument("--outdir", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "luts"))
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    if args.all:
        for input_kind, look, size, name, title in PRESETS:
            data = build_lut(size, input_kind, look)
            path = os.path.join(args.outdir, name)
            write_cube(path, data, size, title)
            print("wrote %s (size=%d, input=%s, look=%s)" % (path, size, input_kind, look))
        return 0

    if not args.out:
        args.out = os.path.join(
            args.outdir,
            "iPhoneCam_%s_%s_%d.cube" % (args.input, args.look, args.size))
    data = build_lut(args.size, args.input, args.look)
    write_cube(args.out, data, args.size,
               "iPhone standard camera %s / %s" % (args.input, args.look))
    print("wrote %s (size=%d, input=%s, look=%s)" % (args.out, args.size, args.input, args.look))
    return 0


if __name__ == "__main__":
    sys.exit(main())
