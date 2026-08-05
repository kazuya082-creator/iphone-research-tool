import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { CAPTION_Y, COLOR, FONT } from "../layout";

type LineProps = {
  children: React.ReactNode;
  delay: number;
  size: number;
  weight?: number;
  color?: string;
  marker?: boolean;
};

/**
 * 1行ずつ下から立ち上がってくる見出し。
 * 台本が「1行 = 1センテンス」なので、行単位で出すとリズムが台本と揃う。
 */
export const Line: React.FC<LineProps> = ({
  children,
  delay,
  size,
  weight = 900,
  color = COLOR.ink,
  marker = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 14, mass: 0.6 } });
  const y = interpolate(s, [0, 1], [46, 0]);

  return (
    <div
      style={{
        position: "relative",
        display: "inline-block",
        opacity: s,
        transform: `translateY(${y}px)`,
        fontFamily: FONT,
        fontWeight: weight,
        fontSize: size,
        lineHeight: 1.42,
        letterSpacing: -1,
        color,
        padding: "0 6px",
      }}
    >
      {marker ? (
        <span
          style={{
            position: "absolute",
            left: 0,
            right: 0,
            bottom: size * 0.06,
            height: size * 0.34,
            background: "rgba(255,214,10,0.75)",
            borderRadius: 6,
            transform: `scaleX(${interpolate(
              frame - delay - 6,
              [0, 12],
              [0, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" },
            )})`,
            transformOrigin: "left center",
            zIndex: -1,
          }}
        />
      ) : null}
      {children}
    </div>
  );
};

/** まず / しかも / さらに のバッジ */
export const StepBadge: React.FC<{ label: string; delay: number }> = ({ label, delay }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - delay, fps, config: { damping: 12, mass: 0.5 } });

  return (
    <div
      style={{
        display: "inline-block",
        transform: `scale(${interpolate(s, [0, 1], [0.7, 1])}) rotate(${interpolate(
          s,
          [0, 1],
          [-6, -2],
        )}deg)`,
        opacity: s,
        padding: "10px 34px",
        borderRadius: 18,
        background: COLOR.accent,
        color: COLOR.white,
        fontFamily: FONT,
        fontWeight: 900,
        fontSize: 46,
        letterSpacing: 2,
        boxShadow: "0 12px 30px rgba(255,59,92,0.35)",
      }}
    >
      {label}
    </div>
  );
};

/** 画面下の焼き込み字幕。音を出さずに見る人向けなので常時出す */
export const Caption: React.FC<{ text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [0, 8], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: CAPTION_Y,
        left: 0,
        right: 0,
        display: "flex",
        justifyContent: "center",
        opacity,
      }}
    >
      <div
        style={{
          maxWidth: 900,
          padding: "16px 38px",
          borderRadius: 20,
          background: "rgba(11,16,32,0.88)",
          color: COLOR.white,
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 42,
          lineHeight: 1.3,
          textAlign: "center",
        }}
      >
        {text}
      </div>
    </div>
  );
};
