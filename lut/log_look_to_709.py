#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ログ素材用ルック LUT から、その 709 バージョンを作る。

いつも作っている2本のうち、片方（ログ素材用）だけがある状態からもう片方を作るためのツール。

    ログ素材用 : T = ルック ∘ N   （Apple Log 2 -> Rec.709 変換 + グレードが1本に入っている）
    709ルック用: K = T ∘ N⁻¹      （すでに Rec.709 の素材に当てるグレードだけの LUT）

N（ニュートラル変換 LUT。例: AppleLog2_to_Rec709_65_Grid.cube）を数値的に逆引きして、
ログ素材用 LUT と合成する。手で似せるのではなく、同じ絵になるように計算で出す。

使い方:
    python3 log_look_to_709.py --neutral AppleLog2_to_Rec709_65_Grid.cube \\
                               --look Tech_AppleLog2.cube -o luts/Tech_Rec709_33.cube

    python3 log_look_to_709.py --selftest      # 合成データで逆引き精度を確認する
"""

import argparse
import os
import sys

import numpy as np
from scipy.spatial import cKDTree


# ---------------------------------------------------------------------------
# .cube 入出力
# ---------------------------------------------------------------------------

def read_cube(path):
    """.cube を読む。戻り値は (size, data) で data は [b][g][r] 順の (s,s,s,3)。"""
    size = None
    rows = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if line.upper().startswith("LUT_3D_SIZE"):
                size = int(line.split()[1])
                continue
            if line.upper().startswith(("TITLE", "DOMAIN_MIN", "DOMAIN_MAX", "LUT_1D_SIZE")):
                continue
            parts = line.split()
            if len(parts) != 3:
                continue
            try:
                rows.append([float(v) for v in parts])
            except ValueError:
                continue
    if size is None:
        raise SystemExit("LUT_3D_SIZE が見つかりません: %s" % path)
    data = np.array(rows, dtype=np.float64)
    if data.shape[0] != size ** 3:
        raise SystemExit("エントリ数が LUT_3D_SIZE と合いません: %s (%d != %d)"
                         % (path, data.shape[0], size ** 3))
    return size, data.reshape(size, size, size, 3)


def write_cube(path, values, size, header_lines):
    with open(path, "w") as f:
        for line in header_lines:
            f.write("# %s\n" % line)
        f.write("LUT_3D_SIZE %d\n" % size)
        f.write("DOMAIN_MIN 0.0 0.0 0.0\n")
        f.write("DOMAIN_MAX 1.0 1.0 1.0\n")
        for row in values:
            f.write("%.6f %.6f %.6f\n" % (row[0], row[1], row[2]))


def sample(data, size, pts):
    """三重線形補間で LUT を適用する。pts は (N,3) の RGB。"""
    pos = np.clip(pts, 0.0, 1.0) * (size - 1)
    i0 = np.floor(pos).astype(int)
    i0 = np.minimum(i0, size - 2) if size > 1 else i0
    i1 = np.minimum(i0 + 1, size - 1)
    f = pos - i0
    out = np.zeros((pts.shape[0], 3))
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


def grid_points(size):
    """.cube の並び順（red が最速）で格子点を返す。"""
    axis = np.linspace(0.0, 1.0, size)
    b, g, r = np.meshgrid(axis, axis, axis, indexing="ij")
    return np.stack([r.ravel(), g.ravel(), b.ravel()], axis=-1)


# ---------------------------------------------------------------------------
# LUT の逆引き
# ---------------------------------------------------------------------------

def invert(data, size, targets, seed_size=49, iters=40, verbose=True):
    """N(x) = y を x について解く。戻り値は (x, 残差)。

    1) N を細かい格子で前方サンプルし、KD木で最も近い出力を持つ x を初期値にする
    2) 数値ヤコビアンでガウス・ニュートン反復（[0,1] にクランプ）
    """
    seeds = grid_points(seed_size)
    seed_out = sample(data, size, seeds)
    tree = cKDTree(seed_out)
    _, idx = tree.query(targets, k=1)
    x = seeds[idx].copy()

    h = 0.5 / (size - 1)
    eye = np.eye(3)[None, :, :] * 1e-6
    for _ in range(iters):
        fx = sample(data, size, x) - targets
        jac = np.empty((x.shape[0], 3, 3))
        for c in range(3):
            dp = np.zeros(3)
            dp[c] = h
            jac[:, :, c] = (sample(data, size, x + dp) - sample(data, size, x - dp)) / (2 * h)
        try:
            step = np.linalg.solve(jac + eye, -fx[:, :, None])[:, :, 0]
        except np.linalg.LinAlgError:
            step = -np.einsum("nij,nj->ni", np.linalg.pinv(jac), fx)
        step = np.clip(step, -0.25, 0.25)
        x = np.clip(x + step, 0.0, 1.0)

    resid = np.linalg.norm(sample(data, size, x) - targets, axis=1)
    if verbose:
        print("  逆引き残差: 平均 %.5f / 中央値 %.5f / 最大 %.5f (0-1 スケール)"
              % (resid.mean(), np.median(resid), resid.max()))
        print("  残差 > 0.01 の格子点: %.2f%%（元の変換で出せない色＝ガモット外）"
              % (100.0 * (resid > 0.01).mean()))
    return x, resid


# ---------------------------------------------------------------------------
# 本体
# ---------------------------------------------------------------------------

def build(neutral_path, look_path, out_path, size=33, seed_size=49):
    n_size, n_data = read_cube(neutral_path)
    t_size, t_data = read_cube(look_path)
    print("ニュートラル変換 LUT : %s (size=%d)" % (os.path.basename(neutral_path), n_size))
    print("ログ素材用ルック LUT : %s (size=%d)" % (os.path.basename(look_path), t_size))

    targets = grid_points(size)
    print("Rec.709 の %d^3 = %d 点について N を逆引きします..." % (size, size ** 3))
    x, resid = invert(n_data, n_size, targets, seed_size=seed_size)

    # K(y) = y + (T(x) - N(x))
    # 逆引きが完全に解けた点では T(x) そのもの（N(x) = y なので）。解けない点＝
    # ニュートラル変換では出せない色（ガモット外）では、いちばん近い到達点での
    # 「ルックのかかり方（差分）」をそのまま延長する。T(x) をそのまま使うと
    # ガモット外の色が1点に潰れて、彩度の高い被写体でハンティングが起きる。
    reached = sample(n_data, n_size, x)
    values = np.clip(targets + (sample(t_data, t_size, x) - reached), 0.0, 1.0)
    write_cube(out_path, values, size, [
        "709 look (Rec.709 -> Rec.709 + look)",
        "derived as T . N^-1 from:",
        "  N = %s" % os.path.basename(neutral_path),
        "  T = %s" % os.path.basename(look_path),
        "generated by log_look_to_709.py",
    ])
    print("書き出し: %s" % out_path)

    # 検証: ログ素材に N -> K と当てた結果が、元の T と一致するか
    rng = np.random.default_rng(0)
    probe = rng.random((20000, 3))
    via = sample(values.reshape(size, size, size, 3), size, sample(n_data, n_size, probe))
    direct = sample(t_data, t_size, probe)
    d = np.abs(via - direct) * 255.0
    print()
    print("検証: ログ素材に「N → 生成した709ルック」と当てた結果 vs 元の %s"
          % os.path.basename(look_path))
    print("  差: 平均 %.2f / 中央値 %.2f / 最大 %.1f レベル (8bit)"
          % (d.mean(), np.median(d), d.max()))
    print("  差 <= 2 レベル: %.1f%%" % (100.0 * (d <= 2).mean()))
    return values, d


def selftest():
    """合成データで逆引きの精度を確認する（実ファイル無しで動く）。"""
    print("=== セルフテスト: 既知の N と K から T を作り、K を復元できるか ===")
    size_n, size_k = 65, 33

    def fake_neutral(p):                      # log っぽいデコード + 軽い彩度落ち
        y = np.clip((np.power(np.clip(p, 1e-4, 1), 0.45) - 0.12) / 0.83, 0, 1)
        lum = y @ np.array([0.2126, 0.7152, 0.0722])
        return np.clip(lum[:, None] + (y - lum[:, None]) * 0.9, 0, 1)

    def fake_look(p):                         # コントラスト + 寒色寄せ
        q = np.clip((p - 0.5) * 1.12 + 0.5, 0, 1)
        return np.clip(q + np.array([-0.02, 0.0, 0.03]) * (1 - q), 0, 1)

    tmp = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".selftest")
    os.makedirs(tmp, exist_ok=True)
    n_pts = grid_points(size_n)
    write_cube(os.path.join(tmp, "N.cube"), fake_neutral(n_pts), size_n, ["synthetic neutral"])
    t_pts = grid_points(size_k)
    write_cube(os.path.join(tmp, "T.cube"), fake_look(fake_neutral(t_pts)), size_k,
               ["synthetic log look"])

    values, _ = build(os.path.join(tmp, "N.cube"), os.path.join(tmp, "T.cube"),
                      os.path.join(tmp, "K.cube"), size=size_k)
    truth = fake_look(t_pts)
    d = np.abs(values - truth) * 255.0
    print()
    print("復元した K vs 本物の K : 平均 %.2f / 最大 %.1f レベル (8bit)" % (d.mean(), d.max()))
    print("  ※差の大きい所はニュートラル変換のガモット外＝正解が定義されない領域")
    ok = d.mean() < 1.0
    print("判定: %s" % ("OK" if ok else "要調査"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--neutral", help="ニュートラル変換 LUT（例: AppleLog2_to_Rec709_65_Grid.cube）")
    ap.add_argument("--look", help="ログ素材用のルック LUT（例: Tech_AppleLog2.cube）")
    ap.add_argument("-o", "--out", help="出力する 709 ルック LUT")
    ap.add_argument("--size", type=int, default=33)
    ap.add_argument("--seed-size", type=int, default=49, help="逆引きの初期値に使う格子の細かさ")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()

    if args.selftest:
        return selftest()
    if not (args.neutral and args.look and args.out):
        ap.error("--neutral / --look / -o を指定してください（または --selftest）")
    build(args.neutral, args.look, args.out, size=args.size, seed_size=args.seed_size)
    return 0


if __name__ == "__main__":
    sys.exit(main())
