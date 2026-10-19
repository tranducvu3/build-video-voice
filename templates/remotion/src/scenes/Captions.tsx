import {interpolate, useCurrentFrame} from 'remotion';
import type {Beat} from '../types';
import type {Theme} from '../theme';

// Sentence-sized pieces of a beat, each shown for its share of the beat's speech.
const pieces = (text: string, isVertical: boolean = false) => {
  const clean = text.replace(/\[[^\]]+\]/g, '').replace(/\s+/g, ' ').trim();
  const maxLen = isVertical ? 46 : 84;
  const out: string[] = [];

  for (let s of clean.split(/(?<=[.!?…])\s+/)) {
    while (s.length > maxLen) {
      let cut = -1;
      const commaCut = Math.max(s.lastIndexOf(', ', maxLen), s.lastIndexOf('; ', maxLen), s.lastIndexOf(' - ', maxLen));
      if (commaCut >= Math.floor(maxLen * 0.35)) {
        cut = commaCut + 1;
      } else {
        cut = s.lastIndexOf(' ', maxLen);
      }
      if (cut <= 0) break;
      out.push(s.slice(0, cut).trim());
      s = s.slice(cut).trim();
    }
    if (s) out.push(s);
  }
  return out;
};

export const Captions = ({beats, theme, isVertical = false}: {beats: Beat[]; theme: Theme; isVertical?: boolean}) => {
  const frame = useCurrentFrame();
  let cue: {text: string; start: number; end: number} | null = null;
  for (const b of beats) {
    const ps = pieces(b.text, isVertical);
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

  const bottomPos = isVertical ? 220 : 54;
  const sideMargin = isVertical ? 40 : 120;
  const fontSize = isVertical ? 36 : 40;

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
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          background: isVertical ? 'rgba(15, 15, 18, 0.94)' : 'rgba(5, 60, 66, 0.92)',
          color: '#ffffff',
          fontFamily: theme.font,
          fontWeight: 700,
          fontSize: fontSize,
          lineHeight: 1.32,
          padding: isVertical ? '12px 28px' : '14px 30px',
          borderRadius: 20,
          maxWidth: isVertical ? 920 : 1500,
          textAlign: 'center',
          boxShadow: '0 16px 40px rgba(0,0,0,0.5)',
          border: isVertical ? '2px solid rgba(255, 215, 0, 0.5)' : 'none',
          textShadow: '0 2px 8px rgba(0,0,0,0.8)',
          textWrap: 'balance' as any,
          wordBreak: 'keep-all' as any,
          overflowWrap: 'break-word',
        }}
      >
        {cue.text}
      </div>
    </div>
  );
};
