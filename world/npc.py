from __future__ import annotations
from typing import TYPE_CHECKING
from world.char import Charactor

if TYPE_CHECKING:
    from world.player import Player


class Npc(Charactor):
    def __init__(self, npc_id: str, name: str, desc: str = ""):
        super().__init__()
        self.id = npc_id
        self.name = name
        self.desc = desc
        self.is_invulnerable = True
        self.topics: dict[str, str] = {}

    async def on_death(self, killer):
        # NPCs don't die
        self.hp = self.max_hp

    async def respond_to_say(self, player: "Player", message: str):
        response = None
        for keyword, reply in self.topics.items():
            if keyword.lower() in message.lower():
                response = reply
                break
        if response:
            if self.environment and hasattr(self.environment, "channel"):
                await self.environment.channel.say(f"{self.name} 说：{response}")
