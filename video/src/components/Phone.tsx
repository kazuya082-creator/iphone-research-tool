import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR, FONT, PHONE_H, PHONE_TOP, PHONE_W } from "../layout";

const BEZEL = 12;
const SCREEN_W = PHONE_W - BEZEL * 2;
const SCREEN_H = PHONE_H - BEZEL * 2;

const clamp = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;

/** タップの波紋。押した位置と時間を渡すだけ */
const Ripple: React.FC<{ x: number; y: number; at: number; color?: string }> = ({
  x,
  y,
  at,
  color = "rgba(10,132,255,0.45)",
}) => {
  const frame = useCurrentFrame();
  const t = frame - at;
  if (t < 0 || t > 26) return null;
  const scale = interpolate(t, [0, 26], [0.2, 2.2], clamp);
  const opacity = interpolate(t, [0, 6, 26], [0, 0.9, 0], clamp);

  return (
    <div
      style={{
        position: "absolute",
        left: x - 40,
        top: y - 40,
        width: 80,
        height: 80,
        borderRadius: 40,
        border: `4px solid ${color}`,
        background: color.replace("0.45", "0.16"),
        transform: `scale(${scale})`,
        opacity,
      }}
    />
  );
};

const StatusBar: React.FC = () => (
  <div
    style={{
      height: 54,
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 30px",
      fontFamily: FONT,
      fontWeight: 700,
      fontSize: 22,
      color: COLOR.ink,
    }}
  >
    <span>9:41</span>
    <div style={{ display: "flex", gap: 6, alignItems: "center" }}>
      <div style={{ width: 22, height: 12, borderRadius: 3, background: COLOR.ink, opacity: 0.85 }} />
      <div style={{ width: 26, height: 13, borderRadius: 4, border: `2px solid ${COLOR.ink}`, opacity: 0.6 }} />
    </div>
  </div>
);

export type Row = {
  label: string;
  value?: string;
  target?: boolean;
  toggle?: boolean;
};

const RowView: React.FC<{ row: Row; active: boolean; on?: boolean }> = ({ row, active, on }) => (
  <div
    style={{
      display: "flex",
      alignItems: "center",
      justifyContent: "space-between",
      padding: "0 22px",
      height: row.value ? 100 : 74,
      background: active ? "rgba(10,132,255,0.10)" : COLOR.white,
      borderBottom: "1px solid rgba(11,16,32,0.07)",
      fontFamily: FONT,
      fontSize: 30,
      fontWeight: row.target ? 700 : 400,
      color: COLOR.ink,
    }}
  >
    {row.value ? (
      // 値つきの行は横並びだと文字が潰れるので上下に積む
      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
        <span style={{ fontSize: 24, color: COLOR.inkSub, fontWeight: 700 }}>{row.label}</span>
        <span style={{ fontSize: 30, fontWeight: 900, whiteSpace: "nowrap" }}>{row.value}</span>
      </div>
    ) : (
      <span>{row.label}</span>
    )}
    <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
      {row.toggle ? (
        <div
          style={{
            width: 62,
            height: 36,
            borderRadius: 18,
            background: on ? COLOR.green : "rgba(11,16,32,0.18)",
            position: "relative",
            transition: "none",
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 3,
              left: on ? 29 : 3,
              width: 30,
              height: 30,
              borderRadius: 15,
              background: COLOR.white,
              boxShadow: "0 2px 6px rgba(0,0,0,0.2)",
            }}
          />
        </div>
      ) : (
        <span style={{ color: "rgba(11,16,32,0.28)", fontSize: 30 }}>›</span>
      )}
    </div>
  </div>
);

