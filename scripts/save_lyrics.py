#!/usr/bin/env python3
"""Save user-provided lyric text to a .txt file (and optionally render MP3).

This is a generic text → file utility. You provide the text, it writes the
file. It does not fetch anything from the internet.

Usage examples (run on YOUR machine):

  # 1) Pipe text in from a file (most common)
  python3 scripts/save_lyrics.py --name 02_실로암 < pasted.txt

  # 2) Paste interactively, end with a single line containing "END"
  python3 scripts/save_lyrics.py --name 02_실로암

  # 3) Read from the system clipboard (needs pyperclip installed)
  python3 scripts/save_lyrics.py --name 02_실로암 --clipboard

  # 4) Same as above and immediately build the MP3
  python3 scripts/save_lyrics.py --name 02_실로암 --clipboard --build

By default files go to ./lyrics/<name>.txt and MP3s to ./audio/<name>.mp3.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys


SENTINEL_DEFAULT = "END"


def _read_stdin_interactive(sentinel: str) -> str:
    print(f"가사 본문을 붙여넣고, 마지막에 빈 줄에 '{sentinel}' 만 입력 후 Enter:",
          file=sys.stderr)
    lines: list[str] = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == sentinel:
            break
        lines.append(line)
    return "\n".join(lines)


def _read_stdin_piped() -> str:
    return sys.stdin.read()


def _read_clipboard() -> str:
    try:
        import pyperclip  # type: ignore
    except ImportError:
        sys.exit("pyperclip 이 필요해요. 설치:  pip install pyperclip")
    text = pyperclip.paste()
    if not text:
        sys.exit("클립보드가 비어 있습니다.")
    return text


def _safe_name(name: str) -> str:
    """Allow Korean/ASCII letters, digits, dash, underscore. Replace the rest."""
    cleaned = re.sub(r"[^\w가-힣ㄱ-ㅎㅏ-ㅣ\-]+", "_", name, flags=re.UNICODE).strip("_")
    return cleaned or "lyrics"


def _normalize(text: str) -> str:
    """Light cleanup: strip trailing spaces per line, collapse multiple blanks."""
    out_lines: list[str] = []
    prev_blank = False
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            if not prev_blank:
                out_lines.append("")
            prev_blank = True
        else:
            out_lines.append(line)
            prev_blank = False
    # trim leading/trailing blanks
    while out_lines and not out_lines[0].strip():
        out_lines.pop(0)
    while out_lines and not out_lines[-1].strip():
        out_lines.pop()
    return "\n".join(out_lines) + "\n"


def main() -> None:
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)

    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--name", required=True,
                    help="파일명 (확장자 제외). 예: 02_실로암")
    ap.add_argument("--lyrics-dir", default=os.path.join(root, "lyrics"),
                    help="저장 폴더 (기본: ./lyrics)")
    ap.add_argument("--clipboard", action="store_true",
                    help="시스템 클립보드에서 본문 읽기 (pyperclip 필요)")
    ap.add_argument("--sentinel", default=SENTINEL_DEFAULT,
                    help=f"대화식 입력 종료 표시 단어 (기본: {SENTINEL_DEFAULT})")
    ap.add_argument("--build", action="store_true",
                    help="저장 후 make_song.sh 로 MP3 까지 합성")
    ap.add_argument("--freq", type=float, default=220.0,
                    help="드론 주파수 Hz (기본 220=A3)")
    ap.add_argument("--speed", type=float, default=0.95,
                    help="TTS 속도 배율 (기본 0.95)")
    ap.add_argument("--force", action="store_true",
                    help="기존 파일이 있어도 덮어쓰기")
    args = ap.parse_args()

    if args.clipboard:
        text = _read_clipboard()
    elif sys.stdin.isatty():
        text = _read_stdin_interactive(args.sentinel)
    else:
        text = _read_stdin_piped()

    text = _normalize(text)
    if not text.strip():
        sys.exit("본문이 비어 있어 저장하지 않았습니다.")

    safe = _safe_name(args.name)
    out_dir = os.path.abspath(args.lyrics_dir)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{safe}.txt")
    if os.path.exists(out_path) and not args.force:
        sys.exit(f"이미 존재합니다: {out_path}\n덮어쓰려면 --force")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✓ 저장: {out_path}  ({len(text)} chars, {text.count(chr(10))} lines)")

    if args.build:
        make_song = os.path.join(here, "make_song.sh")
        if not os.path.exists(make_song):
            sys.exit(f"make_song.sh 없음: {make_song}")
        audio_dir = os.path.join(root, "audio")
        os.makedirs(audio_dir, exist_ok=True)
        mp3 = os.path.join(audio_dir, f"{safe}.mp3")
        print(f"\n→ MP3 합성: {mp3}")
        subprocess.run(
            ["bash", make_song, out_path, mp3, str(args.freq), str(args.speed)],
            check=True,
        )


if __name__ == "__main__":
    main()
