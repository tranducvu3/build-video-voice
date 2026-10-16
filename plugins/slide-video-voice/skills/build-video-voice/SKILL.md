---
name: build-video-voice
description: Turn an existing slide deck (PDF, PowerPoint/Keynote/ODP, an HTML deck such as a feature-guide keynote, or a folder of slide images) into an MP4 video with a spoken voice-over that explains each slide, generated locally by VieNeu-TTS. Each slide stays on screen exactly as long as its explanation; the clips form one narration track with soft subtitles. Picks the GPU when there is an NVIDIA card or an Apple Silicon Mac, otherwise the CPU. Use when the user asks to "make a video from these slides", "add voice / narration / voice-over to a deck", "tạo video từ slide", "thuyết minh / lồng tiếng cho slide".
argument-hint: "<deck-path> [--out DIR] [--device auto|cpu|gpu] [--voice NAME]"
allowed-tools: Bash, Read, Write, Edit, SendUserFile, AskUserQuestion
---

# Slide deck → narrated video

```bash
P="${CLAUDE_PLUGIN_ROOT}/scripts"; VD="${CLAUDE_PLUGIN_DATA}/voice"; PY="$VD/.venv/bin/python"
```
The deck is the first argument. If there is none, ask for the path. Pass any `--device` /
`--voice` arguments on to `generate` in step 4, and `--out` to `ingest` in step 2.

The slides are the picture; the voice explains them. Nothing about the slides is redesigned:
every slide is shown as exported, full frame, for as long as its explanation lasts.

