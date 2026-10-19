import React from 'react';
import {AbsoluteFill, Img, OffthreadVideo, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';
import {Captions} from './Captions';

export const HookScene = ({scene, theme, isVertical}: {scene: Scene; theme: Theme; isVertical: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();

  // Animations
  const enter = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const badgeIn = spring({frame: frame - 4, fps, config: {damping: 12, stiffness: 150}});
  const textIn = spring({frame: frame - 8, fps, config: {damping: 15, stiffness: 130}});
  const imgIn = spring({frame: frame - 12, fps, config: {damping: 16, stiffness: 110}});

  // Floating gentle drift
  const t = frame / fps;
  const floatY = Math.sin(t * 2.5) * 8;
  const zoom = 1 + 0.04 * (frame / Math.max(1, scene.frames));

  const badgeText = scene.badge || '🔥 CẢNH BÁO CHO TÍN ĐỒ SHOPEE';
  const title = scene.title || 'ĐỪNG VỘI MUA KHI CHƯA XEM!';
  const subtitle = scene.subtitle || 'Bí mật đằng sau chiếc máy đang sốt xình xịch này!';

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 30%, #2a110a 0%, #111114 70%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#ffffff',
      }}
    >
      {/* Background ambient glow */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? '15%' : '10%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: isVertical ? 650 : 800,
          height: isVertical ? 650 : 800,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(238, 77, 45, 0.3) 0%, transparent 70%)',
          filter: 'blur(60px)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Container */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? 110 : 60,
          left: 0,
          right: 0,
          bottom: isVertical ? 430 : 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isVertical ? '0 30px' : '0 80px',
        }}
      >
        {/* Header Block: Badge & Punchy Title */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
          {/* Badge */}
          <div
            style={{
              opacity: badgeIn,
              transform: `scale(${badgeIn}) translateY(${(1 - badgeIn) * 20}px)`,
              background: 'linear-gradient(90deg, #ff5722 0%, #ee4d2d 100%)',
              color: '#ffffff',
              fontWeight: 800,
              fontSize: isVertical ? 26 : 24,
              padding: isVertical ? '10px 26px' : '8px 24px',
              borderRadius: 999,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              boxShadow: '0 8px 24px rgba(238, 77, 45, 0.45)',
              marginBottom: isVertical ? 18 : 16,
            }}
          >
            {badgeText}
          </div>

          {/* Big Hook Title */}
          <div
            style={{
              opacity: textIn,
              transform: `translateY(${(1 - textIn) * 30}px)`,
              fontSize: isVertical ? 52 : 68,
              fontWeight: 900,
              lineHeight: 1.15,
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              color: '#ffffff',
              textShadow: '0 4px 20px rgba(0,0,0,0.8), 0 0 40px rgba(238,77,45,0.4)',
              maxWidth: isVertical ? 960 : 1400,
            }}
          >
            {title}
          </div>

          {subtitle && (
            <div
              style={{
                opacity: textIn,
                transform: `translateY(${(1 - textIn) * 20}px)`,
                fontSize: isVertical ? 26 : 32,
                fontWeight: 600,
                color: theme.highlight,
                marginTop: isVertical ? 12 : 12,
                textShadow: '0 2px 10px rgba(0,0,0,0.6)',
              }}
            >
              {subtitle}
            </div>
          )}
        </div>

        {/* Hero Product Preview Card (Video or Image) */}
        {(scene.video || scene.image) && (
          <div
            style={{
              opacity: imgIn,
              transform: `scale(${imgIn * zoom}) translateY(${floatY}px)`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: isVertical ? 860 : 640,
              height: isVertical ? 820 : 540,
              background: 'rgba(255, 255, 255, 0.05)',
              borderRadius: 40,
              border: '2px solid rgba(238, 77, 45, 0.4)',
              boxShadow: '0 30px 80px rgba(0, 0, 0, 0.75), 0 0 50px rgba(238, 77, 45, 0.3)',
              backdropFilter: 'blur(16px)',
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
      </div>

      {/* Captions */}
      <Captions beats={scene.beats} theme={theme} isVertical={isVertical} />
    </AbsoluteFill>
  );
};
