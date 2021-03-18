"""Logs pipe output and stores it into queue."""
from abc import abstractmethod
from logging import getLogger
from queue import Queue
from threading import Event, Thread
from typing import IO


class PipeManager:
    """Logs pipe output and stores it into queue."""

    def __init__(self, event: Event, pipe: IO):
        self.event = event
        self.queue: Queue = Queue()
        self.logger = getLogger(__name__)
        self.thread = self.create_thread(pipe)

    def create_thread(self, pipe: IO):
        thread = Thread(target=self.log, args=(pipe,))
        thread.daemon = True  # thread dies with the program
        thread.start()
        return thread

    @abstractmethod
    def log(self, pipe: IO):
        raise NotImplementedError()  # pragma: no cover

    @abstractmethod
    def read(self):
        raise NotImplementedError()  # pragma: no cover


class BytesPipeManager(PipeManager):
    """For bytes."""

    def __init__(self, event: Event, pipe: IO, frame_bytes: int):
        self.frame_bytes = frame_bytes
        super().__init__(event, pipe)

    def log(self, pipe: IO):
        with pipe:
            try:
                while True:
                    if self.event.is_set():
                        break
                    out_bytes = pipe.read(self.frame_bytes)
                    if out_bytes != b"":
                        self.queue.put(out_bytes)
            # Reason: Dfficult to cause intentionally.
            except ValueError as error:  # pragma: no cover
                self.logger.info(error, exc_info=True)

    def read(self):
        """
        Vacuums stderr by get_nowait().
        see:
          - Answer: A non-blocking read on a subprocess.PIPE in Python - Stack Overflow
            https://stackoverflow.com/a/4896288/12721873
        """
        list_string = []
        while not self.queue.empty():
            list_string.append(self.queue.get_nowait())
        return list_string


class StringPipeManager(PipeManager):
    """For strings."""

    def log(self, pipe: IO):
        with pipe:
            try:
                for line in iter(pipe.readline, b""):
                    self.queue.put(line)
                    self.logger.info(line.decode("utf-8").rstrip())
                    if self.event.is_set():
                        break
            # Reason: Dfficult to cause intentionally.
            except ValueError as error:  # pragma: no cover
                self.logger.info(error, exc_info=True)

    def read(self):
        """
        Vacuums stderr by get_nowait().
        see:
          - Answer: A non-blocking read on a subprocess.PIPE in Python - Stack Overflow
            https://stackoverflow.com/a/4896288/12721873
        """
        list_string = []
        while not self.queue.empty():
            list_string.append(self.queue.get_nowait().decode("utf-8"))
        return "".join(list_string)
