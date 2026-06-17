from __future__ import annotations
import copy
from world.space import SpaceObject

GLOBAL_ITEM_LIST: dict[str, "Item"] = {}


class Item(SpaceObject):
    def __init__(self, item_id: str, name: str, desc: str = ""):
        super().__init__()
        self.id = item_id
        self.name = name
        self.desc = desc
        self.count: int = 1
        self.is_stackable: bool = False
        self.is_unmov: bool = False
        self.wear_pos: str = ""  # "" means not wearable
        GLOBAL_ITEM_LIST[item_id] = self

    def put(self, env: SpaceObject):
        if self.is_stackable:
            for obj in env.content:
                if isinstance(obj, Item) and obj.id == self.id:
                    obj.count += self.count
                    return
        super().put(env)

    def clone(self) -> "Item":
        obj = copy.copy(self)
        obj.content = []
        obj.environment = None
        return obj

    def to_str(self) -> str:
        count_str = f" x{self.count}" if self.count > 1 else ""
        return f"{self.name}{count_str} — {self.desc}"

    def on_use(self, player) -> str:
        return f"你使用了 {self.name}，但什么都没发生。"


class Weapon(Item):
    def __init__(self, item_id: str, name: str, desc: str = "", damage: tuple[int, int] = (1, 4)):
        super().__init__(item_id, name, desc)
        self.wear_pos = "right_hand"
        self.damage_min, self.damage_max = damage

    def roll_damage(self) -> int:
        import random
        return random.randint(self.damage_min, self.damage_max)