The engine is [VieNeu-TTS](https://github.com/pnnbao97/VieNeu-TTS) v3 Turbo (Apache-2.0),
running on this machine: no API key, and no text leaves the machine. It is a Vietnamese model
with English code-switching. If the deck is in English, tell the user the voice will be English
spoken by a Vietnamese voice, and let them decide whether to go on.

## 1. Voice engine (installs once)
```bash
bash "$P/setup-voice.sh" "$VD"
```
- Needs `uv` (the script says how to install it if it's missing).
- Device: if `nvidia-smi` sees a GPU it installs the CUDA build (PyTorch, ~7 GB); on an Apple
  Silicon Mac the PyTorch build that runs on the Mac's GPU (MPS, under 1 GB); otherwise the
  torch-free CPU build (ONNX Runtime, a few hundred MB). `SVV_VOICE_DEVICE=cpu|gpu` forces one.
  An identical install from the `feature-guide` plugin is linked instead of downloaded again.
  Tell the user which device it picked.
- The first install, and the first generate (it downloads the model), take a few minutes. Run
  the install in the background and do steps 2–3 meanwhile.

## 2. Export the slides
```bash
python3 -I "$P/slides.py" ingest "<deck>" [--out DIR]
```
- Writes `slides/NN.png` (1920×1080 by default) and `slides.json` (each slide's on-screen text
  and speaker notes) into the project dir, by default `<deck-dir>/<deck-name>-video/`.
  Call it `$DIR` from here on.
- **PDF**: `pdftoppm` / `pdftotext` (poppler). The most reliable input; when a conversion
  struggles, ask the user to export the deck to PDF.
- **.pptx / .ppt / .odp / .key**: converted with LibreOffice (`soffice`). Speaker notes are read
  from a .pptx and used to seed the script. Hidden slides are left out.
- **HTML deck**: each slide is screenshotted with headless Chrome at `<deck>#s1`, `#s2`, … (the
  feature-guide keynote format; its `data-note` speaker notes are picked up). Other decks: set
  `--url-pattern` (`'#/{i}'` for reveal.js, 0-based) and `--count N`. Raise `--wait-ms` if
  animations are caught mid-way.
- **Folder of images**: one slide per image, in natural sort order (`2.png` before `10.png`).
- Slides that aren't 16:9 are letterboxed on `--bg` at render time.

Look at every exported slide with Read (they are images) and check none is blank, cut off or
caught mid-animation before going on.

## 3. Script: one explanation per slide
```bash
"$PY" "$P/voice.py" draft "$DIR"
```
This writes `$DIR/voice/script.json` with one scene per slide, in order, seeded with the
slide's speaker notes, else its on-screen text. Seeds are raw material, not narration: rewrite
every scene's `text` from the slide image and `slides.json`:
- **Explain, don't read.** Say what the slide means and why it matters, in the order the eye
  moves over it (title → main visual → details). Mention every number, chart or table the slide
  shows and what it tells the viewer; don't recite each bullet word for word.
- **Opening slide** carries the introduction: greet, name the topic and who it is for, and
  outline what the video covers ("Video gồm ba phần: …"). About 15–25 s.
- **Section and transition slides** open their part ("Phần hai: triển khai.").
- **Closing slide** carries the conclusion: recap in one or two sentences, say where to get
  help or what to do next, and thank the viewer.
- Talk like a person presenting to a colleague: short spoken sentences, no bullet fragments,
  no "slide này có…". Aim for ~2.5 words per second on screen time; keep every slide at least
  ~3 s so viewers can read it, and dense slides long enough to take in.
- Keep exactly one scene per slide with its `id`. To skip a slide, delete it from the deck
  and re-ingest; don't leave a scene empty.
- **`lexicon`**: written form → how it should be spoken. Add every acronym, symbol, unit,
  email/URL and number the model would misread, e.g. `"CSV": "xê ét vê"`, `"KPI": "ka pê i"`,
  `"%": " phần trăm"`, `"Q3": "quý ba"`, `" / ": ", "`. Keep `text` readable (it becomes the
  subtitles); the lexicon is applied only at speak time.
- **`voice`**: a preset name, or null for the default (Hải Đăng). Editors' picks: Hải Đăng,
  Mai Anh, Thiện Minh, Trúc Ly, Thùy Dung, Ngọc Huyền, Quang Sơn, Ngọc Trân. `--voice`
  overrides it.

Show the user the whole script, one block per slide (slide number + its first line of text +
the narration), plus the voice name. Then ask (AskUserQuestion) whether to generate it as
written. It is new spoken content the user has not seen, so don't skip this.

## 4. Generate the voice
```bash
"$PY" "$P/voice.py" generate "$DIR" [--device auto|cpu|gpu] [--voice "Mai Anh"]
```
- `--device auto` (default) uses the GPU (`cuda` or `mps`) and falls back to the CPU if the GPU
  can't load the model or fails while speaking. Report the device it used and how long it took
  (the GPU batches every slide together; the CPU runs about 2× real time).
- Output: `voice/NN-<id>.wav` per slide, `voice/narration.wav` (all concatenated),
  `voice/transcript.md` (start time and text per slide) and `voice/voice.json` (per-slide
  `frames`/`startFrame` used by the render).
- It prints one line per slide with its duration and flags any slide under 2.5 s; lengthen
  that text.
- `--lead` / `--tail` (default 0.4 s / 0.8 s) set the silence before and after each
  explanation, i.e. the pause around each slide change. `--fps` (default 30).

Send `voice/narration.wav` with SendUserFile so the user can check pronunciation before any
video is rendered. To fix a slide, edit its text or the lexicon, then re-speak only that one:
```bash
"$PY" "$P/voice.py" generate "$DIR" --only p03,p07
```
The other clips are kept and the track and timings are rebuilt. A lexicon change touches every
slide that contains the term; the command names any it needs.

## 5. Draft → final
```bash
python3 -I "$P/slides.py" render "$DIR" --draft          # → $DIR/out/draft.mp4, 960×540, fast
```
Send the draft. Options, for draft and final alike:
- `--subs soft` (default) adds a subtitle track viewers can switch on (from `text`, timed per
  sentence); `--subs none` leaves it out.
- `--motion zoom` adds a slow 4% push-in on every slide; `--fade 0.3` fades each slide in from
  black. Default is a still slide with a hard cut, which suits text-heavy decks best.
- `--bg '#ffffff'` sets the letterbox colour for slides that aren't 16:9.

Fix wording, pronunciation or voice in `script.json` and `generate --only`. To change a slide's
picture, fix the deck, then `ingest --force` → `draft --force` (re-apply the script edits) →
`generate`. `generate` and `render` refuse to run on stale inputs and say which step to redo.

**Final**, once the user approves the draft:
```bash
python3 -I "$P/slides.py" render "$DIR" --out "<dest>/<deck-name>-voice.mp4" [same options]
```
Default `<dest>` is `$DIR/out/`. `render` prints the file's duration next to the voice's
`totalSec`; they must match (it prints `OFF BY` otherwise). Copy `voice/transcript.md` next to
the video as `<deck-name>-transcript.md`, then send the final file and tell the user its length,
the voice and the device used.
