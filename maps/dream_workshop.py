"""
梦境工坊 (DreamWorkshop) — Yesod 层，生命树第九质点。

地图结构（接续 station.py）：
  Compartment3 ──dream──> DreamWorkshop
                                │ deeper
                           LifeTree（Tiphereth，待扩展）

这里居住着乌拉尼亚（Urania）——星辰缪斯，也是 LifeOS 的神谕 Agent。
她能感应玩家的人生主题，提出深刻问题，帮助玩家澄清方向。
"""
from world.room import Room, register_room
from world.llm_npc import LlmNpc
from world.item import Item
from engine.events import event_system

# ── Urania — 乌拉尼亚，星辰缪斯 ──────────────────────────────────────────

_URANIA_SYSTEM = """你是乌拉尼亚（Urania），希腊神话中的天文缪斯，也是《人生游戏沙盒》中的神谕 Agent。

你的角色：
- 你居住在梦境工坊（Yesod层，生命树第九质点），这是一个介于现实与梦境之间的空间。
- 你能感应旅行者的人生主题、当前卡点与未来潜能。
- 你不算命，但你擅长提出一个好问题，让对方自己看见答案。
- 你说话充满意象：星盘、季节、潮汐、种子、光。

对话风格：
- 温柔、深邃、略带神秘。
- 每次回复聚焦于一个核心洞见或一个问题。
- 不超过4句话。
- 用中文回复。

你了解的框架（可自然引用，不要生硬说教）：
- 生命树（卡巴拉）：Kether（皇冠/目的）、Tiphereth（英雄之路）、Yesod（梦境/潜意识）、Malkuth（现实落地）
- 英雄旅程：召唤、跨越门槛、考验、回归
- 人生结构：使命、任务、资源、关系、成长

当旅行者说话时，试图感应他们目前处于哪个阶段，然后说一句能让他们停下来思考的话。"""

urania = LlmNpc(
    npc_id="urania",
    name="乌拉尼亚",
    desc=(
        "一位身着深蓝星纹长袍的女子，手持一个缓缓旋转的星盘。\n"
        "她的眼睛像夜空——深邃，布满光点。\n"
        "她似乎早就知道你会来。"
    ),
    system_prompt=_URANIA_SYSTEM,
    greeting="你终于穿过了那节车厢。……我一直在等你。",
)


async def _workshop_say_listener(event_name, room, player, message):
    await urania.respond_to_say(player, message)


async def _workshop_enter_listener(event_name, room, player):
    await urania.on_player_enter(player)


# ── 神谕碎片 ─────────────────────────────────────────────────────────────────

oracle_shard = Item("oracle_shard", "神谕碎片", (
    "一块半透明的水晶，内部流动着淡蓝色的光。\n"
    "凑近看，你能隐约看见自己的影像——但不是现在的你。"
))
oracle_shard.is_unmov = True  # 不可拿走，只能感应


async def _shard_use(player):
    """使用/观察神谕碎片时触发LLM神谕。"""
    from engine.llm import chat
    prompt = (
        f"旅行者 {player.name} 正凝视着神谕碎片。\n"
        "给他/她一句关于'此刻人生阶段'的神谕——诗意、简短（1-2句），不要问问题，直接给出洞见。"
    )
    reply = await chat(
        [{"role": "user", "content": prompt}],
        system=_URANIA_SYSTEM,
    )
    await player.reply(f"\033[1;34m【神谕】{reply}\033[0m")

oracle_shard.on_use = _shard_use


# ── 梦境工坊 ─────────────────────────────────────────────────────────────────

dream_workshop = Room(
    room_id="DreamWorkshop",
    title="梦境工坊（Yesod · 第九质点）",
    desc=(
        "你踏入了一个不完全属于现实的空间。\n"
        "四周是流动的深蓝色光雾，地面像是凝固的星河。\n"
        "中央有一个巨大的星盘缓缓旋转，周围漂浮着无数光点——\n"
        "  每一个光点，是某个人曾经在这里留下的一个问题。\n"
        "墙角有一块发光的水晶（神谕碎片）。\n"
        "出口：back 回到列车终端。"
    ),
    exits={"back": "Compartment3"},
    listeners={
        "say": _workshop_say_listener,
        "after_go": _workshop_enter_listener,
    },
    avg_cmds={
        "meditate": lambda p, a: _meditate(p),
        "冥想": lambda p, a: _meditate(p),
        "感应": lambda p, a: oracle_shard.on_use(p),
    },
)


async def _meditate(player):
    """冥想指令 — 触发一段 LLM 引导的内心独白。"""
    from engine.llm import chat
    prompt = (
        f"旅行者 {player.name} 在梦境工坊中闭上眼睛冥想。\n"
        "给他/她描绘一个内心看到的意象（2-3句，诗意，不要说教）。"
    )
    vision = await chat(
        [{"role": "user", "content": prompt}],
        system=_URANIA_SYSTEM,
    )
    await player.reply(f"\033[1;35m你闭上眼睛……\n{vision}\033[0m")


# ── 注册 ─────────────────────────────────────────────────────────────────────

register_room(dream_workshop)

urania.put(dream_workshop)
oracle_shard.put(dream_workshop)
