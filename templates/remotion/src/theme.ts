import {Easing} from 'remotion';
import type {Props} from './types';

export const theme = (p: Props) => ({
  primary: p.theme?.primary ?? '#0f7c86',
  deep: p.theme?.deep ?? '#053c42',
  accent: p.theme?.accent ?? '#2dd4bf',
  light: p.theme?.light ?? '#9ccdd4',
  highlight: p.theme?.highlight ?? '#F2A900',
  ground: p.theme?.ground ?? '#ffffff',
  font: '"Be Vietnam Pro", ui-sans-serif, system-ui, sans-serif',
  ease: Easing.bezier(0.4, 0, 0.2, 1),
  pop: Easing.bezier(0.34, 1.56, 0.64, 1),
});
export type Theme = ReturnType<typeof theme>;
