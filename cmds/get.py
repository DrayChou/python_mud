from cmds import register
from world.item import Item


async def cmd_get(player, args):
    if not args:
        await player.reply("拿什么？")
        return
    target_name = " ".join(args)
    room = player.environment
    target = room.resolve_content(target_name)
    if target is None:
        await player.reply(f"这里没有 '{target_name}'。")
        return
    if not isinstance(target, Item):
        await player.reply(f"{target.name} 不能被拿起。")
        return
    if target.is_unmov:
        await player.reply(f"{target.name} 无法被移动。")
        return
    target.put(player)
    await player.reply(f"你拿起了 {target.name}。")
    await room.channel.say(f"{player.name} 拿起了 {target.name}。", player)


async def cmd_drop(player, args):
    if not args:
        await player.reply("丢弃什么？")
        return
    target_name = " ".join(args)
    target = player.resolve_content(target_name)
    if target is None:
        await player.reply(f"你背包里没有 '{target_name}'。")
        return
    target.put(player.environment)
    await player.reply(f"你放下了 {target.name}。")
    await player.environment.channel.say(f"{player.name} 放下了 {target.name}。", player)


register("get", cmd_get, "get <物品>  拾取物品")
register("take", cmd_get, "同 get")
register("drop", cmd_drop, "drop <物品>  放下物品")
