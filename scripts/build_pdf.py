#!/usr/bin/env python3
"""Build the Genesis Quiz PDF with Adobe-compatible Korean fonts.

This regenerates `genesis_quiz.pdf` at the repository root using ReportLab,
embedding Nanum TrueType fonts as subsets so Adobe Acrobat / Reader can
display, search and copy Korean text on all platforms.
"""
from __future__ import annotations

import os
import sys

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen.canvas import Canvas

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

from data.quiz import PARTS, QUESTIONS  # noqa: E402


# ── Fonts ─────────────────────────────────────────────────────────────────────

FONT_DIR = "/usr/share/fonts/truetype/nanum"

FONTS = {
    "Serif":      os.path.join(FONT_DIR, "NanumMyeongjo.ttf"),
    "SerifBold":  os.path.join(FONT_DIR, "NanumMyeongjoBold.ttf"),
    "Sans":       os.path.join(FONT_DIR, "NanumGothic.ttf"),
    "SansBold":   os.path.join(FONT_DIR, "NanumGothicBold.ttf"),
}


def register_fonts() -> None:
    for name, path in FONTS.items():
        if not os.path.exists(path):
            raise SystemExit(
                f"required font missing: {path}\n"
                "install with: apt-get install -y fonts-nanum"
            )
        pdfmetrics.registerFont(TTFont(name, path, subfontIndex=0))


# ── Palette ───────────────────────────────────────────────────────────────────

GOLD       = HexColor("#B8893E")
GOLD_LIGHT = HexColor("#D7B070")
INK        = HexColor("#1F1A17")
INK_SOFT   = HexColor("#3A332E")
GRAY       = HexColor("#8A857F")
GRAY_LIGHT = HexColor("#B8B3AD")
BURGUNDY   = HexColor("#7C2D2A")
RULE       = HexColor("#D9D2C7")

PAGE_W, PAGE_H = A4
MARGIN_L = 70
MARGIN_R = 70
MARGIN_T = 70
MARGIN_B = 80
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


# ── Text helpers ──────────────────────────────────────────────────────────────

def text_w(c: Canvas, font: str, size: float, s: str) -> float:
    return c.stringWidth(s, font, size)


def wrap_text(c: Canvas, font: str, size: float, s: str, max_w: float) -> list[str]:
    out: list[str] = []
    for paragraph in s.split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for w in words:
            cand = (cur + " " + w) if cur else w
            if text_w(c, font, size, cand) <= max_w:
                cur = cand
            else:
                if cur:
                    out.append(cur)
                if text_w(c, font, size, w) > max_w:
                    buf = ""
                    for ch in w:
                        if text_w(c, font, size, buf + ch) <= max_w:
                            buf += ch
                        else:
                            if buf:
                                out.append(buf)
                            buf = ch
                    cur = buf
                else:
                    cur = w
        if cur:
            out.append(cur)
    return out


# ── Page chrome ───────────────────────────────────────────────────────────────

def draw_footer(c: Canvas, page_no: int) -> None:
    c.setFont("Serif", 9)
    c.setFillColor(GRAY)
    y = MARGIN_B - 40
    c.drawString(MARGIN_L, y, "창세기 퀴즈 · Genesis Quiz")
    c.drawRightString(PAGE_W - MARGIN_R, y, "질문 · 힌트 · 정답")
    c.drawCentredString(PAGE_W / 2, y, f"— {page_no} —")


# ── Doc / cursor ──────────────────────────────────────────────────────────────

class Doc:
    def __init__(self, out_path: str):
        c = Canvas(out_path, pagesize=A4, pageCompression=1)
        c.setTitle("창세기 퀴즈 · Genesis Quiz")
        c.setAuthor("Genesis Quiz")
        c.setSubject("창세기 1–50장 · 30문항 퀴즈 (질문 · 힌트 · 정답)")
        c.setKeywords("성경, 창세기, 퀴즈, Genesis, Bible, Quiz")
        c.setCreator("build_pdf.py")
        c.setProducer("ReportLab + Nanum TTF — Adobe-compatible build")
        # set /Lang on the document catalog for Adobe accessibility
        c._doc.Catalog.Lang = "(ko-KR)"
        self.c = c
        self.page_no = 1
        self.y = PAGE_H - MARGIN_T

    def new_page(self) -> None:
        draw_footer(self.c, self.page_no)
        self.c.showPage()
        self.page_no += 1
        self.y = PAGE_H - MARGIN_T

    def remaining(self) -> float:
        return self.y - MARGIN_B

    def ensure_space(self, h: float) -> None:
        if self.remaining() < h:
            self.new_page()

    def finalize(self) -> None:
        draw_footer(self.c, self.page_no)
        self.c.save()


# ── Measurement (mirrors drawing) ─────────────────────────────────────────────

