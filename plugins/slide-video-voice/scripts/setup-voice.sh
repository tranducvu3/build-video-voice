#!/usr/bin/env bash
# Install (once) the VieNeu-TTS voice environment used by build-video-voice.
#   setup-voice.sh <voice-dir>
# <voice-dir> should be ${CLAUDE_PLUGIN_DATA}/voice so it survives plugin updates.
# Picks the device: an NVIDIA GPU (nvidia-smi answers) or an Apple Silicon Mac (its GPU via
# MPS) installs vieneu[cuda] (PyTorch; on macOS the extra just pulls the MPS-capable torch),
# anything else installs the torch-free CPU build (ONNX Runtime). SVV_VOICE_DEVICE=cpu|gpu
# forces one. Reinstalls only when the device or the pinned version changes.
# An identical install left by the feature-guide plugin is linked instead of downloaded again
# (the GPU build is ~7 GB).
set -euo pipefail
dest=${1:?voice dir}
VIENEU_VERSION=3.8.3
# Both match upstream's uv.lock. With huggingface_hub 2.x the cache shards blobs into
# subfolders, so a model's .onnx and its external .data resolve to different directories and
# onnxruntime refuses to load it ("External data path escapes model directory").
ONNXRUNTIME_VERSION=1.24.4
HF_HUB_VERSION=1.13.0
PYTHON_VERSION=3.12

device=${SVV_VOICE_DEVICE:-auto}
if [ "$device" = auto ]; then
  if [ "$(uname -s)" = Darwin ]; then
    [ "$(uname -m)" = arm64 ] && device=gpu || device=cpu
  elif command -v nvidia-smi >/dev/null && nvidia-smi -L >/dev/null 2>&1; then device=gpu; else device=cpu; fi
fi
case "$device" in gpu|cpu) ;; *) echo "SVV_VOICE_DEVICE must be cpu or gpu (got $device)" >&2; exit 1 ;; esac

stamp="vieneu-$VIENEU_VERSION-ort-$ONNXRUNTIME_VERSION-hf-$HF_HUB_VERSION-$device-py$PYTHON_VERSION"
if [ -f "$dest/.stamp" ] && [ "$(cat "$dest/.stamp")" = "$stamp" ] && [ -x "$dest/.venv/bin/python" ]; then
  echo "voice ready: $dest ($device)"; exit 0
fi

for other in "$(dirname "$(dirname "$dest")")"/feature-guide-*/voice; do
  if [ -f "$other/.stamp" ] && [ "$(cat "$other/.stamp")" = "$stamp" ] && [ -x "$other/.venv/bin/python" ]; then
    other=$(cd "$other" && pwd -P)
    mkdir -p "$(dirname "$dest")"
    rm -rf "$dest"; ln -s "$other" "$dest"
    echo "voice ready: $dest → $other ($device, shared with feature-guide)"; exit 0
  fi
done

command -v uv >/dev/null || { echo "uv is required: curl -LsSf https://astral.sh/uv/install.sh | sh" >&2; exit 1; }
[ -L "$dest" ] && rm "$dest"
mkdir -p "$dest"
rm -rf "$dest/.venv" "$dest/.stamp"
uv venv --quiet --python "$PYTHON_VERSION" "$dest/.venv"
pkg="vieneu==$VIENEU_VERSION"; [ "$device" = gpu ] && pkg="vieneu[cuda]==$VIENEU_VERSION"
uv pip install --quiet --python "$dest/.venv/bin/python" "$pkg" "onnxruntime==$ONNXRUNTIME_VERSION" "huggingface_hub==$HF_HUB_VERSION"
echo "$stamp" > "$dest/.stamp"
echo "voice installed: $dest ($device)"
