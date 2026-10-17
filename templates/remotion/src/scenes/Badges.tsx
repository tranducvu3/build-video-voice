import React from 'react';
import {spring, useCurrentFrame, useVideoConfig} from 'remotion';

// Official Shopee Mall Badge
export const ShopeeMallBadge = ({scale = 1}: {scale?: number}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6 * scale,
      background: '#d0011b',
      color: '#ffffff',
      padding: `${4 * scale}px ${10 * scale}px`,
      borderRadius: 4 * scale,
      fontWeight: 800,
      fontSize: 14 * scale,
      letterSpacing: '0.04em',
      textTransform: 'uppercase',
      boxShadow: '0 2px 8px rgba(208, 1, 27, 0.4)',
    }}
  >
    <svg width={14 * scale} height={14 * scale} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2L1 7v2h22V7L12 2zm-8 8v9h3v-9H4zm6 0v9h3v-9h-3zm6 0v9h3v-9h-3zM1 21v2h22v-2H1z" />
    </svg>
    Mall
  </div>
);

// FreeShip Xtra Badge
export const FreeShipBadge = ({scale = 1}: {scale?: number}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6 * scale,
      background: 'linear-gradient(135deg, #00bfa5 0%, #00897b 100%)',
      color: '#ffffff',
      padding: `${4 * scale}px ${10 * scale}px`,
      borderRadius: 4 * scale,
      fontWeight: 800,
      fontSize: 13 * scale,
      letterSpacing: '0.02em',
      boxShadow: '0 2px 8px rgba(0, 191, 165, 0.35)',
    }}
  >
    <svg width={15 * scale} height={15 * scale} viewBox="0 0 24 24" fill="currentColor">
      <path d="M20 8h-3V4H3c-1.1 0-2 .9-2 2v11h2c0 1.66 1.34 3 3 3s3-1.34 3-3h6c0 1.66 1.34 3 3 3s3-1.34 3-3h2v-5l-3-4zM6 18.5c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5zm13.5-9l1.96 2.5H17V9.5h2.5zm-1.5 9c-.83 0-1.5-.67-1.5-1.5s.67-1.5 1.5-1.5 1.5.67 1.5 1.5-.67 1.5-1.5 1.5z" />
    </svg>
    Freeship Xtra
  </div>
);

// Star Rating Component
export const StarRating = ({rating = 4.9, count = '10k+', scale = 1}: {rating?: number; count?: string; scale?: number}) => (
  <div
    style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: 6 * scale,
      background: 'rgba(0,0,0,0.4)',
      padding: `${6 * scale}px ${14 * scale}px`,
      borderRadius: 999,
      backdropFilter: 'blur(8px)',
      border: '1px solid rgba(255,255,255,0.15)',
    }}
  >
    <div style={{display: 'flex', gap: 2 * scale}}>
      {[1, 2, 3, 4, 5].map((i) => (
        <svg key={i} width={18 * scale} height={18 * scale} viewBox="0 0 24 24" fill="#ffd700">
          <path d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z" />
        </svg>
      ))}
    </div>
    <span style={{color: '#ffd700', fontWeight: 800, fontSize: 18 * scale}}>{rating.toFixed(1)}</span>
    <span style={{color: '#ffffff', opacity: 0.85, fontSize: 15 * scale, fontWeight: 500}}>({count})</span>
  </div>
);

// Shopee Shopping Bag Icon
export const ShopeeBagIcon = ({size = 120}: {size?: number}) => (
  <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
    <defs>
      <linearGradient id="shopeeBagGrad" x1="0" y1="0" x2="100" y2="100" gradientUnits="userSpaceOnUse">
        <stop stopColor="#ff5722" />
        <stop offset="1" stopColor="#d0011b" />
      </linearGradient>
      <filter id="bagGlow" x="-20%" y="-20%" width="140%" height="140%">
        <feDropShadow dx="0" dy="8" stdDeviation="12" floodColor="#ee4d2d" floodOpacity="0.5" />
      </filter>
    </defs>
    <rect x="18" y="32" width="64" height="58" rx="14" fill="url(#shopeeBagGrad)" filter="url(#bagGlow)" />
    <path d="M34 34V24C34 15.1634 41.1634 8 50 8C58.8366 8 66 15.1634 66 24V34" stroke="#ffffff" strokeWidth="6" strokeLinecap="round" />
    {/* Shopee 'S' mark in bag */}
    <path
      d="M56 46C56 44 54 43 51 43H47C44.5 43 43 44.5 43 47C43 49.5 45 51 48 52L52 53.5C56 55 58 57.5 58 61C58 65 54.5 67 50 67C45 67 42 65 42 61M50 40V43M50 67V70"
      stroke="#ffffff"
      strokeWidth="4"
      strokeLinecap="round"
      strokeLinejoin="round"
    />
  </svg>
);

// Bouncing CTA Pointer Arrow
export const BouncingArrow = ({direction = 'down', scale = 1}: {direction?: 'down' | 'left' | 'down-left'; scale?: number}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const bounce = Math.sin((frame / fps) * 6) * 12 * scale;

  let rotate = '0deg';
  if (direction === 'left') rotate = '90deg';
  if (direction === 'down-left') rotate = '45deg';

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        transform: `translateY(${bounce}px) rotate(${rotate})`,
        filter: 'drop-shadow(0 4px 10px rgba(0,0,0,0.4))',
      }}
    >
      <svg width={48 * scale} height={48 * scale} viewBox="0 0 24 24" fill="#ffd700">
        <path d="M12 4l-1.41 1.41L16.17 11H4v2h12.17l-5.58 5.59L12 20l8-8z" transform="rotate(90 12 12)" />
      </svg>
    </div>
  );
};
