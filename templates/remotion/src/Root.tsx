import {Composition} from 'remotion';
import {SlideVideo} from './SlideVideo';
import type {Props} from './types';

const sample: Props = {
  fps: 30, width: 1920, height: 1080, slideWidth: 1920, slideHeight: 1080,
  captions: true, progress: true, chapters: [], totalFrames: 90,
  scenes: [{id: 'p01', kind: 'section', image: '', startFrame: 0, frames: 90, section: {n: 1, of: 1, title: 'Pass --props=props.json'}, beats: []}],
};

export const RemotionRoot = () => (
  <Composition
    id="Slides"
    component={SlideVideo}
    defaultProps={sample}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={90}
    calculateMetadata={({props}) => ({fps: props.fps, width: props.width, height: props.height, durationInFrames: Math.max(1, props.totalFrames)})}
  />
);
