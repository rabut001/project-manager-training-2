#!/usr/bin/env python3
"""content/ の問題データを検証する。CI とビルド前に実行する。

    python3 tools/validate.py          # 公開に必要な項目がすべて埋まっているか
    python3 tools/validate.py --draft  # 作業中。問題文と解説が空でもよい
"""

from __future__ import annotations

import argparse
import json
import sys

from exams import CONTENT, EXAM_IDS, QUESTION_COUNT, exam_by_id

CHOICES = ["ア", "イ", "ウ", "エ"]
VISUALS = {"figure", "table", "image"}


def check_exam(exam_id: str, draft: bool) -> list[str]:
    errors: list[str] = []
    path = CONTENT / exam_id / "exam.json"
    if not path.is_file():
        return [f"{exam_id}: exam.json がありません"]
    exam = json.loads(path.read_text(encoding="utf-8"))
    if exam.get("id") != exam_id or exam.get("title") != exam_by_id(exam_id)[1]:
        errors.append(f"{exam_id}: id または title が一覧と一致しません")
    questions = exam.get("questions", [])
    if [q.get("no") for q in questions] != list(range(1, QUESTION_COUNT + 1)):
        errors.append(f"{exam_id}: 問番号が 1〜{QUESTION_COUNT} の順に並んでいません")
    for q in questions:
        where = f"{exam_id} 問{q.get('no')}"
        if q.get("answer") not in CHOICES:
            errors.append(f"{where}: answer がア〜エではありません")
        image = q.get("image", "")
        if image != f"{exam_id}/q{q.get('no', 0):02d}.webp" or not (CONTENT / image).is_file():
            errors.append(f"{where}: 問題画像 {image} がありません")
        choices = q.get("choices")
        if not isinstance(choices, dict) or list(choices) != CHOICES:
            errors.append(f"{where}: choices のキーがア〜エではありません")
        visuals = q.get("visuals")
        if not isinstance(visuals, list) or not set(visuals) <= VISUALS:
            errors.append(f"{where}: visuals が不正です")
        for key in ("stem", "explanation"):
            if not isinstance(q.get(key), str):
                errors.append(f"{where}: {key} が文字列ではありません")
        if draft:
            continue
        if not q.get("stem"):
            errors.append(f"{where}: stem が空です")
        if isinstance(choices, dict) and not all(choices.values()):
            errors.append(f"{where}: choices に空の肢があります")
        explanation = q.get("explanation") or ""
        if not explanation:
            errors.append(f"{where}: explanation が空です")
        elif f"{q.get('answer')}が正解" not in explanation:
            errors.append(f"{where}: explanation に「{q.get('answer')}が正解」がありません")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--draft", action="store_true")
    args = parser.parse_args()
    index = json.loads((CONTENT / "index.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in index]
    errors: list[str] = []
    if ids != [eid for eid in EXAM_IDS if eid in ids]:
        errors.append("index.json の並びが新しい順ではありません")
    for item in index:
        if item.get("title") != exam_by_id(item["id"])[1]:
            errors.append(f"index.json: {item['id']} の title が一覧と一致しません")
        errors += check_exam(item["id"], args.draft)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        sys.exit(f"{len(errors)} 件の問題があります。")
    print(f"{len(ids)} 回を検証しました。")


if __name__ == "__main__":
    main()
