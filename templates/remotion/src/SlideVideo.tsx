import {AbsoluteFill, Audio, Sequence, staticFile} from 'remotion';
import type {Props} from './types';
import {theme as makeTheme} from './theme';
import {useFonts} from './Fonts';
import {SlideScene} from './scenes/SlideScene';
import {SectionCard} from './scenes/SectionCard';
import {HookScene} from './scenes/HookScene';
import {ProductScene} from './scenes/ProductScene';
import {FeatureScene} from './scenes/FeatureScene';
import {SocialProofScene} from './scenes/SocialProofScene';
import {CtaScene} from './scenes/CtaScene';
import {Progress} from './scenes/Progress';

export const SlideVideo = (p: Props) => {
  const t = makeTheme(p);
  useFonts(p.fonts);
  const isVertical = p.height > p.width || p.aspectRatio === '9:16';

  const renderScene = (s: Props['scenes'][0]) => {
    switch (s.kind) {
      case 'hook':
        return <HookScene scene={s} theme={t} isVertical={isVertical} />;
      case 'product':
        return <ProductScene scene={s} theme={t} isVertical={isVertical} />;
      case 'feature':
        return <FeatureScene scene={s} theme={t} isVertical={isVertical} />;
      case 'social_proof':
        return <SocialProofScene scene={s} theme={t} isVertical={isVertical} />;
      case 'cta':
        return <CtaScene scene={s} theme={t} isVertical={isVertical} />;
      case 'section':
        return <SectionCard scene={s} theme={t} />;
      default:
        return <SlideScene scene={s} slideW={p.slideWidth ?? p.width} theme={t} captions={p.captions} />;
    }
  };

  return (
    <AbsoluteFill style={{background: t.ground}}>
      {p.scenes.map((s) => (
        <Sequence key={s.id} from={s.startFrame} durationInFrames={s.frames} premountFor={30}>
          {renderScene(s)}
        </Sequence>
      ))}
      {!isVertical && p.progress && <Progress p={p} theme={t} />}
      {p.bgm && <Audio src={staticFile(p.bgm)} volume={p.bgmVolume ?? 0.14} loop />}
      {p.audio && <Audio src={staticFile(p.audio)} />}
    </AbsoluteFill>
  );
};
