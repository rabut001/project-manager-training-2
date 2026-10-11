#!/usr/bin/env python3
"""午前Ⅱの問題冊子（ページ全体が画像）を、問と問のあいだの余白で1問ずつ切り出し、WebP で保存する。

    python3 tools/cut.py 2025-r07-aki
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import pymupdf
from PIL import Image

from exams import CONTENT, QUESTION_COUNT, exam_by_id, mondai_pdf

THRESH = 180
MIN_RUN = 9
PAD_X = 40
PAD_Y = 36
RENDER_SCALE = 200 / 72
WEBP_QUALITY = 80
# OCR は「問」を別の字に読むことがある。実際に出た読み違いだけを足す。
HEADER_RE = re.compile(r"[問間癌則]\d+")


def dark_runs(row: bytes) -> list[tuple[int, int]]:
    runs: list[tuple[int, int]] = []
    start = None
    for x, pixel in enumerate(row):
        if pixel < THRESH:
            if start is None:
                start = x
        elif start is not None:
            if x - start >= MIN_RUN:
                runs.append((start, x))
            start = None
    if start is not None and len(row) - start >= MIN_RUN:
        runs.append((start, len(row)))
    return runs


def is_page_number(runs: list[tuple[int, int]], width: int) -> bool:
    if not runs:
        return False
    x0 = runs[0][0]
    x1 = runs[-1][1]
    span = x1 - x0
    center = (x0 + x1) / 2
    return 40 < span < 160 and abs(center - width / 2) < 120


def footer_top(samples: bytes, width: int, height: int) -> int:
    """下端から見て、ページ番号「- n -」の上端を返す。"""
    y = height - 1
    limit = int(height * 0.75)
    while y > limit:
        runs = dark_runs(samples[y * width : (y + 1) * width])
        if is_page_number(runs, width):
            while y > limit:
                above = samples[(y - 1) * width : y * width]
                center_band = above[width // 2 - 80 : width // 2 + 80]
                if not any(pixel < THRESH for pixel in center_band):
                    break
                y -= 1
            return y
        y -= 1
    return int(height * 0.90)


def content_bounds(
    samples: bytes, width: int, y0: int, y1: int
) -> tuple[int, int, int, int] | None:
    ink_rows: list[int] = []
    for y in range(y0, y1):
        row = samples[y * width : (y + 1) * width]
        if sum(pixel < THRESH for pixel in row) >= MIN_RUN:
            ink_rows.append(y)
    if not ink_rows:
        return None
    # ページ番号の手前にある孤立した汚れは、問の本文から大きく離れているので捨てる。
    kept = [ink_rows[0]]
    for y in ink_rows[1:]:
        if y - kept[-1] > 160:
            break
        kept.append(y)
    ink_rows = kept
    columns = [0] * width
    for y in ink_rows:
        row = samples[y * width : (y + 1) * width]
        for x, pixel in enumerate(row):
            if pixel < THRESH:
                columns[x] += 1
    clusters: list[list[int]] = []
    start = None
    for x, count in enumerate(columns):
        if count >= 3:
            if start is None:
                start = x
        elif start is not None:
            clusters.append([start, x])
            start = None
    if start is not None:
        clusters.append([start, width])
    merged: list[list[int]] = []
    for cluster in clusters:
        # 選択肢が左右に離れて並ぶ行も、一つの問として残す。
        if not merged or cluster[0] - merged[-1][1] > 180:
            merged.append(cluster)
        else:
            merged[-1][1] = cluster[1]
    main = max(merged, key=lambda item: item[1] - item[0])
    return main[0], ink_rows[0], main[1], ink_rows[-1] + 1


def load_page_image(doc: pymupdf.Document, page_index: int) -> pymupdf.Pixmap:
    xref = doc[page_index].get_images()[0][0]
    return pymupdf.Pixmap(doc, xref)


def header_ys(page: pymupdf.Page) -> list[float]:
    """問番号の行の上端を、ページ上のポイント座標で返す。"""
    clip = pymupdf.Rect(20, 30, 150, page.rect.height - 30)
    pix = page.get_pixmap(
        matrix=pymupdf.Matrix(3, 3),
        colorspace=pymupdf.csGRAY,
        alpha=False,
        clip=clip,
    )
    fd, path = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    pix.save(path)
    try:
        proc = subprocess.run(
            ["tesseract", path, "stdout", "-l", "jpn", "--psm", "6", "tsv"],
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        os.remove(path)
    lines: dict[tuple[str, str, str], list[list[str]]] = {}
    for row in proc.stdout.splitlines()[1:]:
        cols = row.split("\t")
        if len(cols) < 12 or cols[0] != "5" or not cols[11].strip():
            continue
        lines.setdefault((cols[2], cols[3], cols[4]), []).append(cols)
    ys: list[float] = []
    for words in lines.values():
        words.sort(key=lambda word: int(word[6]))
        text = "".join(word[11].strip() for word in words).replace(" ", "")
        text = text.lstrip("・･.．-* ")
        if HEADER_RE.match(text):
            top = min(int(word[7]) for word in words)
            ys.append(30 + top / 3)
    ys.sort()
    merged: list[float] = []
    for y in ys:
        if not merged or y - merged[-1] > 8:
            merged.append(y)
    return merged


def crop_questions(pdf_path: Path, out_dir: Path) -> list[Path]:
    doc = pymupdf.open(pdf_path)
    # 表紙・表記ルール・メモ用紙には問番号がない。ページは正立で描く。
    pages: list[tuple[int, pymupdf.Pixmap, list[int], int]] = []
    for page_index in range(doc.page_count):
        page = doc[page_index]
        ys = header_ys(page)
        if not ys:
            continue
        pix = page.get_pixmap(
            matrix=pymupdf.Matrix(RENDER_SCALE, RENDER_SCALE),
            colorspace=pymupdf.csGRAY,
            alpha=False,
        )
        tops = [max(0, round(y * RENDER_SCALE)) for y in ys]
        pages.append((page_index, pix, tops, footer_top(pix.samples, pix.width, pix.height)))
    total = sum(len(tops) for _, _, tops, _ in pages)
    if total != QUESTION_COUNT:
        doc.close()
        raise SystemExit(f"問の先頭が {total} 個でした。25 個である必要があります。")

    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    number = 1
    for _, pix, tops, footer in pages:
        samples = pix.samples
        width, height = pix.width, pix.height
        limits = tops + [footer]
        for index, top in enumerate(tops):
            bottom_limit = limits[index + 1]
            bounds = content_bounds(samples, width, top, bottom_limit)
            if bounds is None:
                doc.close()
                raise SystemExit(f"問{number} の領域が空です。")
            x0, y0, x1, y1 = bounds
            x0 = max(0, x0 - PAD_X)
            y0 = max(0, y0 - PAD_Y)
            x1 = min(width, x1 + PAD_X)
            y1 = min(bottom_limit, y1 + PAD_Y)
            if index + 1 < len(tops):
                y1 = min(y1, tops[index + 1] - 8)
            crop = bytearray()
            for y in range(y0, y1):
                crop += samples[y * width + x0 : y * width + x1]
            image = Image.frombytes("L", (x1 - x0, y1 - y0), bytes(crop))
            path = out_dir / f"q{number:02d}.webp"
            image.save(path, "WEBP", quality=WEBP_QUALITY, method=6)
            written.append(path)
            print(f"q{number:02d} {image.width}x{image.height} {path.stat().st_size // 1024}KB")
            number += 1
    doc.close()
    return written


def main() -> None:
    parser = argparse.ArgumentParser(description="午前Ⅱの問題冊子を1問ずつ切り出す。")
    parser.add_argument("exam_id", help="回の id（例: 2025-r07-aki）")
    args = parser.parse_args()
    exam_by_id(args.exam_id)
    pdf_path = mondai_pdf(args.exam_id)
    if not pdf_path.is_file():
        sys.exit(f"問題冊子がありません。先に tools/fetch.py を実行します: {pdf_path}")
    crop_questions(pdf_path, CONTENT / args.exam_id)


if __name__ == "__main__":
    main()
