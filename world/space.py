from __future__ import annotations
from typing import Any, Optional


class SpaceObject:
    def __init__(self):
        self.id: str = ""
        self.name: str = ""
        self.desc: str = ""
        self.environment: Optional["SpaceObject"] = None
        self.content: list["SpaceObject"] = []
        self.listeners: dict[str, Any] = {}

    def put(self, env: "SpaceObject"):
        if self.environment is not None:
            self.leave()
        self.environment = env
        env.content.append(self)

    def leave(self):
        if self.environment is not None:
            try:
                self.environment.content.remove(self)
            except ValueError:
                pass
            self.environment = None

    def search(self, key: str, value: Any) -> list["SpaceObject"]:
        return [obj for obj in self.content if getattr(obj, key, None) == value]

    def resolve_content(self, name: str) -> Optional["SpaceObject"]:
        name_lower = name.lower()
        # Exact id match
        for obj in self.content:
            if obj.id.lower() == name_lower:
                return obj
        # Fuzzy name match
        for obj in self.content:
            if name_lower in obj.name.lower():
                return obj
        return None

    def to_str(self) -> str:
        return f"{self.name} — {self.desc}"
