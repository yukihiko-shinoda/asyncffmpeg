"""
To collect coverage in except KeyboardInterrupt block.
Since coverage.py can't trace asyncio.ProcessPoolExecutor.
see: https://github.com/nedbat/coveragepy/issues/481
"""
from __future__ import annotations

import multiprocessing
import os
import signal
from contextlib import AbstractContextManager
from queue import Empty
from types import TracebackType
from typing import Any, Awaitable, Callable, Generator, Generic, List, Literal, NoReturn, Optional, Type

import psutil

from tests.testlibraries.types import TypeVarArgument, TypeVarReturnValue


class ProcessPoolExecutorSimulator:
    """
    To collect coverage in except KeyboardInterrupt block.
    Since coverage.py can't trace asyncio.ProcessPoolExecutor.
    see: https://github.com/nedbat/coveragepy/issues/481
    """

    def __init__(self, corofn: Callable[..., Awaitable[Any]], *args: Any) -> None:
        self.process = multiprocessing.Process(target=self.run, args=(corofn, args))

    @staticmethod
    def run(corofn: Callable[..., Generator[Any, Any, Any]], args: List[Any]) -> Optional[TypeVarReturnValue]:
        """Runs coroutine as generator and receive SIGINT to interrupt."""

        def handler(_signum: int, _frame: Optional[Any]) -> NoReturn:
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
                while True:
                    prompt = coroutine_executor.run_step_in_child_process(prompt)
            except Empty:
                return prompt


class CoroutineExecutor(
    AbstractContextManager["CoroutineExecutor[TypeVarReturnValue, TypeVarArgument]"],
    Generic[TypeVarReturnValue, TypeVarArgument],
):
    """Executes coroutine as generator in subprocess to arrow stopping running generator."""

    def __init__(self, coroutine: Generator[TypeVarReturnValue, TypeVarArgument, Any]) -> None:
        self.coroutine = coroutine
        self.queue: "multiprocessing.Queue[TypeVarReturnValue]" = multiprocessing.Queue()

    def __enter__(self) -> CoroutineExecutor[TypeVarReturnValue, TypeVarArgument]:
        return self

    def __exit__(
        self,
        _exc_type: Optional[Type[BaseException]],
        _exc_val: Optional[BaseException],
        _exc_tb: Optional[TracebackType],
    ) -> Literal[False]:
        self.coroutine.close()
        return False

    def run_step_in_child_process(self, arg: TypeVarArgument) -> TypeVarReturnValue:
        process = multiprocessing.Process(target=self.run_step, args=(arg,))
        process.start()
        process.join()
        return self.queue.get()

    def run_step(self, arg: TypeVarArgument) -> None:
        self.queue.put(self.coroutine.send(arg))
