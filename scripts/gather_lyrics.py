#!/usr/bin/env python3
"""Semi-automatic lyrics-gathering helper.

For each song in `SONGS`, this script:
  1. Skips if the target .txt already exists.
  2. Opens Melon's search page in your default browser.
  3. You copy the lyrics from the song page and paste into the terminal.
  4. Press a sentinel line (default: a single line containing "END") to finish.
  5. The pasted text is saved to lyrics/NN_title.txt.

Run on YOUR machine (not the agent's sandbox):

    python3 scripts/gather_lyrics.py

You can pass a starting index to skip songs you already have:

    python3 scripts/gather_lyrics.py --start 3

Output directory defaults to ./lyrics next to this script's parent.
"""
from __future__ import annotations

import argparse
import os
import sys
import urllib.parse
import webbrowser
from dataclasses import dataclass


@dataclass
class Song:
    no: int
    title: str            # display title (Korean)
    filename: str         # output filename stem (e.g. "01_광야를_지나며")
    search_query: str     # what to search on Melon


SONGS = [
    Song(1, "광야를 지나며",        "01_광야를_지나며",        "광야를 지나며"),
    Song(2, "실로암",              "02_실로암",              "실로암 CCM"),
    Song(3, "이런 교회 되게 하소서", "03_이런_교회_되게_하소서", "이런 교회 되게 하소서"),
    Song(4, "감사함으로",           "04_감사함으로",           "감사함으로 CCM"),
    Song(5, "행복합니다 (이재훈)",   "05_행복합니다",           "이재훈 행복합니다"),
    Song(6, "소문의 낙원 (악동뮤지션)","06_소문의_낙원",         "악동뮤지션 소문의 낙원"),
    Song(7, "잇쉬가 잇샤에게",      "07_잇쉬가_잇샤에게",      "잇쉬가 잇샤에게"),
    Song(8, "요게벳의 노래",        "08_요게벳의_노래",        "요게벳의 노래"),
    Song(9, "시편 139편",          "09_시편_139편",          "시편 139편 CCM"),
]


def melon_search_url(q: str) -> str:
    return "https://www.melon.com/search/total/index.htm?q=" + urllib.parse.quote(q)


def read_paste(sentinel: str = "END") -> str:
    """Read multi-line input from stdin until a line equals the sentinel."""
    lines: list[str] = []
    print(f"  가사를 붙여넣고, 마지막에 빈 줄에 '{sentinel}' 만 입력 후 Enter:")
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == sentinel:
            break
        lines.append(line)
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1,
                    help="첫 번째로 처리할 곡 번호 (1~9). 이미 받은 곡 건너뛸 때")
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "..", "lyrics"),
                    help="가사 .txt 저장 폴더 (기본: ./lyrics)")
    ap.add_argument("--sentinel", default="END",
                    help="입력 종료 표시 단어 (기본: END)")
    ap.add_argument("--no-browser", action="store_true",
                    help="브라우저 자동 오픈 비활성화")
    args = ap.parse_args()

    out_dir = os.path.abspath(args.dir)
    os.makedirs(out_dir, exist_ok=True)
    print(f"가사 저장 폴더: {out_dir}\n")

    for s in SONGS:
        if s.no < args.start:
            continue
        out_path = os.path.join(out_dir, f"{s.filename}.txt")
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            print(f"[{s.no:02d}/9] {s.title}  →  이미 있음, 스킵")
            continue
        url = melon_search_url(s.search_query)
        print(f"\n[{s.no:02d}/9] {s.title}")
        print(f"  검색: {url}")
        if not args.no_browser:
            try:
                webbrowser.open(url, new=2)
            except Exception:
                pass
        print("  → 멜론에서 곡 클릭 → 가사 탭 → 전체 선택 복사")
        text = read_paste(args.sentinel)
        if not text.strip():
            print("  (빈 입력 — 다음 곡으로)")
            continue
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"  ✓ 저장: {out_path}  ({len(text)} chars)")

    print("\n끝. 다음 명령으로 MP3 일괄 생성:")
    print("  python3 scripts/build_all.py")


if __name__ == "__main__":
    main()
