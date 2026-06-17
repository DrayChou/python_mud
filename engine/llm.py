"""
Ollama async client — stdlib only (urllib + asyncio executor).

Usage:
    from engine.llm import chat
    reply = await chat([{"role":"user","content":"你好"}], system="你是...")
"""
from __future__ import annotations
import asyncio
import json
import urllib.request
import urllib.error
from typing import Optional

from config import OLLAMA_URL, LLM_MODEL, LLM_TIMEOUT


def _sync_chat(model: str, messages: list[dict], timeout: int) -> str:
    payload = json.dumps({"model": model, "messages": messages, "stream": False}).encode()
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    return data["message"]["content"].strip()


async def chat(
    messages: list[dict],
    system: Optional[str] = None,
    model: str = LLM_MODEL,
    timeout: int = LLM_TIMEOUT,
) -> str:
    """Async wrapper around Ollama /api/chat. Runs blocking I/O in executor."""
    full_messages = []
    if system:
        full_messages.append({"role": "system", "content": system})
    full_messages.extend(messages)

    loop = asyncio.get_event_loop()
    try:
        reply = await asyncio.wait_for(
            loop.run_in_executor(None, _sync_chat, model, full_messages, timeout),
            timeout=timeout + 5,
        )
        return reply
    except asyncio.TimeoutError:
        return "（……沉默）"
    except Exception as e:
        return f"（系统繁忙：{e}）"
