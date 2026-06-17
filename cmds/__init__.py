from __future__ import annotations
import importlib
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from world.player import Player

command_list: dict[str, Callable] = {}
command_desc: dict[str, str] = {}


def register(name: str, func: Callable, desc: str = ""):
    command_list[name] = func
    command_desc[name] = desc


def reload_cmds():
    cmd_modules = [
        "cmds.common",
        "cmds.say",
        "cmds.kill",
        "cmds.hp",
        "cmds.get",
        "cmds.use",
    ]
    for mod in cmd_modules:
        importlib.import_module(mod)


async def dispatch(player: "Player", line: str):
    parts = line.strip().split()
    if not parts:
        await player.reply("> ")
        return
    cmd = parts[0].lower()
    args = parts[1:]

    # Check room-local dynamic commands first
    if cmd in player.dynamic_cmds:
        await player.dynamic_cmds[cmd](player, args)
        await player.reply("> ")
        return

    if cmd in command_list:
        await command_list[cmd](player, args)
    else:
        from config import LLM_ENABLED
        if LLM_ENABLED:
            await player.reply("\033[2m（正在理解你的意思……）\033[0m")
            from engine.llm_cmd import parse_natural_command
            parsed = await parse_natural_command(player, line)
            if parsed and parsed.lower() != "unknown":
                await player.reply(f"\033[2m→ {parsed}\033[0m")
                await dispatch(player, parsed)
                return
            else:
                await player.reply(f"不知道如何 '{line}'。输入 help 查看指令列表。")
        else:
            await player.reply(f"不知道如何 '{cmd}'。输入 help 查看指令列表。")
    await player.reply("> ")
