# build-video-voice

A Claude Code skill (`/build-video-voice`) that turns a slide deck you already have into an
animated video with a voice-over that explains each slide.

It is a customised version of `feature-guide:build-video-voice` from
[Techcoop-vn/techcoop-claude-plugins](https://github.com/Techcoop-vn/techcoop-claude-plugins):
the same local VieNeu-TTS voice engine, but the picture comes from an existing deck instead of
a feature-guide storyboard, and the video is assembled with Remotion.

## What it does

1. **Exports the slides and their regions** — PDF, PowerPoint/Keynote/ODP (via LibreOffice), an
   HTML deck (e.g. a feature-guide keynote, via headless Chrome) or a folder of images → one
   1920×1080 PNG per slide, plus each slide's text and speaker notes. For PDF decks it also
   finds numbered regions (`r1`, `r2`, …) for every image and text block.
2. **Writes the narration** — Claude drafts the script as *beats* per slide; each beat pairs one
   or two spoken sentences with a `focus` (the region the camera frames while it is spoken) and
   an optional callout chip, and the full script is shown for approval.
3. **Speaks it locally** with [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo
   (Vietnamese, with English code-switching). GPU (NVIDIA CUDA / Apple MPS) when available,
   otherwise CPU. No API key; no text leaves the machine.
4. **Renders the video** — the camera zooms to whatever is being explained, with highlight
   rings, callout chips, chapter cards, a chapter bar and captions, every slide timed to its
   voice, plus a soft subtitle track and a transcript. Draft first, then final.

## Install

Clone it as a personal skill, so it is available as `/build-video-voice` in every project:

```bash
git clone git@github.com:tranducvu3/slide-video-voice.git ~/.claude/skills/build-video-voice
```

Update with `git -C ~/.claude/skills/build-video-voice pull`. Then:
`/build-video-voice path/to/deck.pdf`

The voice engine installs once into `~/.local/share/build-video-voice/voice`, and the Remotion
renderer once into `~/.local/share/build-video-voice/renderer` (both outside the skill folder,
so updates keep them).

## Requirements

- `ffmpeg` / `ffprobe`, Python 3.10+
- `uv` (installs the voice engine once into the plugin data dir; ~7 GB for the CUDA build,
  a few hundred MB for CPU — an identical install left by `feature-guide` is reused)
- Node 20+ (the Remotion renderer; an identical install left by `feature-guide` is reused)
- PDF decks: poppler (`pdftoppm`, `pdftotext`, `pdfinfo`)
- PowerPoint / Keynote / ODP decks: LibreOffice (`soffice`)
- HTML decks: Google Chrome or Chromium

## Scripts

- `SKILL.md` — the workflow Claude follows
- `scripts/slides.py ingest <deck>` — export slides → `<deck>-video/slides/`, `slides.json`
- `scripts/slides.py regions <project>` — find the numbered regions → `regions.json`, overlays
- `scripts/voice.py draft|generate <project>` — narration script and voice clips
- `scripts/slides.py render <project> [--draft] [--still <frame>] [--captions off] [--subs none]`
- `scripts/setup-voice.sh <voice-dir>` — one-time voice engine install
- `scripts/setup-renderer.sh <skill-dir> <renderer-dir>` — one-time Remotion renderer install

The voice engine is Apache-2.0; see its repository for model terms.
