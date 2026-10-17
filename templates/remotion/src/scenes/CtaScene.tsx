import React from 'react';
import {AbsoluteFill, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';
import {ShopeeBagIcon, BouncingArrow} from './Badges';
import {Captions} from './Captions';

export const CtaScene = ({scene, theme, isVertical}: {scene: Scene; theme: Theme; isVertical: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();

  // Animations
  const bagIn = spring({frame, fps, config: {damping: 12, stiffness: 140}});
  const titleIn = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 130}});
  const btnIn = spring({frame: frame - 12, fps, config: {damping: 11, stiffness: 160}});
  const urgencyIn = spring({frame: frame - 18, fps, config: {damping: 15, stiffness: 130}});

  const ctaTarget = scene.ctaTarget || 'cart';
  let targetText = '👉 BẤM VÀO GIỎ HÀNG GÓC TRÁI ĐỂ SĂN DEAL!';
  let arrowDir: 'down' | 'left' | 'down-left' = 'down-left';

  if (ctaTarget === 'bio') {
    targetText = '👉 BẤM VÀO LINK TRONG BIO / TRANG CÁ NHÂN NHA!';
    arrowDir = 'down';
  } else if (ctaTarget === 'comment') {
    targetText = '👉 LINK MUA CHÍNH HÃNG Ở BÌNH LUẬN ĐẦU TIÊN!';
    arrowDir = 'down';
  } else if (ctaTarget === 'description') {
    targetText = '👉 LINK MUA CHÍNH HÃNG KÈM VOUCHER Ở MÔ TẢ!';
    arrowDir = 'down';
  }

  const ctaText = scene.ctaText || 'SĂN DEAL CHÍNH HÃNG NGAY!';

  return (
    <AbsoluteFill
      style={{
        background: `linear-gradient(135deg, #ff5722 0%, #ee4d2d 50%, #b71c1c 100%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#ffffff',
      }}
    >
      {/* Decorative radial circles */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          backgroundImage: 'radial-gradient(rgba(255,255,255,0.15) 2px, transparent 2px)',
          backgroundSize: '40px 40px',
          opacity: 0.7,
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: isVertical ? 140 : 70,
          left: 0,
          right: 0,
          bottom: isVertical ? 580 : 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isVertical ? '0 50px' : '0 100px',
        }}
      >
        {/* Top: Shopee Shopping Bag & Floating Vouchers */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', position: 'relative'}}>
          <div
            style={{
              opacity: bagIn,
              transform: `scale(${bagIn})`,
            }}
          >
            <ShopeeBagIcon size={isVertical ? 140 : 140} />
          </div>

          {/* Floating Voucher Badges */}
          <div
            style={{
              position: 'absolute',
              top: 20,
              left: isVertical ? -90 : -140,
              background: '#ffd700',
              color: '#d0011b',
              fontWeight: 900,
              fontSize: isVertical ? 22 : 20,
              padding: '8px 18px',
              borderRadius: 12,
              boxShadow: '0 8px 20px rgba(0,0,0,0.3)',
              transform: 'rotate(-12deg)',
            }}
          >
            VOUCHER 50K
          </div>

          <div
            style={{
              position: 'absolute',
              top: 40,
              right: isVertical ? -90 : -140,
              background: '#00bfa5',
              color: '#ffffff',
              fontWeight: 900,
              fontSize: isVertical ? 22 : 20,
              padding: '8px 18px',
              borderRadius: 12,
              boxShadow: '0 8px 20px rgba(0,0,0,0.3)',
              transform: 'rotate(10deg)',
            }}
          >
            FREESHIP 0Đ
          </div>
        </div>

        {/* Center: Main CTA Headline & Direction */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
          <div
            style={{
              opacity: titleIn,
              transform: `translateY(${(1 - titleIn) * 30}px)`,
              fontSize: isVertical ? 50 : 64,
              fontWeight: 900,
              lineHeight: 1.15,
              textTransform: 'uppercase',
              letterSpacing: '-0.02em',
              textShadow: '0 6px 30px rgba(0,0,0,0.6)',
              marginBottom: 16,
            }}
          >
            {ctaText}
          </div>

          {/* Big Clickable-style Button */}
          <div
            style={{
              opacity: btnIn,
              transform: `scale(${btnIn})`,
              background: '#ffd700',
              color: '#1a1a1a',
              fontSize: isVertical ? 34 : 38,
              fontWeight: 900,
              padding: isVertical ? '16px 40px' : '18px 44px',
              borderRadius: 999,
              boxShadow: '0 16px 45px rgba(0, 0, 0, 0.45), 0 0 40px rgba(255, 215, 0, 0.6)',
              letterSpacing: '0.02em',
              display: 'flex',
              alignItems: 'center',
              gap: 16,
            }}
          >
            <span>MUA NGAY TRÊN SHOPEE</span>
            <span>⚡</span>
          </div>

          {/* Where to click text */}
          <div
            style={{
              marginTop: isVertical ? 18 : 28,
              fontSize: isVertical ? 26 : 30,
              fontWeight: 800,
              color: '#ffffff',
              textShadow: '0 2px 14px rgba(0,0,0,0.8)',
              background: 'rgba(0, 0, 0, 0.4)',
              padding: isVertical ? '10px 24px' : '12px 28px',
              borderRadius: 20,
              backdropFilter: 'blur(8px)',
            }}
          >
            {targetText}
          </div>
        </div>

        {/* Bottom: Urgency Alert */}
        <div
          style={{
            opacity: urgencyIn,
            transform: `translateY(${(1 - urgencyIn) * 20}px)`,
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'rgba(0, 0, 0, 0.5)',
            border: '1.5px solid rgba(255, 215, 0, 0.6)',
            padding: isVertical ? '14px 32px' : '10px 24px',
            borderRadius: 999,
            fontSize: isVertical ? 26 : 22,
            fontWeight: 800,
            color: '#ffd700',
            boxShadow: '0 10px 30px rgba(0,0,0,0.3)',
          }}
        >
          <span>🔥</span>
          <span>SỐ LƯỢNG VOUCHER CÓ HẠN - NHANH TAY KẺO HẾT!</span>
        </div>
      </div>

      {/* If pointing to cart at bottom-left in vertical format, render bouncing arrow */}
      {isVertical && ctaTarget === 'cart' && (
        <div style={{position: 'absolute', bottom: 120, left: 50, zIndex: 100}}>
          <BouncingArrow direction="down-left" scale={1.8} />
        </div>
      )}

      <Captions beats={scene.beats} theme={theme} isVertical={isVertical} />
    </AbsoluteFill>
  );
};
