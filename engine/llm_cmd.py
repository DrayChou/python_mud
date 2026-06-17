"""
LLM command parser — falls back to LLM when a player's input
doesn't match any registered command.

The LLM receives the game context (room, exits, visible objects, inventory)
and returns structured JSON like:
    {"command": "go east"}
"""
from __future__ import annotations
import re
from typing import TYPE_CHECKING
from engine.llm import chat
from engine.json_utils import loads_loose

if TYPE_CHECKING:
    from world.player import Player

_SYSTEM = """你是一个文字MUD游戏（人生游戏沙盒）的指令解析助手。

你的任务：将玩家的自然语言输入转换为游戏可执行的一条指令。

可用指令格式：
  look [目标]       — 查看房间或物体
  go <方向>         — 移动（east/west/north/south/dream 等）
  say <内容>        — 对当前房间里的人说话
  kill <目标>       — 攻击目标
  get <物品>        — 拾取物品
  drop <物品>       — 丢弃物品
  wear <装备>       — 穿戴装备
  use <物品>        — 使用物品
  inv               — 查看背包
  hp                — 查看状态
  who               — 查看在线玩家
  bye               — 退出游戏

规则：
1. 只返回纯 JSON，不要解释，不要 markdown。
2. 返回格式固定为：{"command":"具体指令"}
3. 如果输入的是对话/问句，通常转换为 say <内容>。
4. 如果无法合理转换，返回：{"command":"unknown"}
5. 方向词中文映射：东=east 西=west 南=south 北=north 梦=dream
"""


def _normalize_command_text(result: str) -> str:
    result = result.strip().strip('"\'"\'\'。，').strip()
    result = re.sub(r"\s+", " ", result)
    return result if result else "unknown"


def _extract_command(payload) -> str:
    if isinstance(payload, dict):
        command = payload.get("command")
        if isinstance(command, str):
            return _normalize_command_text(command)
    if isinstance(payload, list) and payload:
        first = payload[0]
        if isinstance(first, dict):
            command = first.get("command")
            if isinstance(command, str):
                return _normalize_command_text(command)
    raise ValueError(f"unsupported command payload: {payload!r}")


async def parse_natural_command(player: "Player", text: str) -> str:
    """Returns a game command string, or 'unknown' if parsing fails."""
    room = player.environment
    exits = list(room.exits.keys()) if room else []
    visible = [obj.name for obj in room.content if obj is not player] if room else []
    inventory = [obj.name for obj in player.content]

    context = (
        f"当前位置：{room.title if room else '未知'}\n"
        f"可用出口：{', '.join(exits) or '无'}\n"
        f"房间内可见：{', '.join(visible) or '无'}\n"
        f"背包：{', '.join(inventory) or '空'}"
    )

    user_msg = f"[游戏上下文]\n{context}\n\n[玩家输入]\n{text}"
    result = await chat([{"role": "user", "content": user_msg}], system=_SYSTEM)

    try:
        payload = loads_loose(result)
        return _extract_command(payload)
    except Exception:
        return _normalize_command_text(result)
