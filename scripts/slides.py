#!/usr/bin/env python3
"""Turn an existing slide deck into a narrated video (stdlib only; needs ffmpeg).

  slides.py ingest <deck> [--out DIR] [--width 1920] [--height 1080]
                          [--url-pattern '#s{n}'] [--count N] [--wait-ms 4000] [--force]
      Export every slide of <deck> to DIR/slides/NN.png and write DIR/slides.json with each
      slide's on-screen text and speaker notes. <deck> is a .pdf, a .pptx/.ppt/.odp/.key
      (converted with LibreOffice), a folder of images (natural sort order) or an .html deck
      (screenshotted with headless Chrome at <url-pattern>, 1-based; the default '#s{n}' fits
      feature-guide keynote decks, '#/{i}' fits reveal.js with 0-based {i}).
      DIR defaults to <deck-dir>/<deck-name>-video.
  slides.py render <project-dir> [--draft] [--out FILE] [--subs soft|none]
                                 [--motion none|zoom] [--fade SEC] [--bg COLOR]
      Build the video from slides/ and voice/voice.json: each slide stays on screen exactly as
      long as its voice clip, the narration track is muxed in, and (default) a soft subtitle
      track is added from the script. --draft renders a fast 960×540 preview.
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
import zipfile
from pathlib import Path

IMAGE_EXT = {'.png', '.jpg', '.jpeg', '.webp', '.bmp', '.gif'}
OFFICE_EXT = {'.pptx', '.ppt', '.odp', '.key', '.pps', '.ppsx'}
SUB_MAX_CHARS = 90


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode:
        die(f'{cmd[0]} failed ({r.returncode}):\n{r.stderr[-2000:]}')
    return r.stdout


def need(*tools):
    for t in tools:
        if not shutil.which(t):
            die(f'{t} is required but not on PATH.')


def sha_file(p):
    """Same digest as voice.py sha() for a file; a folder also hashes its file names."""
    p = Path(p)
    if not p.is_dir():
        return hashlib.sha256(p.read_bytes()).hexdigest()
    h = hashlib.sha256()
    for f in sorted(f for f in p.rglob('*') if f.is_file()):
        h.update(f.name.encode())
        h.update(f.read_bytes())
    return h.hexdigest()


def natural(p):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', p.name)]


def clean(text):
    lines = [re.sub(r'[ \t]+', ' ', l).strip() for l in text.replace('\f', '\n').splitlines()]
    return '\n'.join(l for l in lines if l)


# ---------- ingest ----------

def from_pdf(pdf, sd, w, h):
    need('pdfinfo', 'pdftoppm', 'pdftotext')
    pages = int(re.search(r'Pages:\s+(\d+)', run(['pdfinfo', str(pdf)])).group(1))
    run(['pdftoppm', '-png', '-scale-to-x', str(w), '-scale-to-y', '-1', str(pdf), str(sd / 'raw')])
    raw = sorted(sd.glob('raw-*.png'), key=natural)
    if len(raw) != pages:
        die(f'pdftoppm wrote {len(raw)} images for {pages} pages')
    out = []
    for n, img in enumerate(raw, 1):
        img.rename(sd / f'{n:02d}.png')
        text = run(['pdftotext', '-f', str(n), '-l', str(n), '-layout', str(pdf), '-'])
        out.append({'text': clean(text), 'notes': ''})
    return out


def pptx_notes(path):
    """Speaker notes per visible slide, in presentation order; None if unreadable."""
    try:
        z = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return None
    rels = lambda p: dict(re.findall(r'Id="([^"]+)"[^>]*Target="([^"]+)"', z.read(p).decode('utf8'))) \
        if p in z.namelist() else {}
    pres = z.read('ppt/presentation.xml').decode('utf8')
    prels = rels('ppt/_rels/presentation.xml.rels')
    texts = lambda xml: clean('\n'.join(html.unescape(' '.join(re.findall(r'<a:t>([^<]*)</a:t>', p)))
                                        for p in re.findall(r'<a:p>.*?</a:p>', xml, re.S)))
    out = []
    for rid in re.findall(r'<p:sldId [^>]*r:id="([^"]+)"', pres):
        slide = 'ppt/' + prels[rid].lstrip('/').removeprefix('ppt/')
        if 'show="0"' in z.read(slide).decode('utf8')[:500]:
            continue  # LibreOffice leaves hidden slides out of the PDF
        srels = rels(slide.replace('slides/', 'slides/_rels/') + '.rels')
        note = next((t for t in srels.values() if 'notesSlide' in t), None)
        body = ''
        if note:
            xml = z.read('ppt/' + note.replace('../', '')).decode('utf8')
            # Drop the slide-image and slide-number placeholders; keep the body text.
            shapes = [s for s in re.findall(r'<p:sp>.*?</p:sp>', xml, re.S) if 'type="body"' in s]
            body = texts(''.join(shapes))
        out.append(body)
    return out


def from_office(deck, sd, w, h):
    office = shutil.which('soffice') or shutil.which('libreoffice')
    if not office:
        die('LibreOffice (soffice) is needed for .pptx/.odp/.key. Install it, or export the deck to PDF and pass the PDF.')
    with tempfile.TemporaryDirectory() as tmp:
        run([office, '--headless', '--convert-to', 'pdf', '--outdir', tmp, str(deck)])
        pdf = next(Path(tmp).glob('*.pdf'), None) or die('LibreOffice produced no PDF')
        slides = from_pdf(pdf, sd, w, h)
        shutil.copy(pdf, sd.parent / 'deck.pdf')
    notes = pptx_notes(deck) if deck.suffix.lower() in ('.pptx', '.ppsx') else None
    if notes is not None and len(notes) != len(slides):
        print(f'warning: {len(notes)} notes for {len(slides)} slides; speaker notes skipped', file=sys.stderr)
        notes = None
    for s, n in zip(slides, notes or []):
        s['notes'] = n
    return slides


def from_images(folder, sd, w, h):
    need('ffmpeg')
    imgs = sorted((f for f in folder.iterdir() if f.suffix.lower() in IMAGE_EXT), key=natural)
    if not imgs:
        die(f'No images in {folder}')
    for n, img in enumerate(imgs, 1):
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(img), '-frames:v', '1', '-vf', f'scale={w}:-2', str(sd / f'{n:02d}.png')])
    return [{'text': '', 'notes': '', 'from': img.name} for img in imgs]


def chrome():
    for c in ('google-chrome', 'google-chrome-stable', 'chromium', 'chromium-browser', 'chrome'):
        if shutil.which(c):
            return shutil.which(c)
    mac = Path('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
    return str(mac) if mac.exists() else die('Chrome or Chromium is needed to screenshot an HTML deck.')


def from_html(deck, sd, w, h, pattern, count, wait_ms):
    src = deck.read_text(encoding='utf8', errors='replace')
    sections = re.findall(r'<section\b([^>]*\bclass="[^"]*\bslide\b[^"]*"[^>]*)>(.*?)</section>', src, re.S)
    n_slides = count or len(sections)
    if not n_slides:
        die('Found no <section class="slide"> in the deck; pass --count N and a matching --url-pattern.')
    exe = chrome()
    out = []
    for n in range(1, n_slides + 1):
        url = deck.resolve().as_uri() + pattern.format(n=n, i=n - 1)
        png = sd / f'{n:02d}.png'
        with tempfile.TemporaryDirectory() as prof:
            run([exe, '--headless=new', '--disable-gpu', '--hide-scrollbars', '--no-first-run', '--mute-audio',
                 f'--user-data-dir={prof}', f'--window-size={w},{h}', f'--virtual-time-budget={wait_ms}',
                 f'--screenshot={png}', url])
        if not png.exists():
            die(f'Chrome wrote no screenshot for {url}')
        attrs, body = sections[n - 1] if n <= len(sections) else ('', '')
        note = re.search(r'data-note="([^"]*)"', attrs)
        text = html.unescape(re.sub(r'<[^>]+>', '\n', re.sub(r'<(script|style)\b.*?</\1>', '', body, flags=re.S)))
        out.append({'text': clean(text), 'notes': html.unescape(note.group(1)) if note else ''})
    return out


def ingest(a):
    deck = Path(a.deck).resolve()
    if not deck.exists():
        die(f'{deck} not found')
    proj = Path(a.out).resolve() if a.out else deck.parent / f'{deck.stem}-video'
    sd = proj / 'slides'
    if (proj / 'slides.json').exists() and not a.force:
        die(f'{proj}/slides.json exists. Pass --force to re-export (the voice script must then be re-drafted).')
    shutil.rmtree(sd, ignore_errors=True)
    sd.mkdir(parents=True)
    ext = deck.suffix.lower()
    if deck.is_dir():
        kind, slides = 'images', from_images(deck, sd, a.width, a.height)
    elif ext == '.pdf':
        kind, slides = 'pdf', from_pdf(deck, sd, a.width, a.height)
    elif ext in OFFICE_EXT:
        kind, slides = 'office', from_office(deck, sd, a.width, a.height)
    elif ext in ('.html', '.htm'):
        kind, slides = 'html', from_html(deck, sd, a.width, a.height, a.url_pattern, a.count, a.wait_ms)
    else:
        die(f'Unsupported deck type: {deck.name} (pdf, pptx/ppt/odp/key, html, or a folder of images)')
    for n, s in enumerate(slides, 1):
        s.update({'id': f'p{n:02d}', 'image': f'slides/{n:02d}.png'})
    manifest = {'source': str(deck), 'kind': kind, 'sourceHash': sha_file(deck),
                'width': a.width, 'height': a.height, 'slides': slides}
    (proj / 'slides.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    for s in slides:
        first = (s['text'].splitlines() or [''])[0][:70]
        print(f'{s["id"]}  {s["image"]}  notes:{"yes" if s["notes"] else "no ":<3}  {first}')
    print(f'{len(slides)} slides → {proj}')


# ---------- regions ----------

def pdf_regions(pdf, page, w, h):
    """Images and text blocks on one PDF page, as slide-pixel boxes."""
    with tempfile.TemporaryDirectory() as tmp:
        run(['pdftohtml', '-xml', '-q', '-f', str(page), '-l', str(page), str(pdf), f'{tmp}/p'])
        xml = Path(f'{tmp}/p.xml').read_text(encoding='utf8', errors='replace')
    pg = re.search(r'<page [^>]*height="([\d.]+)" width="([\d.]+)"', xml)
    sx, sy = w / float(pg.group(2)), h / float(pg.group(1))
    box = lambda m: [float(m['left']) * sx, float(m['top']) * sy, float(m['width']) * sx, float(m['height']) * sy]
    attrs = lambda s: dict(re.findall(r'(\w+)="([^"]*)"', s))
    out = []
    for m in re.finditer(r'<image ([^>]*)/>', xml):
        b = box(attrs(m.group(1)))
        area = b[2] * b[3] / (w * h)
        if 0.004 < area < 0.85:  # skip specks and full-slide backgrounds
            out.append({'kind': 'image', 'box': b, 'text': ''})
    lines = []
    for m in re.finditer(r'<text ([^>]*)>(.*?)</text>', xml, re.S):
        t = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        if t:
            lines.append({'box': box(attrs(m.group(1))), 'text': t})
    lines.sort(key=lambda l: (l['box'][1], l['box'][0]))
    blocks = []
    for l in lines:
        x, y, bw, bh = l['box']
        for b in blocks:
            X, Y, BW, BH = b['box']
            overlap = min(x + bw, X + BW) - max(x, X)
            if overlap > -bh * 0.6 and -bh * 0.5 < y - (Y + BH) < bh * 1.1:
                nx, ny = min(x, X), min(y, Y)
                b['box'] = [nx, ny, max(x + bw, X + BW) - nx, max(y + bh, Y + BH) - ny]
                b['text'] += ' ' + l['text']
                break
        else:
            blocks.append({'kind': 'text', 'box': list(l['box']), 'text': l['text']})
    return out + blocks


def overlay(img, regs, dest):
    font = (run(['fc-match', '-f', '%{file}', 'DejaVu Sans:bold']).strip() if shutil.which('fc-match') else '')
    vf = []
    for r in regs:
        x, y, w, h = r['box']
        color = 'orange' if r['kind'] == 'image' else 'deepskyblue'
        vf.append(f'drawbox=x={x}:y={y}:w={w}:h={h}:color={color}@0.9:t=4')
        if font:
            vf.append(f"drawtext=fontfile='{font}':text='{r['id']}':x={x + 6}:y={y + 6}:fontsize=34:fontcolor=white:box=1:boxcolor={color}@0.9:boxborderw=6")
    run(['ffmpeg', '-v', 'error', '-y', '-i', str(img), '-vf', ','.join(vf) or 'null', '-frames:v', '1', str(dest)])


def regions(a):
    """regions.json: numbered boxes per slide that beats can point the camera at."""
    need('ffmpeg')
    proj = Path(a.project).resolve()
    sm = json.loads((proj / 'slides.json').read_text())
    pdf = Path(sm['source']) if sm['kind'] == 'pdf' else proj / 'deck.pdf'
    if not pdf.exists():
        print('No PDF behind this deck: write focus boxes as [x, y, w, h] in slide pixels instead of region ids.', file=sys.stderr)
    od = proj / 'regions'
    od.mkdir(exist_ok=True)
    allr = {}
    for n, s in enumerate(sm['slides'], 1):
        regs = pdf_regions(pdf, n, sm['width'], sm['height']) if pdf.exists() else []
        for i, r in enumerate(regs, 1):
            r['id'] = f'r{i}'
            r['box'] = [round(v) for v in r['box']]
        allr[s['id']] = regs
        overlay(proj / s['image'], regs, od / f'{n:02d}.png')
        print(f'{s["id"]}: ' + ', '.join(f'{r["id"]}={r["kind"]}{"" if r["kind"] == "image" else ":" + r["text"][:24]}' for r in regs))
    (proj / 'regions.json').write_text(json.dumps(allr, ensure_ascii=False, indent=1) + '\n')
    print(f'→ {proj / "regions.json"}, overlays in {od}')


# ---------- render ----------

def chunks(text):
    """Subtitle-sized pieces: sentences, split again at commas when too long."""
    out = []
    for sent in re.split(r'(?<=[.!?…])\s+', text.strip()):
        while len(sent) > SUB_MAX_CHARS:
            cut = max(sent.rfind(', ', 0, SUB_MAX_CHARS), sent.rfind(' ', 0, SUB_MAX_CHARS))
            if cut <= 0:
                break
            out.append(sent[:cut + 1].strip())
            sent = sent[cut + 1:].strip()
        if sent:
            out.append(sent)
    return out


CUE = re.compile(r'\s*\[[^\]]+\]\s*')
RANGES = {
    'latin': 'U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+0304, U+0308, U+0329, U+2000-206F, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215, U+FEFF, U+FFFD',
    'latin-ext': 'U+0100-02BA, U+02BD-02C5, U+02C7-02CC, U+02CE-02D7, U+02DD-02FF, U+0304, U+0308, U+0329, U+1D00-1DBF, U+1E00-1E9F, U+1EF2-1EFF, U+2020, U+20A0-20AB, U+20AD-20C0, U+2113, U+2C60-2C7F, U+A720-A7FF',
    'vietnamese': 'U+0102-0103, U+0110-0111, U+0128-0129, U+0168-0169, U+01A0-01A1, U+01AF-01B0, U+0300-0301, U+0303-0304, U+0308-0309, U+0323, U+0329, U+1EA0-1EF9, U+20AB',
}
SKILL = Path(__file__).resolve().parent.parent


def plain(text):
    return CUE.sub(' ', text).strip()


def beats_of(scene):
    return scene.get('beats') or [{'text': scene.get('text', '')}]


def spoken_hash(scene, script, speed):
    """Same digest as voice.py: focus and callout edits don't need a re-speak, text edits do."""
    lex = script.get('lexicon') or {}
    def say(t):
        for k in sorted(lex, key=len, reverse=True):
            t = t.replace(k, lex[k])
        return t
    return hashlib.sha256(json.dumps([say(b['text']) for b in beats_of(scene)] + [speed], ensure_ascii=False).encode()).hexdigest()[:16]


