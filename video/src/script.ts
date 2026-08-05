/**
 * リールの台本データ。
 *
 * ここだけ書き換えれば別ネタのリールになる、というのがこの構成の狙い。
 * 構成は kazuya-script-creator スキルの型に合わせている:
 *   フック → 転換（製品名/機能名）→ まず → しかも → さらに → つまり → CTA
 */

export type Scene =
  | { type: "hook"; frames: number; lines: string[]; caption: string }
  | { type: "title"; frames: number; title: string; sub: string; caption: string }
  | {
      type: "step";
      frames: number;
      label: string;
      lines: string[];
      caption: string;
      screen: "settings" | "actions" | "assigned";
    }
  | { type: "punch"; frames: number; lines: string[]; caption: string }
  | { type: "cta"; frames: number; lines: string[]; keyword: string; caption: string };

export const HANDLE = "@kazuya_iphone";

export const SCENES: Scene[] = [
  {
    type: "hook",
    frames: 110,
    lines: ["料理中に手がベタベタ", "スマホ触りたくないけど", "タイマーは止めたい"],
    caption: "手が使えない時のiPhone",
  },
  {
    type: "title",
    frames: 80,
    title: "背面タップ",
    sub: "iPhoneに最初から入ってる機能",
    caption: "知らない人の方が多い",
  },
  {
    type: "step",
    frames: 170,
    label: "まず",
    lines: ["設定 → アクセシビリティ", "→ タッチ → 背面タップ"],
    caption: "設定から数タップで有効化",
    screen: "settings",
  },
  {
    type: "step",
    frames: 160,
    label: "しかも",
    lines: ["ダブルタップに", "好きな機能を割り当て"],
    caption: "スクショ・ライト・カメラなど",
    screen: "actions",
  },
  {
    type: "step",
    frames: 150,
    label: "さらに",
    lines: ["トリプルタップは", "別の機能を登録できる"],
    caption: "背面だけで2つ操作が増える",
    screen: "assigned",
  },
  {
    type: "punch",
    frames: 90,
    lines: ["つまり", "画面を触らずに", "iPhoneが動く"],
    caption: "手がふさがってても大丈夫",
  },
  {
    type: "cta",
    frames: 110,
    lines: ["「背面」とコメントで", "設定手順を送ります"],
    keyword: "背面",
    caption: "保存しておくと後で使える",
  },
];

export const TOTAL_FRAMES = SCENES.reduce((sum, s) => sum + s.frames, 0);

/** 全テキスト（フォントのプリロード用） */
export const ALL_TEXT =
  SCENES.map((s) => JSON.stringify(s)).join("") + HANDLE + "「」→";
