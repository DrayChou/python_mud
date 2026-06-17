from __future__ import annotations
import asyncio
import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from world.char import Charactor

MISS_MESSAGES = [
    "{attacker} 的攻击被 {target} 轻松躲开！",
    "{attacker} 挥动武器，却打了个空！",
    "{target} 灵活地侧身，让过了 {attacker} 的攻击。",
]

HIT_MESSAGES_LIGHT = [
    "{attacker} 击中了 {target}，造成 {dmg} 点伤害。",
]

HIT_MESSAGES_HEAVY = [
    "{attacker} 猛烈地打击 {target}，造成 {dmg} 点重创！",
]

DEATH_MESSAGES = [
    "{target} 倒在了地上，再也起不来了。",
    "{target} 发出最后一声呻吟，缓缓倒下。",
]


def _fmt(template: str, attacker: "Charactor", target: "Charactor", **kw) -> str:
    return template.format(
        attacker=attacker.name,
        target=target.name,
        **kw,
    )


async def combat(attacker: "Charactor", target: "Charactor"):
    from engine.events import event_system

    # Hit roll: base 50%
    hit_chance = 50
    if random.randint(1, 100) > hit_chance:
        msg = _fmt(random.choice(MISS_MESSAGES), attacker, target)
        await _broadcast_combat(attacker, target, msg)
        return

    # Damage
    weapon = attacker.equipment.get("right_hand")
    if weapon and hasattr(weapon, "roll_damage"):
        dmg = weapon.roll_damage()
    else:
        dmg = random.randint(1, 3)

    # STR bonus placeholder
    dmg = max(1, dmg)

    hp_pct = target.hp / max(target.max_hp, 1)
    templates = HIT_MESSAGES_HEAVY if hp_pct < 0.3 else HIT_MESSAGES_LIGHT
    msg = _fmt(random.choice(templates), attacker, target, dmg=dmg)

    await target.modify_hp(-dmg)
    await _broadcast_combat(attacker, target, msg)

    if target.hp <= 0:
        death_msg = _fmt(random.choice(DEATH_MESSAGES), attacker, target)
        await _broadcast_combat(attacker, target, death_msg)
        # Clear combat state
        attacker.fright_list.discard(id(target))
        target.fright_list.discard(id(attacker))
        # Trigger die event on target's room
        if target.environment:
            await event_system.trigger("die", target.environment, target)
        await target.on_death(attacker)


async def _broadcast_combat(attacker: "Charactor", target: "Charactor", msg: str):
    room = attacker.environment
    if room is None:
        return
    # Send to combatants directly
    for combatant in [attacker, target]:
        if hasattr(combatant, "reply"):
            await combatant.reply(msg)
    # Broadcast to room bystanders
    if hasattr(room, "channel"):
        await room.channel.say(msg, attacker, target)
