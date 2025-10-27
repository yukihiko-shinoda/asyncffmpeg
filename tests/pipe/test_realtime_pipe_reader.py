"""Test for asyncffmpeg.pipe.realtime_pipe_reader."""

import os
import re
import sys
import time
from pathlib import Path

# Reason: This package requires to use subprocess.
from subprocess import PIPE  # nosec
from subprocess import Popen  # nosec
from unittest.mock import MagicMock

import ffmpeg
import pytest

from asyncffmpeg.pipe.realtime_pipe_reader import FFmpegRealtimePipeReader
from asyncffmpeg.pipe.realtime_pipe_reader import StringRealtimePipeReader
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_LONG
from tests.testlibraries import SECOND_SLEEP_FOR_TEST_SHORT
from tests.testlibraries.instance_resource import InstanceResource


class TestStringRealtimePipeReader:
    """Tests for StringRealtimePipeReader."""

    def test(self) -> None:
        """Test that realtime pipe reader can read stdout and stderr continuously."""
        command = [sys.executable, str(Path("tests") / "testlibraries" / "print_forever.py")]
        # Reason: This only executes test code.
        with Popen(command, stdout=PIPE, stderr=PIPE) as popen:  # noqa: S603  # nosec
            realtime_pipe_reader = StringRealtimePipeReader(popen)
            time.sleep(SECOND_SLEEP_FOR_TEST_LONG)
            realtime_pipe_reader.stop()
            assert f"stderr{os.linesep}" * 10 in realtime_pipe_reader.read_stderr()
            assert f"stdout{os.linesep}" * 10 in realtime_pipe_reader.read_stdout()
            popen.terminate()

    def test_stdout_none(self) -> None:
        """Test that ValueError is raised when popen.stdout is None."""
        popen_mock = MagicMock()
        popen_mock.stdout = None
        popen_mock.stderr = MagicMock()
        with pytest.raises(ValueError, match=r"popen\.stdout is None"):
            StringRealtimePipeReader(popen_mock)

    def test_stderr_none(self) -> None:
        """Test that ValueError is raised when popen.stderr is None."""
        popen_mock = MagicMock()
        popen_mock.stdout = MagicMock()
        popen_mock.stderr = None
        with pytest.raises(ValueError, match=r"popen\.stderr is None"):
            StringRealtimePipeReader(popen_mock)


class TestFFmpegRealtimePipeReader:
    """Tests for FFmpegRealtimePipeReader."""

    def test(self, path_file_input: Path) -> None:
        """Test that FFmpeg realtime pipe reader can read frame bytes from stdout."""
        expected_frame_bytes_minimum = 700
        expected_frame_bytes_maximum = 1100
        popen = self.create_popen(path_file_input)
        realtime_pipe_reader = FFmpegRealtimePipeReader(popen, frame_bytes=384 * 216 * 3)
        popen.wait()
        realtime_pipe_reader.stop()
        list_frame_bytes = realtime_pipe_reader.read_stdout()
        assert expected_frame_bytes_minimum < len(list_frame_bytes) <= expected_frame_bytes_maximum
        stderr = realtime_pipe_reader.read_stderr()
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_FIRSTLINE, stderr) is not None
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_LASTLINE, stderr) is not None

    def test_stop(self, path_file_input: Path) -> None:
        """Test that FFmpeg realtime pipe reader can be stopped early."""
        expected_frame_bytes_minimum = 0
        expected_frame_bytes_maximum = 700
        popen = self.create_popen(path_file_input)
        realtime_pipe_reader = FFmpegRealtimePipeReader(popen, frame_bytes=384 * 216 * 3)
        time.sleep(SECOND_SLEEP_FOR_TEST_SHORT)
        realtime_pipe_reader.stop()
        list_frame_bytes = realtime_pipe_reader.read_stdout()
        assert expected_frame_bytes_minimum < len(list_frame_bytes) <= expected_frame_bytes_maximum
        stderr = realtime_pipe_reader.read_stderr()
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_FIRSTLINE, stderr) is not None
        assert re.search(InstanceResource.REGEX_STDERR_FFMPEG_LASTLINE, stderr) is None

    def test_stdout_none(self) -> None:
        """Test that ValueError is raised when popen.stdout is None."""
        popen_mock = MagicMock()
        popen_mock.stdout = None
        popen_mock.stderr = MagicMock()
        with pytest.raises(ValueError, match=r"popen\.stdout is None"):
            FFmpegRealtimePipeReader(popen_mock, frame_bytes=1024)

    def test_stderr_none(self) -> None:
        """Test that ValueError is raised when popen.stderr is None."""
        popen_mock = MagicMock()
        popen_mock.stdout = MagicMock()
        popen_mock.stderr = None
        with pytest.raises(ValueError, match=r"popen\.stderr is None"):
            FFmpegRealtimePipeReader(popen_mock, frame_bytes=1024)

    @staticmethod
    def create_popen(path_file_input: Path) -> Popen[bytes]:
        stream = ffmpeg.input(path_file_input)
        stream = ffmpeg.filter(stream, "scale", 768, -1)
        stream_spec = ffmpeg.output(stream, "pipe:", f="rawvideo").global_args("-n")
        # Reason: Requires to update ffmpeg-python side.
        return ffmpeg.run_async(stream_spec, pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)  # type: ignore[no-any-return]