# Line-height multipliers tuned for Nanum metrics.
LH = 1.55

# Layout constants (kept in sync with draw fns)
Q_INDENT      = 26
INNER_INDENT  = 64
HINT_INDENT   = 38
ANS_INDENT    = 38

Q_FONT,    Q_SIZE     = "SansBold", 12
OPT_FONT,  OPT_SIZE   = "Serif",    11.5
FILL_FONT, FILL_SIZE  = "Serif",    11.5
OX_FONT,   OX_SIZE    = "Serif",    11.5
HINT_LBL_FONT, HINT_LBL_SIZE = "Sans", 10
HINT_FONT, HINT_SIZE  = "Serif",    10.5
ANS_LBL_FONT, ANS_LBL_SIZE   = "SansBold", 11
ANS_FONT,  ANS_SIZE   = "SansBold", 11
META_FONT, META_SIZE  = "Serif",    9.5


def lh(size: float) -> float:
    return size * LH


def measure_question(c: Canvas, q: dict) -> float:
    """Return total height required to render question `q`."""
    h = 0.0
    # meta line (+3pt gap)
    h += lh(META_SIZE) + 3
    # Q label + wrapped question
    q_lines = wrap_text(c, Q_FONT, Q_SIZE, q["q"], CONTENT_W - Q_INDENT)
    h += lh(Q_SIZE) * len(q_lines)
    h += 4
    # fill / options / ox / diamonds
    if "fill" in q:
        line = f"{q['fill']['prefix']}_______{q['fill']['suffix']}"
        h += lh(FILL_SIZE) * len(wrap_text(c, FILL_FONT, FILL_SIZE,
                                           line, CONTENT_W - INNER_INDENT))
        h += 6
    if "options" in q:
        h += lh(OPT_SIZE) * len(q["options"])
        h += 6
    if q.get("ox"):
        h += lh(OX_SIZE)
        h += 6
    if "diamonds" in q:
        h += lh(OPT_SIZE) * len(q["diamonds"])
        h += 6
    # hint
    label = "힌트."
    label_w = text_w(c, HINT_LBL_FONT, HINT_LBL_SIZE, label)
    avail = CONTENT_W - HINT_INDENT - label_w - 8
    h += lh(HINT_SIZE) * len(wrap_text(c, HINT_FONT, HINT_SIZE,
                                       q["hint"], avail))
    h += 4
    # answer
    label = "정답."
    label_w = text_w(c, ANS_LBL_FONT, ANS_LBL_SIZE, label)
    avail = CONTENT_W - ANS_INDENT - label_w - 8
    h += lh(ANS_SIZE) * len(wrap_text(c, ANS_FONT, ANS_SIZE,
                                      q["answer"], avail))
    h += 16  # gap to next question
    return h


# ── Drawing ───────────────────────────────────────────────────────────────────

def stars(level: int) -> str:
    return "★" * level + "☆" * (3 - level)


PART_HEADER_HEIGHT = lh(10) + 10 + lh(26) + 36


def draw_part_header(d: Doc, roman: str, title: str, sub: str,
                     first_question_height: float = 0) -> None:
    """Draw a Part heading. Starts a new page only if there's not enough room
    for the heading plus the next question (avoids orphan headers)."""
    needed = PART_HEADER_HEIGHT + max(first_question_height, 80)
    # Give part headers a bit of top air when not at the page top.
    if d.y < PAGE_H - MARGIN_T - 1:
        d.y -= 14
    if d.remaining() < needed:
        d.new_page()
    c = d.c
    c.setFont("Sans", 10)
    c.setFillColor(GOLD)
    c.drawString(MARGIN_L, d.y, f"Part {roman}")
    d.y -= lh(10) + 10
    c.setFont("SansBold", 26)
    c.setFillColor(INK)
    c.drawString(MARGIN_L, d.y, title)
    d.y -= lh(26) - 4
    c.setFont("Serif", 11)
    c.setFillColor(GRAY)
    c.drawString(MARGIN_L, d.y, sub)
    d.y -= 36


def draw_meta_line(d: Doc, q: dict) -> None:
    c = d.c
    c.setFont(META_FONT, META_SIZE)
    c.setFillColor(GRAY)
    pieces = [
        f"No. {q['no']:02d}",
        q["kind"],
        f"{stars(q['level'])} {q['level_name']}",
        q["ref"],
    ]
    line = "   ·   ".join(pieces)
    c.drawString(MARGIN_L, d.y, line)
    d.y -= lh(META_SIZE) + 3


