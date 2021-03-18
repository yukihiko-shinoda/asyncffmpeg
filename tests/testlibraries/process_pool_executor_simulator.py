"""
To collect coverage in except KeyboardInterrupt block.
Since coverage.py can't trace asyncio.ProcessPoolExecutor.
see: https://github.com/nedbat/coveragepy/issues/481
"""
import multiprocessing
import os
import signal
from contextlib import AbstractContextManager
from queue import Empty
from typing import Awaitable, Callable, Generator

import psutil


class ProcessPoolExecutorSimulator:
    """
    To collect coverage in except KeyboardInterrupt block.
    Since coverage.py can't trace asyncio.ProcessPoolExecutor.
    see: https://github.com/nedbat/coveragepy/issues/481
    """

    def __init__(self, corofn: Callable[..., Awaitable], *args):
        self.process = multiprocessing.Process(target=self.run, args=(corofn, args))

    @staticmethod
    def run(corofn, args):
        """Runs coroutine as generator and receive SIGINT to interrupt."""

        def handler(_signum, _frame):
            # To stop running generator, it requires to be run in subprocess
            # and terminate process when stop.
            current_process = psutil.Process(os.getpid())
            child_processes = current_process.children()
            for child_process in child_processes:
                child_process.send_signal(signal.SIGINT)
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, handler)
        # Coroutine requires to be instantiated in this method,
        # otherwise, warning occur.
        # RuntimeWarning: coroutine 'xxxx' was never awaited
        with CoroutineExecutor(corofn(*args)) as coroutine_executor:
            prompt = None
            try:
                prompt = coroutine_executor.run_step_in_child_process(None)
                while True:
                    prompt = coroutine_executor.run_step_in_child_process(prompt)
            except Empty:
                return prompt


class CoroutineExecutor(AbstractContextManager):
    """Executes coroutine as generator in subprocess to arrow stopping running generator."""

    def __init__(self, coroutine: Generator):
        self.coroutine = coroutine
        self.queue: multiprocessing.Queue = multiprocessing.Queue()

    def __enter__(self):
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.coroutine.close()

    def run_step_in_child_process(self, arg):
        process = multiprocessing.Process(target=self.run_step, args=(arg,))
        process.start()
        process.join()
        return self.queue.get()

    def run_step(self, arg):
        self.queue.put(self.coroutine.send(arg))
