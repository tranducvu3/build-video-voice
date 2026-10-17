import {Easing} from 'remotion';
import type {Props} from './types';

export const theme = (p: Props) => ({
  primary: p.theme?.primary ?? '#ee4d2d',
  deep: p.theme?.deep ?? '#121214',
  accent: p.theme?.accent ?? '#ff6d3b',
  light: p.theme?.light ?? '#ffffff',
  highlight: p.theme?.highlight ?? '#ffd700',
  ground: p.theme?.ground ?? '#18181c',
  shopee: p.theme?.shopee ?? '#ee4d2d',
  cardBg: p.theme?.cardBg ?? 'rgba(30, 30, 36, 0.88)',
  font: '"Be Vietnam Pro", ui-sans-serif, system-ui, sans-serif',
  ease: Easing.bezier(0.4, 0, 0.2, 1),
  pop: Easing.bezier(0.34, 1.56, 0.64, 1),
});
export type Theme = ReturnType<typeof theme>;
