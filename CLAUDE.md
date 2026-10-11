# CLAUDE.md

PM（プロジェクトマネージャ試験）午前Ⅱの演習サイト。概要は [README.md](README.md)、仕様の正本は [docs/spec.md](docs/spec.md)。

## 進め方

- 画面、操作、保存、問題データ、公開のしかたを変える依頼は、実装の前に `changes/` に案件フォルダを作る。手順は [changes/README.md](changes/README.md)。
- 仕様を変えるときは、実装の前に `docs/spec.md` を更新する。`changes/` の文書は記録であり、仕様の参照先にしない。完了した案件のフォルダは編集しない。
- 案件の状況が変わったら `changes/README.md` の表と、その案件の「現在地」を更新する。

## コマンド

Node.js と Python はホストではなく開発コンテナで動かす。`tools/devc.sh` がコンテナを作り、その中で実行する。

```sh
tools/devc.sh npm run dev --prefix app      # http://localhost:5173/project-manager-training-2/
tools/devc.sh npm run check --prefix app    # データ検証 + 型チェック + ビルド
tools/devc.sh python3 tools/validate.py --draft   # 作業中のデータ検証
```

回を追加する手順は `.claude/skills/add-exam/`。

## 問題データ

- `content/<id>/exam.json` の `no`、`answer`、`image` は手で変えない（`tools/init_exam.py` が作る）。
- 問題文（`stem`、`choices`、`visuals`）と解説（`explanation`）は、作成とレビューを分ける。作った手番でチェックリストを `確認済み` にしない。レビューは `.claude/agents/` のサブエージェント（`text-reviewer`、`explanation-reviewer`）に任せる。
- 解説の観点とチェックリストの形式は `changes/0001-initial-build/README.md` の「解説」「チェックリスト」。
- IPA の PDF は `.cache/pdf/`（Git 管理外）に置く。コミットしない。

## 書き方

- 文書、コメント、コミットメッセージは日本語。コミットメッセージは、何をなぜ変えたかを一文で書く。
- UI ライブラリとルーティングライブラリは足さない。色は `app/src/index.css` の `:root` の変数だけで決める。

## 会話の書き出し

利用者に頼まれたら `.claude/skills/export-chat/` に従って `chat-exports/` へ書き出す。`chat-exports/` は記録であり、実装や仕様の根拠にしない。
