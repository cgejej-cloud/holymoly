#!/usr/bin/env python3
"""Batch MP3 builder.

Scans `lyrics/` for *.txt files and produces matching MP3s in `audio/`,
using the same drone-tone + Korean VITS TTS pipeline as make_song.sh.

Run on YOUR machine after gather_lyrics.py:

    python3 scripts/build_all.py
    python3 scripts/build_all.py --freq 196   # drone = G3 instead of A3
    python3 scripts/build_all.py --speed 1.0  # slightly faster narration
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)

    ap = argparse.ArgumentParser()
    ap.add_argument("--lyrics-dir", default=os.path.join(root, "lyrics"))
    ap.add_argument("--out-dir",    default=os.path.join(root, "audio"))
    ap.add_argument("--freq", type=float, default=220.0,
                    help="드론 주파수 Hz (기본 220=A3)")
    ap.add_argument("--speed", type=float, default=0.95,
                    help="TTS 속도 배율 (기본 0.95)")
    ap.add_argument("--force", action="store_true",
                    help="기존 MP3 있어도 다시 생성")
    args = ap.parse_args()

    lyrics_dir = os.path.abspath(args.lyrics_dir)
    out_dir = os.path.abspath(args.out_dir)
    os.makedirs(out_dir, exist_ok=True)

    if not os.path.isdir(lyrics_dir):
        sys.exit(f"가사 폴더 없음: {lyrics_dir}\n"
                 f"먼저 'python3 scripts/gather_lyrics.py' 로 가사를 모아 주세요.")

    make_song = os.path.join(here, "make_song.sh")
    if not os.path.exists(make_song):
        sys.exit(f"make_song.sh 없음: {make_song}")

    txts = sorted(f for f in os.listdir(lyrics_dir) if f.endswith(".txt"))
    if not txts:
        sys.exit(f"가사 파일이 없습니다: {lyrics_dir}")

    print(f"가사 폴더: {lyrics_dir}")
    print(f"MP3 출력:  {out_dir}")
    print(f"드론:      {args.freq} Hz  ·  속도: {args.speed}x\n")

    ok, skip, fail = 0, 0, 0
    for i, name in enumerate(txts, 1):
        stem = os.path.splitext(name)[0]
        in_txt = os.path.join(lyrics_dir, name)
        out_mp3 = os.path.join(out_dir, f"{stem}.mp3")
        if os.path.exists(out_mp3) and not args.force:
            print(f"[{i:02d}/{len(txts)}] {stem}  →  스킵 (이미 존재)")
            skip += 1
            continue
        print(f"[{i:02d}/{len(txts)}] {stem}  →  합성 중…")
        try:
            subprocess.run(
                ["bash", make_song, in_txt, out_mp3,
                 str(args.freq), str(args.speed)],
                check=True,
            )
            ok += 1
        except subprocess.CalledProcessError as e:
            print(f"  ✗ 실패: {e}")
            fail += 1

    print(f"\n끝: 성공 {ok} · 스킵 {skip} · 실패 {fail}")


if __name__ == "__main__":
    main()
