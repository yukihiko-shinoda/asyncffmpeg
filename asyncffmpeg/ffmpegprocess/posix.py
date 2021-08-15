"""Archive process."""
from subprocess import Popen
from typing import Optional

import ffmpeg

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess


class FFmpegProcessPosix(FFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def create_popen(self) -> Popen[bytes]:
        # Reason: Requires to update ffmpeg-python side.
        return ffmpeg.run_async(self.stream_spec, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)  # type: ignore

    async def quit(self, time_to_force_termination: Optional[float] = None) -> None:
        # Otherwise, we'll get OSError: [Errno 9] Bad file descriptor.
        self.realtime_pipe_reader.stop()
        await super().quit(time_to_force_termination)
