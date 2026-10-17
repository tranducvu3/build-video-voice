export type Box = [number, number, number, number];

export type Beat = {
  startFrame: number; // relative to the scene
  frames: number;
  text: string; // caption text, cues removed
  focus: Box | null; // slide-pixel box the camera frames while this beat is spoken
  callout?: string;
};

export type SceneKind = 'slide' | 'section' | 'hook' | 'product' | 'feature' | 'social_proof' | 'cta';

export type Scene = {
  id: string;
  kind: SceneKind;
  image?: string; // public-dir relative
  video?: string; // public-dir relative video path
  videoDuration?: number;
  startFrame: number;
  frames: number;
  title?: string;
  subtitle?: string;
  badge?: string;
  price?: string;
  originalPrice?: string;
  discount?: string;
  rating?: number;
  reviewsCount?: string;
  soldCount?: string;
  reviewQuote?: string;
  reviewAuthor?: string;
  features?: string[];
  ctaText?: string;
  ctaSubtext?: string;
  ctaTarget?: 'cart' | 'bio' | 'comment' | 'description' | 'link';
  affiliateUrl?: string;
  section?: {n?: number | null; of?: number; title: string; kicker?: string};
  chapter?: number; // index into chapters
  beats: Beat[];
};

export type Face = {family: string; weight: number; url: string; unicodeRange?: string};

export type Props = {
  fps: number;
  width: number;
  height: number;
  slideWidth?: number;
  slideHeight?: number;
  aspectRatio?: '9:16' | '16:9';
  audio?: string;
  bgm?: string;
  bgmVolume?: number;
  captions: boolean;
  progress: boolean;
  theme?: Partial<Record<'primary' | 'deep' | 'accent' | 'highlight' | 'ground' | 'light' | 'shopee' | 'cardBg', string>>;
  fonts?: Face[];
  chapters: {title: string; startFrame: number}[];
  scenes: Scene[];
  totalFrames: number;
  product?: {
    name: string;
    brand?: string;
    affiliateUrl?: string;
    ctaLocation?: string;
  };
};
