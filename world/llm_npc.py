"""
LlmNpc — NPC driven by Ollama.

Each LlmNpc has:
- A system_prompt defining its personality and role
- A per-player conversation history (capped at LLM_MAX_HISTORY)
- Responds to 'say' events in its room
- Optionally runs a greeting when a player enters
"""
from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING
from world.npc import Npc
from engine.llm import chat
from config import LLM_ENABLED, LLM_MAX_HISTORY

if TYPE_CHECKING:
    from world.player import Player


class LlmNpc(Npc):
    def __init__(
        self,
        npc_id: str,
        name: str,
        desc: str,
        system_prompt: str,
        greeting: str = "",
    ):
        super().__init__(npc_id, name, desc)
        self.system_prompt = system_prompt
        self.greeting = greeting
        # Separate history per player (uid → list of messages)
        self._histories: dict[int, list[dict]] = {}
        self._thinking: set[int] = set()  # prevent overlapping calls per player

    def _get_history(self, uid: int) -> list[dict]:
        if uid not in self._histories:
            self._histories[uid] = []
        return self._histories[uid]

    def _trim_history(self, uid: int):
        h = self._histories.get(uid, [])
        if len(h) > LLM_MAX_HISTORY:
            self._histories[uid] = h[-LLM_MAX_HISTORY:]

    async def on_player_enter(self, player: "Player"):
        """Called when a player enters the room — send greeting if set."""
        if self.greeting:
            await asyncio.sleep(0.6)
            if self.environment and hasattr(self.environment, "channel"):
                await self.environment.channel.say(f"{self.name} 说：{self.greeting}")

    async def respond_to_say(self, player: "Player", message: str):
        if not LLM_ENABLED:
            await super().respond_to_say(player, message)
            return

        uid = player.user_id
        if uid in self._thinking:
            return  # Already processing for this player
        self._thinking.add(uid)

        try:
            history = self._get_history(uid)
            history.append({"role": "user", "content": f"{player.name}说：{message}"})

            # Build context-enriched system prompt
            room = self.environment
            room_ctx = f"当前所在：{room.title}\n{room.desc}" if room else ""
            full_system = f"{self.system_prompt}\n\n[场景背景]\n{room_ctx}"

            reply = await chat(history, system=full_system)

            history.append({"role": "assistant", "content": reply})
            self._trim_history(uid)

            if self.environment and hasattr(self.environment, "channel"):
                await self.environment.channel.say(f"\033[35m{self.name} 说：{reply}\033[0m")
        finally:
            self._thinking.discard(uid)
