#!/usr/bin/env bash
# Build a "drone + Korean TTS narration" MP3 from a lyrics text file.
#
# Usage: make_song.sh <lyrics.txt> <out.mp3> [drone_freq_hz=220] [speed=0.95]
#
# - TTS: sherpa-onnx VITS Korean voice (mimic3 KSS) — natural Korean speech
# - Drone: ffmpeg sine wave at given Hz (default 220 = A3)
# - Mix: TTS @ 0 dB, drone @ -14 dB, stereo, 44.1 kHz, MP3 192kbps
set -euo pipefail

IN_TXT="${1:?lyrics text file required}"
OUT_MP3="${2:?output mp3 path required}"
FREQ="${3:-220}"
SPEED="${4:-0.95}"

HERE="$(cd "$(dirname "$0")" && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) Korean TTS → WAV (sherpa-onnx VITS, sample rate from model: 22050)
python3 "$HERE/tts_ko.py" "$IN_TXT" "$TMP/tts.wav" "$SPEED"

# 3) Get duration, add 1.5s lead-in + 2.5s tail
DUR_TTS=$(ffprobe -v error -show_entries format=duration \
                  -of default=nw=1:nk=1 "$TMP/tts.wav")
DUR_TOTAL=$(python3 -c "print(${DUR_TTS} + 4.0)")

# 4) Drone sine at FREQ Hz, matched length
ffmpeg -y -hide_banner -loglevel error \
    -f lavfi -t "$DUR_TOTAL" -i "sine=frequency=${FREQ}:sample_rate=44100" \
    -af "volume=-14dB,afade=t=in:st=0:d=1.0,afade=t=out:st=$(python3 -c "print(${DUR_TOTAL}-1.5)"):d=1.5" \
    "$TMP/drone.wav"

# 5) Delay TTS by 1.5s and pad to total length
ffmpeg -y -hide_banner -loglevel error -i "$TMP/tts.wav" \
    -af "adelay=1500|1500,apad=whole_dur=${DUR_TOTAL}" \
    "$TMP/tts_pad.wav"

# 6) Mix drone + TTS, encode to MP3 (192 kbps, joint stereo, 44.1 kHz)
ffmpeg -y -hide_banner -loglevel error \
    -i "$TMP/drone.wav" -i "$TMP/tts_pad.wav" \
    -filter_complex "[0:a][1:a]amix=inputs=2:duration=longest:dropout_transition=0,loudnorm=I=-16:TP=-1.5:LRA=11,aresample=44100" \
    -ac 2 -c:a libmp3lame -b:a 192k -id3v2_version 3 \
    "$OUT_MP3"

echo "wrote: $OUT_MP3 (${DUR_TOTAL}s, drone=${FREQ}Hz, speed=${SPEED})"
