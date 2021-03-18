"""
The code to run in dedicated process group for Windows.

There are 2 purposes:

- to prevent Ctrl + C event propergation ti subprocess (raw FFmpeg execution)
- to prevent effect of setting ConsoleCtrlHandler to parent process (FFmpeg coroutine)
"""
import asyncio
import sys
from logging import DEBUG, basicConfig
from subprocess import PIPE, Popen
from typing import List

# Reason: Windows only. pylint: disable=import-error
import win32api
import win32con

from asyncffmpeg.ffmpegprocess.interface import BaseFFmpegProcess


class FFmpegProcessWindows(BaseFFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def __init__(self, time_to_force_termination: int, argument: List[str]) -> None:
        self.argument = argument
        basicConfig(stream=sys.stdout, level=DEBUG)
        super().__init__(time_to_force_termination)
        win32api.SetConsoleCtrlHandler(None, False)
        win32api.SetConsoleCtrlHandler(self.handle, True)

    def create_popen(self) -> Popen:
        return Popen(["ffmpeg", *self.argument], stdin=PIPE, stdout=PIPE, stderr=PIPE)

    def handle(self, event):
        """Handle console control events (like Ctrl-C)."""
        if event in (
            win32con.CTRL_C_EVENT,
            win32con.CTRL_LOGOFF_EVENT,
            win32con.CTRL_BREAK_EVENT,
            win32con.CTRL_SHUTDOWN_EVENT,
            win32con.CTRL_CLOSE_EVENT,
        ):
            self.logger.info("Console event %s: shutting down bus", event)
            asyncio.run(self.quit(self.time_to_force_termination))
            # 'First to return True stops the calls'
            return 1
        return 0


ffmpeg_process = FFmpegProcessWindows(int(sys.argv[1]), sys.argv[2:])
asyncio.run(ffmpeg_process.wait())
