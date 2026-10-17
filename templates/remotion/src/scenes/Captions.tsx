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

export const Captions = ({beats, theme, isVertical = false}: {beats: Beat[]; theme: Theme; isVertical?: boolean}) => {
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

  const bottomPos = isVertical ? 240 : 54;
  const sideMargin = isVertical ? 40 : 120;
  const fontSize = isVertical ? 46 : 40;

  return (
    <div
      style={{
        position: 'absolute',
        left: sideMargin,
        right: sideMargin,
        bottom: bottomPos,
        display: 'flex',
        justifyContent: 'center',
        opacity: o,
        transform: `translateY(${(1 - o) * 14}px)`,
        zIndex: 50,
      }}
    >
      <div
        style={{
          background: isVertical ? 'rgba(15, 15, 18, 0.92)' : 'rgba(5, 60, 66, 0.92)',
          color: '#ffffff',
          fontFamily: theme.font,
          fontWeight: 700,
          fontSize: fontSize,
          lineHeight: 1.35,
          padding: isVertical ? '16px 36px' : '14px 30px',
          borderRadius: 20,
          maxWidth: isVertical ? 960 : 1500,
          textAlign: 'center',
          boxShadow: '0 16px 40px rgba(0,0,0,0.4)',
          border: isVertical ? '2px solid rgba(255, 215, 0, 0.4)' : 'none',
          textShadow: '0 2px 8px rgba(0,0,0,0.6)',
        }}
      >
        {cue.text}
      </div>
    </div>
  );
};
