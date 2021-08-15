"""The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
import queue
from logging import LogRecord, getLogger
from pathlib import Path
from typing import Any, Callable

# Reason: mypy issue: https://github.com/python/mypy/issues/10198
from asynccpu import ProcessTaskPoolExecutor  # type: ignore

# Reason: Following export method in __init__.py from Effective Python 2nd Edition item 85
from asyncffmpeg import FFmpegCoroutineFactory  # type: ignore
from tests.testlibraries.create_stream_spec_croutine import CreateStreamSpecCoroutineFilter
from tests.testlibraries.keyboardinterrupter.local_socket import LocalSocket


async def example_use_case_interrupt(
    path_file_input: str,
    path_file_output: str,
    queue_log_record: queue.Queue[LogRecord],
    configurer: Callable[..., Any],
) -> None:
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    logger = getLogger(__name__)
    logger.info("Example use case interrupt start")
    with ProcessTaskPoolExecutor(
        max_workers=3, cancel_tasks_when_shutdown=True, queue=queue_log_record, configurer=configurer
    ) as executor:
        ffmpeg_coroutine = FFmpegCoroutineFactory.create()
        coroutine_create_stream_spec_filter = CreateStreamSpecCoroutineFilter(path_file_input, path_file_output)
        future = executor.create_process_task(ffmpeg_coroutine.execute, coroutine_create_stream_spec_filter.create)
        await future
        raise Exception("Failed")


async def example_use_case(path_file_input: Path, path_file_output: Path) -> None:
    """The example use case of FFmpegCroutine for E2E testing in case of interrupt."""
    with ProcessTaskPoolExecutor(max_workers=1, cancel_tasks_when_shutdown=True) as executor:
        task = executor.create_process_task(
            FFmpegCoroutineFactory.create().execute,
            CreateStreamSpecCoroutineFilter(path_file_input, path_file_output).create,
        )
        LocalSocket.send("Ready")
        await task
