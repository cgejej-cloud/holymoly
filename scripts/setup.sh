#!/usr/bin/env bash
# One-shot setup for the song-MP3 pipeline.
# Run this once on your machine (macOS / Linux / WSL):
#
#   bash scripts/setup.sh
#
# Windows: use WSL or install manually (ffmpeg + python3 + pip below).
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"

# 1) ffmpeg
if ! command -v ffmpeg >/dev/null 2>&1; then
    echo "→ ffmpeg 설치"
    if command -v brew >/dev/null 2>&1; then
        brew install ffmpeg
    elif command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update && sudo apt-get install -y ffmpeg
    else
        echo "수동으로 ffmpeg 설치 후 다시 실행: https://ffmpeg.org/download.html"
        exit 1
    fi
fi

# 2) Python deps
echo "→ Python 패키지 설치 (sherpa-onnx, soundfile, numpy)"
python3 -m pip install --upgrade pip
python3 -m pip install sherpa-onnx soundfile numpy

# 3) Korean voice model
VOICES_DIR="$ROOT/voices"
MODEL_DIR="$VOICES_DIR/vits-mimic3-ko_KO-kss_low"
if [ ! -f "$MODEL_DIR/ko_KO-kss_low.onnx" ]; then
    echo "→ 한국어 음성 모델 다운로드 (약 60MB)"
    mkdir -p "$VOICES_DIR"
    cd "$VOICES_DIR"
    curl -fSL -o vits-mimic3-ko.tar.bz2 \
      "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-mimic3-ko_KO-kss_low.tar.bz2"
    tar xjf vits-mimic3-ko.tar.bz2
    rm -f vits-mimic3-ko.tar.bz2
    cd "$ROOT"
fi

echo
echo "✓ 설치 완료. 다음 순서로 사용:"
echo "  1) python3 scripts/gather_lyrics.py    # 가사를 브라우저에서 복사해 .txt로 저장"
echo "  2) python3 scripts/build_all.py        # 모든 .txt를 일괄 MP3로 합성"