def srt(vm, script, path):
    fps = vm['fps']
    stamp = lambda t: f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}'
    beats = {s['id']: beats_of(s) for s in script['scenes']}
    cues = []
    for sc in vm['scenes']:
        for b, tb in zip(beats[sc['id']], sc['beats']):
            pieces = chunks(plain(b['text']))
            total = sum(len(p) for p in pieces) or 1
            t = (sc['startFrame'] + tb['startFrame']) / fps
            for p in pieces:
                d = tb['frames'] / fps * len(p) / total
                cues.append((t, t + d, p))
                t += d
    path.write_text('\n'.join(f'{i}\n{stamp(s)} --> {stamp(e)}\n{p}\n' for i, (s, e, p) in enumerate(cues, 1)))


def resolve_focus(f, regs, sid):
    """null | 'r3' | ['r3', 'r4'] (union) | [x, y, w, h] → [x, y, w, h] in slide pixels."""
    if not f:
        return None
    if isinstance(f, list) and len(f) == 4 and all(isinstance(v, (int, float)) for v in f):
        return f
    ids = [f] if isinstance(f, str) else f
    by = {r['id']: r['box'] for r in regs.get(sid, [])}
    missing = [i for i in ids if i not in by]
    if missing:
        die(f'{sid}: unknown region(s) {", ".join(missing)} (run slides.py regions, see regions.json)')
    xs = [by[i] for i in ids]
    x0, y0 = min(b[0] for b in xs), min(b[1] for b in xs)
    return [x0, y0, max(b[0] + b[2] for b in xs) - x0, max(b[1] + b[3] for b in xs) - y0]


