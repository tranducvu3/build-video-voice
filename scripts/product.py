#!/usr/bin/env python3
"""Product search, asset downloader, and affiliate video generator for Shopee.

Usage:
  product.py search "<keyword>"
      Search product information and find high-res images on web/Shopee.
  product.py fetch "<shopee-url>"
      Extract product details from a Shopee product URL or short link.
  product.py create "<keyword-or-url>" [--out DIR] [--format 9:16|16:9]
                                       [--affiliate-url URL] [--cta-location cart|bio|comment|description]
                                       [--voice NAME] [--speed X] [--price PRICE] [--original-price PRICE]
                                       [--discount DISCOUNT] [--rating STARS] [--sold COUNT]
                                       [--bgm upbeat|chill|off] [--theme shopee|tech|beauty|minimal]
                                       [--image-count N]
      Automates the full pipeline: searches product info, downloads high-res images,
      sets up scenes (Hook -> Showcase -> Features -> Social Proof -> CTA), generates
      a high-converting affiliate script with VieNeu-TTS pronunciation lexicon, and writes
      a ready-to-copy social post caption with hashtags.
"""
import argparse
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def http_get(url, timeout=12):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': '*/*'})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode('utf-8', errors='ignore'), resp.geturl()


def resolve_url(url):
    """Resolve redirects (e.g. s.shopee.vn short links) to the final URL."""
    try:
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req, timeout=10) as resp:
            return resp.geturl()
    except Exception:
        return url


def clean_product_title(raw_title):
    """Strip annoying e-commerce promotional tags like [Mã giảm 50k] [Chính Hãng 100%]."""
    cleaned = re.sub(r'\[[^\]]*\]', ' ', raw_title)
    cleaned = re.sub(r'\([^\)]*(?:chính hãng|freeship|săn sale|bảo hành|mã giảm)[^\)]*\)', ' ', cleaned, flags=re.I)
    cleaned = re.sub(r'(?:chính hãng|freeship|mã giảm|deal hot|hàng mới về)\s*[-–|:]\s*', ' ', cleaned, flags=re.I)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if len(cleaned) > 5 else raw_title.strip()


def search_web_info(query):
    """Query Bing web search to gather specifications, user reviews, and pricing clues."""
    encoded = urllib.parse.quote(f'{query} shopee thong so danh gia')
    url = f'https://www.bing.com/search?q={encoded}'
    try:
        html_content, _ = http_get(url)
    except Exception as e:
        print(f'Warning: web search failed ({e})', file=sys.stderr)
        return {'snippets': [], 'title': query}

    blocks = re.findall(r'<li class="b_algo"[^>]*>(.*?)</li>', html_content, re.S)
    snippets = []
    found_title = ''
    for b in blocks:
        title_m = re.search(r'<h2[^>]*><a[^>]*>(.*?)</a>', b, re.S)
        caption_m = re.search(r'<div class="b_caption"><p>(.*?)</p>', b, re.S) or re.search(r'<p[^>]*>(.*?)</p>', b, re.S)
        if title_m and not found_title:
            t = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
            if 'shopee' in t.lower() or query.lower() in t.lower():
                found_title = clean_product_title(t)
        if caption_m:
            snip = re.sub(r'<[^>]+>', ' ', caption_m.group(1)).strip()
            snip = html.unescape(snip)
            if snip and len(snip) > 20:
                snippets.append(snip)

    return {
        'title': found_title or query,
        'snippets': snippets[:6],
    }


def search_images(query, max_count=8):
    """Search Bing images, prioritizing Shopee CDN (*.susercontent.com) and high-res store images."""
    encoded = urllib.parse.quote(f'{query} shopee')
    url = f'https://www.bing.com/images/search?q={encoded}&form=HDRSC2&first=1'
    try:
        html_content, _ = http_get(url)
    except Exception as e:
        print(f'Warning: image search failed ({e})', file=sys.stderr)
        return []

    # Extract image URLs from murl in Bing HTML
    matches = re.findall(r'murl&quot;:&quot;(http[^&]+)&quot;', html_content) or re.findall(r'&quot;murl&quot;:&quot;([^&]+)&quot;', html_content)

    shopee_urls = []
    other_urls = []
    seen = set()

    for u in matches:
        u = html.unescape(u).strip()
        if u in seen:
            continue
        seen.add(u)
        lower = u.lower()
        if any(bad in lower for bad in ['.svg', 'avatar', 'icon', 'logo', 'favicon', 'banner_small']):
            continue
        if 'susercontent.com' in lower:
            shopee_urls.append(u)
        elif lower.endswith(('.jpg', '.jpeg', '.png', '.webp')):
            other_urls.append(u)

    # Put official Shopee images first
    combined = shopee_urls + other_urls
    return combined[:max_count]


def download_and_convert_images(urls, dest_dir, max_count=6):
    """Download images and convert them into standardized, crisp PNG slides."""
    dest_dir = Path(dest_dir)
    dest_dir.mkdir(parents=True, exist_ok=True)
    saved = []

    for i, u in enumerate(urls[:max_count], 1):
        target = dest_dir / f'{i:02d}.png'
        with tempfile.NamedTemporaryFile(suffix='.tmp', delete=False) as tmp:
            tmp_path = Path(tmp.name)
            try:
                req = urllib.request.Request(u, headers={'User-Agent': USER_AGENT})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    tmp_path.write_bytes(resp.read())

                # Convert to PNG using ffmpeg
                cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(tmp_path), '-frames:v', '1', str(target)]
                r = subprocess.run(cmd, capture_output=True, text=True)
                if r.returncode == 0 and target.exists() and target.stat().st_size > 1000:
                    saved.append(target)
                else:
                    print(f'Warning: failed to convert {u} to PNG', file=sys.stderr)
            except Exception as e:
                print(f'Warning: failed to download image {u}: {e}', file=sys.stderr)
            finally:
                if tmp_path.exists():
                    tmp_path.unlink()

    return saved


def find_product_videos(query_or_url):
    """Auto-detect product videos from Shopee URL or page content."""
    videos = []
    if not query_or_url.startswith(('http://', 'https://')):
        return videos
    try:
        full_url = resolve_url(query_or_url)
        content, _ = http_get(full_url)
        # 1. Search for direct vod.susercontent.com mp4 urls
        direct_urls = re.findall(r'https?://[^\s\"\'<>]*(?:vod\.susercontent\.com|mms\.vod)[^\s\"\'<>]+\.mp4', content)
        for u in direct_urls:
            u = u.replace('\\', '')
            if u not in videos:
                videos.append(u)

        # 2. Search for vid in video_info_list
        vids = re.findall(r'\"vid\":\s*\"([^\"]+)\"', content)
        for v in vids:
            v_url = f'https://mms.vod.susercontent.com/api/v4/11110106/mms/{v}.default.mp4'
            if v_url not in videos:
                videos.append(v_url)
    except Exception as e:
        print(f'Warning: video detection failed ({e})', file=sys.stderr)
    return videos


def download_product_video(url, dest_file):
    """Download product video and remove audio track to keep narration crystal clear."""
    dest_file = Path(dest_file)
    dest_file.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp:
        tmp_path = Path(tmp.name)
        try:
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            with urllib.request.urlopen(req, timeout=20) as resp:
                tmp_path.write_bytes(resp.read())

            # Mute audio track so it doesn't conflict with VieNeu-TTS voice & upbeat BGM
            cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(tmp_path), '-c:v', 'copy', '-an', str(dest_file)]
            r = subprocess.run(cmd, capture_output=True, text=True)
            if r.returncode == 0 and dest_file.exists() and dest_file.stat().st_size > 1000:
                return dest_file
            shutil.copy(tmp_path, dest_file)
            return dest_file
        except Exception as e:
            print(f'Warning: failed to download video {url}: {e}', file=sys.stderr)
            return None
        finally:
            if tmp_path.exists():
                tmp_path.unlink()


def generate_affiliate_copy(product_name, info, options):
    """Generate high-converting Vietnamese affiliate script with proven e-commerce formula."""
    price = options.get('price') or 'giá cực hời'
    discount = options.get('discount') or '-35%'
    cta_loc = options.get('cta_location') or 'cart'

    # Determine CTA spoken text
    if cta_loc == 'cart':
        cta_spoken = 'Link mua chính hãng kèm mã freeship và voucher giảm giá mình để ngay ở giỏ hàng góc trái màn hình nha!'
        cta_target_name = 'giỏ hàng góc trái'
    elif cta_loc == 'bio':
        cta_spoken = 'Link mua chính hãng giảm giá độc quyền mình để trên phần bio đầu trang cá nhân, cả nhà bấm vào săn ngay nha!'
        cta_target_name = 'link bio'
    elif cta_loc == 'comment':
        cta_spoken = 'Link mua chính hãng kèm voucher độc quyền mình ghim ở ngay bình luận đầu tiên, tranh thủ săn ngay kẻo hết deal hời nha!'
        cta_target_name = 'bình luận đầu tiên'
    else:
        cta_spoken = 'Link mua chính hãng kèm voucher giảm giá mình để chi tiết ở phần mô tả, mọi người click vào mua ngay nha!'
        cta_target_name = 'phần mô tả'

    # Extract snippets into feature talking points
    snippets = info.get('snippets', [])
    feat1_text = snippets[0][:120] if len(snippets) > 0 else 'Thiết kế cao cấp, độ hoàn thiện cực kỳ tỉ mỉ và bền bỉ.'
    feat2_text = snippets[1][:120] if len(snippets) > 1 else 'Hiệu năng vượt trội trong tầm giá, dùng siêu thích và tiện lợi.'

    scenes = [
        {
            'id': 'p01',
            'kind': 'hook',
            'badge': '🔥 CẢNH BÁO CHO TÍN ĐỒ SHOPEE',
            'title': f'ĐỪNG VỘI MUA {product_name.upper()[:28]}...',
            'subtitle': 'Nếu bạn chưa xem hết chiếc video này!',
            'beats': [
                {
                    'text': f'Đừng vội mua {product_name} nếu bạn chưa biết điều này! [cười]',
                    'callout': 'Xem ngay kẻo tiếc!',
                }
            ],
        },
        {
            'id': 'p02',
            'kind': 'product',
            'title': product_name[:60],
            'price': options.get('price') or 'Giá cực sốc',
            'originalPrice': options.get('original_price') or '',
            'discount': discount,
            'features': ['100% Chính Hãng', 'Bảo Hành 12 Tháng', 'Freeship Toàn Quốc'],
            'beats': [
                {
                    'text': f'Chiếc {product_name} này đang làm mưa làm gió trên Shopee vì vừa xịn mà giá lại quá hời!',
                    'callout': f'{discount} Hôm Nay',
                }
            ],
        },
        {
            'id': 'p03',
            'kind': 'feature',
            'badge': 'Ưu Điểm Vượt Trội',
            'title': 'Điểm Ăn Tiền Nhất Của Em Nó',
            'subtitle': 'Trải nghiệm mượt mà, tối ưu từng chi tiết!',
            'beats': [
                {
                    'text': f'Điểm ăn tiền nhất chính là độ hoàn thiện cực kỳ chuẩn chỉ, dùng rất thích và đáng đồng tiền bát gạo.',
                    'callout': 'Đáng Tiền Bát Gạo',
                }
            ],
        },
        {
            'id': 'p04',
            'kind': 'feature',
            'badge': 'Tiện Ích Đỉnh Cao',
            'title': 'Càng Dùng Càng Mê',
            'subtitle': 'Tiết kiệm thời gian và tối ưu hiệu suất mỗi ngày.',
            'beats': [
                {
                    'text': f'Chưa hết nha, em nó còn siêu tiện lợi, ai dùng qua cũng phải gật gù khen ngợi luôn!',
                    'callout': 'Dùng Là Mê',
                }
            ],
        },
        {
            'id': 'p05',
            'kind': 'social_proof',
            'rating': float(options.get('rating') or 4.9),
            'soldCount': options.get('sold') or '15.8k+',
            'reviewsCount': '9.5k',
            'reviewQuote': 'Giao hàng siêu nhanh, đóng gói cẩn thận. Dùng cực kỳ thích, đúng chuẩn hàng chính hãng 10/10!',
            'reviewAuthor': 'Người mua đã xác minh từ Shopee Mall',
            'beats': [
                {
                    'text': 'Đã có hơn 10 nghìn lượt mua và đánh giá 4 chấm 9 sao trên Shopee Mall, nên các bạn cứ hoàn toàn yên tâm.',
                    'callout': '⭐ 4.9 Sao Uy Tín',
                }
            ],
        },
        {
            'id': 'p06',
            'kind': 'cta',
            'ctaText': 'SĂN DEAL CHÍNH HÃNG NGAY!',
            'ctaTarget': cta_loc,
            'beats': [
                {
                    'text': f'Đợt này Shopee đang trợ giá và tặng voucher độc quyền, {cta_spoken}',
                    'callout': 'Bấm Vào Link Ngay!',
                }
            ],
        },
    ]

    # Pre-populate pronunciation lexicon for VieNeu-TTS
    lexicon = {
        'Shopee': 'sô pi',
        'shopee': 'sô pi',
        'Voucher': 'vou chờ',
        'voucher': 'vou chờ',
        'Freeship': 'phi ship',
        'freeship': 'phi ship',
        'Deal': 'điu',
        'deal': 'điu',
        'Sale': 'seo',
        'sale': 'seo',
        'Mall': 'mon',
        'mall': 'mon',
        'Review': 'ri viu',
        'review': 'ri viu',
        'video': 'vi dé o',
        'Video': 'vi dé o',
        'Type-C': 'túp xi',
        'type-c': 'túp xi',
        'Type C': 'túp xi',
        'Bluetooth': 'bu lu tút',
        'bluetooth': 'bu lu tút',
        'Wireless': 'quai lẹt',
        'RGB': 'rờ gờ bê',
        'LED': 'lét',
        'mAh': 'mili ampe giờ',
        'GB': 'ghi ga bai',
        'TB': 'tê ra bai',
        'Pro': 'pờ rô',
        'Max': 'mác',
        'Plus': 'pờ lớt',
        'Ultra': 'un tra',
        '4.9': 'bốn chấm chín',
        '5.0': 'năm chấm không',
        '100%': 'một trăm phần trăm',
        '10/10': 'mười trên mười',
    }

    # Add numeric price pronunciation if specified in "k" or numbers
    if options.get('price'):
        p_str = options['price'].lower().replace('.', '').replace(',', '').replace('đ', '').replace('vnd', '').strip()
        m_k = re.match(r'(\d+)k', p_str)
        if m_k:
            val = m_k.group(1)
            lexicon[options['price']] = f'{val} cành'

    return scenes, lexicon


def generate_post_markdown(proj_dir, product_name, options):
    """Generate ready-to-copy social post caption with hashtags and affiliate link."""
    aff_url = options.get('affiliate_url') or 'https://shopee.vn/ (Chèn link affiliate của bạn ở đây)'
    price = options.get('price') or 'Ưu đãi cực tốt'
    discount = options.get('discount') or '-35%'
    cta_loc = options.get('cta_location') or 'cart'

    post_content = f"""# 🛍️ BÀI VIẾT QUẢNG BÁ SHOPEE AFFILIATE

**Sản phẩm:** {product_name}
**Giá sale:** {price} ({discount})
**Link Shopee Affiliate:** {aff_url}

---

## 📝 Caption Đăng TikTok / Shopee Video / Reels / Shorts (Copy & Paste):

```text
🔥 {product_name.upper()} - EM NÀY ĐANG LÀM MƯA LÀM GIÓ VÌ QUÁ NGON TRONG TẦM GIÁ! 🔥

Mấy bà đang tìm một em {product_name} vừa bền đẹp, vừa chuẩn chính hãng thì múc ngay em này nha!
✨ Đánh giá 4.9/5⭐ trên Shopee Mall
✨ Hơn 15.000+ lượt bán chạy
✨ Đang có voucher độc quyền + Freeship toàn quốc

👉 LINK MUA CHÍNH HÃNG: {aff_url}
(Bấm vào { 'giỏ hàng góc trái màn hình' if cta_loc == 'cart' else ('link ở bio trang cá nhân' if cta_loc == 'bio' else 'bình luận đầu tiên') } để săn deal hời nha cả nhà!)

#ShopeeAffiliate #ReviewShopee #ShopeeReview #GocReview #DealHotShopee #{re.sub(r'[^a-zA-Z0-9]', '', product_name)} #KhaiThacAffiliate
```

---

## 💡 Mẹo Tăng Tỷ Lệ Click (CTR) & Chốt Đơn:
1. **Ghim bình luận đầu tiên:** Đặt link affiliate rút gọn kèm mã giảm giá nổi bật.
2. **Khung giờ vàng đăng video:** 11:30 - 13:00 (nghỉ trưa) và 19:30 - 21:30 (lướt tối săn sale).
3. **Giỏ hàng Shopee Video:** Nếu đăng trực tiếp lên Shopee Video, nhớ gắn sản phẩm vào video để người xem bấm mua là bạn nhận hoa hồng ngay lập tức!
"""
    (proj_dir / 'affiliate_post.md').write_text(post_content, encoding='utf-8')


def create_project(query, options):
    """Full workflow: search, download assets, create scenes, generate script and affiliate post."""
    # Step 1: Resolve URL or detect keyword
    if options.get('title'):
        product_name = clean_product_title(options['title'])
    elif query.startswith(('http://', 'https://')):
        full_url = resolve_url(query)
        slug_m = re.search(r'shopee\.vn/([^?]+)', full_url)
        raw_slug = slug_m.group(1) if slug_m else 'san-pham-shopee'
        raw_name = raw_slug.split('-i.')[0].replace('-', ' ')
        product_name = clean_product_title(raw_name)
    else:
        product_name = clean_product_title(query)

    slug = re.sub(r'[^a-z0-9]+', '-', product_name.lower()).strip('-')[:40]
    out_dir = Path(options.get('out') or f'{slug}-affiliate-video').resolve()
    slides_dir = out_dir / 'slides'
    voice_dir = out_dir / 'voice'

    print(f'🛒 Generating affiliate product video for: {product_name}')
    print(f'📁 Project output folder: {out_dir}')

    # Step 2: Search web details & images
    print('🔍 Searching product information and specs...')
    info = search_web_info(product_name)

    image_count = int(options.get('image_count') or 6)
    if options.get('images'):
        print(f'🖼️ Using {len(options["images"])} provided product images...')
        img_urls = options['images']
    else:
        print('🖼️ Finding high-res product images from Shopee...')
        img_urls = search_images(product_name, max_count=image_count + 4)
        if not img_urls:
            print('Warning: No images found via Bing, searching generic product photos...', file=sys.stderr)
            img_urls = search_images(query, max_count=image_count + 2)

    # Step 3: Download and convert images into slides/
    print(f'📥 Downloading {min(len(img_urls), image_count)} images to {slides_dir}...')
    downloaded = download_and_convert_images(img_urls, slides_dir, max_count=image_count)
    if not downloaded:
        die('Failed to download any product images. Check your network or try another search keyword.')

    # Step 3b: Detect & download product video to reuse in video
    video_path_rel = None
    video_src = options.get('video')
    if not video_src and query.startswith(('http://', 'https://')):
        print('🎥 Checking if product has demonstration video...')
        found_vids = find_product_videos(query)
        if found_vids:
            video_src = found_vids[0]
            print(f'🎬 Found product video: {video_src}')

    if video_src:
        target_vid = slides_dir / 'video.mp4'
        if Path(video_src).exists():
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(video_src), '-c:v', 'copy', '-an', str(target_vid)])
            if target_vid.exists() and target_vid.stat().st_size > 1000:
                video_path_rel = 'slides/video.mp4'
                print(f'🎬 Reusing local product video: {target_vid}')
        elif str(video_src).startswith(('http://', 'https://')):
            print(f'📥 Downloading product video from {video_src}...')
            saved = download_product_video(video_src, target_vid)
            if saved:
                video_path_rel = 'slides/video.mp4'
                print(f'✅ Product video downloaded to {target_vid}')

    # Step 4: Setup dimensions (9:16 vertical default, or 16:9)
    fmt = options.get('format', '9:16')
    if fmt == '9:16':
        width, height = 1080, 1920
    else:
        width, height = 1920, 1080

    # Step 5: Build scenes & script
    scenes, lexicon = generate_affiliate_copy(product_name, info, options)

    # Map downloaded images to scenes
    for idx, sc in enumerate(scenes):
        img_idx = idx % len(downloaded) + 1
        sc['image'] = f'slides/{img_idx:02d}.png'

    # If product video is available, show it EXACTLY ONCE (never repeat across multiple scenes)
    if video_path_rel:
        video_assigned = False
        # Priority 1: Show video in the main 'product' hero showcase scene
        for sc in scenes:
            if sc['kind'] == 'product':
                sc['video'] = video_path_rel
                video_assigned = True
                break
        # Priority 2: Fallback to the first 'feature' scene if no 'product' scene exists
        if not video_assigned:
            for sc in scenes:
                if sc['kind'] == 'feature':
                    sc['video'] = video_path_rel
                    video_assigned = True
                    break

    # Build slides manifest
    slides_manifest = {
        'source': query,
        'kind': 'product_affiliate',
        'width': width,
        'height': height,
        'product': {
            'name': product_name,
            'affiliateUrl': options.get('affiliate_url', ''),
            'ctaLocation': options.get('cta_location', 'cart'),
            'video': video_path_rel or '',
        },
        'slides': [
            {'id': s['id'], 'image': s['image'], 'video': s.get('video', ''), 'text': s['beats'][0]['text'], 'notes': ''}
            for s in scenes
        ],
    }
    (out_dir / 'slides.json').write_text(json.dumps(slides_manifest, ensure_ascii=False, indent=2) + '\n')

    # Step 6: Build voice/script.json
    theme_choice = options.get('theme', 'shopee')
    theme_colors = {
        'shopee': {'primary': '#ee4d2d', 'deep': '#121214', 'accent': '#ff6d3b', 'highlight': '#ffd700', 'ground': '#18181c'},
        'tech': {'primary': '#0ea5e9', 'deep': '#032541', 'accent': '#38bdf8', 'highlight': '#34d399', 'ground': '#0b0f19'},
        'beauty': {'primary': '#ec4899', 'deep': '#831843', 'accent': '#f472b6', 'highlight': '#fbbf24', 'ground': '#180d14'},
        'minimal': {'primary': '#333333', 'deep': '#111111', 'accent': '#666666', 'highlight': '#ffd700', 'ground': '#f8f9fa'},
    }.get(theme_choice, {'primary': '#ee4d2d', 'deep': '#121214', 'accent': '#ff6d3b', 'highlight': '#ffd700', 'ground': '#18181c'})

    voice_name = options.get('voice', 'Trúc Ly')
    speed = float(options.get('speed', 1.12))
    bgm_choice = options.get('bgm', 'upbeat')

    script_content = {
        'slidesHash': hashlib.sha256((out_dir / 'slides.json').read_bytes()).hexdigest(),
        'lang': 'vie',
        'width': width,
        'height': height,
        'aspectRatio': fmt,
        'voice': voice_name,
        'speed': speed,
        'temperature': 0.9,
        'bgm': bgm_choice,
        'bgmVolume': 0.14,
        'theme': theme_colors,
        'affiliateUrl': options.get('affiliate_url', ''),
        'lexicon': lexicon,
        'scenes': scenes,
    }

    voice_dir.mkdir(parents=True, exist_ok=True)
    (voice_dir / 'script.json').write_text(json.dumps(script_content, ensure_ascii=False, indent=2) + '\n')

    # Step 7: Generate ready-to-copy social post caption
    generate_post_markdown(out_dir, product_name, options)

    print(f'✅ Project created successfully!')
    print(f'   - Format: {fmt} ({width}x{height})')
    print(f'   - Voice: {voice_name} at {speed}x speed')
    print(f'   - Background Music: {bgm_choice}')
    print(f'   - Scenes: {len(scenes)} (Hook, Showcase, Features, Social Proof, CTA)')
    print(f'   - Social Post: {out_dir}/affiliate_post.md')
    print(f'\nNext steps:')
    print(f'  1. Generate voice: python3 "$P/voice.py" generate "{out_dir}"')
    print(f'  2. Render video:   python3 "$P/slides.py" render "{out_dir}" --out "{out_dir}/out/affiliate.mp4"')


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)

    # Search command
    ps = sub.add_parser('search', help='Search product info & images')
    ps.add_argument('query', help='Product name or keyword')

    # Fetch command
    pf = sub.add_parser('fetch', help='Fetch info from Shopee URL')
    pf.add_argument('url', help='Shopee product URL')

    pc = sub.add_parser('create', help='Create affiliate video project')
    pc.add_argument('query', help='Product name, keyword, or Shopee URL')
    pc.add_argument('--title', help='Override product title')
    pc.add_argument('--images', nargs='*', help='Explicit image URLs or paths to use')
    pc.add_argument('--video', help='Product video URL or file path to reuse in scenes')
    pc.add_argument('--out', help='Output directory')
    pc.add_argument('--format', choices=['9:16', '16:9'], default='9:16', help='Video aspect ratio (default: 9:16 vertical)')
    pc.add_argument('--affiliate-url', default='', help='Shopee affiliate link')
    pc.add_argument('--cta-location', choices=['cart', 'bio', 'comment', 'description'], default='cart', help='Where to instruct viewers to click')
    pc.add_argument('--voice', default='Trúc Ly', help='VieNeu-TTS voice name (default: Trúc Ly)')
    pc.add_argument('--speed', type=float, default=1.12, help='Speech speed multiplier (default: 1.12)')
    pc.add_argument('--price', default='', help='Sale price to display (e.g. 590.000₫)')
    pc.add_argument('--original-price', default='', help='Original price to strikethrough (e.g. 890.000₫)')
    pc.add_argument('--discount', default='-35%', help='Discount tag (e.g. -35%%)')
    pc.add_argument('--rating', type=float, default=4.9, help='Star rating (default: 4.9)')
    pc.add_argument('--sold', default='15.8k+', help='Sold count (e.g. 15.8k+)')
    pc.add_argument('--bgm', default='upbeat', help='Background music: upbeat, off, or audio path')
    pc.add_argument('--theme', choices=['shopee', 'tech', 'beauty', 'minimal'], default='shopee')
    pc.add_argument('--image-count', type=int, default=6, help='Number of product images to download')

    a = p.parse_args()

    if a.cmd == 'search':
        info = search_web_info(a.query)
        imgs = search_images(a.query)
        print(json.dumps({'info': info, 'images': imgs}, ensure_ascii=False, indent=2))
    elif a.cmd == 'fetch':
        full_url = resolve_url(a.url)
        slug_m = re.search(r'shopee\.vn/([^?]+)', full_url)
        raw_slug = slug_m.group(1) if slug_m else 'product'
        raw_name = raw_slug.split('-i.')[0].replace('-', ' ')
        name = clean_product_title(raw_name)
        info = search_web_info(name)
        imgs = search_images(name)
        vids = find_product_videos(full_url)
        print(json.dumps({'name': name, 'url': full_url, 'info': info, 'images': imgs, 'videos': vids}, ensure_ascii=False, indent=2))
    elif a.cmd == 'create':
        opts = {
            'title': a.title,
            'images': a.images,
            'video': a.video,
            'out': a.out,
            'format': a.format,
            'affiliate_url': a.affiliate_url,
            'cta_location': a.cta_location,
            'voice': a.voice,
            'speed': a.speed,
            'price': a.price,
            'original_price': a.original_price,
            'discount': a.discount,
            'rating': a.rating,
            'sold': a.sold,
            'bgm': a.bgm,
            'theme': a.theme,
            'image_count': a.image_count,
        }
        create_project(a.query, opts)


if __name__ == '__main__':
    main()
