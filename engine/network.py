from __future__ import annotations
import asyncio
import sys
import os

# Make python_mud/ importable when running main.py from inside it
_here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _here not in sys.path:
    sys.path.insert(0, _here)

from config import HOST, PORT, BORN_POINT, GREETING, CLIENT_ENCODING
from engine.telnet import TelnetHandler
from engine.timer import heart_of_world
from world.login import LoginHandler, session_pool
from world.room import load_all_maps
from cmds import reload_cmds, dispatch


async def handle_client(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    uid = id(writer)
    addr = writer.get_extra_info("peername", ("?", 0))
    print(f"[CONNECT] {addr} → uid={uid}")

    telnet = TelnetHandler(writer)
    await telnet.negotiate()

    # Send greeting
    writer.write((GREETING + "\r\n请输入用户名：\r\n").encode(CLIENT_ENCODING, errors="replace"))
    await writer.drain()

    login_handler = LoginHandler(uid, writer)

    try:
        async for line in telnet.lines(reader):
            player = session_pool.get(uid)
            if player is None:
                result = await login_handler.handle(line)
                # result is Player on success, None still in login flow
            else:
                await dispatch(player, line)
    except Exception as e:
        print(f"[ERROR] uid={uid}: {e}")
    finally:
        print(f"[DISCONNECT] uid={uid}")
        player = session_pool.pop(uid, None)
        if player:
            player.save()
            if player.environment:
                await player.environment.exit_player(player)
        try:
            writer.close()
            await writer.wait_closed()
        except Exception:
            pass


async def main():
    # Ensure data directory exists
    from config import SAVE_DIR
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Load world and commands
    load_all_maps()
    reload_cmds()

    # Start heartbeat
    asyncio.create_task(heart_of_world.run())

    server = await asyncio.start_server(handle_client, HOST, PORT)
    addrs = ", ".join(str(s.getsockname()) for s in server.sockets)
    print(f"[INFO] MUD 服务器已启动，监听 {addrs}")
    print(f"[INFO] 连接方式：telnet {HOST if HOST != '0.0.0.0' else 'localhost'} {PORT}")

    async with server:
        await server.serve_forever()
