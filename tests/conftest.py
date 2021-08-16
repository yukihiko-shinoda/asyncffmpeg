"""Configuration of pytest"""
import logging
import os
import shutil
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


@pytest.fixture()
def chdir(tmp_path: Path) -> Generator[Path, None, None]:
    path_current = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(path_current)


@pytest.fixture()
# Reason: To refer other fixture. pylint: disable=redefined-outer-name
# Reason: This is fixture. pylint: disable=unused-argument
def code_and_environment_example(
    tmp_path: Path, resource_path_root: Path, path_file_input: Path, chdir: Path
) -> Generator[Path, None, None]:
    """Prepare files for test of example on README.md."""
    path_sut = resource_path_root / "example_readme.py"
    shutil.copy(path_sut, tmp_path)
    shutil.copy(path_file_input, tmp_path / "input.mp4")
    yield tmp_path / path_sut.name
