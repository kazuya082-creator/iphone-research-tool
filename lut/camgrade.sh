#!/usr/bin/env bash
# camgrade — iPhone 標準カメラで撮った素材にルック LUT を当てる
#
#   camgrade <入力ファイル> [neutral|cine|match] [prores|mp4]
#
# Apple Log 2 素材用の `lutgrade` の標準カメラ版。
# 入力の transfer を見て HDR(HLG) / SDR(Rec.709) を判定し、対応する LUT を選ぶ。
#
#   neutral : HLG -> Rec.709 変換のみ（ルック無し）。SDR 入力では何もすることが無い
#   cine    : Log パイプラインの「②控えめシネマティック」と同じグレード（既定）
#   match   : cine + Log グレード素材と混ぜる用の寄せ込み（黒を上げ・ハイライトを丸め）
#
#   prores : 編集用マスター（ProRes 422 / 10bit）
#   mp4    : 確認・納品用（H.264 / CRF18）※既定
#
# 出力は入力と同じフォルダに <元の名前>_<look>.<拡張子> で書き出す。原本は触らない。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LUT_DIR="$SCRIPT_DIR/luts"

usage() {
    sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
    exit 1
}

[ $# -ge 1 ] || usage
SRC="$1"
LOOK="${2:-cine}"
FMT="${3:-mp4}"

[ -f "$SRC" ] || { echo "入力が見つかりません: $SRC" >&2; exit 1; }
case "$LOOK" in neutral|cine|match) ;; *) echo "look は neutral / cine / match のいずれか: $LOOK" >&2; exit 1;; esac
case "$FMT"  in prores|mp4) ;;        *) echo "format は prores / mp4 のいずれか: $FMT" >&2; exit 1;; esac

TRC="$(ffprobe -v error -select_streams v:0 -show_entries stream=color_transfer \
        -of default=nw=1:nk=1 "$SRC" 2>/dev/null || true)"

case "$TRC" in
    arib-std-b67)
        KIND="hlg"
        echo "入力: HDR / HLG (BT.2020) と判定 — トーンマップ込みの LUT を使います"
        ;;
    smpte2084)
        echo "入力が PQ (smpte2084) です。標準カメラの HDR は通常 HLG なので、" >&2
        echo "この素材は別経路（PQ 用の変換）が必要です。処理を中止します。" >&2
        exit 1
        ;;
    *)
        KIND="rec709"
        echo "入力: SDR / Rec.709 と判定 (transfer=${TRC:-未タグ})"
        if [ "$LOOK" = "neutral" ]; then
            echo "SDR 入力に neutral は素通しになるため何もしません。cine か match を指定してください。" >&2
            exit 1
        fi
        ;;
esac

case "$KIND/$LOOK" in
    rec709/cine)   LUT="iPhoneCam_Rec709_Cinematic_33.cube" ;;
    rec709/match)  LUT="iPhoneCam_Rec709_LogMatch_33.cube" ;;
    hlg/neutral)   LUT="iPhoneCam_HLG_to_Rec709_Neutral_33.cube" ;;
    hlg/cine)      LUT="iPhoneCam_HLG_to_Rec709_Cinematic_33.cube" ;;
    hlg/match)     LUT="iPhoneCam_HLG_to_Rec709_LogMatch_33.cube" ;;
esac
LUT_PATH="$LUT_DIR/$LUT"
[ -f "$LUT_PATH" ] || { echo "LUT が見つかりません: $LUT_PATH（make_lut.py --all で生成できます）" >&2; exit 1; }

DIR="$(cd "$(dirname "$SRC")" && pwd)"
BASE="$(basename "$SRC")"
STEM="${BASE%.*}"

# lut3d の後に setparams を必ず挟む。出力オプションの -color_trc だけだと
# ProRes の colr アトムが unspecified のままになる（Log 側で踏んだのと同じ罠）。
VF="lut3d=${LUT_PATH//:/\\:},setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709"

if [ "$FMT" = "prores" ]; then
    OUT="$DIR/${STEM}_${LOOK}.mov"
    ENC=(-c:v prores_ks -profile:v 2 -pix_fmt yuv422p10le -movflags +write_colr)
else
    OUT="$DIR/${STEM}_${LOOK}.mp4"
    ENC=(-c:v libx264 -crf 18 -preset slow -pix_fmt yuv420p -movflags +faststart)
fi

echo "LUT   : $LUT"
echo "出力  : $OUT"

# -noautorotate: 回転メタデータを実体化させず原本と同じ向き・同じ解像度で出す。
# （実体化すると 1920x1080+rotation90 が 1080x1920 になり、
#   完パケ側の build スクリプトが自前でやっている回転処理と二重になる）
ffmpeg -hide_banner -v warning -stats -y -noautorotate -i "$SRC" \
    -vf "$VF" "${ENC[@]}" \
    -color_primaries bt709 -color_trc bt709 -colorspace bt709 \
    -c:a copy "$OUT"

echo "完了: $OUT"
