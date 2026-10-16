---
name: build-video-voice
description: Turn an existing slide deck (PDF, PowerPoint/Keynote/ODP, an HTML deck such as a feature-guide keynote, or a folder of slide images) into an animated MP4 with a lively spoken voice-over that explains each slide, generated locally by VieNeu-TTS. The camera zooms to whatever is being explained, with highlight rings, callout chips, chapter cards, a chapter bar and captions (Remotion), every slide timed to its voice. Picks the GPU when there is an NVIDIA card or an Apple Silicon Mac, otherwise the CPU. Use when the user asks to "make a video from these slides", "add voice / narration / voice-over to a deck", "tạo video từ slide", "thuyết minh / lồng tiếng cho slide".
argument-hint: "<deck-path> [--out DIR] [--device auto|cpu|gpu] [--voice NAME]"
allowed-tools: Bash, Read, Write, Edit, AskUserQuestion
---

# Slide deck → narrated video

```bash
P="${CLAUDE_SKILL_DIR}/scripts"; VD="${XDG_DATA_HOME:-$HOME/.local/share}/build-video-voice/voice"; PY="$VD/.venv/bin/python"
```
The deck is the first argument. If there is none, ask for the path. Pass any `--device` /
`--voice` arguments on to `generate` in step 4, and `--out` to `ingest` in step 2.

The slides are the picture; the voice explains them and the camera follows the voice. Slides are
not redesigned, only framed, highlighted and annotated.

