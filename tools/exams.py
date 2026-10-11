"""収録する回の一覧と、ツールが共有するパス。新しい順に並べる。"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
CACHE = ROOT / ".cache" / "pdf"
CHECKLIST = ROOT / "changes" / "0001-initial-build" / "checklist"
IPA_BASE = "https://www.ipa.go.jp/shiken/mondai-kaiotu/"
QUESTION_COUNT = 25

# (回の id, 表示名, IPA の年度ページ, IPA のファイル名の頭)
EXAMS: list[tuple[str, str, str, str]] = [
    ("2025-r07-aki", "令和7年度秋期", "2025r07", "2025r07a"),
    ("2024-r06-aki", "令和6年度秋期", "2024r06", "2024r06a"),
    ("2023-r05-aki", "令和5年度秋期", "2023r05", "2023r05a"),
    ("2022-r04-aki", "令和4年度秋期", "2022r04", "2022r04a"),
    ("2021-r03-aki", "令和3年度秋期", "2021r03", "2021r03a"),
    ("2020-r02-oct", "令和2年度10月", "2020r02", "2020r02o"),
    ("2019-h31-haru", "平成31年度春期", "2019h31", "2019h31h"),
    ("2018-h30-haru", "平成30年度春期", "2018h30", "2018h30h"),
    ("2017-h29-haru", "平成29年度春期", "2017h29", "2017h29h"),
    ("2016-h28-haru", "平成28年度春期", "2016h28", "2016h28h"),
    ("2015-h27-haru", "平成27年度春期", "2015h27", "2015h27h"),
    ("2014-h26-haru", "平成26年度春期", "2014h26", "2014h26h"),
    ("2013-h25-haru", "平成25年度春期", "2013h25", "2013h25h"),
    ("2012-h24-haru", "平成24年度春期", "2012h24", "2012h24h"),
    ("2011-h23-toku", "平成23年度特別", "2011h23", "2011h23tokubetsu"),
    ("2010-h22-haru", "平成22年度春期", "2010h22", "2010h22h"),
    ("2009-h21-haru", "平成21年度春期", "2009h21", "2009h21h"),
]

EXAM_IDS = [exam[0] for exam in EXAMS]


def exam_by_id(exam_id: str) -> tuple[str, str, str, str]:
    for exam in EXAMS:
        if exam[0] == exam_id:
            return exam
    raise SystemExit(f"回の id が一覧にありません: {exam_id}")


def mondai_pdf(exam_id: str) -> Path:
    return CACHE / exam_id / "am2-mondai.pdf"


def kaitou_pdf(exam_id: str) -> Path:
    return CACHE / exam_id / "am2-kaitou.pdf"
