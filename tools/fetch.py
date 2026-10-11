#!/usr/bin/env python3
"""IPA の過去問題ページから午前Ⅱの問題冊子と解答例を取得し、content/sources.json に記録する。

    python3 tools/fetch.py              # 全回
    python3 tools/fetch.py 2025-r07-aki # 指定した回だけ
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import re
import urllib.request

from exams import CONTENT, EXAM_IDS, IPA_BASE, exam_by_id, kaitou_pdf, mondai_pdf

SOURCES = CONTENT / "sources.json"


def get(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def find_url(page_html: str, file_name: str) -> str:
    match = re.search(r'href="([^"]*/' + re.escape(file_name) + r')"', page_html)
    if not match:
        raise SystemExit(f"年度ページに {file_name} が見つかりません。")
    href = match.group(1)
    return href if href.startswith("http") else "https://www.ipa.go.jp" + href


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("ids", nargs="*", help="回の id。省略すると全回")
    args = parser.parse_args()

    sources = json.loads(SOURCES.read_text(encoding="utf-8")) if SOURCES.exists() else {}
    today = datetime.date.today().isoformat()
    for exam_id in args.ids or EXAM_IDS:
        _, _, page, stem = exam_by_id(exam_id)
        page_url = f"{IPA_BASE}{page}.html"
        page_html = get(page_url).decode("utf-8", errors="replace")
        entry: dict[str, object] = {"page": page_url, "fetched": today}
        for kind, path in (("mondai", mondai_pdf(exam_id)), ("kaitou", kaitou_pdf(exam_id))):
            suffix = "qs" if kind == "mondai" else "ans"
            url = find_url(page_html, f"{stem}_pm_am2_{suffix}.pdf")
            body = get(url)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(body)
            entry[kind] = {"url": url, "sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body)}
        sources[exam_id] = entry
        print(f"{exam_id}: 取得しました")

    ordered = {exam_id: sources[exam_id] for exam_id in EXAM_IDS if exam_id in sources}
    SOURCES.parent.mkdir(parents=True, exist_ok=True)
    SOURCES.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
