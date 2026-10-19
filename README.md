# build-video-voice

An AI skill (`/build-video-voice`) that transforms **e-commerce products (Shopee Affiliate)** or **slide decks (PDF, PPTX, HTML)** into animated, high-converting videos with lively spoken Vietnamese narration, powered locally by [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo and rendered with Remotion.

---

## 🌟 What It Does

### 1. 🛍️ Shopee Affiliate & Product Review Videos (NEW!)
- **Product Search & Asset Downloader**: Enter any product keyword or Shopee link (`https://shopee.vn/...` or `https://s.shopee.vn/...`). The tool searches specs, pros, customer reviews, and downloads official high-res product photos from Shopee CDN (`*.susercontent.com`).
- **Proven High-Converting Affiliate Formula**: Automatically generates an engaging storyboard and script:
  1. `hook`: First 3-second scroll stopper with curiosity/warning badge (`🔥 CẢNH BÁO CHO TÍN ĐỒ SHOPEE`).
  2. `product`: Hero showcase with Shopee Mall & Freeship Xtra badges, strikethrough original price, sale price, and animated `-35%` discount pill.
  3. `feature`: Killer benefit spotlight and value proposition.
  4. `feature`: Secondary everyday convenience.
  5. `social_proof`: ⭐⭐⭐⭐⭐ 4.9/5.0 stars, `15.800+ Đã Bán`, and verified buyer review card.
  6. `cta`: Shopee Orange closer, floating vouchers (`VOUCHER 50K`, `FREESHIP 0Đ`), and animated bouncing arrow pointing directly to the cart / bio affiliate link.
- **9:16 Vertical Mobile Format (1080×1920)**: Built specifically for TikTok, Shopee Video, Facebook Reels, and YouTube Shorts (or 16:9 for landscape) with high-impact, enlarged product cards.
- **Dynamic Background Music (BGM)**: Built-in library of royalty-free cheerful & upbeat tracks (`happy`, `fun`, `carefree`, `upbeat`, etc.) automatically mixed, ducked under speech, and dynamically varied across videos so each review video gets a unique sound.
- **Smart Balanced Subtitles**: Intelligently synchronized with natural speech pauses, balanced line wraps (`text-wrap: balance`), clean 4D/product specs formatting, and zero orphan single words.
- **Copy-Paste Social Post**: Writes `affiliate_post.md` with viral caption, hashtags, and your Shopee affiliate link.

### 2. 📊 Slide Deck Explainer Videos
- **Multi-format Ingest**: PDF, PowerPoint/Keynote/ODP (via LibreOffice), HTML keynotes (headless Chrome), or images folder.
- **Region Detection**: Automatically detects bounding boxes for diagrams, images, and text.
- **Camera Movement**: Zooms into whatever is being explained with highlight rings and callout chips.

### 3. 🎙️ 100% Local & Fast Voice (VieNeu-TTS)
- Runs locally on GPU (NVIDIA CUDA / Apple MPS) or CPU.
- Zero API key required, zero data leaves your machine.
- Natural Vietnamese voices: **Trúc Ly** (high-energy affiliate creator), **Ngọc Huyền** (friendly female), **Hải Đăng** (tech reviewer male), and **Quốc Tuấn** (warm male).
- Full pronunciation lexicon for acronyms ("Type-C", "RGB", "GB", "Shopee" → "sô pi") and prices ("890k" → "tám trăm chín mươi cành").

---

## 🚀 Quick Start

### Create a Shopee Affiliate Video in 3 Steps:

```bash
# 1. Search product, download high-res images, and create project
python3 scripts/product.py create "Bàn phím cơ Aula F75" \
  --format 9:16 \
  --price "890.000₫" \
  --original-price "1.350.000₫" \
  --discount "-34%" \
  --affiliate-url "https://s.shopee.vn/YOUR_AFFILIATE_LINK" \
  --cta-location cart

# 2. Speak narration (takes ~15-20s on GPU)
~/.local/share/build-video-voice/voice/.venv/bin/python scripts/voice.py generate aula-f75-affiliate-video --voice "Trúc Ly"

# 3. Render 1080x1920 MP4 with upbeat music
python3 scripts/slides.py render aula-f75-affiliate-video --out out/aula-f75.mp4 --bgm upbeat
```

---

## 📦 Scripts Overview

- `scripts/product.py create|search|fetch`: Product search, Shopee image download, affiliate script generation, and social post caption.
- `scripts/voice.py draft|generate`: VieNeu-TTS local speech synthesis with custom voice, speed, and pronunciation lexicon.
- `scripts/slides.py ingest|regions|render`: Remotion video rendering with support for 9:16 vertical and 16:9 horizontal, BGM audio mixing, and subtitle generation.
- `scripts/setup-voice.sh`: One-time local voice environment setup.
- `scripts/setup-renderer.sh`: One-time Remotion renderer setup.

---

## 🛠️ Requirements

- `ffmpeg`, `ffprobe`, Python 3.10+
- `uv` (installs the voice engine into `~/.local/share/build-video-voice/voice`)
- Node 20+ (Remotion renderer in `~/.local/share/build-video-voice/renderer`)
- Optional: LibreOffice for `.pptx/.key` decks, Poppler for PDF decks.
