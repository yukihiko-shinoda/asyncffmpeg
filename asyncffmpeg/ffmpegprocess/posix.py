"""Archive process."""

from __future__ import annotations

from typing import TYPE_CHECKING

import ffmpeg

from asyncffmpeg.ffmpegprocess.interface import FFmpegProcess

if TYPE_CHECKING:
    # Reason: This package requires to use subprocess.
    from subprocess import Popen  # nosec


class FFmpegProcessPosix(FFmpegProcess):
    """FFmpeg process wrapping Popen object."""

    def create_popen(self) -> Popen[bytes]:
        # Reason: Requires to update ffmpeg-python side.
        return ffmpeg.run_async(self.stream_spec, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)  # type: ignore[no-any-return]
