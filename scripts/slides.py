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


def srt(manifest, script, path, lead):
    fps = manifest['fps']
    stamp = lambda t: f'{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{int(t % 60):02d},{int(round(t % 1 * 1000)) % 1000:03d}'
    texts = {s['id']: s['text'] for s in script['scenes']}
    cues = []
    for sc in manifest['scenes']:
        pieces = chunks(texts[sc['id']])
        total = sum(len(p) for p in pieces) or 1
        t = sc['startFrame'] / fps + lead
        for p in pieces:
            d = sc['speechSec'] * len(p) / total
            cues.append((t, t + d, p))
            t += d
    path.write_text('\n'.join(f'{i}\n{stamp(s)} --> {stamp(e)}\n{p}\n' for i, (s, e, p) in enumerate(cues, 1)))


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
    if vm.get('scriptHash') != sha_file(proj / 'voice' / 'script.json'):
        die('voice/script.json changed after the last generate. Run voice.py generate (use --only for the edited slides).', 2)
    fps = vm['fps']
    w, h = (960, 540) if a.draft else (sm['width'], sm['height'])
    enc = ['-c:v', 'libx264', '-preset', 'veryfast' if a.draft else 'slow', '-crf', '30' if a.draft else '18',
           '-pix_fmt', 'yuv420p', '-r', str(fps)]
    images = {s['id']: proj / s['image'] for s in sm['slides']}
    out = Path(a.out).resolve() if a.out else proj / 'out' / ('draft.mp4' if a.draft else 'final.mp4')
    out.parent.mkdir(parents=True, exist_ok=True)
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
            srt(vm, script, sub, vm.get('leadSec', 0))
            cmd += ['-i', str(sub)]
            maps += ['-map', '2:s', '-c:s', 'mov_text', '-metadata:s:s:0', f'language={vm.get("lang", "vie")}']
        run(cmd + maps + ['-c:v', 'copy', '-c:a', 'aac', '-b:a', '96k' if a.draft else '192k',
                          '-movflags', '+faststart', str(out)])
    dur = float(run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(out)]))
    off = abs(dur - vm['totalSec'])
    print(f'{out}  {dur:.2f}s (voice {vm["totalSec"]}s{", OFF BY %.2fs" % off if off > 1.5 / fps + 0.05 else ""})')


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
    pr = sub.add_parser('render')
    pr.add_argument('project')
    pr.add_argument('--draft', action='store_true')
    pr.add_argument('--out')
    pr.add_argument('--subs', choices=['soft', 'none'], default='soft')
    pr.add_argument('--motion', choices=['none', 'zoom'], default='none')
    pr.add_argument('--fade', type=float, default=0.0)
    pr.add_argument('--bg', default='black')
    a = p.parse_args()
    ingest(a) if a.cmd == 'ingest' else render(a)


if __name__ == '__main__':
    main()
