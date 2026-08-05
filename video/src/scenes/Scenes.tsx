import React from "react";
import { interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { COLOR, FONT, HEADLINE_TOP } from "../layout";
import { Caption, Line, StepBadge } from "../components/Text";
import { Phone } from "../components/Phone";
import type { Scene } from "../script";
import { HANDLE } from "../script";

const Stack: React.FC<{ top: number; children: React.ReactNode; gap?: number }> = ({
  top,
  children,
  gap = 8,
}) => (
  <div
    style={{
      position: "absolute",
      top,
      left: 70,
      right: 70,
      display: "flex",
      flexDirection: "column",
      alignItems: "center",
      gap,
      textAlign: "center",
    }}
  >
    {children}
  </div>
);

export const HookScene: React.FC<{ scene: Extract<Scene, { type: "hook" }> }> = ({ scene }) => (
  <>
    <Stack top={520} gap={4}>
      {scene.lines.map((l, i) => (
        <Line key={l} delay={6 + i * 14} size={84} marker={i === scene.lines.length - 1}>
          {l}
        </Line>
      ))}
    </Stack>
    <Stack top={980}>
      <Line delay={62} size={44} weight={700} color={COLOR.inkSub}>
        それ、設定1つで解決します
      </Line>
    </Stack>
    <Caption text={scene.caption} />
  </>
);

export const TitleScene: React.FC<{ scene: Extract<Scene, { type: "title" }> }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const s = spring({ frame: frame - 4, fps, config: { damping: 13, mass: 0.7 } });

  return (
    <>
      <Stack top={620} gap={26}>
        <Line delay={0} size={44} weight={700} color={COLOR.inkSub}>
          {scene.sub}
        </Line>
        <div
          style={{
            transform: `scale(${interpolate(s, [0, 1], [0.72, 1])})`,
            opacity: s,
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 152,
            letterSpacing: -4,
            color: COLOR.ink,
            textShadow: "0 18px 40px rgba(11,16,32,0.18)",
          }}
        >
          {scene.title}
        </div>
        <Line delay={26} size={48} weight={900} color={COLOR.accent}>
          知らないと損してる
        </Line>
      </Stack>
      <Caption text={scene.caption} />
    </>
  );
};

export const StepScene: React.FC<{ scene: Extract<Scene, { type: "step" }> }> = ({ scene }) => (
  <>
    <Stack top={HEADLINE_TOP} gap={14}>
      <StepBadge label={scene.label} delay={2} />
      {scene.lines.map((l, i) => (
        <Line key={l} delay={12 + i * 12} size={58}>
          {l}
        </Line>
      ))}
    </Stack>
    <Phone screen={scene.screen} />
    <Caption text={scene.caption} />
  </>
);

export const PunchScene: React.FC<{ scene: Extract<Scene, { type: "punch" }> }> = ({ scene }) => (
  <>
    <Stack top={560} gap={6}>
      {scene.lines.map((l, i) => (
        <Line
          key={l}
          delay={4 + i * 13}
          size={i === 0 ? 62 : 92}
          color={i === 0 ? COLOR.accent : COLOR.ink}
          marker={i === scene.lines.length - 1}
        >
          {l}
        </Line>
      ))}
    </Stack>
    <Caption text={scene.caption} />
  </>
);

export const CtaScene: React.FC<{ scene: Extract<Scene, { type: "cta" }> }> = ({ scene }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const bubble = spring({ frame: frame - 34, fps, config: { damping: 14, mass: 0.7 } });
  const typed = scene.keyword.slice(
    0,
    Math.max(0, Math.floor(interpolate(frame, [46, 62], [0, scene.keyword.length], {
      extrapolateLeft: "clamp",
      extrapolateRight: "clamp",
    }))),
  );

  return (
    <>
      <Stack top={480} gap={6}>
        {scene.lines.map((l, i) => (
          <Line key={l} delay={4 + i * 13} size={72}>
            {l}
          </Line>
        ))}
      </Stack>

      {/* コメント欄の見立て */}
      <div
        style={{
          position: "absolute",
          top: 820,
          left: 120,
          right: 120,
          display: "flex",
          alignItems: "center",
          gap: 20,
          padding: "22px 28px",
          borderRadius: 999,
          background: COLOR.white,
          boxShadow: "0 24px 60px rgba(11,16,32,0.16)",
          opacity: bubble,
          transform: `translateY(${interpolate(bubble, [0, 1], [40, 0])}px)`,
        }}
      >
        <div
          style={{
            width: 62,
            height: 62,
            borderRadius: 31,
            background: `linear-gradient(135deg, ${COLOR.accent}, ${COLOR.blue})`,
            flexShrink: 0,
          }}
        />
        <div
          style={{
            flex: 1,
            fontFamily: FONT,
            fontWeight: 700,
            fontSize: 44,
            color: typed ? COLOR.ink : "rgba(11,16,32,0.3)",
          }}
        >
          {typed || "コメントを追加..."}
          {frame % 20 < 10 && typed.length < scene.keyword.length ? "|" : ""}
        </div>
        <div
          style={{
            fontFamily: FONT,
            fontWeight: 900,
            fontSize: 36,
            color: typed ? COLOR.blue : "rgba(10,132,255,0.35)",
          }}
        >
          送信
        </div>
      </div>

      <Stack top={1010} gap={10}>
        <Line delay={72} size={40} weight={700} color={COLOR.inkSub}>
          iPhoneの便利機能を毎日発信中
        </Line>
        <Line delay={80} size={56} weight={900} color={COLOR.ink}>
          {HANDLE}
        </Line>
      </Stack>
      <Caption text={scene.caption} />
    </>
  );
};
