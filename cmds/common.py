from cmds import register
from engine.events import event_system


async def cmd_look(player, args):
    if not args:
        await player.environment.describe(player)
        return
    target_name = " ".join(args)
    target = player.environment.resolve_content(target_name)
    if target is None:
        target = player.resolve_content(target_name)
    if target:
        await player.reply(target.to_str())
        await event_system.trigger("look", player.environment, player, target_name)
    else:
        await player.reply(f"你看不到 '{target_name}'。")


async def cmd_go(player, args):
    if not args:
        await player.reply("去哪里？请指定方向。")
        return
    direction = args[0].lower()
    room = player.environment
    if direction not in room.exits:
        await player.reply(f"那个方向没有出口。可用出口：{', '.join(room.exits.keys())}")
        return
    handled, results = await event_system.trigger("before_go", room, player, direction)
    if handled and False in results:
        return  # Blocked by listener
    target_room_id = room.exits[direction]
    from world.room import get_room
    target_room = get_room(target_room_id)
    if not target_room:
        await player.reply(f"出口指向未知区域：{target_room_id}")
        return
    await room.exit_player(player, direction)
    await target_room.enter_player(player)


async def cmd_help(player, args):
    from cmds import command_list, command_desc
    lines = ["\033[1;36m=== 指令列表 ===\033[0m"]
    for name, desc in sorted(command_desc.items()):
        lines.append(f"  \033[33m{name:<12}\033[0m {desc}")
    if player.dynamic_cmds:
        lines.append("\033[1;36m=== 本地指令 ===\033[0m")
        for name in player.dynamic_cmds:
            lines.append(f"  \033[35m{name}\033[0m")
    await player.reply("\r\n".join(lines))


async def cmd_bye(player, args):
    await player.reply("再见！愿你的旅程充满意义。")
    player.save()
    if player.environment:
        await player.environment.exit_player(player)
    player.writer.close()


async def cmd_who(player, args):
    from world.login import session_pool
    names = [p.name for p in session_pool.values()]
    await player.reply(f"在线玩家（{len(names)}）：{', '.join(names)}")


async def cmd_inv(player, args):
    if not player.content:
        await player.reply("你的背包空空如也。")
        return
    lines = ["\033[1;33m背包：\033[0m"]
    for item in player.content:
        lines.append(f"  {item.to_str()}")
    await player.reply("\r\n".join(lines))


register("look", cmd_look, "察看房间或物体")
register("l", cmd_look, "look 的缩写")
register("go", cmd_go, "go <方向>  移动到相邻区域")
register("help", cmd_help, "显示指令列表")
register("h", cmd_help, "help 的缩写")
register("bye", cmd_bye, "退出游戏")
register("quit", cmd_bye, "退出游戏")
register("who", cmd_who, "查看在线玩家")
register("inv", cmd_inv, "查看背包")
register("i", cmd_inv, "inv 的缩写")
