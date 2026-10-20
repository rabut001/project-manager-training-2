# プロジェクトマネージャ 午前Ⅱ 演習

IPA が公開しているプロジェクトマネージャ試験（PM）の午前Ⅱを、1問ずつ解く静的サイトです。公開先は <https://rabut001.github.io/project-manager-training-2/> です。

平成21年度春期から令和7年度秋期までの 17 回、各25問を収録します。問題は切り出した画像で表示し、ア〜エを選んで結果を確認します。解説は学習用に書いたもので、IPA の公式解説ではありません。進捗はブラウザの `localStorage` に残し、端末間の同期はしません。

仕様は [docs/spec.md](docs/spec.md) にあります。

## このリポジトリについて

このリポジトリは、Claude Code と OpenAI Codex を比べるために作りました。同じ指示を両方に与え、できあがったものを比較します。このリポジトリは Claude Code で作ったほうです。

| 項目 | 内容 |
| --- | --- |
| ツール | Claude Code |
| モデル | Claude Opus 5.5 |
| モード | high |

開発中の会話は [chat-exports/](chat-exports/) に残しています。

## フォルダ

| パス | 内容 |
| --- | --- |
| `app/` | 演習サイト（Vite + React + TypeScript） |
| `content/` | 問題データ。回ごとの `exam.json` と問題画像、回の一覧、取得元の記録 |
| `tools/` | PDF の取得、問題画像の切り出し、正解の抽出、データ検証、会話の書き出し（Python）と、開発コンテナの実行 |
| `docs/` | 現在の仕様 |
| `changes/` | 改修案件ごとの文書とチェックリスト。サイトには載せない |
| `chat-exports/` | 開発の会話ログ |
| `.claude/` | Claude Code の設定、レビュー用サブエージェント、手順（スキル） |
| `.devcontainer/` | 開発コンテナ（Node.js 24、Python 3.11、PyMuPDF、Tesseract） |
| `.github/workflows/` | 検証と GitHub Pages への公開 |

## 開発

Docker が必要です。VS Code の「Reopen in Container」で開くか、ホストから `tools/devc.sh` でコンテナの中のコマンドを実行します。

```sh
tools/devc.sh npm ci --prefix app
tools/devc.sh npm run dev --prefix app     # http://localhost:5173/project-manager-training-2/
tools/devc.sh npm run check --prefix app   # データ検証、型チェック、ビルド
```

回を取り込む手順は次のとおりです。PDF は `.cache/pdf/` に保存し、リポジトリには入れません。

```sh
tools/devc.sh python3 tools/fetch.py 2025-r07-aki      # 問題冊子と解答例を取得
tools/devc.sh python3 tools/cut.py 2025-r07-aki        # 問題画像を切り出し
tools/devc.sh python3 tools/init_exam.py 2025-r07-aki  # 正解を入れて exam.json を作る
```

問題文と解説はその後に作り、レビューします（`.claude/skills/add-exam/`）。

## 出典

問題冊子と解答例は、独立行政法人情報処理推進機構（IPA）が公開しているものです。取得元の URL と取得日は [content/sources.json](content/sources.json) にあります。

出典: [過去問題 | IPA](https://www.ipa.go.jp/shiken/mondai-kaiotu/index.html)

IPA は、公表している過去の試験問題について、法令に特別の定めがある場合を除き許諾や使用料は不要としています。著作権は放棄されていません。使用時の留意点は [試験制度に関するよくある質問](https://www.ipa.go.jp/shiken/faq.html) を確認してください。
