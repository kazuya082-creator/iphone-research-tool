#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成した .cube が「本当に同じ絵になるか」を数値で検証する。

1) rec709 / cine LUT
   Log パイプラインで使っている実チェーン
     eq=contrast=1.05:saturation=0.92,colorbalance=rs=-0.03:bs=0.05:rh=0.03:bh=-0.03
   を ffmpeg で実行した結果と、lut3d で LUT を当てた結果を
   密なカラースイープ（32^3 色）で比較し、8bit レベルでの誤差を出す。

2) hlg -> rec709 LUT
   グレー階調の単調性、拡散白（HLG 0.75）の着地点、
   ffmpeg の zscale+tonemap 経路との傾向差をチェックする。

使い方: python3 verify_lut.py
"""

import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

HERE = os.path.dirname(os.path.abspath(__file__))
LUTS = os.path.join(HERE, "luts")

CHAIN = ("eq=contrast=1.05:saturation=0.92,"
         "colorbalance=rs=-0.03:bs=0.05:rh=0.03:bh=-0.03")

W, H = 256, 128          # 32^3 = 32768 色をちょうど収める


def run(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode("utf-8", "replace")[-2000:])
        raise SystemExit("ffmpeg failed: %s" % " ".join(cmd[:6]))
    return p.stdout


def sweep_rgb():
    """32^3 の RGB スイープを (H, W, 3) の uint8 画像として返す。"""
    v = np.linspace(0, 255, 32).round().astype(np.uint8)
    r, g, b = np.meshgrid(v, v, v, indexing="ij")
    img = np.stack([r.ravel(), g.ravel(), b.ravel()], axis=-1)
    return img.reshape(H, W, 3)


def make_source(tmp):
    """bt709 / limited / yuv444p のロスレス素材を作る（実素材と同じ経路を通すため）。"""
    raw = os.path.join(tmp, "src.raw")
    src = os.path.join(tmp, "src.mkv")
    sweep_rgb().tofile(raw)
    # scale=out_color_matrix=bt709 を明示しないと swscale が bt601 で YUV 化してしまい、
    # デコード側（bt709 タグ）と食い違って素材自体が壊れる（実素材では起きない状況）。
    run(["ffmpeg", "-v", "error", "-y",
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", "%dx%d" % (W, H), "-i", raw,
         "-vf", "scale=out_color_matrix=bt709:out_range=tv",
         "-c:v", "ffv1", "-pix_fmt", "yuv444p",
         "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
         "-color_range", "tv", src])
    return src


def render(src, vf, tmp, name):
    out = os.path.join(tmp, name)
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", vf,
         "-pix_fmt", "rgb24", "-f", "rawvideo", out])
    return np.fromfile(out, dtype=np.uint8).reshape(H, W, 3).astype(np.int16)


def ffmpeg_eq_luts(tmp):
    """ffmpeg の `eq` が内部で作る 256 エントリの LUT を実測して取り出す。"""
    src = os.path.join(tmp, "eqprobe.yuv")
    ramp = np.arange(256, dtype=np.uint8)[None, :].repeat(4, 0)
    flat = np.full((4, 256), 128, np.uint8)
    out = {}
    for plane, name in ((0, "y"), (1, "c")):
        planes = [ramp if plane == 0 else flat, ramp if plane == 1 else flat, flat]
        with open(src, "wb") as f:
            for pl in planes:
                f.write(pl.tobytes())
        dst = os.path.join(tmp, "eqprobe_out.yuv")
        run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv444p",
             "-s", "256x4", "-i", src, "-vf", CHAIN.split(",")[0],
             "-pix_fmt", "yuv444p", "-f", "rawvideo", dst])
        d = np.fromfile(dst, dtype=np.uint8)
        out[name] = d[plane * 1024:(plane + 1) * 1024].reshape(4, 256)[0].astype(np.float64)
    return out


def quantized_model(rgb, tmp):
    """LUT と同じ変換を、eq だけ ffmpeg 実測テーブルに置き換えて計算する。"""
    import make_lut as M
    tables = ffmpeg_eq_luts(tmp)
    ycc = M.rgb_to_ycbcr_limited(rgb)
    idx = np.clip(np.round(ycc * 255.0), 0, 255).astype(int)
    y = tables["y"][idx[:, 0]] / 255.0
    cb = tables["c"][idx[:, 1]] / 255.0
    cr = tables["c"][idx[:, 2]] / 255.0
    out = M.ycbcr_limited_to_rgb(np.stack([y, cb, cr], axis=-1))
    out = np.clip(out, 0.0, 1.0)
    return M.apply_colorbalance(out, M.LOOKS["cine"]["colorbalance"])


def verify_rec709_cine(tmp):
    print("=" * 72)
    print("1) rec709 / cine : 実フィルタチェーン vs lut3d")
    print("=" * 72)
    src = make_source(tmp)
    cube = os.path.join(LUTS, "iPhoneCam_Rec709_Cinematic_33.cube")

    ref = render(src, CHAIN, tmp, "ref.raw")
    lut = render(src, "lut3d=%s" % cube, tmp, "lut.raw")
    base = render(src, "null", tmp, "base.raw")

    src_rgb = sweep_rgb().reshape(-1, 3).astype(np.int16)
    diff = np.abs(ref - lut)
    grade = np.abs(ref - base)
    bias = (lut - ref).reshape(-1, 3).mean(axis=0)
    resid = np.abs((lut - ref).reshape(-1, 3) - bias)

    print("  比較色数              : %d" % (W * H))
    print("  素材の往復誤差        : 平均 %.2f レベル（0 に近いほどテストが健全）"
          % np.abs(base.reshape(-1, 3) - src_rgb).mean())
    print("  グレード量(参考)      : 平均 %.2f / 最大 %d レベル（無加工 vs グレード後）"
          % (grade.mean(), grade.max()))
    print("  LUT との差            : 平均 %.3f / 最大 %d レベル"
          % (diff.mean(), diff.max()))
    print("  うち一定バイアス      : R%+.2f G%+.2f B%+.2f レベル" % tuple(bias))
    print("    ※ffmpeg の `eq` は 8bit LUT を切り捨てで作るため常に約1レベル暗くなる。")
    print("      LUT 側は連続式なのでこの分だけ差が出る（10bit 出力ではむしろ LUT 側が正しい）。")
    print("  バイアス除去後の残差  : 平均 %.3f / 最大 %.1f レベル ← グレードの形の一致度"
          % (resid.mean(), resid.max()))
    print("  残差 <= 1 レベル      : %.2f%%" % (100.0 * (resid <= 1).mean()))

    # バイアスの出どころを実証する: ffmpeg から eq の 8bit LUT を実測し、
    # 同じ量子化をモデルに入れたうえで実チェーンと比べ直す。
    quant = quantized_model(base.reshape(-1, 3) / 255.0, tmp) * 255.0
    qd = np.abs(quant - ref.reshape(-1, 3))
    print("  参考: eq の 8bit LUT を ffmpeg から実測してモデルに入れた場合")
    print("        実チェーンとの差  : 平均 %.3f / 最大 %.1f レベル"
          % (qd.mean(), qd.max()))
    print("        → ここが 0 に落ちるなら、上のバイアスは全て eq の量子化由来。")

    ok = (resid.mean() < 1.0 and resid.max() <= 10
          and np.abs(bias).max() < 3.0 and qd.mean() < 0.6)
    print("  判定                  : %s"
          % ("OK（実チェーンと同じグレードとみなせる）" if ok else "要調査"))
    return ok


def cube_apply(cube_path, rgb):
    """.cube を読み、三重線形補間で (N,3) の入力に適用する（検算用）。"""
    size = None
    rows = []
    with open(cube_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("LUT_3D_SIZE"):
                size = int(line.split()[1])
            elif line[0].isdigit() or line[0] == "-":
                rows.append([float(x) for x in line.split()])
    data = np.array(rows).reshape(size, size, size, 3)   # [b][g][r]
    pos = np.clip(rgb, 0, 1) * (size - 1)
    i0 = np.floor(pos).astype(int)
    i1 = np.minimum(i0 + 1, size - 1)
    f = pos - i0
    out = np.zeros((rgb.shape[0], 3))
    for db in (0, 1):
        for dg in (0, 1):
            for dr in (0, 1):
                w = ((f[:, 2] if db else 1 - f[:, 2])
                     * (f[:, 1] if dg else 1 - f[:, 1])
                     * (f[:, 0] if dr else 1 - f[:, 0]))
                idx = (i1[:, 2] if db else i0[:, 2],
                       i1[:, 1] if dg else i0[:, 1],
                       i1[:, 0] if dr else i0[:, 0])
                out += w[:, None] * data[idx]
    return out


def verify_hlg(tmp):
    print()
    print("=" * 72)
    print("2) hlg -> rec709 : 階調とホワイトポイントの健全性")
    print("=" * 72)
    neutral = os.path.join(LUTS, "iPhoneCam_HLG_to_Rec709_Neutral_33.cube")

    ramp = np.linspace(0, 1, 256)
    gray = np.stack([ramp, ramp, ramp], axis=-1)
    out = cube_apply(neutral, gray)

    lum = out.mean(axis=1)
    mono = bool(np.all(np.diff(lum) >= -1e-6))
    neutral_err = float(np.abs(out - lum[:, None]).max())
    white = float(cube_apply(neutral, np.array([[0.75, 0.75, 0.75]]))[0].mean())
    peak = float(lum[-1])
    mid = float(cube_apply(neutral, np.array([[0.5, 0.5, 0.5]]))[0].mean())

    print("  グレー階調の単調性        : %s" % ("OK" if mono else "NG"))
    print("  グレーのニュートラル維持  : 最大ずれ %.4f (0 に近いほど良い)" % neutral_err)
    print("  HLG 拡散白 0.75 -> 709    : %.3f  (%.1f IRE / 目安 90-100)" % (white, white * 100))
    print("  HLG ピーク 1.0  -> 709    : %.3f  (白飛びせず頭が残っているか)" % peak)
    print("  HLG 0.5         -> 709    : %.3f" % mid)

    # ffmpeg の zscale+tonemap 経路との傾向比較（同じ絵にはならないが方向が合っているか）
    raw = os.path.join(tmp, "hlg.raw")
    grayimg = np.repeat((ramp * 255).round().astype(np.uint8)[None, :, None], 3, axis=2)
    grayimg = np.repeat(grayimg, 8, axis=0)
    grayimg.tofile(raw)
    src = os.path.join(tmp, "hlg.mkv")
    run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", "%dx%d" % (256, 8), "-i", raw, "-c:v", "ffv1", "-pix_fmt", "yuv444p10le",
         "-color_primaries", "bt2020", "-color_trc", "arib-std-b67",
         "-colorspace", "bt2020nc", "-color_range", "tv", src])
    zs = ("zscale=t=linear:npl=100,format=gbrpf32le,"
          "tonemap=hable:desat=0,zscale=p=bt709:t=bt709:m=bt709:r=tv")
    out2 = os.path.join(tmp, "hlg_zs.raw")
    try:
        run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf", zs,
             "-pix_fmt", "rgb24", "-f", "rawvideo", out2])
        ref = np.fromfile(out2, dtype=np.uint8).reshape(8, 256, 3)[0].mean(axis=1) / 255.0
        d = np.abs(ref - lum)
        print("  zscale+tonemap 経路との差 : 平均 %.3f / 最大 %.3f (0-1 スケール)"
              % (d.mean(), d.max()))
        print("    ※同一結果を狙うものではない（あちらは npl=100 固定の別カーブ）。")
    except SystemExit:
        print("  zscale+tonemap 経路との比較: この ffmpeg ビルドでは実行できずスキップ")

    ok = mono and neutral_err < 0.01 and 0.85 < white < 1.02
    print("  判定                      : %s" % ("OK" if ok else "要調査"))
    return ok


def main():
    with tempfile.TemporaryDirectory() as tmp:
        a = verify_rec709_cine(tmp)
        b = verify_hlg(tmp)
    print()
    print("総合: %s" % ("PASS" if (a and b) else "FAIL"))
    return 0 if (a and b) else 1


if __name__ == "__main__":
    sys.exit(main())
