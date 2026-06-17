from __future__ import annotations
import asyncio
from typing import Optional, TYPE_CHECKING
from world.char import Charactor

if TYPE_CHECKING:
    from world.room import Room


class Monster(Charactor):
    def __init__(
        self,
        mob_id: str,
        name: str,
        desc: str = "",
        hp: int = 30,
        respawn_delay: float = 30.0,
    ):
        super().__init__()
        self.id = mob_id
        self.name = name
        self.desc = desc
        self.hp = hp
        self.max_hp = hp
        self.is_invulnerable = False
        self._respawn_delay = respawn_delay
        self._home_room_id: Optional[str] = None

    def put(self, env):
        if hasattr(env, "id"):
            self._home_room_id = env.id
        super().put(env)

    async def on_death(self, killer):
        await super().on_death(killer)
        self.leave()
        if self._home_room_id and self._respawn_delay > 0:
            asyncio.create_task(self._respawn())

    async def _respawn(self):
        from world.room import get_room
        await asyncio.sleep(self._respawn_delay)
        room = get_room(self._home_room_id)
        if room:
            self.hp = self.max_hp
            self.fright_list.clear()
            self._fright_refs.clear()
            self.put(room)
            await room.channel.say(f"{self.name} 再次出现了！")
