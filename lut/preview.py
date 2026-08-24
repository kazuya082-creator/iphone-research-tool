#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LUT の効きを before/after で見るための比較画像を作る。

  python3 preview.py                     # 内蔵のテストチャートで比較
  python3 preview.py <画像 or 動画>       # 実素材（動画は先頭付近の1フレーム）で比較
  python3 preview.py <入力> --hlg         # 入力を HDR(HLG) 素材として扱う

出力: preview_rec709.png / preview_hlg.png（-o で変更可）
"""

import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
LUTS = os.path.join(HERE, "luts")
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/System/Library/Fonts/SFNS.ttf",
]

SETS = {
    "rec709": [("original", None),
               ("cine", "iPhoneCam_Rec709_Cinematic_33.cube"),
               ("match", "iPhoneCam_Rec709_LogMatch_33.cube")],
    "hlg": [("original (HLG)", None),
            ("neutral", "iPhoneCam_HLG_to_Rec709_Neutral_33.cube"),
            ("cine", "iPhoneCam_HLG_to_Rec709_Cinematic_33.cube"),
            ("match", "iPhoneCam_HLG_to_Rec709_LogMatch_33.cube")],
}


def run(cmd):
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr.decode("utf-8", "replace")[-1500:])
        raise SystemExit("ffmpeg failed")


def test_chart(w=480, h=270):
    """グレーランプ・肌色帯・原色パッチを並べた合成チャート。"""
    img = np.zeros((h, w, 3), np.float64)
    x = np.linspace(0, 1, w)
    img[: h // 3] = x[None, :, None]                      # グレーランプ
    skin = np.array([[0.85, 0.68, 0.58], [0.72, 0.52, 0.42],
                     [0.55, 0.38, 0.30], [0.38, 0.26, 0.21]])
    for i, c in enumerate(skin):                          # 肌色（明るさ違い）
        s, e = h // 3 + i * (h // 12), h // 3 + (i + 1) * (h // 12)
        img[s:e] = c
    patches = np.array([[0.75, 0.15, 0.15], [0.15, 0.55, 0.25], [0.15, 0.30, 0.75],
                        [0.85, 0.75, 0.25], [0.25, 0.65, 0.75], [0.70, 0.35, 0.65],
                        [0.95, 0.95, 0.95], [0.06, 0.06, 0.06]])
    pw = w // len(patches)
    for i, c in enumerate(patches):
        img[2 * h // 3:, i * pw:(i + 1) * pw] = c
    return np.clip(img * 255, 0, 255).astype(np.uint8)


def font():
    for f in FONT_CANDIDATES:
        if os.path.exists(f):
            return f
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input", nargs="?", help="画像 / 動画。省略時は内蔵チャート")
    ap.add_argument("--hlg", action="store_true", help="入力を HDR(HLG) として扱う")
    ap.add_argument("-o", "--out")
    args = ap.parse_args()

    kind = "hlg" if args.hlg else "rec709"
    out = args.out or os.path.join(HERE, "preview_%s.png" % kind)

    with tempfile.TemporaryDirectory() as tmp:
        if args.input:
            src = os.path.join(tmp, "frame.png")
            run(["ffmpeg", "-v", "error", "-y", "-noautorotate", "-i", args.input,
                 "-frames:v", "1", "-vf", "scale=480:-2", src])
        else:
            if args.hlg:
                sys.exit("内蔵チャートは Rec.709 用です。--hlg は実素材と一緒に使ってください。")
            src = os.path.join(tmp, "chart.png")
            raw = os.path.join(tmp, "chart.raw")
            chart = test_chart()
            chart.tofile(raw)
            run(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                 "-s", "%dx%d" % (chart.shape[1], chart.shape[0]), "-i", raw, src])

        inputs, filters, labels = [], [], []
        for i, (name, lut) in enumerate(SETS[kind]):
            inputs += ["-i", src]
            vf = "[%d:v]" % i
            if lut:
                path = os.path.join(LUTS, lut).replace(":", r"\:")
                vf += "lut3d=%s," % path
            vf += "pad=iw:ih+28:0:0:black"
            f = font()
            if f:
                vf += (",drawtext=fontfile=%s:text='%s':x=8:y=h-22:fontsize=15:fontcolor=white"
                       % (f, name))
            filters.append(vf + "[v%d]" % i)
            labels.append("[v%d]" % i)
        fc = ";".join(filters) + ";" + "".join(labels) + "vstack=inputs=%d[out]" % len(labels)
        run(["ffmpeg", "-v", "error", "-y"] + inputs +
            ["-filter_complex", fc, "-map", "[out]", "-frames:v", "1", out])
    print("wrote %s" % out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
