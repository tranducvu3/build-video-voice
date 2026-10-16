#!/usr/bin/env bash
# Install (once) the Remotion project that animates slide videos.
#   setup-renderer.sh <skill-dir> <renderer-dir>
# <renderer-dir> lives outside the skill folder (e.g. ~/.local/share/build-video-voice/renderer).
# Re-copies the template only when it changed. node_modules from the feature-guide plugin's
# renderer is linked when it pins the same packages, otherwise npm installs them (~1–2 min).
set -euo pipefail
root=${1:?skill dir}; dest=${2:?renderer dir}
tpl="$root/templates/remotion"
stamp=$(node -e '
const fs=require("fs"),p=require("path"),h=require("crypto").createHash("sha256");
const walk=d=>fs.readdirSync(d,{withFileTypes:true}).sort((a,b)=>a.name.localeCompare(b.name)).forEach(e=>{
  const f=p.join(d,e.name); if(e.name==="node_modules")return;
  if(e.isDirectory())walk(f); else h.update(p.relative(process.argv[1],f)).update(fs.readFileSync(f));});
walk(process.argv[1]); console.log(h.digest("hex").slice(0,16));' "$tpl")
if [ -f "$dest/.template-stamp" ] && [ "$(cat "$dest/.template-stamp")" = "$stamp" ] && [ -e "$dest/node_modules" ]; then
  echo "renderer ready: $dest"; exit 0
fi
mkdir -p "$dest"
find "$dest" -mindepth 1 -maxdepth 1 ! -name node_modules -exec rm -rf {} +
cp -R "$tpl"/. "$dest"/
deps() { node -e 'const j=require(process.argv[1]);console.log(JSON.stringify([j.dependencies,j.devDependencies]))' "$1"; }
if [ ! -e "$dest/node_modules" ]; then
  for fg in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}"/plugins/data/feature-guide-*/renderer; do
    if [ -d "$fg/node_modules" ] && [ -f "$fg/package.json" ] && [ "$(deps "$fg/package.json")" = "$(deps "$dest/package.json")" ]; then
      ln -s "$(cd "$fg/node_modules" && pwd -P)" "$dest/node_modules"
      echo "linked node_modules from $fg"
      break
    fi
  done
fi
[ -e "$dest/node_modules" ] || (cd "$dest" && npm ci --no-audit --no-fund)
echo "$stamp" > "$dest/.template-stamp"
echo "renderer installed: $dest"
