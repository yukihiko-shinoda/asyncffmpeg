"""FFmpeg coroutine interface."""
import asyncio
from logging import getLogger
from typing import Awaitable, Callable, Optional, Type, TypeVar

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess
from asyncffmpeg.type_alias import StreamSpec

# Since the seconds to Docker wait for stop before killing it is 10
# see: https://docs.docker.com/engine/reference/commandline/stop/
TIME_TO_FORCE_TERMINATION = 8
TypeVarFFmpegProcess = TypeVar("TypeVarFFmpegProcess", bound=FFmpegProcess)


class FFmpegCoroutine:
    """
    Interface of FFmpeg croutine
    since different implementation required between POSIX and Windows.
    """

    def __init__(
        self,
        class_ffmpeg_process: Type[TypeVarFFmpegProcess],
        *,
        time_to_force_termination: int = TIME_TO_FORCE_TERMINATION
    ) -> None:
        self.class_ffmpeg_process = class_ffmpeg_process
        self.time_to_force_termination = time_to_force_termination
        self.ffmpeg_process: Optional[TypeVarFFmpegProcess] = None
        self.logger = getLogger(__name__)

    async def execute(
        self,
        create_stream_spec: Callable[[], Awaitable[StreamSpec]],
        *,
        after_start: Optional[Callable[[TypeVarFFmpegProcess], Awaitable]] = None
    ) -> None:
        """
        Executes FFmpeg process.
        This method defines workflow including interruption and logging.
        """
        try:
            self.logger.debug("FFmpeg coroutine start")
            self.ffmpeg_process = self.class_ffmpeg_process(await create_stream_spec())
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
            raise error
        except Exception as error:
            self.logger.exception("%s", error)
            raise error
        finally:
            self.logger.debug("FFmpeg coroutine finish")
