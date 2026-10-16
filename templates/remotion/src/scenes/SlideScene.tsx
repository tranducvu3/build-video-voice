import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Beat, Box, Scene} from '../types';
import type {Theme} from '../theme';
import {Captions} from './Captions';

type Cam = {z: number; cx: number; cy: number; band: number};

const MAX_ZOOM = 2.3;
const MOVE = 22; // frames the camera takes to reach a beat's focus
const LEAD = 8; // the move starts this many frames before the beat's voice
const BAND = 170; // bottom strip kept clear for captions while a focus is framed

const clamp = (v: number, lo: number, hi: number) => Math.min(hi, Math.max(lo, v));

// Frame a focus box with margin; boxes are slide pixels, the camera works in frame pixels.
const target = (focus: Box | null, k: number, W: number, H: number, band: number): Cam => {
  if (!focus) return {z: 1, cx: W / 2, cy: H / 2, band: 0};
  const [x, y, w, h] = focus.map((v) => v * k);
  const z = clamp(Math.min((0.8 * W) / w, (0.78 * (H - band)) / h), 1, MAX_ZOOM);
  return {z, cx: x + w / 2, cy: y + h / 2, band};
};

// Slide image under a camera that glides from one beat's focus to the next, with a slow
// drift while each beat plays, a highlight ring that dims the rest, and a callout chip.
export const SlideScene = ({scene, slideW, theme, captions}: {scene: Scene; slideW: number; theme: Theme; captions: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();
  const k = W / slideW;
  const beats = scene.beats;
  const band = captions ? BAND : 0;
  const cams = beats.map((b) => target(b.focus, k, W, H, band));
  const wide = target(null, k, W, H, 0);

  let i = -1;
  beats.forEach((b, n) => {
    if (frame >= b.startFrame - LEAD) i = n;
  });
  const beat: Beat | undefined = beats[i];
  const from = i > 0 ? cams[i - 1] : wide;
  const to = i >= 0 ? cams[i] : wide;
  const p = i >= 0 ? interpolate(frame, [beat!.startFrame - LEAD, beat!.startFrame - LEAD + MOVE], [0, 1], {easing: theme.ease, extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}) : 0;
  const drift = i >= 0 ? 1 + 0.025 * clamp((frame - beat!.startFrame) / Math.max(1, beat!.frames), 0, 1) : 1;
  const z = Math.exp(Math.log(from.z) + (Math.log(to.z) - Math.log(from.z)) * p) * drift;
  const cx = from.cx + (to.cx - from.cx) * p;
  const cy = from.cy + (to.cy - from.cy) * p;
  const bd = from.band + (to.band - from.band) * p;

  // entrance: settle from a slight over-zoom and blur
  const enter = spring({frame, fps, config: {damping: 200}, durationInFrames: 16});
  const zz = z * (1 + 0.06 * (1 - enter));
  const tx = clamp(W / 2 - cx * zz, W - W * zz, 0);
  // a framed focus sits above the caption strip; the slide may slide up past its bottom edge to get there
  const ty = clamp((H - bd) / 2 - cy * zz, H - H * zz - bd, 0);

  // highlight for the current beat: lands after the camera, leaves before the next move
  const next = beats[i + 1];
  const end = next ? next.startFrame - LEAD : scene.frames;
  const hl = beat?.focus
    ? interpolate(frame, [beat.startFrame - LEAD + MOVE - 6, beat.startFrame - LEAD + MOVE + 4, end - 4, end], [0, 1, 1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 0;
  const ring = beat?.focus ? spring({frame: frame - (beat.startFrame - LEAD + MOVE - 6), fps, config: {damping: 12, stiffness: 160}}) : 0;
  const fb = beat?.focus?.map((v) => v * k);
  const pad = 14;

  // callout chip in screen space, under the box when there is room, else above it
  let chip: {left: number; top: number} | null = null;
  if (fb && beat?.callout) {
    const sx = fb[0] * zz + tx;
    const sy = fb[1] * zz + ty;
    const sh = fb[3] * zz;
    const below = sy + sh + pad * zz + 24;
    chip = {left: clamp(sx, 40, W - 700), top: below + 90 < H - 170 ? below : Math.max(30, sy - pad * zz - 110)};
  }
  const chipIn = beat?.callout ? spring({frame: frame - (beat.startFrame - LEAD + MOVE + 2), fps, config: {damping: 11, stiffness: 170}}) : 0;

  return (
    <AbsoluteFill style={{background: theme.ground, overflow: 'hidden', opacity: interpolate(frame, [0, 6], [0, 1], {extrapolateRight: 'clamp'})}}>
      <div style={{position: 'absolute', width: W, height: H, transformOrigin: '0 0', transform: `translate(${tx}px, ${ty}px) scale(${zz})`, filter: `blur(${(1 - enter) * 6}px)`}}>
        <Img src={staticFile(scene.image)} style={{width: W, height: H, objectFit: 'contain'}} />
        {fb && (
          <div
            style={{
              position: 'absolute',
              left: fb[0] - pad,
              top: fb[1] - pad,
              width: fb[2] + pad * 2,
              height: fb[3] + pad * 2,
              borderRadius: 14 / zz,
              border: `${5 / zz}px solid ${theme.highlight}`,
              opacity: hl,
              transform: `scale(${1.08 - 0.08 * ring})`,
              boxShadow: `0 0 0 ${4000 / zz}px rgba(5,60,66,${0.3 * hl}), 0 0 ${30 / zz}px ${theme.highlight}`,
            }}
          />
        )}
      </div>
      {chip && beat?.callout && (
        <div
          style={{
            position: 'absolute',
            left: chip.left,
            top: chip.top,
            transform: `scale(${chipIn})`,
            transformOrigin: 'left center',
            opacity: Math.min(1, chipIn) * hl,
            background: theme.highlight,
            color: '#1c1917',
            fontFamily: theme.font,
            fontWeight: 700,
            fontSize: 44,
            padding: '16px 28px',
            borderRadius: 999,
            boxShadow: '0 16px 40px rgba(0,0,0,0.25)',
            whiteSpace: 'nowrap',
          }}
        >
          {beat.callout}
        </div>
      )}
      {captions && <Captions beats={beats} theme={theme} />}
    </AbsoluteFill>
  );
};