def props(proj, sm, vm, script, captions, progress):
    rp = proj / 'regions.json'
    regs = json.loads(rp.read_text()) if rp.exists() else {}
    fd = proj / '_assets' / 'fonts'
    fd.mkdir(parents=True, exist_ok=True)
    faces = []
    for f in sorted((SKILL / 'assets' / 'fonts').glob('*.woff2')):
        shutil.copy(f, fd / f.name)
        m = re.match(r'be-vietnam-pro-(\d+)-(.+)\.woff2', f.name)
        faces.append({'family': 'Be Vietnam Pro', 'weight': int(m.group(1)), 'url': f'_assets/fonts/{f.name}', 'unicodeRange': RANGES[m.group(2)]})
    images = {s['id']: s['image'] for s in sm['slides']}
    sections = [s for s in script['scenes'] if s.get('kind') == 'section']
    numbered = [s for s in sections if (s.get('section') or {}).get('n')]
    chapters, scenes = [], []
    for s, t in zip(script['scenes'], vm['scenes']):
        if s.get('kind') == 'section' and (s.get('section') or {}).get('n'):
            chapters.append({'title': (s.get('section') or {}).get('short') or s['section']['title'], 'startFrame': t['startFrame']})
        sec = dict(s['section'], of=len(numbered)) if s.get('section') else None
        scenes.append({
            'id': s['id'], 'kind': s.get('kind', 'slide'), 'image': images[s['id']],
            'startFrame': t['startFrame'], 'frames': t['frames'], 'section': sec,
            'chapter': len(chapters) - 1 if chapters else None,
            'beats': [{'startFrame': tb['startFrame'], 'frames': tb['frames'], 'text': plain(b['text']),
                       'focus': resolve_focus(b.get('focus'), regs, s['id']), 'callout': b.get('callout')}
                      for b, tb in zip(beats_of(s), t['beats'])],
        })
    return {'fps': vm['fps'], 'width': 1920, 'height': 1080, 'slideWidth': sm['width'], 'slideHeight': sm['height'],
            'audio': vm['audio'], 'captions': captions, 'progress': progress, 'theme': script.get('theme') or {},
            'fonts': faces, 'chapters': chapters, 'scenes': scenes, 'totalFrames': vm['totalFrames']}


