#!/usr/bin/env bash
# 開発コンテナの中でコマンドを実行する。コンテナが無い、または定義が変わったときは作り直す。
#   tools/devc.sh npm run dev --prefix app
#   tools/devc.sh python3 tools/cut.py 2025-r07-aki
#   tools/devc.sh --down
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
workspace="/workspaces/project-manager-training-2"
name="pm2-dev"
hash="$(cat "$root/.devcontainer/Dockerfile" "$root/.devcontainer/requirements.txt" | sha256sum | cut -c1-12)"
image="pm2-dev:$hash"

if [[ "${1:-}" == "--down" ]]; then
  docker rm -f "$name" >/dev/null 2>&1 || true
  exit 0
fi

if [[ "$(docker inspect -f '{{.Config.Image}}' "$name" 2>/dev/null || true)" != "$image" ]]; then
  docker rm -f "$name" >/dev/null 2>&1 || true
  if ! docker image inspect "$image" >/dev/null 2>&1; then
    docker build -q -t "$image" "$root/.devcontainer" >&2
  fi
  docker run -d --name "$name" -u node -p 5173:5173 \
    -v "$root:$workspace" -w "$workspace" "$image" sleep infinity >/dev/null
fi
if [[ "$(docker inspect -f '{{.State.Running}}' "$name")" != "true" ]]; then
  docker start "$name" >/dev/null
fi

relative="${PWD#"$root"}"
[[ "$relative" == "$PWD" ]] && relative=""
flags=(-i)
[[ -t 0 && -t 1 ]] && flags+=(-t)
exec docker exec "${flags[@]}" -w "$workspace$relative" "$name" "$@"
