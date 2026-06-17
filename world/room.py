from __future__ import annotations
import importlib
import glob
import os
from typing import Optional, TYPE_CHECKING
from world.space import SpaceObject
from engine.channel import Channel
from engine.events import event_system

if TYPE_CHECKING:
    from world.player import Player

# Global world registry
_world: dict[str, "Room"] = {}


def get_room(room_id: str) -> Optional["Room"]:
    return _world.get(room_id)


def register_room(room: "Room"):
    _world[room.id] = room


def load_all_maps():
    maps_dir = os.path.join(os.path.dirname(__file__), "..", "maps")
    maps_dir = os.path.abspath(maps_dir)
    pattern = os.path.join(maps_dir, "*.py")
    for path in sorted(glob.glob(pattern)):
        basename = os.path.basename(path)
        if basename.startswith("_"):
            continue
        mod_name = "maps." + basename[:-3]
        importlib.import_module(mod_name)


class Room(SpaceObject):
    def __init__(
        self,
        room_id: str,
        title: str,
        desc: str,
        exits: dict[str, str] | None = None,
        listeners: dict | None = None,
        avg_cmds: dict | None = None,
    ):
        super().__init__()
        self.id = room_id
        self.name = title
        self.title = title
        self.desc = desc
        self.exits: dict[str, str] = exits or {}
        self.channel: Channel = Channel()
        self.avg_cmds: dict = avg_cmds or {}
        # Register provided listeners
        if listeners:
            for event_name, cb in listeners.items():
                event_system.register(event_name, cb, self)

    def spawn(self, obj: SpaceObject):
        obj.put(self)

    async def describe(self, player: "Player"):
        lines = [
            f"\033[1;33m{self.title}\033[0m",
            self.desc,
        ]
        exits_str = "  ".join(self.exits.keys()) if self.exits else "（无出口）"
        lines.append(f"\033[36m[出口: {exits_str}]\033[0m")

        # Show contents (NPCs, monsters, items)
        others = []
        for obj in self.content:
            if obj is not player:
                others.append(f"  {obj.name}")
        if others:
            lines.append("你看见：")
            lines.extend(others)

        await player.reply("\r\n".join(lines))

    async def enter_player(self, player: "Player"):
        old_room = player.environment
        if old_room and old_room is not self:
            await old_room.exit_player(player)

        player.put(self)
        self.channel.join(id(player), player)

        # Copy room-local commands to player
        for k, v in self.avg_cmds.items():
            player.dynamic_cmds[k] = v

        # Announce arrival
        await self.channel.say(f"{player.name} 来到了这里。", player)
        await event_system.trigger("after_go", self, player)
        await self.describe(player)

    async def exit_player(self, player: "Player", direction: str = ""):
        # Remove room-local commands
        for k in self.avg_cmds:
            player.dynamic_cmds.pop(k, None)

        self.channel.leave(id(player))
        await self.channel.say(f"{player.name} 离开了。", player)
        player.leave()
