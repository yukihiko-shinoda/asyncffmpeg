import os
import re
import sys
import time
from pathlib import Path
from subprocess import PIPE, Popen

import ffmpeg

from asyncffmpeg.pipe.realtime_pipe_reader import FFmpegRealtimePipeReader, StringRealtimePipeReader
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_LONG, SECOND_SLEEP_FOR_TEST_SHORT
from tests.testlibraries.instance_resource import InstanceResource


class TestStringRealtimePipeReader:
    def test(self) -> None:
        command = [sys.executable, str(Path("tests") / "testlibraries" / "print_forever.py")]
        popen = Popen(command, stdout=PIPE, stderr=PIPE)
        realtime_pipe_reader = StringRealtimePipeReader(popen)
        time.sleep(SECOND_SLEEP_FOR_TEST_LONG)
        realtime_pipe_reader.stop()
        assert f"stderr{os.linesep}" * 10 in realtime_pipe_reader.read_stderr()
        assert f"stdout{os.linesep}" * 10 in realtime_pipe_reader.read_stdout()
        popen.terminate()


class TestFFmpegRealtimePipeReader:
    def test(self, path_file_input: Path) -> None:
        popen = self.create_popen(path_file_input)
        realtime_pipe_reader = FFmpegRealtimePipeReader(popen, frame_bytes=(384 * 216 * 3))
        popen.wait()
        realtime_pipe_reader.stop()
        list_frame_bytes = realtime_pipe_reader.read_stdout()
        assert 700 < len(list_frame_bytes) <= 1100
        stderr = realtime_pipe_reader.read_stderr()
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_FIRSTLINE, stderr) is not None
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_LASTLINE, stderr) is not None

    def test_stop(self, path_file_input: Path) -> None:
        popen = self.create_popen(path_file_input)
        realtime_pipe_reader = FFmpegRealtimePipeReader(popen, frame_bytes=(384 * 216 * 3))
        time.sleep(SECOND_SLEEP_FOR_TEST_SHORT)
        realtime_pipe_reader.stop()
        list_frame_bytes = realtime_pipe_reader.read_stdout()
        assert 0 < len(list_frame_bytes) <= 700
        stderr = realtime_pipe_reader.read_stderr()
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_FIRSTLINE, stderr) is not None
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_LASTLINE, stderr) is None

    @staticmethod
    def create_popen(path_file_input: Path) -> Popen[bytes]:
        stream = ffmpeg.input(path_file_input)
        stream = ffmpeg.filter(stream, "scale", 768, -1)
        stream_spec = ffmpeg.output(stream, "pipe:", f="rawvideo").global_args("-n")

        return ffmpeg.run_async(stream_spec, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
