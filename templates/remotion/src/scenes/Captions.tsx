import {interpolate, useCurrentFrame} from 'remotion';
import type {Beat} from '../types';
import type {Theme} from '../theme';

const MAX = 84;

// Sentence-sized pieces of a beat, each shown for its share of the beat's speech.
const pieces = (text: string) => {
  const out: string[] = [];
  for (let s of text.split(/(?<=[.!?…])\s+/)) {
    while (s.length > MAX) {
      const cut = Math.max(s.lastIndexOf(', ', MAX), s.lastIndexOf(' ', MAX));
      if (cut <= 0) break;
      out.push(s.slice(0, cut + 1).trim());
      s = s.slice(cut + 1).trim();
    }
    if (s) out.push(s);
  }
  return out;
};

export const Captions = ({beats, theme}: {beats: Beat[]; theme: Theme}) => {
  const frame = useCurrentFrame();
  let cue: {text: string; start: number; end: number} | null = null;
  for (const b of beats) {
    const ps = pieces(b.text);
    const total = ps.reduce((n, p) => n + p.length, 0) || 1;
    let t = b.startFrame;
    for (const p of ps) {
      const d = (b.frames * p.length) / total;
      if (frame >= t && frame < t + d + 4) cue = {text: p, start: t, end: t + d};
      t += d;
    }
  }
  if (!cue) return null;
  const o = interpolate(frame, [cue.start, cue.start + 5, cue.end, cue.end + 4], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  return (
    <div style={{position: 'absolute', left: 120, right: 120, bottom: 54, display: 'flex', justifyContent: 'center', opacity: o, transform: `translateY(${(1 - o) * 14}px)`}}>
      <div
        style={{
          background: 'rgba(5,60,66,0.92)',
          color: '#fff',
          fontFamily: theme.font,
          fontWeight: 600,
          fontSize: 40,
          lineHeight: 1.35,
          padding: '14px 30px',
          borderRadius: 16,
          maxWidth: 1500,
          textAlign: 'center',
          boxShadow: '0 12px 30px rgba(0,0,0,0.18)',
        }}
      >
        {cue.text}
      </div>
    </div>
  );
};
