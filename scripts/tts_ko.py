"""Synthesize Korean speech to WAV using sherpa-onnx VITS (mimic3 KSS).

Usage:
    python3 tts_ko.py <input.txt> <output.wav> [speed=0.95]

Reads a text file, splits into stanzas (blank-line separated), synthesizes
each line, joins with short silences between sentences and longer silences
between stanzas, and writes a single mono WAV at the model's sample rate.
"""
from __future__ import annotations

import os
import re
import sys

import numpy as np
import soundfile as sf
import sherpa_onnx


_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
# Allow override via env var; otherwise look in repo's ./voices.
MODEL_DIR = os.environ.get(
    "PIPER_KO_MODEL_DIR",
    os.path.join(_ROOT, "voices", "vits-mimic3-ko_KO-kss_low"),
)
MODEL = os.path.join(MODEL_DIR, "ko_KO-kss_low.onnx")
TOKENS = os.path.join(MODEL_DIR, "tokens.txt")
ESPEAK_DATA = os.path.join(MODEL_DIR, "espeak-ng-data")


def load_tts() -> sherpa_onnx.OfflineTts:
    cfg = sherpa_onnx.OfflineTtsConfig(
        model=sherpa_onnx.OfflineTtsModelConfig(
            vits=sherpa_onnx.OfflineTtsVitsModelConfig(
                model=MODEL, tokens=TOKENS, data_dir=ESPEAK_DATA,
            ),
            num_threads=4,
        ),
        max_num_sentences=2,
    )
    return sherpa_onnx.OfflineTts(cfg)


def chunk_lyrics(text: str) -> list[list[str]]:
    """Split lyrics into a list of stanzas, each being a list of sentences."""
    text = text.replace("\r\n", "\n")
    stanzas: list[list[str]] = []
    current: list[str] = []
    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            if current:
                stanzas.append(current)
                current = []
            continue
        # Split a long line into shorter sentences at natural breaks.
        parts = re.split(r"(?<=[.!?…])\s+", line)
        for p in parts:
            p = p.strip()
            if p:
                current.append(p)
    if current:
        stanzas.append(current)
    return stanzas


def main() -> None:
    in_path = sys.argv[1]
    out_path = sys.argv[2]
    speed = float(sys.argv[3]) if len(sys.argv) > 3 else 0.95

    text = open(in_path, encoding="utf-8").read()
    stanzas = chunk_lyrics(text)

    tts = load_tts()
    sr = tts.sample_rate
    sentence_gap = np.zeros(int(0.4 * sr), dtype=np.float32)
    stanza_gap   = np.zeros(int(1.1 * sr), dtype=np.float32)

    audio_parts: list[np.ndarray] = []
    total_sents = sum(len(s) for s in stanzas)
    done = 0
    for si, stanza in enumerate(stanzas):
        if si > 0:
            audio_parts.append(stanza_gap)
        for li, line in enumerate(stanza):
            if li > 0:
                audio_parts.append(sentence_gap)
            out = tts.generate(line, sid=0, speed=speed)
            audio_parts.append(np.asarray(out.samples, dtype=np.float32))
            done += 1
            print(f"  [{done}/{total_sents}]", file=sys.stderr)

    full = np.concatenate(audio_parts) if audio_parts else np.zeros(1, np.float32)
    # Light gain normalization
    peak = float(np.max(np.abs(full)) or 1.0)
    if peak > 0:
        full = full * (0.9 / peak)
    sf.write(out_path, full, sr, subtype="PCM_16")
    print(f"wrote {out_path}  ({len(full)/sr:.2f}s, sr={sr})")


if __name__ == "__main__":
    main()
