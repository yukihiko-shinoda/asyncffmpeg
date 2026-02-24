"""FFmpeg process wrapping Popen object."""

from __future__ import annotations

from abc import abstractmethod
from contextlib import suppress
from logging import getLogger

# Reason: This package requires to use subprocess.
from subprocess import Popen  # nosec
from subprocess import TimeoutExpired  # nosec
from typing import TYPE_CHECKING

from livesubprocess import LiveSubProcessFactory

from asyncffmpeg.exceptions import FFmpegProcessError

if TYPE_CHECKING:
    from asyncffmpeg.type_alias import StreamSpec

__all__ = ["FFmpegProcess"]


class BaseFFmpegProcess:
    """FFmpeg process wrapping Popen object.

    This is the base specification of FFmpegProcess.
    """

    def __init__(self, time_to_force_termination: float) -> None:
        self.time_to_force_termination = time_to_force_termination
        self.logger = getLogger(__name__)
        self.popen = self.create_popen()
        self.live_popen = LiveSubProcessFactory.create_popen(self.popen)

    @abstractmethod
    def create_popen(self) -> Popen[bytes]:
        raise NotImplementedError  # pragma: no cover

    async def wait(self) -> None:
        """Waits for subprocess to finish."""
        stdout, return_code = await self.live_popen.wait()
        self.logger.info(stdout)
        # Check for error conditions:
        # 1. Non-zero return code (traditional error)
        # 2. File already exists error (FFmpeg 7.1+ returns 0 but this is still an error condition)
        if return_code != 0 or "already exists. Exiting" in stdout:
            self.logger.error("return_code = %d", return_code)
            raise FFmpegProcessError(stdout, return_code)

    async def quit(self, time_to_force_termination: float | None = None) -> None:
        """Quits FFmpeg process.

        see: https://github.com/kkroening/ffmpeg-python/issues/162#issuecomment-571820244
        """
        time_to_force_termination = self.get_time_to_force_termination(time_to_force_termination)
        self.logger.debug("Stop FFmpeg")
        # No event loop running (e.g. subprocess context): no async readers to stop.
        with suppress(RuntimeError):
            self.live_popen.stop()
        # communicate() can't work in Python 3.8 or older on Windows...
        _stdout, stderr = self.popen.communicate(str.encode("q"))  # Equivalent to send a Q
        self.logger.debug("Sent key Q")
        self.logger.info(stderr.decode("utf-8").rstrip())
        self.logger.debug("To be sure that the process ends")
        try:
            self.popen.wait(timeout=time_to_force_termination)
        # Reason: Whether reproducible or not is depend on implementation of FFmpeg.
        except TimeoutExpired:  # pragma: no cover
            self.logger.exception("Unexpected timeout")
        # Which is more like kill -9
        self.popen.terminate()

    def get_time_to_force_termination(self, time_to_force_termination: float | None) -> float:
        """Gets the time to force termination."""
        return self.time_to_force_termination if time_to_force_termination is None else time_to_force_termination


class FFmpegProcess(BaseFFmpegProcess):
    """FFmpeg process interface which has constructor with stream spec argument."""

    def __init__(self, time_to_force_termination: float, stream_spec: StreamSpec) -> None:
        self.stream_spec = stream_spec
        super().__init__(time_to_force_termination)

    @abstractmethod
    def create_popen(self) -> Popen[bytes]:
        raise NotImplementedError  # pragma: no cover
