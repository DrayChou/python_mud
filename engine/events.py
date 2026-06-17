from __future__ import annotations
import asyncio
from collections import defaultdict
from typing import Any, Callable


class EventSystem:
    def __init__(self):
        # event_name → target_id → sorted list of {callback, priority}
        self._listeners: dict[str, dict[int, list[dict]]] = defaultdict(lambda: defaultdict(list))

    def register(self, event: str, callback: Callable, target: Any, priority: int = 0):
        tid = id(target)
        entry = {"callback": callback, "priority": priority}
        bucket = self._listeners[event][tid]
        bucket.append(entry)
        bucket.sort(key=lambda e: e["priority"])

    def remove(self, event: str, callback: Callable, target: Any):
        tid = id(target)
        bucket = self._listeners[event].get(tid, [])
        self._listeners[event][tid] = [e for e in bucket if e["callback"] is not callback]

    async def trigger(self, event: str, target: Any, *args) -> tuple[bool, list]:
        tid = id(target)
        bucket = self._listeners[event].get(tid, [])
        handled = False
        results = []
        for entry in list(bucket):
            cb = entry["callback"]
            if asyncio.iscoroutinefunction(cb):
                result = await cb(event, target, *args)
            else:
                result = cb(event, target, *args)
            if result is not None:
                handled = True
                results.append(result)
        return handled, results


# Global event system instance
event_system = EventSystem()
