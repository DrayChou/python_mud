"""
车站世界地图 — 对应 Lua 版 MudLib/Map/ 下的车站场景。

地图结构：
  StationHall（大厅）──east──> Platform（站台）
                                    │ north
                              Compartment1（车厢1）
                                    │ north
                              Compartment2（车厢2）
                                    │ north
                              Compartment3（车厢3，有 dream 出口）
                                    │ dream
                              DreamWorkshop（梦境工坊，见 dream_workshop.py）
"""
from world.room import Room, register_room
from world.llm_npc import LlmNpc
from world.monster import Monster
from world.item import Item, Weapon
from engine.events import event_system


# ── Items ──────────────────────────────────────────────────────────────────

ticket = Item("ticket", "车票", "一张破旧的单程车票。")
ticket.is_stackable = True

rusty_knife = Weapon("rusty_knife", "锈铁刀", "一把锈迹斑斑的小刀，看起来还能用。", damage=(2, 6))

# ── NPCs ───────────────────────────────────────────────────────────────────

ticket_clerk = LlmNpc(
    npc_id="ticket_clerk",
    name="售票员",
    desc="一位神情疲惫的中年售票员，眼神空洞却深邃，仿佛见过太多来来往往的旅客。",
    system_prompt=(
        "你是一个神秘的车站售票员，守候在一个时间静止的老式车站。\n"
        "你见过无数旅行者，每个人都在寻找某种'终点'。\n"
        "你说话简短、充满隐喻，偶尔会抛出让人深思的问题。\n"
        "你知道这趟列车不是普通的列车——它通往每个人内心最深处。\n"
        "你不透露具体答案，但会引导旅行者自己去发现。\n"
        "用中文回复，语气平静而略带诗意，回复不超过3句话。"
    ),
    greeting="嗯……又来一位了。",
)


async def _hall_say_listener(event_name, room, player, message):
    await ticket_clerk.respond_to_say(player, message)


# ── Monsters ────────────────────────────────────────────────────────────────

shadow = Monster("shadow", "车厢阴影", "黑暗中一个扭曲的人形轮廓，散发着寒意。", hp=20, respawn_delay=60.0)
lost_soul = Monster("lost_soul", "迷失的旅客", "一个茫然徘徊的灵魂，眼中只剩空洞。", hp=35, respawn_delay=90.0)

# ── Rooms ───────────────────────────────────────────────────────────────────

station_hall = Room(
    room_id="StationHall",
    title="车站入口大厅",
    desc=(
        "一个昏黄灯光下的老式车站大厅。\n"
        "斑驳的墙壁上挂着一块巨大的时刻表，所有的时间栏都是空白的。\n"
        "售票窗口后面坐着一个沉默的售票员。"
    ),
    exits={"east": "Platform"},
    listeners={
        "say": _hall_say_listener,
        "after_go": lambda en, room, player: ticket_clerk.on_player_enter(player),
    },
)

platform = Room(
    room_id="Platform",
    title="候车站台",
    desc=(
        "一条长长的水泥站台，铁轨延伸向远处的黑暗中。\n"
        "空气中飘着淡淡的煤烟味，几盏锈蚀的路灯在风中摇曳。"
    ),
    exits={"west": "StationHall", "north": "Compartment1"},
)

compartment1 = Room(
    room_id="Compartment1",
    title="列车第一节车厢",
    desc=(
        "陈旧的绿皮列车车厢，木质座椅上积了厚厚的灰尘。\n"
        "窗外是永恒的黑夜，偶尔有什么东西掠过玻璃。"
    ),
    exits={"south": "Platform", "north": "Compartment2"},
)

compartment2 = Room(
    room_id="Compartment2",
    title="列车第二节车厢",
    desc=(
        "这节车厢里的灯只有一盏还亮着，发出橘黄色的微光。\n"
        "角落里堆着一些遗落的行李，没有人来认领。"
    ),
    exits={"south": "Compartment1", "north": "Compartment3"},
)

compartment3 = Room(
    room_id="Compartment3",
    title="列车第三节车厢（终端）",
    desc=(
        "列车的最后一节车厢，前方是一道焊死的铁门。\n"
        "墙上有人用指甲刻下了密密麻麻的文字：\n"
        "  '每一次出发都是一次回归。'\n"
        "暗影在这里更浓，仿佛有什么东西在等待。"
    ),
    exits={"south": "Compartment2", "dream": "DreamWorkshop"},
    avg_cmds={
        "read_wall": lambda p, a: p.reply(
            "你仔细阅读墙上的文字……\n"
            "它们记录了无数个旅行者的名字，和他们对'终点'的猜测。\n"
            "最后一行还空着。也许等你来填写？"
        )
    },
)

# ── Register rooms ──────────────────────────────────────────────────────────

register_room(station_hall)
register_room(platform)
register_room(compartment1)
register_room(compartment2)
register_room(compartment3)

# ── Place objects ────────────────────────────────────────────────────────────

ticket_clerk.put(station_hall)
ticket.put(platform)
rusty_knife.put(compartment1)
shadow.put(compartment3)
lost_soul.put(compartment2)
