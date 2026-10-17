---
name: build-video-voice
description: Turn an existing slide deck (PDF, PowerPoint/Keynote/ODP, HTML, or images) OR an e-commerce product (Shopee URL or product keyword) into an animated MP4 with a lively spoken voice-over, generated locally by VieNeu-TTS and rendered with Remotion. For Shopee affiliate videos: searches product info & specs, downloads high-res Shopee CDN images, generates high-converting affiliate scripts (Hook -> Showcase -> Features -> Social Proof -> Urgency -> CTA), renders 9:16 vertical (1080x1920) or 16:9 with badges, dynamic captions, and upbeat background music, plus ready-to-copy social post captions with hashtags. Use when the user asks to "tạo video affiliate", "video review sản phẩm Shopee", "tạo video giới thiệu sản phẩm", "make video from product", "make video from slides", "thuyết minh cho slide", or invokes /build-video-voice.
argument-hint: "[product <name-or-url> | <deck-path>] [--out DIR] [--format 9:16|16:9] [--affiliate-url URL] [--cta-location cart|bio|comment] [--device auto|cpu|gpu] [--voice NAME]"
user_invocable: true
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
---

# Video & Voice Generator: Affiliate Products & Slide Decks

```bash
SKILL_DIR="${CLAUDE_SKILL_DIR:-$HOME/.gemini/config/skills/build-video-voice}"
P="$SKILL_DIR/scripts"; VD="${XDG_DATA_HOME:-$HOME/.local/share}/build-video-voice/voice"; PY="$VD/.venv/bin/python"
```

This skill supports two powerful modes:
- **Mode A: Shopee Affiliate & Product Video (`product`)**: Product name or Shopee link → auto-search & download high-res images → high-converting affiliate script → 9:16 vertical video with Shopee badges, animated CTA, and background music.
- **Mode B: Slide Deck Video (`deck`)**: Existing presentation (PDF, PPTX, HTML, images) → region detection → beats narration → 16:9 animated video.

