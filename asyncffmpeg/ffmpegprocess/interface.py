"""FFmpeg process wrapping Popen object."""

from __future__ import annotations

import asyncio
from abc import abstractmethod
from logging import getLogger

# Reason: This package requires to use subprocess.
from subprocess import Popen  # nosec
from subprocess import TimeoutExpired  # nosec
from typing import TYPE_CHECKING

from asyncffmpeg.exceptions import FFmpegProcessError
from asyncffmpeg.pipe.realtime_pipe_reader import FFmpegRealtimePipeReader
from asyncffmpeg.pipe.realtime_pipe_reader import RealtimePipeReader

if TYPE_CHECKING:
    from asyncffmpeg.type_alias import StreamSpec

__all__ = ["FFmpegProcess"]


class BaseFFmpegProcess:
    """FFmpeg process wrapping Popen object.

    This is the base specification of FFmpegProcess.
    """

    def __init__(self, time_to_force_termination: int) -> None:
        self.time_to_force_termination = time_to_force_termination
        self.logger = getLogger(__name__)
        self.popen = self.create_popen()
        # To prevent blocking when popen.wait() (encountered on Windows)
        # see:
        #   - quiet mode for run_async method might cause ffmpeg process to stick.
        #     · Issue #195 · kkroening/ffmpeg-python
        #     https://github.com/kkroening/ffmpeg-python/issues/195#issuecomment-671062263
        #   - ffmpeg process stops outputting data after ~7 mins · Issue #370 · kkroening/ffmpeg-python
        #     https://github.com/kkroening/ffmpeg-python/issues/370#issuecomment-638391998
        self.realtime_pipe_reader = self.create_realtime_pipe_reader()

    @abstractmethod
    def create_popen(self) -> Popen[bytes]:
        raise NotImplementedError  # pragma: no cover

    def create_realtime_pipe_reader(self) -> RealtimePipeReader:
        return FFmpegRealtimePipeReader(self.popen)

    async def wait(self) -> None:
        """Waits for subprocess to finish."""
        return_code = self.popen.wait()
        # Wait for all stderr received
        # Tracking by pytest: tests/test_ffmpeg_coroutine.py::TestFFmpegCoroutine::test_excecption
        await asyncio.sleep(0.03)
        stderr = self.realtime_pipe_reader.read_stderr()
        self.logger.info(stderr)
        # Check for error conditions:
        # 1. Non-zero return code (traditional error)
        # 2. File already exists error (FFmpeg 7.1+ returns 0 but this is still an error condition)
        if return_code != 0 or "already exists. Exiting" in stderr:
            self.logger.error("return_code = %d", return_code)
            raise FFmpegProcessError(stderr, return_code)

    async def quit(self, time_to_force_termination: float | None = None) -> None:
        """Quits FFmpeg process.

        see: https://github.com/kkroening/ffmpeg-python/issues/162#issuecomment-571820244
        """
        time_to_force_termination = (
            time_to_force_termination if time_to_force_termination is not None else self.time_to_force_termination
        )
        self.logger.debug("Stop FFmpeg")
        # communicate() can't work in Python 3.8 or older on Windows...
        _stdout, stderr = self.popen.communicate(str.encode("q"))  # Equivalent to send a Q
        self.logger.debug("Sent key Q")
        self.logger.info(stderr.decode("utf-8").rstrip())
        self.logger.info(self.realtime_pipe_reader.read_stderr())
        self.logger.debug("To be sure that the process ends")
        try:
            self.popen.wait(timeout=time_to_force_termination)
        # Reason: Whether reproducible or not is depend on implementation of FFmpeg.
        except TimeoutExpired:  # pragma: no cover
            self.logger.exception("Unexpected timeout")
        # Which is more like kill -9
        self.popen.terminate()


class FFmpegProcess(BaseFFmpegProcess):
    """FFmpeg process interface which has constructor with stream spec argument."""

    def __init__(self, time_to_force_termination: int, stream_spec: StreamSpec) -> None:
        self.stream_spec = stream_spec
        super().__init__(time_to_force_termination)

    @abstractmethod
    def create_popen(self) -> Popen[bytes]:
        raise NotImplementedError  # pragma: no cover
