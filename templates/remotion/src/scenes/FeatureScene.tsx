import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';
import {Captions} from './Captions';

export const FeatureScene = ({scene, theme, isVertical}: {scene: Scene; theme: Theme; isVertical: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();

  // Animations
  const imgIn = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const cardIn = spring({frame: frame - 8, fps, config: {damping: 14, stiffness: 130}});
  const chipIn = spring({frame: frame - 14, fps, config: {damping: 12, stiffness: 150}});

  const t = frame / fps;
  const zoom = 1 + 0.04 * (frame / Math.max(1, scene.frames));

  const title = scene.title || 'Điểm Cộng Đáng Tiền Nhất';
  const subtitle = scene.subtitle || 'Trải nghiệm đỉnh cao, tối ưu từng chi tiết!';
  const callout = scene.beats[0]?.callout || scene.badge || 'Đột Phá';

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 60% 40%, #171d2b 0%, #0d0f15 80%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#ffffff',
      }}
    >
      {/* Background cyan/accent glow */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? '35%' : '45%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: isVertical ? 750 : 900,
          height: isVertical ? 750 : 900,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(45, 212, 191, 0.2) 0%, transparent 65%)',
          filter: 'blur(70px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: isVertical ? 110 : 60,
          left: 0,
          right: 0,
          bottom: isVertical ? 440 : 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isVertical ? '0 30px' : '0 90px',
        }}
      >
        {/* Top Callout Badge */}
        <div
          style={{
            opacity: chipIn,
            transform: `scale(${chipIn}) translateY(${(1 - chipIn) * 20}px)`,
            background: 'linear-gradient(90deg, #2dd4bf 0%, #0f7c86 100%)',
            color: '#ffffff',
            fontWeight: 800,
            fontSize: isVertical ? 26 : 22,
            padding: isVertical ? '10px 28px' : '8px 22px',
            borderRadius: 999,
            letterSpacing: '0.04em',
            textTransform: 'uppercase',
            boxShadow: '0 8px 25px rgba(45, 212, 191, 0.4)',
          }}
        >
          ✦ {callout}
        </div>

        {/* Center: High-Res Feature Visual (Video or Image) */}
        {(scene.video || scene.image) && (
          <div
            style={{
              opacity: imgIn,
              transform: `scale(${imgIn * zoom})`,
              width: isVertical ? 900 : 640,
              height: isVertical ? 880 : 500,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.04)',
              borderRadius: 40,
              border: '2px solid rgba(45, 212, 191, 0.35)',
              boxShadow: '0 30px 80px rgba(0, 0, 0, 0.75), 0 0 50px rgba(45, 212, 191, 0.25)',
              overflow: 'hidden',
              padding: scene.video ? 0 : 16,
            }}
          >
            {scene.video ? (
              <OffthreadVideo
                src={staticFile(scene.video)}
                volume={0}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'cover',
                  borderRadius: 40,
                }}
              />
            ) : (
              <Img
                src={staticFile(scene.image!)}
                style={{
                  width: '100%',
                  height: '100%',
                  objectFit: 'contain',
                  filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.6))',
                }}
              />
            )}
          </div>
        )}

        {/* Bottom Feature Card */}
        <div
          style={{
            opacity: cardIn,
            transform: `translateY(${(1 - cardIn) * 30}px)`,
            background: 'rgba(20, 24, 33, 0.88)',
            border: '1.5px solid rgba(255, 255, 255, 0.18)',
            borderRadius: 30,
            padding: isVertical ? '18px 32px' : '20px 32px',
            textAlign: 'center',
            maxWidth: isVertical ? 960 : 1100,
            boxShadow: '0 20px 50px rgba(0,0,0,0.6)',
            backdropFilter: 'blur(16px)',
          }}
        >
          <div style={{fontSize: isVertical ? 40 : 44, fontWeight: 800, color: '#ffffff', marginBottom: 6}}>
            {title}
          </div>
          <div style={{fontSize: isVertical ? 25 : 26, color: '#9ccdd4', fontWeight: 500, lineHeight: 1.35}}>
            {subtitle}
          </div>
        </div>
      </div>

      <Captions beats={scene.beats} theme={theme} isVertical={isVertical} />
    </AbsoluteFill>
  );
};
