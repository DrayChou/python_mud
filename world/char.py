from __future__ import annotations
import asyncio
import random
import time
from typing import Optional, TYPE_CHECKING
from world.space import SpaceObject
from engine.timer import heart_of_world

if TYPE_CHECKING:
    from world.item import Item


class Charactor(SpaceObject):
    def __init__(self):
        super().__init__()
        self.hp: int = 100
        self.max_hp: int = 100
        self.dex: int = 10
        self.str_: int = 10
        self.is_invulnerable: bool = False
        # set of id(enemy) — lightweight tracking
        self.fright_list: set[int] = set()
        self._fright_refs: dict[int, "Charactor"] = {}  # id → ref
        self.equipment: dict[str, "Item"] = {}
        self._last_heartbeat: float = 0.0
        self._heartbeat_interval: float = 2.0
        heart_of_world.register(self)

    # ------------------------------------------------------------------
    # Combat interface
    # ------------------------------------------------------------------

    def attack(self, target: "Charactor"):
        self.fright_list.add(id(target))
        self._fright_refs[id(target)] = target
        target.fright_list.add(id(self))
        target._fright_refs[id(self)] = self

    async def modify_hp(self, delta: int):
        if self.is_invulnerable and delta < 0:
            return
        self.hp = max(0, min(self.max_hp, self.hp + delta))

    def get_local_enemies(self) -> list["Charactor"]:
        room = self.environment
        if room is None:
            return []
        local_ids = {id(obj) for obj in room.content}
        result = []
        for eid in list(self.fright_list):
            if eid in local_ids and eid in self._fright_refs:
                result.append(self._fright_refs[eid])
        return result

    async def on_death(self, killer: "Charactor"):
        self.hp = 0
        self.fright_list.clear()
        self._fright_refs.clear()

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def heart_beat(self, now: float):
        if now - self._last_heartbeat < self._heartbeat_interval:
            return
        self._last_heartbeat = now
        asyncio.ensure_future(self._async_heartbeat())

    async def _async_heartbeat(self):
        await self.combat_control()

    async def combat_control(self):
        if not self.fright_list:
            return
        # Remove dead enemies
        dead = [eid for eid in list(self.fright_list) if eid not in self._fright_refs]
        for eid in dead:
            self.fright_list.discard(eid)

        enemies = self.get_local_enemies()
        if not enemies:
            return

        target = random.choice(enemies)
        if target.hp > 0:
            from world.combat import combat
            await combat(self, target)

    # ------------------------------------------------------------------
    # Display
    # ------------------------------------------------------------------

    def hp_bar(self) -> str:
        pct = self.hp / max(self.max_hp, 1)
        filled = int(pct * 10)
        bar = "█" * filled + "░" * (10 - filled)
        return f"HP [{bar}] {self.hp}/{self.max_hp}"
