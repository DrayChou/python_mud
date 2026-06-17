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

PY_CMD=""
if command -v uv >/dev/null 2>&1; then
  PY_CMD="uv run python"
elif command -v python3 >/dev/null 2>&1; then
  PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PY_CMD="python"
else
  echo "未找到 uv / python3 / python，请先安装 Python 3.11+。" >&2
  exit 1
fi

print_line() {
  printf '%-24s %s\n' "$1" "$2"
}

echo "== python_mud environment check =="
print_line "root dir" "$ROOT_DIR"
print_line ".env loaded" "$([ -f "$ROOT_DIR/.env" ] && echo true || echo false)"
print_line "python cmd" "$PY_CMD"

$PY_CMD - <<'PY'
import importlib.util
import sys
from config import (
    HOST,
    PORT,
    CLIENT_ENCODING,
    BORN_POINT,
    LLM_ENABLED,
    LLM_MODEL,
    LLM_API_TYPE,
    LLM_API_URL,
    LLM_TIMEOUT,
    LLM_MAX_HISTORY,
)
from engine.llm import _resolve_llm_url

def p(key, value):
    print(f"{key:<24} {value}")

p("python version", sys.version.split()[0])
p("HOST", HOST)
p("PORT", PORT)
p("BORN_POINT", BORN_POINT)
p("CLIENT_ENCODING", CLIENT_ENCODING)
p("LLM_ENABLED", LLM_ENABLED)
p("LLM_MODEL", LLM_MODEL)
p("LLM_API_TYPE", LLM_API_TYPE)
p("LLM_API_URL(raw)", LLM_API_URL or "(default)")
p("LLM_API_URL(eff)", _resolve_llm_url())
p("LLM_TIMEOUT", LLM_TIMEOUT)
p("LLM_MAX_HISTORY", LLM_MAX_HISTORY)
p("json_repair", importlib.util.find_spec("json_repair") is not None)
PY

PORT_TO_CHECK="${MUD_BIND_PORT:-${PORT:-7777}}"
if command -v lsof >/dev/null 2>&1; then
  if lsof -nP -iTCP:"$PORT_TO_CHECK" -sTCP:LISTEN >/dev/null 2>&1; then
    print_line "port available" "false"
    echo
    echo "提示：端口 $PORT_TO_CHECK 当前已被占用；启动前请先释放，或设置新的 MUD_BIND_PORT。"
    exit 1
  else
    print_line "port available" "true"
  fi
fi

echo
if [ "${LLM_ENABLED:-true}" = "true" ] && command -v curl >/dev/null 2>&1; then
  echo "== llm connectivity (optional) =="
  RAW_URL="${LLM_API_URL:-}"
  API_TYPE="${LLM_API_TYPE:-ollama}"
  if [ -n "$RAW_URL" ]; then
    if [ "$API_TYPE" = "openai" ]; then
      TEST_URL="${RAW_URL%/}/models"
      if [[ "$RAW_URL" == */v1 ]]; then
        TEST_URL="$RAW_URL/models"
      fi
    else
      TEST_URL="${RAW_URL%/}/api/tags"
    fi
    print_line "probe url" "$TEST_URL"
    if curl -sS --connect-timeout 3 --max-time 8 "$TEST_URL" >/dev/null 2>&1; then
      print_line "llm reachable" "true"
    else
      print_line "llm reachable" "false"
    fi
  fi
fi

echo
printf '环境检查通过，可以运行 %s\n' './sh/start.sh'
