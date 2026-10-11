#!/usr/bin/env python3
"""Claude Code の会話記録（JSONL）を chat-exports/<開始時刻>/chat.md に書き出す。

会話記録はホストの ~/.claude にあるので、コンテナではなくホストの python3 で実行する。

    python3 tools/export_chat.py                 # このリポジトリの最新の会話
    python3 tools/export_chat.py --session <id>  # 会話を指定する

公開するので、書き出すのは利用者の発言、応答の本文、ツール呼び出しの概要だけにする。
システムの付加情報、思考、ツールの出力は含めず、メールアドレスは伏せる。
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "chat-exports"
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
HIDDEN_RE = re.compile(
    r"<(system-reminder|local-command-[a-z]+|command-[a-z]+)>.*?</\1>", re.DOTALL
)


def project_dir() -> Path:
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(ROOT))
    return Path.home() / ".claude" / "projects" / slug


def clean(text: str) -> str:
    text = HIDDEN_RE.sub("", text)
    text = EMAIL_RE.sub("（メールアドレス）", text)
    return text.strip()


def relative(path: str) -> str:
    try:
        return str(Path(path).resolve().relative_to(ROOT))
    except ValueError:
        return Path(path).name


def tool_summary(block: dict) -> str:
    name = block.get("name", "")
    args = block.get("input") or {}
    if name == "Bash":
        detail = args.get("description") or args.get("command", "").splitlines()[0]
    elif name in ("Read", "Write", "Edit", "NotebookEdit"):
        detail = relative(args.get("file_path", ""))
    elif name in ("Agent", "Task"):
        detail = f"{args.get('subagent_type', '')} {args.get('description', '')}".strip()
    elif name == "WebFetch":
        detail = args.get("url", "")
    elif name == "WebSearch":
        detail = args.get("query", "")
    elif name == "Skill":
        detail = args.get("skill", "")
    else:
        detail = ""
    return f"- `{name}` {clean(detail)}".rstrip()


def to_markdown(lines: list[dict]) -> tuple[str, datetime.datetime]:
    parts: list[str] = []
    started: datetime.datetime | None = None
    tools: list[str] = []

    def flush_tools() -> None:
        if tools:
            parts.append("<details><summary>ツール呼び出し " + str(len(tools)) + " 件</summary>\n\n" + "\n".join(tools) + "\n\n</details>")
            tools.clear()

    for entry in lines:
        if entry.get("isSidechain") or entry.get("isMeta"):
            continue
        kind = entry.get("type")
        message = entry.get("message") or {}
        content = message.get("content")
        if kind == "user":
            texts = [content] if isinstance(content, str) else [
                block.get("text", "") for block in content or [] if block.get("type") == "text"
            ]
            text = clean("\n".join(texts))
            if not text:
                continue
            if started is None and entry.get("timestamp"):
                started = datetime.datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
            flush_tools()
            parts.append("## 利用者\n\n" + text)
        elif kind == "assistant" and isinstance(content, list):
            for block in content:
                if block.get("type") == "text" and clean(block.get("text", "")):
                    flush_tools()
                    parts.append("## Claude\n\n" + clean(block["text"]))
                elif block.get("type") == "tool_use":
                    tools.append(tool_summary(block))
    flush_tools()
    if started is None:
        raise SystemExit("利用者の発言がありません。")
    return "\n\n".join(parts) + "\n", started.astimezone()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--session", help="会話の id（JSONL のファイル名）")
    args = parser.parse_args()
    directory = project_dir()
    if args.session:
        source = directory / f"{args.session}.jsonl"
    else:
        candidates = sorted(directory.glob("*.jsonl"), key=lambda path: path.stat().st_mtime)
        if not candidates:
            raise SystemExit(f"会話記録がありません: {directory}")
        source = candidates[-1]
    lines = [json.loads(line) for line in source.read_text(encoding="utf-8").splitlines() if line.strip()]
    body, started = to_markdown(lines)
    folder = OUT / started.strftime("%Y-%m-%d-%H%M")
    folder.mkdir(parents=True, exist_ok=True)
    title = f"# 会話ログ {started.strftime('%Y-%m-%d %H:%M')}\n\n"
    (folder / "chat.md").write_text(title + body, encoding="utf-8")
    print(folder.relative_to(ROOT) / "chat.md")


if __name__ == "__main__":
    main()
