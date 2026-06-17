from __future__ import annotations
import asyncio
from typing import Optional, TYPE_CHECKING
from world.player import Player, hash_password

if TYPE_CHECKING:
    from asyncio import StreamWriter

# uid → Player (active sessions)
session_pool: dict[int, Player] = {}


class LoginHandler:
    def __init__(self, uid: int, writer: "StreamWriter"):
        self.uid = uid
        self.writer = writer
        self._state = "username"
        self._pending_name: str = ""
        self._pending_confirm: str = ""

    async def _send(self, msg: str):
        from config import CLIENT_ENCODING
        try:
            self.writer.write((msg + "\r\n").encode(CLIENT_ENCODING, errors="replace"))
            await self.writer.drain()
        except Exception:
            pass

    async def start(self):
        await self._send("请输入用户名：")

    async def handle(self, line: str) -> Optional[Player]:
        line = line.strip()

        if self._state == "username":
            if not line:
                await self._send("用户名不能为空，请重新输入：")
                return None
            self._pending_name = line
            if Player.exists(line):
                self._state = "password"
                await self._send(f"欢迎回来，{line}！请输入密码：")
            else:
                self._state = "new_password"
                await self._send(f"新用户：{line}，请设置密码：")
            return None

        if self._state == "password":
            data = Player.load_data(self._pending_name)
            if data and data.get("pass_hash") == hash_password(line):
                return await self._complete_login(data)
            else:
                await self._send("密码错误，请重新输入：")
                return None

        if self._state == "new_password":
            if len(line) < 3:
                await self._send("密码至少需要3个字符，请重新设置：")
                return None
            self._pending_confirm = line
            self._state = "confirm_password"
            await self._send("请再次输入密码确认：")
            return None

        if self._state == "confirm_password":
            if line != self._pending_confirm:
                self._state = "new_password"
                await self._send("两次密码不一致，请重新设置密码：")
                return None
            return await self._create_and_login()

        return None

    async def _complete_login(self, data: dict) -> Player:
        # Kick existing session
        for uid, existing in list(session_pool.items()):
            if existing.user_name == self._pending_name:
                await existing.reply("你的账号在另一处登录，你已被踢下线。")
                existing.save()
                del session_pool[uid]
                break

        player = Player(self.uid, self.writer, self._pending_name)
        player.restore_from_data(data)
        session_pool[self.uid] = player

        from world.room import get_room
        from config import BORN_POINT
        room_id = data.get("cur_room") or BORN_POINT
        room = get_room(room_id) or get_room(BORN_POINT)
        await player.reply(f"\033[1;32m登录成功！欢迎回来，{player.name}。\033[0m")
        if room:
            await player.enter(room)
        return player

    async def _create_and_login(self) -> Player:
        player = Player(self.uid, self.writer, self._pending_name)
        player.pass_hash = hash_password(self._pending_confirm)
        player.save()
        session_pool[self.uid] = player

        from world.room import get_room
        from config import BORN_POINT
        room = get_room(BORN_POINT)
        await player.reply(f"\033[1;32m角色创建成功！欢迎来到世界，{player.name}。\033[0m")
        if room:
            await player.enter(room)
        return player
