"""The code to run in dedicated process group for Windows.

There are 2 purposes:

- to prevent Ctrl + C event propergation ti subprocess (raw FFmpeg execution)
- to prevent effect of setting ConsoleCtrlHandler to parent process (FFmpeg coroutine)
"""

from __future__ import annotations

import sys
from pathlib import Path

# Reason: This package requires to use subprocess.
# Reason: CREATE_NEW_PROCESS_GROUP is packaged only in Windows
from subprocess import CREATE_NEW_PROCESS_GROUP  # type: ignore[attr-defined]  # nosec
from subprocess import PIPE  # nosec
from subprocess import Popen  # nosec

import ffmpeg

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess
from asyncffmpeg.pipe.realtime_pipe_reader import RealtimePipeReader
from asyncffmpeg.pipe.realtime_pipe_reader import StringRealtimePipeReader


class FFmpegProcessWindowsWrapper(FFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def create_popen(self) -> Popen[bytes]:
        argument = [
            sys.executable,
            str(Path(__file__).resolve().parent / "windows.py"),
            str(self.time_to_force_termination),
            *ffmpeg.get_args(self.stream_spec),
        ]
        self.logger.debug(argument)
        # Reason:
        #   consider-using-with: This method is instead of ffmpeg.run_async(). pylint: disable=consider-using-with
        #   S603: Imput is limited enough.
        return Popen(argument, creationflags=CREATE_NEW_PROCESS_GROUP, stdout=PIPE, stderr=PIPE)  # noqa: S603  # nosec

    def create_realtime_pipe_reader(self) -> RealtimePipeReader:
        return StringRealtimePipeReader(self.popen)

    async def quit(self, time_to_force_termination: float | None = None) -> None:
        self.logger.info(self.realtime_pipe_reader.read_stdout())
        self.logger.error(self.realtime_pipe_reader.read_stderr())
        self.popen.wait(time_to_force_termination)
        self.logger.error(self.realtime_pipe_reader.read_stderr())
