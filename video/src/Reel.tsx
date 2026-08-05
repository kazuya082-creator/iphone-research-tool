import React from "react";
import { AbsoluteFill, Sequence } from "remotion";
import { Background, HandleChip, ProgressBar } from "./components/Chrome";
import { CtaScene, HookScene, PunchScene, StepScene, TitleScene } from "./scenes/Scenes";
import { SCENES, type Scene } from "./script";
import { COLOR, FONT } from "./layout";
import { useFonts } from "./useFonts";

const renderScene = (scene: Scene) => {
  switch (scene.type) {
    case "hook":
      return <HookScene scene={scene} />;
    case "title":
      return <TitleScene scene={scene} />;
    case "step":
      return <StepScene scene={scene} />;
    case "punch":
      return <PunchScene scene={scene} />;
    case "cta":
      return <CtaScene scene={scene} />;
  }
};

export const Reel: React.FC = () => {
  useFonts();

  let from = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: COLOR.paper, fontFamily: FONT }}>
      <Background />
      {SCENES.map((scene, i) => {
        const start = from;
        from += scene.frames;
        return (
          <Sequence key={i} from={start} durationInFrames={scene.frames}>
            {renderScene(scene)}
          </Sequence>
        );
      })}
      <HandleChip />
      <ProgressBar />
    </AbsoluteFill>
  );
};
