"""To keep task property even raise KeyboardInterrupt."""

import asyncio
import os
import signal
import time
from collections.abc import Coroutine
from logging import getLogger
from typing import TYPE_CHECKING
from typing import Any
from typing import Generic

from tests.testlibraries import SECOND_SLEEP_FOR_TEST_MIDDLE
from tests.testlibraries.types import TypeVarReturnValue

if TYPE_CHECKING:
    from asyncio.tasks import Task


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
        """Tests keyboard interrupt and send response to pytest by socket when succeed."""
        self.logger.debug("Test keyboard interrupt start")
        try:
            asyncio.run(self.keyboard_interrupt())
        except KeyboardInterrupt:
            print("Sleep in except")
            time.sleep(SECOND_SLEEP_FOR_TEST_MIDDLE)
            print("Assert in except")
            assert self.task is not None
            assert self.task.done()
            assert self.task.cancelled()
            raise

    async def keyboard_interrupt(self) -> None:
        """Simulates keyboard interrupt by CTRL_C_EVENT."""
        self.logger.debug("Keyboard interrupt start")
        print("Create task")
        self.task = asyncio.create_task(self.target_coroutine)
        process_id = await self.get_process_id
        try:
            # Reason: only for Windows. pylint: disable=no-member
            os.kill(process_id, signal.CTRL_C_EVENT)  # type: ignore[attr-defined]
            print("Await task")
            await self.task
        except KeyboardInterrupt:
            print("Await task in except")
            # await self.task
            print("Assert")
            assert not self.task.done()
            print("Task not done")
            assert not self.task.cancelled()
            print("Task cancelled")
            raise
