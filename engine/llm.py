"""
LLM async client — stdlib only (urllib + asyncio executor).

Supports:
- Ollama `/api/chat`
- OpenAI-compatible `/v1/chat/completions`
"""
from __future__ import annotations
import asyncio
import json
import urllib.request
from typing import Optional

from config import LLM_API_KEY, LLM_API_TYPE, LLM_API_URL, LLM_MODEL, LLM_TIMEOUT


def _resolve_llm_url() -> str:
    url = (LLM_API_URL or "").rstrip("/")
    if not url:
        if LLM_API_TYPE == "openai":
            return "http://127.0.0.1:1234/v1/chat/completions"
        return "http://127.0.0.1:11434/api/chat"

    if LLM_API_TYPE == "openai":
        if url.endswith("/v1/chat/completions"):
            return url
        if url.endswith("/v1"):
            return url + "/chat/completions"
        if url.startswith("http://") or url.startswith("https://"):
            if "/" not in url.split("://", 1)[1]:
                return url + "/v1/chat/completions"
        return url

    if url.endswith("/api/chat"):
        return url
    if url.endswith("/api"):
        return url + "/chat"
    if url.startswith("http://") or url.startswith("https://"):
        if "/" not in url.split("://", 1)[1]:
            return url + "/api/chat"
    return url


def _sync_chat(model: str, messages: list[dict], timeout: int) -> str:
    url = _resolve_llm_url()
    headers = {"Content-Type": "application/json"}

    if LLM_API_TYPE == "openai":
        payload_obj = {
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": 0,
            "max_tokens": 256,
        }
        if LLM_API_KEY:
            headers["Authorization"] = f"Bearer {LLM_API_KEY}"
    else:
        payload_obj = {
            "model": model,
            "messages": messages,
            "stream": False,
        }

    payload = json.dumps(payload_obj).encode()
    req = urllib.request.Request(
        url,
        data=payload,
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())

    if LLM_API_TYPE == "openai":
        return data["choices"][0]["message"]["content"].strip()
    return data["message"]["content"].strip()


async def chat(
    messages: list[dict],
    system: Optional[str] = None,
    model: str = LLM_MODEL,
    timeout: int = LLM_TIMEOUT,
) -> str:
    """Async wrapper around Ollama/OpenAI-compatible chat APIs."""
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
