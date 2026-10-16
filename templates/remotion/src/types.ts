export type Box = [number, number, number, number];

export type Beat = {
  startFrame: number; // relative to the scene
  frames: number;
  text: string; // caption text, cues removed
  focus: Box | null; // slide-pixel box the camera frames while this beat is spoken
  callout?: string;
};

export type Scene = {
  id: string;
  kind: 'slide' | 'section';
  image: string; // public-dir relative
  startFrame: number;
  frames: number;
  section?: {n?: number | null; of?: number; title: string; kicker?: string};
  chapter?: number; // index into chapters
  beats: Beat[];
};

export type Face = {family: string; weight: number; url: string; unicodeRange?: string};

export type Props = {
  fps: number;
  width: number;
  height: number;
  slideWidth: number;
  slideHeight: number;
  audio?: string;
  captions: boolean;
  progress: boolean;
  theme?: Partial<Record<'primary' | 'deep' | 'accent' | 'highlight' | 'ground' | 'light', string>>;
  fonts?: Face[];
  chapters: {title: string; startFrame: number}[];
  scenes: Scene[];
  totalFrames: number;
};
