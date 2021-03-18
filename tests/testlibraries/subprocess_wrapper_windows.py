"""Subprocess wrapper for Windows."""
import asyncio
import logging
import os
import re
import sys
import time
from logging import DEBUG, basicConfig, getLogger, handlers
from multiprocessing import Manager

import psutil

from tests.testlibraries import SECOND_SLEEP_FOR_TEST_LONG
from tests.testlibraries.example_use_case import example_use_case_interrupt
from tests.testlibraries.instance_resource import InstanceResource
from tests.testlibraries.keyboardinterrupter.keyboard_interrupter import KeyboardInterrupter
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket


async def get_process_id():
    """The process to get process id to kill."""
    print("Await sleep")
    logger = getLogger(__name__)
    logger.debug("Get process id")
    # Wait for starting subprocess
    # otherwise, time.sleep() will block starting subprocess.
    current_process = psutil.Process(os.getpid())
    while len(current_process.children()) < 2:
        print(len(current_process.children()))
        await asyncio.sleep(0.01)
    logger.debug("Start sleep")
    time.sleep(SECOND_SLEEP_FOR_TEST_LONG)
    print("Kill all processes in this window.")
    return 0


def worker_configurer():
    logger = getLogger()
    logger.setLevel(DEBUG)


def listener_configurer(queue) -> handlers.QueueListener:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("[%(levelname)s/%(processName)s] %(message)s"))
    return handlers.QueueListener(queue, console_handler)


class Checker:
    """Checks logger output from queue."""

    def __init__(self):
        self.ffmpeg_process_quit_finish = False
        self.ffmpeg_closed_log = False
        self.logger = getLogger(__name__)

    def check(self, queue):
        """Checks logger output from queue."""
        log_record: logging.LogRecord = queue.get()
        self.logger.handle(log_record)
        if "FFmpeg process quit finish" in log_record.message:
            self.ffmpeg_process_quit_finish = True
        if re.search(InstanceResource.REGEX_STDERR_FFMPEG_LASTLINE, log_record.message,) is not None:
            self.ffmpeg_closed_log = True


def check_log(queue):
    """Checks log."""
    logger = getLogger(__name__)
    checker = Checker()
    try:
        while not queue.empty():
            checker.check(queue)
        assert checker.ffmpeg_process_quit_finish
        assert checker.ffmpeg_closed_log
    except BaseException:
        logger.exception("Error!")
        time.sleep(10)
        raise


def main():
    """Tests CTRL + C."""
    manager = Manager()
    queue = manager.Queue(-1)
    path_file_input = LocalSocket.receive()
    LocalSocket.send("Next")
    path_file_output = LocalSocket.receive()
    basicConfig(stream=sys.stdout, level=DEBUG)
    logger = getLogger(__name__)
    try:
        KeyboardInterrupter(
            example_use_case_interrupt(path_file_input, path_file_output, queue, worker_configurer), get_process_id()
        ).test_keyboard_interrupt()
    except KeyboardInterrupt:
        logger.debug("__main__ KeyboardInterrupt")
        check_log(queue)
        LocalSocket.send("Test succeed")
        logger.debug("__main__ sleep")
    finally:
        time.sleep(10)


if __name__ == "__main__":
    main()
