from __future__ import annotations
import asyncio
import time
import weakref
from typing import Callable


class HeartOfWorld:
    def __init__(self):
        self._members: weakref.WeakSet = weakref.WeakSet()
        self._rate = 1.0  # seconds

    def register(self, obj):
        self._members.add(obj)

    def unregister(self, obj):
        self._members.discard(obj)

    async def run(self):
        while True:
            await asyncio.sleep(self._rate)
            now = time.time()
            for obj in list(self._members):
                try:
                    result = obj.heart_beat(now)
                    if asyncio.iscoroutine(result):
                        await result
                except Exception:
                    pass

    async def after(self, delay: float, callback: Callable):
        async def _run():
            await asyncio.sleep(delay)
            result = callback()
            if asyncio.iscoroutine(result):
                await result
        asyncio.create_task(_run())


# Singleton
heart_of_world = HeartOfWorld()
