import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';

// A chapter opener: deep ground, drifting shapes, a big outlined number sliding in, the
// kicker, then the title word by word, and an accent bar that grows under it.
export const SectionCard = ({scene, theme}: {scene: Scene; theme: Theme}) => {
  const frame = useCurrentFrame();
  const {fps, width, durationInFrames} = useVideoConfig();
  const s = scene.section ?? {title: scene.id};
  const num = s.n ? String(s.n).padStart(2, '0') : null;
  const kicker = s.kicker ?? (s.n ? `Phần ${s.n}${s.of ? ` / ${s.of}` : ''}` : '');
  const inN = spring({frame, fps, config: {damping: 16, stiffness: 120}});
  const inK = spring({frame: frame - 6, fps, config: {damping: 200}});
  const bar = spring({frame: frame - 14, fps, config: {damping: 200}, durationInFrames: 20});
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const words = s.title.split(/\s+/);
  const t = frame / fps;

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 75% 40%, ${theme.primary} 0%, ${theme.deep} 62%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#fff',
        opacity: out,
      }}
    >
      <div style={{position: 'absolute', inset: 0, backgroundImage: 'radial-gradient(rgba(255,255,255,0.10) 1.6px, transparent 1.6px)', backgroundSize: '34px 34px', transform: `translateY(${-t * 12}px)`}} />
      <div style={{position: 'absolute', width: 760, height: 760, borderRadius: '50%', right: -120 + Math.sin(t) * 20, top: 120 + Math.cos(t * 0.8) * 20, background: theme.light, opacity: 0.18, transform: `scale(${0.6 + 0.4 * inN})`}} />
      <div style={{position: 'absolute', width: 300, height: 300, borderRadius: 60, right: 520, bottom: -90, background: theme.accent, opacity: 0.16, transform: `rotate(${20 + t * 14}deg) scale(${inN})`}} />
      {num && (
        <div
          style={{
            position: 'absolute',
            right: 150,
            top: 170,
            fontSize: 520,
            fontWeight: 700,
            lineHeight: 1,
            color: 'transparent',
            WebkitTextStroke: `4px rgba(255,255,255,0.55)`,
            transform: `translateX(${(1 - inN) * 300}px)`,
            opacity: inN,
          }}
        >
          {num}
        </div>
      )}
      <div style={{position: 'absolute', left: 170, top: 0, bottom: 0, width: width * 0.62, display: 'flex', flexDirection: 'column', justifyContent: 'center'}}>
        {kicker && (
          <div style={{fontSize: 40, fontWeight: 600, letterSpacing: '0.12em', textTransform: 'uppercase', color: theme.accent, opacity: inK, transform: `translateY(${(1 - inK) * 20}px)`, marginBottom: 26}}>
            {kicker}
          </div>
        )}
        <div style={{fontSize: s.title.length > 34 ? 92 : 116, fontWeight: 700, lineHeight: 1.12}}>
          {words.map((w, n) => {
            const p = spring({frame: frame - 10 - n * 3, fps, config: {damping: 14, stiffness: 140}});
            return (
              <span key={n} style={{display: 'inline-block', marginRight: '0.26em', opacity: Math.min(1, p), transform: `translateY(${(1 - p) * 60}px)`}}>
                {w}
              </span>
            );
          })}
        </div>
        <div style={{height: 12, width: 260 * bar, borderRadius: 6, background: theme.highlight, marginTop: 40}} />
      </div>
    </AbsoluteFill>
  );
};