The engine is [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo (Apache-2.0),
running on this machine: no API key, and no text leaves the machine. It is a Vietnamese model
with English code-switching. If the deck is in English, tell the user the voice will be English
spoken by a Vietnamese voice, and let them decide whether to go on.

## 1. Voice engine and renderer (install once)
```bash
bash "$P/setup-voice.sh" "$VD"
bash "$P/setup-renderer.sh" "${CLAUDE_SKILL_DIR}" "$R"
```
with `R="${XDG_DATA_HOME:-$HOME/.local/share}/build-video-voice/renderer"`.
- Voice needs `uv`. If `nvidia-smi` sees a GPU it installs the CUDA build (PyTorch, ~7 GB); on
  an Apple Silicon Mac the MPS build (under 1 GB); otherwise the CPU build (ONNX Runtime).
  `SVV_VOICE_DEVICE=cpu|gpu` forces one. Tell the user which device it picked.
- The renderer is a Remotion project (Node 20+). Both scripts link an identical install left by
  the `feature-guide` plugin instead of downloading again.
- First installs and the first generate take a few minutes: run them in the background and do
  steps 2–3 meanwhile.

## 2. Export the slides and find their regions
```bash
python3 -I "$P/slides.py" ingest "<deck>" [--out DIR]
python3 -I "$P/slides.py" regions "$DIR"
```
- `ingest` writes `slides/NN.png` (1920×1080) and `slides.json` (text + speaker notes) into
  `<deck-dir>/<deck-name>-video/` by default. Call it `$DIR`.
  - **PDF** (poppler) is the most reliable input. **.pptx/.ppt/.odp/.key** go through LibreOffice
    (`soffice`); .pptx speaker notes seed the script. **HTML decks** are screenshotted with
    headless Chrome at `#s1`, `#s2`, … (`--url-pattern '#/{i}'` for reveal.js, `--count N`).
    **A folder of images** is one slide per image, natural order.
- `regions` writes `regions.json`: numbered boxes (`r1`, `r2`, …) for every image and text block
  on each slide, plus `regions/NN.png` overlays showing them. Only PDF-backed decks get regions;
  for others, give focus boxes as `[x, y, w, h]` in slide pixels.
- Look at every slide and its overlay (tile 4 per image with ffmpeg `xstack` to save context).
  Check none is blank or cut off. Text the PDF hides behind other shapes also gets boxes —
  ignore those. Block boxes can be coarse; for one line, read line boxes with
  `pdftohtml -xml -i -f N -l N` and scale by 1920 / page width.

## 3. Script: beats that point the camera
```bash
"$PY" "$P/voice.py" draft "$DIR"
```
`voice/script.json` has one scene per slide, in order. Rewrite it:
- **Keep it short.** Target ~2.5 words/s and roughly 5–8 s per content slide; a 25-slide deck
  should land around 2–3 minutes. Explain what matters and skip what the viewer can read; never
  read a rules slide line by line, pick the 2–3 rules people trip over.
- **Beats.** Each scene is `beats: [{text, focus, callout?}]`, 1–4 beats. A beat is one or two
  short spoken sentences, and `focus` is what the camera frames while it is spoken: a region id
  (`"r3"`), several (`["r1","r2"]`, framed together), a box `[x,y,w,h]`, or `null` for the whole
  slide. Follow the order the eye should move. `callout` is a short chip (≤ 30 chars) for the
  number or button that must stick (`"Beginner 42 km · Advanced 84 km"`, `"Nhớ bấm Đồng bộ!"`).
  Use it on a few beats, not all.
- **Section slides** (a title-only divider) become animated chapter cards:
  `"kind": "section", "section": {"n": 1, "title": "Thể lệ cuộc thi", "short": "Thể lệ"}`.
  Numbered sections drive the chapter bar (`short` is its label); an aside without `n` takes
  a `kicker` instead (`"Mẹo nhỏ"`). Give each one a single short beat ("Phần một: thể lệ.").
- **Tone.** Lively and warm, like a colleague hyping a team event: short sentences,
  exclamations, "bạn"/"mình", a question now and then. The opening slide greets and promises
  what the viewer gets; the closing slide recaps in one line, says where to get help, signs off.
  The model's cues `[cười]`, `[thở dài]`, `[hắng giọng]` work inline; use `[cười]` once at most.
- **`lexicon`**: written form → spoken form for acronyms, units, dates, URLs and numbers
  (`"km": "ki lô mét"`, `"IT": "ai ti"`, `"sports.techcoop.vn": "sports chấm techcoop chấm vi en"`).
  Captions show the written `text`.
- **Voice.** Prefer a natural-style voice (*Trúc Ly*, *Ngọc Huyền*, *Đoan Trang*, female;
  *Hải Đăng*, *Quốc Tuấn*, male). The news-style ones (*Mai Anh*, *Thùy Dung*, *Minh Đức*) sound
  flat on explainer videos. `speed` (default 1.08) and `temperature` (default 0.9) live in the
  script too.
- Optional `theme`: `{primary, deep, accent, light, highlight, ground}` colours; default teal/amber.

Show the user the whole script (per slide: number, beats with their focus/callout) and the
voice, then ask (AskUserQuestion) whether to generate it. It is new spoken content, so don't
skip this.

## 4. Generate the voice
```bash
"$PY" "$P/voice.py" generate "$DIR" [--device auto|cpu|gpu] [--voice "Trúc Ly"] [--speed 1.1]
```
- Every beat is spoken separately (the GPU batches them all), stretched to `speed` without a
  pitch change, then each slide's beats are joined with `--gap` (0.25 s) between them and
  `--lead`/`--tail` (0.35 s / 0.55 s) around. Output: `voice/NN-<id>.wav`,
  `voice/narration.wav`, `voice/transcript.md`, `voice/voice.json` (per-slide and per-beat
  frames). Report the device and time.
- To fix wording or pronunciation, edit `script.json` and re-speak only those slides:
  `generate "$DIR" --only p03,p07`.

## 5. Stills → draft → final
```bash
python3 -I "$P/slides.py" render "$DIR" --still <frame>      # → _assets/stills/fNNNNN.png (half size)
python3 -I "$P/slides.py" render "$DIR" --draft              # → out/draft.mp4, 960×540
```
The video is animated with Remotion: each slide arrives with a short settle-and-blur, the
camera glides to each beat's focus and drifts slowly while it is spoken, a highlight ring dims
the rest, callout chips pop in, section slides become chapter cards, a chapter bar and label run
along the top, and captions show the beat being spoken. A soft subtitle track is muxed in too.
- **Stills first.** For a few beats (with focus, with callouts, a section card), take frame
  `scene.startFrame + beat.startFrame + 0.6·beat.frames` from `voice.json`, render them, tile
  them and look: is the focus framed, readable, not under the caption, chip not covering what's
  being said? Edit `focus`/`callout` in `script.json` and re-render; that needs no new voice.
  Changing a beat's `text` does: `generate --only <id>` (`render` names the slides).
- Then render the draft and give the user its path, plus `voice/narration.wav`.
- Options: `--captions off`, `--progress off`, `--subs none`. `--engine ffmpeg` is a plain
  fallback without Node (still slides, `--motion zoom`, `--fade 0.3`).

**Final**, once the user approves the draft:
```bash
python3 -I "$P/slides.py" render "$DIR" --out "<dest>/<deck-name>-voice.mp4"
```
`render` prints the duration next to the voice's `totalSec`; they must match (`OFF BY`
otherwise). The destination folder ends up with just the mp4 — scratch files (props, stills)
live under `$DIR/_assets/` and the transcript stays in `$DIR/voice/transcript.md`. Then give the
user the path, length, voice and device.