const Page: React.FC<{ title: string; back?: string; rows: Row[]; activeIndex?: number; toggleOn?: boolean }> = ({
  title,
  back,
  rows,
  activeIndex = -1,
  toggleOn,
}) => (
  <div style={{ width: SCREEN_W, height: SCREEN_H - 54, background: "#EFEFF4" }}>
    <div
      style={{
        height: 78,
        display: "flex",
        alignItems: "center",
        padding: "0 20px",
        gap: 8,
        background: "rgba(255,255,255,0.92)",
        borderBottom: "1px solid rgba(11,16,32,0.08)",
        fontFamily: FONT,
      }}
    >
      {back ? (
        <span style={{ color: COLOR.blue, fontSize: 26, fontWeight: 700, whiteSpace: "nowrap" }}>
          ‹ {back}
        </span>
      ) : null}
      <span
        style={{
          flex: 1,
          textAlign: "center",
          fontSize: 30,
          fontWeight: 900,
          color: COLOR.ink,
          marginRight: back ? 40 : 0,
          whiteSpace: "nowrap",
        }}
      >
        {title}
      </span>
    </div>
    <div style={{ marginTop: 22, borderTop: "1px solid rgba(11,16,32,0.07)" }}>
      {rows.map((r, i) => (
        <RowView key={r.label} row={r} active={i === activeIndex} on={toggleOn} />
      ))}
    </div>
  </div>
);

/** 画面の中身。台本の3ステップに対応した3種類 */
const SETTINGS_PAGES: { title: string; back?: string; rows: Row[]; targetIndex: number }[] = [
  {
    title: "設定",
    rows: [
      { label: "一般" },
      { label: "アクセシビリティ", target: true },
      { label: "画面表示と明るさ" },
      { label: "壁紙" },
      { label: "サウンド" },
    ],
    targetIndex: 1,
  },
  {
    title: "アクセシビリティ",
    back: "設定",
    rows: [
      { label: "音声コントロール" },
      { label: "サイドボタン" },
      { label: "タッチ", target: true },
      { label: "Face IDと注視" },
      { label: "スイッチコントロール" },
    ],
    targetIndex: 2,
  },
  {
    title: "タッチ",
    back: "戻る",
    rows: [
      { label: "AssistiveTouch" },
      { label: "触覚" },
      { label: "簡易アクセス" },
      { label: "背面タップ", target: true, toggle: true },
    ],
    targetIndex: 3,
  },
];

const ACTION_ROWS: Row[] = [
  { label: "なし" },
  { label: "スクリーンショット", target: true },
  { label: "Siri" },
  { label: "コントロールセンター" },
  { label: "フラッシュライト" },
  { label: "拡大鏡" },
];

const rowY = (index: number) => 54 + 78 + 22 + index * 74 + 37;

const SettingsScreen: React.FC = () => {
  const frame = useCurrentFrame();
  // 40f と 85f でドリルダウン、125f でトグルON
  const progress = interpolate(frame, [40, 54, 85, 99], [0, 1, 1, 2], clamp);
  const toggleOn = frame >= 128;

  return (
    <>
      {SETTINGS_PAGES.map((p, i) => (
        <div
          key={p.title}
          style={{
            position: "absolute",
            top: 54,
            left: 0,
            width: SCREEN_W,
            transform: `translateX(${(i - progress) * SCREEN_W}px)`,
            boxShadow: i > 0 ? "-8px 0 24px rgba(0,0,0,0.10)" : undefined,
          }}
        >
          <Page {...p} toggleOn={toggleOn} />
        </div>
      ))}
      <Ripple x={SCREEN_W / 2} y={rowY(SETTINGS_PAGES[0].targetIndex)} at={40} />
      <Ripple x={SCREEN_W / 2} y={rowY(SETTINGS_PAGES[1].targetIndex)} at={85} />
      <Ripple
        x={SCREEN_W - 60}
        y={rowY(SETTINGS_PAGES[2].targetIndex)}
        at={126}
        color="rgba(48,209,88,0.45)"
      />
    </>
  );
};