def draw_q_text(d: Doc, q: dict) -> None:
    c = d.c
    c.setFont(Q_FONT, Q_SIZE)
    c.setFillColor(INK)
    c.drawString(MARGIN_L, d.y, "Q.")
    lines = wrap_text(c, Q_FONT, Q_SIZE, q["q"], CONTENT_W - Q_INDENT)
    for i, ln in enumerate(lines):
        if i > 0:
            d.y -= lh(Q_SIZE)
        c.drawString(MARGIN_L + Q_INDENT, d.y, ln)
    d.y -= lh(Q_SIZE)
    d.y -= 4


def draw_fill(d: Doc, fill: dict) -> None:
    c = d.c
    c.setFont(FILL_FONT, FILL_SIZE)
    c.setFillColor(INK_SOFT)
    line = f"{fill['prefix']}_______{fill['suffix']}"
    lines = wrap_text(c, FILL_FONT, FILL_SIZE, line, CONTENT_W - INNER_INDENT)
    for ln in lines:
        c.drawString(MARGIN_L + INNER_INDENT, d.y, ln)
        d.y -= lh(FILL_SIZE)
    d.y -= 6


def draw_options(d: Doc, options) -> None:
    c = d.c
    c.setFont(OPT_FONT, OPT_SIZE)
    c.setFillColor(INK_SOFT)
    for letter, text in options:
        c.drawString(MARGIN_L + INNER_INDENT, d.y, f"{letter}.")
        c.drawString(MARGIN_L + INNER_INDENT + 22, d.y, text)
        d.y -= lh(OPT_SIZE)
    d.y -= 6


def draw_ox(d: Doc) -> None:
    c = d.c
    c.setFont(OX_FONT, OX_SIZE)
    c.setFillColor(INK_SOFT)
    c.drawString(MARGIN_L + INNER_INDENT, d.y,
                 "O  (맞다 / 참)    ·    X  (틀리다 / 거짓)")
    d.y -= lh(OX_SIZE) + 6


def draw_diamonds(d: Doc, items) -> None:
    c = d.c
    c.setFont(OPT_FONT, OPT_SIZE)
    c.setFillColor(INK_SOFT)
    for it in items:
        c.drawString(MARGIN_L + INNER_INDENT, d.y, "◇")
        c.drawString(MARGIN_L + INNER_INDENT + 18, d.y, it)
        d.y -= lh(OPT_SIZE)
    d.y -= 6


def draw_hint(d: Doc, hint: str) -> None:
    c = d.c
    label = "힌트."
    c.setFont(HINT_LBL_FONT, HINT_LBL_SIZE)
    c.setFillColor(GOLD)
    label_w = text_w(c, HINT_LBL_FONT, HINT_LBL_SIZE, label)
    c.drawString(MARGIN_L + HINT_INDENT, d.y, label)
    c.setFont(HINT_FONT, HINT_SIZE)
    c.setFillColor(GRAY)
    avail = CONTENT_W - HINT_INDENT - label_w - 8
    lines = wrap_text(c, HINT_FONT, HINT_SIZE, hint, avail)
    for i, ln in enumerate(lines):
        if i > 0:
            d.y -= lh(HINT_SIZE)
        c.drawString(MARGIN_L + HINT_INDENT + label_w + 8, d.y, ln)
    d.y -= lh(HINT_SIZE) + 4


def draw_answer(d: Doc, ans: str) -> None:
    c = d.c
    label = "정답."
    c.setFont(ANS_LBL_FONT, ANS_LBL_SIZE)
    c.setFillColor(BURGUNDY)
    label_w = text_w(c, ANS_LBL_FONT, ANS_LBL_SIZE, label)
    c.drawString(MARGIN_L + ANS_INDENT, d.y, label)
    c.setFont(ANS_FONT, ANS_SIZE)
    avail = CONTENT_W - ANS_INDENT - label_w - 8
    lines = wrap_text(c, ANS_FONT, ANS_SIZE, ans, avail)
    for i, ln in enumerate(lines):
        if i > 0:
            d.y -= lh(ANS_SIZE)
        c.drawString(MARGIN_L + ANS_INDENT + label_w + 8, d.y, ln)
    d.y -= lh(ANS_SIZE) + 16


def draw_question(d: Doc, q: dict) -> None:
    h = measure_question(d.c, q)
    # If the question doesn't fit, push to new page (keep-together).
    if d.remaining() < h:
        d.new_page()
    draw_meta_line(d, q)
    draw_q_text(d, q)
    if "fill" in q:
        draw_fill(d, q["fill"])
    if "options" in q:
        draw_options(d, q["options"])
    if q.get("ox"):
        draw_ox(d)
    if "diamonds" in q:
        draw_diamonds(d, q["diamonds"])
    draw_hint(d, q["hint"])
    draw_answer(d, q["answer"])


# ── Cover page ────────────────────────────────────────────────────────────────

