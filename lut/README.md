# iPhone 標準カメラ素材用 ルック LUT

Blackmagic Cam の Apple Log 2 素材に当てている完パケグレードと同じ「絵」を、
**iPhone 標準カメラアプリで撮った素材**にも当てるための LUT 一式。

Log 素材側は `lutgrade`（`AppleLog2_to_Rec709_65_Grid.cube` + `eq`/`colorbalance`）で
処理しているが、標準カメラ素材にはそのまま当てられない（ログではないので二重にグレードされる）。
ここではその後段のグレードだけを LUT に焼き込み、さらに標準カメラの HDR(HLG) 素材については
HLG → Rec.709 のトーンマップまで同じ 1 本に畳み込んである。

## ファイル

| ファイル | 中身 |
|---|---|
| `camgrade.sh` | ワンコマンド実行。入力を見て LUT を自動選択する（`lutgrade` の標準カメラ版） |
| `make_lut.py` | LUT ジェネレータ。ルックの数値はすべてこの中の `LOOKS` に集約 |
| `verify_lut.py` | 生成した LUT が実フィルタチェーンと一致するかを ffmpeg で数値検証 |
| `preview.py` | before/after の比較画像を作る |
| `log_look_to_709.py` | ログ素材用ルック LUT から 709 バージョンを作る（下記） |
| `luts/*.cube` | 生成済み LUT（33 グリッド） |

## 使い方

```bash
# 確認・納品用 mp4
./camgrade.sh IMG_1234.MOV cine mp4

# 編集用 ProRes マスター
./camgrade.sh IMG_1234.MOV cine prores
```

書式は `camgrade.sh <入力> [neutral|cine|match] [prores|mp4]`。
出力は入力と同じフォルダに `<元の名前>_<look>.<拡張子>`。原本は触らない。

Mac のどこからでも叩けるようにするなら `lutgrade` と同じ要領で:

```bash
ln -s "$PWD/camgrade.sh" /opt/homebrew/bin/camgrade
```

手で ffmpeg を書く場合:

```bash
ffmpeg -noautorotate -i IMG_1234.MOV \
  -vf "lut3d=luts/iPhoneCam_Rec709_Cinematic_33.cube,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709" \
  -c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le -movflags +write_colr -c:a copy out.mov
```

## どの LUT が選ばれるか

`camgrade.sh` は `ffprobe` で `color_transfer` を見て自動判定する。

| 入力 | 判定 | 使う LUT |
|---|---|---|
| HDR ビデオ ON（`arib-std-b67` / BT.2020） | HLG | `iPhoneCam_HLG_to_Rec709_*` |
| HDR ビデオ OFF（`bt709` / 未タグ） | SDR | `iPhoneCam_Rec709_*` |
| PQ（`smpte2084`） | 非対応 | 中止（標準カメラは通常 HLG。PQ が来たら別途対応が要る） |

ルックは 4 択:

- **neutral** — HLG → Rec.709 の変換のみ。ルック無し。SDR 入力では何もすることが無いので拒否される
- **cine** — Log パイプラインの「②控えめシネマティック」と**同一のグレード**
  （`eq=contrast=1.05:saturation=0.92` → `colorbalance=rs=-0.03:bs=0.05:rh=0.03:bh=-0.03`）
- **match** — cine に加えて、標準カメラ特有の締まりすぎ・濃さを寝かせた版。
  Log グレード素材と同じ動画に混ぜるときはこちら
- **tech** — `Tech_AppleLog2.cube` の 709 バージョン。`log_look_to_709.py` で生成する（下記）。
  HDR 撮影はオフの運用なので HLG 版は用意していない

## Log 素材と並べたときの注意

**cine を当てても Log 素材と完全に同じ絵にはならない。** 当てているグレード操作は同一だが、
土台が違う（標準カメラは Apple の絵作りが焼き込み済み、Log 素材はニュートラル変換後）。
これを寄せるためのものが `match` で、その補正値（黒の持ち上げ 0.012 / コントラスト 0.99 /
彩度 0.90 / ハイライトショルダー 0.78）は**実素材で追い込む前提の初期値**。
同じ被写体を標準カメラと Blackmagic Cam で撮り比べた素材があれば、そこに合わせて
`make_lut.py` の `LOOKS["match"]` を振って `python3 make_lut.py --all` で焼き直すのが早い。

