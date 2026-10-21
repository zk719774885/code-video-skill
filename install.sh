#!/usr/bin/env bash
# code-video 一键安装（macOS / Linux / Git Bash）：bash install.sh [--remotion] [--hyperframes] [--video-home DIR]
set -e
SKILL="$(cd "$(dirname "$0")" && pwd)"; VIDEO_HOME="$HOME/claude-video"; R=0; HF=0
while [ $# -gt 0 ]; do case "$1" in --remotion) R=1;; --hyperframes) HF=1;; --video-home) VIDEO_HOME="$2"; shift;; esac; shift; done
for c in node python3 ffmpeg; do command -v $c >/dev/null || { [ $c = python3 ] && command -v python >/dev/null && continue; echo "缺少 $c，请先安装"; exit 1; }; done
PY=$(command -v python3 || command -v python)
echo "▶ Python 依赖 numpy scipy"; $PY -m pip install --quiet numpy scipy
echo "▶ sy-styles-20 依赖与浏览器内核"; (cd "$SKILL/engines/sy-styles-20" && npm install --silent && npx --yes playwright install chromium)
mkdir -p "$VIDEO_HOME"
if [ $R = 1 ]; then echo "▶ Remotion（>3 人营利公司商用需购买 Company License）"; (cd "$VIDEO_HOME" && [ -d remotion-studio ] || npx -y create-video@latest --yes --blank remotion-studio); npx -y skills add remotion-dev/skills -g -y -a claude-code; fi
if [ $HF = 1 ]; then echo "▶ HyperFrames"; (cd "$VIDEO_HOME" && [ -d hyperframes-studio ] || npx -y hyperframes@latest init hyperframes-studio --example blank --non-interactive); npx -y hyperframes@latest skills update; fi
echo "export SY_STYLES=\"$SKILL/engines/sy-styles-20\"" >> "$HOME/.bashrc" 2>/dev/null || true
echo "✔ 完成。引擎：$SKILL/engines/sy-styles-20；视频项目建议放在 $VIDEO_HOME"
