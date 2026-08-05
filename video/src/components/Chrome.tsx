import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR, FONT, HANDLE_Y } from "../layout";
import { HANDLE } from "../script";

/** 背景：淡いグラデーションとゆっくり動く光の玉 */
export const Background: React.FC = () => {
  const frame = useCurrentFrame();
  const drift = (speed: number, amp: number, phase: number) =>
    Math.sin((frame / speed) + phase) * amp;

  return (
    <AbsoluteFill style={{ backgroundColor: COLOR.paper, overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          width: 1100,
          height: 1100,
          left: -280 + drift(70, 40, 0),
          top: -180 + drift(90, 50, 1),
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(10,132,255,0.30), rgba(10,132,255,0) 68%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 1000,
          height: 1000,
          right: -300 + drift(85, 45, 2),
          bottom: -120 + drift(65, 35, 3),
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(255,59,92,0.26), rgba(255,59,92,0) 68%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 800,
          height: 800,
          left: 220 + drift(110, 60, 4),
          top: 700 + drift(75, 40, 5),
          borderRadius: "50%",
          background: "radial-gradient(circle, rgba(48,209,88,0.18), rgba(48,209,88,0) 70%)",
        }}
      />
    </AbsoluteFill>
  );
};

/** 上部の進捗バー（残り時間が見えると離脱が減る） */
export const ProgressBar: React.FC = () => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const pct = interpolate(frame, [0, durationInFrames - 1], [0, 100]);

  return (
    <div
      style={{
        position: "absolute",
        top: 150,
        left: 90,
        right: 90,
        height: 10,
        borderRadius: 5,
        background: "rgba(11,16,32,0.10)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${pct}%`,
          height: "100%",
          borderRadius: 5,
          background: `linear-gradient(90deg, ${COLOR.blue}, ${COLOR.accent})`,
        }}
      />
    </div>
  );
};

/** アカウント名のチップ（リポスト対策と認知の刷り込み） */
export const HandleChip: React.FC = () => (
  <div
    style={{
      position: "absolute",
      top: HANDLE_Y,
      left: 0,
      right: 0,
      display: "flex",
      justifyContent: "center",
    }}
  >
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 14,
        padding: "12px 30px",
        borderRadius: 999,
        background: "rgba(255,255,255,0.72)",
        border: "2px solid rgba(11,16,32,0.08)",
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: 30,
        color: COLOR.inkSub,
        letterSpacing: 0.5,
      }}
    >
      <div
        style={{
          width: 20,
          height: 20,
          borderRadius: 10,
          background: `linear-gradient(135deg, ${COLOR.accent}, ${COLOR.blue})`,
        }}
      />
      {HANDLE}
    </div>
  </div>
);
