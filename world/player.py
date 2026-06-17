from __future__ import annotations
import asyncio
import hashlib
import json
import os
from typing import Optional, TYPE_CHECKING
from world.char import Charactor

if TYPE_CHECKING:
    from asyncio import StreamWriter
    from world.room import Room


class Player(Charactor):
    def __init__(self, uid: int, writer: "StreamWriter", user_name: str):
        super().__init__()
        self.user_id = uid
        self.writer = writer
        self.user_name = user_name
        self.name = user_name
        self.pass_hash: str = ""
        self.dynamic_cmds: dict = {}
        self._heartbeat_interval = 3.0

    # ------------------------------------------------------------------
    # I/O
    # ------------------------------------------------------------------

    async def reply(self, message: str):
        from config import CLIENT_ENCODING
        try:
            self.writer.write((message + "\r\n").encode(CLIENT_ENCODING, errors="replace"))
            await self.writer.drain()
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------------

    async def enter(self, room: "Room"):
        await room.enter_player(self)

    async def fly_to(self, room_id: str):
        from world.room import get_room
        room = get_room(room_id)
        if room:
            await self.enter(room)
        else:
            await self.reply(f"无法传送：找不到房间 {room_id}")

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self):
        from config import SAVE_DIR
        os.makedirs(SAVE_DIR, exist_ok=True)
        data = {
            "user_name": self.user_name,
            "pass_hash": self.pass_hash,
            "cur_room": self.environment.id if self.environment else "",
            "hp": self.hp,
            "max_hp": self.max_hp,
            "inventory": [
                {"id": obj.id, "count": getattr(obj, "count", 1)}
                for obj in self.content
            ],
            "equipment": {
                slot: item.id for slot, item in self.equipment.items()
            },
        }
        path = os.path.join(SAVE_DIR, f"{self.user_name}.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    @classmethod
    def load_data(cls, user_name: str) -> Optional[dict]:
        from config import SAVE_DIR
        path = os.path.join(SAVE_DIR, f"{user_name}.json")
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def exists(cls, user_name: str) -> bool:
        from config import SAVE_DIR
        return os.path.exists(os.path.join(SAVE_DIR, f"{user_name}.json"))

    def restore_from_data(self, data: dict):
        from world.item import GLOBAL_ITEM_LIST
        self.hp = data.get("hp", self.max_hp)
        self.max_hp = data.get("max_hp", 100)
        self.pass_hash = data.get("pass_hash", "")
        # Restore inventory
        for entry in data.get("inventory", []):
            item_template = GLOBAL_ITEM_LIST.get(entry["id"])
            if item_template:
                item = item_template.clone()
                item.count = entry.get("count", 1)
                item.put(self)
        # Restore equipment
        for slot, item_id in data.get("equipment", {}).items():
            item = self.resolve_content(item_id)
            if item:
                self.equipment[slot] = item

    # ------------------------------------------------------------------
    # Death
    # ------------------------------------------------------------------

    async def on_death(self, killer: Charactor):
        await super().on_death(killer)
        self.hp = self.max_hp // 2
        await self.reply("你死了！……但生命的旅程并未结束。")
        from config import BORN_POINT
        await self.fly_to(BORN_POINT)


def hash_password(password: str) -> str:
    return hashlib.md5(password.encode()).hexdigest()
