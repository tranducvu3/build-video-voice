#!/usr/bin/env python3
"""Voice-over for a slide video with VieNeu-TTS (github.com/pnnbao97/VieNeu-TTS).

  voice.py draft    <project-dir> [--force]
      Write voice/script.json from slides.json: one scene per slide, seeded with the slide's
      speaker notes, else its on-screen text. Rewrite each scene as a spoken explanation of
      that slide, fill the `lexicon` (written form → spoken form, e.g. "CSV": "xê ét vê"), then
      generate. Refuses to overwrite unless --force.
  voice.py generate <project-dir> [--device auto|cpu|gpu] [--voice NAME] [--only p01,p03]
                                  [--lead SEC] [--tail SEC] [--fps N]
      Speak every scene into voice/NN-<id>.wav, padded with --lead/--tail silence and rounded
      up to whole video frames, concatenate them into voice/narration.wav, and write
      voice/transcript.md and voice/voice.json (per-slide durations that slides.py render uses).
      --only re-speaks the named slides and keeps the rest.

Device: --device auto uses the GPU (PyTorch) when one is available, otherwise the CPU
(ONNX Runtime). The GPU is an NVIDIA card (CUDA) or, on Apple Silicon, the Mac's own GPU (MPS).
In auto mode a GPU that fails to load the model or to speak falls back to the CPU.
Run it with the venv from setup-voice.sh. Models are cached next to that venv (<voice-dir>/hf),
not in ~/.cache/huggingface: a cache written by huggingface_hub 2.x links the model's .onnx and
.data files into different folders, which onnxruntime refuses to load.
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

VOICE_DIR = 'voice'
DEFAULT_FPS = 30
DEFAULT_LEAD = 0.4
DEFAULT_TAIL = 0.8  # a slide change needs a beat more air than a UI step
SILENCE = 0.01  # amplitude below which the model's own edge silence is trimmed
SHORT_SCENE_SEC = 2.5


def die(msg, code=1):
    print(msg, file=sys.stderr)
    sys.exit(code)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def slides_file(d):
    p = d / 'slides.json'
    return p if p.exists() else die(f'No {p}. Run: slides.py ingest <deck> --out {d}')


def draft(d, force):
    out = d / VOICE_DIR / 'script.json'
    if out.exists() and not force:
        die(f'{out} exists. Edit it, or pass --force to start over.')
    sf = slides_file(d)
    slides = json.loads(sf.read_text())['slides']
    scenes = [{'id': s['id'], 'slide': s['image'], 'text': (s.get('notes') or s.get('text') or '').replace('\n', ' ').strip()}
              for s in slides]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'slidesHash': sha(sf), 'lang': 'vie', 'voice': None, 'lexicon': {}, 'scenes': scenes},
                              ensure_ascii=False, indent=2) + '\n')
    print(out)


def speakable(text, lexicon):
    # Longest keys first so "Standard O/S" wins over "O/S".
    for k in sorted(lexicon, key=len, reverse=True):
        text = text.replace(k, lexicon[k])
    return text


def gpu_backend():
    """'cuda', 'mps' (Apple Silicon) or None. Unsupported MPS ops fall back to the CPU per op."""
    os.environ.setdefault('PYTORCH_ENABLE_MPS_FALLBACK', '1')
    try:
        import torch
        if torch.cuda.is_available():
            return 'cuda'
        if torch.backends.mps.is_available():
            return 'mps'
    except Exception:
        pass
    return None


def load_tts(device):
    from vieneu import Vieneu
    if device == 'cpu':
        return Vieneu(backend='onnx', device='cpu'), 'cpu'
    gpu = gpu_backend()
    if device == 'gpu' and not gpu:
        die('--device gpu, but no GPU is usable in this venv (CUDA or Apple MPS). Re-run setup-voice.sh with SVV_VOICE_DEVICE=gpu on a machine with an NVIDIA GPU or Apple Silicon.')
    if gpu:
        try:
            return Vieneu(backend='pytorch', device=gpu), gpu
        except Exception as e:  # e.g. too little VRAM; the CPU path always works
            if device == 'gpu':
                raise
            print(f'GPU ({gpu}) load failed ({e}); falling back to CPU', file=sys.stderr)
    return Vieneu(backend='onnx', device='cpu'), 'cpu'


def speak(device, texts, kw):
    tts, used = load_tts(device)
    try:
        # GPU batches every scene into shared forward passes; on CPU infer_batch runs sequentially anyway.
        wavs = tts.infer_batch(texts, **kw) if used != 'cpu' else [tts.infer(t, **kw) for t in texts]
    except Exception as e:
        if device != 'auto' or used == 'cpu':
            raise
        print(f'GPU ({used}) failed while speaking ({e}); retrying on CPU', file=sys.stderr)
        tts, used = load_tts('cpu')
        wavs = [tts.infer(t, **kw) for t in texts]
    return tts.sample_rate, wavs, used


def trim(wav, sr):
    import numpy as np
    loud = np.flatnonzero(np.abs(wav) > SILENCE)
    if not len(loud):
        return wav
    margin = int(0.02 * sr)
    return wav[max(0, loud[0] - margin):loud[-1] + margin]


def fit(wav, sr, fps, lead, tail):
    """Pad a spoken clip with silence and round it up to whole frames; return (clip, frames)."""
    import numpy as np
    body = np.concatenate([np.zeros(int(lead * sr), np.float32), wav.astype(np.float32), np.zeros(int(tail * sr), np.float32)])
    frames = max(1, math.ceil(len(body) * fps / sr))
    total = round(frames * sr / fps)
    return np.pad(body, (0, total - len(body))), frames


def generate(d, a):
    import numpy as np
    import soundfile as sf
    vd = d / VOICE_DIR
    sp = vd / 'script.json'
    if not sp.exists():
        die(f'No {sp}. Run: voice.py draft {d}')
    script = json.loads(sp.read_text())
    slf = slides_file(d)
    if script.get('slidesHash') != sha(slf):
        die('slides.json changed after the voice script was drafted. Re-draft (voice.py draft --force) and re-apply your edits.', 2)
    expected = [s['id'] for s in json.loads(slf.read_text())['slides']]
    ids = [s['id'] for s in script['scenes']]
    if ids != expected:
        die(f'Script scenes {ids} do not match the slides {expected}. Keep one scene per slide, in order.', 2)
    empty = [s['id'] for s in script['scenes'] if not s.get('text', '').strip()]
    if empty:
        die(f'Slides with no narration: {", ".join(empty)}')

    old, old_voice, fps = {}, None, a.fps or script.get('fps') or DEFAULT_FPS
    mp = vd / 'voice.json'
    only = set(a.only.split(',')) if a.only else None
    if only:
        unknown = only - set(ids)
        if unknown:
            die(f'--only: unknown slide ids {", ".join(sorted(unknown))}')
        if not mp.exists():
            die('--only needs an earlier full generate (no voice/voice.json yet).')
        prev = json.loads(mp.read_text())
        if a.fps and prev.get('fps') != a.fps:
            die(f'The earlier clips were timed for {prev.get("fps")} fps. Regenerate without --only to change fps.')
        fps = prev['fps']
        old, old_voice = {s['id']: s for s in prev['scenes']}, prev.get('voice')

    # A partial re-speak keeps the earlier speaker so the clips still match.
    voice = a.voice or script.get('voice') or old_voice
    lexicon = script.get('lexicon') or {}
    text_hash = lambda s: hashlib.sha256(speakable(s['text'], lexicon).encode()).hexdigest()[:16]
    todo = [s for s in script['scenes'] if not only or s['id'] in only]
    if only:
        stale = [s['id'] for s in script['scenes'] if s['id'] not in only and old.get(s['id'], {}).get('textHash') != text_hash(s)]
        if stale:
            die(f'No up-to-date clip for {", ".join(stale)} (its text or the lexicon changed). Add it to --only.')
    t0 = time.time()
    kw = {'voice': voice} if voice else {}
    texts = [speakable(s['text'], lexicon) for s in todo]
    sr, wavs, device = speak(a.device, texts, kw)
    spoken = dict(zip((s['id'] for s in todo), wavs))
    print(f'spoke {len(todo)} slide(s) on {device} in {time.time() - t0:.1f}s', file=sys.stderr)

    scenes, clips, start = [], [], 0
    for n, s in enumerate(script['scenes'], 1):
        f = f'{VOICE_DIR}/{n:02d}-{s["id"]}.wav'
        if s['id'] in spoken:
            speech = trim(np.asarray(spoken[s['id']], np.float32), sr)
            clip, frames = fit(speech, sr, fps, a.lead, a.tail)
            sf.write(d / f, clip, sr)
            speech_sec = len(speech) / sr
        else:
            prev = old[s['id']]
            clip, file_sr = sf.read(d / prev['file'], dtype='float32')
            if file_sr != sr:
                die(f'{prev["file"]} is {file_sr} Hz, expected {sr}. Regenerate without --only.')
            frames, speech_sec, f = prev['frames'], prev['speechSec'], prev['file']
        clips.append(clip)
        scenes.append({'id': s['id'], 'file': f, 'speechSec': round(speech_sec, 3),
                       'durationSec': frames / fps, 'frames': frames, 'startFrame': start,
                       'textHash': text_hash(s)})
        start += frames

    track = np.concatenate(clips)
    peak = float(np.max(np.abs(track))) if len(track) else 0
    if peak > 0.89:  # keep the joined track under ~-1 dBFS
        track = track * (0.89 / peak)
    sf.write(vd / 'narration.wav', track, sr)

    import vieneu
    manifest = {
        'engine': f'VieNeu-TTS v3 Turbo (vieneu {getattr(vieneu, "__version__", "?")})',
        'device': device, 'voice': voice, 'lang': script.get('lang', 'vie'), 'sampleRate': sr, 'fps': fps,
        'leadSec': a.lead if not only else prev.get('leadSec', a.lead),
        'slidesHash': sha(slf), 'scriptHash': sha(sp),
        'audio': f'{VOICE_DIR}/narration.wav', 'totalFrames': start, 'totalSec': round(start / fps, 3),
        'scenes': scenes,
    }
    mp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n')
    clock = lambda f: f'{int(f / fps // 60)}:{f / fps % 60:04.1f}'
    lines = [f'# {d.name} — transcript', '']
    for sc, s in zip(scenes, script['scenes']):
        lines += [f'**{clock(sc["startFrame"])} · slide {sc["id"][1:]}**', '', s['text'], '']
    (vd / 'transcript.md').write_text('\n'.join(lines))
    for s in scenes:
        warn = '  (short: viewers need time to read the slide)' if s['durationSec'] < SHORT_SCENE_SEC else ''
        print(f'{s["id"]:>6}  {s["durationSec"]:6.2f}s  frames {s["startFrame"]}+{s["frames"]}{warn}')
    print(f'total {manifest["totalSec"]}s → {mp}')


def main():
    os.environ.setdefault('HF_HUB_CACHE', str(Path(sys.prefix).parent / 'hf'))
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest='cmd', required=True)
    pd = sub.add_parser('draft')
    pd.add_argument('dir')
    pd.add_argument('--force', action='store_true')
    pg = sub.add_parser('generate')
    pg.add_argument('dir')
    pg.add_argument('--device', choices=['auto', 'cpu', 'gpu'], default='auto')
    pg.add_argument('--voice')
    pg.add_argument('--only')
    pg.add_argument('--lead', type=float, default=DEFAULT_LEAD)
    pg.add_argument('--tail', type=float, default=DEFAULT_TAIL)
    pg.add_argument('--fps', type=int)
    a = p.parse_args()
    d = Path(a.dir).resolve()
    if a.cmd == 'draft':
        draft(d, a.force)
    else:
        generate(d, a)


if __name__ == '__main__':
    main()
