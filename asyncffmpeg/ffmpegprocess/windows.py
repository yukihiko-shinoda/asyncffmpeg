"""The code to run in dedicated process group for Windows.

There are 2 purposes:

- to prevent Ctrl + C event propergation ti subprocess (raw FFmpeg execution)
- to prevent effect of setting ConsoleCtrlHandler to parent process (FFmpeg coroutine)
"""

import asyncio
import sys
from logging import DEBUG
from logging import basicConfig

# Reason: This package requires to use subprocess.
from subprocess import PIPE  # nosec
from subprocess import Popen  # nosec

# Reason: Windows only. pylint: disable=import-error
import win32api
import win32con

from asyncffmpeg.ffmpegprocess.interface import BaseFFmpegProcess


class FFmpegProcessWindows(BaseFFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def __init__(self, time_to_force_termination: int, argument: list[str]) -> None:
        self.argument = argument
        basicConfig(stream=sys.stdout, level=DEBUG)
        super().__init__(time_to_force_termination)
        # Reason:
        win32api.SetConsoleCtrlHandler(None, badd=False)
        win32api.SetConsoleCtrlHandler(self.handle, badd=True)

    def create_popen(self) -> Popen[bytes]:
        # Reason:
        # consider-using-with: This method is instead of ffmpeg.run_async(). pylint: disable=consider-using-with
        # S603: Running ffMpeg is not very risky.
        # S607: For user's convenience.
        return Popen(["ffmpeg", *self.argument], stdin=PIPE, stdout=PIPE, stderr=PIPE)  # noqa: S603,S607  # nosec

    def handle(self, event: int) -> int:
        """Handle console control events (like Ctrl-C).

        Maybe, copied from CherryPy:
        - cherrypy.process.win32 — CherryPy 0.1.dev56+g0f364c0dd documentation
          https://docs.cherrypy.dev/en/latest/_modules/cherrypy/process/win32.html#ConsoleCtrlHandler.handle
        """
        if event in (
            win32con.CTRL_C_EVENT,
            win32con.CTRL_LOGOFF_EVENT,
            win32con.CTRL_BREAK_EVENT,
            win32con.CTRL_SHUTDOWN_EVENT,
            win32con.CTRL_CLOSE_EVENT,
        ):
            self.logger.info("Console event %s: shutting down bus", event)
            asyncio.run(self.quit(self.time_to_force_termination))
            # 'First to return True stops the calls'  noqa: ERA001
            return 1
        return 0


ffmpeg_process = FFmpegProcessWindows(int(sys.argv[1]), sys.argv[2:])
asyncio.run(ffmpeg_process.wait())
