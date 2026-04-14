from __future__ import annotations

import asyncio
from dataclasses import dataclass


@dataclass
class SchedulerRuntimeState:
    enabled: bool = False
    running: bool = False
    interval_seconds: int = 0


class SchedulerRuntime:
    def __init__(self) -> None:
        self.state = SchedulerRuntimeState()
        self._loop_task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._run_lock = asyncio.Lock()

    async def start(self, *, interval_seconds: int, run_once_coro) -> None:
        if self._loop_task is not None:
            return
        self.state.enabled = True
        self.state.running = True
        self.state.interval_seconds = interval_seconds
        self._stop_event.clear()

        async def runner() -> None:
            while not self._stop_event.is_set():
                async with self._run_lock:
                    await run_once_coro()
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=interval_seconds)
                except asyncio.TimeoutError:
                    continue

        self._loop_task = asyncio.create_task(runner())

    async def stop(self) -> None:
        self.state.running = False
        if self._loop_task is None:
            return
        self._stop_event.set()
        await self._loop_task
        self._loop_task = None


scheduler_runtime = SchedulerRuntime()
