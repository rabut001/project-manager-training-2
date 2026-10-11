---
name: export-chat
description: このリポジトリの会話を chat-exports/ へ Markdown で書き出す。利用者が会話ログの書き出し、エクスポート、chat-exports への保存を頼んだときに使う。
---

# 会話の書き出し

会話記録はホストの `~/.claude/projects/` にあるので、コンテナではなくホストで実行する。手で Markdown を組み立てない。

```sh
python3 tools/export_chat.py                 # このリポジトリの最新の会話
python3 tools/export_chat.py --session <id>  # 会話を指定する
```

- 出力は `chat-exports/<会話の開始時刻 YYYY-MM-DD-HHMM>/chat.md`。同じ会話を書き出し直すと上書きする。
- 書き出すのは利用者の発言、応答の本文、ツール呼び出しの概要だけ。システムの付加情報、思考、ツールの出力、サブエージェントの会話は含めない。メールアドレスは伏せる。
- 標準出力のパスを利用者に伝える。頼まれない限りコミットしない。
- GitHub に載るので、書き出した後に秘密の情報（トークン、パスワード、個人の連絡先）が入っていないかを grep で確かめる。
