import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue
        if value and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ.setdefault(key, value)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _env_str(name: str, default: str) -> str:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value


def _normalize_llm_api_type(value: str) -> str:
    value = (value or "ollama").strip().lower()
    if value in {"openai-compatible", "openai_compatible"}:
        return "openai"
    if value not in {"ollama", "openai"}:
        return "ollama"
    return value


_load_dotenv(BASE_DIR / ".env")

HOST = os.getenv("MUD_BIND_HOST") or os.getenv("HOST") or "0.0.0.0"
PORT = _env_int("MUD_BIND_PORT", _env_int("PORT", 7777))
BORN_POINT = _env_str("BORN_POINT", "StationHall")
SAVE_DIR = os.path.join(BASE_DIR, "data", "players")
CLIENT_ENCODING = _env_str("CLIENT_ENCODING", "utf-8")   # 默认使用 UTF-8；老旧中文 Telnet 环境可改为 "gbk"

LLM_ENABLED = _env_bool("LLM_ENABLED", True)
LLM_MODEL = _env_str("LLM_MODEL", "qwen2.5:3b")
LLM_API_TYPE = _normalize_llm_api_type(_env_str("LLM_API_TYPE", "ollama"))
LLM_API_URL = os.getenv("LLM_API_URL") or _env_str("OLLAMA_URL", "")
LLM_API_KEY = _env_str("LLM_API_KEY", "")
LLM_TIMEOUT = _env_int("LLM_TIMEOUT", 30)
LLM_MAX_HISTORY = _env_int("LLM_MAX_HISTORY", 12)

GREETING = r"""
  ____  _   _  ___  __  __ _   _ ____
 |  _ \| | | |/ _ \|  \/  | | | |  _ \
 | |_) | |_| | | | | |\/| | | | | | | |
 |  __/|  _  | |_| | |  | | |_| | |_| |
 |_|   |_| |_|\___/|_|  |_|\___/|____/

        人生游戏 MUD v0.1
   欢迎来到这个世界，旅行者。
"""
