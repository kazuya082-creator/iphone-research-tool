import React from "react";
import { Composition } from "remotion";
import { Reel } from "./Reel";
import { TOTAL_FRAMES } from "./script";
import { FPS, HEIGHT, WIDTH } from "./theme";

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Reel"
    component={Reel}
    durationInFrames={TOTAL_FRAMES}
    fps={FPS}
    width={WIDTH}
    height={HEIGHT}
  />
);
