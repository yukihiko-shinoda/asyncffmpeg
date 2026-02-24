"""To keep task property even raise KeyboardInterrupt."""

from __future__ import annotations

import asyncio
import os
import signal
import time
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic

from tests.testlibraries import SECOND_SLEEP_FOR_TEST_MIDDLE
from tests.testlibraries.types import TypeVarReturnValue

if TYPE_CHECKING:
    from asyncio.tasks import Task
    from collections.abc import Coroutine


class KeyboardInterrupter(Generic[TypeVarReturnValue]):
    """To keep task property even raise KeyboardInterrupt."""

    def __init__(
        self,
        target_coroutine: Coroutine[Any, Any, TypeVarReturnValue],
        get_process_id: Coroutine[Any, Any, int],
    ) -> None:
        # Reason: pytest bug. pylint: disable=unsubscriptable-object
        self.target_coroutine = target_coroutine
        self.get_process_id = get_process_id
        self.task: Task[TypeVarReturnValue] | None = None
        self.logger = getLogger(__name__)

    def test_keyboard_interrupt(self) -> None:
        """Tests keyboard interrupt and send response to pytest by socket when succeed.

        The assertion window is only ~0.25 s (SECOND_SLEEP_FOR_TEST_MIDDLE).
        Any blocking call inside quit() that exceeds this budget will cause
        ``assert self.task.done()`` to fail.

        Event timeline after ``os.kill(0, CTRL_C_EVENT)``::

            t = 0s    CTRL_C_EVENT sent to process group A
            t ≈ 0s    subprocess_wrapper_windows.py raises KeyboardInterrupt → asyncio.run() exits
            t ≈ 0s    Worker process raises KeyboardInterrupt → FFmpegCoroutine.execute()
                      calls ``await self.ffmpeg_process.quit()``
            t ≈ 0s    quit() must return quickly — any popen.wait(N) blocks for N seconds
            t = 0.25s test_keyboard_interrupt() wakes from time.sleep(0.25)
            t = 0.25s ``assert self.task.done()`` — fails if quit() is still blocking
        """
        self.logger.debug("Test keyboard interrupt start")
        try:
            asyncio.run(self.keyboard_interrupt())
        except KeyboardInterrupt:
            print("Sleep in except")
            time.sleep(SECOND_SLEEP_FOR_TEST_MIDDLE)
            print("Assert in except")
            self.debug_task()
            assert self.task is not None
            assert self.task.done()
            assert self.task.cancelled()
            raise

    def debug_task(self) -> None:
        """Debug task state."""
        self.logger.debug(
            "Debug task: task=%s done=%s cancelled=%s",
            self.task,
            self.task.done() if self.task is not None else "N/A",
            self.task.cancelled() if self.task is not None else "N/A",
        )

    async def keyboard_interrupt(self) -> None:
        """Simulates keyboard interrupt by CTRL_C_EVENT."""
        self.logger.debug("Keyboard interrupt start")
        print("Create task")
        self.task = asyncio.create_task(self.target_coroutine)
        process_id = await self.get_process_id
        try:
            # Reason: only for Windows. pylint: disable=no-member
            self.logger.debug("Sending CTRL_C_EVENT to process_id=%d", process_id)
            os.kill(process_id, signal.CTRL_C_EVENT)  # type: ignore[attr-defined]
            self.logger.debug("CTRL_C_EVENT sent; sleeping %.2fs", SECOND_SLEEP_FOR_TEST_MIDDLE)
            print("Await task")
            await self.task
        except KeyboardInterrupt:
            print("Await task in except")
            # await self.task
            print("Assert")
            self.logger.debug(
                "KeyboardInterrupt in keyboard_interrupt: task.done()=%s task.cancelled()=%s",
                self.task.done(),
                self.task.cancelled(),
            )
            assert not self.task.done()
            print("Task not done")
            assert not self.task.cancelled()
            print("Task cancelled")
            raise
