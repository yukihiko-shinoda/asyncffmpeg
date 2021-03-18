"""
To realize non-blocking read.
see:
    - Answer: A non-blocking read on a subprocess.PIPE in Python - Stack Overflow
    https://stackoverflow.com/a/4896288/12721873
"""
from abc import abstractmethod
from subprocess import Popen
from threading import Event
from typing import Optional

from asyncffmpeg.pipe.pipe_manager import BytesPipeManager, StringPipeManager


class RealtimePipeReader:
    """Abstract class."""

    def __init__(self):
        self.event = Event()

    @abstractmethod
    def read_stdout(self):
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def read_stderr(self):
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def stop(self):
        raise NotImplementedError()  # pragma: no cover


class StringRealtimePipeReader(RealtimePipeReader):
    """For strings."""

    def __init__(self, popen: Popen):
        super().__init__()
        assert popen.stdout is not None
        assert popen.stderr is not None
        self.pipe_manager_stdout = StringPipeManager(self.event, popen.stdout)
        self.pipe_manager_stderr = StringPipeManager(self.event, popen.stderr)

    def read_stdout(self):
        return self.pipe_manager_stdout.read()

    def read_stderr(self):
        return self.pipe_manager_stderr.read()

    def stop(self):
        self.event.set()
        self.pipe_manager_stdout.thread.join()
        self.pipe_manager_stderr.thread.join()


class FFmpegRealtimePipeReader(RealtimePipeReader):
    """For FFmpeg."""

    def __init__(self, popen: Popen, *, frame_bytes: Optional[int] = None):
        super().__init__()
        assert popen.stdout is not None
        assert popen.stderr is not None
        self.pipe_manager_stderr = StringPipeManager(self.event, popen.stderr)
        self.pipe_manager_stdout = (
            None if frame_bytes is None else BytesPipeManager(self.event, popen.stdout, frame_bytes)
        )

    def read_stdout(self):
        return self.pipe_manager_stdout.read()

    def read_stderr(self):
        return self.pipe_manager_stderr.read()

    def stop(self):
        self.event.set()
        self.pipe_manager_stderr.thread.join()
        if self.pipe_manager_stdout is not None:
            self.pipe_manager_stdout.thread.join()
