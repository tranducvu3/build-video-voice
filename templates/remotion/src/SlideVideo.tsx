import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import type {Props} from './types';
import {theme as makeTheme} from './theme';
import {useFonts} from './Fonts';
import {SlideScene} from './scenes/SlideScene';
import {SectionCard} from './scenes/SectionCard';
import {Progress} from './scenes/Progress';

export const SlideVideo = (p: Props) => {
  const t = makeTheme(p);
  useFonts(p.fonts);
  return (
    <AbsoluteFill style={{background: t.ground}}>
      {p.scenes.map((s) => (
        <Sequence key={s.id} from={s.startFrame} durationInFrames={s.frames} premountFor={30}>
          {s.kind === 'section' ? <SectionCard scene={s} theme={t} /> : <SlideScene scene={s} slideW={p.slideWidth} theme={t} captions={p.captions} />}
        </Sequence>
      ))}
      {p.progress && <Progress p={p} theme={t} />}
      {p.audio && <Audio src={staticFile(p.audio)} />}
    </AbsoluteFill>
  );
};
