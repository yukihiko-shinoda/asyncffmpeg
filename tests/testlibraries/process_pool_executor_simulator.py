"""To collect coverage in except KeyboardInterrupt block.

Since coverage.py can't trace asyncio.ProcessPoolExecutor.
see: https://github.com/nedbat/coveragepy/issues/481
"""

from __future__ import annotations

import multiprocessing
import os
import signal
from contextlib import AbstractContextManager
from queue import Empty
from typing import TYPE_CHECKING
from typing import Any
from typing import Callable
from typing import Generic
from typing import Literal
from typing import NoReturn

import psutil

from tests.testlibraries.types import ParamSpecCoroutineFunctionArguments
from tests.testlibraries.types import TypeVarArgument
from tests.testlibraries.types import TypeVarReturnValue

if TYPE_CHECKING:
    from collections.abc import Awaitable
    from collections.abc import Generator
    from types import TracebackType


class CoroutineExecutor(
    AbstractContextManager["CoroutineExecutor[TypeVarReturnValue, TypeVarArgument]"],
    Generic[TypeVarReturnValue, TypeVarArgument],
):
    """Executes coroutine as generator in subprocess to arrow stopping running generator."""

    def __init__(self, coroutine: Generator[TypeVarReturnValue, TypeVarArgument, Any]) -> None:
        self.coroutine = coroutine
        # Reason: Queue is subscriptable in Python 3.9+. pylint: disable=unsubscriptable-object
        self.queue: multiprocessing.Queue[TypeVarReturnValue] = multiprocessing.Queue()

    def __exit__(
        self,
        _exc_type: type[BaseException] | None,
        _exc_val: BaseException | None,
        _exc_tb: TracebackType | None,
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


class ProcessPoolExecutorSimulator(Generic[TypeVarReturnValue]):
    """To collect coverage in except KeyboardInterrupt block.

    Since coverage.py can't trace asyncio.ProcessPoolExecutor.
    see: https://github.com/nedbat/coveragepy/issues/481
    """

    def __init__(
        self,
        corofn: Callable[ParamSpecCoroutineFunctionArguments, Awaitable[TypeVarReturnValue]],
        *args: ParamSpecCoroutineFunctionArguments.args,
        **kwargs: ParamSpecCoroutineFunctionArguments.kwargs,
    ) -> None:
        self.process = multiprocessing.Process(target=self.run, args=(corofn, *args), kwargs=kwargs)

    @staticmethod
    def run(
        corofn: Callable[ParamSpecCoroutineFunctionArguments, Generator[Any, Any, TypeVarReturnValue]],
        *args: ParamSpecCoroutineFunctionArguments.args,
        **kwargs: ParamSpecCoroutineFunctionArguments.kwargs,
    ) -> TypeVarReturnValue | None:
        """Runs coroutine as generator and receive SIGINT to interrupt."""

        # Reason: To follow the specification of Python.
        def handler(_signum: int, _frame: Any | None) -> NoReturn:  # noqa: ANN401
            # To stop running generator, it requires to be run in subprocess
            # and terminate process when stop.
            current_process = psutil.Process(os.getpid())
            child_processes = current_process.children()
            for child_process in child_processes:
                child_process.send_signal(signal.SIGINT)
            raise KeyboardInterrupt

        signal.signal(signal.SIGINT, handler)
        # Coroutine requires to be instantiated in this method,
        # otherwise, warning occur.
        # RuntimeWarning: coroutine 'xxxx' was never awaited
        with CoroutineExecutor(corofn(*args, **kwargs)) as coroutine_executor:
            prompt = None
            try:
                while True:
                    prompt = coroutine_executor.run_step_in_child_process(prompt)
            except Empty:
                return prompt
