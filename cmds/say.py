from cmds import register
from engine.events import event_system


async def cmd_say(player, args):
    if not args:
        await player.reply("说什么？")
        return
    message = " ".join(args)
    room = player.environment
    broadcast = f"{player.name} 说：{message}"

    # Send to player themselves
    await player.reply(f"你说：{message}")

    # Broadcast to room (excluding player since they already see it)
    await room.channel.say(broadcast, player)

    # Trigger say event (NPCs can react)
    await event_system.trigger("say", room, player, message)


register("say", cmd_say, "say <内容>  对房间里的人说话")
register("'", cmd_say, "say 的缩写")
