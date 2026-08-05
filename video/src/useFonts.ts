import { useEffect, useState } from "react";
import { continueRender, delayRender, staticFile } from "remotion";
import { ALL_TEXT } from "./script";

/**
 * public/notosansjp.css（Google Fontsのサブセットをローカルに落としたもの）を読み込み、
 * 実際に使う文字のグリフが揃うまでレンダリングを待たせる。
 * unicode-range で分割されているので document.fonts.load に本文を渡して明示的に取りに行く。
 */
export const useFonts = () => {
  const [handle] = useState(() => delayRender("フォント読み込み"));

  useEffect(() => {
    const link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = staticFile("notosansjp.css");
    document.head.appendChild(link);

    const load = async () => {
      try {
        await Promise.all(
          [400, 700, 900].map((w) =>
            document.fonts.load(`${w} 100px "Noto Sans JP"`, ALL_TEXT),
          ),
        );
        await document.fonts.ready;
      } finally {
        continueRender(handle);
      }
    };

    // link の onload を待ってから font-face を解決する
    link.onload = load;
    link.onerror = () => continueRender(handle);
  }, [handle]);
};