const ActionsScreen: React.FC = () => {
  const frame = useCurrentFrame();
  const checkedIndex = frame >= 62 ? 1 : -1;

  return (
    <>
      <div style={{ position: "absolute", top: 54, left: 0, width: SCREEN_W }}>
        <div
          style={{
            height: 78,
            display: "flex",
            alignItems: "center",
            padding: "0 20px",
            background: "rgba(255,255,255,0.92)",
            borderBottom: "1px solid rgba(11,16,32,0.08)",
            fontFamily: FONT,
          }}
        >
          <span style={{ color: COLOR.blue, fontSize: 26, fontWeight: 700, whiteSpace: "nowrap" }}>
            ‹ 戻る
          </span>
          <span
            style={{
              flex: 1,
              textAlign: "center",
              fontSize: 30,
              fontWeight: 900,
              color: COLOR.ink,
              marginRight: 40,
              whiteSpace: "nowrap",
            }}
          >
            ダブルタップ
          </span>
        </div>
        <div style={{ marginTop: 22, borderTop: "1px solid rgba(11,16,32,0.07)", background: "#EFEFF4" }}>
          {ACTION_ROWS.map((r, i) => (
            <div
              key={r.label}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                padding: "0 22px",
                height: 74,
                background: i === checkedIndex ? "rgba(10,132,255,0.10)" : COLOR.white,
                borderBottom: "1px solid rgba(11,16,32,0.07)",
                fontFamily: FONT,
                fontSize: 30,
                fontWeight: i === checkedIndex ? 700 : 400,
                color: COLOR.ink,
              }}
            >
              <span>{r.label}</span>
              {i === checkedIndex ? (
                <span style={{ color: COLOR.blue, fontSize: 34, fontWeight: 900 }}>✓</span>
              ) : null}
            </div>
          ))}
        </div>
      </div>
      <Ripple x={SCREEN_W / 2} y={rowY(1)} at={58} />
    </>
  );
};

const AssignedScreen: React.FC = () => {
  const frame = useCurrentFrame();

  return (
    <>
      <div style={{ position: "absolute", top: 54, left: 0, width: SCREEN_W }}>
        <Page
          title="背面タップ"
          back="タッチ"
          rows={[
            { label: "ダブルタップ", value: "スクリーンショット", target: frame >= 40 },
            { label: "トリプルタップ", value: "フラッシュライト", target: frame >= 88 },
          ]}
          activeIndex={frame >= 88 ? 1 : frame >= 40 ? 0 : -1}
        />
        <div
          style={{
            position: "absolute",
            top: 396,
            left: 0,
            right: 0,
            padding: "0 24px",
            fontFamily: FONT,
            fontSize: 24,
            lineHeight: 1.5,
            color: COLOR.inkSub,
          }}
        >
          iPhoneの背面を2回・3回叩くと、
          <br />
          ここで選んだ操作が実行されます。
        </div>
      </div>
      <Ripple x={SCREEN_W / 2} y={rowY(0)} at={38} />
      <Ripple x={SCREEN_W / 2} y={rowY(1)} at={86} color="rgba(255,59,92,0.45)" />
    </>
  );
};

const SCREENS = {
  settings: SettingsScreen,
  actions: ActionsScreen,
  assigned: AssignedScreen,
};

export const Phone: React.FC<{ screen: keyof typeof SCREENS }> = ({ screen }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 10, fps, config: { damping: 16, mass: 0.8 } });
  const Screen = SCREENS[screen];

  return (
    <div
      style={{
        position: "absolute",
        top: PHONE_TOP,
        left: (1080 - PHONE_W) / 2,
        width: PHONE_W,
        height: PHONE_H,
        borderRadius: 56,
        background: "#12161F",
        padding: BEZEL,
        boxShadow: "0 40px 80px rgba(11,16,32,0.28)",
        opacity: s,
        transform: `translateY(${interpolate(s, [0, 1], [70, 0])}px) scale(${interpolate(
          s,
          [0, 1],
          [0.94, 1],
        )})`,
      }}
    >
      <div
        style={{
          position: "relative",
          width: SCREEN_W,
          height: SCREEN_H,
          borderRadius: 46,
          overflow: "hidden",
          background: "#EFEFF4",
        }}
      >
        <StatusBar />
        <Screen />
        {/* Dynamic Island */}
        <div
          style={{
            position: "absolute",
            top: 12,
            left: SCREEN_W / 2 - 52,
            width: 104,
            height: 30,
            borderRadius: 15,
            background: "#12161F",
          }}
        />
      </div>
    </div>
  );
};
