"""Configuration of pytest"""
import logging
from contextlib import contextmanager
from logging import handlers
from multiprocessing import Queue

import pytest

collect_ignore = ["setup.py"]


@pytest.fixture
def response():
    """Sample pytest fixture.

    See more at: http://doc.pytest.org/en/latest/fixture.html
    """
    # import requests
    # return requests.get('https://github.com/audreyr/cookiecutter-pypackage')


@pytest.fixture
def path_file_input(resource_path_root):
    yield resource_path_root / "sample.mp4"


@pytest.fixture
def path_file_output(tmp_path):
    yield tmp_path / "out.mp4"


@pytest.fixture()
def caplog_workaround():
    """
    To capture log from subprocess.
    see:
      - Answer: Empty messages in caplog when logs emitted in a different process - Stack Overflow
        https://stackoverflow.com/a/63054881/12721873
    """

    @contextmanager
    def ctx():
        logger_queue = Queue()
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
