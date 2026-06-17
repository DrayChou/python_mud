import os

HOST = "0.0.0.0"
PORT = 7777
BORN_POINT = "StationHall"
SAVE_DIR = os.path.join(os.path.dirname(__file__), "data", "players")
LLM_ENABLED = True
LLM_MODEL = "qwen2.5:3b"
CLIENT_ENCODING = "gbk"   # Telnet CP936 中文环境；UTF-8 客户端改为 "utf-8"
OLLAMA_URL = "http://localhost:11434"
LLM_TIMEOUT = 30       # seconds per request
LLM_MAX_HISTORY = 12   # messages kept per NPC conversation

GREETING = r"""
  ____  _   _  ___  __  __ _   _ ____
 |  _ \| | | |/ _ \|  \/  | | | |  _ \
 | |_) | |_| | | | | |\/| | | | | | | |
 |  __/|  _  | |_| | |  | | |_| | |_| |
 |_|   |_| |_|\___/|_|  |_|\___/|____/

        人生游戏 MUD v0.1
   欢迎来到这个世界，旅行者。
"""