def draw_cover(d: Doc) -> None:
    c = d.c
    cx = PAGE_W / 2

    c.setFillColor(GOLD_LIGHT)
    c.circle(cx - 6, PAGE_H - 270, 1.4, fill=1, stroke=0)
    c.circle(cx + 6, PAGE_H - 270, 1.4, fill=1, stroke=0)

    c.setFillColor(GOLD)
    c.setFont("SansBold", 12)
    c.drawCentredString(cx, PAGE_H - 300, "A Walk Through")
    c.drawCentredString(cx, PAGE_H - 322, "THE BOOK OF GENESIS")

    c.setFillColor(INK)
    c.setFont("SansBold", 40)
    c.drawCentredString(cx, PAGE_H - 400, "창세기 퀴즈")

    c.setFillColor(INK_SOFT)
    c.setFont("Serif", 14)
    c.drawCentredString(cx, PAGE_H - 432, "질문 · 힌트 · 정답")

    c.setStrokeColor(GOLD)
    c.setLineWidth(1.0)
    c.line(cx - 95, PAGE_H - 470, cx + 95, PAGE_H - 470)

    c.setFillColor(GRAY)
    c.setFont("Serif", 11.5)
    c.drawCentredString(cx, PAGE_H - 500, "총 30문  ·  객관식 12  ·  주관식 18")
    c.drawCentredString(cx, PAGE_H - 522, "초급 9  ·  중급 10  ·  고급 11")
    c.drawCentredString(cx, PAGE_H - 544, "창세기 1장 1절 → 50장 20절")

    c.setFillColor(INK_SOFT)
    c.setFont("Serif", 13)
    c.drawCentredString(cx, PAGE_H - 640, "\"태초에 하나님이 천지를 창조하시니라\"")
    c.setFillColor(GOLD)
    c.setFont("SansBold", 11.5)
    c.drawCentredString(cx, PAGE_H - 662, "GENESIS 1:1")


# ── Quick answer key ──────────────────────────────────────────────────────────

def draw_answer_key_header(d: Doc) -> None:
    c = d.c
    cx = PAGE_W / 2
    c.setFillColor(INK)
    c.setFont("SansBold", 34)
    c.drawCentredString(cx, d.y, "정답 일람표")
    d.y -= lh(34) - 6
    c.setFillColor(GOLD)
    c.setFont("SansBold", 13)
    c.drawCentredString(cx, d.y, "Quick Answer Key")
    d.y -= 20
    c.setStrokeColor(GOLD)
    c.setLineWidth(0.8)
    c.line(cx - 80, d.y, cx + 80, d.y)
    d.y -= 32


def draw_answer_key(d: Doc) -> None:
    c = d.c
    draw_answer_key_header(d)

    col_num_x   = MARGIN_L + 4
    col_meta_x  = MARGIN_L + 42
    col_ans_x   = MARGIN_L + 180
    col_ans_w   = PAGE_W - MARGIN_R - col_ans_x - 4

    for q in QUESTIONS:
        meta = f"{q['ref']}  ·  {stars(q['level'])}"
        meta_lines = wrap_text(c, "Serif", 10.5, meta,
                               col_ans_x - col_meta_x - 8)
        ans_lines = wrap_text(c, "Serif", 10.5, q["answer_short"], col_ans_w)
        row_h = max(len(meta_lines), len(ans_lines)) * lh(10.5) + 10
        if d.remaining() < row_h + 6:
            d.new_page()
        top_y = d.y
        c.setFillColor(GRAY_LIGHT)
        c.setFont("Serif", 11)
        c.drawString(col_num_x, top_y, f"{q['no']:02d}")
        c.setFillColor(GRAY)
        c.setFont("Serif", 10.5)
        for i, ln in enumerate(meta_lines):
            c.drawString(col_meta_x, top_y - i * lh(10.5), ln)
        c.setFillColor(INK)
        for i, ln in enumerate(ans_lines):
            c.drawString(col_ans_x, top_y - i * lh(10.5), ln)
        d.y = top_y - row_h + 4
        c.setStrokeColor(RULE)
        c.setLineWidth(0.4)
        c.line(MARGIN_L, d.y + 2, PAGE_W - MARGIN_R, d.y + 2)
        d.y -= 6


# ── Main ──────────────────────────────────────────────────────────────────────

def build(out_path: str) -> None:
    register_fonts()
    d = Doc(out_path)

    draw_cover(d)
    d.new_page()

    q_by_no = {q["no"]: q for q in QUESTIONS}
    for part in PARTS:
        first_q = q_by_no[part["questions"][0]]
        draw_part_header(d, part["roman"], part["title"], part["sub"],
                         first_question_height=measure_question(d.c, first_q))
        for n in part["questions"]:
            draw_question(d, q_by_no[n])

    d.new_page()
    draw_answer_key(d)

    d.finalize()


if __name__ == "__main__":
    out = os.path.join(ROOT, "genesis_quiz.pdf")
    build(out)
    print(f"wrote {out}")
