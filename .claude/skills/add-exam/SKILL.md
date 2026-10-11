---
name: add-exam
description: PM 午前Ⅱの回を取り込む（PDF 取得、問題画像の切り出し、正解、問題文、解説、レビュー）。新しい回を足すとき、既存の回の問題文や解説を作り直すときに使う。
---

# 回の取り込み

回は `tools/exams.py` の `EXAMS` に載っている必要がある。新しい回なら、先に `changes/` に案件を作り、`EXAMS` と `docs/spec.md` の収録範囲を更新する。チェックリストの置き場所（`tools/exams.py` の `CHECKLIST`）も、その案件のフォルダに向ける。

## 1. 取得・切り出し・正解

```sh
tools/devc.sh python3 tools/fetch.py <id>
tools/devc.sh python3 tools/cut.py <id>
tools/devc.sh python3 tools/init_exam.py <id>
```

`cut.py` が 25 問にならないときは、OCR が「問N」を読み落としている。問題冊子のページを画像にして原因を確かめ、`tools/cut.py` を直す。切り出した画像は全問開いて、問の途中で切れていないか、次の問が混ざっていないかを確かめる。

## 2. 問題文

1. 問題画像を開き、`exam.json` の `stem`、`choices`、`visuals` を書く。形式は `docs/spec.md` の「問題データ」。
2. チェックリストの `text.status` を `抽出済み` にし、図・表の判断や読みに迷った点を `作成` のコメントに書く。
3. `text-reviewer` サブエージェントにレビューさせる。`要見直し` を直して `抽出済み` に戻し、すべて `確認済み` になるまで繰り返す。

## 3. 解説

問題文がすべて `確認済み` になってから入る。

1. 観点（`changes/0001-initial-build/README.md` の「解説」）に従って `explanation` を書く。正解の肢を最初に示し、「<正解>が正解」を含める。
2. 4肢を `作成済み` にし、用語の根拠、断定を避けた点、長くした理由を `作成` のコメントに書く。
3. `explanation-reviewer` サブエージェントにレビューさせる。`要見直し` の肢の文だけを直して `作成済み` に戻し、すべて `確認済み` になるまで繰り返す。

## 4. 確認

```sh
tools/devc.sh npm run check --prefix app
```

開発サーバでその回を開き、数問を解いて解説が出ることを確かめる。
