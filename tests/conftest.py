"""Configuration of pytest"""
import logging
from contextlib import contextmanager
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from typing import Callable, ContextManager, Generator

import pytest

collect_ignore = ["setup.py"]


@pytest.fixture
def path_file_input(resource_path_root: Path) -> Generator[Path, None, None]:
    yield resource_path_root / "sample.mp4"


@pytest.fixture
def path_file_output(tmp_path: Path) -> Generator[Path, None, None]:
    yield tmp_path / "out.mp4"


@pytest.fixture()
def caplog_workaround() -> Callable[[], ContextManager[None]]:
    """
    To capture log from subprocess.
    see:
      - Answer: Empty messages in caplog when logs emitted in a different process - Stack Overflow
        https://stackoverflow.com/a/63054881/12721873
    """

    @contextmanager
    def ctx() -> Generator[None, None, None]:
        logger_queue: "Queue[logging.LogRecord]" = Queue()
        logger = logging.getLogger()
        queue_handler = handlers.QueueHandler(logger_queue)
        logger.addHandler(queue_handler)
        yield
        logger.removeHandler(queue_handler)
        while not logger_queue.empty():
            log_record: logging.LogRecord = logger_queue.get()
            # Reason: To hack. pylint: disable=protected-access
            logger.handle(log_record)

    return ctx
