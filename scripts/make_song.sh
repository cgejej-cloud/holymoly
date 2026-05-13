#!/usr/bin/env bash
# Build a "drone + Korean TTS narration" MP3 from a lyrics text file.
#
# Usage: make_song.sh <lyrics.txt> <out.mp3> [drone_freq_hz=220] [speed=130]
#
# - TTS: espeak-ng Korean voice (offline)
# - Drone: ffmpeg sine wave at given Hz (default 220 = A3)
# - Mix: TTS @ 0 dB, drone @ -14 dB, stereo, 44.1 kHz, MP3 192kbps
set -euo pipefail

IN_TXT="${1:?lyrics text file required}"
OUT_MP3="${2:?output mp3 path required}"
FREQ="${3:-220}"
SPEED="${4:-130}"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

# 1) Light cleanup: strip leading/trailing whitespace per line, drop empties,
#    add a short pause hint between sections (ellipsis triggers a pause in espeak-ng).
python3 - "$IN_TXT" > "$TMP/clean.txt" <<'PY'
import sys, re, pathlib
src = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8")
out = []
prev_blank = False
for raw in src.splitlines():
    line = raw.strip()
    if not line:
        prev_blank = True
        continue
    if prev_blank and out:
        out.append("...")  # short pause between stanzas
    # normalize whitespace inside the line
    line = re.sub(r"\s+", " ", line)
    out.append(line)
    prev_blank = False
sys.stdout.write("\n".join(out) + "\n")
PY

# 2) Korean TTS → WAV
espeak-ng -v ko -s "$SPEED" -p 45 -a 180 -g 6 \
    -f "$TMP/clean.txt" -w "$TMP/tts.wav"

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
