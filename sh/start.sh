#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$ROOT_DIR"

load_dotenv_defaults() {
  local env_file="$1"
  [ -f "$env_file" ] || return 0
  while IFS= read -r raw_line || [ -n "$raw_line" ]; do
    local line="$raw_line"
    line="${line#${line%%[![:space:]]*}}"
    line="${line%${line##*[![:space:]]}}"
    [ -z "$line" ] && continue
    case "$line" in
      \#*) continue ;;
    esac
    case "$line" in
      *=*) ;;
      *) continue ;;
    esac
    local key="${line%%=*}"
    local value="${line#*=}"
    key="${key%${key##*[![:space:]]}}"
    key="${key#${key%%[![:space:]]*}}"
    value="${value#${value%%[![:space:]]*}}"
    value="${value%${value##*[![:space:]]}}"
    if [ -n "$value" ] && [ "${value#\"}" != "$value" ] && [ "${value%\"}" != "$value" ]; then
      value="${value#\"}"
      value="${value%\"}"
    elif [ -n "$value" ] && [ "${value#\'}" != "$value" ] && [ "${value%\'}" != "$value" ]; then
      value="${value#\'}"
      value="${value%\'}"
    fi
    if [ -z "${!key+x}" ]; then
      export "$key=$value"
    fi
  done < "$env_file"
}

load_dotenv_defaults "$ROOT_DIR/.env"

MUD_BIND_HOST="${MUD_BIND_HOST:-${HOST:-0.0.0.0}}"
MUD_BIND_PORT="${MUD_BIND_PORT:-${PORT:-7777}}"

if command -v lsof >/dev/null 2>&1 && lsof -nP -iTCP:"$MUD_BIND_PORT" -sTCP:LISTEN >/dev/null 2>&1; then
  echo "端口 $MUD_BIND_PORT 已被占用，请先关闭占用进程，或改用其他端口。" >&2
  lsof -nP -iTCP:"$MUD_BIND_PORT" -sTCP:LISTEN >&2 || true
  echo "可通过设置 MUD_BIND_PORT 启动到其他端口，例如：MUD_BIND_PORT=7778 ./sh/start.sh" >&2
  exit 1
fi

if command -v uv >/dev/null 2>&1; then
  exec uv run python main.py
fi
if command -v python3 >/dev/null 2>&1; then
  exec python3 main.py
fi
if command -v python >/dev/null 2>&1; then
  exec python main.py
fi

echo "未找到 uv / python3 / python，请先安装 Python 3.11+。" >&2
exit 1
