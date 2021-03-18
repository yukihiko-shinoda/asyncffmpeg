"""FFmpeg coroutine Factory."""
import os

from asyncffmpeg.ffmpeg_coroutine import TIME_TO_FORCE_TERMINATION, FFmpegCoroutine
from asyncffmpeg.ffmpegprocess.posix import FFmpegProcessPosix

if os.name == "nt":
    from asyncffmpeg.ffmpegprocess.windows_wrapper import FFmpegProcessWindowsWrapper  # pragma: no cover


class FFmpegCoroutineFactory:
    @staticmethod
    def create(*, time_to_force_termination: int = TIME_TO_FORCE_TERMINATION):
        return (
            FFmpegCoroutine(FFmpegProcessWindowsWrapper, time_to_force_termination=time_to_force_termination)
            if os.name == "nt"
            else FFmpegCoroutine(FFmpegProcessPosix, time_to_force_termination=time_to_force_termination)
        )
