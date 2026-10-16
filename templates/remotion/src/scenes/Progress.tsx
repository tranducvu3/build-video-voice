import {interpolate, useCurrentFrame} from 'remotion';
import type {Props} from '../types';
import type {Theme} from '../theme';

// Chapter bar along the top plus the current chapter's name, shown over slide scenes only.
export const Progress = ({p, theme}: {p: Props; theme: Theme}) => {
  const frame = useCurrentFrame();
  const scene = p.scenes.find((s) => frame >= s.startFrame && frame < s.startFrame + s.frames);
  if (!scene || scene.kind === 'section' || scene.chapter == null || !p.chapters.length) return null;
  const ch = p.chapters;
  const first = ch[0].startFrame;
  const span = p.totalFrames - first;
  const show = interpolate(frame - scene.startFrame, [0, 10], [0, 1], {extrapolateRight: 'clamp'});
  return (
    <>
      <div style={{position: 'absolute', top: 0, left: 0, right: 0, height: 10, display: 'flex', gap: 6, opacity: show}}>
        {ch.map((c, i) => {
          const end = ch[i + 1]?.startFrame ?? p.totalFrames;
          const fill = Math.min(1, Math.max(0, (frame - c.startFrame) / (end - c.startFrame)));
          return (
            <div key={i} style={{flex: (end - c.startFrame) / span, background: 'rgba(5,60,66,0.18)', overflow: 'hidden'}}>
              <div style={{height: '100%', width: `${fill * 100}%`, background: theme.highlight}} />
            </div>
          );
        })}
      </div>
      <div
        style={{
          position: 'absolute',
          top: 28,
          right: 36,
          opacity: show,
          background: 'rgba(5,60,66,0.88)',
          color: '#fff',
          fontFamily: theme.font,
          fontSize: 26,
          fontWeight: 600,
          padding: '8px 18px',
          borderRadius: 999,
        }}
      >
        <span style={{color: theme.accent}}>{String(scene.chapter + 1).padStart(2, '0')}</span>&nbsp;&nbsp;{ch[scene.chapter].title}
      </div>
    </>
  );
};
