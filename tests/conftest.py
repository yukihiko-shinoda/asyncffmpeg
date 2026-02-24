"""Configuration of pytest."""

import logging
import os
import shutil
import time
from collections.abc import Generator
from contextlib import AbstractContextManager
from contextlib import contextmanager
from logging import handlers
from multiprocessing import Queue
from pathlib import Path
from queue import Empty
from typing import Callable

import pytest

collect_ignore = ["setup.py"]


@pytest.fixture
def path_file_input(resource_path_root: Path) -> Path:
    return resource_path_root / "sample.mp4"


@pytest.fixture
def path_file_output(tmp_path: Path) -> Path:
    return tmp_path / "out.mp4"


@pytest.fixture
def caplog_workaround() -> Callable[[], AbstractContextManager[None]]:
    """To capture log from subprocess.

    see:
      - Answer: Empty messages in caplog when logs emitted in a different process - Stack Overflow
        https://stackoverflow.com/a/63054881/12721873
    """

    @contextmanager
    def ctx() -> Generator[None, None, None]:
        # Reason: Queue is subscriptable in Python 3.9+. pylint: disable=unsubscriptable-object
        logger_queue: Queue[logging.LogRecord] = Queue()
        logger = logging.getLogger()
        queue_handler = handlers.QueueHandler(logger_queue)
        logger.addHandler(queue_handler)
        # Set the log level to capture all logs
        original_level = logger.level
        logger.setLevel(logging.DEBUG)
        yield
        logger.removeHandler(queue_handler)
        logger.setLevel(original_level)
        # Process logs with a timeout to avoid infinite wait
        timeout_end = time.time() + 2  # 2 second timeout
        while not logger_queue.empty() and time.time() < timeout_end:
            try:
                log_record: logging.LogRecord = logger_queue.get(timeout=0.1)
            except Empty:
                # Queue became empty while we were waiting
                break
            # Reason: To hack. pylint: disable=protected-access
            logger.handle(log_record)

    return ctx


@pytest.fixture
def chdir(tmp_path: Path) -> Generator[Path, None, None]:
    path_current = Path.cwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(path_current)


@pytest.fixture
# Reason: To refer other fixture. pylint: disable=redefined-outer-name
# Reason: This is fixture. pylint: disable=unused-argument
def code_and_environment_example(
    tmp_path: Path,
    resource_path_root: Path,
    path_file_input: Path,
    # Reason: Since pytest fixture can't use @pytest.mark.usefixtures.
    chdir: Path,  # noqa: ARG001
) -> Path:
    """Prepare files for test of example on README.md."""
    path_sut = resource_path_root / "example_readme.py"
    shutil.copy(path_sut, tmp_path)
    shutil.copy(path_file_input, tmp_path / "input.mp4")
    return tmp_path / path_sut.name


class LoggingEnvironment:
    """Environment for logging in subprocess."""

    def __init__(self, tmp_path: Path) -> None:
        self.debug_log_path = tmp_path / "subprocess_debug.log"

    def create_env(self) -> dict[str, str]:
        """Create environment variables for subprocess."""
        env: dict[str, str] = {}
        env.update(os.environ)
        pythonpath = env.get("PYTHONPATH")
        env["PYTHONPATH"] = str(Path(__file__).parent.parent) + (
            "" if pythonpath is None else (os.pathsep + pythonpath)
        )
        env["ASYNCFFMPEG_DEBUG_LOG"] = str(self.debug_log_path)
        return env

    def get_log_content(self) -> str:
        """Get the content of the debug log."""
        return (
            self.debug_log_path.read_text(encoding="utf-8")
            if self.debug_log_path.exists()
            else "(log file not created)"
        )


@pytest.fixture
def logging_environment(tmp_path: Path) -> LoggingEnvironment:
    return LoggingEnvironment(tmp_path)
