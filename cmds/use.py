from cmds import register
from world.item import Item


async def cmd_use(player, args):
    if not args:
        await player.reply("使用什么？")
        return
    target_name = " ".join(args)
    target = player.resolve_content(target_name)
    if target is None:
        target = player.environment.resolve_content(target_name)
    if target is None:
        await player.reply(f"找不到 '{target_name}'。")
        return
    if not isinstance(target, Item):
        await player.reply(f"{target.name} 不能被使用。")
        return
    result = target.on_use(player)
    await player.reply(result)


async def cmd_wear(player, args):
    if not args:
        await player.reply("穿戴什么？")
        return
    target_name = " ".join(args)
    target = player.resolve_content(target_name)
    if target is None:
        await player.reply(f"你背包里没有 '{target_name}'。")
        return
    if not isinstance(target, Item) or not target.wear_pos:
        await player.reply(f"{target.name} 不能被穿戴。")
        return
    # Remove existing item in slot
    old = player.equipment.get(target.wear_pos)
    if old:
        old.put(player)  # back to inventory
        await player.reply(f"你取下了 {old.name}。")
    player.equipment[target.wear_pos] = target
    target.leave()  # remove from content list (still "owned")
    await player.reply(f"你装备了 {target.name}。")


async def cmd_remove(player, args):
    if not args:
        await player.reply("卸下什么？")
        return
    target_name = " ".join(args)
    found_slot = None
    for slot, item in player.equipment.items():
        if target_name.lower() in item.name.lower() or target_name.lower() == item.id.lower():
            found_slot = slot
            break
    if not found_slot:
        await player.reply(f"你没有装备 '{target_name}'。")
        return
    item = player.equipment.pop(found_slot)
    item.put(player)
    await player.reply(f"你卸下了 {item.name}。")


register("use", cmd_use, "use <物品>  使用物品")
register("wear", cmd_wear, "wear <装备>  穿戴装备")
register("remove", cmd_remove, "remove <装备>  卸下装备")
