"""
The code to run in dedicated process group for Windows.

There are 2 purposes:

- to prevent Ctrl + C event propergation ti subprocess (raw FFmpeg execution)
- to prevent effect of setting ConsoleCtrlHandler to parent process (FFmpeg coroutine)
"""
import sys
from pathlib import Path

# Reason: CREATE_NEW_PROCESS_GROUP is packaged only in Windows
from subprocess import CREATE_NEW_PROCESS_GROUP, PIPE, Popen  # type: ignore

import ffmpeg

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess
from asyncffmpeg.pipe.realtime_pipe_reader import RealtimePipeReader, StringRealtimePipeReader


class FFmpegProcessWindowsWrapper(FFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def create_popen(self) -> Popen:
        argument = [
            sys.executable,
            str(Path(__file__).resolve().parent / "windows.py"),
            *ffmpeg.get_args(self.stream_spec),
        ]
        self.logger.debug(argument)
        return Popen(argument, creationflags=CREATE_NEW_PROCESS_GROUP, stdout=PIPE, stderr=PIPE)

    def create_realtime_pipe_reader(self) -> RealtimePipeReader:
        return StringRealtimePipeReader(self.popen)

    async def quit(self, time_to_force_termination) -> None:
        self.logger.info(self.realtime_pipe_reader.read_stdout())
        self.logger.error(self.realtime_pipe_reader.read_stderr())
        self.popen.wait(time_to_force_termination)
        self.logger.error(self.realtime_pipe_reader.read_stderr())
