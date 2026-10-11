#!/usr/bin/env python3
"""解答例 PDF から正解を取り、content/<id>/exam.json を作る（既存の問題文と解説は残す）。
content/index.json と、その回のチェックリストの雛形も作る。

    python3 tools/init_exam.py 2025-r07-aki
"""

from __future__ import annotations

import argparse
import json
import re

import pymupdf

from exams import CHECKLIST, CONTENT, EXAM_IDS, QUESTION_COUNT, exam_by_id, kaitou_pdf

CHOICES = ["ア", "イ", "ウ", "エ"]
ANSWER_RE = re.compile(r"問\s*(\d+)\s+([アイウエ]|（注）)\s")
NOTE_RE = re.compile(r"（注）[ \t]*(\S[^\n]*)")


def read_answers(exam_id: str) -> tuple[dict[int, str | None], str]:
    """問番号ごとの正解と、解答例の注記を返す。注記の付いた問（問題として成立しないなど）の正解は None。"""
    with pymupdf.open(kaitou_pdf(exam_id)) as doc:
        text = "".join(page.get_text() for page in doc)
    # 午前Ⅱの節だけを見る（解答例に午前Ⅰなどが並ぶ回に備える）。
    start = text.find("午前Ⅱ")
    section = text[start:] if start >= 0 else text
    answers: dict[int, str | None] = {}
    for no, choice in ANSWER_RE.findall(section + " "):
        answers.setdefault(int(no), None if choice == "（注）" else choice)
    note = next((m.group(1).strip() for m in NOTE_RE.finditer(section) if m.group(1).strip()), "")
    if None in answers.values() and not note:
        raise SystemExit("注記の付いた問がありますが、注記の文を読めませんでした。")
    expected = set(range(1, QUESTION_COUNT + 1))
    if set(answers) != expected:
        raise SystemExit(f"正解を {QUESTION_COUNT} 問分読めませんでした: {sorted(answers)}")
    return answers, note


def write_json(path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("exam_id")
    args = parser.parse_args()
    exam_id, title, _, _ = exam_by_id(args.exam_id)
    answers, note = read_answers(exam_id)

    path = CONTENT / exam_id / "exam.json"
    old = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"questions": []}
    old_by_no = {question["no"]: question for question in old["questions"]}
    questions = []
    for no in range(1, QUESTION_COUNT + 1):
        image = f"{exam_id}/q{no:02d}.webp"
        if not (CONTENT / image).is_file():
            raise SystemExit(f"問題画像がありません。先に tools/cut.py を実行します: {image}")
        previous = old_by_no.get(no, {})
        question: dict[str, object] = {"no": no, "answer": answers[no]}
        if answers[no] is None:
            question["answerNote"] = note
        questions.append(
            question
            | {
                "image": image,
                "stem": previous.get("stem", ""),
                "choices": previous.get("choices", {choice: "" for choice in CHOICES}),
                "visuals": previous.get("visuals", []),
                "explanation": previous.get("explanation", ""),
            }
        )
    write_json(path, {"id": exam_id, "title": title, "questions": questions})

    present = [
        {"id": eid, "title": exam_by_id(eid)[1]}
        for eid in EXAM_IDS
        if (CONTENT / eid / "exam.json").exists()
    ]
    write_json(CONTENT / "index.json", present)

    checklist = CHECKLIST / f"{exam_id}.json"
    if not checklist.exists():
        write_json(
            checklist,
            {
                "examId": exam_id,
                "questions": [
                    {
                        "no": no,
                        "text": {"status": "未着手", "comments": []},
                        "explanation": {
                            choice: {"status": "未着手", "comments": []} for choice in CHOICES
                        },
                    }
                    for no in range(1, QUESTION_COUNT + 1)
                ],
            },
        )
    print(f"{exam_id}: 正解 {''.join(answers[no] or '－' for no in range(1, QUESTION_COUNT + 1))}")


if __name__ == "__main__":
    main()
