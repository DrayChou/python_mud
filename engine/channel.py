from __future__ import annotations
import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.player import Player


class Channel:
    def __init__(self):
        self.members: dict[int, "Player"] = {}

    def join(self, uid: int, player: "Player"):
        self.members[uid] = player

    def leave(self, uid: int):
        self.members.pop(uid, None)

    async def say(self, message: str, *exclude: "Player"):
        exclude_ids = {id(p) for p in exclude}
        tasks = []
        for uid, player in list(self.members.items()):
            if uid not in exclude_ids:
                tasks.append(player.reply(message))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
