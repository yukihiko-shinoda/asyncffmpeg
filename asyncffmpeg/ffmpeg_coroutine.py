"""FFmpeg coroutine interface."""

from __future__ import annotations

import asyncio
from asyncio.exceptions import CancelledError
from logging import getLogger
from signal import SIGTERM
from signal import signal
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Generic
from typing import NoReturn
from typing import TypeVar

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from asyncffmpeg.type_alias import StreamSpec


__all__ = ["FFmpegCoroutine"]

# Since the seconds to Docker wait for stop before killing it is 10
# see: https://docs.docker.com/engine/reference/commandline/stop/
TIME_TO_FORCE_TERMINATION = 8
TypeVarFFmpegProcess = TypeVar("TypeVarFFmpegProcess", bound=FFmpegProcess)


class FFmpegCoroutine(Generic[TypeVarFFmpegProcess]):
    """Interface of FFmpeg croutine since different implementation required between POSIX and Windows."""

    def __init__(
        self,
        class_ffmpeg_process: type[TypeVarFFmpegProcess],
        *,
        time_to_force_termination: int = TIME_TO_FORCE_TERMINATION,
    ) -> None:
        self.class_ffmpeg_process = class_ffmpeg_process
        self.time_to_force_termination = time_to_force_termination
        self.ffmpeg_process: TypeVarFFmpegProcess | None = None
        self.logger = getLogger(__name__)

    async def execute(
        self,
        create_stream_spec: Callable[[], Awaitable[StreamSpec]],
        *,
        after_start: Callable[[TypeVarFFmpegProcess], Awaitable[Any]] | None = None,
    ) -> None:
        """Executes FFmpeg process.

        This method defines workflow including interruption and logging.
        """
        try:
            self.logger.debug("FFmpeg coroutine start")
            signal(SIGTERM, self.sigterm_handler)
            self.ffmpeg_process = self.class_ffmpeg_process(self.time_to_force_termination, await create_stream_spec())
            self.logger.debug("Instantiate FFmpeg process finish")
            if after_start:
                self.logger.debug("Await after_start coroutine start")
                await after_start(self.ffmpeg_process)
            self.logger.debug("Await FFmpeg process start")
            await self.ffmpeg_process.wait()
            self.logger.debug("Await FFmpeg process finish")
        except (KeyboardInterrupt, asyncio.CancelledError) as error:
            self.logger.info("Process cancelled")
            self.logger.debug(type(error).__name__)
            if self.ffmpeg_process is not None:
                self.logger.info("FFmpeg process quit start")
                await self.ffmpeg_process.quit(self.time_to_force_termination)
                self.logger.info("FFmpeg process quit finish")
            raise
        except Exception:
            self.logger.exception("Unexpected error occurred")
            raise
        finally:
            self.logger.debug("FFmpeg coroutine finish")

    # Reason:
    #   ANN401: To follow the specification of Python.
    #   no cover: Can't collect coverage because of termination.
    def sigterm_handler(self, _signum: int, _frame: Any | None) -> NoReturn:  # noqa: ANN401 # pragma: no cover
        self.logger.debug("SIGTERM handler: Start")
        raise CancelledError