def render_remotion(a, proj, sm, vm, script, out):
    r = Path(a.renderer).expanduser()
    if not (r / 'node_modules').exists():
        die(f'No renderer at {r}. Run: bash {SKILL}/scripts/setup-renderer.sh {SKILL} {r}')
    pj = proj / 'out' / 'props.json'
    pj.parent.mkdir(parents=True, exist_ok=True)
    pj.write_text(json.dumps(props(proj, sm, vm, script, a.captions == 'on', a.progress == 'on'), ensure_ascii=False))
    base = ['npx', 'remotion']
    common = ['src/index.ts', 'Slides', str(out), f'--props={pj}', f'--public-dir={proj}', '--log=error']
    if a.still is not None:
        cmd = base + ['still'] + common + [f'--frame={a.still}', '--scale=0.5']
    elif a.draft:
        cmd = base + ['render'] + common + ['--codec=h264', '--scale=0.5', '--jpeg-quality=75', '--crf=26']
    else:
        cmd = base + ['render'] + common + ['--codec=h264', '--jpeg-quality=95', '--crf=18', '--audio-bitrate=192k']
    lock = ['flock', '/tmp/build-video-voice-render.lock'] if shutil.which('flock') else []
    r2 = subprocess.run(lock + cmd, cwd=r, capture_output=True, text=True)
    if r2.returncode:
        die(f'remotion failed:\n{(r2.stderr or r2.stdout)[-3000:]}')
    if a.still is not None:
        print(out)
        return False
    if a.subs == 'soft':
        sub = proj / 'voice' / 'narration.srt'
        srt(vm, script, sub)
        tmp = out.with_suffix('.subs.mp4')
        run(['ffmpeg', '-v', 'error', '-y', '-i', str(out), '-i', str(sub), '-map', '0', '-map', '1', '-c', 'copy',
             '-c:s', 'mov_text', '-metadata:s:s:0', f'language={vm.get("lang", "vie")}', '-movflags', '+faststart', str(tmp)])
        tmp.replace(out)
    return True


