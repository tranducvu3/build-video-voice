import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import type {Scene} from '../types';
import type {Theme} from '../theme';
import {StarRating} from './Badges';
import {Captions} from './Captions';

export const SocialProofScene = ({scene, theme, isVertical}: {scene: Scene; theme: Theme; isVertical: boolean}) => {
  const frame = useCurrentFrame();
  const {width: W, height: H, fps} = useVideoConfig();

  // Entrance animations
  const starsIn = spring({frame, fps, config: {damping: 12, stiffness: 150}});
  const countIn = spring({frame: frame - 6, fps, config: {damping: 14, stiffness: 140}});
  const bubbleIn = spring({frame: frame - 12, fps, config: {damping: 15, stiffness: 120}});
  const trustIn = spring({frame: frame - 18, fps, config: {damping: 16, stiffness: 130}});

  const rating = scene.rating ?? 4.9;
  const soldCount = scene.soldCount || '15.800+';
  const reviewsCount = scene.reviewsCount || '8.2k';
  const quote = scene.reviewQuote || 'Giao hàng siêu nhanh, đóng gói cẩn thận. Dùng cực kỳ thích, đúng chuẩn hàng chính hãng 10/10!';
  const author = scene.reviewAuthor || 'Nguyễn Hoàng *** (Đã mua hàng)';

  return (
    <AbsoluteFill
      style={{
        background: `radial-gradient(circle at 50% 35%, #24161a 0%, #100a0d 80%)`,
        overflow: 'hidden',
        fontFamily: theme.font,
        color: '#ffffff',
      }}
    >
      {/* Background warm glow */}
      <div
        style={{
          position: 'absolute',
          top: isVertical ? '35%' : '40%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: isVertical ? 750 : 900,
          height: isVertical ? 750 : 900,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(255, 215, 0, 0.18) 0%, transparent 65%)',
          filter: 'blur(70px)',
          pointerEvents: 'none',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: isVertical ? 130 : 60,
          left: 0,
          right: 0,
          bottom: isVertical ? 580 : 160,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isVertical ? '0 45px' : '0 90px',
        }}
      >
        {/* Top: Star Rating & Sales Volume */}
        <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center'}}>
          <div
            style={{
              opacity: starsIn,
              transform: `scale(${starsIn})`,
              marginBottom: 16,
            }}
          >
            <StarRating rating={rating} count={`${reviewsCount} đánh giá`} scale={isVertical ? 1.4 : 1.3} />
          </div>

          <div
            style={{
              opacity: countIn,
              transform: `translateY(${(1 - countIn) * 20}px)`,
              fontSize: isVertical ? 42 : 56,
              fontWeight: 900,
              color: '#ffffff',
              letterSpacing: '-0.01em',
              textShadow: '0 4px 20px rgba(0,0,0,0.8)',
            }}
          >
            🔥 ĐÃ BÁN HƠN <span style={{color: '#ff5722'}}>{soldCount}</span> CHIẾC!
          </div>
          <div style={{fontSize: isVertical ? 22 : 24, color: '#e0e0e0', fontWeight: 500, marginTop: 8}}>
            99% khách hàng hài lòng và đánh giá 5 sao
          </div>
        </div>

        {/* Center: Verified Buyer Review Bubble */}
        <div
          style={{
            opacity: bubbleIn,
            transform: `scale(${bubbleIn}) translateY(${(1 - bubbleIn) * 25}px)`,
            background: 'rgba(255, 255, 255, 0.08)',
            border: '2px solid rgba(255, 215, 0, 0.3)',
            borderRadius: 30,
            padding: isVertical ? '18px 24px' : '28px 40px',
            maxWidth: isVertical ? 860 : 1000,
            boxShadow: '0 20px 60px rgba(0,0,0,0.6), 0 0 40px rgba(255,215,0,0.15)',
            backdropFilter: 'blur(20px)',
            position: 'relative',
          }}
        >
          {/* Quote Mark */}
          <div
            style={{
              position: 'absolute',
              top: -24,
              left: 40,
              fontSize: 80,
              lineHeight: 1,
              color: '#ffd700',
              fontFamily: 'serif',
            }}
          >
            “
          </div>

          <div
            style={{
              fontSize: isVertical ? 28 : 32,
              fontWeight: 600,
              lineHeight: 1.4,
              color: '#ffffff',
              marginBottom: 16,
              marginTop: 10,
            }}
          >
            {quote}
          </div>

          <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderTop: '1px solid rgba(255,255,255,0.15)', paddingTop: 16}}>
            <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
              <div
                style={{
                  width: 38,
                  height: 38,
                  borderRadius: '50%',
                  background: 'linear-gradient(135deg, #ff5722 0%, #ffd700 100%)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 800,
                  fontSize: 18,
                  color: '#ffffff',
                }}
              >
                ✓
              </div>
              <div>
                <div style={{fontSize: isVertical ? 24 : 22, fontWeight: 700, color: '#ffffff'}}>{author}</div>
                <div style={{fontSize: isVertical ? 18 : 17, color: '#00bfa5', fontWeight: 600}}>✓ Đã mua hàng từ Shopee Mall</div>
              </div>
            </div>
            <div style={{display: 'flex', gap: 4}}>
              {[1, 2, 3, 4, 5].map((s) => (
                <span key={s} style={{color: '#ffd700', fontSize: 24}}>★</span>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom Trust Badges */}
        <div
          style={{
            opacity: trustIn,
            transform: `translateY(${(1 - trustIn) * 20}px)`,
            display: 'flex',
            gap: 16,
            flexWrap: 'wrap',
            justifyContent: 'center',
          }}
        >
          {['100% Chính Hãng', 'Đổi Trả 15 Ngày Miễn Phí', 'Giao Nhanh 24H'].map((t, idx) => (
            <div
              key={idx}
              style={{
                background: 'rgba(255, 255, 255, 0.08)',
                color: '#ffffff',
                fontSize: isVertical ? 22 : 20,
                fontWeight: 600,
                padding: '8px 20px',
                borderRadius: 999,
                border: '1px solid rgba(255,255,255,0.15)',
              }}
            >
              🛡️ {t}
            </div>
          ))}
        </div>
      </div>

      <Captions beats={scene.beats} theme={theme} isVertical={isVertical} />
    </AbsoluteFill>
  );
};
