from cmds import register


async def cmd_hp(player, args):
    bar = player.hp_bar()
    equip = player.equipment
    equip_str = "（空手）"
    if equip:
        equip_str = ", ".join(f"{slot}: {item.name}" for slot, item in equip.items())
    await player.reply(f"{bar}\n装备：{equip_str}")


register("hp", cmd_hp, "查看生命值和装备")
register("score", cmd_hp, "同 hp")
