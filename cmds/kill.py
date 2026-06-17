from cmds import register


async def cmd_kill(player, args):
    if not args:
        await player.reply("攻击谁？")
        return
    target_name = " ".join(args)
    room = player.environment
    target = room.resolve_content(target_name)
    if target is None:
        await player.reply(f"这里没有 '{target_name}'。")
        return
    if target is player:
        await player.reply("你无法攻击自己。")
        return
    from world.char import Charactor
    if not isinstance(target, Charactor):
        await player.reply(f"{target.name} 不能被攻击。")
        return
    if target.is_invulnerable:
        await player.reply(f"{target.name} 不可被伤害。")
        return
    player.attack(target)
    await player.reply(f"你向 {target.name} 发起了攻击！")
    await room.channel.say(f"{player.name} 向 {target.name} 发起了攻击！", player)


register("kill", cmd_kill, "kill <目标>  攻击目标")
register("k", cmd_kill, "kill 的缩写")