## 検証

`python3 verify_lut.py`（要 ffmpeg）。32,768 色のスイープで、
実フィルタチェーン（`eq`+`colorbalance`）と `lut3d` の出力を突き合わせている。

現状の結果（ffmpeg 6.1）:

- グレード量そのものが平均 6.18 / 最大 33 レベルなのに対し、**LUT との差は平均 1.6 / 最大 7 レベル**
- そのうち R+2.4 / G+0.3 / B+2.0 レベルは**一定バイアス**で、ffmpeg の `eq` が
  8bit LUT を切り捨てで作ることに由来する（LUT 側は連続式なので、10bit 出力ではむしろ LUT 側が正確）
- バイアスを除いた「グレードの形」の残差は**平均 0.64 レベル**
- 裏取りとして、ffmpeg から `eq` の 256 エントリ LUT を実測してモデルに同じ量子化を入れると
  差は**平均 0.32 / 最大 3 レベル**まで落ちる → 上のバイアスは全て量子化由来と確認済み

HLG LUT 側は、グレー階調の単調性、グレーのニュートラル維持（ずれ 0.001 以下）、
HLG 拡散白（信号 0.75）が **96.4 IRE** に着地すること、ピークが白飛びしないことを検証している。

## 実装メモ（踏んだ罠）

- **`colorbalance` の `l` は `max+min`**（明度ではなくその 2 倍）。`(max+min)/2` だと
  シャドウ／ハイライトの効き始める明るさが丸ごとズレる。ffmpeg 6.1 の実測から確定した
- **`setparams` は必須**。出力オプションの `-color_trc` だけでは ProRes の colr アトムが
  unspecified のままになる（Log パイプラインで踏んだのと同じ罠）
- **`-noautorotate` を付けている**。付けないと回転メタデータが実体化して
  1920x1080+rotation90 が 1080x1920 になり、完パケ側 build スクリプトの回転処理と二重になる
- HLG のトーンマップは Hable/Reinhard を peak で正規化する素直なやり方をやめている。
  それだと拡散白が 62 IRE まで落ちて眠くなるため、拡散白までは素通しし、
  その上だけを 1.0 に漸近させるショルダー（knee 0.70・折れ目が出ないよう傾き連続）にしてある

## ログ素材用ルックの 709 バージョンを作る

ルック LUT はいつも2本セットで作っている:

- **ログ素材用** … `T = ルック ∘ N`（Apple Log 2 → Rec.709 変換とグレードが1本に入っている）
- **709ルック用** … `K = T ∘ N⁻¹`（すでに Rec.709 の素材に当てる、グレードだけの LUT）

片方（ログ素材用）しか無いとき、`log_look_to_709.py` がニュートラル変換 LUT を数値的に
逆引きして、もう片方を計算で出す。手で似せるのではなく同じ絵になるように作る。

```bash
python3 log_look_to_709.py \
  --neutral ~/Downloads/AppleLog2_to_Rec709_65_Grid.cube \
  --look    Tech_AppleLog2.cube \
  -o        luts/Tech_Rec709_33.cube
```

- ニュートラル変換 LUT は**そのルックを作ったときに使った物と同じ**を渡すこと（違うと絵がズレる）
- ガモット外（ニュートラル変換では出せない彩度の高い色）は、いちばん近い到達点での
  ルックのかかり方（差分）を延長して埋める。`T(x)` をそのまま使うと、その領域の色が
  1点に潰れて彩度の高い被写体でハンティングが起きる
- 書き出し後に「ログ素材へ N → 生成した709ルックと当てた結果」と「元のログ素材用ルック」を
  2万点で突き合わせ、差をレベル単位で報告する
- `python3 log_look_to_709.py --selftest` で、既知の N と K から作った T から K を復元できるかを確認できる
  （合成データでの実測: 復元した LUT を経由した絵の差は最大 2.4 / 平均 0.09 レベル）

## 焼き直し

```bash
python3 make_lut.py --all                          # 既定の5本を再生成
python3 make_lut.py --input hlg --look cine --size 65 -o big.cube   # 65 グリッド版
```