def render(a):
    need('ffmpeg', 'ffprobe')
    proj = Path(a.project).resolve()
    sm = json.loads((proj / 'slides.json').read_text())
    vp = proj / 'voice' / 'voice.json'
    if not vp.exists():
        die(f'No {vp}. Generate the voice first (voice.py generate).')
    vm = json.loads(vp.read_text())
    if vm.get('slidesHash') != sha_file(proj / 'slides.json'):
        die('slides.json changed after the voice was generated. Re-draft and regenerate the voice.', 2)
    script = json.loads((proj / 'voice' / 'script.json').read_text())
    stale = [sc['id'] for sc, t in zip(script['scenes'], vm['scenes']) if spoken_hash(sc, script, vm['speed']) != t['textHash']]
    if stale or len(script['scenes']) != len(vm['scenes']):
        die(f'Spoken text changed for {", ".join(stale)} since the last generate. Run: voice.py generate --only {",".join(stale)}', 2)
    default = f'stills/f{a.still:05d}.png' if a.still is not None else ('draft.mp4' if a.draft else 'final.mp4')
    out = Path(a.out).resolve() if a.out else proj / 'out' / default
    out.parent.mkdir(parents=True, exist_ok=True)
    if a.engine == 'remotion':
        if not render_remotion(a, proj, sm, vm, script, out):
            return
    else:
        render_ffmpeg(a, proj, sm, vm, script, out)
    dur = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(out)]))
    fps = vm['fps']
    off = abs(dur - vm['totalSec'])
    print(f'{out}  {dur:.2f}s (voice {vm["totalSec"]}s{", OFF BY %.2fs" % off if off > 1.5 / fps + 0.05 else ""})')


