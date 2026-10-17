import React from 'react';
import {AbsoluteFill, Img, interpolate, spring, staticFile, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';
import {ShopeeMallBadge, FreeShipBadge} from './Badges';
import {Captions} from './Captions';

export const ProductScene = ({scene, theme, isVertical}: {scene: Scene; theme: Theme; isVertical: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();

  // Entrance animations
  const imgIn = spring({frame, fps, config: {damping: 14, stiffness: 120}});
  const badgesIn = spring({frame: frame - 6, fps, config: {damping: 15, stiffness: 140}});
  const titleIn = spring({frame: frame - 10, fps, config: {damping: 16, stiffness: 130}});
  const priceIn = spring({frame: frame - 14, fps, config: {damping: 12, stiffness: 160}});

  // Floating oscillation
  const t = frame / fps;
  const floatY = Math.sin(t * 2) * 10;
  const zoom = 1 + 0.03 * (frame / Math.max(1, scene.frames));

  const features = scene.features || ['Chính Hãng 100%', 'Bảo Hành 12 Tháng', 'Đổi Trả 15 Ngày'];

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 40%, #1e1e24 0%, #0d0d10 80%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#ffffff',
      }}
    >
      {/* Background soft glow */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? '40%' : '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: isVertical ? 750 : 900,
          height: isVertical ? 750 : 900,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(238, 77, 45, 0.22) 0%, transparent 65%)',
          filter: 'blur(70px)',
          pointerEvents: 'none',
        }}
      />

      {/* Main Content Layout */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? 130 : 60,
          left: 0,
          right: 0,
          bottom: isVertical ? 480 : 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isVertical ? '0 45px' : '0 90px',
        }}
      >
        {/* Top Badges & Title Block */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', width: '100%'}}>
          <div
            style={{
              opacity: badgesIn,
              transform: `scale(${badgesIn})`,
              display: 'flex',
              gap: 12,
              marginBottom: 16,
            }}
          >
            <ShopeeMallBadge scale={isVertical ? 1.4 : 1.2} />
            <FreeShipBadge scale={isVertical ? 1.4 : 1.2} />
          </div>

          <div
            style={{
              opacity: titleIn,
              transform: `translateY(${(1 - titleIn) * 25}px)`,
              fontSize: isVertical ? 48 : 54,
              fontWeight: 800,
              lineHeight: 1.2,
              letterSpacing: '-0.01em',
              maxWidth: isVertical ? 920 : 1200,
              textShadow: '0 2px 16px rgba(0,0,0,0.7)',
            }}
          >
            {scene.title || 'Sản Phẩm Đang Hot Nhất Shopee'}
          </div>
        </div>

        {/* Center: Hero Product Image with 3D Float */}
        {scene.image && (
          <div
            style={{
              opacity: imgIn,
              transform: `scale(${imgIn * zoom}) translateY(${floatY}px)`,
              position: 'relative',
              width: isVertical ? 600 : 560,
              height: isVertical ? 560 : 440,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              background: 'rgba(255, 255, 255, 0.04)',
              borderRadius: 36,
              border: '1.5px solid rgba(255, 255, 255, 0.12)',
              boxShadow: '0 30px 70px rgba(0, 0, 0, 0.65), 0 0 40px rgba(238, 77, 45, 0.15)',
              padding: 24,
            }}
          >
            <Img
              src={staticFile(scene.image)}
              style={{
                width: '100%',
                height: '100%',
                objectFit: 'contain',
                filter: 'drop-shadow(0 20px 30px rgba(0,0,0,0.6))',
              }}
            />

            {/* Discount sticker in corner */}
            {scene.discount && (
              <div
                style={{
                  position: 'absolute',
                  top: 20,
                  right: 20,
                  background: 'linear-gradient(135deg, #d0011b 0%, #ee4d2d 100%)',
                  color: '#ffffff',
                  fontWeight: 900,
                  fontSize: isVertical ? 32 : 28,
                  padding: isVertical ? '10px 22px' : '8px 18px',
                  borderRadius: 20,
                  boxShadow: '0 6px 20px rgba(208, 1, 27, 0.5)',
                  transform: 'rotate(6deg)',
                }}
              >
                {scene.discount}
              </div>
            )}
          </div>
        )}

        {/* Bottom Block: Price and Feature Chips */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', width: '100%'}}>
          {/* Price Tag Bar */}
          {scene.price && (
            <div
              style={{
                opacity: priceIn,
                transform: `scale(${priceIn})`,
                display: 'flex',
                alignItems: 'baseline',
                gap: 16,
                background: 'rgba(0, 0, 0, 0.55)',
                padding: isVertical ? '12px 36px' : '10px 30px',
                borderRadius: 999,
                border: '1.5px solid rgba(238, 77, 45, 0.5)',
                boxShadow: '0 10px 30px rgba(0, 0, 0, 0.4)',
                marginBottom: 20,
              }}
            >
              <span style={{fontSize: isVertical ? 30 : 26, color: '#e0e0e0', fontWeight: 600}}>Giá chỉ:</span>
              <span style={{fontSize: isVertical ? 60 : 52, fontWeight: 900, color: '#ff5722', letterSpacing: '-0.02em'}}>
                {scene.price}
              </span>
              {scene.originalPrice && (
                <span style={{fontSize: isVertical ? 30 : 26, color: '#888899', textDecoration: 'line-through', fontWeight: 500}}>
                  {scene.originalPrice}
                </span>
              )}
            </div>
          )}

          {/* Floating Feature Pills */}
          <div
            style={{
              display: 'flex',
              flexWrap: 'wrap',
              justifyContent: 'center',
              gap: 12,
              maxWidth: isVertical ? 960 : 1200,
            }}
          >
            {features.map((feat, idx) => {
              const chipIn = spring({frame: frame - 16 - idx * 4, fps, config: {damping: 14, stiffness: 140}});
              return (
                <div
                  key={idx}
                  style={{
                    opacity: chipIn,
                    transform: `scale(${chipIn}) translateY(${(1 - chipIn) * 15}px)`,
                    background: 'rgba(255, 255, 255, 0.08)',
                    border: '1px solid rgba(255, 255, 255, 0.2)',
                    color: '#ffffff',
                    fontSize: isVertical ? 26 : 22,
                    fontWeight: 700,
                    padding: isVertical ? '10px 22px' : '8px 18px',
                    borderRadius: 999,
                    backdropFilter: 'blur(10px)',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
                  }}
                >
                  ✓ {feat}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Captions */}
      <Captions beats={scene.beats} theme={theme} isVertical={isVertical} />
    </AbsoluteFill>
  );
};