The engine is [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo (Apache-2.0), running locally on GPU (CUDA / Apple MPS) or CPU. No API key needed, no data leaves the machine.

---

## 1. Environment & Setup (Install once)

```bash
bash "$P/setup-voice.sh" "$VD"
bash "$P/setup-renderer.sh" "$SKILL_DIR" "${XDG_DATA_HOME:-$HOME/.local/share}/build-video-voice/renderer"
```
- Voice uses `uv` with PyTorch (GPU CUDA/MPS) or ONNX Runtime (CPU).
- Renderer is Remotion (Node 20+). Setup runs once and is shared across projects.

---

## 2A. MODE A: Shopee Affiliate Product Video

Use when the user provides a product name, keyword, or Shopee link (e.g. `https://shopee.vn/...` or `https://s.shopee.vn/...`).

### Step 1: Ingest product info, images & create project
```bash
python3 -I "$P/product.py" create "<product-name-or-url>" \
  [--out DIR] \
  [--format 9:16|16:9] \
  [--affiliate-url "https://s.shopee.vn/..."] \
  [--cta-location cart|bio|comment|description] \
  [--video "<video-url-or-file>"] \
  [--price "790.000₫"] [--original-price "1.200.000₫"] [--discount "-35%"] \
  [--voice "Trúc Ly"|"Hải Đăng"] [--speed 1.12] [--bgm upbeat|off]
```
- **9:16 Vertical (1080×1920)** is the default and recommended format for TikTok, Shopee Video, Facebook Reels, and YouTube Shorts.
- **Auto-Search**: Gathers specs, pros/cons, user reviews, and pricing.
- **Asset Downloader**: Downloads high-res product photos from Shopee CDN (`*.susercontent.com`) into `$DIR/slides/01.png`, `02.png`, etc.
- **Product Video Reuse (Show Once Only)**: If the product has a video on Shopee (VOD CDN or `video_info_list`), it automatically detects and downloads it, strips the original audio (`ffmpeg -an`) to prevent clash with narration/BGM, and displays it **exactly once** in the main `product` hero showcase scene. The video is never repeated across multiple scenes or looped unnecessarily, keeping visual engagement fresh and avoiding repetitive footage. Subsequent feature scenes use high-res graphic slides. Can also be provided manually via `--video <url-or-path>`.
- **Affiliate Scenes Formula**:
  1. `hook`: Scroll-stopping question/warning (`🔥 CẢNH BÁO CHO TÍN ĐỒ SHOPEE`, `ĐỪNG VỘI MUA... KHI CHƯA XEM HẾT!`).
  2. `product`: Hero showcase with Shopee Mall & Freeship Xtra badges, live product demonstration video (shown once), price tag, discount pill (`-35%`), and feature tags.
  3. `feature`: Killer benefit spotlight with high-res zoom visual and value proposition.
  4. `feature`: Secondary benefit / everyday convenience.
  5. `social_proof`: ⭐⭐⭐⭐⭐ 4.9/5.0 stars, `15.800+ Đã Bán`, and verified buyer review bubble.
  6. `cta`: Shopee Orange closer, animated bouncing arrow pointing to the affiliate link/cart, voucher reminders (`Voucher 50k`, `Freeship 0đ`), and urgency callout.
- **Social Post**: Writes `$DIR/affiliate_post.md` with viral caption, hashtags (`#ShopeeAffiliate`, `#GocReview`), and the user's affiliate link.

### Step 2: Review script & beats
Check `$DIR/voice/script.json`. The copy is pre-tuned for high conversion with natural conversational Vietnamese and full pronunciation `lexicon` for prices ("890k" → "tám trăm chín mươi cành"), brand names, and abbreviations ("Type-C", "RGB", "Shopee" → "sô pi").
Show the user the draft script and voice, and confirm before speaking.

### Step 3: Speak narration
```bash
"$PY" "$P/voice.py" generate "$DIR" [--device auto|cpu|gpu] [--voice "Trúc Ly"] [--speed 1.12]
```
- Recommended voices for affiliate: **Trúc Ly** (energetic, persuasive female affiliate creator), **Ngọc Huyền** (warm friendly female), or **Hải Đăng** (tech reviewer male).
- Speed default: `1.12` to `1.15` for fast-paced mobile engagement.

### Step 4: Render Video
```bash
# Fast draft preview
python3 -I "$P/slides.py" render "$DIR" --draft

# Final 1080x1920 video with background music
python3 -I "$P/slides.py" render "$DIR" --out "<dest>/<product>-affiliate.mp4" --bgm upbeat
```
- Outputs crisp MP4 with floating 3D badges, glowing effects, CapCut/TikTok style dynamic captions, and ducked upbeat background music.
- Give the user the final MP4 path and the contents of `$DIR/affiliate_post.md` ready to copy-paste!

---

## 2B. MODE B: Slide Deck Video (PDF / PPTX / HTML / Images)

Use when the user provides an existing presentation file or images folder.

### Step 1: Export slides and find regions
```bash
python3 -I "$P/slides.py" ingest "<deck>" [--out DIR]
python3 -I "$P/slides.py" regions "$DIR"
```
- Exports `slides/NN.png` (1920×1080) and detects bounding boxes (`r1`, `r2`, …) for images and text.

### Step 2: Draft script
```bash
"$PY" "$P/voice.py" draft "$DIR"
```
- Rewrite `$DIR/voice/script.json` into 1–4 beats per slide (`focus`, `callout`).
- Default voice: **Hải Đăng** (male) or **Trúc Ly** (female).

### Step 3: Speak & Render
```bash
"$PY" "$P/voice.py" generate "$DIR"
python3 -I "$P/slides.py" render "$DIR" --out "<dest>/<deck>-voice.mp4"
```

---

## Key Best Practices for High-Converting Shopee Affiliate Videos

1. **First 3 Seconds (The Hook)**: Never start with a boring greeting. Hook immediately with a pain point, shocking stat, or curiosity trigger ("Đừng mua nếu chưa biết...", "Chiếc máy đang làm mưa làm gió...").
2. **Trust & Social Proof**: Always show real metrics (4.9⭐, 10k+ sold, Shopee Mall badge) to destroy buyer hesitation.
3. **Irresistible CTA**: Tell the viewer *exactly* where to click ("Bấm vào giỏ hàng góc trái màn hình", "Link ở bio trang cá nhân") and give them a reason to act *now* (voucher 50k, freeship, limited stock).
4. **Captions**: Bold, vibrant subtitles at safe vertical height so viewers watch even with sound muted while scrolling.
