"""Subprocess wrapper for Windows."""

import asyncio
import logging
import os
import queue
import re
import sys
import time
from logging import DEBUG
from logging import LogRecord
from logging import basicConfig
from logging import getLogger
from logging import handlers
from multiprocessing import Manager

import psutil

from tests.testlibraries import SECOND_SLEEP_FOR_TEST_LONG
from tests.testlibraries.example_use_case import example_use_case_interrupt
from tests.testlibraries.instance_resource import InstanceResource
from tests.testlibraries.keyboardinterrupter.keyboard_interrupter import KeyboardInterrupter
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket


async def get_process_id() -> int:
    """The process to get process id to kill."""
    print("Await sleep")
    logger = getLogger(__name__)
    logger.debug("Get process id")
    # Wait for starting subprocess
    # otherwise, time.sleep() will block starting subprocess.
    current_process = psutil.Process(os.getpid())
    length_children_has_one_in_windows = 2  # From investigation result
    while len(current_process.children()) < length_children_has_one_in_windows:
        print(len(current_process.children()))
        await asyncio.sleep(0.01)
    logger.debug("Start sleep")
    # To block this process until KeyboardInterrupt is sent
    time.sleep(SECOND_SLEEP_FOR_TEST_LONG)  # noqa: ASYNC251
    print("Kill all processes in this window.")
    return 0


def worker_configurer() -> None:
    logger = getLogger()
    logger.setLevel(DEBUG)


def listener_configurer(queue_log_record: queue.Queue[LogRecord]) -> handlers.QueueListener:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s/%(processName)s] %(message)s"))
    return handlers.QueueListener(queue_log_record, console_handler)


class Checker:
    """Checks logger output from queue."""

    def __init__(self) -> None:
        self.ffmpeg_process_quit_finish = False
        self.ffmpeg_closed_log = False
        self.logger = getLogger(__name__)

    def check_record(self, log_record: LogRecord) -> None:
        """Checks a single log record."""
        self.logger.handle(log_record)
        if "FFmpeg process quit finish" in log_record.message:
            self.ffmpeg_process_quit_finish = True
        if (
            re.search(
                InstanceResource.REGEX_STDERR_FFMPEG_LAST_LINE,
                log_record.message,
            )
            is not None
        ):
            self.ffmpeg_closed_log = True


def check_log(queue_log_record: "queue.Queue[LogRecord]") -> None:
    """Checks log."""
    logger = getLogger(__name__)
    checker = Checker()
    messages = []
    while not queue_log_record.empty():
        record = queue_log_record.get()
        messages.append(record.message)
        checker.check_record(record)
    logger.debug("check_log: processed %d messages", len(messages))
    logger.debug("check_log: ffmpeg_process_quit_finish=%s", checker.ffmpeg_process_quit_finish)
    logger.debug("check_log: ffmpeg_closed_log=%s", checker.ffmpeg_closed_log)
    logger.debug("check_log: all messages: %s", messages)
    try:
        assert checker.ffmpeg_process_quit_finish, "Missing 'FFmpeg process quit finish' in logs"
        assert checker.ffmpeg_closed_log, "Missing FFmpeg stderr final line in logs"
    except BaseException:
        logger.exception("Log check failed")
        time.sleep(10)
        raise


def main() -> None:
    """Tests CTRL + C."""
    manager = Manager()
    queue_log_record = manager.Queue(-1)
    path_file_input = LocalSocket.receive()
    LocalSocket.send("Next")
    path_file_output = LocalSocket.receive()
    basicConfig(stream=sys.stdout, level=DEBUG)
    log_path = os.environ.get("ASYNCFFMPEG_DEBUG_LOG")
    if log_path:
        file_handler = logging.FileHandler(log_path, mode="w", encoding="utf-8")
        file_handler.setLevel(DEBUG)
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s %(process)d %(levelname)s %(name)s:%(lineno)d %(message)s"),
        )
        logging.getLogger().addHandler(file_handler)
    logger = getLogger(__name__)
    logger.debug("main: path_file_input=%s path_file_output=%s", path_file_input, path_file_output)
    try:
        KeyboardInterrupter(
            example_use_case_interrupt(path_file_input, path_file_output, queue_log_record, worker_configurer),
            get_process_id(),
        ).test_keyboard_interrupt()
    except KeyboardInterrupt:
        logger.debug("__main__ KeyboardInterrupt")
        try:
            check_log(queue_log_record)
            LocalSocket.send("Test succeed")
            logger.debug("__main__ sleep")
        except BaseException as exc:
            logger.exception("check_log or send failed after KeyboardInterrupt")
            LocalSocket.send(f"Error: {exc!r}")
            raise
    except BaseException as exc:
        logger.exception("Unexpected exception (not KeyboardInterrupt)")
        LocalSocket.send(f"Error: {exc!r}")
        raise
    finally:
        time.sleep(10)


if __name__ == "__main__":
    main()
