import {useEffect, useState} from 'react';
import {cancelRender, continueRender, delayRender, staticFile} from 'remotion';
import type {Face} from './types';

export const useFonts = (faces: Face[] | undefined) => {
  const [handle] = useState(() => delayRender('fonts'));
  useEffect(() => {
    Promise.all(
      (faces ?? []).map((f) =>
        new FontFace(f.family, `url(${staticFile(f.url)}) format('woff2')`, {weight: String(f.weight), ...(f.unicodeRange ? {unicodeRange: f.unicodeRange} : {})})
          .load()
          .then((ff) => document.fonts.add(ff)),
      ),
    )
      .then(() => continueRender(handle))
      .catch((e) => cancelRender(e));
  }, [faces, handle]);
};