def render_ffmpeg(a, proj, sm, vm, script, out):
    """Plain fallback without Node: still slides (optional slow zoom / fade), hard cuts."""
    fps = vm['fps']
    w, h = (960, 540) if a.draft else (sm['width'], sm['height'])
    enc = ['-c:v', 'libx264', '-preset', 'veryfast' if a.draft else 'slow', '-crf', '30' if a.draft else '18',
           '-pix_fmt', 'yuv420p', '-r', str(fps)]
    images = {s['id']: proj / s['image'] for s in sm['slides']}
    with tempfile.TemporaryDirectory(dir=proj) as tmp:
        tmp = Path(tmp)
        segs = []
        for sc in vm['scenes']:
            n = sc['frames']
            fit = f'scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color={a.bg},setsar=1'
            if a.motion == 'zoom':
                # Upscale first so zoompan's integer crop steps don't jitter.
                vf = (f'{fit},scale={w * 2}:{h * 2},zoompan=z=\'1+0.04*on/{n}\':x=\'iw/2-iw/zoom/2\':'
                      f'y=\'ih/2-ih/zoom/2\':d={n}:s={w}x{h}:fps={fps}')
                inp = ['-i', str(images[sc['id']])]
            else:
                vf = fit
                inp = ['-loop', '1', '-framerate', str(fps), '-i', str(images[sc['id']])]
            if a.fade > 0:
                vf += f',fade=in:st=0:d={a.fade}'
            seg = tmp / f'{sc["id"]}.mp4'
            run(['ffmpeg', '-v', 'error', '-y', *inp, '-vf', f'{vf},format=yuv420p', '-frames:v', str(n), *enc, str(seg)])
            segs.append(seg)
        (tmp / 'list.txt').write_text(''.join(f"file '{s.name}'\n" for s in segs))
        video = tmp / 'video.mp4'
        run(['ffmpeg', '-v', 'error', '-y', '-f', 'concat', '-safe', '0', '-i', str(tmp / 'list.txt'), '-c', 'copy', str(video)])
        cmd = ['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-i', str(proj / vm['audio'])]
        maps = ['-map', '0:v', '-map', '1:a']
        if a.subs == 'soft':
            sub = proj / 'voice' / 'narration.srt'
            srt(vm, script, sub)
            cmd += ['-i', str(sub)]
            maps += ['-map', '2:s', '-c:s', 'mov_text', '-metadata:s:s:0', f'language={vm.get("lang", "vie")}']
        run(cmd + maps + ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k' if a.draft else '192k',
                          '-movflags', '+faststart', str(out)])


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    pi = sub.add_parser('ingest')
    pi.add_argument('deck')
    pi.add_argument('--out')
    pi.add_argument('--width', type=int, default=1920)
    pi.add_argument('--height', type=int, default=1080)
    pi.add_argument('--url-pattern', default='#s{n}')
    pi.add_argument('--count', type=int)
    pi.add_argument('--wait-ms', type=int, default=4000)
    pi.add_argument('--force', action='store_true')
    pg = sub.add_parser('regions')
    pg.add_argument('project')
    pr = sub.add_parser('render')
    pr.add_argument('project')
    pr.add_argument('--draft', action='store_true')
    pr.add_argument('--out')
    pr.add_argument('--engine', choices=['remotion', 'ffmpeg'], default='remotion')
    pr.add_argument('--renderer', default=str(Path(os.environ.get('XDG_DATA_HOME', Path.home() / '.local/share')) / 'build-video-voice/renderer'))
    pr.add_argument('--still', type=int, metavar='FRAME')
    pr.add_argument('--captions', choices=['on', 'off'], default='on')
    pr.add_argument('--progress', choices=['on', 'off'], default='on')
    pr.add_argument('--subs', choices=['soft', 'none'], default='soft')
    pr.add_argument('--motion', choices=['none', 'zoom'], default='none')
    pr.add_argument('--fade', type=float, default=0.0)
    pr.add_argument('--bg', default='black')
    a = p.parse_args()
    {'ingest': ingest, 'regions': regions, 'render': render}[a.cmd](a)


if __name__ == '__main__':
    main()
