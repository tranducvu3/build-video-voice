# slide-video-voice

A Claude Code plugin that turns a slide deck you already have into a video with a voice-over
that explains each slide.

It is a customised version of `feature-guide:build-video-voice` from
[Techcoop-vn/techcoop-claude-plugins](https://github.com/Techcoop-vn/techcoop-claude-plugins):
the same local VieNeu-TTS voice engine, but the picture comes from an existing deck instead of
a feature-guide storyboard, and the video is assembled with ffmpeg instead of Remotion.

## What it does

1. **Exports the slides** — PDF, PowerPoint/Keynote/ODP (via LibreOffice), an HTML deck
   (e.g. a feature-guide keynote, via headless Chrome) or a folder of images → one 1920×1080
   PNG per slide, plus each slide's text and speaker notes.
2. **Writes the narration** — Claude drafts one spoken explanation per slide from the slide
   image, its text and notes (opening slide = introduction, closing slide = conclusion) and
   shows you the full script for approval.
3. **Speaks it locally** with [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo
   (Vietnamese, with English code-switching). GPU (NVIDIA CUDA / Apple MPS) when available,
   otherwise CPU. No API key; no text leaves the machine.
4. **Renders the video** — every slide stays on screen exactly as long as its explanation,
   one narration track, a soft subtitle track and a transcript. Draft first, then final.

## Install

```
/plugin marketplace add tranducvu3/slide-video-voice
/plugin install slide-video-voice@slide-video-voice
/reload-plugins
```

Then: `/slide-video-voice:build-video-voice path/to/deck.pdf`

## Requirements

- `ffmpeg` / `ffprobe`, Python 3.10+
- `uv` (installs the voice engine once into the plugin data dir; ~7 GB for the CUDA build,
  a few hundred MB for CPU — an identical install left by `feature-guide` is reused)
- PDF decks: poppler (`pdftoppm`, `pdftotext`, `pdfinfo`)
- PowerPoint / Keynote / ODP decks: LibreOffice (`soffice`)
- HTML decks: Google Chrome or Chromium

## Scripts

- `scripts/slides.py ingest <deck>` — export slides → `<deck>-video/slides/`, `slides.json`
- `scripts/voice.py draft|generate <project>` — narration script and voice clips
- `scripts/slides.py render <project> [--draft] [--motion zoom] [--fade 0.3] [--subs none]`
- `scripts/setup-voice.sh <voice-dir>` — one-time voice engine install

The voice engine is Apache-2.0; see its repository for model terms.
